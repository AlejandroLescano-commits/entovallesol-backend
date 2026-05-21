"""
test_auth.py – Pruebas Unitarias del módulo de Autenticación
EntoValleSOL Backend

Casos cubiertos:
  CA01 – AuthService.login  (éxito, credenciales malas, cuenta inactiva)
  CA02 – AuthService.refresh (token válido, inválido, payload corrupto)
  CA03 – AuthService.logout / logout_all
  CA04 – TokenRepository (save, is_valid, revoke, revoke_all)
  CA05 – Funciones de seguridad (hash_password, verify_password, tokens JWT)

Ejecutar:
  pytest tests/unit/test_auth.py -v
"""
import hashlib
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch, call

from fastapi import HTTPException


# ═══════════════════════════════════════════════════════════════════════════════
# CA01 – AuthService.login
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthServiceLogin:
    """CA01: Login con distintos escenarios."""

    def _make_service(self, mock_db, usuario=None, token_valido=True):
        """Construye AuthService con repos mockeados."""
        from app.services.auth_service import AuthService

        svc = AuthService.__new__(AuthService)
        svc.user_repo  = MagicMock()
        svc.token_repo = MagicMock()

        svc.user_repo.get_by_email.return_value = usuario
        svc.token_repo.save.return_value = None
        return svc

    def test_login_exitoso_retorna_token_response(self, mock_db, usuario_activo):
        """CA01-1: Login correcto devuelve access_token, refresh_token y datos del usuario."""
        svc = self._make_service(mock_db, usuario_activo)

        with patch("app.services.auth_service.verify_password", return_value=True), \
             patch("app.services.auth_service.create_access_token",  return_value="acc.tok"), \
             patch("app.services.auth_service.create_refresh_token", return_value="ref.tok"):

            from app.domain.schemas.auth_schema import LoginRequest
            result = svc.login(LoginRequest(email="ana@entolab.com", password="correcta"))

        assert result.access_token  == "acc.tok"
        assert result.refresh_token == "ref.tok"
        assert result.rol           == "admin"
        assert result.user_id       == 1

    def test_login_password_incorrecta_lanza_401(self, mock_db, usuario_activo):
        """CA01-2: Contraseña incorrecta debe lanzar HTTPException 401."""
        svc = self._make_service(mock_db, usuario_activo)

        with patch("app.services.auth_service.verify_password", return_value=False):
            from app.domain.schemas.auth_schema import LoginRequest
            with pytest.raises(HTTPException) as exc:
                svc.login(LoginRequest(email="ana@entolab.com", password="mala"))

        assert exc.value.status_code == 401

    def test_login_email_inexistente_lanza_401(self, mock_db):
        """CA01-3: Email que no existe debe lanzar HTTPException 401."""
        svc = self._make_service(mock_db, usuario=None)

        with patch("app.services.auth_service.verify_password", return_value=False):
            from app.domain.schemas.auth_schema import LoginRequest
            with pytest.raises(HTTPException) as exc:
                svc.login(LoginRequest(email="noexi@ste.com", password="x"))

        assert exc.value.status_code == 401

    def test_login_cuenta_inactiva_lanza_403(self, mock_db, usuario_inactivo):
        """CA01-4: Usuario con activo=False debe lanzar HTTPException 403."""
        svc = self._make_service(mock_db, usuario_inactivo)

        with patch("app.services.auth_service.verify_password", return_value=True):
            from app.domain.schemas.auth_schema import LoginRequest
            with pytest.raises(HTTPException) as exc:
                svc.login(LoginRequest(email="ana@entolab.com", password="correcta"))

        assert exc.value.status_code == 403

    def test_login_guarda_refresh_token_en_bd(self, mock_db, usuario_activo):
        """CA01-5: Tras login exitoso debe llamarse token_repo.save una vez."""
        svc = self._make_service(mock_db, usuario_activo)

        with patch("app.services.auth_service.verify_password", return_value=True), \
             patch("app.services.auth_service.create_access_token",  return_value="a"), \
             patch("app.services.auth_service.create_refresh_token", return_value="r"):

            from app.domain.schemas.auth_schema import LoginRequest
            svc.login(LoginRequest(email="ana@entolab.com", password="correcta"))

        svc.token_repo.save.assert_called_once_with(usuario_activo.id, "r")

    def test_login_retorna_expires_in_correcto(self, mock_db, usuario_activo):
        """CA01-6: expires_in debe ser ACCESS_TOKEN_EXPIRE_MINUTES * 60."""
        svc = self._make_service(mock_db, usuario_activo)

        with patch("app.services.auth_service.verify_password", return_value=True), \
             patch("app.services.auth_service.create_access_token",  return_value="a"), \
             patch("app.services.auth_service.create_refresh_token", return_value="r"), \
             patch("app.services.auth_service.settings") as mock_cfg:

            mock_cfg.ACCESS_TOKEN_EXPIRE_MINUTES = 15
            from app.domain.schemas.auth_schema import LoginRequest
            result = svc.login(LoginRequest(email="ana@entolab.com", password="correcta"))

        assert result.expires_in == 15 * 60


