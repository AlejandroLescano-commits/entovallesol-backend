from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.infrastructure.database.base import Base

class Finca(Base):
    __tablename__ = "fincas"
    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    ubicacion = Column(String(200), nullable=True)
    activa = Column(Boolean, default=True)
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
