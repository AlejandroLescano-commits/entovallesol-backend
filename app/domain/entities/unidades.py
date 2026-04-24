from sqlalchemy import Column, Integer, String, Boolean, Text
from app.infrastructure.database.base import Base

class UnidadMedidasitodroga(Base):
    __tablename__ = "unidadmedidasitodroga"
    id          = Column(Integer, primary_key=True, index=True)
    nombre      = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    activo      = Column(Boolean, default=True)

class UnidadMedidaAvispas(Base):
    __tablename__ = "unidadmedidaavispas"
    id          = Column(Integer, primary_key=True, index=True)
    nombre      = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    activo      = Column(Boolean, default=True)

class UnidadDeMedidaGalleria(Base):
    __tablename__ = "unidaddemedidagalleria"
    id          = Column(Integer, primary_key=True, index=True)
    nombre      = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    activo      = Column(Boolean, default=True)

class UnidadDeMedidaMoscas(Base):
    __tablename__ = "unidaddemedidamoscas"
    id          = Column(Integer, primary_key=True, index=True)
    nombre      = Column(String, nullable=False)
    descripcion = Column(Text, nullable=True)
    activo      = Column(Boolean, default=True)