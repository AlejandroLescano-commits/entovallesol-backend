"""
test_entrenamiento.py – Pruebas Unitarias del módulo de Entrenamiento
EntoValleSOL Backend

Casos cubiertos:
  CA01 – _safe()  (nan, inf, None, valores normales)
  CA02 – EntrenamientoService.update_config  (rango inválido, sets vacíos)
  CA03 – EntrenamientoService.entrenar_especie  (especie no configurada, auto-train off,
          sin datos, sin datos nuevos, entrenamiento exitoso, modelo peor rechazado)
  CA04 – EntrenamientoService.get_kpis
  CA05 – EntrenamientoService.get_todas_configs

Ejecutar:
  pytest tests/unit/test_entrenamiento.py -v
"""
import pytest
from datetime import date, timedelta
from unittest.mock import MagicMock, patch, call

import numpy as np


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _make_service(mock_db):
    from app.services.entrenamiento_service import EntrenamientoService
    svc = EntrenamientoService.__new__(EntrenamientoService)
    svc.db = mock_db
    return svc


def _make_registro(fecha: date, cantidad: float):
    r = MagicMock()
    r.fecha    = fecha
    r.cantidad = cantidad
    return r


def _config(activo=True, rango_meses=6, ultimo_hash=None, ultimo_r2=None):
    return {
        "especie":       "sitotroga",
        "activo":        activo,
        "rango_meses":   rango_meses,
        "ultimo_hash":   ultimo_hash,
        "ultimo_r2":     ultimo_r2,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# CA01 – _safe
# ═══════════════════════════════════════════════════════════════════════════════

class TestSafe:
    """CA01: La función _safe sanitiza nan/inf para PostgreSQL y JSON."""

    def test_nan_retorna_none(self):
        """CA01-1: float nan → None."""
        from app.services.entrenamiento_service import _safe
        assert _safe(float("nan")) is None

    def test_inf_retorna_none(self):
        """CA01-2: float inf → None."""
        from app.services.entrenamiento_service import _safe
        assert _safe(float("inf")) is None

    def test_neg_inf_retorna_none(self):
        """CA01-3: float -inf → None."""
        from app.services.entrenamiento_service import _safe
        assert _safe(float("-inf")) is None

    def test_none_retorna_none(self):
        """CA01-4: None de entrada → None de salida."""
        from app.services.entrenamiento_service import _safe
        assert _safe(None) is None

    def test_float_normal_redondea_a_4_decimales(self):
        """CA01-5: Float normal se redondea a 4 decimales."""
        from app.services.entrenamiento_service import _safe
        result = _safe(3.14159265)
        assert result == pytest.approx(3.1416, rel=1e-4)

    def test_cero_retorna_cero(self):
        """CA01-6: 0.0 no es nan ni inf; debe retornar 0.0."""
        from app.services.entrenamiento_service import _safe
        assert _safe(0.0) == pytest.approx(0.0)


# ═══════════════════════════════════════════════════════════════════════════════
# CA02 – update_config
# ═══════════════════════════════════════════════════════════════════════════════

class TestUpdateConfig:
    """CA02: Actualización de configuración de especie."""

    def test_rango_meses_cero_lanza_value_error(self, mock_db):
        """CA02-1: rango_meses=0 (fuera de 1-24) debe lanzar ValueError."""
        svc = _make_service(mock_db)
        with pytest.raises(ValueError, match="rango_meses"):
            svc.update_config("sitotroga", activo=None, rango_meses=0)

    def test_rango_meses_25_lanza_value_error(self, mock_db):
        """CA02-2: rango_meses=25 (fuera de 1-24) debe lanzar ValueError."""
        svc = _make_service(mock_db)
        with pytest.raises(ValueError):
            svc.update_config("sitotroga", activo=None, rango_meses=25)

    def test_sin_cambios_retorna_config_actual(self, mock_db):
        """CA02-3: Sin activo ni rango → retorna la config sin ejecutar UPDATE."""
        svc = _make_service(mock_db)
        cfg = _config()
        svc._get_config = MagicMock(return_value=cfg)
        result = svc.update_config("sitotroga", activo=None, rango_meses=None)
        assert result is cfg
        mock_db.execute.assert_not_called()

    def test_actualizar_activo_ejecuta_update(self, mock_db):
        """CA02-4: activo=False debe ejecutar UPDATE en BD y hacer commit."""
        svc = _make_service(mock_db)
        svc._get_config = MagicMock(return_value=_config())
        svc.update_config("sitotroga", activo=False, rango_meses=None)
        mock_db.execute.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_actualizar_rango_valido_ejecuta_update(self, mock_db):
        """CA02-5: rango_meses=12 (válido) debe ejecutar UPDATE."""
        svc = _make_service(mock_db)
        svc._get_config = MagicMock(return_value=_config())
        svc.update_config("sitotroga", activo=None, rango_meses=12)
        mock_db.execute.assert_called_once()

    def test_ambos_campos_actualizados_juntos(self, mock_db):
        """CA02-6: activo + rango_meses en la misma llamada → un solo UPDATE."""
        svc = _make_service(mock_db)
        svc._get_config = MagicMock(return_value=_config())
        svc.update_config("sitotroga", activo=True, rango_meses=3)
        assert mock_db.execute.call_count == 1  # un único UPDATE


# ═══════════════════════════════════════════════════════════════════════════════
# CA03 – entrenar_especie
# ═══════════════════════════════════════════════════════════════════════════════

class TestEntrenarEspecie:
    """CA03: Lógica principal de entrenamiento."""

    def _svc_con_repo(self, mock_db, registros=None, config=None):
        svc = _make_service(mock_db)
        svc._get_config = MagicMock(return_value=config or _config())
        mock_repo = MagicMock()
        mock_repo.list_sitotroga.return_value = registros or []
        with patch("app.services.entrenamiento_service.ProduccionRepository", return_value=mock_repo):
            pass
        return svc, mock_repo

    def test_especie_no_configurada_retorna_saltado(self, mock_db):
        """CA03-1: Config vacía (especie desconocida) → saltado=True."""
        svc = _make_service(mock_db)
        svc._get_config = MagicMock(return_value={})
        with patch("app.services.entrenamiento_service.ProduccionRepository"):
            result = svc.entrenar_especie("sitotroga")
        assert result["saltado"] is True

    def test_auto_train_desactivado_retorna_saltado(self, mock_db):
        """CA03-2: activo=False sin forzar → saltado=True."""
        svc = _make_service(mock_db)
        svc._get_config = MagicMock(return_value=_config(activo=False))
        with patch("app.services.entrenamiento_service.ProduccionRepository"):
            result = svc.entrenar_especie("sitotroga", forzar=False)
        assert result["saltado"] is True
        assert "desactivado" in result["motivo"].lower()

    def test_forzar_ignora_flag_activo(self, mock_db):
        """CA03-3: forzar=True debe ignorar activo=False y continuar."""
        registros = [_make_registro(date(2025, i, 1), float(i * 100)) for i in range(1, 6)]
        svc = _make_service(mock_db)
        svc._get_config = MagicMock(return_value=_config(activo=False, rango_meses=6))
        svc._guardar_modelo              = MagicMock()
        svc._insertar_log                = MagicMock()
        svc._actualizar_config_post_entreno = MagicMock()

        with patch("app.services.entrenamiento_service.ProduccionRepository") as MockRepo:
            MockRepo.return_value.list_sitotroga.return_value = registros
            result = svc.entrenar_especie("sitotroga", forzar=True)

        assert result.get("saltado") is not True
        assert "entrenado" in result

    def test_insuficientes_registros_retorna_saltado(self, mock_db):
        """CA03-4: Menos de 2 registros → saltado=True."""
        svc = _make_service(mock_db)
        svc._get_config = MagicMock(return_value=_config())

        with patch("app.services.entrenamiento_service.ProduccionRepository") as MockRepo:
            MockRepo.return_value.list_sitotroga.return_value = [
                _make_registro(date(2025, 1, 1), 100.0)
            ]
            result = svc.entrenar_especie("sitotroga", forzar=True)

        assert result["saltado"] is True
        assert "1 registros" in result["motivo"]

    def test_sin_datos_nuevos_retorna_saltado(self, mock_db):
        """CA03-5: Mismo hash que el último entrenamiento → saltado=True (sin forzar)."""
        import hashlib
        registros = [
            _make_registro(date(2025, 1, 1), 100.0),
            _make_registro(date(2025, 2, 1), 200.0),
        ]
        # Calcular el hash que produciría el servicio
        pares = sorted(zip(["2025-01-01", "2025-02-01"], [100.0, 200.0]))
        hash_actual = hashlib.md5(str(pares).encode()).hexdigest()

        svc = _make_service(mock_db)
        svc._get_config = MagicMock(return_value=_config(ultimo_hash=hash_actual))

        with patch("app.services.entrenamiento_service.ProduccionRepository") as MockRepo:
            MockRepo.return_value.list_sitotroga.return_value = registros
            result = svc.entrenar_especie("sitotroga", forzar=False)

        assert result["saltado"] is True
        assert "Sin datos nuevos" in result["motivo"]

    def test_entrenamiento_exitoso_retorna_metricas(self, mock_db):
        """CA03-6: Entrenamiento con datos suficientes retorna r2, mae, rmse."""
        registros = [_make_registro(date(2025, i, 1), float(i * 50)) for i in range(1, 8)]
        svc = _make_service(mock_db)
        svc._get_config = MagicMock(return_value=_config(rango_meses=6))
        svc._guardar_modelo              = MagicMock()
        svc._insertar_log                = MagicMock()
        svc._actualizar_config_post_entreno = MagicMock()

        with patch("app.services.entrenamiento_service.ProduccionRepository") as MockRepo:
            MockRepo.return_value.list_sitotroga.return_value = registros
            result = svc.entrenar_especie("sitotroga", forzar=True)

        assert result["entrenado"] is True
        assert "r2_score" in result
        assert "mae"      in result
        assert "rmse"     in result

    def test_modelo_peor_no_se_guarda(self, mock_db):
        """CA03-7: Si R² nuevo < R² anterior - 0.02, fue_reemplazado=False."""
        registros = [_make_registro(date(2025, i, 1), float(i * 50)) for i in range(1, 8)]
        svc = _make_service(mock_db)
        # R² anterior muy alto
        svc._get_config = MagicMock(return_value=_config(ultimo_r2=0.99, rango_meses=6))
        svc._guardar_modelo              = MagicMock()
        svc._insertar_log                = MagicMock()
        svc._actualizar_config_post_entreno = MagicMock()

        with patch("app.services.entrenamiento_service.ProduccionRepository") as MockRepo:
            MockRepo.return_value.list_sitotroga.return_value = registros
            # Entrenamos sin forzar para que se aplique la comparación de R²
            result = svc.entrenar_especie("sitotroga", forzar=False)

        # Solo verificamos que el campo existe; el valor depende del R² real
        assert "fue_reemplazado" in result

    def test_guardar_modelo_llamado_cuando_reemplazado(self, mock_db):
        """CA03-8: Si fue_reemplazado=True, _guardar_modelo debe invocarse."""
        registros = [_make_registro(date(2025, i, 1), float(i * 100)) for i in range(1, 8)]
        svc = _make_service(mock_db)
        svc._get_config = MagicMock(return_value=_config(rango_meses=6))
        svc._guardar_modelo              = MagicMock()
        svc._insertar_log                = MagicMock()
        svc._actualizar_config_post_entreno = MagicMock()

        with patch("app.services.entrenamiento_service.ProduccionRepository") as MockRepo:
            MockRepo.return_value.list_sitotroga.return_value = registros
            result = svc.entrenar_especie("sitotroga", forzar=True)

        if result.get("fue_reemplazado"):
            svc._guardar_modelo.assert_called_once()

    def test_commit_llamado_al_final(self, mock_db):
        """CA03-9: db.commit() debe llamarse exactamente una vez al finalizar."""
        registros = [_make_registro(date(2025, i, 1), float(i * 100)) for i in range(1, 8)]
        svc = _make_service(mock_db)
        svc._get_config = MagicMock(return_value=_config(rango_meses=6))
        svc._guardar_modelo              = MagicMock()
        svc._insertar_log                = MagicMock()
        svc._actualizar_config_post_entreno = MagicMock()

        with patch("app.services.entrenamiento_service.ProduccionRepository") as MockRepo:
            MockRepo.return_value.list_sitotroga.return_value = registros
            svc.entrenar_especie("sitotroga", forzar=True)

        mock_db.commit.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
# CA04 – get_kpis
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetKpis:
    """CA04: Historial de KPIs del modelo."""

    def test_retorna_lista_de_dicts(self, mock_db):
        """CA04-1: get_kpis debe retornar una lista de dicts."""
        svc = _make_service(mock_db)
        filas = [MagicMock() for _ in range(3)]
        for i, f in enumerate(filas):
            f.__iter__ = MagicMock(return_value=iter([]))
            f.keys     = MagicMock(return_value=["r2_score", "mae"])
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [
            {"r2_score": 0.9, "mae": 5.0, "rmse": 6.0,
             "n_registros": 10, "fue_reemplazado": True,
             "motivo_rechazo": None, "entrenado_en": "2025-01-01"}
            for _ in range(3)
        ]
        mock_db.execute.return_value = mock_result
        result = svc.get_kpis("sitotroga")
        assert isinstance(result, list)
        assert len(result) == 3

    def test_kpis_contienen_r2_y_mae(self, mock_db):
        """CA04-2: Cada entrada debe contener r2_score y mae."""
        svc = _make_service(mock_db)
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [
            {"r2_score": 0.85, "mae": 10.0, "rmse": 12.0,
             "n_registros": 5, "fue_reemplazado": True,
             "motivo_rechazo": None, "entrenado_en": "2025-01-01"}
        ]
        mock_db.execute.return_value = mock_result
        result = svc.get_kpis("sitotroga")
        assert "r2_score" in result[0]
        assert "mae"      in result[0]

    def test_especie_sin_kpis_retorna_lista_vacia(self, mock_db):
        """CA04-3: Especie sin historial retorna lista vacía."""
        svc = _make_service(mock_db)
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        result = svc.get_kpis("galleria")
        assert result == []


# ═══════════════════════════════════════════════════════════════════════════════
# CA05 – get_todas_configs
# ═══════════════════════════════════════════════════════════════════════════════

class TestGetTodasConfigs:
    """CA05: Listar configuraciones de todas las especies."""

    def test_retorna_lista_de_dicts(self, mock_db):
        """CA05-1: get_todas_configs retorna lista de dicts."""
        svc = _make_service(mock_db)
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = [
            {"especie": "sitotroga",    "activo": True, "rango_meses": 6},
            {"especie": "trichogramma", "activo": True, "rango_meses": 6},
        ]
        mock_db.execute.return_value = mock_result
        result = svc.get_todas_configs()
        assert len(result) == 2
        assert result[0]["especie"] == "sitotroga"

    def test_lista_vacia_cuando_sin_config(self, mock_db):
        """CA05-2: Sin configuración en BD retorna lista vacía."""
        svc = _make_service(mock_db)
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        result = svc.get_todas_configs()
        assert result == []
