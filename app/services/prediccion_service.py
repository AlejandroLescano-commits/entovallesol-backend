from sqlalchemy.orm import Session
from datetime import date, timedelta
from typing import Optional
import numpy as np
from sklearn.linear_model import LinearRegression
from app.infrastructure.repositories.produccion_repository import ProduccionRepository


class PrediccionService:
    def __init__(self, db: Session):
        self.repo = ProduccionRepository(db)

    # ── Método central de predicción ──────────────────────────────────────────
    def _predecir(self, fechas: list, cantidades: list, dias_futuro: int) -> dict:
        """
        Recibe listas de fechas y cantidades históricas.
        Devuelve predicción de demanda y producción necesaria para los próximos días.
        """
        if len(cantidades) < 2:
            return {"error": "No hay suficientes datos históricos para predecir (mínimo 2 registros)."}

        # Convertir fechas a número ordinal para regresión
        X = np.array([d.toordinal() for d in fechas]).reshape(-1, 1)
        y = np.array(cantidades, dtype=float)

        modelo = LinearRegression()
        modelo.fit(X, y)

        # Generar predicciones para los próximos N días
        hoy = date.today()
        fechas_futuras = [hoy + timedelta(days=i+1) for i in range(dias_futuro)]
        X_futuro = np.array([d.toordinal() for d in fechas_futuras]).reshape(-1, 1)
        predicciones = modelo.predict(X_futuro)

        # Producción necesaria = predicción + 10% de margen de seguridad
        produccion_necesaria = [round(max(0, p * 1.1), 2) for p in predicciones]
        demanda_predicha = [round(max(0, p), 2) for p in predicciones]

        return {
            "r2_score": round(modelo.score(X, y), 4),
            "dias_predichos": dias_futuro,
            "predicciones": [
                {
                    "fecha": str(f),
                    "demanda_estimada": d,
                    "produccion_necesaria": p,
                }
                for f, d, p in zip(fechas_futuras, demanda_predicha, produccion_necesaria)
            ],
            "tendencia": "creciente" if modelo.coef_[0] > 0 else "decreciente",
            "promedio_historico": round(float(np.mean(y)), 2),
        }

    # ── Sitotroga ─────────────────────────────────────────────────────────────
    def predecir_sitotroga(self, dias_futuro: int) -> dict:
        registros = self.repo.list_sitotroga(None, None)
        if not registros:
            return {"error": "Sin datos históricos de sitotroga."}
        fechas = [r.fecha for r in registros]
        cantidades = [r.cantidad for r in registros]
        resultado = self._predecir(fechas, cantidades, dias_futuro)
        resultado["especie"] = "Sitotroga cerealella"
        resultado["unidad"] = "gramos"
        return resultado

    # ── Trichogramma ──────────────────────────────────────────────────────────
    def predecir_trichogramma(self, dias_futuro: int) -> dict:
        registros = self.repo.list_trichogramma(None, None)
        if not registros:
            return {"error": "Sin datos históricos de trichogramma."}
        fechas = [r.fecha for r in registros]
        cantidades = [r.cantidad for r in registros]
        resultado = self._predecir(fechas, cantidades, dias_futuro)
        resultado["especie"] = "Trichogramma"
        resultado["unidad"] = "pulgadas"
        return resultado

    # ── Galleria ──────────────────────────────────────────────────────────────
    def predecir_galleria(self, dias_futuro: int) -> dict:
        registros = self.repo.list_galleria(None, None)
        if not registros:
            return {"error": "Sin datos históricos de galleria."}
        fechas = [r.fecha for r in registros]
        cantidades = [r.cantidad for r in registros]
        resultado = self._predecir(fechas, cantidades, dias_futuro)
        resultado["especie"] = "Galleria melonella"
        resultado["unidad"] = "unidades"
        return resultado

    # ── Paratheresia ──────────────────────────────────────────────────────────
    def predecir_paratheresia(self, dias_futuro: int) -> dict:
        registros = self.repo.list_paratheresia(None, None)
        if not registros:
            return {"error": "Sin datos históricos de paratheresia."}
        fechas = [r.fecha for r in registros]
        cantidades = [r.cantidad for r in registros]
        resultado = self._predecir(fechas, cantidades, dias_futuro)
        resultado["especie"] = "Paratheresia claripalpis"
        resultado["unidad"] = "parejas"
        return resultado

    # ── Todas juntas ──────────────────────────────────────────────────────────
    def predecir_todas(self, dias_futuro: int) -> dict:
        return {
            "sitotroga":    self.predecir_sitotroga(dias_futuro),
            "trichogramma": self.predecir_trichogramma(dias_futuro),
            "galleria":     self.predecir_galleria(dias_futuro),
            "paratheresia": self.predecir_paratheresia(dias_futuro),
        }