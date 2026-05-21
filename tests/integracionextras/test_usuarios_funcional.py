"""
test_usuarios_funcional.py – Pruebas Funcionales del módulo de Usuarios
EntoValleSOL Backend

Casos cubiertos:
  USR-01 – POST /usuarios crea usuario con campos correctos (solo admin)
  USR-02 – GET  /usuarios lista todos los usuarios (solo admin)
  USR-03 – GET  /usuarios/{id} retorna usuario específico
  USR-04 – PUT  /usuarios/{id} actualiza campos permitidos
  USR-05 – DELETE /usuarios/{id} elimina el usuario
  USR-06 – Email duplicado al crear → HTTP 400
  USR-07 – Usuario no encontrado → HTTP 404
  USR-08 – Operario/Supervisor no puede crear ni listar usuarios (403)
  USR-09 – Actualización parcial (PATCH-like con PUT) solo modifica campos enviados
  USR-10 – Desactivar usuario (activo=False) sin eliminarlo

Ejecutar:
  pytest tests/integracionextras/test_usuarios_funcional.py -v
"""
import pytest
import uuid


def _email_unico():
    """Genera un email único para no colisionar entre tests."""
    return f"user_{uuid.uuid4().hex[:8]}@entovallesol.com"


# ═══════════════════════════════════════════════════════════════════════════════
# USR-01 – Crear usuario (admin)
# ═══════════════════════════════════════════════════════════════════════════════
class TestUSR01CrearUsuario:
    """USR-01: POST /usuarios crea un nuevo usuario correctamente."""

    def test_crea_usuario_retorna_201(self, client, admin_headers):
        """USR-01: Creación válida → HTTP 201."""
        payload = {
            "nombre": "Nuevo Operario",
            "email": _email_unico(),
            "password": "Pass1234!",
            "rol": "operario",
        }
        resp = client.post("/api/v1/usuarios/", json=payload, headers=admin_headers)
        assert resp.status_code == 201

    def test_crea_usuario_retorna_campos_correctos(self, client, admin_headers):
        """USR-01: Respuesta incluye id, nombre, email, rol y activo."""
        email = _email_unico()
        payload = {
            "nombre": "Test Campos",
            "email": email,
            "password": "Pass1234!",
            "rol": "supervisor",
        }
        resp = client.post("/api/v1/usuarios/", json=payload, headers=admin_headers)
        data = resp.json()
        assert data["nombre"] == "Test Campos"
        assert data["email"] == email
        assert data["rol"] == "supervisor"
        assert data["activo"] is True
        assert isinstance(data["id"], int)
        assert data["id"] > 0

    def test_password_no_se_expone_en_respuesta(self, client, admin_headers):
        """USR-01 (seguridad): La respuesta no debe incluir password ni password_hash."""
        payload = {
            "nombre": "Secure Test",
            "email": _email_unico(),
            "password": "SecurePass99!",
            "rol": "operario",
        }
        resp = client.post("/api/v1/usuarios/", json=payload, headers=admin_headers)
        data = resp.json()
        assert "password" not in data
        assert "password_hash" not in data

    def test_rol_por_defecto_es_operario(self, client, admin_headers):
        """USR-01: Sin especificar rol, debe asignarse 'operario' por defecto."""
        payload = {
            "nombre": "Default Rol",
            "email": _email_unico(),
            "password": "Pass1234!",
        }
        resp = client.post("/api/v1/usuarios/", json=payload, headers=admin_headers)
        assert resp.status_code == 201
        assert resp.json()["rol"] == "operario"

    def test_creado_en_esta_presente(self, client, admin_headers):
        """USR-01: La respuesta incluye el campo creado_en con valor."""
        payload = {
            "nombre": "Timestamp Test",
            "email": _email_unico(),
            "password": "Pass1234!",
            "rol": "operario",
        }
        resp = client.post("/api/v1/usuarios/", json=payload, headers=admin_headers)
        assert "creado_en" in resp.json()
        assert resp.json()["creado_en"] is not None


