"""
conftest.py – Fixtures para tests funcionales/integración del módulo de Producción
Ubicación: tests/integration/conftest.py
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.infrastructure.database.session import get_db
from app.infrastructure.database.base import Base
from app.domain.entities.usuario import Usuario
from app.core.security import hash_password

# ─── BD SQLite para tests ─────────────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///./test_funcional.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

TEST_EMAIL    = "test@entovallesol.com"
TEST_PASSWORD = "Test1234!"


# ─── Setup / Teardown de tablas (una vez por módulo) ─────────────────────────

@pytest.fixture(scope="module", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ─── Sesión compartida por test ───────────────────────────────────────────────

@pytest.fixture
def db():
    """
    Una única sesión SQLAlchemy por test.
    El client y los fixtures de seed usan ESTA MISMA sesión,
    así todo lo insertado es visible en la misma transacción.
    """
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ─── TestClient que comparte la sesión del fixture db ────────────────────────

@pytest.fixture
def client(db):
    """
    TestClient con get_db reemplazado por la sesión de test.
    Cualquier dato insertado en 'db' antes de usar el client es visible.
    """
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ─── Usuario de prueba (creado en la MISMA sesión que el client) ──────────────

@pytest.fixture
def test_user(db):
    """
    Inserta el usuario de prueba en la sesión compartida con el client.
    Si ya existe (test anterior no hizo rollback completo), lo reutiliza.
    """
    usuario = db.query(Usuario).filter(Usuario.email == TEST_EMAIL).first()
    if not usuario:
        usuario = Usuario(
            nombre="Usuario Test",
            email=TEST_EMAIL,
            password_hash=hash_password(TEST_PASSWORD),
            rol="admin",
            activo=True,
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
    return usuario


# ─── Headers JWT ──────────────────────────────────────────────────────────────

@pytest.fixture
def auth_headers(client, test_user):
    """
    Hace login con el usuario de prueba (ya existente en la misma sesión)
    y retorna el header Authorization listo para usar.
    """
    response = client.post(
        "/api/v1/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, (
        f"Login falló ({response.status_code}): {response.text}\n"
        f"  → El usuario '{TEST_EMAIL}' debería existir en la BD de test.\n"
        "  → Verifica que el campo en la entidad se llame 'password_hash'."
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
