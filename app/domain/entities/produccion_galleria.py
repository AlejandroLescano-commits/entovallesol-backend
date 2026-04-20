from sqlalchemy import Column, Integer, Float, Date, String, ForeignKey, Text, DateTime
from sqlalchemy.sql import func
from app.infrastructure.database.base import Base

class ProduccionGalleria(Base):
    """Registro diario de larvas de Galleria mellonella (unidad: unidades)."""
    __tablename__ = "produccion_galleria"
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, index=True)
    unidad = Column(String(20), default="unidades")
    produccion_dia = Column(Float, default=0)
    salida_paratheresia = Column(Float, default=0)
    salida_instalacion = Column(Float, default=0)
    salida_ventas = Column(Float, default=0)
    salida_total = Column(Float, default=0)
    saldo = Column(Float, default=0)
    tasa_mortalidad = Column(Float, nullable=True)
    observaciones = Column(Text, nullable=True)
    registrado_por = Column(Integer, ForeignKey("usuarios.id"))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
