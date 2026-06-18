from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime
from sqlalchemy.sql import func
from app.infrastructure.database.base import Base

class ConversionParametros(Base):
    __tablename__ = "conversion_parametros"

    id              = Column(Integer, primary_key=True, index=True)
    especie_origen  = Column(String(50))
    especie_destino = Column(String(50))
    factor          = Column(Numeric(10, 4))
    dias_ciclo      = Column(Integer)
    unidad_origen   = Column(String(30))
    unidad_destino  = Column(String(30))
    activo          = Column(Boolean, default=True)
    actualizado_en  = Column(DateTime(timezone=True), server_default=func.now())
