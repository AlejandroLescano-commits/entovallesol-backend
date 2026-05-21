"""
test_usuario.py – Pruebas Unitarias del módulo de Usuarios
EntoValleSOL Backend

Casos cubiertos:
  CA01 – UsuarioRepository (get_by_id, get_by_email, get_all, create, update, delete)
  CA02 – UsuarioService.crear  (email duplicado, hash de password, retorno)
  CA03 – UsuarioService.obtener (existente, no existente)
  CA04 – UsuarioService.actualizar
  CA05 – UsuarioService.eliminar
  CA06 – Schemas Pydantic (UsuarioCreate, UsuarioUpdate, UsuarioResponse)

Ejecutar:
  pytest tests/unit/test_usuario.py -v
"""
import pytest
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

from fastapi import HTTPException
from pydantic import ValidationError


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _make_usuario(id=1, nombre="Ana Torres", email="ana@entolab.com",
                  rol="operario", activo=True):
    u = MagicMock()
    u.id            = id
    u.nombre        = nombre
    u.email         = email
    u.rol           = rol
    u.activo        = activo
    u.password_hash = "$2b$12$fakehash"
    u.creado_en     = datetime(2025, 1, 1, tzinfo=timezone.utc)
    return u


# ═══════════════════════════════════════════════════════════════════════════════
# CA01 – UsuarioRepository
# ═══════════════════════════════════════════════════════════════════════════════

class TestUsuarioRepository:
    """CA01: Operaciones de acceso a datos de usuarios."""

    def _repo(self, mock_db):
        from app.infrastructure.repositories.usuario_repository import UsuarioRepository
        return UsuarioRepository(mock_db)

    def _setup_query_first(self, mock_db, return_value):
        mock_db.query.return_value.filter.return_value.first.return_value = return_value

    def test_get_by_id_existente_retorna_usuario(self, mock_db, usuario_activo):
        """CA01-1: get_by_id con id existente retorna el objeto."""
        self._setup_query_first(mock_db, usuario_activo)
        repo = self._repo(mock_db)
        result = repo.get_by_id(1)
        assert result is usuario_activo

    def test_get_by_id_inexistente_retorna_none(self, mock_db):
        """CA01-2: get_by_id con id inexistente retorna None."""
        self._setup_query_first(mock_db, None)
        repo = self._repo(mock_db)
        assert repo.get_by_id(9999) is None

    def test_get_by_email_existente(self, mock_db, usuario_activo):
        """CA01-3: get_by_email con email válido retorna el usuario."""
        self._setup_query_first(mock_db, usuario_activo)
        repo = self._repo(mock_db)
        result = repo.get_by_email("ana@entolab.com")
        assert result.email == "ana@entolab.com"

    def test_get_by_email_inexistente_retorna_none(self, mock_db):
        """CA01-4: Email inexistente → None."""
        self._setup_query_first(mock_db, None)
        repo = self._repo(mock_db)
        assert repo.get_by_email("noexi@ste.com") is None

    def test_get_all_retorna_lista(self, mock_db):
        """CA01-5: get_all retorna lista de usuarios."""
        usuarios = [_make_usuario(id=1), _make_usuario(id=2)]
        mock_db.query.return_value.all.return_value = usuarios
        repo = self._repo(mock_db)
        result = repo.get_all()
        assert len(result) == 2

    def test_create_llama_add_commit_refresh(self, mock_db):
        """CA01-6: create() debe llamar add, commit y refresh exactamente una vez."""
        mock_obj = _make_usuario()

        with patch("app.infrastructure.repositories.usuario_repository.Usuario", return_value=mock_obj):
            repo = self._repo(mock_db)
            repo.create({"nombre": "Ana", "email": "ana@e.com", "password_hash": "h", "rol": "operario"})

        mock_db.add.assert_called_once_with(mock_obj)
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once_with(mock_obj)

    def test_update_aplica_campos_y_hace_commit(self, mock_db, usuario_activo):
        """CA01-7: update() debe setattr los campos nuevos y hacer commit."""
        self._setup_query_first(mock_db, usuario_activo)
        repo = self._repo(mock_db)
        repo.update(1, {"nombre": "Nuevo Nombre", "rol": "admin"})
        assert usuario_activo.nombre == "Nuevo Nombre"
        assert usuario_activo.rol    == "admin"
        mock_db.commit.assert_called_once()

    def test_delete_elimina_y_hace_commit(self, mock_db, usuario_activo):
        """CA01-8: delete() debe llamar db.delete y commit."""
        self._setup_query_first(mock_db, usuario_activo)
        repo = self._repo(mock_db)
        result = repo.delete(1)
        mock_db.delete.assert_called_once_with(usuario_activo)
        mock_db.commit.assert_called_once()
        assert result is usuario_activo

    def test_delete_id_inexistente_retorna_none(self, mock_db):
        """CA01-9: delete() con id inexistente retorna None sin lanzar error."""
        self._setup_query_first(mock_db, None)
        repo = self._repo(mock_db)
        result = repo.delete(9999)
        assert result is None
        mock_db.delete.assert_not_called()


