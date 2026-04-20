from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.infrastructure.database.session import get_db
from app.core.dependencies import get_current_user, require_admin
from app.services.usuario_service import UsuarioService
from app.domain.schemas.usuario_schema import UsuarioCreate, UsuarioUpdate, UsuarioResponse

router = APIRouter()

@router.get("/", response_model=List[UsuarioResponse])
def listar(db: Session = Depends(get_db), _=Depends(require_admin)):
    return UsuarioService(db).listar()

@router.post("/", response_model=UsuarioResponse, status_code=201)
def crear(data: UsuarioCreate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return UsuarioService(db).crear(data)

@router.get("/{user_id}", response_model=UsuarioResponse)
def obtener(user_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return UsuarioService(db).obtener(user_id)

@router.put("/{user_id}", response_model=UsuarioResponse)
def actualizar(user_id: int, data: UsuarioUpdate, db: Session = Depends(get_db), _=Depends(require_admin)):
    return UsuarioService(db).actualizar(user_id, data)

@router.delete("/{user_id}", status_code=204)
def eliminar(user_id: int, db: Session = Depends(get_db), _=Depends(require_admin)):
    UsuarioService(db).eliminar(user_id)
