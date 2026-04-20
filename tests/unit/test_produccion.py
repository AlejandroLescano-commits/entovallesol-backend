import pytest
from unittest.mock import MagicMock
from app.services.produccion_service import ProduccionService
from app.domain.schemas.produccion_schema import ProduccionSitotrogaCreate
from datetime import date

def test_calcular_saldo_sitotroga():
    db = MagicMock()
    svc = ProduccionService(db)
    # mock último saldo = 100
    svc.repo.get_ultimo_saldo_sitotroga = MagicMock(return_value=100.0)
    svc.repo.create_sitotroga = MagicMock(side_effect=lambda d: d)

    data = ProduccionSitotrogaCreate(
        fecha=date(2024, 3, 1),
        produccion_dia=500.0,
        salida_t_exiguum=200.0,
        salida_t_pretiosum=0,
        salida_infestacion=0,
        salida_ventas=50.0,
    )
    result = svc.registrar_sitotroga(data, user_id=1)
    assert result["salida_total"] == 250.0
    assert result["saldo"] == 350.0  # 100 + 500 - 250
