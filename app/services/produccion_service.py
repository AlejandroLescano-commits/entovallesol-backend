from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
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
        return self.repo.create_nota_sitodroga({**data.model_dump(), "registrado_por": user_id})

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

        if data.tiposalida == "Paratheresia" and data.ratio:
            parejas = floor(data.cantidad / data.ratio)

            # 👉 afecta saldo de Paratheresia
            self.repo.create_paratheresia({
                "fecha": data.fecha,
                "cantidad": parejas,
                "id_unidad": data.id_unidad,
                "registrado_por": user_id
            })

        # 👉 guarda la nota normal
        return self.repo.create_nota_galleria({**payload, "registrado_por": user_id})