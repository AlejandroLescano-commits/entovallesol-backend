from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.orm import Session
from app.infrastructure.database.session import get_db
from app.core.dependencies import require_admin
from app.services.importacion_service import ImportacionService

router = APIRouter()

@router.post("/sitotroga")
async def importar_sitotroga(file: UploadFile = File(...), db: Session = Depends(get_db), cu=Depends(require_admin)):
    return ImportacionService(db).importar_sitotroga(await file.read(), cu.id)

@router.post("/trichogramma")
async def importar_trichogramma(file: UploadFile = File(...), db: Session = Depends(get_db), cu=Depends(require_admin)):
    return ImportacionService(db).importar_trichogramma(await file.read(), cu.id)

@router.post("/galleria")
async def importar_galleria(file: UploadFile = File(...), db: Session = Depends(get_db), cu=Depends(require_admin)):
    return ImportacionService(db).importar_galleria(await file.read(), cu.id)

@router.post("/paratheresia")
async def importar_paratheresia(file: UploadFile = File(...), db: Session = Depends(get_db), cu=Depends(require_admin)):
    return ImportacionService(db).importar_paratheresia(await file.read(), cu.id)