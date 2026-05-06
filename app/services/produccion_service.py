from sqlalchemy.orm import Session
from typing import Optional
from datetime import date, datetime
from math import floor
from app.infrastructure.repositories.produccion_repository import ProduccionRepository
from app.domain.schemas.produccion_schema import (
    ProduccionSitotrogaCreate, ProduccionTrichogrammaCreate,
    ProduccionGalleriaCreate, ProduccionParathesiaCreate,
    NotaSalidaSitodrogaCreate, NotaSalidaAvispitasCreate,
    NotaSalidaMoscasCreate, NotaSalidaGalleriaCreate,
)

class ProduccionService:
    def __init__(self, db: Session):
        self.repo = ProduccionRepository(db)

    # ── Producción ────────────────────────────────────────────────────────────
    def registrar_sitotroga(self, data: ProduccionSitotrogaCreate, user_id: int):
        return self.repo.create_sitotroga({**data.model_dump(), "registrado_por": user_id})

    def listar_sitotroga(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        return self.repo.list_sitotroga(fecha_inicio, fecha_fin)

    def registrar_trichogramma(self, data: ProduccionTrichogrammaCreate, user_id: int):
        return self.repo.create_trichogramma({**data.model_dump(), "registrado_por": user_id})

    def listar_trichogramma(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        return self.repo.list_trichogramma(fecha_inicio, fecha_fin)

    def registrar_galleria(self, data: ProduccionGalleriaCreate, user_id: int):
        return self.repo.create_galleria({**data.model_dump(), "registrado_por": user_id})

    def listar_galleria(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        return self.repo.list_galleria(fecha_inicio, fecha_fin)

    def registrar_paratheresia(self, data: ProduccionParathesiaCreate, user_id: int):
        return self.repo.create_paratheresia({**data.model_dump(), "registrado_por": user_id})

    def listar_paratheresia(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        return self.repo.list_paratheresia(fecha_inicio, fecha_fin)

    # ── Notas de Salida ───────────────────────────────────────────────────────
    def registrar_nota_sitodroga(self, data: NotaSalidaSitodrogaCreate, user_id: int):
        payload = data.model_dump()

        # Primero guardamos la nota para obtener su ID
        nota = self.repo.create_nota_sitodroga({**payload, "registrado_por": user_id})

        # Efecto secundario: genera producción de Trichogramma enlazada
        if data.tiposalida == "T.exiguum":
            planchas = (data.cantidad - data.factor) / 12.5
            self.repo.create_trichogramma({
                "fecha": data.fecha,
                "cantidad": planchas * 80,  # pulg²
                "id_unidad": data.id_unidad,
                "registrado_por": user_id,
                "nota_origen_id": nota.id,
            })

        return nota

    def listar_notas_sitodroga(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        return self.repo.list_notas_sitodroga(fecha_inicio, fecha_fin)

    def registrar_nota_avispitas(self, data: NotaSalidaAvispitasCreate, user_id: int):
        return self.repo.create_nota_avispitas({**data.model_dump(), "registrado_por": user_id})

    def listar_notas_avispitas(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        return self.repo.list_notas_avispitas(fecha_inicio, fecha_fin)

    def registrar_nota_moscas(self, data: NotaSalidaMoscasCreate, user_id: int):
        return self.repo.create_nota_moscas({**data.model_dump(), "registrado_por": user_id})

    def listar_notas_moscas(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        return self.repo.list_notas_moscas(fecha_inicio, fecha_fin)

    def listar_notas_galleria(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        return self.repo.list_notas_galleria(fecha_inicio, fecha_fin)

    def registrar_nota_galleria(self, data: NotaSalidaGalleriaCreate, user_id: int):
        payload = data.model_dump()

        # Primero guardamos la nota para obtener su ID
        nota = self.repo.create_nota_galleria({**payload, "registrado_por": user_id})

        # Efecto secundario: genera producción de Paratheresia enlazada
        if data.tiposalida == "Paratheresia" and data.ratio:
            parejas = floor(data.cantidad / data.ratio)
            self.repo.create_paratheresia({
                "fecha": data.fecha,
                "cantidad": parejas,
                "id_unidad": data.id_unidad,
                "registrado_por": user_id,
                "nota_origen_id": nota.id,
            })

        return nota

    # ── Anulaciones Producción ────────────────────────────────────────────────
    def anular_sitotroga(self, id: int, user_id: int):
        try:
            obj = self.repo.anular_sitotroga(id, user_id)
            self.repo.db.commit()
            self.repo.db.refresh(obj)
            return obj
        except Exception:
            self.repo.db.rollback()
            raise

    def anular_trichogramma(self, id: int, user_id: int):
        try:
            obj = self.repo.anular_trichogramma(id, user_id)
            self.repo.db.commit()
            self.repo.db.refresh(obj)
            return obj
        except Exception:
            self.repo.db.rollback()
            raise

    def anular_galleria(self, id: int, user_id: int):
        try:
            obj = self.repo.anular_galleria(id, user_id)
            self.repo.db.commit()
            self.repo.db.refresh(obj)
            return obj
        except Exception:
            self.repo.db.rollback()
            raise

    def anular_paratheresia(self, id: int, user_id: int):
        try:
            obj = self.repo.anular_paratheresia(id, user_id)
            self.repo.db.commit()
            self.repo.db.refresh(obj)
            return obj
        except Exception:
            self.repo.db.rollback()
            raise

    # ── Anulaciones Notas de Salida ───────────────────────────────────────────
    def anular_nota_sitodroga(self, id: int, user_id: int):
        """
        Si era T.exiguum, anula también el ProduccionTrichogramma
        que se creó automáticamente. Todo en una sola transacción.
        """
        try:
            nota = self.repo.anular_nota_sitodroga(id, user_id)

            if nota.tiposalida == "T.exiguum":
                trich = self.repo.find_trichogramma_por_nota(id)
                if trich:
                    trich.activo = False
                    trich.anulado_por = user_id
                    trich.anulado_en = datetime.utcnow()

            self.repo.db.commit()
            self.repo.db.refresh(nota)
            return nota
        except Exception:
            self.repo.db.rollback()
            raise

    def anular_nota_avispitas(self, id: int, user_id: int):
        try:
            obj = self.repo.anular_nota_avispitas(id, user_id)
            self.repo.db.commit()
            self.repo.db.refresh(obj)
            return obj
        except Exception:
            self.repo.db.rollback()
            raise

    def anular_nota_moscas(self, id: int, user_id: int):
        try:
            obj = self.repo.anular_nota_moscas(id, user_id)
            self.repo.db.commit()
            self.repo.db.refresh(obj)
            return obj
        except Exception:
            self.repo.db.rollback()
            raise

    def anular_nota_galleria(self, id: int, user_id: int):
        """
        Si era Paratheresia, anula también el ProduccionParatheresia
        que se creó automáticamente. Todo en una sola transacción.
        """
        try:
            nota = self.repo.anular_nota_galleria(id, user_id)

            if nota.tiposalida == "Paratheresia":
                par = self.repo.find_paratheresia_por_nota(id)
                if par:
                    par.activo = False
                    par.anulado_por = user_id
                    par.anulado_en = datetime.utcnow()

            self.repo.db.commit()
            self.repo.db.refresh(nota)
            return nota
        except Exception:
            self.repo.db.rollback()
            raise
