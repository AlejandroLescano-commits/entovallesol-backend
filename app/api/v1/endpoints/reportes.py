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
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    db: Session = Depends(get_db), _=Depends(get_current_user)
):
    data = ReporteService(db).generar_excel_trichogramma(fecha_inicio, fecha_fin)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=trichogramma_{fecha_inicio}_{fecha_fin}.xlsx"}
    )

@router.get("/excel/galleria")
def excel_galleria(
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    db: Session = Depends(get_db), _=Depends(get_current_user)
):
    data = ReporteService(db).generar_excel_galleria(fecha_inicio, fecha_fin)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=galleria_{fecha_inicio}_{fecha_fin}.xlsx"}
    )

@router.get("/excel/paratheresia")
def excel_paratheresia(
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    db: Session = Depends(get_db), _=Depends(get_current_user)
):
    data = ReporteService(db).generar_excel_paratheresia(fecha_inicio, fecha_fin)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=paratheresia_{fecha_inicio}_{fecha_fin}.xlsx"}
    )

@router.get("/excel/notas/sitodroga")
def excel_notas_sitodroga(
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    db: Session = Depends(get_db), _=Depends(get_current_user)
):
    data = ReporteService(db).generar_excel_notas_sitodroga(fecha_inicio, fecha_fin)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=notas_sitodroga_{fecha_inicio}_{fecha_fin}.xlsx"}
    )

@router.get("/excel/notas/avispitas")
def excel_notas_avispitas(
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    db: Session = Depends(get_db), _=Depends(get_current_user)
):
    data = ReporteService(db).generar_excel_notas_avispitas(fecha_inicio, fecha_fin)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=notas_avispitas_{fecha_inicio}_{fecha_fin}.xlsx"}
    )

@router.get("/excel/notas/moscas")
def excel_notas_moscas(
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    db: Session = Depends(get_db), _=Depends(get_current_user)
):
    data = ReporteService(db).generar_excel_notas_moscas(fecha_inicio, fecha_fin)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=notas_moscas_{fecha_inicio}_{fecha_fin}.xlsx"}
    )

@router.get("/excel/notas/galleria")
def excel_notas_galleria(
    fecha_inicio: date = Query(...),
    fecha_fin: date = Query(...),
    db: Session = Depends(get_db), _=Depends(get_current_user)
):
    data = ReporteService(db).generar_excel_notas_galleria(fecha_inicio, fecha_fin)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=notas_galleria_{fecha_inicio}_{fecha_fin}.xlsx"}
    )