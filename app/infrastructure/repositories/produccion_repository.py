from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import Optional
from datetime import date
from app.domain.entities.produccion_sitotroga import ProduccionSitotroga
from app.domain.entities.produccion_trichogramma import ProduccionTrichogramma
from app.domain.entities.produccion_galleria import ProduccionGalleria
from app.domain.entities.produccion_paratheresia import ProduccionParatheresia

class ProduccionRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Sitotroga ──
    def create_sitotroga(self, data: dict):
        obj = ProduccionSitotroga(**data)
        self.db.add(obj); self.db.commit(); self.db.refresh(obj); return obj

    def list_sitotroga(self, fi: Optional[date], ff: Optional[date]):
        q = self.db.query(ProduccionSitotroga)
        if fi: q = q.filter(ProduccionSitotroga.fecha >= fi)
        if ff: q = q.filter(ProduccionSitotroga.fecha <= ff)
        return q.order_by(ProduccionSitotroga.fecha).all()

    def get_ultimo_saldo_sitotroga(self) -> Optional[float]:
        r = self.db.query(ProduccionSitotroga).order_by(desc(ProduccionSitotroga.fecha)).first()
        return r.saldo if r else None

    # ── Trichogramma ──
    def create_trichogramma(self, data: dict):
        obj = ProduccionTrichogramma(**data)
        self.db.add(obj); self.db.commit(); self.db.refresh(obj); return obj

    def list_trichogramma(self, especie: Optional[str], fi: Optional[date], ff: Optional[date]):
        q = self.db.query(ProduccionTrichogramma)
        if especie: q = q.filter(ProduccionTrichogramma.especie == especie)
        if fi: q = q.filter(ProduccionTrichogramma.fecha >= fi)
        if ff: q = q.filter(ProduccionTrichogramma.fecha <= ff)
        return q.order_by(ProduccionTrichogramma.fecha).all()

    def get_ultimo_saldo_trichogramma(self, especie: str) -> Optional[float]:
        r = (self.db.query(ProduccionTrichogramma)
             .filter(ProduccionTrichogramma.especie == especie)
             .order_by(desc(ProduccionTrichogramma.fecha)).first())
        return r.saldo if r else None

    # ── Galleria ──
    def create_galleria(self, data: dict):
        obj = ProduccionGalleria(**data)
        self.db.add(obj); self.db.commit(); self.db.refresh(obj); return obj

    def list_galleria(self, fi: Optional[date], ff: Optional[date]):
        q = self.db.query(ProduccionGalleria)
        if fi: q = q.filter(ProduccionGalleria.fecha >= fi)
        if ff: q = q.filter(ProduccionGalleria.fecha <= ff)
        return q.order_by(ProduccionGalleria.fecha).all()

    def get_ultimo_saldo_galleria(self) -> Optional[float]:
        r = self.db.query(ProduccionGalleria).order_by(desc(ProduccionGalleria.fecha)).first()
        return r.saldo if r else None

    # ── Paratheresia ──
    def create_paratheresia(self, data: dict):
        obj = ProduccionParatheresia(**data)
        self.db.add(obj); self.db.commit(); self.db.refresh(obj); return obj

    def list_paratheresia(self, fi: Optional[date], ff: Optional[date]):
        q = self.db.query(ProduccionParatheresia)
        if fi: q = q.filter(ProduccionParatheresia.fecha >= fi)
        if ff: q = q.filter(ProduccionParatheresia.fecha <= ff)
        return q.order_by(ProduccionParatheresia.fecha).all()

    def get_ultimo_saldo_paratheresia(self) -> Optional[float]:
        r = self.db.query(ProduccionParatheresia).order_by(desc(ProduccionParatheresia.fecha)).first()
        return r.saldo if r else None