# ═══════════════════════════════════════════════════════════════════════════════
# CA02 – UsuarioService.crear
# ═══════════════════════════════════════════════════════════════════════════════

class TestUsuarioServiceCrear:
    """CA02: Creación de nuevos usuarios."""

    def _svc(self, mock_db, usuario_existente=None):
        from app.services.usuario_service import UsuarioService
        svc = UsuarioService.__new__(UsuarioService)
        svc.repo = MagicMock()
        svc.repo.get_by_email.return_value = usuario_existente
        svc.repo.create.return_value = _make_usuario()
        return svc

    def test_crear_email_duplicado_lanza_400(self, mock_db, usuario_activo):
        """CA02-1: Email ya registrado debe lanzar HTTPException 400."""
        svc = self._svc(mock_db, usuario_existente=usuario_activo)
        from app.domain.schemas.usuario_schema import UsuarioCreate
        with pytest.raises(HTTPException) as exc:
            svc.crear(UsuarioCreate(nombre="X", email="ana@entolab.com", password="pw"))
        assert exc.value.status_code == 400

    def test_crear_hashea_password(self, mock_db):
        """CA02-2: password_hash debe ser distinto del password original."""
        svc = self._svc(mock_db)
        captured = {}
        def fake_create(data):
            captured["data"] = data
            return _make_usuario()
        svc.repo.create.side_effect = fake_create

        from app.domain.schemas.usuario_schema import UsuarioCreate
        with patch("app.services.usuario_service.hash_password", return_value="$2b$12$hash"):
            svc.crear(UsuarioCreate(nombre="Carlos", email="c@e.com", password="plain"))

        assert captured["data"]["password_hash"] == "$2b$12$hash"
        assert "password" not in captured["data"]

    def test_crear_no_incluye_campo_password(self, mock_db):
        """CA02-3: El dict enviado al repo no debe tener la key 'password'."""
        svc = self._svc(mock_db)
        captured = {}
        svc.repo.create.side_effect = lambda d: (captured.update(d), _make_usuario())[1]

        from app.domain.schemas.usuario_schema import UsuarioCreate
        with patch("app.services.usuario_service.hash_password", return_value="h"):
            svc.crear(UsuarioCreate(nombre="X", email="x@e.com", password="pw"))

        assert "password" not in captured

    def test_crear_rol_por_defecto_operario(self, mock_db):
        """CA02-4: rol por defecto debe ser 'operario'."""
        svc = self._svc(mock_db)
        captured = {}
        svc.repo.create.side_effect = lambda d: (captured.update(d), _make_usuario())[1]

        from app.domain.schemas.usuario_schema import UsuarioCreate
        with patch("app.services.usuario_service.hash_password", return_value="h"):
            svc.crear(UsuarioCreate(nombre="X", email="x2@e.com", password="pw"))

        assert captured.get("rol") == "operario"

    def test_crear_retorna_usuario(self, mock_db):
        """CA02-5: crear() debe retornar el objeto usuario creado."""
        svc = self._svc(mock_db)
        from app.domain.schemas.usuario_schema import UsuarioCreate
        with patch("app.services.usuario_service.hash_password", return_value="h"):
            result = svc.crear(UsuarioCreate(nombre="X", email="x3@e.com", password="pw"))
        assert result is not None
        assert result.id == 1


# ═══════════════════════════════════════════════════════════════════════════════
# CA03 – UsuarioService.obtener
# ═══════════════════════════════════════════════════════════════════════════════

class TestUsuarioServiceObtener:
    """CA03: Obtener usuario por id."""

    def _svc(self, usuario=None):
        from app.services.usuario_service import UsuarioService
        svc = UsuarioService.__new__(UsuarioService)
        svc.repo = MagicMock()
        svc.repo.get_by_id.return_value = usuario
        return svc

    def test_obtener_existente_retorna_usuario(self, usuario_activo):
        """CA03-1: id válido retorna el usuario."""
        svc = self._svc(usuario_activo)
        result = svc.obtener(1)
        assert result is usuario_activo

    def test_obtener_inexistente_lanza_404(self):
        """CA03-2: id inexistente lanza HTTPException 404."""
        svc = self._svc(None)
        with pytest.raises(HTTPException) as exc:
            svc.obtener(9999)
        assert exc.value.status_code == 404

    def test_obtener_llama_repo_con_id_correcto(self, usuario_activo):
        """CA03-3: Se llama get_by_id con el id exacto recibido."""
        svc = self._svc(usuario_activo)
        svc.obtener(42)
        svc.repo.get_by_id.assert_called_once_with(42)


# ═══════════════════════════════════════════════════════════════════════════════
# CA04 – UsuarioService.actualizar
# ═══════════════════════════════════════════════════════════════════════════════

