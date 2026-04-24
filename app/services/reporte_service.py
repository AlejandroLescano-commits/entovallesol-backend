from sqlalchemy.orm import Session
from datetime import date
import io, openpyxl
from app.infrastructure.repositories.produccion_repository import ProduccionRepository

class ReporteService:
    def __init__(self, db: Session):
        self.repo = ProduccionRepository(db)

    # ── Producción ────────────────────────────────────────────────────────────
    def generar_excel_sitotroga(self, fecha_inicio: date, fecha_fin: date) -> bytes:
        registros = self.repo.list_sitotroga(fecha_inicio, fecha_fin)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Produccion Sitotroga"
        ws.append(["ID", "Fecha", "ID Unidad", "Cantidad", "Activo", "Registrado por", "Creado en"])
        for r in registros:
            ws.append([r.id, str(r.fecha), r.id_unidad, r.cantidad,
                       r.activo, r.registrado_por, str(r.creado_en)])
        return _to_bytes(wb)

    def generar_excel_trichogramma(self, fecha_inicio: date, fecha_fin: date) -> bytes:
        registros = self.repo.list_trichogramma(fecha_inicio, fecha_fin)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Produccion Trichogramma"
        ws.append(["ID", "Fecha", "ID Unidad", "Cantidad", "Activo", "Registrado por", "Creado en"])
        for r in registros:
            ws.append([r.id, str(r.fecha), r.id_unidad, r.cantidad,
                       r.activo, r.registrado_por, str(r.creado_en)])
        return _to_bytes(wb)

    def generar_excel_galleria(self, fecha_inicio: date, fecha_fin: date) -> bytes:
        registros = self.repo.list_galleria(fecha_inicio, fecha_fin)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Produccion Galleria"
        ws.append(["ID", "Fecha", "ID Unidad", "Cantidad", "Activo", "Registrado por", "Creado en"])
        for r in registros:
            ws.append([r.id, str(r.fecha), r.id_unidad, r.cantidad,
                       r.activo, r.registrado_por, str(r.creado_en)])
        return _to_bytes(wb)

    def generar_excel_paratheresia(self, fecha_inicio: date, fecha_fin: date) -> bytes:
        registros = self.repo.list_paratheresia(fecha_inicio, fecha_fin)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Produccion Paratheresia"
        ws.append(["ID", "Fecha", "ID Unidad", "Cantidad", "Activo", "Registrado por", "Creado en"])
        for r in registros:
            ws.append([r.id, str(r.fecha), r.id_unidad, r.cantidad,
                       r.activo, r.registrado_por, str(r.creado_en)])
        return _to_bytes(wb)

    # ── Notas de Salida ───────────────────────────────────────────────────────
    def generar_excel_notas_sitodroga(self, fecha_inicio: date, fecha_fin: date) -> bytes:
        registros = self.repo.list_notas_sitodroga(fecha_inicio, fecha_fin)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Notas Sitodroga"
        ws.append(["ID", "Fecha", "Tipo Salida", "Descripción", "ID Unidad",
                   "Factor", "Cantidad", "Activo", "Registrado por", "Creado en"])
        for r in registros:
            ws.append([r.id, str(r.fecha), r.tiposalida, r.descripcion,
                       r.id_unidad, r.factor, r.cantidad,
                       r.activo, r.registrado_por, str(r.creado_en)])
        return _to_bytes(wb)

    def generar_excel_notas_avispitas(self, fecha_inicio: date, fecha_fin: date) -> bytes:
        registros = self.repo.list_notas_avispitas(fecha_inicio, fecha_fin)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Notas Avispitas"
        ws.append(["ID", "Fecha", "Tipo Salida", "Lugar Liberación", "Descripción",
                   "ID Unidad", "Cantidad", "Activo", "Registrado por", "Creado en"])
        for r in registros:
            ws.append([r.id, str(r.fecha), r.tiposalida, r.id_lugarliberacion,
                       r.descripcion, r.id_unidad, r.cantidad,
                       r.activo, r.registrado_por, str(r.creado_en)])
        return _to_bytes(wb)

    def generar_excel_notas_moscas(self, fecha_inicio: date, fecha_fin: date) -> bytes:
        registros = self.repo.list_notas_moscas(fecha_inicio, fecha_fin)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Notas Moscas"
        ws.append(["ID", "Fecha", "Tipo Salida", "Lugar Liberación", "Descripción",
                   "ID Unidad", "Cantidad", "Activo", "Registrado por", "Creado en"])
        for r in registros:
            ws.append([r.id, str(r.fecha), r.tiposalida, r.id_lugarliberacion,
                       r.descripcion, r.id_unidad, r.cantidad,
                       r.activo, r.registrado_por, str(r.creado_en)])
        return _to_bytes(wb)

    def generar_excel_notas_galleria(self, fecha_inicio: date, fecha_fin: date) -> bytes:
        registros = self.repo.list_notas_galleria(fecha_inicio, fecha_fin)
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Notas Galleria"
        ws.append(["ID", "Fecha", "Tipo Salida", "Descripción", "ID Unidad",
                   "Cantidad", "Ratio", "Activo", "Registrado por", "Creado en"])
        for r in registros:
            ws.append([r.id, str(r.fecha), r.tiposalida, r.descripcion,
                       r.id_unidad, r.cantidad, r.ratio,
                       r.activo, r.registrado_por, str(r.creado_en)])
        return _to_bytes(wb)


def _to_bytes(wb: openpyxl.Workbook) -> bytes:
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()