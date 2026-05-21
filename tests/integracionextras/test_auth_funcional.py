"""
test_auth_funcional.py – Pruebas Funcionales del módulo de Autenticación
EntoValleSOL Backend
Casos cubiertos:
  AUTH-01 – Login exitoso retorna access_token, refresh_token y datos de usuario
  AUTH-02 – Login con credenciales incorrectas → HTTP 401
  AUTH-03 – Login con cuenta desactivada → HTTP 403
  AUTH-04 – Refresh token válido genera nuevo access_token
  AUTH-05 – Refresh token revocado no puede reutilizarse
  AUTH-06 – Logout revoca el refresh_token actual
  AUTH-07 – Logout-all revoca todas las sesiones del usuario
  AUTH-08 – GET /auth/me retorna datos del usuario autenticado
  AUTH-09 – Campos obligatorios ausentes en login → HTTP 422
  AUTH-10 – Email con formato inválido → HTTP 422

Ejecutar:
  pytest tests/integracionextras/test_auth_funcional.py -v
  pytest tests/integracionextras/test_auth_funcional.py -v -k "AUTH01"
"""
import pytest
from fastapi.testclient import TestClient
from app.domain.entities.usuario import Usuario
from app.core.security import hash_password

# ─── Credenciales locales del módulo ─────────────────────────────────────────
AUTH_EMAIL    = "auth_test@entovallesol.com"
AUTH_PASSWORD = "AuthPass1!"

INACTIVE_EMAIL    = "inactive@entovallesol.com"
INACTIVE_PASSWORD = "Inactive1!"


