from sqlalchemy.orm import Session
from app.domain.entities.usuario import Usuario

class UsuarioRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int):
        return self.db.query(Usuario).filter(Usuario.id == user_id).first()

    def get_by_email(self, email: str):
        return self.db.query(Usuario).filter(Usuario.email == email).first()

    def get_all(self):
        return self.db.query(Usuario).all()

    def create(self, data: dict):
        obj = Usuario(**data)
        self.db.add(obj)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def update(self, user_id: int, data: dict):
        obj = self.get_by_id(user_id)
        for k, v in data.items():
            setattr(obj, k, v)
        self.db.commit()
        self.db.refresh(obj)
        return obj

    def delete(self, user_id: int):
        obj = self.get_by_id(user_id)
        if obj:
            self.db.delete(obj)
            self.db.commit()
        return obj
