import hashlib
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from app.domain.entities.refresh_token import RefreshToken
from app.core.config import settings


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class TokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, user_id: int, refresh_token: str) -> None:
        expires = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        obj = RefreshToken(user_id=user_id, token_hash=_hash(refresh_token), expires_at=expires)
        self.db.add(obj)
        self.db.commit()

    def is_valid(self, refresh_token: str) -> bool:
        """True si el token existe, no fue revocado y no expiró."""
        h = _hash(refresh_token)
        row = self.db.query(RefreshToken).filter(
            RefreshToken.token_hash == h,
            RefreshToken.revoked == False,
        ).first()
        if not row:
            return False
        if row.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            return False
        return True

    def revoke(self, refresh_token: str) -> None:
        h = _hash(refresh_token)
        row = self.db.query(RefreshToken).filter(RefreshToken.token_hash == h).first()
        if row:
            row.revoked = True
            self.db.commit()

    def revoke_all_for_user(self, user_id: int) -> None:
        """Revoca TODOS los refresh tokens del usuario (logout en todos los dispositivos)."""
        self.db.query(RefreshToken).filter(
            RefreshToken.user_id == user_id,
            RefreshToken.revoked == False,
        ).update({"revoked": True})
        self.db.commit()
