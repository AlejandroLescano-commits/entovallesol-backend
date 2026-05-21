"""
test_produccion.py – Pruebas Unitarias del módulo de Producción Biológica
EntoValleSOL Backend

Casos cubiertos:
  CA01 – ProduccionRepository.create_sitotroga
  CA02 – ProduccionRepository.anular_sitotroga
  CA03 – ProduccionRepository.list_sitotroga (filtros de fecha)
  CA04 – find_trichogramma_por_nota / find_paratheresia_por_nota
  CA05 – Schemas Pydantic (validators de cantidad)
  CA06 – Notas de Salida (avispitas / moscas / galleria)

Ejecutar:
  pytest tests/unit/test_produccion.py -v
"""
import pytest
from datetime import date, datetime
from unittest.mock import MagicMock, patch, call

# ─── Imports del proyecto ─────────────────────────────────────────────────────
# Ajusta los paths según tu estructura real
from app.infrastructure.repositories.produccion_repository import ProduccionRepository
from app.domain.entities.produccion_sitotroga import ProduccionSitotroga
from app.domain.entities.produccion_trichogramma import ProduccionTrichogramma
from app.domain.entities.produccion_galleria import ProduccionGalleria
from app.domain.entities.produccion_paratheresia import ProduccionParatheresia
from app.domain.entities.notas_salida import (
    NotaSalidaSitodroga,
    NotaSalidaAvispitas,
    NotaSalidaMoscas,
    NotaSalidaGalleriamelonella,
)
from app.domain.schemas.produccion_schema import (
    ProduccionSitotrogaCreate,
    ProduccionTrichogrammaCreate,
    ProduccionGalleriaCreate,
    ProduccionParathesiaCreate,
    NotaSalidaSitodrogaCreate,
    NotaSalidaAvispitasCreate,
    NotaSalidaMoscasCreate,
    NotaSalidaGalleriaCreate,
)
from pydantic import ValidationError


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def make_mock_obj(cls, **kwargs):
    """Crea un objeto mock que simula un registro ORM con los atributos dados."""
    obj = MagicMock(spec=cls)
    defaults = {"id": 1, "activo": True, "anulado_por": None, "anulado_en": None}
    for k, v in {**defaults, **kwargs}.items():
        setattr(obj, k, v)
    return obj


def make_mock_db(query_return=None):
    """Crea un mock de sesión SQLAlchemy con commit/refresh/add espiados."""
    db = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.add = MagicMock()

    if query_return is not None:
        # Cadena: db.query(...).filter(...).first() o .all()
        mock_query = MagicMock()
        mock_filter = MagicMock()
        mock_filter.first.return_value = query_return
        mock_filter.all.return_value = query_return if isinstance(query_return, list) else [query_return]
        mock_filter.order_by.return_value = mock_filter
        mock_query.filter.return_value = mock_filter
        db.query.return_value = mock_query

    return db


# ═══════════════════════════════════════════════════════════════════════════════
# CA01 – create_sitotroga
# ═══════════════════════════════════════════════════════════════════════════════