# ═══════════════════════════════════════════════════════════════════════════════
# CA02 – AuthService.refresh
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthServiceRefresh:
    """CA02: Renovación de access token."""

    def _make_service(self, token_valido: bool, payload: dict = None):
        from app.services.auth_service import AuthService
        svc = AuthService.__new__(AuthService)
        svc.token_repo = MagicMock()
        svc.token_repo.is_valid.return_value = token_valido

        if payload:
            with patch("app.services.auth_service.decode_refresh_token", return_value=payload):
                pass  # solo preparamos el patch más abajo

        return svc

    def test_refresh_valido_retorna_nuevo_access_token(self):
        """CA02-1: Refresh válido devuelve nuevo access_token."""
        from app.services.auth_service import AuthService
        from app.domain.schemas.auth_schema import RefreshRequest

        svc = AuthService.__new__(AuthService)
        svc.token_repo = MagicMock()
        svc.token_repo.is_valid.return_value = True

        payload = {"sub": "1", "rol": "admin"}

        with patch("app.services.auth_service.decode_refresh_token", return_value=payload), \
             patch("app.services.auth_service.create_access_token",  return_value="nuevo.acc"), \
             patch("app.services.auth_service.settings") as cfg:

            cfg.ACCESS_TOKEN_EXPIRE_MINUTES = 15
            result = svc.refresh(RefreshRequest(refresh_token="tok.valido"))

        assert result.access_token == "nuevo.acc"

    def test_refresh_token_invalido_lanza_401(self):
        """CA02-2: token_repo.is_valid=False debe lanzar HTTPException 401."""
        from app.services.auth_service import AuthService
        from app.domain.schemas.auth_schema import RefreshRequest

        svc = AuthService.__new__(AuthService)
        svc.token_repo = MagicMock()
        svc.token_repo.is_valid.return_value = False

        with pytest.raises(HTTPException) as exc:
            svc.refresh(RefreshRequest(refresh_token="tok.malo"))

        assert exc.value.status_code == 401

    def test_refresh_decode_lanza_value_error_da_401(self):
        """CA02-3: Si decode_refresh_token lanza ValueError → HTTPException 401."""
        from app.services.auth_service import AuthService
        from app.domain.schemas.auth_schema import RefreshRequest

        svc = AuthService.__new__(AuthService)
        svc.token_repo = MagicMock()
        svc.token_repo.is_valid.return_value = True

        with patch("app.services.auth_service.decode_refresh_token", side_effect=ValueError("expirado")):
            with pytest.raises(HTTPException) as exc:
                svc.refresh(RefreshRequest(refresh_token="tok"))

        assert exc.value.status_code == 401

    def test_refresh_retorna_expires_in(self):
        """CA02-4: expires_in debe calcularse correctamente."""
        from app.services.auth_service import AuthService
        from app.domain.schemas.auth_schema import RefreshRequest

        svc = AuthService.__new__(AuthService)
        svc.token_repo = MagicMock()
        svc.token_repo.is_valid.return_value = True

        with patch("app.services.auth_service.decode_refresh_token", return_value={"sub": "1", "rol": "admin"}), \
             patch("app.services.auth_service.create_access_token",  return_value="x"), \
             patch("app.services.auth_service.settings") as cfg:

            cfg.ACCESS_TOKEN_EXPIRE_MINUTES = 30
            result = svc.refresh(RefreshRequest(refresh_token="t"))

        assert result.expires_in == 30 * 60


