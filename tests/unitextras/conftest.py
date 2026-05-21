"""
conftest.py – Fixtures compartidas para tests unitarios (Auth, Usuario, Predicción,
              Entrenamiento, Importación, Reporte)

Ubicación: tests/unit/conftest.py
Ejecutar: pytest tests/unit/ -v
"""
import pytest
from datetime import date, datetime, timezone
from unittest.mock import MagicMock


# ═══════════════════════════════════════════════════════════════════════════════
# DB mock genérico
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def mock_db():
    """Sesión SQLAlchemy completamente mockeada (sin BD real)."""
    db = MagicMock()
    db.add     = MagicMock()
    db.commit  = MagicMock()
    db.refresh = MagicMock()
    db.query   = MagicMock()
    db.execute = MagicMock()
    return db


# ═══════════════════════════════════════════════════════════════════════════════
# Usuarios
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def usuario_activo():
    """Usuario ORM mock con activo=True."""
    u = MagicMock()
    u.id            = 1
    u.nombre        = "Ana Torres"
    u.email         = "ana@entolab.com"
    u.password_hash = "$2b$12$fakehash"
    u.rol           = "admin"
    u.activo        = True
    return u


@pytest.fixture
def usuario_inactivo(usuario_activo):
    """Igual que usuario_activo pero con activo=False."""
    usuario_activo.activo = False
    return usuario_activo


@pytest.fixture
def usuario_create_data():
    """Dict válido para UsuarioCreate."""
    return {
        "nombre":   "Carlos Paz",
        "email":    "carlos@entolab.com",
        "password": "segura1234",
        "rol":      "operario",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Tokens
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def refresh_token_valido():
    return "token.valido.firmado"


@pytest.fixture
def refresh_token_obj():
    """Objeto ORM RefreshToken mock, no revocado y no expirado."""
    obj = MagicMock()
    obj.id         = 1
    obj.user_id    = 1
    obj.token_hash = "abc123"
    obj.revoked    = False
    obj.expires_at = datetime(2099, 1, 1, tzinfo=timezone.utc)
    return obj


# ═══════════════════════════════════════════════════════════════════════════════
# Producción (helpers reutilizables entre Predicción, Reporte, etc.)
# ═══════════════════════════════════════════════════════════════════════════════

def make_prod_record(fecha: date, cantidad: float, activo: bool = True, tiposalida: str = None):
    """Crea un registro ORM mock con los campos mínimos."""
    r = MagicMock()
    r.fecha      = fecha
    r.cantidad   = cantidad
    r.activo     = activo
    r.tiposalida = tiposalida
    r.ratio      = None
    return r


@pytest.fixture
def prod_records_sitotroga():
    """3 registros de producción Sitotroga para tests de predicción/reporte."""
    return [
        make_prod_record(date(2025, 1, 10), 300.0),
        make_prod_record(date(2025, 3, 15), 450.0),
        make_prod_record(date(2025, 5, 20), 500.0),
    ]


@pytest.fixture
def notas_sitodroga():
    """2 notas de salida Sitotroga."""
    n1 = make_prod_record(date(2025, 3, 15), 100.0, tiposalida="T.exiguum")
    n2 = make_prod_record(date(2025, 5, 20), 200.0, tiposalida="Ventas")
    return [n1, n2]
