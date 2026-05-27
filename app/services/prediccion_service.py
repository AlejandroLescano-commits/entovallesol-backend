# app/services/prediccion_service.py
import io
import math
from collections import defaultdict
from datetime import date, timedelta
from typing import Optional

import joblib
import numpy as np
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.infrastructure.repositories.produccion_repository import ProduccionRepository


def _sanitizar(obj):
    """Convierte nan/inf a None recursivamente para que JSON no explote."""
    if isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    if isinstance(obj, dict):
        return {k: _sanitizar(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitizar(v) for v in obj]
    return obj


def _agregar_semanal(
    fechas: list[date],
    cantidades: list[float],
) -> tuple[list[date], list[float]]:
    """
    Agrega registros diarios en totales semanales (lunes como inicio de semana).
    Devuelve listas ordenadas por fecha de inicio de semana.
    Usado para especies con producción cíclica (Galleria) donde la regresión
    diaria produce R² negativo por el ruido inter-día.
    """
    por_semana: dict[date, float] = defaultdict(float)
    for f, c in zip(fechas, cantidades):
        # Inicio de semana (lunes)
        inicio_semana = f - timedelta(days=f.weekday())
        por_semana[inicio_semana] += c

    semanas_ordenadas = sorted(por_semana.keys())
    return semanas_ordenadas, [por_semana[s] for s in semanas_ordenadas]


ESPECIES = {
    "sitotroga": {
        "nombre":        "Sitotroga cerealella",
        "unidad":        "gramos",
        "list_prod":     "list_sitotroga",
        "list_salidas":  "list_notas_sitodroga",
        "tipos_salida":  ["T.exiguum", "T.pretiosum", "Infestación", "Ventas"],
        "agregar_semanal": False,
    },
    "trichogramma": {
        "nombre":        "Trichogramma",
        "unidad":        "pulgadas",
        "list_prod":     "list_trichogramma",
        "list_salidas":  "list_notas_avispitas",
        "tipos_salida":  ["Parasitacion", "Liberacion", "Ventas"],
        "agregar_semanal": False,
    },
    "galleria": {
        "nombre":        "Galleria melonella",
        "unidad":        "unidades",
        "list_prod":     "list_galleria",
        "list_salidas":  "list_notas_galleria",
        "tipos_salida":  ["Paratheresia", "Instalacion", "Ventas"],
        "agregar_semanal": True,   # ← ciclos biológicos alternados, agregar por semana
    },
    "paratheresia": {
        "nombre":        "Paratheresia claripalpis",
        "unidad":        "parejas",
        "list_prod":     "list_paratheresia",
        "list_salidas":  "list_notas_moscas",
        "tipos_salida":  ["Parasitacion", "Venta", "Liberacion"],
        "agregar_semanal": False,
    },
}


class PrediccionService:
    def __init__(self, db: Session):
        self.db   = db
        self.repo = ProduccionRepository(db)

    # ── Carga de modelo desde BD ──────────────────────────────────────────────

    def _cargar_modelo(self, especie: str):
        row = self.db.execute(
            text("SELECT modelo_pkl FROM modelo_entrenado WHERE especie = :e"),
            {"e": especie}
        ).first()
        if not row or not row[0]:
            return None
        return joblib.load(io.BytesIO(bytes(row[0])))

    def _info_modelo(self, especie: str) -> dict:
        row = self.db.execute(
            text("""
                SELECT r2_score, mae, rmse, n_registros, entrenado_en
                FROM modelo_entrenado WHERE especie = :e
            """),
            {"e": especie}
        ).mappings().first()
        return dict(row) if row else {}

    def _config_especie(self, especie: str) -> dict:
        row = self.db.execute(
            text("SELECT * FROM modelo_config WHERE especie = :e"),
            {"e": especie}
        ).mappings().first()
        return dict(row) if row else {}

    def _comparativa_algoritmos(self, especie: str) -> dict:
        import json
        row = self.db.execute(
            text("""
                SELECT detalle_algoritmos
                FROM modelo_log
                WHERE especie = :e
                ORDER BY entrenado_en DESC
                LIMIT 1
            """),
            {"e": especie}
        ).first()
        if not row or not row[0]:
            return {}
        try:
            return json.loads(row[0]) if isinstance(row[0], str) else row[0]
        except Exception:
            return {}

    # ── Motor de predicción ───────────────────────────────────────────────────

    def _predecir(
        self,
        modelo,
        fechas_hist:     list[date],
        cantidades_hist: list[float],
        dias_futuro:     int,
        agregar_semanal: bool = False,
    ) -> dict:
        # Para Galleria: agregar por semana antes de predecir
        if agregar_semanal:
            fechas_hist, cantidades_hist = _agregar_semanal(fechas_hist, cantidades_hist)

        y_hist = np.array(cantidades_hist, dtype=float)

        # FIX: usar base_ordinal guardada en el modelo durante el entrenamiento.
        # Si el modelo no tiene base_ordinal (modelo antiguo), usar el primer dato histórico
        # como fallback para mantener compatibilidad.
        base_ordinal: int = getattr(modelo, "base_ordinal", fechas_hist[0].toordinal())

        # X histórico con índice relativo (igual que en entrenamiento)
        X_hist = np.array([d.toordinal() - base_ordinal for d in fechas_hist]).reshape(-1, 1)

        hoy            = date.today()
        fechas_futuras = [hoy + timedelta(days=i + 1) for i in range(dias_futuro)]

        # FIX: X futuro también relativo a la misma base — el modelo ve valores
        # coherentes con su entrenamiento, no ordinales absolutos ~739_000.
        X_fut = np.array([d.toordinal() - base_ordinal for d in fechas_futuras]).reshape(-1, 1)

        preds = modelo.predict(X_fut)

        r2_raw = modelo.score(X_hist, y_hist)
        r2     = None if (math.isnan(r2_raw) or math.isinf(r2_raw)) else round(float(r2_raw), 4)

        coef      = modelo.coef_[0] if hasattr(modelo, "coef_") else 0.0
        tendencia = "creciente" if coef > 0 else "decreciente"

        preds_individuales: dict[str, list] = {}
        if hasattr(modelo, "modelos"):
            for nombre, alg in modelo.modelos.items():
                try:
                    p_ind = alg.predict(X_fut)
                    preds_individuales[nombre] = [
                        round(max(0.0, float(v)), 2) for v in p_ind
                    ]
                except Exception:
                    preds_individuales[nombre] = []

        # Nota informativa cuando se usa agregación semanal
        nota: Optional[str] = (
            "Predicción basada en totales semanales (producción cíclica). "
            "La demanda estimada representa el total esperado para esa semana."
            if agregar_semanal else None
        )

        resultado = {
            "r2_score":                  r2,
            "dias_predichos":            dias_futuro,
            "tendencia":                 tendencia,
            "promedio_historico":        round(float(np.mean(y_hist)), 2),
            "pesos_ensemble":            getattr(modelo, "pesos", {}),
            "predicciones_individuales": preds_individuales,
            "predicciones": [
                {
                    "fecha":                str(f),
                    "demanda_estimada":     round(max(0.0, float(p)), 2),
                    "produccion_necesaria": round(max(0.0, float(p) * 1.1), 2),
                }
                for f, p in zip(fechas_futuras, preds)
            ],
        }
        if nota:
            resultado["nota"] = nota
        return resultado

    # ── Predicción por tipo de salida ─────────────────────────────────────────

    def _predecir_por_destino(
        self,
        modelo,
        salidas:         list,
        tipos_salida:    list[str],
        dias_futuro:     int,
        es_galleria:     bool = False,
        agregar_semanal: bool = False,
    ) -> dict[str, dict]:
        resultado = {}

        for tipo in tipos_salida:
            registros_tipo = [s for s in salidas if s.tiposalida == tipo]

            if len(registros_tipo) < 2:
                resultado[tipo] = {"error": f"Datos insuficientes para '{tipo}'"}
                continue

            por_fecha: dict[date, float] = defaultdict(float)
            for s in registros_tipo:
                cantidad = s.cantidad
                if es_galleria and tipo == "Paratheresia" and s.ratio:
                    cantidad = s.cantidad * s.ratio
                por_fecha[s.fecha] += cantidad

            fechas     = sorted(por_fecha.keys())
            cantidades = [por_fecha[f] for f in fechas]

            resultado[tipo] = self._predecir(
                modelo,
                fechas,
                cantidades,
                dias_futuro,
                agregar_semanal=agregar_semanal,
            )

        return resultado

    # ── Balance producción vs demanda ─────────────────────────────────────────

    def _calcular_balance(
        self,
        pred_produccion:  dict,
        pred_por_destino: dict[str, dict],
    ) -> list[dict]:
        if not pred_produccion or "predicciones" not in pred_produccion:
            return []

        demanda_por_fecha: dict[str, float] = defaultdict(float)
        for tipo, pred in pred_por_destino.items():
            if "predicciones" not in pred:
                continue
            for p in pred["predicciones"]:
                demanda_por_fecha[p["fecha"]] += p["demanda_estimada"]

        balance = []
        for p in pred_produccion["predicciones"]:
            fecha      = p["fecha"]
            produccion = p["produccion_necesaria"]
            demanda    = round(demanda_por_fecha.get(fecha, 0.0), 2)
            diferencia = round(produccion - demanda, 2)
            balance.append({
                "fecha":                  fecha,
                "produccion_esperada":    produccion,
                "demanda_total_esperada": demanda,
                "balance":                diferencia,
                "estado":                 "superávit" if diferencia >= 0 else "déficit",
            })

        return balance

    # ── Método principal por especie ──────────────────────────────────────────

    def predecir_especie(self, clave: str, dias_futuro: int) -> dict:
        if clave not in ESPECIES:
            return {"error": f"Especie '{clave}' no reconocida."}

        cfg_esp = ESPECIES[clave]
        usar_semanas = cfg_esp.get("agregar_semanal", False)

        modelo = self._cargar_modelo(clave)
        if not modelo:
            return {
                "error": (
                    "El modelo aún no ha sido entrenado. "
                    "Usa el botón de entrenamiento para generarlo."
                )
            }

        info_modelo = self._info_modelo(clave)
        config      = self._config_especie(clave)
        comparativa = self._comparativa_algoritmos(clave)

        rango_meses = config.get("rango_meses", 6)
        desde       = date.today() - timedelta(days=rango_meses * 30)

        prod_registros = getattr(self.repo, cfg_esp["list_prod"])(desde, None)
        if len(prod_registros) < 2:
            return {"error": "No hay suficientes datos históricos de producción (mínimo 2)."}

        # Ordenar ascendente por fecha (el repo devuelve desc)
        prod_registros  = sorted(prod_registros, key=lambda r: r.fecha)
        fechas_prod     = [r.fecha    for r in prod_registros]
        cantidades_prod = [r.cantidad for r in prod_registros]

        pred_produccion = self._predecir(
            modelo,
            fechas_prod,
            cantidades_prod,
            dias_futuro,
            agregar_semanal=usar_semanas,
        )

        salidas = getattr(self.repo, cfg_esp["list_salidas"])(desde, None)
        salidas = sorted(salidas, key=lambda s: s.fecha)

        pred_por_destino = self._predecir_por_destino(
            modelo          = modelo,
            salidas         = salidas,
            tipos_salida    = cfg_esp["tipos_salida"],
            dias_futuro     = dias_futuro,
            es_galleria     = (clave == "galleria"),
            agregar_semanal = usar_semanas,
        )

        balance = self._calcular_balance(pred_produccion, pred_por_destino)

        return {
            "especie":           cfg_esp["nombre"],
            "unidad":            cfg_esp["unidad"],
            "auto_train_activo": config.get("activo", False),
            "rango_meses":       rango_meses,
            "agregacion":        "semanal" if usar_semanas else "diaria",
            "modelo_info": {
                "tipo":         "Ensemble (LinearRegression + Ridge + SVR + Holt-Winters)",
                "r2_score":     info_modelo.get("r2_score"),
                "mae":          info_modelo.get("mae"),
                "rmse":         info_modelo.get("rmse"),
                "n_registros":  info_modelo.get("n_registros"),
                "entrenado_en": str(info_modelo.get("entrenado_en", "")),
            },
            "comparativa_algoritmos":  comparativa,
            "prediccion_produccion":   pred_produccion,
            "prediccion_por_destino":  pred_por_destino,
            "balance":                 balance,
        }

    # ── Todas las especies ────────────────────────────────────────────────────

    def predecir_todas(self, dias_futuro: int) -> dict:
        return _sanitizar({
            clave: self.predecir_especie(clave, dias_futuro)
            for clave in ESPECIES
        })

    # ── Métodos individuales (compatibilidad con router) ──────────────────────

    def predecir_sitotroga(self, dias_futuro: int) -> dict:
        return _sanitizar(self.predecir_especie("sitotroga", dias_futuro))

    def predecir_trichogramma(self, dias_futuro: int) -> dict:
        return _sanitizar(self.predecir_especie("trichogramma", dias_futuro))

    def predecir_galleria(self, dias_futuro: int) -> dict:
        return _sanitizar(self.predecir_especie("galleria", dias_futuro))

    def predecir_paratheresia(self, dias_futuro: int) -> dict:
        return _sanitizar(self.predecir_especie("paratheresia", dias_futuro))
