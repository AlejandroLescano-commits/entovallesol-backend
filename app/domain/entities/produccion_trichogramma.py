from sqlalchemy import Column, Integer, Float, Date, String, ForeignKey, Text, DateTime
from sqlalchemy.sql import func
from app.infrastructure.database.base import Base

class ProduccionTrichogramma(Base):
    """Registro diario de avispitas Trichogramma (unidad: pulg²)."""
    __tablename__ = "produccion_trichogramma"
    id = Column(Integer, primary_key=True, index=True)
    fecha = Column(Date, nullable=False, index=True)
    especie = Column(String(50), nullable=False)           # exiguum | pretiosum
    unidad = Column(String(20), default="pulg2")
    produccion_dia = Column(Float, default=0)
    salida_parasitacion = Column(Float, default=0)
    # Salidas por finca/sector
    salida_san_ricardo_a = Column(Float, default=0)
    salida_san_ricardo_b = Column(Float, default=0)
    salida_quemazón = Column(Float, default=0)
    salida_trapiche = Column(Float, default=0)
    salida_segundo_jiron = Column(Float, default=0)
    salida_pabellon_alto = Column(Float, default=0)
    salida_sacachique = Column(Float, default=0)
    salida_la_encantada = Column(Float, default=0)
    salida_ventas = Column(Float, default=0)
    salida_total = Column(Float, default=0)
    saldo = Column(Float, default=0)
    porcentaje_eclosion = Column(Float, nullable=True)
    observaciones = Column(Text, nullable=True)
    registrado_por = Column(Integer, ForeignKey("usuarios.id"))
    creado_en = Column(DateTime(timezone=True), server_default=func.now())
