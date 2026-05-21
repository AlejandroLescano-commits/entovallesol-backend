"""
conftest.py – Fixtures compartidas para tests unitarios del módulo de Producción
Ubicación: tests/unit/conftest.py
"""
import pytest
from datetime import date
from unittest.mock import MagicMock

from app.domain.entities.produccion_sitotroga import ProduccionSitotroga


# ─── mock_db ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_db():
    """Sesión SQLAlchemy completamente mockeada (sin BD real)."""
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.query = MagicMock()
    return db


# ─── sample_sitotroga_data ────────────────────────────────────────────────────

@pytest.fixture
def sample_sitotroga_data():
    """Datos mínimos válidos para crear un registro de Sitotroga."""
    return {
        "fecha": date(2025, 5, 20),
        "id_unidad": 1,
        "cantidad": 500.0,
        "registrado_por": 1,
    }
