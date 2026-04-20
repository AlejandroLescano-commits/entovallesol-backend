from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.infrastructure.repositories.usuario_repository import UsuarioRepository
from app.domain.schemas.usuario_schema import UsuarioCreate, UsuarioUpdate
from app.core.security import hash_password

class UsuarioService:
    def __init__(self, db: Session):
        self.repo = UsuarioRepository(db)

    def crear(self, data: UsuarioCreate):
        if self.repo.get_by_email(data.email):
            raise HTTPException(status_code=400, detail="Email ya registrado")
        hashed = hash_password(data.password)
        return self.repo.create({**data.model_dump(exclude={"password"}), "password_hash": hashed})

    def listar(self):
        return self.repo.get_all()

    def obtener(self, user_id: int):
        u = self.repo.get_by_id(user_id)
        if not u:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return u

    def actualizar(self, user_id: int, data: UsuarioUpdate):
        return self.repo.update(user_id, data.model_dump(exclude_none=True))

    def eliminar(self, user_id: int):
        return self.repo.delete(user_id)
