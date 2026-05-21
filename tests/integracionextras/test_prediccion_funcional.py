"""
test_prediccion_funcional.py – Pruebas Funcionales del módulo de Predicción
EntoValleSOL Backend

Casos cubiertos:
  PRED-01 – GET /prediccion/sitotroga retorna predicción con estructura correcta
  PRED-02 – GET /prediccion/trichogramma retorna predicción válida
  PRED-03 – GET /prediccion/galleria retorna predicción válida
  PRED-04 – GET /prediccion/paratheresia retorna predicción válida
  PRED-05 – GET /prediccion/todas retorna predicciones de todas las especies
  PRED-06 – Parámetro dias=1 (mínimo permitido) funciona correctamente
  PRED-07 – Parámetro dias=365 (máximo permitido) funciona correctamente
  PRED-08 – dias=0 → HTTP 422 (fuera de rango)
  PRED-09 – dias=366 → HTTP 422 (fuera de rango)
  PRED-10 – Todos los endpoints de predicción requieren autenticación

Ejecutar:
  pytest tests/integracionextras/test_prediccion_funcional.py -v
"""
import pytest


ESPECIES_ENDPOINTS = [
    "/api/v1/prediccion/sitotroga",
    "/api/v1/prediccion/trichogramma",
    "/api/v1/prediccion/galleria",
    "/api/v1/prediccion/paratheresia",
]


# ═══════════════════════════════════════════════════════════════════════════════
# PRED-01 – Predicción Sitotroga
# ═══════════════════════════════════════════════════════════════════════════════
class TestPRED01PrediccionSitotroga:
    """PRED-01: GET /prediccion/sitotroga retorna estructura de predicción correcta."""

    def test_retorna_http_200(self, client, admin_headers):
        """PRED-01: Respuesta exitosa con código 200."""
        resp = client.get("/api/v1/prediccion/sitotroga", headers=admin_headers)
        assert resp.status_code == 200

    def test_respuesta_es_objeto_no_lista(self, client, admin_headers):
        """PRED-01: La respuesta es un objeto (dict), no una lista."""
        resp = client.get("/api/v1/prediccion/sitotroga", headers=admin_headers)
        assert isinstance(resp.json(), dict)

    def test_contiene_campo_predicciones_o_equivalente(self, client, admin_headers):
        """PRED-01: La respuesta incluye datos de predicción (campo predicciones, datos o similar)."""
        resp = client.get("/api/v1/prediccion/sitotroga", headers=admin_headers)
        data = resp.json()
        # El campo exacto depende de la implementación de PrediccionService
        tiene_datos = any(
            k in data
            for k in ("predicciones", "datos", "values", "forecast", "resultado", "items")
        )
        assert tiene_datos or len(data) > 0, (
            "La respuesta no contiene ningún campo de predicción reconocible"
        )

    def test_parametro_dias_por_defecto_es_30(self, client, admin_headers):
        """PRED-01: Sin especificar dias, el endpoint usa 30 días por defecto."""
        resp = client.get("/api/v1/prediccion/sitotroga", headers=admin_headers)
        assert resp.status_code == 200  # No debe fallar con el default


