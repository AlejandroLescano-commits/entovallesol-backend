from sqlalchemy.orm import Session
from datetime import date
import io, openpyxl
from app.infrastructure.repositories.produccion_repository import ProduccionRepository

class ReporteService:
    def __init__(self, db: Session):
        self.repo = ProduccionRepository(db)

    def generar_excel_sitotroga(self, fecha_inicio: date, fecha_fin: date) -> bytes:
        registros = self.repo.list_sitotroga(fecha_inicio, fecha_fin)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Sitotroga"
        headers = ["ID", "Fecha", "Producción/día (g)", "Salida T.exiguum", "Salida T.pretiosum",
                   "Infestación", "Ventas", "Total Salida", "Saldo"]
        ws.append(headers)
        for r in registros:
            ws.append([r.id, str(r.fecha), r.produccion_dia, r.salida_t_exiguum,
                       r.salida_t_pretiosum, r.salida_infestacion, r.salida_ventas,
                       r.salida_total, r.saldo])
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()

    def generar_excel_trichogramma(self, especie: str, fecha_inicio: date, fecha_fin: date) -> bytes:
        registros = self.repo.list_trichogramma(especie, fecha_inicio, fecha_fin)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = f"Trichogramma_{especie}"
        headers = ["ID", "Fecha", "Especie", "Producción/día (pulg²)", "Parasitación",
                   "San Ricardo A", "San Ricardo B", "Quemazón", "Trapiche",
                   "2do Jirón", "Pabellón Alto", "Sacachique", "La Encantada",
                   "Ventas", "Total Salida", "Saldo", "% Eclosión"]
        ws.append(headers)
        for r in registros:
            ws.append([r.id, str(r.fecha), r.especie, r.produccion_dia, r.salida_parasitacion,
                       r.salida_san_ricardo_a, r.salida_san_ricardo_b, r.salida_quemazón,
                       r.salida_trapiche, r.salida_segundo_jiron, r.salida_pabellon_alto,
                       r.salida_sacachique, r.salida_la_encantada, r.salida_ventas,
                       r.salida_total, r.saldo, r.porcentaje_eclosion])
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()
