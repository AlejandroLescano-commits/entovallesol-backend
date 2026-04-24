from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.infrastructure.database.session import get_db
from app.core.dependencies import require_admin, get_current_user
from app.domain.entities.lugares import LugarLiberacionAvispitas, LugarLiberacionMoscas
from app.domain.entities.unidades import (
    UnidadMedidasitodroga, UnidadMedidaAvispas,
    UnidadDeMedidaGalleria, UnidadDeMedidaMoscas,
)

router = APIRouter()

@router.get("/")
def obtener_config(_=Depends(require_admin)):
    return {
        "especies": [
            "sitotroga",
            "trichogramma_exiguum",
            "trichogramma_pretiosum",
            "galleria",
            "paratheresia"
        ],
        "roles": ["admin", "supervisor", "operario"],
        "version": "1.0.0"
    }

@router.get("/lugares/avispitas")
def lugares_avispitas(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(LugarLiberacionAvispitas).filter(LugarLiberacionAvispitas.activo == True).all()

@router.get("/lugares/moscas")
def lugares_moscas(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(LugarLiberacionMoscas).filter(LugarLiberacionMoscas.activo == True).all()

@router.get("/unidades/sitodroga")
def unidades_sitodroga(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(UnidadMedidasitodroga).filter(UnidadMedidasitodroga.activo == True).all()

@router.get("/unidades/avispas")
def unidades_avispas(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(UnidadMedidaAvispas).filter(UnidadMedidaAvispas.activo == True).all()

@router.get("/unidades/galleria")
def unidades_galleria(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(UnidadDeMedidaGalleria).filter(UnidadDeMedidaGalleria.activo == True).all()

@router.get("/unidades/moscas")
def unidades_moscas(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(UnidadDeMedidaMoscas).filter(UnidadDeMedidaMoscas.activo == True).all()