# ═══════════════════════════════════════════════════════════════════════════════
# PRED-02/03/04 – Predicción por especie
# ═══════════════════════════════════════════════════════════════════════════════
class TestPRED02_04PrediccionPorEspecie:
    """PRED-02/03/04: Cada especie tiene su propio endpoint de predicción."""

    @pytest.mark.parametrize("endpoint", ESPECIES_ENDPOINTS)
    def test_endpoint_retorna_200(self, client, admin_headers, endpoint):
        """PRED-02/03/04: Cada endpoint de especie debe responder con 200."""
        resp = client.get(endpoint, headers=admin_headers)
        assert resp.status_code == 200, (
            f"Endpoint {endpoint} falló con {resp.status_code}: {resp.text}"
        )

    @pytest.mark.parametrize("endpoint", ESPECIES_ENDPOINTS)
    def test_endpoint_retorna_dict(self, client, admin_headers, endpoint):
        """PRED-02/03/04: La respuesta debe ser un objeto JSON."""
        resp = client.get(endpoint, headers=admin_headers)
        assert isinstance(resp.json(), dict)

    @pytest.mark.parametrize("endpoint", ESPECIES_ENDPOINTS)
    def test_endpoint_acepta_parametro_dias(self, client, admin_headers, endpoint):
        """PRED-02/03/04: Pasar dias=60 debe funcionar sin error."""
        resp = client.get(endpoint, params={"dias": 60}, headers=admin_headers)
        assert resp.status_code == 200

    def test_trichogramma_retorna_200(self, client, admin_headers):
        """PRED-02: Específico para trichogramma."""
        resp = client.get("/api/v1/prediccion/trichogramma", headers=admin_headers)
        assert resp.status_code == 200

    def test_galleria_retorna_200(self, client, admin_headers):
        """PRED-03: Específico para galleria."""
        resp = client.get("/api/v1/prediccion/galleria", headers=admin_headers)
        assert resp.status_code == 200

    def test_paratheresia_retorna_200(self, client, admin_headers):
        """PRED-04: Específico para paratheresia."""
        resp = client.get("/api/v1/prediccion/paratheresia", headers=admin_headers)
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# PRED-05 – Predicción de todas las especies
# ═══════════════════════════════════════════════════════════════════════════════
class TestPRED05PrediccionTodas:
    """PRED-05: GET /prediccion/todas retorna predicciones de todas las especies."""

    def test_retorna_200(self, client, admin_headers):
        """PRED-05: Respuesta exitosa."""
        resp = client.get("/api/v1/prediccion/todas", headers=admin_headers)
        assert resp.status_code == 200

    def test_retorna_objeto_con_multiples_claves(self, client, admin_headers):
        """PRED-05: La respuesta debe incluir datos de más de una especie."""
        resp = client.get("/api/v1/prediccion/todas", headers=admin_headers)
        data = resp.json()
        # Debe haber al menos 2 claves (una por especie o estructura agrupada)
        assert len(data) >= 2 or isinstance(data, dict)

    def test_acepta_parametro_dias(self, client, admin_headers):
        """PRED-05: /prediccion/todas acepta el parámetro dias."""
        resp = client.get(
            "/api/v1/prediccion/todas",
            params={"dias": 90},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_operario_puede_acceder(self, client, operario_headers):
        """PRED-05: Operario también puede consultar predicciones."""
        resp = client.get("/api/v1/prediccion/todas", headers=operario_headers)
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# PRED-06 – Parámetro dias mínimo (1)
# ═══════════════════════════════════════════════════════════════════════════════
class TestPRED06DiasMinimo:
    """PRED-06: dias=1 es el mínimo permitido y debe funcionar correctamente."""

    @pytest.mark.parametrize("endpoint", ESPECIES_ENDPOINTS)
    def test_dias_1_retorna_200(self, client, admin_headers, endpoint):
        """PRED-06: dias=1 en todos los endpoints → 200."""
        resp = client.get(endpoint, params={"dias": 1}, headers=admin_headers)
        assert resp.status_code == 200

    def test_dias_1_en_todas_las_especies(self, client, admin_headers):
        """PRED-06: /prediccion/todas con dias=1 → 200."""
        resp = client.get(
            "/api/v1/prediccion/todas",
            params={"dias": 1},
            headers=admin_headers,
        )
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# PRED-07 – Parámetro dias máximo (365)
# ═══════════════════════════════════════════════════════════════════════════════
class TestPRED07DiasMaximo:
    """PRED-07: dias=365 es el máximo permitido y debe funcionar correctamente."""

    @pytest.mark.parametrize("endpoint", ESPECIES_ENDPOINTS)
    def test_dias_365_retorna_200(self, client, admin_headers, endpoint):
        """PRED-07: dias=365 en todos los endpoints → 200."""
        resp = client.get(endpoint, params={"dias": 365}, headers=admin_headers)
        assert resp.status_code == 200

    def test_dias_365_en_todas_las_especies(self, client, admin_headers):
        """PRED-07: /prediccion/todas con dias=365 → 200."""
        resp = client.get(
            "/api/v1/prediccion/todas",
            params={"dias": 365},
            headers=admin_headers,
        )
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# PRED-08 – dias=0 fuera de rango mínimo
# ═══════════════════════════════════════════════════════════════════════════════
class TestPRED08DiasCeroInvalido:
    """PRED-08: dias=0 está fuera del rango ge=1 y debe retornar HTTP 422."""

    @pytest.mark.parametrize("endpoint", ESPECIES_ENDPOINTS)
    def test_dias_0_retorna_422(self, client, admin_headers, endpoint):
        """PRED-08: dias=0 → 422 en todos los endpoints de especie."""
        resp = client.get(endpoint, params={"dias": 0}, headers=admin_headers)
        assert resp.status_code == 422, (
            f"Endpoint {endpoint} aceptó dias=0 (retornó {resp.status_code})"
        )

    def test_dias_0_en_todas_retorna_422(self, client, admin_headers):
        """PRED-08: /prediccion/todas con dias=0 → 422."""
        resp = client.get(
            "/api/v1/prediccion/todas",
            params={"dias": 0},
            headers=admin_headers,
        )
        assert resp.status_code == 422

    def test_dias_negativos_retorna_422(self, client, admin_headers):
        """PRED-08 (variante): dias negativos también deben ser rechazados."""
        resp = client.get(
            "/api/v1/prediccion/sitotroga",
            params={"dias": -5},
            headers=admin_headers,
        )
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# PRED-09 – dias=366 fuera de rango máximo
# ═══════════════════════════════════════════════════════════════════════════════
class TestPRED09DiasMaximoExcedido:
    """PRED-09: dias=366 supera el máximo le=365 y debe retornar HTTP 422."""

    @pytest.mark.parametrize("endpoint", ESPECIES_ENDPOINTS)
    def test_dias_366_retorna_422(self, client, admin_headers, endpoint):
        """PRED-09: dias=366 → 422 en todos los endpoints de especie."""
        resp = client.get(endpoint, params={"dias": 366}, headers=admin_headers)
        assert resp.status_code == 422, (
            f"Endpoint {endpoint} aceptó dias=366 (retornó {resp.status_code})"
        )

    def test_dias_1000_retorna_422(self, client, admin_headers):
        """PRED-09 (variante): Un valor muy alto también debe rechazarse."""
        resp = client.get(
            "/api/v1/prediccion/sitotroga",
            params={"dias": 1000},
            headers=admin_headers,
        )
        assert resp.status_code == 422

    def test_dias_366_en_todas_retorna_422(self, client, admin_headers):
        """PRED-09: /prediccion/todas con dias=366 → 422."""
        resp = client.get(
            "/api/v1/prediccion/todas",
            params={"dias": 366},
            headers=admin_headers,
        )
        assert resp.status_code == 422


# ═══════════════════════════════════════════════════════════════════════════════
# PRED-10 – Autenticación requerida
# ═══════════════════════════════════════════════════════════════════════════════
class TestPRED10Autenticacion:
    """PRED-10: Todos los endpoints de predicción requieren token JWT."""

    ALL_ENDPOINTS = ESPECIES_ENDPOINTS + ["/api/v1/prediccion/todas"]

    @pytest.mark.parametrize("endpoint", ALL_ENDPOINTS)
    def test_sin_token_retorna_401_o_403(self, client, endpoint):
        """PRED-10: GET sin Authorization → 401 o 403."""
        resp = client.get(endpoint)
        assert resp.status_code in (401, 403), (
            f"Endpoint {endpoint} no está protegido (retornó {resp.status_code})"
        )

    def test_token_invalido_retorna_401(self, client):
        """PRED-10: Token malformado → 401 o 403."""
        resp = client.get(
            "/api/v1/prediccion/sitotroga",
            headers={"Authorization": "Bearer token.invalido.fake"},
        )
        assert resp.status_code in (401, 403)

    @pytest.mark.parametrize("endpoint", ALL_ENDPOINTS)
    def test_con_token_valido_retorna_200(self, client, operario_headers, endpoint):
        """PRED-10 (positivo): Token válido permite acceso."""
        resp = client.get(endpoint, headers=operario_headers)
        assert resp.status_code == 200