class TestCreateSitotroga:
    """CA01: Crear registro de producción Sitotroga cereallela."""

    def test_retorna_objeto_con_id_asignado(self, mock_db, sample_sitotroga_data):
        """CA01-1: Objeto retornado debe tener id asignado tras commit."""
        mock_obj = make_mock_obj(ProduccionSitotroga, id=42)

        def fake_refresh(obj):
            obj.id = 42

        mock_db.refresh.side_effect = fake_refresh

        with patch("app.infrastructure.repositories.produccion_repository.ProduccionSitotroga") as MockCls:
            MockCls.return_value = mock_obj
            repo = ProduccionRepository(mock_db)
            result = repo.create_sitotroga(sample_sitotroga_data)

        assert result.id == 42

    def test_id_es_entero_positivo(self, mock_db, sample_sitotroga_data):
        """CA01-2: id debe ser entero positivo después del refresh."""
        mock_obj = make_mock_obj(ProduccionSitotroga, id=7)
        mock_db.refresh.side_effect = lambda obj: setattr(obj, "id", 7)

        with patch("app.infrastructure.repositories.produccion_repository.ProduccionSitotroga", return_value=mock_obj):
            repo = ProduccionRepository(mock_db)
            result = repo.create_sitotroga(sample_sitotroga_data)

        assert isinstance(result.id, int)
        assert result.id > 0

    def test_activo_true_por_defecto(self, mock_db, sample_sitotroga_data):
        """CA01-3: activo=True debe ser el valor por defecto."""
        mock_obj = make_mock_obj(ProduccionSitotroga, activo=True)

        with patch("app.infrastructure.repositories.produccion_repository.ProduccionSitotroga", return_value=mock_obj):
            repo = ProduccionRepository(mock_db)
            result = repo.create_sitotroga(sample_sitotroga_data)

        assert result.activo is True

    def test_cantidad_guardada_correctamente(self, mock_db):
        """CA01-4: El campo cantidad debe persistirse con el valor exacto."""
        data = {"fecha": date(2025, 5, 20), "id_unidad": 1, "cantidad": 1234.5, "registrado_por": 1}
        mock_obj = make_mock_obj(ProduccionSitotroga, cantidad=1234.5)

        with patch("app.infrastructure.repositories.produccion_repository.ProduccionSitotroga", return_value=mock_obj):
            repo = ProduccionRepository(mock_db)
            result = repo.create_sitotroga(data)

        assert result.cantidad == pytest.approx(1234.5)

    def test_id_unidad_none_no_lanza_error(self, mock_db):
        """CA01-5: id_unidad es opcional; None no debe generar error."""
        data = {"fecha": date(2025, 5, 20), "id_unidad": None, "cantidad": 100.0, "registrado_por": 1}
        mock_obj = make_mock_obj(ProduccionSitotroga, id_unidad=None)

        with patch("app.infrastructure.repositories.produccion_repository.ProduccionSitotroga", return_value=mock_obj):
            repo = ProduccionRepository(mock_db)
            result = repo.create_sitotroga(data)  # no debe lanzar

        assert result.id_unidad is None

    def test_commit_y_refresh_llamados_una_vez(self, mock_db, sample_sitotroga_data):
        """CA01-6: commit() y refresh() deben invocarse exactamente 1 vez."""
        mock_obj = make_mock_obj(ProduccionSitotroga)

        with patch("app.infrastructure.repositories.produccion_repository.ProduccionSitotroga", return_value=mock_obj):
            repo = ProduccionRepository(mock_db)
            repo.create_sitotroga(sample_sitotroga_data)

        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_obj)


# ═══════════════════════════════════════════════════════════════════════════════
# CA02 – anular_sitotroga
# ═══════════════════════════════════════════════════════════════════════════════

class TestAnularSitotroga:
    """CA02: Soft-delete de registro de Sitotroga."""

    def _setup_query(self, db, obj_to_return):
        """Configura db.query(...).filter(...).first() para retornar obj_to_return."""
        mock_filter = MagicMock()
        mock_filter.first.return_value = obj_to_return
        db.query.return_value.filter.return_value = mock_filter

    def test_anular_registro_activo(self, mock_db):
        """CA02-1: Anular registro activo debe marcar activo=False."""
        obj = make_mock_obj(ProduccionSitotroga, id=1, activo=True)
        self._setup_query(mock_db, obj)

        repo = ProduccionRepository(mock_db)
        result = repo.anular_sitotroga(1, 99)

        assert result.activo is False
        assert result.anulado_por == 99
        assert result.anulado_en is not None

    def test_id_inexistente_lanza_value_error(self, mock_db):
        """CA02-2: id inexistente debe lanzar ValueError."""
        self._setup_query(mock_db, None)

        repo = ProduccionRepository(mock_db)
        with pytest.raises(ValueError, match="Registro no encontrado o ya anulado"):
            repo.anular_sitotroga(9999, 1)

    def test_registro_ya_anulado_lanza_value_error(self, mock_db):
        """CA02-3: Registro con activo=False debe lanzar ValueError."""
        # La query filtra activo==True, así que retorna None para anulados
        self._setup_query(mock_db, None)

        repo = ProduccionRepository(mock_db)
        with pytest.raises(ValueError, match="Registro no encontrado o ya anulado"):
            repo.anular_sitotroga(1, 1)

    def test_anulado_en_es_datetime(self, mock_db):
        """CA02-4: anulado_en debe ser una instancia de datetime."""
        obj = make_mock_obj(ProduccionSitotroga, id=1, activo=True)
        self._setup_query(mock_db, obj)

        repo = ProduccionRepository(mock_db)
        repo.anular_sitotroga(1, 5)

        assert isinstance(obj.anulado_en, datetime)

    def test_anulado_por_recibe_user_id_correcto(self, mock_db):
        """CA02-5: anulado_por debe coincidir con el user_id recibido."""
        obj = make_mock_obj(ProduccionSitotroga, id=1, activo=True)
        self._setup_query(mock_db, obj)

        repo = ProduccionRepository(mock_db)
        repo.anular_sitotroga(1, 42)

        assert obj.anulado_por == 42

    def test_commit_no_es_llamado(self, mock_db):
        """CA02-6: commit() NO debe llamarse aquí (lo gestiona el service)."""
        obj = make_mock_obj(ProduccionSitotroga, id=1, activo=True)
        self._setup_query(mock_db, obj)

        repo = ProduccionRepository(mock_db)
        repo.anular_sitotroga(1, 1)

        mock_db.commit.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# CA03 – list_sitotroga (filtros de fecha)
