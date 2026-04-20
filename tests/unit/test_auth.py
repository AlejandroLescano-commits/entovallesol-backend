import pytest
from unittest.mock import MagicMock, patch
from app.services.auth_service import AuthService
from app.domain.schemas.auth_schema import LoginRequest, RefreshRequest
from app.core.security import create_refresh_token


def _mock_user():
    from app.core.security import hash_password
    u = MagicMock()
    u.id = 1
    u.nombre = "Admin Test"
    u.email = "admin@test.com"
    u.rol = "admin"
    u.activo = True
    u.password_hash = hash_password("secret123")
    return u


def test_login_retorna_ambos_tokens():
    db = MagicMock()
    svc = AuthService(db)
    svc.user_repo.get_by_email = MagicMock(return_value=_mock_user())
    svc.token_repo.save = MagicMock()

    result = svc.login(LoginRequest(email="admin@test.com", password="secret123"))

    assert result.access_token
    assert result.refresh_token
    assert result.expires_in == 15 * 60
    svc.token_repo.save.assert_called_once()


def test_login_credenciales_incorrectas():
    from fastapi import HTTPException
    db = MagicMock()
    svc = AuthService(db)
    svc.user_repo.get_by_email = MagicMock(return_value=None)

    with pytest.raises(HTTPException) as exc:
        svc.login(LoginRequest(email="x@x.com", password="wrong"))
    assert exc.value.status_code == 401


def test_refresh_token_invalido():
    from fastapi import HTTPException
    db = MagicMock()
    svc = AuthService(db)
    svc.token_repo.is_valid = MagicMock(return_value=False)

    with pytest.raises(HTTPException) as exc:
        svc.refresh(RefreshRequest(refresh_token="token_falso"))
    assert exc.value.status_code == 401


def test_refresh_token_valido():
    db = MagicMock()
    svc = AuthService(db)
    user = _mock_user()
    rt = create_refresh_token({"sub": str(user.id), "rol": user.rol})

    svc.token_repo.is_valid = MagicMock(return_value=True)
    result = svc.refresh(RefreshRequest(refresh_token=rt))

    assert result.access_token
    assert result.expires_in == 15 * 60


def test_logout_revoca_token():
    db = MagicMock()
    svc = AuthService(db)
    svc.token_repo.revoke = MagicMock()

    result = svc.logout("some_refresh_token", user_id=1)
    svc.token_repo.revoke.assert_called_once_with("some_refresh_token")
    assert "cerrada" in result["message"]
