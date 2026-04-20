from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class ProduccionSitotrogaCreate(BaseModel):
    fecha: date
    produccion_dia: Optional[float] = None
    salida_t_exiguum: float = 0
    salida_t_pretiosum: float = 0
    salida_infestacion: float = 0
    salida_ventas: float = 0
    observaciones: Optional[str] = None

class ProduccionSitotrogaResponse(ProduccionSitotrogaCreate):
    id: int
    salida_total: float
    saldo: float
    creado_en: datetime
    class Config:
        from_attributes = True

class ProduccionTrichogrammaCreate(BaseModel):
    fecha: date
    especie: str   # exiguum | pretiosum
    produccion_dia: float = 0
    salida_parasitacion: float = 0
    salida_san_ricardo_a: float = 0
    salida_san_ricardo_b: float = 0
    salida_quemazón: float = 0
    salida_trapiche: float = 0
    salida_segundo_jiron: float = 0
    salida_pabellon_alto: float = 0
    salida_sacachique: float = 0
    salida_la_encantada: float = 0
    salida_ventas: float = 0
    porcentaje_eclosion: Optional[float] = None
    observaciones: Optional[str] = None

class ProduccionTrichogrammaResponse(ProduccionTrichogrammaCreate):
    id: int
    salida_total: float
    saldo: float
    creado_en: datetime
    class Config:
        from_attributes = True

class ProduccionGalleriaCreate(BaseModel):
    fecha: date
    produccion_dia: float = 0
    salida_paratheresia: float = 0
    salida_instalacion: float = 0
    salida_ventas: float = 0
    tasa_mortalidad: Optional[float] = None
    observaciones: Optional[str] = None

class ProduccionParathesiaCreate(BaseModel):
    fecha: date
    produccion_dia: float = 0
    salida_parasitacion: float = 0
    salida_quemazón: float = 0
    salida_segundo_jiron: float = 0
    salida_san_ricardo_a: float = 0
    salida_san_ricardo_b: float = 0
    salida_sacachique: float = 0
    salida_pabellon_alto: float = 0
    salida_trapiche: float = 0
    salida_ventas: float = 0
    observaciones: Optional[str] = None
