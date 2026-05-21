"""
conftest.py – Fixtures compartidos para tests funcionales extras
Ubicación: tests/integracionextras/conftest.py

Usa SQLite en memoria para aislamiento total.
Todos los archivos de test en esta carpeta comparten estos fixtures.
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

# ─── BD SQLite para tests extras ──────────────────────────────────────────────
TEST_DATABASE_URL = "sqlite:///./test_extras.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ─── Credenciales de prueba por rol ───────────────────────────────────────────
ADMIN_EMAIL       = "admin_extras@entovallesol.com"
ADMIN_PASSWORD    = "Admin1234!"

SUPERVISOR_EMAIL    = "supervisor_extras@entovallesol.com"
SUPERVISOR_PASSWORD = "Super1234!"

OPERARIO_EMAIL    = "operario_extras@entovallesol.com"
OPERARIO_PASSWORD = "Oper1234!"


# ─── Setup / Teardown de tablas (una vez por sesión de pytest) ────────────────
@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# ─── Sesión por test ──────────────────────────────────────────────────────────
@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ─── TestClient con BD de test ────────────────────────────────────────────────
@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c
    app.dependency_overrides.clear()


# ─── Usuarios por rol ─────────────────────────────────────────────────────────
@pytest.fixture
def admin_user(db):
    u = db.query(Usuario).filter(Usuario.email == ADMIN_EMAIL).first()
    if not u:
        u = Usuario(
            nombre="Admin Extras",
            email=ADMIN_EMAIL,
            password_hash=hash_password(ADMIN_PASSWORD),
            rol="admin",
            activo=True,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
    return u


@pytest.fixture
def supervisor_user(db):
    u = db.query(Usuario).filter(Usuario.email == SUPERVISOR_EMAIL).first()
    if not u:
        u = Usuario(
            nombre="Supervisor Extras",
            email=SUPERVISOR_EMAIL,
            password_hash=hash_password(SUPERVISOR_PASSWORD),
            rol="supervisor",
            activo=True,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
    return u


@pytest.fixture
def operario_user(db):
    u = db.query(Usuario).filter(Usuario.email == OPERARIO_EMAIL).first()
    if not u:
        u = Usuario(
            nombre="Operario Extras",
            email=OPERARIO_EMAIL,
            password_hash=hash_password(OPERARIO_PASSWORD),
            rol="operario",
            activo=True,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
    return u


# ─── Headers JWT por rol ──────────────────────────────────────────────────────
@pytest.fixture
def admin_headers(client, admin_user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert resp.status_code == 200, f"Login admin falló: {resp.text}"
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def supervisor_headers(client, supervisor_user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": SUPERVISOR_EMAIL, "password": SUPERVISOR_PASSWORD},
    )
    assert resp.status_code == 200, f"Login supervisor falló: {resp.text}"
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


@pytest.fixture
def operario_headers(client, operario_user):
    resp = client.post(
        "/api/v1/auth/login",
        json={"email": OPERARIO_EMAIL, "password": OPERARIO_PASSWORD},
    )
    assert resp.status_code == 200, f"Login operario falló: {resp.text}"
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}
