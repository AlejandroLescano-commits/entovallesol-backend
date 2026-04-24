from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.infrastructure.database.session import get_db
from app.core.dependencies import get_current_user
from app.services.prediccion_service import PrediccionService

router = APIRouter()

@router.get("/sitotroga")
def predecir_sitotroga(
    dias: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Predicción de demanda y producción necesaria para Sitotroga cerealella."""
    return PrediccionService(db).predecir_sitotroga(dias)

@router.get("/trichogramma")
def predecir_trichogramma(
    dias: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Predicción de demanda y producción necesaria para Trichogramma."""
    return PrediccionService(db).predecir_trichogramma(dias)

@router.get("/galleria")
def predecir_galleria(
    dias: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Predicción de demanda y producción necesaria para Galleria melonella."""
    return PrediccionService(db).predecir_galleria(dias)

@router.get("/paratheresia")
def predecir_paratheresia(
    dias: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Predicción de demanda y producción necesaria para Paratheresia claripalpis."""
    return PrediccionService(db).predecir_paratheresia(dias)

@router.get("/todas")
def predecir_todas(
    dias: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    """Predicción de demanda y producción necesaria para todas las especies."""
    return PrediccionService(db).predecir_todas(dias)