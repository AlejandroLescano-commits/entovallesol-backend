from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.orm import Session
from datetime import date
from app.infrastructure.database.session import get_db
from app.core.dependencies import get_current_user
from app.services.reporte_service import ReporteService

router = APIRouter()

@router.get("/excel/sitotroga")
def excel_sitotroga(
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    db: Session = Depends(get_db), _=Depends(get_current_user)
):
    data = ReporteService(db).generar_excel_sitotroga(fecha_inicio, fecha_fin)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=sitotroga_{fecha_inicio}_{fecha_fin}.xlsx"}
    )

@router.get("/excel/trichogramma")
def excel_trichogramma(
    especie: str = Query(...),
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    db: Session = Depends(get_db), _=Depends(get_current_user)
):
    data = ReporteService(db).generar_excel_trichogramma(especie, fecha_inicio, fecha_fin)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=trichogramma_{especie}_{fecha_inicio}_{fecha_fin}.xlsx"}
    )
