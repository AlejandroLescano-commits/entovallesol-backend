# app/services/entrenamiento_service.py
import hashlib
import io
import math
from datetime import date, timedelta
from typing import Optional
import joblib
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import TimeSeriesSplit
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.services.prediccion_service import _agregar_semanal

ESPECIES_CONFIG = {
    "sitotroga":    {"list_fn": "list_sitotroga",    "agregar_semanal": False, "modelo_ciclico": False},
    "trichogramma": {"list_fn": "list_trichogramma", "agregar_semanal": False, "modelo_ciclico": False},
    # FIX: agregar_semanal=True para que el entrenamiento sea consistente con la predicción
    "galleria":     {"list_fn": "list_galleria",     "agregar_semanal": True,  "modelo_ciclico": True},
    "paratheresia": {"list_fn": "list_paratheresia",  "agregar_semanal": False, "modelo_ciclico": False},
}

ENSEMBLE_PESOS_DEFAULT = {
    "linear":      0.20,
    "ridge":       0.30,
    "svr":         0.30,
    "holtwinters": 0.20,
}

ENSEMBLE_CICLICO_PESOS_DEFAULT = {
    "fourier_ridge": 0.35,
    "holtwinters2":  0.35,
    "svr_ciclico":   0.30,
}

# Mínimo de registros recomendado para que los pesos de CV sean confiables
MIN_REGISTROS_CV_CONFIABLE = 30


def _safe(v) -> Optional[float]:
    if v is None:
        return None
    f = float(v)
    return None if (math.isnan(f) or math.isinf(f)) else round(f, 4)

def _rmse(y_true, y_pred) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


# ── Modelo Fourier + Ridge ────────────────────────────────────────────────────
class _FourierRidgeWrapper:
    """
    Transforma el índice ordinal relativo en features de Fourier para capturar
    ciclos de período configurable, luego aplica Ridge.
    Ideal para patrones alto/bajo alternantes como Galleria.
    """
    def __init__(self, periodos: list[int] = None):
        self.periodos = periodos or [2, 7, 14]
        self._pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("model",  Ridge(alpha=1.0)),
        ])
        self.coef_ = [0.0]

    def _features(self, X: np.ndarray) -> np.ndarray:
        """Genera features seno/coseno para cada período."""
        t = X.flatten().astype(float)
        cols = [t]  # incluir el índice lineal también
        for p in self.periodos:
            cols.append(np.sin(2 * np.pi * t / p))
            cols.append(np.cos(2 * np.pi * t / p))
        return np.column_stack(cols)

    def fit(self, X, y):
        Xf = self._features(X)
        self._pipeline.fit(Xf, y)
        try:
            inner = self._pipeline.named_steps["model"]
            self.coef_ = [float(inner.coef_[0])]
        except Exception:
            self.coef_ = [0.0]
        return self

    def predict(self, X):
        Xf = self._features(X)
        return self._pipeline.predict(Xf)

    def score(self, X, y):
        y_pred = self.predict(X)
        ss_res = np.sum((np.array(y) - y_pred) ** 2)
        ss_tot = np.sum((np.array(y) - np.mean(y)) ** 2)
        if ss_tot == 0:
            return 1.0
        return float(1 - ss_res / ss_tot)


