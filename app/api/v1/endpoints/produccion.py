from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import date
from app.infrastructure.database.session import get_db
from app.core.dependencies import get_current_user
from app.services.produccion_service import ProduccionService
from app.domain.schemas.produccion_schema import (
    ProduccionSitotrogaCreate, ProduccionSitotrogaResponse,
    ProduccionTrichogrammaCreate, ProduccionTrichogrammaResponse,
    ProduccionGalleriaCreate, ProduccionParathesiaCreate,
)

router = APIRouter()

# ── Sitotroga ──
@router.get("/sitotroga")
def listar_sitotroga(
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db), _=Depends(get_current_user)
):
    return ProduccionService(db).listar_sitotroga(fecha_inicio, fecha_fin)

@router.post("/sitotroga", status_code=201)
def crear_sitotroga(data: ProduccionSitotrogaCreate, db: Session = Depends(get_db), cu=Depends(get_current_user)):
    return ProduccionService(db).registrar_sitotroga(data, cu.id)

# ── Trichogramma ──
@router.get("/trichogramma")
def listar_trichogramma(
    especie: Optional[str] = Query(None),
    fecha_inicio: Optional[date] = Query(None),
    fecha_fin: Optional[date] = Query(None),
    db: Session = Depends(get_db), _=Depends(get_current_user)
):
    return ProduccionService(db).listar_trichogramma(especie, fecha_inicio, fecha_fin)

@router.post("/trichogramma", status_code=201)
def crear_trichogramma(data: ProduccionTrichogrammaCreate, db: Session = Depends(get_db), cu=Depends(get_current_user)):
    return ProduccionService(db).registrar_trichogramma(data, cu.id)

# ── Galleria ──
@router.post("/galleria", status_code=201)
def crear_galleria(data: ProduccionGalleriaCreate, db: Session = Depends(get_db), cu=Depends(get_current_user)):
    return ProduccionService(db).registrar_galleria(data, cu.id)

# ── Paratheresia ──
@router.post("/paratheresia", status_code=201)
def crear_paratheresia(data: ProduccionParathesiaCreate, db: Session = Depends(get_db), cu=Depends(get_current_user)):
    return ProduccionService(db).registrar_paratheresia(data, cu.id)