# ═══════════════════════════════════════════════════════════════════════════════

class TestListSitotroga:
    """CA03: Listado con filtros opcionales de fecha."""

    def _make_records(self, fechas):
        return [make_mock_obj(ProduccionSitotroga, fecha=f, activo=True) for f in fechas]

    def _setup_list_query(self, db, records):
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = records
        db.query.return_value = mock_q

    def test_sin_filtros_retorna_todos_activos(self, mock_db):
        """CA03-1: Sin filtros debe retornar los 3 registros activos."""
        records = self._make_records([date(2025, 1, 10), date(2025, 3, 15), date(2025, 5, 20)])
        self._setup_list_query(mock_db, records)

        repo = ProduccionRepository(mock_db)
        result = repo.list_sitotroga(None, None)

        assert len(result) == 3

    def test_filtrar_por_fecha_inicio(self, mock_db):
        """CA03-2: fecha_inicio filtra registros anteriores a la fecha."""
        records = self._make_records([date(2025, 3, 15), date(2025, 5, 20)])
        self._setup_list_query(mock_db, records)

        repo = ProduccionRepository(mock_db)
        result = repo.list_sitotroga(date(2025, 3, 1), None)

        assert len(result) == 2
        assert all(r.fecha >= date(2025, 3, 1) for r in result)

    def test_filtrar_por_fecha_fin(self, mock_db):
        """CA03-3: fecha_fin filtra registros posteriores a la fecha."""
        records = self._make_records([date(2025, 1, 10)])
        self._setup_list_query(mock_db, records)

        repo = ProduccionRepository(mock_db)
        result = repo.list_sitotroga(None, date(2025, 2, 28))

        assert len(result) == 1

    def test_filtrar_por_rango_completo(self, mock_db):
        """CA03-4: Rango completo devuelve solo registros dentro del rango."""
        records = self._make_records([date(2025, 3, 15)])
        self._setup_list_query(mock_db, records)

        repo = ProduccionRepository(mock_db)
        result = repo.list_sitotroga(date(2025, 3, 1), date(2025, 4, 30))

        assert len(result) == 1
        assert result[0].fecha == date(2025, 3, 15)

    def test_anulados_excluidos(self, mock_db):
        """CA03-5: Registros con activo=False no deben aparecer en el resultado."""
        records = self._make_records([date(2025, 5, 20)])  # Solo 1 activo
        self._setup_list_query(mock_db, records)

        repo = ProduccionRepository(mock_db)
        result = repo.list_sitotroga(None, None)

        assert len(result) == 1
        assert all(r.activo is True for r in result)

    def test_orden_descendente_por_fecha(self, mock_db):
        """CA03-6: El primer elemento debe ser el más reciente."""
        fechas = [date(2025, 5, 20), date(2025, 3, 15), date(2025, 1, 10)]
        records = self._make_records(fechas)
        self._setup_list_query(mock_db, records)

        repo = ProduccionRepository(mock_db)
        result = repo.list_sitotroga(None, None)

        assert result[0].fecha == date(2025, 5, 20)


# ═══════════════════════════════════════════════════════════════════════════════
# CA04 – find_trichogramma_por_nota / find_paratheresia_por_nota
# ═══════════════════════════════════════════════════════════════════════════════