# ═══════════════════════════════════════════════════════════════════════════════
# CA03 – AuthService.logout / logout_all
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuthServiceLogout:
    """CA03: Cierre de sesión."""

    def _make_service(self):
        from app.services.auth_service import AuthService
        svc = AuthService.__new__(AuthService)
        svc.token_repo = MagicMock()
        return svc

    def test_logout_llama_revoke(self):
        """CA03-1: logout debe llamar token_repo.revoke con el token correcto."""
        svc = self._make_service()
        svc.logout("mi.refresh.token", user_id=1)
        svc.token_repo.revoke.assert_called_once_with("mi.refresh.token")

    def test_logout_retorna_mensaje(self):
        """CA03-2: logout debe retornar dict con key 'message'."""
        svc = self._make_service()
        result = svc.logout("tok", user_id=1)
        assert "message" in result

    def test_logout_all_llama_revoke_all_for_user(self):
        """CA03-3: logout_all debe llamar revoke_all_for_user con el user_id."""
        svc = self._make_service()
        svc.logout_all(user_id=7)
        svc.token_repo.revoke_all_for_user.assert_called_once_with(7)

    def test_logout_all_retorna_mensaje(self):
        """CA03-4: logout_all debe retornar dict con key 'message'."""
        svc = self._make_service()
        result = svc.logout_all(user_id=1)
        assert "message" in result


# ═══════════════════════════════════════════════════════════════════════════════
# CA04 – TokenRepository
# ═══════════════════════════════════════════════════════════════════════════════

class TestTokenRepository:
    """CA04: Operaciones CRUD del repositorio de tokens."""

    def _hash(self, token: str) -> str:
        return hashlib.sha256(token.encode()).hexdigest()

    def test_save_agrega_y_hace_commit(self, mock_db):
        """CA04-1: save() debe hacer add y commit exactamente una vez."""
        from app.infrastructure.repositories.token_repository import TokenRepository
        with patch("app.infrastructure.repositories.token_repository.settings") as cfg:
            cfg.REFRESH_TOKEN_EXPIRE_DAYS = 7
            repo = TokenRepository(mock_db)
            repo.save(user_id=1, refresh_token="tok123")

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()

    def test_save_almacena_hash_no_token_plano(self, mock_db):
        """CA04-2: El objeto guardado debe contener token_hash, no el token en texto claro."""
        from app.infrastructure.repositories.token_repository import TokenRepository
        captured = {}

        def fake_add(obj):
            captured["obj"] = obj

        mock_db.add.side_effect = fake_add

        with patch("app.infrastructure.repositories.token_repository.settings") as cfg:
            cfg.REFRESH_TOKEN_EXPIRE_DAYS = 7
            repo = TokenRepository(mock_db)
            repo.save(user_id=1, refresh_token="tok_plano")

        assert captured["obj"].token_hash == self._hash("tok_plano")
        assert captured["obj"].token_hash != "tok_plano"

    def test_is_valid_retorna_false_si_no_existe(self, mock_db):
        """CA04-3: Token inexistente debe retornar False."""
        from app.infrastructure.repositories.token_repository import TokenRepository
        mock_db.query.return_value.filter.return_value.first.return_value = None
        repo = TokenRepository(mock_db)
        assert repo.is_valid("tok_inexistente") is False

    def test_is_valid_retorna_false_si_expirado(self, mock_db, refresh_token_obj):
        """CA04-4: Token expirado (expires_at en el pasado) debe retornar False."""
        from app.infrastructure.repositories.token_repository import TokenRepository
        refresh_token_obj.expires_at = datetime(2000, 1, 1, tzinfo=timezone.utc)
        mock_db.query.return_value.filter.return_value.first.return_value = refresh_token_obj
        repo = TokenRepository(mock_db)
        assert repo.is_valid("cualquier_tok") is False

    def test_is_valid_retorna_true_token_vigente(self, mock_db, refresh_token_obj):
        """CA04-5: Token vigente y no revocado debe retornar True."""
        from app.infrastructure.repositories.token_repository import TokenRepository
        mock_db.query.return_value.filter.return_value.first.return_value = refresh_token_obj
        repo = TokenRepository(mock_db)
        assert repo.is_valid("tok_bueno") is True

    def test_revoke_marca_revoked_true_y_hace_commit(self, mock_db, refresh_token_obj):
        """CA04-6: revoke() debe marcar revoked=True y hacer commit."""
        from app.infrastructure.repositories.token_repository import TokenRepository
        mock_db.query.return_value.filter.return_value.first.return_value = refresh_token_obj
        repo = TokenRepository(mock_db)
        repo.revoke("tok")
        assert refresh_token_obj.revoked is True
        mock_db.commit.assert_called_once()

    def test_revoke_token_inexistente_no_lanza_error(self, mock_db):
        """CA04-7: Si el token no existe, revoke() no debe lanzar excepción."""
        from app.infrastructure.repositories.token_repository import TokenRepository
        mock_db.query.return_value.filter.return_value.first.return_value = None
        repo = TokenRepository(mock_db)
        repo.revoke("fantasma")  # no debe lanzar

    def test_revoke_all_for_user_llama_update_y_commit(self, mock_db):
        """CA04-8: revoke_all_for_user() debe llamar .update() y commit una vez."""
        from app.infrastructure.repositories.token_repository import TokenRepository
        mock_filter = MagicMock()
        mock_db.query.return_value.filter.return_value = mock_filter
        repo = TokenRepository(mock_db)
        repo.revoke_all_for_user(user_id=3)
        mock_filter.update.assert_called_once_with({"revoked": True})
        mock_db.commit.assert_called_once()


