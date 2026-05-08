# app/services/entrenamiento_service.py
import hashlib, io, math
from datetime import date, timedelta
from typing import Optional

import joblib
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sqlalchemy import text
from sqlalchemy.orm import Session

ESPECIES_CONFIG = {
    "sitotroga":    {"list_fn": "list_sitotroga"},
    "trichogramma": {"list_fn": "list_trichogramma"},
    "galleria":     {"list_fn": "list_galleria"},
    "paratheresia": {"list_fn": "list_paratheresia"},
}


def _safe(v) -> Optional[float]:
    """Convierte nan/inf a None para que PostgreSQL y JSON no exploten."""
    if v is None:
        return None
    f = float(v)
    return None if (math.isnan(f) or math.isinf(f)) else round(f, 4)


class EntrenamientoService:
    def __init__(self, db: Session):
        self.db = db

    # ── Helpers BD ────────────────────────────────────────────────────────────

    def _get_config(self, especie: str) -> dict:
        row = self.db.execute(
            text("SELECT * FROM modelo_config WHERE especie = :e"),
            {"e": especie}
        ).mappings().first()
        return dict(row) if row else {}

    def get_todas_configs(self) -> list:
        rows = self.db.execute(
            text("SELECT * FROM modelo_config ORDER BY especie")
        ).mappings().all()
        return [dict(r) for r in rows]

    def update_config(self, especie: str, activo: bool | None, rango_meses: int | None) -> dict:
        sets, params = [], {"e": especie}
        if activo is not None:
            sets.append("activo = :activo")
            params["activo"] = activo
        if rango_meses is not None:
            if not (1 <= rango_meses <= 24):
                raise ValueError("rango_meses debe estar entre 1 y 24")
            sets.append("rango_meses = :rango")
            params["rango"] = rango_meses
        if not sets:
            return self._get_config(especie)
        self.db.execute(
            text(f"UPDATE modelo_config SET {', '.join(sets)} WHERE especie = :e"),
            params
        )
        self.db.commit()
        return self._get_config(especie)

    def _guardar_modelo(self, especie: str, modelo, metricas: dict, n: int):
        buf = io.BytesIO()
        joblib.dump(modelo, buf)
        self.db.execute(text("""
            INSERT INTO modelo_entrenado
                (especie, modelo_pkl, r2_score, mae, rmse, n_registros, entrenado_en)
            VALUES
                (:e, :blob, :r2, :mae, :rmse, :n, NOW())
            ON CONFLICT (especie) DO UPDATE SET
                modelo_pkl   = EXCLUDED.modelo_pkl,
                r2_score     = EXCLUDED.r2_score,
                mae          = EXCLUDED.mae,
                rmse         = EXCLUDED.rmse,
                n_registros  = EXCLUDED.n_registros,
                entrenado_en = EXCLUDED.entrenado_en
        """), {
            "e":    especie,
            "blob": buf.getvalue(),
            "r2":   metricas["r2"],
            "mae":  metricas["mae"],
            "rmse": metricas["rmse"],
            "n":    n,
        })

    def _insertar_log(self, especie: str, metricas: dict, n: int,
                      reemplazado: bool, motivo: Optional[str]):
        self.db.execute(text("""
            INSERT INTO modelo_log
                (especie, r2_score, mae, rmse, n_registros, fue_reemplazado, motivo_rechazo)
            VALUES
                (:e, :r2, :mae, :rmse, :n, :r, :m)
        """), {
            "e":   especie,
            "r2":  metricas["r2"],
            "mae": metricas["mae"],
            "rmse": metricas["rmse"],
            "n":   n,
            "r":   reemplazado,
            "m":   motivo,
        })

    def _actualizar_config_post_entreno(self, especie: str, nuevo_hash: str, r2: float):
        self.db.execute(text("""
            UPDATE modelo_config
            SET ultimo_hash    = :h,
                ultimo_r2      = :r2,
                ultimo_entreno = NOW(),
                proximo_entreno = NOW() + INTERVAL '1 day'
            WHERE especie = :e
        """), {"h": nuevo_hash, "r2": r2, "e": especie})

    def get_kpis(self, especie: str) -> list:
        rows = self.db.execute(text("""
            SELECT r2_score, mae, rmse, n_registros,
                   fue_reemplazado, motivo_rechazo, entrenado_en
            FROM modelo_log
            WHERE especie = :e
            ORDER BY entrenado_en DESC
            LIMIT 30
        """), {"e": especie}).mappings().all()
        return [dict(r) for r in rows]

    # ── Lógica principal ──────────────────────────────────────────────────────

    def entrenar_especie(self, clave: str, forzar: bool = False) -> dict:
        """
        forzar=True  → ignora el check de activo (para entrenamientos manuales).
        forzar=False → comportamiento original del cron.
        """
        from app.infrastructure.repositories.produccion_repository import ProduccionRepository
        repo = ProduccionRepository(self.db)

        cfg = self._get_config(clave)
        if not cfg:
            return {"saltado": True, "motivo": "Especie no configurada"}

        # Solo el cron respeta el flag activo; el manual siempre procede
        if not forzar and not cfg["activo"]:
            return {"saltado": True, "motivo": "Auto-train desactivado"}

        # Rango dinámico
        desde     = date.today() - timedelta(days=cfg["rango_meses"] * 30)
        list_fn   = ESPECIES_CONFIG[clave]["list_fn"]
        registros = getattr(repo, list_fn)(desde, None)

        if len(registros) < 2:          # mínimo 2 para R² válido
            return {
                "saltado": True,
                "motivo":  f"Solo {len(registros)} registros en el rango "
                           f"({cfg['rango_meses']} meses). Mínimo 2.",
            }

        fechas     = [r.fecha    for r in registros]
        cantidades = [r.cantidad for r in registros]

        # ¿Hay datos nuevos? (solo relevante para el cron)
        nuevo_hash = hashlib.md5(
            str(sorted(zip([str(f) for f in fechas], cantidades))).encode()
        ).hexdigest()
        if not forzar and cfg.get("ultimo_hash") == nuevo_hash:
            return {"saltado": True, "motivo": "Sin datos nuevos desde el último entrenamiento"}

        # Entrenar
        X = np.array([d.toordinal() for d in fechas]).reshape(-1, 1)
        y = np.array(cantidades, dtype=float)

        modelo = LinearRegression().fit(X, y)
        y_pred = modelo.predict(X)

        metricas = {
            "r2":   _safe(modelo.score(X, y)),
            "mae":  _safe(mean_absolute_error(y, y_pred)),
            "rmse": _safe(np.sqrt(mean_squared_error(y, y_pred))),
        }

        # Si R² es None (< 2 muestras llegaron aquí de algún modo) → rechazar
        if metricas["r2"] is None:
            return {
                "saltado": True,
                "motivo":  "R² indefinido (datos insuficientes para evaluar el modelo)",
            }

        # ¿El nuevo modelo es mejor que el guardado? (solo si no es forzado)
        fue_reemplazado = True
        motivo_rechazo  = None
        r2_anterior     = cfg.get("ultimo_r2")

        if not forzar and r2_anterior is not None and metricas["r2"] < r2_anterior - 0.02:
            fue_reemplazado = False
            motivo_rechazo  = (
                f"R² nuevo {metricas['r2']} < R² actual {r2_anterior} (umbral −0.02)"
            )

        if fue_reemplazado:
            self._guardar_modelo(clave, modelo, metricas, len(registros))
            self._actualizar_config_post_entreno(clave, nuevo_hash, metricas["r2"])

        self._insertar_log(clave, metricas, len(registros), fue_reemplazado, motivo_rechazo)
        self.db.commit()

        return {
            "entrenado":       True,
            "fue_reemplazado": fue_reemplazado,
            "r2_score":        metricas["r2"],
            "mae":             metricas["mae"],
            "rmse":            metricas["rmse"],
            "motivo_rechazo":  motivo_rechazo,
            "n_registros":     len(registros),
        }
