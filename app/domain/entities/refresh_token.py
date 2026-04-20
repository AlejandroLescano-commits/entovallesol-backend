from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.infrastructure.database.base import Base


class RefreshToken(Base):
    """Almacena refresh tokens emitidos para poder revocarlos en logout."""
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("usuarios.id"), nullable=False, index=True)
    token_hash = Column(String(256), unique=True, nullable=False, index=True)
    revoked = Column(Boolean, default=False)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