class TestFindPorNota:
    """CA04: Búsqueda de registros derivados vinculados por nota_origen_id."""

    def _setup_find(self, db, return_value):
        mock_filter = MagicMock()
        mock_filter.first.return_value = return_value
        db.query.return_value.filter.return_value = mock_filter

    def test_encontrar_trichogramma_existente(self, mock_db):
        """CA04-1: Debe retornar el objeto con nota_origen_id correcto."""
        obj = make_mock_obj(ProduccionTrichogramma, nota_origen_id=5)
        self._setup_find(mock_db, obj)

        repo = ProduccionRepository(mock_db)
        result = repo.find_trichogramma_por_nota(5)

        assert result is not None
        assert result.nota_origen_id == 5

    def test_nota_id_inexistente_retorna_none(self, mock_db):
        """CA04-2: nota_id que no existe debe retornar None."""
        self._setup_find(mock_db, None)

        repo = ProduccionRepository(mock_db)
        result = repo.find_trichogramma_por_nota(9999)

        assert result is None

    def test_anulados_no_retornados(self, mock_db):
        """CA04-3: Registros con activo=False no deben retornarse."""
        # La query filtra activo==True; simulamos None para anulados
        self._setup_find(mock_db, None)

        repo = ProduccionRepository(mock_db)
        result = repo.find_trichogramma_por_nota(5)

        assert result is None

    def test_retorna_solo_el_primero(self, mock_db):
        """CA04-4: Debe usar .first() — retorna un único objeto aunque haya duplicados."""
        obj = make_mock_obj(ProduccionTrichogramma, nota_origen_id=5)
        self._setup_find(mock_db, obj)

        repo = ProduccionRepository(mock_db)
        result = repo.find_trichogramma_por_nota(5)

        # Verificamos que se usó .first() (la query solo retorna 1 objeto)
        assert result == obj

    def test_find_paratheresia_funciona_igual(self, mock_db):
        """CA04-5: find_paratheresia_por_nota debe tener el mismo comportamiento."""
        obj = make_mock_obj(ProduccionParatheresia, nota_origen_id=3)
        self._setup_find(mock_db, obj)

        repo = ProduccionRepository(mock_db)
        result = repo.find_paratheresia_por_nota(3)

        assert result is not None
        assert result.nota_origen_id == 3

    def test_sin_nota_origen_no_interfiere(self, mock_db):
        """CA04-6: Registros sin nota_origen_id no deben coincidir."""
        self._setup_find(mock_db, None)

        repo = ProduccionRepository(mock_db)
        result = repo.find_trichogramma_por_nota(1)

        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# CA05 – Schemas Pydantic (validators de cantidad)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSchemaValidators:
    """CA05: Validadores Pydantic rechazan cantidades inválidas."""

    def test_nota_sitodroga_cantidad_cero_lanza_error(self):
        """CA05-1: cantidad=0 debe lanzar ValidationError."""
        with pytest.raises(ValidationError, match="La cantidad debe ser mayor a 0"):
            NotaSalidaSitodrogaCreate(
                tiposalida="T.exiguum",
                fecha=date(2025, 5, 20),
                cantidad=0,
            )

    def test_nota_sitodroga_cantidad_negativa_lanza_error(self):
        """CA05-2: cantidad negativa debe lanzar ValidationError."""
        with pytest.raises(ValidationError):
            NotaSalidaSitodrogaCreate(
                tiposalida="Ventas",
                fecha=date(2025, 5, 20),
                cantidad=-50.0,
            )

    def test_nota_sitodroga_datos_validos_aceptados(self):
        """CA05-3: Datos válidos deben crear el objeto con factor=1 por defecto."""
        obj = NotaSalidaSitodrogaCreate(
            tiposalida="Ventas",
            fecha=date(2025, 5, 20),
            cantidad=100.0,
        )
        assert obj.cantidad == pytest.approx(100.0)
        assert obj.factor == pytest.approx(1.0)

    def test_nota_avispitas_cantidad_cero_lanza_error(self):
        """CA05-4: NotaSalidaAvispitasCreate con cantidad=0 debe lanzar error."""
        with pytest.raises(ValidationError):
            NotaSalidaAvispitasCreate(
                tiposalida="Liberacion",
                fecha=date(2025, 5, 20),
                cantidad=0,
            )

    def test_produccion_sitotroga_id_unidad_none_por_defecto(self):
        """CA05-5: id_unidad debe ser None por defecto en ProduccionSitotrogaCreate."""
        obj = ProduccionSitotrogaCreate(
            fecha=date(2025, 5, 20),
            cantidad=200.0,
        )
        assert obj.id_unidad is None

    def test_nota_galleria_ratio_none_sin_error(self):
        """CA05-6: ratio=None debe aceptarse cuando tiposalida != Paratheresia."""
        obj = NotaSalidaGalleriaCreate(
            tiposalida="Instalacion",
            fecha=date(2025, 5, 20),
            cantidad=50.0,
        )
        assert obj.ratio is None


