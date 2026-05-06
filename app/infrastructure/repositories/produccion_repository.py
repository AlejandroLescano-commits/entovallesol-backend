from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime
from app.domain.entities.produccion_sitotroga import ProduccionSitotroga
from app.domain.entities.produccion_trichogramma import ProduccionTrichogramma
from app.domain.entities.produccion_galleria import ProduccionGalleria
from app.domain.entities.produccion_paratheresia import ProduccionParatheresia
from app.domain.entities.notas_salida import (
    NotaSalidaSitodroga, NotaSalidaAvispitas,
    NotaSalidaMoscas, NotaSalidaGalleriamelonella,
)

class ProduccionRepository:
    def __init__(self, db: Session):
        self.db = db

    # ── Producción ────────────────────────────────────────────────────────────
    def create_sitotroga(self, data: dict):
        obj = ProduccionSitotroga(**data)
        self.db.add(obj); self.db.commit(); self.db.refresh(obj)
        return obj

    def list_sitotroga(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        q = self.db.query(ProduccionSitotroga).filter(ProduccionSitotroga.activo == True)
        if fecha_inicio: q = q.filter(ProduccionSitotroga.fecha >= fecha_inicio)
        if fecha_fin:    q = q.filter(ProduccionSitotroga.fecha <= fecha_fin)
        return q.order_by(ProduccionSitotroga.fecha.desc()).all()

    def create_trichogramma(self, data: dict):
        obj = ProduccionTrichogramma(**data)
        self.db.add(obj); self.db.commit(); self.db.refresh(obj)
        return obj

    def list_trichogramma(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        q = self.db.query(ProduccionTrichogramma).filter(ProduccionTrichogramma.activo == True)
        if fecha_inicio: q = q.filter(ProduccionTrichogramma.fecha >= fecha_inicio)
        if fecha_fin:    q = q.filter(ProduccionTrichogramma.fecha <= fecha_fin)
        return q.order_by(ProduccionTrichogramma.fecha.desc()).all()

    def create_galleria(self, data: dict):
        obj = ProduccionGalleria(**data)
        self.db.add(obj); self.db.commit(); self.db.refresh(obj)
        return obj

    def list_galleria(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        q = self.db.query(ProduccionGalleria).filter(ProduccionGalleria.activo == True)
        if fecha_inicio: q = q.filter(ProduccionGalleria.fecha >= fecha_inicio)
        if fecha_fin:    q = q.filter(ProduccionGalleria.fecha <= fecha_fin)
        return q.order_by(ProduccionGalleria.fecha.desc()).all()

    def create_paratheresia(self, data: dict):
        obj = ProduccionParatheresia(**data)
        self.db.add(obj); self.db.commit(); self.db.refresh(obj)
        return obj

    def list_paratheresia(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        q = self.db.query(ProduccionParatheresia).filter(ProduccionParatheresia.activo == True)
        if fecha_inicio: q = q.filter(ProduccionParatheresia.fecha >= fecha_inicio)
        if fecha_fin:    q = q.filter(ProduccionParatheresia.fecha <= fecha_fin)
        return q.order_by(ProduccionParatheresia.fecha.desc()).all()

    # ── Notas de Salida ───────────────────────────────────────────────────────
    def create_nota_sitodroga(self, data: dict):
        obj = NotaSalidaSitodroga(**data)
        self.db.add(obj); self.db.commit(); self.db.refresh(obj)
        return obj

    def list_notas_sitodroga(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        q = self.db.query(NotaSalidaSitodroga).filter(NotaSalidaSitodroga.activo == True)
        if fecha_inicio: q = q.filter(NotaSalidaSitodroga.fecha >= fecha_inicio)
        if fecha_fin:    q = q.filter(NotaSalidaSitodroga.fecha <= fecha_fin)
        return q.order_by(NotaSalidaSitodroga.fecha.desc()).all()

    def create_nota_avispitas(self, data: dict):
        obj = NotaSalidaAvispitas(**data)
        self.db.add(obj); self.db.commit(); self.db.refresh(obj)
        return obj

    def list_notas_avispitas(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        q = self.db.query(NotaSalidaAvispitas).filter(NotaSalidaAvispitas.activo == True)
        if fecha_inicio: q = q.filter(NotaSalidaAvispitas.fecha >= fecha_inicio)
        if fecha_fin:    q = q.filter(NotaSalidaAvispitas.fecha <= fecha_fin)
        return q.order_by(NotaSalidaAvispitas.fecha.desc()).all()

    def create_nota_moscas(self, data: dict):
        obj = NotaSalidaMoscas(**data)
        self.db.add(obj); self.db.commit(); self.db.refresh(obj)
        return obj

    def list_notas_moscas(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        q = self.db.query(NotaSalidaMoscas).filter(NotaSalidaMoscas.activo == True)
        if fecha_inicio: q = q.filter(NotaSalidaMoscas.fecha >= fecha_inicio)
        if fecha_fin:    q = q.filter(NotaSalidaMoscas.fecha <= fecha_fin)
        return q.order_by(NotaSalidaMoscas.fecha.desc()).all()

    def create_nota_galleria(self, data: dict):
        obj = NotaSalidaGalleriamelonella(**data)
        self.db.add(obj); self.db.commit(); self.db.refresh(obj)
        return obj

    def list_notas_galleria(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        q = self.db.query(NotaSalidaGalleriamelonella).filter(NotaSalidaGalleriamelonella.activo == True)
        if fecha_inicio: q = q.filter(NotaSalidaGalleriamelonella.fecha >= fecha_inicio)
        if fecha_fin:    q = q.filter(NotaSalidaGalleriamelonella.fecha <= fecha_fin)

        return q.order_by(NotaSalidaGalleriamelonella.fecha.desc()).all()
    def anular_sitotroga(self, id: int, user_id: int):
        obj = self.db.query(ProduccionSitotroga).filter(
            ProduccionSitotroga.id == id, ProduccionSitotroga.activo == True
        ).first()
        if not obj:
            raise ValueError("Registro no encontrado o ya anulado")
        obj.activo = False
        obj.anulado_por = user_id
        obj.anulado_en = datetime.utcnow()
        return obj  # sin commit — el service lo maneja

    def anular_trichogramma(self, id: int, user_id: int):
        obj = self.db.query(ProduccionTrichogramma).filter(
            ProduccionTrichogramma.id == id, ProduccionTrichogramma.activo == True
        ).first()
        if not obj:
            raise ValueError("Registro no encontrado o ya anulado")
        obj.activo = False
        obj.anulado_por = user_id
        obj.anulado_en = datetime.utcnow()
        return obj

    def anular_galleria(self, id: int, user_id: int):
        obj = self.db.query(ProduccionGalleria).filter(
            ProduccionGalleria.id == id, ProduccionGalleria.activo == True
        ).first()
        if not obj:
            raise ValueError("Registro no encontrado o ya anulado")
        obj.activo = False
        obj.anulado_por = user_id
        obj.anulado_en = datetime.utcnow()
        return obj

    def anular_paratheresia(self, id: int, user_id: int):
        obj = self.db.query(ProduccionParatheresia).filter(
            ProduccionParatheresia.id == id, ProduccionParatheresia.activo == True
        ).first()
        if not obj:
            raise ValueError("Registro no encontrado o ya anulado")
        obj.activo = False
        obj.anulado_por = user_id
        obj.anulado_en = datetime.utcnow()
        return obj

    def anular_nota_sitodroga(self, id: int, user_id: int):
        obj = self.db.query(NotaSalidaSitodroga).filter(
            NotaSalidaSitodroga.id == id, NotaSalidaSitodroga.activo == True
        ).first()
        if not obj:
            raise ValueError("Nota no encontrada o ya anulada")
        obj.activo = False
        obj.anulado_por = user_id
        obj.anulado_en = datetime.utcnow()
        return obj

    def anular_nota_avispitas(self, id: int, user_id: int):
        obj = self.db.query(NotaSalidaAvispitas).filter(
            NotaSalidaAvispitas.id == id, NotaSalidaAvispitas.activo == True
        ).first()
        if not obj:
            raise ValueError("Nota no encontrada o ya anulada")
        obj.activo = False
        obj.anulado_por = user_id
        obj.anulado_en = datetime.utcnow()
        return obj

    def anular_nota_moscas(self, id: int, user_id: int):
        obj = self.db.query(NotaSalidaMoscas).filter(
            NotaSalidaMoscas.id == id, NotaSalidaMoscas.activo == True
        ).first()
        if not obj:
            raise ValueError("Nota no encontrada o ya anulada")
        obj.activo = False
        obj.anulado_por = user_id
        obj.anulado_en = datetime.utcnow()
        return obj

    def anular_nota_galleria(self, id: int, user_id: int):
        obj = self.db.query(NotaSalidaGalleriamelonella).filter(
            NotaSalidaGalleriamelonella.id == id, NotaSalidaGalleriamelonella.activo == True
        ).first()
        if not obj:
            raise ValueError("Nota no encontrada o ya anulada")
        obj.activo = False
        obj.anulado_por = user_id
        obj.anulado_en = datetime.utcnow()
        return obj

    # Helper: buscar registro de trichogramma asociado a una nota de sitodroga
    def find_trichogramma_por_nota(self, nota_id: int):
        """Busca el registro de trichogramma que fue creado automáticamente por una nota sitodroga T.exiguum"""
        return self.db.query(ProduccionTrichogramma).filter(
            ProduccionTrichogramma.nota_origen_id == nota_id,
            ProduccionTrichogramma.activo == True
        ).first()

    # Helper: buscar registro de paratheresia asociado a una nota de galleria
    def find_paratheresia_por_nota(self, nota_id: int):
        return self.db.query(ProduccionParatheresia).filter(
            ProduccionParatheresia.nota_origen_id == nota_id,
            ProduccionParatheresia.activo == True
        ).first()
