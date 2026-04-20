from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.infrastructure.database.session import get_db
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user
from app.domain.schemas.auth_schema import (
    LoginRequest, TokenResponse,
    RefreshRequest, RefreshResponse,
)
from pydantic import BaseModel

router = APIRouter()


class LogoutRequest(BaseModel):
    refresh_token: str


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """Autentica usuario y retorna access_token (15 min) + refresh_token (7 días)."""
    return AuthService(db).login(data)


@router.post("/refresh", response_model=RefreshResponse)
def refresh_token(data: RefreshRequest, db: Session = Depends(get_db)):
    """Renueva el access_token usando un refresh_token válido."""
    return AuthService(db).refresh(data)


@router.post("/logout")
def logout(
    data: LogoutRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Revoca el refresh_token actual (cierra esta sesión)."""
    return AuthService(db).logout(data.refresh_token, current_user.id)


@router.post("/logout-all")
def logout_all(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Revoca TODOS los refresh_tokens del usuario."""
    return AuthService(db).logout_all(current_user.id)


@router.get("/me")
def get_me(current_user=Depends(get_current_user)):
    """Retorna datos del usuario autenticado."""
    return {
        "id": current_user.id,
        "nombre": current_user.nombre,
        "email": current_user.email,
        "rol": current_user.rol,
    }
