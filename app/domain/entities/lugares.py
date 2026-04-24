from sqlalchemy import Column, Integer, String, Boolean, Text
from app.infrastructure.database.base import Base

class LugarLiberacionAvispitas(Base):
    __tablename__ = "lugaresliberacionavispitas"
    id          = Column(Integer, primary_key=True, index=True)
    nombre      = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    activo      = Column(Boolean, default=True)

class LugarLiberacionMoscas(Base):
    __tablename__ = "lugaresliberacionmoscas"
    id          = Column(Integer, primary_key=True, index=True)
    nombre      = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    activo      = Column(Boolean, default=True)