# ── Holt-Winters con estacionalidad explícita ─────────────────────────────────
class _HoltWinters2Wrapper:
    """
    Holt-Winters con período estacional = 2 para capturar el ciclo
    alto/bajo alternante de Galleria.

    FIX: score() ya no cae a predecir la media cuando fittedvalues tiene
    dimensión distinta a X — usa directamente los valores ajustados del modelo.
    """
    def __init__(self, seasonal_periods: int = 2):
        self.seasonal_periods = seasonal_periods
        self._model   = None
        self._fit_len = 0
        self.coef_    = [0.0]

    def fit(self, X, y):
        n = len(y)
        # Necesitamos al menos 2 ciclos completos
        if n >= self.seasonal_periods * 2:
            try:
                hw = ExponentialSmoothing(
                    y,
                    trend="add",
                    seasonal="add",
                    seasonal_periods=self.seasonal_periods,
                    initialization_method="estimated",
                ).fit(optimized=True)
            except Exception:
                hw = ExponentialSmoothing(
                    y,
                    trend=None,
                    seasonal="add",
                    seasonal_periods=self.seasonal_periods,
                    initialization_method="heuristic",
                ).fit(optimized=True)
        else:
            # Fallback sin estacionalidad si hay muy pocos datos
            hw = ExponentialSmoothing(
                y,
                trend="add" if n >= 4 else None,
                seasonal=None,
                initialization_method="estimated",
            ).fit(optimized=True)

        self._model   = hw
        self._fit_len = n
        if n >= 2:
            preds_hist = hw.fittedvalues
            self.coef_ = [float(preds_hist.iloc[-1] - preds_hist.iloc[0]) / max(n - 1, 1)]
        return self

    def predict(self, X):
        steps    = len(X)
        forecast = self._model.forecast(steps)
        return np.array(forecast)

    def score(self, X, y):
        # FIX: usar fittedvalues del modelo (dimensión == len(y) siempre),
        # NO intentar alinear con len(X) que puede diferir.
        fitted = np.array(self._model.fittedvalues)
        y_arr  = np.array(y)
        # Si por alguna razón la dimensión no coincide, recortamos al mínimo
        n = min(len(fitted), len(y_arr))
        fitted = fitted[:n]
        y_arr  = y_arr[:n]
        ss_res = np.sum((y_arr - fitted) ** 2)
        ss_tot = np.sum((y_arr - np.mean(y_arr)) ** 2)
        if ss_tot == 0:
            return 1.0
        return float(1 - ss_res / ss_tot)


# ── SVR con features cíclicas ─────────────────────────────────────────────────
class _SVRCiclicoWrapper:
    """SVR con features de Fourier para capturar patrones cíclicos."""
    def __init__(self, periodos: list[int] = None):
        self.periodos = periodos or [2, 7, 14]
        self._pipeline = Pipeline([
            ("scaler", StandardScaler()),
            ("model",  SVR(kernel="rbf", C=100, epsilon=0.1)),
        ])
        self.coef_ = [0.0]

    def _features(self, X: np.ndarray) -> np.ndarray:
        t = X.flatten().astype(float)
        cols = [t]
        for p in self.periodos:
            cols.append(np.sin(2 * np.pi * t / p))
            cols.append(np.cos(2 * np.pi * t / p))
        return np.column_stack(cols)

    def fit(self, X, y):
        Xf = self._features(X)
        self._pipeline.fit(Xf, y)
        return self

    def predict(self, X):
        Xf = self._features(X)
        return self._pipeline.predict(Xf)

    def score(self, X, y):
        y_pred = self.predict(X)
        ss_res = np.sum((np.array(y) - y_pred) ** 2)
        ss_tot = np.sum((np.array(y) - np.mean(y)) ** 2)
        if ss_tot == 0:
            return 1.0
        return float(1 - ss_res / ss_tot)


# ── Wrapper Holt-Winters estándar (para EnsembleModel normal) ─────────────────
class _HoltWintersWrapper:
    """
    FIX: score() usa fittedvalues del modelo (no intenta alinear con len(X)),
    evitando que el R² sea artificialmente 0 cuando las dimensiones no coinciden.
    """
    def __init__(self):
        self._model   = None
        self._fit_len = 0
        self.coef_    = [0.0]

    def fit(self, X, y):
        n        = len(y)
        trend    = "add" if n >= 4 else None
        seasonal = None
        try:
            hw = ExponentialSmoothing(
                y,
                trend=trend,
                seasonal=seasonal,
                initialization_method="estimated",
            ).fit(optimized=True)
        except Exception:
            hw = ExponentialSmoothing(
                y,
                trend=None,
                seasonal=None,
                initialization_method="estimated",
            ).fit(optimized=True)
        self._model   = hw
        self._fit_len = n
        if n >= 2:
            preds_hist = hw.fittedvalues
            self.coef_ = [float(preds_hist.iloc[-1] - preds_hist.iloc[0]) / max(n - 1, 1)]
        return self

    def predict(self, X):
        steps    = len(X)
        forecast = self._model.forecast(steps)
        return np.array(forecast)

    def score(self, X, y):
        # FIX: usar siempre fittedvalues (dimensión == len(y)),
        # recortando al mínimo si hay discrepancia residual.
        fitted = np.array(self._model.fittedvalues)
        y_arr  = np.array(y)
        n      = min(len(fitted), len(y_arr))
        fitted = fitted[:n]
        y_arr  = y_arr[:n]
        ss_res = np.sum((y_arr - fitted) ** 2)
        ss_tot = np.sum((y_arr - np.mean(y_arr)) ** 2)
        if ss_tot == 0:
            return 1.0
        return float(1 - ss_res / ss_tot)