class TestUsuarioServiceActualizar:
    """CA04: Actualización parcial de usuario."""

    def _svc(self, usuario=None):
        from app.services.usuario_service import UsuarioService
        svc = UsuarioService.__new__(UsuarioService)
        svc.repo = MagicMock()
        svc.repo.update.return_value = usuario or _make_usuario()
        return svc

    def test_actualizar_solo_campos_no_none(self):
        """CA04-1: Solo los campos con valor deben enviarse al repo."""
        svc = self._svc()
        captured = {}
        svc.repo.update.side_effect = lambda uid, d: (captured.update(d), _make_usuario())[1]

        from app.domain.schemas.usuario_schema import UsuarioUpdate
        svc.actualizar(1, UsuarioUpdate(nombre="Nuevo"))

        assert "nombre" in captured
        assert "email"  not in captured   # None excluido
        assert "rol"    not in captured

    def test_actualizar_retorna_usuario_modificado(self, usuario_activo):
        """CA04-2: actualizar() retorna el objeto actualizado."""
        svc = self._svc(usuario_activo)
        from app.domain.schemas.usuario_schema import UsuarioUpdate
        result = svc.actualizar(1, UsuarioUpdate(rol="admin"))
        assert result is usuario_activo

    def test_actualizar_activo_false_desactiva_usuario(self):
        """CA04-3: activo=False debe incluirse en el dict enviado al repo."""
        svc = self._svc()
        captured = {}
        svc.repo.update.side_effect = lambda uid, d: (captured.update(d), _make_usuario())[1]

        from app.domain.schemas.usuario_schema import UsuarioUpdate
        svc.actualizar(1, UsuarioUpdate(activo=False))

        assert captured.get("activo") is False


# ═══════════════════════════════════════════════════════════════════════════════
# CA05 – UsuarioService.eliminar
# ═══════════════════════════════════════════════════════════════════════════════

class TestUsuarioServiceEliminar:
    """CA05: Eliminación de usuario."""

    def _svc(self, retorno=None):
        from app.services.usuario_service import UsuarioService
        svc = UsuarioService.__new__(UsuarioService)
        svc.repo = MagicMock()
        svc.repo.delete.return_value = retorno
        return svc

    def test_eliminar_llama_repo_delete(self, usuario_activo):
        """CA05-1: eliminar() debe llamar repo.delete con el id correcto."""
        svc = self._svc(usuario_activo)
        svc.eliminar(1)
        svc.repo.delete.assert_called_once_with(1)

    def test_eliminar_retorna_objeto_eliminado(self, usuario_activo):
        """CA05-2: eliminar() retorna el objeto que fue eliminado."""
        svc = self._svc(usuario_activo)
        result = svc.eliminar(1)
        assert result is usuario_activo

    def test_eliminar_id_inexistente_retorna_none(self):
        """CA05-3: Si el usuario no existe, retorna None sin error."""
        svc = self._svc(None)
        result = svc.eliminar(9999)
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════════
# CA06 – Schemas Pydantic
# ═══════════════════════════════════════════════════════════════════════════════

class TestUsuarioSchemas:
    """CA06: Validación de schemas Pydantic."""

    def test_usuario_create_valido(self):
        """CA06-1: Datos válidos crean el schema sin error."""
        from app.domain.schemas.usuario_schema import UsuarioCreate
        obj = UsuarioCreate(nombre="X", email="x@e.com", password="pw123", rol="admin")
        assert obj.rol == "admin"

    def test_usuario_create_rol_default_operario(self):
        """CA06-2: Sin especificar rol, el default debe ser 'operario'."""
        from app.domain.schemas.usuario_schema import UsuarioCreate
        obj = UsuarioCreate(nombre="X", email="x@e.com", password="pw")
        assert obj.rol == "operario"

    def test_usuario_create_email_invalido_lanza_error(self):
        """CA06-3: Email malformado debe lanzar ValidationError."""
        from app.domain.schemas.usuario_schema import UsuarioCreate
        with pytest.raises(ValidationError):
            UsuarioCreate(nombre="X", email="no-es-email", password="pw")

    def test_usuario_update_todos_opcionales(self):
        """CA06-4: UsuarioUpdate sin campos no lanza error (todos opcionales)."""
        from app.domain.schemas.usuario_schema import UsuarioUpdate
        obj = UsuarioUpdate()
        assert obj.nombre is None
        assert obj.email  is None

    def test_usuario_update_exclude_none(self):
        """CA06-5: model_dump(exclude_none=True) excluye campos None."""
        from app.domain.schemas.usuario_schema import UsuarioUpdate
        obj = UsuarioUpdate(nombre="Solo nombre")
        d = obj.model_dump(exclude_none=True)
        assert "nombre" in d
        assert "email"  not in d
        assert "rol"    not in d

    def test_usuario_response_from_attributes(self, usuario_activo):
        """CA06-6: UsuarioResponse acepta ORM objects gracias a from_attributes."""
        from app.domain.schemas.usuario_schema import UsuarioResponse
        usuario_activo.creado_en = datetime(2025, 1, 1, tzinfo=timezone.utc)
        r = UsuarioResponse.model_validate(usuario_activo)
        assert r.id    == usuario_activo.id
        assert r.email == usuario_activo.email
