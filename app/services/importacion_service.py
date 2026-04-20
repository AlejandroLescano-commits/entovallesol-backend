import pandas as pd
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.services.produccion_service import ProduccionService
from app.domain.schemas.produccion_schema import ProduccionSitotrogaCreate, ProduccionTrichogrammaCreate

class ImportacionService:
    """Carga masiva desde archivos Excel con la misma estructura que usa ValleSol."""

    def __init__(self, db: Session):
        self.db = db
        self.produccion_svc = ProduccionService(db)

    def importar_sitotroga(self, file_bytes: bytes, user_id: int) -> dict:
        df = pd.read_excel(file_bytes, header=6)
        df.columns = ["fecha", "unidad", "produccion_dia", "salida_t_exiguum",
                      "salida_t_pretiosum", "salida_infestacion", "salida_ventas",
                      "salida_total", "saldo"]
        df = df.dropna(subset=["fecha"])
        count = 0
        for _, row in df.iterrows():
            try:
                data = ProduccionSitotrogaCreate(
                    fecha=row["fecha"].date() if hasattr(row["fecha"], "date") else row["fecha"],
                    produccion_dia=row.get("produccion_dia"),
                    salida_t_exiguum=row.get("salida_t_exiguum", 0) or 0,
                    salida_t_pretiosum=row.get("salida_t_pretiosum", 0) or 0,
                    salida_infestacion=row.get("salida_infestacion", 0) or 0,
                    salida_ventas=row.get("salida_ventas", 0) or 0,
                )
                self.produccion_svc.registrar_sitotroga(data, user_id)
                count += 1
            except Exception:
                continue
        return {"importados": count}
