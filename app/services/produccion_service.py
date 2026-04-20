from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date
from app.infrastructure.repositories.produccion_repository import ProduccionRepository
from app.domain.schemas.produccion_schema import (
    ProduccionSitotrogaCreate, ProduccionTrichogrammaCreate,
    ProduccionGalleriaCreate, ProduccionParathesiaCreate,
)

class ProduccionService:
    def __init__(self, db: Session):
        self.repo = ProduccionRepository(db)

    # ── Sitotroga ──
    def registrar_sitotroga(self, data: ProduccionSitotrogaCreate, user_id: int):
        salida_total = (data.salida_t_exiguum + data.salida_t_pretiosum
                        + data.salida_infestacion + data.salida_ventas)
        ultimo_saldo = self.repo.get_ultimo_saldo_sitotroga()
        saldo = (ultimo_saldo or 0) + (data.produccion_dia or 0) - salida_total
        return self.repo.create_sitotroga({**data.model_dump(), "salida_total": salida_total,
                                           "saldo": saldo, "registrado_por": user_id})

    def listar_sitotroga(self, fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        return self.repo.list_sitotroga(fecha_inicio, fecha_fin)

    # ── Trichogramma ──
    def registrar_trichogramma(self, data: ProduccionTrichogrammaCreate, user_id: int):
        salida_total = (data.salida_parasitacion + data.salida_san_ricardo_a +
                        data.salida_san_ricardo_b + data.salida_quemazón +
                        data.salida_trapiche + data.salida_segundo_jiron +
                        data.salida_pabellon_alto + data.salida_sacachique +
                        data.salida_la_encantada + data.salida_ventas)
        ultimo_saldo = self.repo.get_ultimo_saldo_trichogramma(data.especie)
        saldo = (ultimo_saldo or 0) + data.produccion_dia - salida_total
        return self.repo.create_trichogramma({**data.model_dump(), "salida_total": salida_total,
                                              "saldo": saldo, "registrado_por": user_id})

    def listar_trichogramma(self, especie: Optional[str], fecha_inicio: Optional[date], fecha_fin: Optional[date]):
        return self.repo.list_trichogramma(especie, fecha_inicio, fecha_fin)

    # ── Galleria ──
    def registrar_galleria(self, data: ProduccionGalleriaCreate, user_id: int):
        salida_total = data.salida_paratheresia + data.salida_instalacion + data.salida_ventas
        ultimo_saldo = self.repo.get_ultimo_saldo_galleria()
        saldo = (ultimo_saldo or 0) + data.produccion_dia - salida_total
        return self.repo.create_galleria({**data.model_dump(), "salida_total": salida_total,
                                          "saldo": saldo, "registrado_por": user_id})

    # ── Paratheresia ──
    def registrar_paratheresia(self, data: ProduccionParathesiaCreate, user_id: int):
        salida_total = (data.salida_parasitacion + data.salida_quemazón +
                        data.salida_segundo_jiron + data.salida_san_ricardo_a +
                        data.salida_san_ricardo_b + data.salida_sacachique +
                        data.salida_pabellon_alto + data.salida_trapiche + data.salida_ventas)
        ultimo_saldo = self.repo.get_ultimo_saldo_paratheresia()
        saldo = (ultimo_saldo or 0) + data.produccion_dia - salida_total
        return self.repo.create_paratheresia({**data.model_dump(), "salida_total": salida_total,
                                              "saldo": saldo, "registrado_por": user_id})
