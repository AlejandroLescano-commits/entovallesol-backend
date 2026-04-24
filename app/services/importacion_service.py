import pandas as pd
from sqlalchemy.orm import Session
from app.services.produccion_service import ProduccionService
from app.domain.schemas.produccion_schema import (
    ProduccionSitotrogaCreate, ProduccionTrichogrammaCreate,
    ProduccionGalleriaCreate, ProduccionParathesiaCreate,
)

class ImportacionService:
    """
    Carga masiva desde Excel.
    Formato esperado para todas las especies:
    Columnas: fecha | cantidad
    (opcionalmente: id_unidad)
    """

    def __init__(self, db: Session):
        self.db = db
        self.svc = ProduccionService(db)

    def _leer_excel(self, file_bytes: bytes) -> pd.DataFrame:
        df = pd.read_excel(file_bytes)
        df.columns = [c.strip().lower() for c in df.columns]
        df = df.dropna(subset=["fecha"])
        return df

    def importar_sitotroga(self, file_bytes: bytes, user_id: int) -> dict:
        df = self._leer_excel(file_bytes)
        count, errors = 0, 0
        for _, row in df.iterrows():
            try:
                data = ProduccionSitotrogaCreate(
                    fecha=row["fecha"].date() if hasattr(row["fecha"], "date") else row["fecha"],
                    cantidad=float(row.get("cantidad", 0) or 0),
                    id_unidad=int(row["id_unidad"]) if "id_unidad" in row and pd.notna(row["id_unidad"]) else None,
                )
                self.svc.registrar_sitotroga(data, user_id)
                count += 1
            except Exception:
                errors += 1
        return {"importados": count, "errores": errors}

    def importar_trichogramma(self, file_bytes: bytes, user_id: int) -> dict:
        df = self._leer_excel(file_bytes)
        count, errors = 0, 0
        for _, row in df.iterrows():
            try:
                data = ProduccionTrichogrammaCreate(
                    fecha=row["fecha"].date() if hasattr(row["fecha"], "date") else row["fecha"],
                    cantidad=float(row.get("cantidad", 0) or 0),
                    id_unidad=int(row["id_unidad"]) if "id_unidad" in row and pd.notna(row["id_unidad"]) else None,
                )
                self.svc.registrar_trichogramma(data, user_id)
                count += 1
            except Exception:
                errors += 1
        return {"importados": count, "errores": errors}

    def importar_galleria(self, file_bytes: bytes, user_id: int) -> dict:
        df = self._leer_excel(file_bytes)
        count, errors = 0, 0
        for _, row in df.iterrows():
            try:
                data = ProduccionGalleriaCreate(
                    fecha=row["fecha"].date() if hasattr(row["fecha"], "date") else row["fecha"],
                    cantidad=float(row.get("cantidad", 0) or 0),
                    id_unidad=int(row["id_unidad"]) if "id_unidad" in row and pd.notna(row["id_unidad"]) else None,
                )
                self.svc.registrar_galleria(data, user_id)
                count += 1
            except Exception:
                errors += 1
        return {"importados": count, "errores": errors}

    def importar_paratheresia(self, file_bytes: bytes, user_id: int) -> dict:
        df = self._leer_excel(file_bytes)
        count, errors = 0, 0
        for _, row in df.iterrows():
            try:
                data = ProduccionParathesiaCreate(
                    fecha=row["fecha"].date() if hasattr(row["fecha"], "date") else row["fecha"],
                    cantidad=float(row.get("cantidad", 0) or 0),
                    id_unidad=int(row["id_unidad"]) if "id_unidad" in row and pd.notna(row["id_unidad"]) else None,
                )
                self.svc.registrar_paratheresia(data, user_id)
                count += 1
            except Exception:
                errors += 1
        return {"importados": count, "errores": errors}