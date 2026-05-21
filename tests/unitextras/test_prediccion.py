"""
test_prediccion.py – Pruebas Unitarias del módulo de Predicción
EntoValleSOL Backend

Casos cubiertos:
  CA01 – _sanitizar()  (nan, inf, None, estructuras anidadas)
  CA02 – PrediccionService._predecir()  (resultado, tendencias, r2)
  CA03 – PrediccionService._predecir_por_destino()  (insuficientes, galleria ratio)
  CA04 – PrediccionService._calcular_balance()  (superávit, déficit, vacío)
  CA05 – PrediccionService.predecir_especie()  (especie inválida, sin modelo, sin datos)
  CA06 – PrediccionService.predecir_todas()

Ejecutar:
  pytest tests/unit/test_prediccion.py -v
"""
import math
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch, PropertyMock

import numpy as np
from sklearn.linear_model import LinearRegression


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _make_modelo(coef=1.0, intercept=0.0):
    """Crea un modelo LinearRegression pre-entrenado con datos sintéticos."""
    X = np.array([[1], [2], [3], [4], [5]])
    y = np.array([10, 20, 30, 40, 50], dtype=float)
    m = LinearRegression().fit(X, y)
    return m


def _make_registro(fecha: date, cantidad: float, tiposalida: str = None, ratio: float = None):
    r = MagicMock()
    r.fecha      = fecha
    r.cantidad   = cantidad
    r.tiposalida = tiposalida
    r.ratio      = ratio
    return r


def _make_service(mock_db):
    from app.services.prediccion_service import PrediccionService
    svc = PrediccionService.__new__(PrediccionService)
    svc.db   = mock_db
    svc.repo = MagicMock()
    return svc


# ═══════════════════════════════════════════════════════════════════════════════
# CA01 – _sanitizar
# ═══════════════════════════════════════════════════════════════════════════════

class TestSanitizar:
    """CA01: La función _sanitizar convierte nan/inf a None."""

    def test_nan_float_retorna_none(self):
        """CA01-1: float nan debe convertirse a None."""
        from app.services.prediccion_service import _sanitizar
        assert _sanitizar(float("nan")) is None

    def test_inf_float_retorna_none(self):
        """CA01-2: float inf debe convertirse a None."""
        from app.services.prediccion_service import _sanitizar
        assert _sanitizar(float("inf")) is None

    def test_neg_inf_retorna_none(self):
        """CA01-3: float -inf debe convertirse a None."""
        from app.services.prediccion_service import _sanitizar
        assert _sanitizar(float("-inf")) is None

    def test_float_normal_no_cambia(self):
        """CA01-4: Float normal debe mantenerse igual."""
        from app.services.prediccion_service import _sanitizar
        assert _sanitizar(3.14) == pytest.approx(3.14)

    def test_none_no_cambia(self):
        """CA01-5: None debe mantenerse como None."""
        from app.services.prediccion_service import _sanitizar
        assert _sanitizar(None) is None

    def test_dict_anidado_sanitizado(self):
        """CA01-6: Diccionario con nan anidado debe convertirse correctamente."""
        from app.services.prediccion_service import _sanitizar
        resultado = _sanitizar({"r2": float("nan"), "valor": 1.5})
        assert resultado["r2"]    is None
        assert resultado["valor"] == pytest.approx(1.5)

    def test_lista_anidada_sanitizada(self):
        """CA01-7: Lista con nan y valores normales debe sanitizarse elemento a elemento."""
        from app.services.prediccion_service import _sanitizar
        resultado = _sanitizar([float("nan"), 2.0, float("inf")])
        assert resultado == [None, 2.0, None]

    def test_entero_pasa_sin_cambio(self):
        """CA01-8: Enteros no deben modificarse."""
        from app.services.prediccion_service import _sanitizar
        assert _sanitizar(42) == 42


# ═══════════════════════════════════════════════════════════════════════════════
# CA02 – PrediccionService._predecir
# ═══════════════════════════════════════════════════════════════════════════════