# ─── Fixtures adicionales de este módulo ─────────────────────────────────────
@pytest.fixture
def auth_user(db):
    u = db.query(Usuario).filter(Usuario.email == AUTH_EMAIL).first()
    if not u:
        u = Usuario(
            nombre="Auth User Test",
            email=AUTH_EMAIL,
            password_hash=hash_password(AUTH_PASSWORD),
            rol="operario",
            activo=True,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
    return u


@pytest.fixture
def inactive_user(db):
    u = db.query(Usuario).filter(Usuario.email == INACTIVE_EMAIL).first()
    if not u:
        u = Usuario(
            nombre="Inactive User",
            email=INACTIVE_EMAIL,
            password_hash=hash_password(INACTIVE_PASSWORD),
            rol="operario",
            activo=False,
        )
        db.add(u)
        db.commit()
        db.refresh(u)
    return u


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH-01 – Login exitoso
# ═══════════════════════════════════════════════════════════════════════════════
class TestAUTH01LoginExitoso:
    """AUTH-01: Login con credenciales correctas retorna tokens y datos de usuario."""

    def test_retorna_http_200(self, client, auth_user):
        """AUTH-01: Respuesta debe ser HTTP 200."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
        )
        assert resp.status_code == 200

    def test_retorna_access_token_no_vacio(self, client, auth_user):
        """AUTH-01: access_token presente y no vacío."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
        )
        data = resp.json()
        assert "access_token" in data
        assert len(data["access_token"]) > 20

    def test_retorna_refresh_token_no_vacio(self, client, auth_user):
        """AUTH-01: refresh_token presente y no vacío."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
        )
        assert len(resp.json()["refresh_token"]) > 20

    def test_retorna_datos_del_usuario(self, client, auth_user):
        """AUTH-01: Respuesta incluye nombre, rol y user_id correctos."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
        )
        data = resp.json()
        assert data["nombre"] == "Auth User Test"
        assert data["rol"] == "operario"
        assert isinstance(data["user_id"], int)
        assert data["user_id"] > 0

    def test_token_type_es_bearer(self, client, auth_user):
        """AUTH-01: token_type debe ser 'bearer'."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
        )
        assert resp.json()["token_type"] == "bearer"

    def test_expires_in_es_positivo(self, client, auth_user):
        """AUTH-01: expires_in debe ser un entero positivo (segundos)."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
        )
        assert isinstance(resp.json()["expires_in"], int)
        assert resp.json()["expires_in"] > 0


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH-02 – Login con credenciales incorrectas
# ═══════════════════════════════════════════════════════════════════════════════
class TestAUTH02CredencialesIncorrectas:
    """AUTH-02: Login con credenciales incorrectas debe retornar HTTP 401."""

    def test_password_incorrecto_retorna_401(self, client, auth_user):
        """AUTH-02: Contraseña errónea → 401."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": "WrongPassword99!"},
        )
        assert resp.status_code == 401

    def test_email_inexistente_retorna_401(self, client, auth_user):
        """AUTH-02: Email que no existe en BD → 401."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "noexiste@entovallesol.com", "password": AUTH_PASSWORD},
        )
        assert resp.status_code == 401

    def test_ambos_campos_incorrectos_retorna_401(self, client, auth_user):
        """AUTH-02: Email y contraseña ambos incorrectos → 401."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": "nada@nada.com", "password": "nada"},
        )
        assert resp.status_code == 401

    def test_mensaje_error_no_revela_que_campo_fallo(self, client, auth_user):
        """AUTH-02 (seguridad): El mensaje de error debe ser genérico."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": "wrong"},
        )
        detail = resp.json().get("detail", "").lower()
        # No debe indicar si fue el email o la contraseña el campo incorrecto
        assert "correo" in detail or "contraseña" in detail
        assert "email no encontrado" not in detail
        assert "usuario no existe" not in detail


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH-03 – Cuenta desactivada
# ═══════════════════════════════════════════════════════════════════════════════
class TestAUTH03CuentaDesactivada:
    """AUTH-03: Login con cuenta activo=False debe retornar HTTP 403."""

    def test_cuenta_desactivada_retorna_403(self, client, inactive_user):
        """AUTH-03: Usuario con activo=False → 403."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": INACTIVE_EMAIL, "password": INACTIVE_PASSWORD},
        )
        assert resp.status_code == 403

    def test_mensaje_indica_cuenta_desactivada(self, client, inactive_user):
        """AUTH-03: El mensaje debe mencionar que la cuenta está desactivada."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": INACTIVE_EMAIL, "password": INACTIVE_PASSWORD},
        )
        detail = resp.json().get("detail", "").lower()
        assert "desactivada" in detail or "inactiva" in detail or "disabled" in detail


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH-04 – Refresh token genera nuevo access_token
# ═══════════════════════════════════════════════════════════════════════════════
class TestAUTH04RefreshToken:
    """AUTH-04: Un refresh_token válido debe generar un nuevo access_token."""

    def test_refresh_retorna_nuevo_access_token(self, client, auth_user):
        """AUTH-04: /auth/refresh con token válido → nuevo access_token."""
        login = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
        )
        refresh_token = login.json()["refresh_token"]
        original_access = login.json()["access_token"]

        resp = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["access_token"] != original_access

    def test_refresh_retorna_expires_in_positivo(self, client, auth_user):
        """AUTH-04: El nuevo token debe incluir expires_in positivo."""
        login = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
        )
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": login.json()["refresh_token"]},
        )
        assert resp.json()["expires_in"] > 0

    def test_refresh_con_token_invalido_retorna_401(self, client, auth_user):
        """AUTH-04 (negativo): Token falso → 401."""
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "esto.no.es.un.token.valido"},
        )
        assert resp.status_code == 401

    def test_refresh_sin_campo_retorna_422(self, client, auth_user):
        """AUTH-04 (negativo): Cuerpo vacío → 422."""
        resp = client.post("/api/v1/auth/refresh", json={})
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH-05 – Refresh token revocado no puede reutilizarse
# ═══════════════════════════════════════════════════════════════════════════════
class TestAUTH05RefreshRevocado:
    """AUTH-05: Un refresh_token ya revocado (por logout) no debe ser reutilizable."""

    def test_refresh_tras_logout_retorna_401(self, client, auth_user):
        """AUTH-05: refresh_token revocado por logout → 401 en /auth/refresh."""
        login = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
        )
        tokens = login.json()
        access_token  = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        # Hacer logout
        client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": refresh_token},
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # Intentar reutilizar el refresh revocado
        resp = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH-06 – Logout revoca la sesión actual
