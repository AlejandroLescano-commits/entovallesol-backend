from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.infrastructure.database.session import get_db
from app.core.security import decode_access_token
from app.infrastructure.repositories.usuario_repository import UsuarioRepository

bearer = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
):
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
        user_id: int = int(payload["sub"])
    except (ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de acceso inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = UsuarioRepository(db).get_by_id(user_id)
    if not user or not user.activo:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o inactivo")
    return user


def require_admin(current_user=Depends(get_current_user)):
    if current_user.rol != "admin":
        raise HTTPException(status_code=403, detail="Se requiere rol administrador")
    return current_user


def require_supervisor_or_admin(current_user=Depends(get_current_user)):
    if current_user.rol not in ("admin", "supervisor"):
        raise HTTPException(status_code=403, detail="Se requiere rol supervisor o admin")
    return current_user