# ═══════════════════════════════════════════════════════════════════════════════
# CA05 – Funciones de seguridad (security.py)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSecurityFunctions:
    """CA05: hash_password, verify_password y funciones JWT."""

    def test_hash_password_no_devuelve_texto_plano(self):
        """CA05-1: El hash no debe ser igual a la contraseña original."""
        from app.core.security import hash_password
        h = hash_password("mi_password")
        assert h != "mi_password"

    def test_hash_password_empieza_con_bcrypt_prefix(self):
        """CA05-2: bcrypt siempre empieza con $2b$."""
        from app.core.security import hash_password
        h = hash_password("cualquier_cosa")
        assert h.startswith("$2b$") or h.startswith("$2a$")

    def test_verify_password_correcto_retorna_true(self):
        """CA05-3: Contraseña correcta debe verificarse como True."""
        from app.core.security import hash_password, verify_password
        h = hash_password("secreto123")
        assert verify_password("secreto123", h) is True

    def test_verify_password_incorrecto_retorna_false(self):
        """CA05-4: Contraseña incorrecta debe retornar False."""
        from app.core.security import hash_password, verify_password
        h = hash_password("secreto123")
        assert verify_password("otra_cosa", h) is False

    def test_create_access_token_retorna_string(self):
        """CA05-5: create_access_token debe retornar un string no vacío."""
        from app.core.security import create_access_token
        with patch("app.core.security.settings") as cfg:
            cfg.ACCESS_TOKEN_EXPIRE_MINUTES = 15
            cfg.SECRET_KEY   = "supersecret"
            cfg.ALGORITHM    = "HS256"
            tok = create_access_token({"sub": "1", "rol": "admin"})
        assert isinstance(tok, str) and len(tok) > 0

    def test_create_y_decode_access_token_round_trip(self):
        """CA05-6: El payload codificado debe recuperarse correctamente."""
        from app.core.security import create_access_token, decode_access_token
        with patch("app.core.security.settings") as cfg:
            cfg.ACCESS_TOKEN_EXPIRE_MINUTES = 15
            cfg.SECRET_KEY  = "supersecret_key"
            cfg.ALGORITHM   = "HS256"
            tok     = create_access_token({"sub": "42", "rol": "supervisor"})
            payload = decode_access_token(tok)
        assert payload["sub"] == "42"
        assert payload["rol"] == "supervisor"

    def test_decode_access_token_con_token_falso_lanza_value_error(self):
        """CA05-7: Token manipulado debe lanzar ValueError."""
        from app.core.security import decode_access_token
        with patch("app.core.security.settings") as cfg:
            cfg.SECRET_KEY = "supersecret"
            cfg.ALGORITHM  = "HS256"
            with pytest.raises(ValueError):
                decode_access_token("token.completamente.falso")

    def test_create_y_decode_refresh_token_round_trip(self):
        """CA05-8: Refresh token debe sobrevivir el encode/decode."""
        from app.core.security import create_refresh_token, decode_refresh_token
        with patch("app.core.security.settings") as cfg:
            cfg.REFRESH_TOKEN_EXPIRE_DAYS = 7
            cfg.REFRESH_SECRET_KEY = "refresh_secret_key"
            cfg.ALGORITHM          = "HS256"
            tok     = create_refresh_token({"sub": "5", "rol": "operario"})
            payload = decode_refresh_token(tok)
        assert payload["sub"] == "5"
        assert payload["type"] == "refresh"
