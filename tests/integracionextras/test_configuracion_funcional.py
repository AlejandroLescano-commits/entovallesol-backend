"""
test_configuracion_funcional.py – Pruebas Funcionales del módulo de Configuración
EntoValleSOL Backend

Casos cubiertos:
  CFG-01 – GET /config/ retorna listado de especies, roles y versión (solo admin)
  CFG-02 – GET /config/lugares/avispitas retorna lugares activos
  CFG-03 – GET /config/lugares/moscas retorna lugares activos
  CFG-04 – GET /config/unidades/sitodroga retorna unidades activas
  CFG-05 – GET /config/unidades/avispas retorna unidades activas
  CFG-06 – GET /config/unidades/galleria retorna unidades activas
  CFG-07 – GET /config/unidades/moscas retorna unidades activas
  CFG-08 – Todos los endpoints de config requieren autenticación
  CFG-09 – GET /config/ solo accesible para admin (operario → 403)
  CFG-10 – Respuestas de catálogos tienen estructura id/nombre/activo

Ejecutar:
  pytest tests/integracionextras/test_configuracion_funcional.py -v
"""
import pytest


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-01 – Configuración general (solo admin)
# ═══════════════════════════════════════════════════════════════════════════════
class TestCFG01ConfiguracionGeneral:
    """CFG-01: GET /config/ retorna la configuración global del sistema."""

    def test_admin_obtiene_config_correcta(self, client, admin_headers):
        """CFG-01: Admin puede acceder y recibe especies, roles y versión."""
        resp = client.get("/api/v1/config/", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "especies" in data
        assert "roles" in data
        assert "version" in data

    def test_especies_incluye_todas_las_esperadas(self, client, admin_headers):
        """CFG-01: El listado de especies debe incluir las 5 especies del sistema."""
        resp = client.get("/api/v1/config/", headers=admin_headers)
        especies = resp.json()["especies"]
        esperadas = {
            "sitotroga",
            "trichogramma_exiguum",
            "trichogramma_pretiosum",
            "galleria",
            "paratheresia",
        }
        assert esperadas.issubset(set(especies)), (
            f"Faltan especies. Recibidas: {especies}"
        )

    def test_roles_incluye_los_tres_roles(self, client, admin_headers):
        """CFG-01: Deben existir exactamente los roles admin, supervisor, operario."""
        resp = client.get("/api/v1/config/", headers=admin_headers)
        roles = resp.json()["roles"]
        assert "admin" in roles
        assert "supervisor" in roles
        assert "operario" in roles

    def test_version_es_string_no_vacio(self, client, admin_headers):
        """CFG-01: El campo versión debe ser un string no vacío."""
        resp = client.get("/api/v1/config/", headers=admin_headers)
        version = resp.json()["version"]
        assert isinstance(version, str)
        assert len(version) > 0


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-02 – Lugares de liberación de avispitas
# ═══════════════════════════════════════════════════════════════════════════════
class TestCFG02LugaresAvispitas:
    """CFG-02: GET /config/lugares/avispitas retorna lista de lugares activos."""

    def test_retorna_200_y_lista(self, client, admin_headers):
        """CFG-02: Respuesta 200 con una lista."""
        resp = client.get("/api/v1/config/lugares/avispitas", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_todos_los_elementos_estan_activos(self, client, admin_headers):
        """CFG-02: Ningún lugar retornado debe tener activo=False."""
        resp = client.get("/api/v1/config/lugares/avispitas", headers=admin_headers)
        for lugar in resp.json():
            assert lugar.get("activo") is True, (
                f"Lugar inactivo encontrado: {lugar}"
            )

    def test_operario_puede_acceder(self, client, operario_headers):
        """CFG-02: Este endpoint es accesible para cualquier usuario autenticado."""
        resp = client.get("/api/v1/config/lugares/avispitas", headers=operario_headers)
        assert resp.status_code == 200

    def test_sin_token_retorna_401(self, client):
        """CFG-02: Sin autenticación → 401 o 403."""
        resp = client.get("/api/v1/config/lugares/avispitas")
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-03 – Lugares de liberación de moscas
# ═══════════════════════════════════════════════════════════════════════════════
class TestCFG03LugaresMoscas:
    """CFG-03: GET /config/lugares/moscas retorna lista de lugares activos."""

    def test_retorna_200_y_lista(self, client, admin_headers):
        """CFG-03: Respuesta 200 con lista."""
        resp = client.get("/api/v1/config/lugares/moscas", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_todos_los_elementos_estan_activos(self, client, admin_headers):
        """CFG-03: Solo deben retornarse lugares con activo=True."""
        resp = client.get("/api/v1/config/lugares/moscas", headers=admin_headers)
        for lugar in resp.json():
            assert lugar.get("activo") is True

    def test_supervisor_puede_acceder(self, client, supervisor_headers):
        """CFG-03: Supervisor también puede consultar este catálogo."""
        resp = client.get("/api/v1/config/lugares/moscas", headers=supervisor_headers)
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-04 – Unidades de medida sitodroga
# ═══════════════════════════════════════════════════════════════════════════════
class TestCFG04UnidadesSitodroga:
    """CFG-04: GET /config/unidades/sitodroga retorna unidades activas."""

    def test_retorna_200_y_lista(self, client, admin_headers):
        resp = client.get("/api/v1/config/unidades/sitodroga", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_elementos_tienen_campo_nombre(self, client, admin_headers):
        """CFG-04: Cada unidad debe tener al menos id y nombre."""
        resp = client.get("/api/v1/config/unidades/sitodroga", headers=admin_headers)
        for unidad in resp.json():
            assert "id" in unidad
            assert "nombre" in unidad

    def test_solo_activos(self, client, admin_headers):
        """CFG-04: Unidades con activo=False no deben aparecer."""
        resp = client.get("/api/v1/config/unidades/sitodroga", headers=admin_headers)
        for unidad in resp.json():
            assert unidad.get("activo") is True


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-05 – Unidades de medida avispas
# ═══════════════════════════════════════════════════════════════════════════════
class TestCFG05UnidadesAvispas:
    """CFG-05: GET /config/unidades/avispas retorna unidades de avispas activas."""

    def test_retorna_200_y_lista(self, client, admin_headers):
        resp = client.get("/api/v1/config/unidades/avispas", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_solo_activos(self, client, admin_headers):
        resp = client.get("/api/v1/config/unidades/avispas", headers=admin_headers)
        for unidad in resp.json():
            assert unidad.get("activo") is True

    def test_operario_puede_acceder(self, client, operario_headers):
        resp = client.get("/api/v1/config/unidades/avispas", headers=operario_headers)
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-06 – Unidades de medida galleria
# ═══════════════════════════════════════════════════════════════════════════════
class TestCFG06UnidadesGalleria:
    """CFG-06: GET /config/unidades/galleria retorna unidades de galleria activas."""

    def test_retorna_200_y_lista(self, client, admin_headers):
        resp = client.get("/api/v1/config/unidades/galleria", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_elementos_tienen_id_nombre_activo(self, client, admin_headers):
        """CFG-06: Schema mínimo de cada elemento."""
        resp = client.get("/api/v1/config/unidades/galleria", headers=admin_headers)
        for u in resp.json():
            assert "id" in u
            assert "nombre" in u

    def test_solo_activos(self, client, admin_headers):
        resp = client.get("/api/v1/config/unidades/galleria", headers=admin_headers)
        for u in resp.json():
            assert u.get("activo") is True


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-07 – Unidades de medida moscas
# ═══════════════════════════════════════════════════════════════════════════════
class TestCFG07UnidadesMoscas:
    """CFG-07: GET /config/unidades/moscas retorna unidades de moscas activas."""

    def test_retorna_200_y_lista(self, client, admin_headers):
        resp = client.get("/api/v1/config/unidades/moscas", headers=admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_solo_activos(self, client, admin_headers):
        resp = client.get("/api/v1/config/unidades/moscas", headers=admin_headers)
        for u in resp.json():
            assert u.get("activo") is True

    def test_supervisor_puede_acceder(self, client, supervisor_headers):
        resp = client.get("/api/v1/config/unidades/moscas", headers=supervisor_headers)
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-08 – Autenticación requerida en todos los endpoints
# ═══════════════════════════════════════════════════════════════════════════════
class TestCFG08AutenticacionRequerida:
    """CFG-08: Sin token, todos los endpoints de config deben rechazar la request."""

    ENDPOINTS = [
        "/api/v1/config/lugares/avispitas",
        "/api/v1/config/lugares/moscas",
        "/api/v1/config/unidades/sitodroga",
        "/api/v1/config/unidades/avispas",
        "/api/v1/config/unidades/galleria",
        "/api/v1/config/unidades/moscas",
    ]

    @pytest.mark.parametrize("endpoint", ENDPOINTS)
    def test_sin_token_retorna_401_o_403(self, client, endpoint):
        """CFG-08: Cada endpoint de catálogo requiere autenticación."""
        resp = client.get(endpoint)
        assert resp.status_code in (401, 403), (
            f"Endpoint {endpoint} no está protegido (retornó {resp.status_code})"
        )

    def test_config_principal_sin_token_retorna_401(self, client):
        """CFG-08: GET /config/ sin token → 401 o 403."""
        resp = client.get("/api/v1/config/")
        assert resp.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-09 – Control de acceso en /config/ (solo admin)
# ═══════════════════════════════════════════════════════════════════════════════
class TestCFG09ControlAccesoConfig:
    """CFG-09: GET /config/ es exclusivo de admin; otros roles reciben 403."""

    def test_operario_no_puede_acceder_a_config_principal(self, client, operario_headers):
        """CFG-09: Operario → GET /config/ → 403."""
        resp = client.get("/api/v1/config/", headers=operario_headers)
        assert resp.status_code == 403

    def test_supervisor_no_puede_acceder_a_config_principal(self, client, supervisor_headers):
        """CFG-09: Supervisor → GET /config/ → 403."""
        resp = client.get("/api/v1/config/", headers=supervisor_headers)
        assert resp.status_code == 403

    def test_admin_si_puede_acceder(self, client, admin_headers):
        """CFG-09 (positivo): Admin → GET /config/ → 200."""
        resp = client.get("/api/v1/config/", headers=admin_headers)
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# CFG-10 – Estructura de respuesta de catálogos
# ═══════════════════════════════════════════════════════════════════════════════
class TestCFG10EstructuraRespuesta:
    """CFG-10: Las respuestas de catálogos tienen los campos id, nombre y activo."""

    CATALOGOS = [
        "/api/v1/config/lugares/avispitas",
        "/api/v1/config/lugares/moscas",
        "/api/v1/config/unidades/sitodroga",
        "/api/v1/config/unidades/avispas",
        "/api/v1/config/unidades/galleria",
        "/api/v1/config/unidades/moscas",
    ]

    @pytest.mark.parametrize("endpoint", CATALOGOS)
    def test_estructura_minima_de_catalogo(self, client, admin_headers, endpoint):
        """CFG-10: Cada elemento del catálogo tiene id, nombre y activo."""
        resp = client.get(endpoint, headers=admin_headers)
        assert resp.status_code == 200
        for elemento in resp.json():
            assert "id" in elemento, f"Falta 'id' en {endpoint}"
            assert "nombre" in elemento, f"Falta 'nombre' en {endpoint}"
            assert "activo" in elemento, f"Falta 'activo' en {endpoint}"

    @pytest.mark.parametrize("endpoint", CATALOGOS)
    def test_ids_son_enteros_positivos(self, client, admin_headers, endpoint):
        """CFG-10: Los ids deben ser enteros positivos."""
        resp = client.get(endpoint, headers=admin_headers)
        for elemento in resp.json():
            assert isinstance(elemento["id"], int)
            assert elemento["id"] > 0

    @pytest.mark.parametrize("endpoint", CATALOGOS)
    def test_nombres_no_estan_vacios(self, client, admin_headers, endpoint):
        """CFG-10: El campo nombre no debe ser vacío ni null."""
        resp = client.get(endpoint, headers=admin_headers)
        for elemento in resp.json():
            assert elemento["nombre"] is not None
            assert len(str(elemento["nombre"])) > 0
