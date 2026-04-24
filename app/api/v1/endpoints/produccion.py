from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from app.infrastructure.database.session import get_db
from app.core.dependencies import get_current_user
from app.services.produccion_service import ProduccionService
from app.domain.schemas.produccion_schema import (
    ProduccionSitotrogaCreate, ProduccionSitotrogaResponse,
    ProduccionTrichogrammaCreate, ProduccionTrichogrammaResponse,
    ProduccionGalleriaCreate, ProduccionGalleriaResponse,
    ProduccionParathesiaCreate, ProduccionParathesiaResponse,
    NotaSalidaSitodrogaCreate, NotaSalidaSitodrogaResponse,
    NotaSalidaAvispitasCreate, NotaSalidaAvispitasResponse,
    NotaSalidaMoscasCreate, NotaSalidaMoscasResponse,
    NotaSalidaGalleriaCreate, NotaSalidaGalleriaResponse,
)

router = APIRouter()

# ── Producción Sitotroga ──────────────────────────────────────────────────────
@router.post("/sitotroga", response_model=ProduccionSitotrogaResponse, status_code=201)
def registrar_sitotroga(data: ProduccionSitotrogaCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ProduccionService(db).registrar_sitotroga(data, user.id)

@router.get("/sitotroga", response_model=list[ProduccionSitotrogaResponse])
def listar_sitotroga(fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return ProduccionService(db).listar_sitotroga(fecha_inicio, fecha_fin)

# ── Producción Trichogramma ───────────────────────────────────────────────────
@router.post("/trichogramma", response_model=ProduccionTrichogrammaResponse, status_code=201)
def registrar_trichogramma(data: ProduccionTrichogrammaCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ProduccionService(db).registrar_trichogramma(data, user.id)

@router.get("/trichogramma", response_model=list[ProduccionTrichogrammaResponse])
def listar_trichogramma(fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return ProduccionService(db).listar_trichogramma(fecha_inicio, fecha_fin)

# ── Producción Galleria ───────────────────────────────────────────────────────
@router.post("/galleria", response_model=ProduccionGalleriaResponse, status_code=201)
def registrar_galleria(data: ProduccionGalleriaCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ProduccionService(db).registrar_galleria(data, user.id)

@router.get("/galleria", response_model=list[ProduccionGalleriaResponse])
def listar_galleria(fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return ProduccionService(db).listar_galleria(fecha_inicio, fecha_fin)

# ── Producción Paratheresia ───────────────────────────────────────────────────
@router.post("/paratheresia", response_model=ProduccionParathesiaResponse, status_code=201)
def registrar_paratheresia(data: ProduccionParathesiaCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ProduccionService(db).registrar_paratheresia(data, user.id)

@router.get("/paratheresia", response_model=list[ProduccionParathesiaResponse])
def listar_paratheresia(fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return ProduccionService(db).listar_paratheresia(fecha_inicio, fecha_fin)

# ── Notas de Salida Sitodroga ─────────────────────────────────────────────────
@router.post("/notas/sitodroga", response_model=NotaSalidaSitodrogaResponse, status_code=201)
def registrar_nota_sitodroga(data: NotaSalidaSitodrogaCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ProduccionService(db).registrar_nota_sitodroga(data, user.id)

@router.get("/notas/sitodroga", response_model=list[NotaSalidaSitodrogaResponse])
def listar_notas_sitodroga(fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return ProduccionService(db).listar_notas_sitodroga(fecha_inicio, fecha_fin)

# ── Notas de Salida Avispitas ─────────────────────────────────────────────────
@router.post("/notas/avispitas", response_model=NotaSalidaAvispitasResponse, status_code=201)
def registrar_nota_avispitas(data: NotaSalidaAvispitasCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ProduccionService(db).registrar_nota_avispitas(data, user.id)

@router.get("/notas/avispitas", response_model=list[NotaSalidaAvispitasResponse])
def listar_notas_avispitas(fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return ProduccionService(db).listar_notas_avispitas(fecha_inicio, fecha_fin)

# ── Notas de Salida Moscas ────────────────────────────────────────────────────
@router.post("/notas/moscas", response_model=NotaSalidaMoscasResponse, status_code=201)
def registrar_nota_moscas(data: NotaSalidaMoscasCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ProduccionService(db).registrar_nota_moscas(data, user.id)

@router.get("/notas/moscas", response_model=list[NotaSalidaMoscasResponse])
def listar_notas_moscas(fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return ProduccionService(db).listar_notas_moscas(fecha_inicio, fecha_fin)

# ── Notas de Salida Galleria ──────────────────────────────────────────────────
@router.post("/notas/galleria", response_model=NotaSalidaGalleriaResponse, status_code=201)
def registrar_nota_galleria(data: NotaSalidaGalleriaCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return ProduccionService(db).registrar_nota_galleria(data, user.id)

@router.get("/notas/galleria", response_model=list[NotaSalidaGalleriaResponse])
def listar_notas_galleria(fecha_inicio: Optional[date] = None, fecha_fin: Optional[date] = None, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return ProduccionService(db).listar_notas_galleria(fecha_inicio, fecha_fin)