# ═══════════════════════════════════════════════════════════════════════════════
# CA06 – Notas de Salida (avispitas / moscas / galleria)
# ═══════════════════════════════════════════════════════════════════════════════

class TestNotasSalida:
    """CA06: CRUD de notas de salida para los distintos organismos."""

    def _setup_query(self, db, obj_to_return):
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.order_by.return_value = mock_q
        mock_q.all.return_value = obj_to_return if isinstance(obj_to_return, list) else [obj_to_return]
        mock_q.first.return_value = obj_to_return if not isinstance(obj_to_return, list) else obj_to_return[0] if obj_to_return else None
        db.query.return_value = mock_q

    def test_create_nota_avispitas_guarda_tiposalida(self, mock_db):
        """CA06-1: tiposalida debe persistirse correctamente."""
        mock_obj = make_mock_obj(NotaSalidaAvispitas, tiposalida="Liberacion")

        with patch("app.infrastructure.repositories.produccion_repository.NotaSalidaAvispitas", return_value=mock_obj):
            repo = ProduccionRepository(mock_db)
            result = repo.create_nota_avispitas(
                {"tiposalida": "Liberacion", "fecha": date(2025, 5, 20), "cantidad": 1000.0, "registrado_por": 1}
            )

        assert result.tiposalida == "Liberacion"
        assert result.id is not None

    def test_list_notas_avispitas_solo_activas(self, mock_db):
        """CA06-2: Solo deben retornarse notas con activo=True."""
        activas = [
            make_mock_obj(NotaSalidaAvispitas, id=1, activo=True),
            make_mock_obj(NotaSalidaAvispitas, id=2, activo=True),
        ]
        self._setup_query(mock_db, activas)

        repo = ProduccionRepository(mock_db)
        result = repo.list_notas_avispitas(None, None)

        assert len(result) == 2
        assert all(r.activo is True for r in result)

    def test_anular_nota_avispitas_ya_anulada_lanza_error(self, mock_db):
        """CA06-3: Nota ya anulada debe lanzar ValueError."""
        # query filtra activo==True → retorna None para una nota anulada
        mock_q = MagicMock()
        mock_q.filter.return_value = mock_q
        mock_q.first.return_value = None
        mock_db.query.return_value = mock_q

        repo = ProduccionRepository(mock_db)
        with pytest.raises(ValueError, match="Nota no encontrada o ya anulada"):
            repo.anular_nota_avispitas(1, 99)

    def test_create_nota_moscas_guarda_lugarliberacion(self, mock_db):
        """CA06-4: id_lugarliberacion debe persistirse correctamente."""
        mock_obj = make_mock_obj(NotaSalidaMoscas, id_lugarliberacion=3)

        with patch("app.infrastructure.repositories.produccion_repository.NotaSalidaMoscas", return_value=mock_obj):
            repo = ProduccionRepository(mock_db)
            result = repo.create_nota_moscas(
                {"tiposalida": "Parasitacion", "fecha": date(2025, 5, 20), "cantidad": 500.0,
                 "id_lugarliberacion": 3, "registrado_por": 1}
            )

        assert result.id_lugarliberacion == 3

    def test_create_nota_galleria_guarda_ratio(self, mock_db):
        """CA06-5: ratio debe persistirse para notas tipo Paratheresia."""
        mock_obj = make_mock_obj(NotaSalidaGalleriamelonella, ratio=0.85)

        with patch("app.infrastructure.repositories.produccion_repository.NotaSalidaGalleriamelonella", return_value=mock_obj):
            repo = ProduccionRepository(mock_db)
            result = repo.create_nota_galleria(
                {"tiposalida": "Paratheresia", "fecha": date(2025, 5, 20),
                 "cantidad": 200.0, "ratio": 0.85, "registrado_por": 1}
            )

        assert result.ratio == pytest.approx(0.85)

    def test_list_notas_galleria_filtra_por_fecha_inicio(self, mock_db):
        """CA06-6: Solo deben retornarse notas posteriores a fecha_inicio."""
        mayo = make_mock_obj(NotaSalidaGalleriamelonella, fecha=date(2025, 5, 20), activo=True)
        self._setup_query(mock_db, [mayo])

        repo = ProduccionRepository(mock_db)
        result = repo.list_notas_galleria(date(2025, 4, 1), None)

        assert len(result) == 1
        assert result[0].fecha == date(2025, 5, 20)