class TestPredecir:
    """CA02: Motor de predicción lineal."""

    def _fechas_cantidades(self, n=5):
        base = date(2025, 1, 1)
        fechas = [base + timedelta(days=i * 30) for i in range(n)]
        cantidades = [100.0 + i * 20 for i in range(n)]
        return fechas, cantidades

    def test_retorna_claves_esperadas(self, mock_db):
        """CA02-1: El resultado debe contener r2_score, predicciones, tendencia y promedio."""
        svc = _make_service(mock_db)
        modelo = _make_modelo()
        fechas, cantidades = self._fechas_cantidades()
        result = svc._predecir(modelo, fechas, cantidades, dias_futuro=3)
        for k in ["r2_score", "dias_predichos", "tendencia", "promedio_historico", "predicciones"]:
            assert k in result

    def test_cantidad_predicciones_igual_a_dias_futuro(self, mock_db):
        """CA02-2: Número de predicciones == dias_futuro."""
        svc    = _make_service(mock_db)
        modelo = _make_modelo()
        fechas, cantidades = self._fechas_cantidades()
        result = svc._predecir(modelo, fechas, cantidades, dias_futuro=7)
        assert len(result["predicciones"]) == 7

    def test_prediccion_contiene_fecha_demanda_produccion(self, mock_db):
        """CA02-3: Cada predicción debe tener fecha, demanda_estimada y produccion_necesaria."""
        svc    = _make_service(mock_db)
        modelo = _make_modelo()
        fechas, cantidades = self._fechas_cantidades()
        result = svc._predecir(modelo, fechas, cantidades, dias_futuro=2)
        p = result["predicciones"][0]
        assert "fecha"                in p
        assert "demanda_estimada"     in p
        assert "produccion_necesaria" in p

    def test_demanda_nunca_negativa(self, mock_db):
        """CA02-4: demanda_estimada nunca debe ser negativa (max con 0)."""
        svc = _make_service(mock_db)
        # Modelo decreciente que podría predecir valores negativos
        X = np.array([[1], [2], [3], [4], [5]])
        y = np.array([500, 400, 300, 200, 100], dtype=float)
        modelo = LinearRegression().fit(X, y)
        fechas     = [date(2025, 1, 1) + timedelta(days=i * 30) for i in range(5)]
        cantidades = [500, 400, 300, 200, 100]
        result = svc._predecir(modelo, fechas, cantidades, dias_futuro=30)
        assert all(p["demanda_estimada"] >= 0 for p in result["predicciones"])

    def test_produccion_necesaria_es_demanda_por_110pct(self, mock_db):
        """CA02-5: produccion_necesaria == demanda_estimada * 1.1 (margen de 10%)."""
        svc    = _make_service(mock_db)
        modelo = _make_modelo()
        fechas, cantidades = self._fechas_cantidades()
        result = svc._predecir(modelo, fechas, cantidades, dias_futuro=1)
        p = result["predicciones"][0]
        assert p["produccion_necesaria"] == pytest.approx(p["demanda_estimada"] * 1.1, rel=1e-3)

    def test_tendencia_creciente(self, mock_db):
        """CA02-6: Modelo con coeficiente positivo → tendencia 'creciente'."""
        svc    = _make_service(mock_db)
        modelo = _make_modelo(coef=1.0)
        fechas, cantidades = self._fechas_cantidades()
        result = svc._predecir(modelo, fechas, cantidades, dias_futuro=1)
        assert result["tendencia"] == "creciente"

    def test_tendencia_decreciente(self, mock_db):
        """CA02-7: Modelo con coeficiente negativo → tendencia 'decreciente'."""
        svc = _make_service(mock_db)
        X = np.array([[1], [2], [3], [4], [5]])
        y = np.array([500, 400, 300, 200, 100], dtype=float)
        modelo = LinearRegression().fit(X, y)
        fechas     = [date(2025, 1, 1) + timedelta(days=i * 30) for i in range(5)]
        cantidades = [500, 400, 300, 200, 100]
        result = svc._predecir(modelo, fechas, cantidades, dias_futuro=1)
        assert result["tendencia"] == "decreciente"


