# app/api/v1/endpoints/entrenamiento.py
import os
from fastapi import APIRouter, Header, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.infrastructure.database.session import get_db
from app.core.dependencies import get_current_user
from app.services.entrenamiento_service import EntrenamientoService

router = APIRouter()
CRON_SECRET = os.getenv("CRON_SECRET")


@router.post("/entrenar")
def ejecutar_entrenamiento(
    x_cron_secret: str = Header(None),
    db: Session = Depends(get_db)
):
    if not CRON_SECRET or x_cron_secret != CRON_SECRET:
        raise HTTPException(status_code=403, detail="No autorizado")

    svc = EntrenamientoService(db)
    return {
        clave: svc.entrenar_especie(clave)
        for clave in ["sitotroga", "trichogramma", "galleria", "paratheresia"]
    }


@router.post("/entrenar/manual")
def entrenar_manual(
    especie: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    svc = EntrenamientoService(db)
    if especie:
        return {especie: svc.entrenar_especie(especie, forzar=True)}
    return {
        clave: svc.entrenar_especie(clave, forzar=True)
        for clave in ["sitotroga", "trichogramma", "galleria", "paratheresia"]
    }


@router.get("/config")
def get_config(db: Session = Depends(get_db)):
    svc = EntrenamientoService(db)
    return svc.get_todas_configs()


@router.patch("/config/{especie}")
def update_config(
    especie: str,
    activo: bool | None = Query(default=None),
    rango_meses: int | None = Query(default=None),
    db: Session = Depends(get_db)
):
    svc = EntrenamientoService(db)
    return svc.update_config(especie, activo, rango_meses)


@router.get("/kpis/{especie}")
def get_kpis(especie: str, db: Session = Depends(get_db)):
    svc = EntrenamientoService(db)
    return svc.get_kpis(especie)
