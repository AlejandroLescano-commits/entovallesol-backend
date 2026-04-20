from sqlalchemy import Column, Integer, Float, Date, String, ForeignKey, Text
from sqlalchemy.sql import func
from sqlalchemy import DateTime
from app.infrastructure.database.base import Base

class ProduccionSitotroga(Base):
    """Registro diario de huevos de Sitotroga cerealella (unidad: gramos)."""
    __tablename__ = "produccion_sitotroga"
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, index=True)
    unidad = Column(String(20), default="gramos")
    produccion_dia = Column(Float, nullable=True)          # producción del día
    salida_t_exiguum = Column(Float, default=0)            # salida para T. exiguum
    salida_t_pretiosum = Column(Float, default=0)          # salida para T. pretiosum
    salida_infestacion = Column(Float, default=0)          # salida infestación
    salida_ventas = Column(Float, default=0)               # ventas
    salida_total = Column(Float, default=0)
    saldo = Column(Float, default=0)
    observaciones = Column(Text, nullable=True)
    registrado_por = Column(Integer, ForeignKey("usuarios.id"))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