# ═══════════════════════════════════════════════════════════════════════════════
# USR-02 – Listar usuarios (admin)
# ═══════════════════════════════════════════════════════════════════════════════
class TestUSR02ListarUsuarios:
    """USR-02: GET /usuarios retorna lista de todos los usuarios."""

    def test_listar_retorna_200_y_lista(self, client, admin_headers):
        """USR-02: Admin puede listar todos los usuarios."""
        resp = client.get("/api/v1/usuarios/", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_lista_incluye_usuarios_creados(self, client, admin_headers):
        """USR-02: Un usuario recién creado aparece en el listado."""
        email = _email_unico()
        client.post(
            "/api/v1/usuarios/",
            json={"nombre": "Para Listar", "email": email, "password": "Pass1!"},
            headers=admin_headers,
        )
        resp = client.get("/api/v1/usuarios/", headers=admin_headers)
        emails = [u["email"] for u in resp.json()]
        assert email in emails

    def test_cada_usuario_tiene_campos_requeridos(self, client, admin_headers):
        """USR-02: Cada elemento de la lista tiene los campos del schema."""
        resp = client.get("/api/v1/usuarios/", headers=admin_headers)
        for usuario in resp.json():
            assert "id" in usuario
            assert "nombre" in usuario
            assert "email" in usuario
            assert "rol" in usuario
            assert "activo" in usuario


# ═══════════════════════════════════════════════════════════════════════════════
# USR-03 – Obtener usuario por ID
# ═══════════════════════════════════════════════════════════════════════════════
class TestUSR03ObtenerUsuario:
    """USR-03: GET /usuarios/{id} retorna el usuario correcto."""

    def test_obtener_usuario_existente(self, client, admin_headers):
        """USR-03: Obtener por id correcto → HTTP 200 con datos."""
        create_resp = client.post(
            "/api/v1/usuarios/",
            json={"nombre": "Para Obtener", "email": _email_unico(), "password": "Pass1!"},
            headers=admin_headers,
        )
        user_id = create_resp.json()["id"]

        resp = client.get(f"/api/v1/usuarios/{user_id}", headers=admin_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == user_id

    def test_obtener_usuario_inexistente_retorna_404(self, client, admin_headers):
        """USR-03: id que no existe → HTTP 404."""
        resp = client.get("/api/v1/usuarios/999999", headers=admin_headers)
        assert resp.status_code == 404

    def test_operario_puede_ver_su_propio_perfil(self, client, operario_headers, operario_user):
        """USR-03: Operario puede consultar GET /usuarios/{su_id}."""
        resp = client.get(
            f"/api/v1/usuarios/{operario_user.id}",
            headers=operario_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == operario_user.email


# ═══════════════════════════════════════════════════════════════════════════════
# USR-04 – Actualizar usuario
# ═══════════════════════════════════════════════════════════════════════════════
class TestUSR04ActualizarUsuario:
    """USR-04: PUT /usuarios/{id} actualiza los campos enviados."""

    def test_actualizar_nombre(self, client, admin_headers):
        """USR-04: Cambiar el nombre del usuario."""
        create_resp = client.post(
            "/api/v1/usuarios/",
            json={"nombre": "Nombre Original", "email": _email_unico(), "password": "Pass1!"},
            headers=admin_headers,
        )
        user_id = create_resp.json()["id"]

        resp = client.put(
            f"/api/v1/usuarios/{user_id}",
            json={"nombre": "Nombre Actualizado"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["nombre"] == "Nombre Actualizado"

    def test_actualizar_rol(self, client, admin_headers):
        """USR-04: Cambiar el rol de operario a supervisor."""
        create_resp = client.post(
            "/api/v1/usuarios/",
            json={"nombre": "Cambio Rol", "email": _email_unico(), "password": "Pass1!", "rol": "operario"},
            headers=admin_headers,
        )
        user_id = create_resp.json()["id"]

        resp = client.put(
            f"/api/v1/usuarios/{user_id}",
            json={"rol": "supervisor"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["rol"] == "supervisor"

    def test_actualizar_usuario_inexistente_retorna_404(self, client, admin_headers):
        """USR-04: Actualizar id que no existe → 404."""
        resp = client.put(
            "/api/v1/usuarios/999999",
            json={"nombre": "Fantasma"},
            headers=admin_headers,
        )
        assert resp.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# USR-05 – Eliminar usuario
# ═══════════════════════════════════════════════════════════════════════════════
class TestUSR05EliminarUsuario:
    """USR-05: DELETE /usuarios/{id} elimina el usuario de la BD."""

    def test_eliminar_usuario_retorna_204(self, client, admin_headers):
        """USR-05: Eliminación exitosa → HTTP 204 sin cuerpo."""
        create_resp = client.post(
            "/api/v1/usuarios/",
            json={"nombre": "Para Eliminar", "email": _email_unico(), "password": "Pass1!"},
            headers=admin_headers,
        )
        user_id = create_resp.json()["id"]

        resp = client.delete(f"/api/v1/usuarios/{user_id}", headers=admin_headers)
        assert resp.status_code == 204

    def test_usuario_eliminado_no_aparece_en_listado(self, client, admin_headers):
        """USR-05: Tras eliminar, el usuario no debe aparecer en GET /usuarios/."""
        email = _email_unico()
        create_resp = client.post(
            "/api/v1/usuarios/",
            json={"nombre": "Borrar", "email": email, "password": "Pass1!"},
            headers=admin_headers,
        )
        user_id = create_resp.json()["id"]
        client.delete(f"/api/v1/usuarios/{user_id}", headers=admin_headers)

        list_resp = client.get("/api/v1/usuarios/", headers=admin_headers)
        ids = [u["id"] for u in list_resp.json()]
        assert user_id not in ids

    def test_eliminar_usuario_inexistente_no_falla(self, client, admin_headers):
        """USR-05: Eliminar id que no existe → 404 o 204 (sin crash)."""
        resp = client.delete("/api/v1/usuarios/999998", headers=admin_headers)
        assert resp.status_code in (204, 404)


# ═══════════════════════════════════════════════════════════════════════════════
# USR-06 – Email duplicado
# ═══════════════════════════════════════════════════════════════════════════════
class TestUSR06EmailDuplicado:
    """USR-06: Crear usuario con email ya registrado → HTTP 400."""

    def test_email_duplicado_retorna_400(self, client, admin_headers):
        """USR-06: Segundo registro con mismo email → 400."""
        email = _email_unico()
        payload = {"nombre": "Primero", "email": email, "password": "Pass1!"}
        client.post("/api/v1/usuarios/", json=payload, headers=admin_headers)

        resp = client.post(
            "/api/v1/usuarios/",
            json={"nombre": "Segundo", "email": email, "password": "OtroPass!"},
            headers=admin_headers,
        )
        assert resp.status_code == 400

    def test_mensaje_indica_email_registrado(self, client, admin_headers):
        """USR-06: El mensaje de error debe mencionar que el email ya existe."""
        email = _email_unico()
        client.post(
            "/api/v1/usuarios/",
            json={"nombre": "Primero", "email": email, "password": "Pass1!"},
            headers=admin_headers,
        )
        resp = client.post(
            "/api/v1/usuarios/",
            json={"nombre": "Segundo", "email": email, "password": "Pass1!"},
            headers=admin_headers,
        )
        detail = resp.json().get("detail", "").lower()
        assert "registrado" in detail or "existe" in detail or "duplicate" in detail


# ═══════════════════════════════════════════════════════════════════════════════
# USR-07 – Usuario no encontrado
# ═══════════════════════════════════════════════════════════════════════════════
class TestUSR07UsuarioNoEncontrado:
    """USR-07: Operaciones sobre un id inexistente → HTTP 404."""

    def test_get_id_inexistente(self, client, admin_headers):
        resp = client.get("/api/v1/usuarios/8888888", headers=admin_headers)
        assert resp.status_code == 404

    def test_put_id_inexistente(self, client, admin_headers):
        resp = client.put(
            "/api/v1/usuarios/8888888",
            json={"nombre": "Ghost"},
            headers=admin_headers,
        )
        assert resp.status_code == 404

    def test_mensaje_404_es_descriptivo(self, client, admin_headers):
        """USR-07: El mensaje 404 debe indicar que el usuario no fue encontrado."""
        resp = client.get("/api/v1/usuarios/8888888", headers=admin_headers)
        detail = resp.json().get("detail", "").lower()
        assert "encontrado" in detail or "not found" in detail or "existe" in detail


# ═══════════════════════════════════════════════════════════════════════════════
# USR-08 – Control de acceso por rol
# ═══════════════════════════════════════════════════════════════════════════════
class TestUSR08ControlAccesoRol:
    """USR-08: Operario y Supervisor no pueden crear ni listar usuarios."""

    def test_operario_no_puede_crear_usuario(self, client, operario_headers):
        """USR-08: Operario → POST /usuarios → 403."""
        resp = client.post(
            "/api/v1/usuarios/",
            json={"nombre": "Intento", "email": _email_unico(), "password": "Pass1!"},
            headers=operario_headers,
        )
        assert resp.status_code == 403

    def test_operario_no_puede_listar_usuarios(self, client, operario_headers):
        """USR-08: Operario → GET /usuarios/ → 403."""
        resp = client.get("/api/v1/usuarios/", headers=operario_headers)
        assert resp.status_code == 403

    def test_supervisor_no_puede_crear_usuario(self, client, supervisor_headers):
        """USR-08: Supervisor → POST /usuarios → 403."""
        resp = client.post(
            "/api/v1/usuarios/",
            json={"nombre": "Intento Sup", "email": _email_unico(), "password": "Pass1!"},
            headers=supervisor_headers,
        )
        assert resp.status_code == 403

    def test_supervisor_no_puede_eliminar_usuario(self, client, admin_headers, supervisor_headers):
        """USR-08: Supervisor → DELETE /usuarios/{id} → 403."""
        create_resp = client.post(
            "/api/v1/usuarios/",
            json={"nombre": "Víctima", "email": _email_unico(), "password": "Pass1!"},
            headers=admin_headers,
        )
        user_id = create_resp.json()["id"]
        resp = client.delete(f"/api/v1/usuarios/{user_id}", headers=supervisor_headers)
        assert resp.status_code == 403

    def test_sin_token_no_puede_listar(self, client):
        """USR-08: Sin token → GET /usuarios/ → 401 o 403."""
        resp = client.get("/api/v1/usuarios/")
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════════════════
# USR-09 – Actualización parcial
# ═══════════════════════════════════════════════════════════════════════════════
class TestUSR09ActualizacionParcial:
    """USR-09: PUT con campos parciales solo modifica lo enviado, resto intacto."""

    def test_cambiar_nombre_no_altera_rol(self, client, admin_headers):
        """USR-09: Actualizar solo nombre → el rol permanece igual."""
        email = _email_unico()
        create_resp = client.post(
            "/api/v1/usuarios/",
            json={"nombre": "Original", "email": email, "password": "Pass1!", "rol": "supervisor"},
            headers=admin_headers,
        )
        user_id = create_resp.json()["id"]

        resp = client.put(
            f"/api/v1/usuarios/{user_id}",
            json={"nombre": "Cambiado"},
            headers=admin_headers,
        )
        assert resp.json()["rol"] == "supervisor"
        assert resp.json()["email"] == email

    def test_cambiar_rol_no_altera_nombre(self, client, admin_headers):
        """USR-09: Actualizar solo rol → el nombre permanece igual."""
        create_resp = client.post(
            "/api/v1/usuarios/",
            json={"nombre": "Nombre Fijo", "email": _email_unico(), "password": "Pass1!", "rol": "operario"},
            headers=admin_headers,
        )
        user_id = create_resp.json()["id"]

        resp = client.put(
            f"/api/v1/usuarios/{user_id}",
            json={"rol": "admin"},
            headers=admin_headers,
        )
        assert resp.json()["nombre"] == "Nombre Fijo"
        assert resp.json()["rol"] == "admin"


# ═══════════════════════════════════════════════════════════════════════════════
# USR-10 – Desactivar usuario (activo=False)
# ═══════════════════════════════════════════════════════════════════════════════
class TestUSR10DesactivarUsuario:
    """USR-10: Actualizar activo=False desactiva el usuario sin eliminarlo."""

    def test_desactivar_usuario_cambia_activo_a_false(self, client, admin_headers):
        """USR-10: activo=False en PUT persiste correctamente."""
        create_resp = client.post(
            "/api/v1/usuarios/",
            json={"nombre": "A Desactivar", "email": _email_unico(), "password": "Pass1!"},
            headers=admin_headers,
        )
        user_id = create_resp.json()["id"]

        resp = client.put(
            f"/api/v1/usuarios/{user_id}",
            json={"activo": False},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["activo"] is False

    def test_usuario_desactivado_aun_aparece_en_listado(self, client, admin_headers):
        """USR-10: Desactivar NO elimina; el usuario sigue en el listado."""
        email = _email_unico()
        create_resp = client.post(
            "/api/v1/usuarios/",
            json={"nombre": "Desactivado Visible", "email": email, "password": "Pass1!"},
            headers=admin_headers,
        )
        user_id = create_resp.json()["id"]
        client.put(
            f"/api/v1/usuarios/{user_id}",
            json={"activo": False},
            headers=admin_headers,
        )

        list_resp = client.get("/api/v1/usuarios/", headers=admin_headers)
        ids = [u["id"] for u in list_resp.json()]
        assert user_id in ids

    def test_usuario_desactivado_no_puede_loguearse(self, client, admin_headers):
        """USR-10: Un usuario desactivado via PUT no puede hacer login → 403."""
        email = _email_unico()
        password = "Pass1234!"
        create_resp = client.post(
            "/api/v1/usuarios/",
            json={"nombre": "Bloqueado", "email": email, "password": password},
            headers=admin_headers,
        )
        user_id = create_resp.json()["id"]
        client.put(
            f"/api/v1/usuarios/{user_id}",
            json={"activo": False},
            headers=admin_headers,
        )

        login_resp = client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": password},
        )
        assert login_resp.status_code == 403
