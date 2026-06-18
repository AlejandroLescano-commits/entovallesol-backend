from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import date, datetime

# ── Producción Sitotroga ──────────────────────────────────────────────────────
class ProduccionSitotrogaCreate(BaseModel):
    fecha: date
    id_unidad: Optional[int] = None
    cantidad: float

class ProduccionSitotrogaResponse(BaseModel):
    id: int
    fecha: date
    id_unidad: Optional[int]
    cantidad: float
    activo: bool
    registrado_por: Optional[int]
    creado_en: datetime
    class Config:
        from_attributes = True

# ── Producción Trichogramma ───────────────────────────────────────────────────
class ProduccionTrichogrammaCreate(BaseModel):
    fecha: date
    id_unidad: Optional[int] = None
    cantidad: float

class ProduccionTrichogrammaResponse(BaseModel):
    id: int
    fecha: date
    id_unidad: Optional[int]
    cantidad: float
    activo: bool
    registrado_por: Optional[int]
    creado_en: datetime
    class Config:
        from_attributes = True

# ── Producción Galleria ───────────────────────────────────────────────────────
class ProduccionGalleriaCreate(BaseModel):
    fecha: date
    id_unidad: Optional[int] = None
    cantidad: float

class ProduccionGalleriaResponse(BaseModel):
    id: int
    fecha: date
    id_unidad: Optional[int]
    cantidad: float
    activo: bool
    registrado_por: Optional[int]
    creado_en: datetime
    class Config:
        from_attributes = True

# ── Producción Paratheresia ───────────────────────────────────────────────────
class ProduccionParathesiaCreate(BaseModel):
    fecha: date
    id_unidad: Optional[int] = None
    cantidad: float

class ProduccionParathesiaResponse(BaseModel):
    id: int
    fecha: date
    id_unidad: Optional[int]
    cantidad: float
    activo: bool
    registrado_por: Optional[int]
    creado_en: datetime
    class Config:
        from_attributes = True

# ── Notas de Salida Sitodroga ─────────────────────────────────────────────────
class NotaSalidaSitodrogaCreate(BaseModel):
    tiposalida: str   # T.exiguum | T.pretiosum | Infestación | Ventas
    descripcion: Optional[str] = None
    fecha: date
    id_unidad: Optional[int] = None
    factor: float = 1
    cantidad: float

    @field_validator('cantidad')
    @classmethod
    def cantidad_positiva(cls, v):
        if v <= 0:
            raise ValueError('La cantidad debe ser mayor a 0')
        return v


class NotaSalidaSitodrogaResponse(BaseModel):
    id: int
    tiposalida: str
    descripcion: Optional[str]
    fecha: date
    id_unidad: Optional[int]
    factor: float
    cantidad: float
    activo: bool
    registrado_por: Optional[int]
    creado_en: datetime
    class Config:
        from_attributes = True

# ── Notas de Salida Avispitas ─────────────────────────────────────────────────
class NotaSalidaAvispitasCreate(BaseModel):
    tiposalida: str   # Parasitacion | Liberacion | Ventas
    id_lugarliberacion: Optional[int] = None
    descripcion: Optional[str] = None
    fecha: date
    id_unidad: Optional[int] = None
    cantidad: float

    @field_validator('cantidad')
    @classmethod
    def cantidad_positiva(cls, v):
        if v <= 0:
            raise ValueError('La cantidad debe ser mayor a 0')
        return v

class NotaSalidaAvispitasResponse(BaseModel):
    id: int
    tiposalida: str
    id_lugarliberacion: Optional[int]
    descripcion: Optional[str]
    fecha: date
    id_unidad: Optional[int]
    cantidad: float
    activo: bool
    registrado_por: Optional[int]
    creado_en: datetime
    class Config:
        from_attributes = True

# ── Notas de Salida Moscas ────────────────────────────────────────────────────
class NotaSalidaMoscasCreate(BaseModel):
    tiposalida: str   # Parasitacion | Venta | Liberacion
    id_lugarliberacion: Optional[int] = None
    descripcion: Optional[str] = None
    fecha: date
    id_unidad: Optional[int] = None
    cantidad: float

class NotaSalidaMoscasResponse(BaseModel):
    id: int
    tiposalida: str
    id_lugarliberacion: Optional[int]
    descripcion: Optional[str]
    fecha: date
    id_unidad: Optional[int]
    cantidad: float
    activo: bool
    registrado_por: Optional[int]
    creado_en: datetime
    class Config:
        from_attributes = True

# ── Notas de Salida Galleria melonella ────────────────────────────────────────
class NotaSalidaGalleriaCreate(BaseModel):
    tiposalida: str   # Paratheresia | Instalacion | Ventas
    descripcion: Optional[str] = None
    fecha: date
    id_unidad: Optional[int] = None
    cantidad: float
    ratio: Optional[float] = None  # Solo cuando tiposalida = Paratheresia

class NotaSalidaGalleriaResponse(BaseModel):
    id: int
    tiposalida: str
    descripcion: Optional[str]
    fecha: date
    id_unidad: Optional[int]
    cantidad: float
    ratio: Optional[float]
    activo: bool
    registrado_por: Optional[int]
    creado_en: datetime
    class Config:
        from_attributes = True


class LugarLiberacionCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class LugarLiberacionUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    activo: Optional[bool] = None

class LugarLiberacionResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    activo: bool
    class Config:
        from_attributes = True


class ProyeccionRequest(BaseModel):
    especie_destino: str      # 'trichogramma' o 'paratheresia'
    cantidad_objetivo: float  # ej: 30
    fecha_objetivo: date      # ej: 2026-01-20

class ProyeccionResponse(BaseModel):
    especie_destino: str
    cantidad_objetivo: float
    fecha_objetivo: date
    especie_origen: str
    cantidad_origen_necesaria: float
    unidad_origen: str
    fecha_inicio_produccion: date
    dias_ciclo: int
    factor: float       