# ═══════════════════════════════════════════════════════════════════════════════
class TestAUTH06Logout:
    """AUTH-06: POST /auth/logout revoca el refresh_token de la sesión actual."""

    def test_logout_retorna_mensaje_de_exito(self, client, auth_user):
        """AUTH-06: Logout exitoso → HTTP 200 con mensaje."""
        login = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
        )
        tokens = login.json()
        resp = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": tokens["refresh_token"]},
            headers={"Authorization": f"Bearer {tokens['access_token']}"},
        )
        assert resp.status_code == 200
        assert "message" in resp.json()

    def test_logout_sin_token_retorna_401(self, client, auth_user):
        """AUTH-06 (seguridad): Logout sin Authorization → 401 o 403."""
        login = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
        )
        resp = client.post(
            "/api/v1/auth/logout",
            json={"refresh_token": login.json()["refresh_token"]},
        )
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH-07 – Logout-all revoca todas las sesiones
# ═══════════════════════════════════════════════════════════════════════════════
class TestAUTH07LogoutAll:
    """AUTH-07: POST /auth/logout-all revoca TODOS los refresh_tokens del usuario."""

    def test_logout_all_invalida_multiples_sesiones(self, client, auth_user):
        """AUTH-07: Tras logout-all, ningún refresh_token previo puede usarse."""
        # Crear dos sesiones (dos logins)
        s1 = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
        ).json()
        s2 = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
        ).json()

        # Logout-all usando la primera sesión
        client.post(
            "/api/v1/auth/logout-all",
            headers={"Authorization": f"Bearer {s1['access_token']}"},
        )

        # Ambas sesiones deben quedar inválidas
        r1 = client.post("/api/v1/auth/refresh", json={"refresh_token": s1["refresh_token"]})
        r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": s2["refresh_token"]})
        assert r1.status_code == 401
        assert r2.status_code == 401

    def test_logout_all_retorna_mensaje(self, client, auth_user):
        """AUTH-07: Respuesta debe incluir un mensaje de confirmación."""
        login = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
        ).json()
        resp = client.post(
            "/api/v1/auth/logout-all",
            headers={"Authorization": f"Bearer {login['access_token']}"},
        )
        assert resp.status_code == 200
        assert "message" in resp.json()


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH-08 – GET /auth/me
# ═══════════════════════════════════════════════════════════════════════════════
class TestAUTH08GetMe:
    """AUTH-08: GET /auth/me retorna los datos del usuario autenticado."""

    def test_me_retorna_datos_correctos(self, client, auth_user):
        """AUTH-08: /auth/me devuelve id, nombre, email y rol."""
        login = client.post(
            "/api/v1/auth/login",
            json={"email": AUTH_EMAIL, "password": AUTH_PASSWORD},
        ).json()
        resp = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login['access_token']}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == AUTH_EMAIL
        assert data["nombre"] == "Auth User Test"
        assert data["rol"] == "operario"
        assert isinstance(data["id"], int)

    def test_me_sin_token_retorna_401(self, client):
        """AUTH-08 (seguridad): Sin token → 401 o 403."""
        resp = client.get("/api/v1/auth/me")
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH-09 – Campos obligatorios ausentes
# ═══════════════════════════════════════════════════════════════════════════════
class TestAUTH09CamposObligatorios:
    """AUTH-09: Ausencia de campos requeridos en login → HTTP 422."""

    def test_sin_email_retorna_422(self, client):
        """AUTH-09: Sin campo email → 422."""
        resp = client.post("/api/v1/auth/login", json={"password": AUTH_PASSWORD})
        assert resp.status_code == 422

    def test_sin_password_retorna_422(self, client):
        """AUTH-09: Sin campo password → 422."""
        resp = client.post("/api/v1/auth/login", json={"email": AUTH_EMAIL})
        assert resp.status_code == 422

    def test_body_vacio_retorna_422(self, client):
        """AUTH-09: Body JSON vacío → 422."""
        resp = client.post("/api/v1/auth/login", json={})
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# AUTH-10 – Email con formato inválido
# ═══════════════════════════════════════════════════════════════════════════════
class TestAUTH10EmailInvalido:
    """AUTH-10: Email con formato inválido → HTTP 422 (validación Pydantic)."""

    @pytest.mark.parametrize("email_invalido", [
        "noesuncorreo",
        "falta@",
        "@sindominio.com",
        "doble@@dominio.com",
        "",
    ])
    def test_email_invalido_retorna_422(self, client, email_invalido):
        """AUTH-10: Varios formatos inválidos de email deben ser rechazados."""
        resp = client.post(
            "/api/v1/auth/login",
            json={"email": email_invalido, "password": AUTH_PASSWORD},
        )
        assert resp.status_code == 422
