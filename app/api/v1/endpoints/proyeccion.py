from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import timedelta
from app.infrastructure.database.session import get_db
from app.core.dependencies import get_current_user
from app.domain.entities.conversion import ConversionParametros
from app.domain.schemas.produccion_schema import ProyeccionRequest, ProyeccionResponse

router = APIRouter()

@router.post("/calcular", response_model=ProyeccionResponse)
def calcular_proyeccion(
    data: ProyeccionRequest,
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    param = db.query(ConversionParametros).filter(
        ConversionParametros.especie_destino == data.especie_destino,
        ConversionParametros.activo == True
    ).first()

    if not param:
        raise HTTPException(
            status_code=404,
            detail=f"No hay parámetros de conversión para {data.especie_destino}"
        )

    cantidad_origen = float(data.cantidad_objetivo) / float(param.factor)
    fecha_inicio    = data.fecha_objetivo - timedelta(days=param.dias_ciclo)

    return ProyeccionResponse(
        especie_destino           = data.especie_destino,
        cantidad_objetivo         = data.cantidad_objetivo,
        fecha_objetivo            = data.fecha_objetivo,
        especie_origen            = param.especie_origen,
        cantidad_origen_necesaria = round(cantidad_origen, 2),
        unidad_origen             = param.unidad_origen,
        fecha_inicio_produccion   = fecha_inicio,
        dias_ciclo                = param.dias_ciclo,
        factor                    = float(param.factor)
    )

@router.get("/parametros")
def obtener_parametros(
    db: Session = Depends(get_db),
    _=Depends(get_current_user)
):
    return db.query(ConversionParametros).filter(
        ConversionParametros.activo == True
    ).all()
