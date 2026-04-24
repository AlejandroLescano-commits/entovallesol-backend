from sqlalchemy import Column, Integer, Float, Date, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.sql import func
from app.infrastructure.database.base import Base

class NotaSalidaSitodroga(Base):
    __tablename__ = "notasalida_sitodroga"
    id             = Column(Integer, primary_key=True, index=True)
    tiposalida     = Column(String, nullable=False)
    descripcion    = Column(Text, nullable=True)
    fecha          = Column(Date, nullable=False)
    id_unidad      = Column(Integer, ForeignKey("unidadmedidasitodroga.id"))
    factor         = Column(Float, default=1)
    cantidad       = Column(Float, nullable=False)
    activo         = Column(Boolean, default=True)
    registrado_por = Column(Integer, ForeignKey("usuarios.id"))
    creado_en      = Column(DateTime(timezone=True), server_default=func.now())

class DetalleNotaSalidaSitodroga(Base):
    __tablename__ = "detalle_notasalida_sitodroga"
    id            = Column(Integer, primary_key=True, index=True)
    id_notasalida = Column(Integer, ForeignKey("notasalida_sitodroga.id"), nullable=False)
    activo        = Column(Boolean, default=True)

class NotaSalidaAvispitas(Base):
    __tablename__ = "notasalida_avispitas"
    id                 = Column(Integer, primary_key=True, index=True)
    tiposalida         = Column(String, nullable=False)
    id_lugarliberacion = Column(Integer, ForeignKey("lugaresliberacionavispitas.id"))
    descripcion        = Column(Text, nullable=True)
    fecha              = Column(Date, nullable=False)
    id_unidad          = Column(Integer, ForeignKey("unidadmedidaavispas.id"))
    cantidad           = Column(Float, nullable=False)
    activo             = Column(Boolean, default=True)
    registrado_por     = Column(Integer, ForeignKey("usuarios.id"))
    creado_en          = Column(DateTime(timezone=True), server_default=func.now())

class DetalleNotaSalidaAvispitas(Base):
    __tablename__ = "detalle_notasalida_avispitas"
    id            = Column(Integer, primary_key=True, index=True)
    id_notasalida = Column(Integer, ForeignKey("notasalida_avispitas.id"), nullable=False)
    activo        = Column(Boolean, default=True)

class NotaSalidaMoscas(Base):
    __tablename__ = "notasalida_moscas"
    id                 = Column(Integer, primary_key=True, index=True)
    tiposalida         = Column(String, nullable=False)
    id_lugarliberacion = Column(Integer, ForeignKey("lugaresliberacionmoscas.id"))
    descripcion        = Column(Text, nullable=True)
    fecha              = Column(Date, nullable=False)
    id_unidad          = Column(Integer, ForeignKey("unidaddemedidamoscas.id"))
    cantidad           = Column(Float, nullable=False)
    activo             = Column(Boolean, default=True)
    registrado_por     = Column(Integer, ForeignKey("usuarios.id"))
    creado_en          = Column(DateTime(timezone=True), server_default=func.now())

class DetalleNotaSalidaMoscas(Base):
    __tablename__ = "detalle_notasalida_moscas"
    id            = Column(Integer, primary_key=True, index=True)
    id_notasalida = Column(Integer, ForeignKey("notasalida_moscas.id"), nullable=False)
    activo        = Column(Boolean, default=True)

class NotaSalidaGalleriamelonella(Base):
    __tablename__ = "notasalida_galleriamelonella"
    id             = Column(Integer, primary_key=True, index=True)
    tiposalida     = Column(String, nullable=False)
    descripcion    = Column(Text, nullable=True)
    fecha          = Column(Date, nullable=False)
    id_unidad      = Column(Integer, ForeignKey("unidaddemedidagalleria.id"))
    cantidad       = Column(Float, nullable=False)
    ratio          = Column(Float, nullable=True)
    activo         = Column(Boolean, default=True)
    registrado_por = Column(Integer, ForeignKey("usuarios.id"))
    creado_en      = Column(DateTime(timezone=True), server_default=func.now())

class DetalleNotaSalidaGalleriamelonella(Base):
    __tablename__ = "detalle_notasalida_galleriamelonella"
    id            = Column(Integer, primary_key=True, index=True)
    id_notasalida = Column(Integer, ForeignKey("notasalida_galleriamelonella.id"), nullable=False)
    activo        = Column(Boolean, default=True)