# ═══════════════════════════════════════════════════════════════════════════════
# CA03 – _predecir_por_destino
# ═══════════════════════════════════════════════════════════════════════════════

class TestPredecirPorDestino:
    """CA03: Predicción desagregada por tipo de salida."""

    def _modelo(self):
        return _make_modelo()

    def test_tipo_sin_datos_retorna_error(self, mock_db):
        """CA03-1: Tipo de salida con < 2 registros debe retornar dict con 'error'."""
        svc = _make_service(mock_db)
        salidas = [_make_registro(date(2025, 1, 1), 100.0, tiposalida="T.exiguum")]
        result  = svc._predecir_por_destino(self._modelo(), salidas, ["T.exiguum"], 5)
        assert "error" in result["T.exiguum"]

    def test_tipo_con_datos_suficientes_retorna_predicciones(self, mock_db):
        """CA03-2: Tipo con >= 2 registros debe retornar predicciones."""
        svc = _make_service(mock_db)
        salidas = [
            _make_registro(date(2025, 1, 1), 100.0, tiposalida="Ventas"),
            _make_registro(date(2025, 2, 1), 150.0, tiposalida="Ventas"),
            _make_registro(date(2025, 3, 1), 200.0, tiposalida="Ventas"),
        ]
        result = svc._predecir_por_destino(self._modelo(), salidas, ["Ventas"], 5)
        assert "predicciones" in result["Ventas"]
        assert len(result["Ventas"]["predicciones"]) == 5

    def test_galleria_paratheresia_aplica_ratio(self, mock_db):
        """CA03-3: Para Galleria/Paratheresia con ratio, la cantidad debe multiplicarse."""
        svc = _make_service(mock_db)
        salidas = [
            _make_registro(date(2025, 1, 1), 100.0, tiposalida="Paratheresia", ratio=0.5),
            _make_registro(date(2025, 2, 1), 200.0, tiposalida="Paratheresia", ratio=0.5),
            _make_registro(date(2025, 3, 1), 300.0, tiposalida="Paratheresia", ratio=0.5),
        ]
        # Con es_galleria=True, cantidad efectiva = cantidad * ratio
        result = svc._predecir_por_destino(
            self._modelo(), salidas, ["Paratheresia"], 5, es_galleria=True
        )
        assert "predicciones" in result["Paratheresia"]

    def test_multiples_tipos_en_resultado(self, mock_db):
        """CA03-4: Se deben retornar entradas para todos los tipos solicitados."""
        svc = _make_service(mock_db)
        tipos  = ["T.exiguum", "Ventas"]
        result = svc._predecir_por_destino(self._modelo(), [], tipos, 3)
        assert "T.exiguum" in result
        assert "Ventas"    in result

    def test_acumulacion_por_fecha(self, mock_db):
        """CA03-5: Varios registros en la misma fecha deben acumularse."""
        svc = _make_service(mock_db)
        salidas = [
            _make_registro(date(2025, 1, 1), 100.0, tiposalida="Ventas"),
            _make_registro(date(2025, 1, 1), 50.0,  tiposalida="Ventas"),  # misma fecha
            _make_registro(date(2025, 2, 1), 200.0, tiposalida="Ventas"),
        ]
        # Solo deben quedar 2 fechas únicas
        result = svc._predecir_por_destino(self._modelo(), salidas, ["Ventas"], 2)
        assert "predicciones" in result["Ventas"]


# ═══════════════════════════════════════════════════════════════════════════════
# CA04 – _calcular_balance
# ═══════════════════════════════════════════════════════════════════════════════

