from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.infrastructure.repositories.token_repository import TokenRepository
from app.core.security import (
    verify_password, create_access_token, create_refresh_token,
    decode_refresh_token,
)
from app.core.config import settings
from app.domain.schemas.auth_schema import LoginRequest, TokenResponse, RefreshRequest, RefreshResponse


class AuthService:
    def __init__(self, db: Session):
        self.user_repo = UsuarioRepository(db)
        self.token_repo = TokenRepository(db)

    # ── Login ─────────────────────────────────────────────────────────────────
    def login(self, data: LoginRequest) -> TokenResponse:
        user = self.user_repo.get_by_email(data.email)
        if not user or not verify_password(data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Correo o contraseña incorrectos",
            )
        if not user.activo:
            raise HTTPException(status_code=403, detail="Cuenta desactivada")

        payload = {"sub": str(user.id), "rol": user.rol}
        access_token = create_access_token(payload)
        refresh_token = create_refresh_token(payload)

        # Persiste el refresh token (para poder revocarlo)
        self.token_repo.save(user.id, refresh_token)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            rol=user.rol,
            nombre=user.nombre,
            user_id=user.id,
        )

    # ── Refresh ───────────────────────────────────────────────────────────────
    def refresh(self, data: RefreshRequest) -> RefreshResponse:
        if not self.token_repo.is_valid(data.refresh_token):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido, revocado o expirado. Inicia sesión nuevamente.",
            )
        try:
            payload = decode_refresh_token(data.refresh_token)
        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))

        new_access = create_access_token({"sub": payload["sub"], "rol": payload["rol"]})
        return RefreshResponse(
            access_token=new_access,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    # ── Logout ────────────────────────────────────────────────────────────────
    def logout(self, refresh_token: str, user_id: int) -> dict:
        self.token_repo.revoke(refresh_token)
        return {"message": "Sesión cerrada correctamente"}

    def logout_all(self, user_id: int) -> dict:
        self.token_repo.revoke_all_for_user(user_id)
        return {"message": "Sesión cerrada en todos los dispositivos"}
