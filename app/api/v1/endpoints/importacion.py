from fastapi import APIRouter, Depends, UploadFile, File, Query
from sqlalchemy.orm import Session
from app.infrastructure.database.session import get_db
from app.core.dependencies import require_admin
from app.services.importacion_service import ImportacionService

router = APIRouter()

@router.post("/sitotroga")
async def importar_sitotroga(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    cu=Depends(require_admin)
):
    content = await file.read()
    return ImportacionService(db).importar_sitotroga(content, cu.id)