class TestCalcularBalance:
    """CA04: Balance producción vs demanda."""

    def _pred_produccion(self, fechas_cantidades):
        return {
            "predicciones": [
                {"fecha": str(f), "produccion_necesaria": c}
                for f, c in fechas_cantidades
            ]
        }

    def _pred_destino(self, tipo, fechas_cantidades):
        return {
            tipo: {
                "predicciones": [
                    {"fecha": str(f), "demanda_estimada": c}
                    for f, c in fechas_cantidades
                ]
            }
        }

    def test_superavit_cuando_produccion_mayor(self, mock_db):
        """CA04-1: produccion > demanda → estado 'superávit'."""
        svc = _make_service(mock_db)
        prod = self._pred_produccion([(date(2025, 6, 1), 500.0)])
        dest = self._pred_destino("Ventas", [(date(2025, 6, 1), 300.0)])
        balance = svc._calcular_balance(prod, dest)
        assert balance[0]["estado"] == "superávit"
        assert balance[0]["balance"] > 0

    def test_deficit_cuando_demanda_mayor(self, mock_db):
        """CA04-2: demanda > produccion → estado 'déficit'."""
        svc  = _make_service(mock_db)
        prod = self._pred_produccion([(date(2025, 6, 1), 100.0)])
        dest = self._pred_destino("Ventas", [(date(2025, 6, 1), 400.0)])
        balance = svc._calcular_balance(prod, dest)
        assert balance[0]["estado"] == "déficit"
        assert balance[0]["balance"] < 0

    def test_retorna_lista_vacia_sin_produccion(self, mock_db):
        """CA04-3: pred_produccion vacío retorna lista vacía."""
        svc     = _make_service(mock_db)
        balance = svc._calcular_balance({}, {})
        assert balance == []

    def test_demanda_acumula_multiples_tipos(self, mock_db):
        """CA04-4: La demanda total debe sumar todos los tipos de destino."""
        svc  = _make_service(mock_db)
        prod = self._pred_produccion([(date(2025, 6, 1), 1000.0)])
        dest = {
            "T.exiguum": {"predicciones": [{"fecha": "2025-06-01", "demanda_estimada": 200.0}]},
            "Ventas":    {"predicciones": [{"fecha": "2025-06-01", "demanda_estimada": 300.0}]},
        }
        balance = svc._calcular_balance(prod, dest)
        assert balance[0]["demanda_total_esperada"] == pytest.approx(500.0)

    def test_balance_retorna_n_entradas_igual_a_predicciones(self, mock_db):
        """CA04-5: La lista de balance tiene el mismo número de filas que las predicciones."""
        svc  = _make_service(mock_db)
        dias = [(date(2025, 6, i), 100.0) for i in range(1, 6)]
        prod = self._pred_produccion(dias)
        dest = {}
        balance = svc._calcular_balance(prod, dest)
        assert len(balance) == 5

    def test_equilibrio_exacto_es_superavit(self, mock_db):
        """CA04-6: Cuando producción == demanda, balance == 0 → superávit."""
        svc  = _make_service(mock_db)
        prod = self._pred_produccion([(date(2025, 6, 1), 300.0)])
        dest = self._pred_destino("Ventas", [(date(2025, 6, 1), 300.0)])
        balance = svc._calcular_balance(prod, dest)
        assert balance[0]["balance"] == pytest.approx(0.0)
        assert balance[0]["estado"] == "superávit"


# ═══════════════════════════════════════════════════════════════════════════════
# CA05 – predecir_especie
# ═══════════════════════════════════════════════════════════════════════════════

