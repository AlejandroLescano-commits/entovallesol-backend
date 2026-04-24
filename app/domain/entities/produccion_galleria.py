from sqlalchemy import Column, Integer, Float, Date, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.infrastructure.database.base import Base

class ProduccionGalleria(Base):
    __tablename__ = "produccion_galleria"
    id             = Column(Integer, primary_key=True, index=True)
    fecha          = Column(Date, nullable=False, index=True)
    id_unidad      = Column(Integer, ForeignKey("unidaddemedidagalleria.id"))
    cantidad       = Column(Float, nullable=False)
    activo         = Column(Boolean, default=True)
    registrado_por = Column(Integer, ForeignKey("usuarios.id"))
    creado_en      = Column(DateTime(timezone=True), server_default=func.now())