# ── Ensemble estándar (Sitotroga, Trichogramma, Paratheresia) ─────────────────
class EnsembleModel:
    def __init__(self):
        self.modelos:  dict = {}
        self.pesos:    dict = {}
        self.metricas: dict = {}
        self.coef_     = [0.0]
        # FIX: guardar la base ordinal para reconstruir X relativo en predicción
        self.base_ordinal: int = 0

    def fit(self, X: np.ndarray, y: np.ndarray, base_ordinal: int = 0):
        # Guardar la base para que predict pueda recibir fechas absolutas si es necesario
        self.base_ordinal = base_ordinal

        candidatos = {
            "linear":      LinearRegression(),
            "ridge":       Pipeline([
                               ("scaler", StandardScaler()),
                               ("model",  Ridge(alpha=1.0)),
                           ]),
            "svr":         Pipeline([
                               ("scaler", StandardScaler()),
                               ("model",  SVR(kernel="rbf", C=100, epsilon=0.1)),
                           ]),
            "holtwinters": _HoltWintersWrapper(),
        }
        n = len(y)
        # FIX: mínimo 3 splits para estimaciones de CV más robustas
        n_splits = min(5, max(3, n // 10))
        tscv     = TimeSeriesSplit(n_splits=n_splits)
        rmse_cv: dict[str, list[float]] = {k: [] for k in candidatos}
        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            if len(y_train) < 2:
                continue
            for nombre, modelo in candidatos.items():
                try:
                    modelo.fit(X_train, y_train)
                    y_pred_val = modelo.predict(X_val)
                    rmse_cv[nombre].append(_rmse(y_val, y_pred_val))
                except Exception:
                    rmse_cv[nombre].append(float("inf"))
        for nombre, modelo in candidatos.items():
            try:
                modelo.fit(X, y)
            except Exception:
                pass
        self.modelos = candidatos
        for nombre, modelo in candidatos.items():
            try:
                y_pred = modelo.predict(X)
                r2_v   = modelo.score(X, y)
                self.metricas[nombre] = {
                    "r2":   _safe(r2_v),
                    "mae":  _safe(mean_absolute_error(y, y_pred)),
                    "rmse": _safe(_rmse(y, y_pred)),
                    "rmse_cv_promedio": _safe(
                        float(np.mean(rmse_cv[nombre]))
                        if rmse_cv[nombre] and not any(math.isinf(v) for v in rmse_cv[nombre])
                        else None
                    ),
                }
            except Exception:
                self.metricas[nombre] = {"r2": None, "mae": None, "rmse": None, "rmse_cv_promedio": None}
        rmse_promedios = {}
        for nombre in candidatos:
            vals = [v for v in rmse_cv[nombre] if not math.isinf(v) and not math.isnan(v)]
            rmse_promedios[nombre] = float(np.mean(vals)) if vals else float("inf")
        if all(math.isinf(v) for v in rmse_promedios.values()):
            self.pesos = ENSEMBLE_PESOS_DEFAULT.copy()
        else:
            inv = {}
            for k, v in rmse_promedios.items():
                inv[k] = 1.0 / v if not math.isinf(v) and v > 0 else 0.0
            total = sum(inv.values())
            if total == 0:
                self.pesos = ENSEMBLE_PESOS_DEFAULT.copy()
            else:
                self.pesos = {k: round(v / total, 4) for k, v in inv.items()}
        try:
            lr = self.modelos["linear"]
            if hasattr(lr, "coef_"):
                self.coef_ = [float(lr.coef_[0])]
            else:
                inner = lr.named_steps.get("model", lr)
                self.coef_ = [float(inner.coef_[0])] if hasattr(inner, "coef_") else [0.0]
        except Exception:
            self.coef_ = [0.0]
        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        predicciones = []
        pesos_usados = []
        for nombre, modelo in self.modelos.items():
            try:
                pred  = modelo.predict(X)
                peso  = self.pesos.get(nombre, 0.0)
                predicciones.append(pred * peso)
                pesos_usados.append(peso)
            except Exception:
                pass
        if not predicciones:
            return np.zeros(len(X))
        total_peso = sum(pesos_usados)
        resultado  = np.sum(predicciones, axis=0)
        if total_peso > 0 and abs(total_peso - 1.0) > 1e-6:
            resultado = resultado / total_peso
        return resultado

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        if ss_tot == 0:
            return 1.0
        return float(1 - ss_res / ss_tot)


# ── Ensemble cíclico (Galleria) ───────────────────────────────────────────────
class EnsembleCiclicoModel:
    """
    Ensemble especializado para especies con producción cíclica (Galleria).
    Usa Fourier+Ridge, Holt-Winters con período=2 y SVR con features cíclicas.
    """
    def __init__(self, periodos_fourier: list[int] = None):
        self.periodos_fourier = periodos_fourier or [2, 7, 14]
        self.modelos:  dict = {}
        self.pesos:    dict = {}
        self.metricas: dict = {}
        self.coef_     = [0.0]
        # FIX: guardar la base ordinal para reconstruir X relativo en predicción
        self.base_ordinal: int = 0

    def fit(self, X: np.ndarray, y: np.ndarray, base_ordinal: int = 0):
        self.base_ordinal = base_ordinal

        candidatos = {
            "fourier_ridge": _FourierRidgeWrapper(periodos=self.periodos_fourier),
            "holtwinters2":  _HoltWinters2Wrapper(seasonal_periods=2),
            "svr_ciclico":   _SVRCiclicoWrapper(periodos=self.periodos_fourier),
        }
        n        = len(y)
        # FIX: mínimo 3 splits
        n_splits = min(5, max(3, n // 10))
        tscv     = TimeSeriesSplit(n_splits=n_splits)
        rmse_cv: dict[str, list[float]] = {k: [] for k in candidatos}

        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            if len(y_train) < 4:
                continue
            for nombre, modelo in candidatos.items():
                try:
                    modelo.fit(X_train, y_train)
                    y_pred_val = modelo.predict(X_val)
                    rmse_cv[nombre].append(_rmse(y_val, y_pred_val))
                except Exception:
                    rmse_cv[nombre].append(float("inf"))

        for nombre, modelo in candidatos.items():
            try:
                modelo.fit(X, y)
            except Exception:
                pass

        self.modelos = candidatos

        for nombre, modelo in candidatos.items():
            try:
                y_pred = modelo.predict(X)
                r2_v   = modelo.score(X, y)
                self.metricas[nombre] = {
                    "r2":   _safe(r2_v),
                    "mae":  _safe(mean_absolute_error(y, y_pred)),
                    "rmse": _safe(_rmse(y, y_pred)),
                    "rmse_cv_promedio": _safe(
                        float(np.mean(rmse_cv[nombre]))
                        if rmse_cv[nombre] and not any(math.isinf(v) for v in rmse_cv[nombre])
                        else None
                    ),
                }
            except Exception:
                self.metricas[nombre] = {"r2": None, "mae": None, "rmse": None, "rmse_cv_promedio": None}

        # Pesos inversamente proporcionales al RMSE de CV
        rmse_promedios = {}
        for nombre in candidatos:
            vals = [v for v in rmse_cv[nombre] if not math.isinf(v) and not math.isnan(v)]
            rmse_promedios[nombre] = float(np.mean(vals)) if vals else float("inf")

        if all(math.isinf(v) for v in rmse_promedios.values()):
            self.pesos = ENSEMBLE_CICLICO_PESOS_DEFAULT.copy()
        else:
            inv = {}
            for k, v in rmse_promedios.items():
                inv[k] = 1.0 / v if not math.isinf(v) and v > 0 else 0.0
            total = sum(inv.values())
            self.pesos = (
                {k: round(v / total, 4) for k, v in inv.items()}
                if total > 0
                else ENSEMBLE_CICLICO_PESOS_DEFAULT.copy()
            )

        try:
            self.coef_ = self.modelos["fourier_ridge"].coef_
        except Exception:
            self.coef_ = [0.0]

        return self

    def predict(self, X: np.ndarray) -> np.ndarray:
        predicciones = []
        pesos_usados = []
        for nombre, modelo in self.modelos.items():
            try:
                pred = modelo.predict(X)
                peso = self.pesos.get(nombre, 0.0)
                predicciones.append(pred * peso)
                pesos_usados.append(peso)
            except Exception:
                pass
        if not predicciones:
            return np.zeros(len(X))
        total_peso = sum(pesos_usados)
        resultado  = np.sum(predicciones, axis=0)
        if total_peso > 0 and abs(total_peso - 1.0) > 1e-6:
            resultado = resultado / total_peso
        return resultado

    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        if ss_tot == 0:
            return 1.0
        return float(1 - ss_res / ss_tot)


class EntrenamientoService:
    def __init__(self, db: Session):
        self.db = db

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
        """Serializa y persiste el modelo. No hace commit — se delega a entrenar_especie."""
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
            "r2":   metricas["ensemble"]["r2"],
            "mae":  metricas["ensemble"]["mae"],
            "rmse": metricas["ensemble"]["rmse"],
            "n":    n,
        })

    def _insertar_log(
        self,
        especie:     str,
        metricas:    dict,
        n:           int,
        reemplazado: bool,
        motivo:      Optional[str],
    ):
        import json
        self.db.execute(text("""
            INSERT INTO modelo_log
                (especie, r2_score, mae, rmse, n_registros,
                 fue_reemplazado, motivo_rechazo, detalle_algoritmos, entrenado_en)
            VALUES
                (:e, :r2, :mae, :rmse, :n, :r, :m, :det, NOW())
        """), {
            "e":   especie,
            "r2":  metricas["ensemble"]["r2"],
            "mae": metricas["ensemble"]["mae"],
            "rmse": metricas["ensemble"]["rmse"],
            "n":   n,
            "r":   reemplazado,
            "m":   motivo,
            "det": json.dumps(metricas),
        })

    def _actualizar_config_post_entreno(self, especie: str, nuevo_hash: str, r2: float):
        self.db.execute(text("""
            UPDATE modelo_config
            SET ultimo_hash     = :h,
                ultimo_r2       = :r2,
                ultimo_entreno  = NOW(),
                proximo_entreno = NOW() + INTERVAL '1 day'
            WHERE especie = :e
        """), {"h": nuevo_hash, "r2": r2, "e": especie})

    def get_kpis(self, especie: str) -> list:
        rows = self.db.execute(text("""
            SELECT r2_score, mae, rmse, n_registros,
                   fue_reemplazado, motivo_rechazo, entrenado_en,
                   detalle_algoritmos
            FROM modelo_log
            WHERE especie = :e
            ORDER BY entrenado_en DESC
            LIMIT 30
        """), {"e": especie}).mappings().all()
        return [dict(r) for r in rows]

    def entrenar_especie(self, clave: str, forzar: bool = False) -> dict:
        from app.infrastructure.repositories.produccion_repository import ProduccionRepository
        repo = ProduccionRepository(self.db)

        cfg = self._get_config(clave)
        if not cfg:
            return {"saltado": True, "motivo": "Especie no configurada"}
        if not forzar and not cfg["activo"]:
            return {"saltado": True, "motivo": "Auto-train desactivado"}

        desde     = date.today() - timedelta(days=cfg["rango_meses"] * 30)
        list_fn   = ESPECIES_CONFIG[clave]["list_fn"]
        registros = getattr(repo, list_fn)(desde, None)

        if len(registros) < 2:
            return {
                "saltado": True,
                "motivo":  f"Solo {len(registros)} registros en el rango "
                           f"({cfg['rango_meses']} meses). Mínimo 2.",
            }

        # Ordenar ascendente por fecha
        registros  = sorted(registros, key=lambda r: r.fecha)
        fechas     = [r.fecha    for r in registros]
        cantidades = [r.cantidad for r in registros]

        # Agregación semanal si corresponde (ej: Galleria)
        if ESPECIES_CONFIG[clave].get("agregar_semanal"):
            fechas, cantidades = _agregar_semanal(fechas, cantidades)
            if len(fechas) >= 2:
                gaps  = [(fechas[i] - fechas[i-1]).days for i in range(1, len(fechas))]
                corte = None
                for i, g in enumerate(gaps):
                    if g > 60:
                        corte = i + 1
                if corte is not None:
                    fechas     = fechas[corte:]
                    cantidades = cantidades[corte:]

        if len(fechas) < 2:
            return {
                "saltado": True,
                "motivo":  f"Solo {len(fechas)} puntos tras agregación. Mínimo 2.",
            }

        nuevo_hash = hashlib.md5(
            str(sorted(zip([str(f) for f in fechas], cantidades))).encode()
        ).hexdigest()
        if not forzar and cfg.get("ultimo_hash") == nuevo_hash:
            return {"saltado": True, "motivo": "Sin datos nuevos desde el último entrenamiento"}

        # FIX: índice ordinal relativo — base en el primer dato histórico.
        # El modelo siempre ve X en [0, N], nunca valores absolutos ~739_000.
        base_ordinal = fechas[0].toordinal()
        X = np.array([d.toordinal() - base_ordinal for d in fechas]).reshape(-1, 1)
        y = np.array(cantidades, dtype=float)

        # Elegir ensemble según la especie
        es_ciclico = ESPECIES_CONFIG[clave].get("modelo_ciclico", False)
        if es_ciclico:
            ensemble = EnsembleCiclicoModel()
        else:
            ensemble = EnsembleModel()

        # FIX: pasar base_ordinal al fit para que quede guardado en el modelo
        ensemble.fit(X, y, base_ordinal=base_ordinal)
        y_pred_ens = ensemble.predict(X)

        metricas = {
            "ensemble": {
                "r2":   _safe(ensemble.score(X, y)),
                "mae":  _safe(mean_absolute_error(y, y_pred_ens)),
                "rmse": _safe(_rmse(y, y_pred_ens)),
            },
            "algoritmos": ensemble.metricas,
            "pesos":       ensemble.pesos,
            "tipo":        "ciclico" if es_ciclico else "estandar",
            # Advertencia si los datos son insuficientes para CV confiable
            "advertencia_cv": (
                f"Solo {len(fechas)} registros — pesos de CV pueden tener alta varianza. "
                f"Se recomiendan ≥{MIN_REGISTROS_CV_CONFIABLE} para mayor robustez."
            ) if len(fechas) < MIN_REGISTROS_CV_CONFIABLE else None,
        }

        if metricas["ensemble"]["r2"] is None:
            return {
                "saltado": True,
                "motivo":  "R² indefinido (datos insuficientes para evaluar el modelo)",
            }

        fue_reemplazado = True
        motivo_rechazo  = None
        r2_anterior     = cfg.get("ultimo_r2")
        if not forzar and r2_anterior is not None:
            r2_nuevo = metricas["ensemble"]["r2"]
            if r2_nuevo < r2_anterior - 0.02:
                fue_reemplazado = False
                motivo_rechazo  = (
                    f"R² ensemble nuevo {r2_nuevo} < R² actual {r2_anterior} (umbral −0.02)"
                )

        if fue_reemplazado:
            self._guardar_modelo(clave, ensemble, metricas, len(fechas))
            self._actualizar_config_post_entreno(
                clave, nuevo_hash, metricas["ensemble"]["r2"]
            )
        self._insertar_log(clave, metricas, len(fechas), fue_reemplazado, motivo_rechazo)
        self.db.commit()

        mejor_algo = min(
            ensemble.metricas,
            key=lambda k: ensemble.metricas[k].get("rmse") or float("inf"),
        )
        return {
            "entrenado":         True,
            "fue_reemplazado":   fue_reemplazado,
            "motivo_rechazo":    motivo_rechazo,
            "n_registros":       len(fechas),
            "advertencia_cv":    metricas.get("advertencia_cv"),
            "ensemble": {
                "r2_score": metricas["ensemble"]["r2"],
                "mae":      metricas["ensemble"]["mae"],
                "rmse":     metricas["ensemble"]["rmse"],
            },
            "mejor_algoritmo_individual": mejor_algo,
            "comparativa_algoritmos":     ensemble.metricas,
            "pesos_ensemble":             ensemble.pesos,
        }

    def entrenar_todas(self, forzar: bool = False) -> dict:
        return {
            clave: self.entrenar_especie(clave, forzar=forzar)
            for clave in ESPECIES_CONFIG
        }
