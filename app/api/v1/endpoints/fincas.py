from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.infrastructure.database.session import get_db
from app.core.dependencies import get_current_user
from app.domain.entities.finca import Finca

router = APIRouter()

@router.get("/")
def listar_fincas(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Finca).filter(Finca.activa == True).all()