class TestPredecirEspecie:
    """CA05: Método principal por especie."""

    def test_especie_invalida_retorna_error(self, mock_db):
        """CA05-1: Clave desconocida debe retornar dict con 'error'."""
        svc = _make_service(mock_db)
        result = svc.predecir_especie("especie_falsa", 30)
        assert "error" in result

    def test_sin_modelo_retorna_error(self, mock_db):
        """CA05-2: Si no hay modelo entrenado, debe retornar dict con 'error'."""
        svc = _make_service(mock_db)
        svc._cargar_modelo    = MagicMock(return_value=None)
        svc._info_modelo      = MagicMock(return_value={})
        svc._config_especie   = MagicMock(return_value={})
        result = svc.predecir_especie("sitotroga", 30)
        assert "error" in result

    def test_sin_datos_historicos_retorna_error(self, mock_db):
        """CA05-3: Menos de 2 registros históricos → error."""
        svc = _make_service(mock_db)
        svc._cargar_modelo  = MagicMock(return_value=_make_modelo())
        svc._info_modelo    = MagicMock(return_value={})
        svc._config_especie = MagicMock(return_value={})
        svc.repo.list_sitotroga.return_value = [_make_registro(date(2025, 1, 1), 100.0)]
        result = svc.predecir_especie("sitotroga", 30)
        assert "error" in result

    def test_resultado_completo_con_datos_suficientes(self, mock_db, prod_records_sitotroga):
        """CA05-4: Con modelo y datos suficientes, el resultado contiene las claves esperadas."""
        svc = _make_service(mock_db)
        modelo = _make_modelo()
        svc._cargar_modelo  = MagicMock(return_value=modelo)
        svc._info_modelo    = MagicMock(return_value={"r2_score": 0.9, "mae": 5.0, "rmse": 6.0,
                                                       "n_registros": 3, "entrenado_en": "2025-01-01"})
        svc._config_especie = MagicMock(return_value={"activo": True, "rango_meses": 6})
        svc.repo.list_sitotroga.return_value     = prod_records_sitotroga
        svc.repo.list_notas_sitodroga.return_value = []

        result = svc.predecir_especie("sitotroga", 7)

        assert "especie"                  in result
        assert "prediccion_produccion"    in result
        assert "prediccion_por_destino"   in result
        assert "balance"                  in result

    def test_resultado_especie_nombre_correcto(self, mock_db, prod_records_sitotroga):
        """CA05-5: El nombre de la especie retornado debe coincidir con el configurado."""
        svc = _make_service(mock_db)
        svc._cargar_modelo  = MagicMock(return_value=_make_modelo())
        svc._info_modelo    = MagicMock(return_value={"r2_score": 0.9, "entrenado_en": ""})
        svc._config_especie = MagicMock(return_value={"activo": True, "rango_meses": 6})
        svc.repo.list_sitotroga.return_value       = prod_records_sitotroga
        svc.repo.list_notas_sitodroga.return_value = []

        result = svc.predecir_especie("sitotroga", 7)
        assert result["especie"] == "Sitotroga cerealella"


# ═══════════════════════════════════════════════════════════════════════════════
# CA06 – predecir_todas
# ═══════════════════════════════════════════════════════════════════════════════

class TestPredecirTodas:
    """CA06: Predicción de todas las especies."""

    def test_retorna_dict_con_cuatro_especies(self, mock_db):
        """CA06-1: predecir_todas debe retornar una clave por especie."""
        svc = _make_service(mock_db)
        svc.predecir_especie = MagicMock(return_value={"especie": "X"})
        result = svc.predecir_todas(dias_futuro=7)
        assert set(result.keys()) == {"sitotroga", "trichogramma", "galleria", "paratheresia"}

    def test_llama_predecir_especie_por_cada_clave(self, mock_db):
        """CA06-2: Se debe llamar predecir_especie una vez por especie."""
        svc = _make_service(mock_db)
        svc.predecir_especie = MagicMock(return_value={})
        svc.predecir_todas(30)
        assert svc.predecir_especie.call_count == 4

    def test_resultado_sanitizado_sin_nan(self, mock_db):
        """CA06-3: El resultado final no debe contener nan (reemplazado por None)."""
        svc = _make_service(mock_db)
        svc.predecir_especie = MagicMock(return_value={"r2": float("nan")})
        result = svc.predecir_todas(7)
        for v in result.values():
            assert not (isinstance(v.get("r2"), float) and math.isnan(v.get("r2", 0)))
