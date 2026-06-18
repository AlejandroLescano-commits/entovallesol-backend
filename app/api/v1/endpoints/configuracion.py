from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.infrastructure.database.session import get_db
from app.core.dependencies import require_admin, get_current_user
from app.domain.entities.lugares import LugarLiberacionAvispitas, LugarLiberacionMoscas
from app.domain.entities.unidades import (
    UnidadMedidasitodroga, UnidadMedidaAvispas,
    UnidadDeMedidaGalleria, UnidadDeMedidaMoscas,
)
from app.domain.schemas.produccion_schema import (
    LugarLiberacionCreate, LugarLiberacionUpdate, LugarLiberacionResponse,
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

# ── Lugares Avispitas ───────────────────────────────────────────────────────
@router.get("/lugares/avispitas")
def lugares_avispitas(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(LugarLiberacionAvispitas).filter(LugarLiberacionAvispitas.activo == True).all()

@router.get("/lugares/avispitas/todos", response_model=list[LugarLiberacionResponse])
def lugares_avispitas_todos(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(LugarLiberacionAvispitas).order_by(LugarLiberacionAvispitas.nombre).all()

@router.post("/lugares/avispitas", response_model=LugarLiberacionResponse, status_code=201)
def crear_lugar_avispitas(data: LugarLiberacionCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    obj = LugarLiberacionAvispitas(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.put("/lugares/avispitas/{id}", response_model=LugarLiberacionResponse)
def actualizar_lugar_avispitas(id: int, data: LugarLiberacionUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    obj = db.query(LugarLiberacionAvispitas).filter(LugarLiberacionAvispitas.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Lugar no encontrado")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/lugares/avispitas/{id}")
def eliminar_lugar_avispitas(id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    obj = db.query(LugarLiberacionAvispitas).filter(LugarLiberacionAvispitas.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Lugar no encontrado")
    try:
        db.delete(obj)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar: el lugar está en uso en notas de salida. Desactívelo en su lugar."
        )
    return {"id": id, "eliminado": True}

# ── Lugares Moscas ──────────────────────────────────────────────────────────
@router.get("/lugares/moscas")
def lugares_moscas(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(LugarLiberacionMoscas).filter(LugarLiberacionMoscas.activo == True).all()

@router.get("/lugares/moscas/todos", response_model=list[LugarLiberacionResponse])
def lugares_moscas_todos(db: Session = Depends(get_db), _=Depends(require_admin)):
    return db.query(LugarLiberacionMoscas).order_by(LugarLiberacionMoscas.nombre).all()

@router.post("/lugares/moscas", response_model=LugarLiberacionResponse, status_code=201)
def crear_lugar_moscas(data: LugarLiberacionCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    obj = LugarLiberacionMoscas(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

@router.put("/lugares/moscas/{id}", response_model=LugarLiberacionResponse)
def actualizar_lugar_moscas(id: int, data: LugarLiberacionUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    obj = db.query(LugarLiberacionMoscas).filter(LugarLiberacionMoscas.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Lugar no encontrado")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(obj, k, v)
    db.commit()
    db.refresh(obj)
    return obj

@router.delete("/lugares/moscas/{id}")
def eliminar_lugar_moscas(id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    obj = db.query(LugarLiberacionMoscas).filter(LugarLiberacionMoscas.id == id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="Lugar no encontrado")
    try:
        db.delete(obj)
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="No se puede eliminar: el lugar está en uso en notas de salida. Desactívelo en su lugar."
        )
    return {"id": id, "eliminado": True}

# ── Unidades (sin cambios) ────────────────────────────────────────────────────
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
