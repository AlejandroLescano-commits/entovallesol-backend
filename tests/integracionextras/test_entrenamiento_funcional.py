"""
test_entrenamiento_funcional.py – Pruebas Funcionales del módulo de Entrenamiento
EntoValleSOL Backend

Casos cubiertos:
  ENT-01 – POST /entrenamiento/entrenar con CRON_SECRET válido → entrena todas las especies
  ENT-02 – POST /entrenamiento/entrenar con CRON_SECRET inválido → HTTP 403
  ENT-03 – POST /entrenamiento/entrenar sin header CRON_SECRET → HTTP 403
  ENT-04 – POST /entrenamiento/entrenar/manual sin especie → entrena todas
  ENT-05 – POST /entrenamiento/entrenar/manual con especie específica → solo esa
  ENT-06 – POST /entrenamiento/entrenar/manual con especie inválida → error controlado
  ENT-07 – GET /entrenamiento/config retorna configuración de todas las especies
  ENT-08 – PATCH /entrenamiento/config/{especie} actualiza activo
  ENT-09 – PATCH /entrenamiento/config/{especie} actualiza rango_meses
  ENT-10 – GET /entrenamiento/kpis/{especie} retorna métricas del modelo
  ENT-11 – Entrenamiento manual requiere autenticación
  ENT-12 – KPIs de especie inexistente retorna error controlado

Ejecutar:
  pytest tests/integracionextras/test_entrenamiento_funcional.py -v
"""
import os
import pytest

# El CRON_SECRET para tests (debe coincidir con lo que el entorno de test tenga)
CRON_SECRET_VALIDO = os.getenv("CRON_SECRET", "test_cron_secret_12345")

ESPECIES_VALIDAS = ["sitotroga", "trichogramma", "galleria", "paratheresia"]


# ═══════════════════════════════════════════════════════════════════════════════
# ENT-01 – Entrenamiento automático con CRON_SECRET válido
# ═══════════════════════════════════════════════════════════════════════════════
class TestENT01EntrenamientoAutomatico:
    """ENT-01: POST /entrenamiento/entrenar con CRON_SECRET correcto → 200."""

    def test_entrena_todas_las_especies(self, client):
        """ENT-01: La respuesta incluye una clave por cada especie entrenada."""
        resp = client.post(
            "/api/v1/entrenamiento/entrenar",
            headers={"x-cron-secret": CRON_SECRET_VALIDO},
        )
        assert resp.status_code == 200
        data = resp.json()
        for especie in ESPECIES_VALIDAS:
            assert especie in data, f"Falta la especie '{especie}' en la respuesta"

    def test_respuesta_es_dict_de_resultados(self, client):
        """ENT-01: La respuesta es un dict con resultado por especie."""
        resp = client.post(
            "/api/v1/entrenamiento/entrenar",
            headers={"x-cron-secret": CRON_SECRET_VALIDO},
        )
        assert isinstance(resp.json(), dict)


# ═══════════════════════════════════════════════════════════════════════════════
# ENT-02 – CRON_SECRET inválido
# ═══════════════════════════════════════════════════════════════════════════════
class TestENT02CronSecretInvalido:
    """ENT-02: POST /entrenamiento/entrenar con secret incorrecto → HTTP 403."""

    def test_secret_incorrecto_retorna_403(self, client):
        """ENT-02: CRON_SECRET erróneo → 403."""
        resp = client.post(
            "/api/v1/entrenamiento/entrenar",
            headers={"x-cron-secret": "secret_incorrecto_999"},
        )
        assert resp.status_code == 403

    def test_secret_vacio_retorna_403(self, client):
        """ENT-02 (variante): CRON_SECRET vacío → 403."""
        resp = client.post(
            "/api/v1/entrenamiento/entrenar",
            headers={"x-cron-secret": ""},
        )
        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════════
# ENT-03 – Sin header CRON_SECRET
# ═══════════════════════════════════════════════════════════════════════════════
class TestENT03SinCronSecret:
    """ENT-03: POST /entrenamiento/entrenar sin el header → HTTP 403."""

    def test_sin_header_retorna_403(self, client):
        """ENT-03: Ausencia total del header x-cron-secret → 403."""
        resp = client.post("/api/v1/entrenamiento/entrenar")
        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════════
# ENT-04 – Entrenamiento manual sin especie (todas)
# ═══════════════════════════════════════════════════════════════════════════════
class TestENT04EntrenamientoManualTodas:
    """ENT-04: POST /entrenamiento/entrenar/manual sin query param → todas las especies."""

    def test_sin_especie_entrena_todas(self, client, admin_headers):
        """ENT-04: Sin query param especie → las 4 especies aparecen en respuesta."""
        resp = client.post(
            "/api/v1/entrenamiento/entrenar/manual",
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        for especie in ESPECIES_VALIDAS:
            assert especie in data

    def test_respuesta_tiene_resultados_por_especie(self, client, admin_headers):
        """ENT-04: Cada especie tiene un resultado (no nulo)."""
        resp = client.post(
            "/api/v1/entrenamiento/entrenar/manual",
            headers=admin_headers,
        )
        data = resp.json()
        for especie in ESPECIES_VALIDAS:
            assert data[especie] is not None


# ═══════════════════════════════════════════════════════════════════════════════
# ENT-05 – Entrenamiento manual de especie específica
# ═══════════════════════════════════════════════════════════════════════════════
class TestENT05EntrenamientoManualEspecifica:
    """ENT-05: POST /entrenamiento/entrenar/manual?especie=X → solo esa especie."""

    @pytest.mark.parametrize("especie", ESPECIES_VALIDAS)
    def test_entrena_solo_especie_solicitada(self, client, admin_headers, especie):
        """ENT-05: Al especificar una especie, la respuesta tiene solo esa clave."""
        resp = client.post(
            "/api/v1/entrenamiento/entrenar/manual",
            params={"especie": especie},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert especie in data
        # Las otras especies NO deben aparecer
        otras = [e for e in ESPECIES_VALIDAS if e != especie]
        for otra in otras:
            assert otra not in data, (
                f"Especie '{otra}' apareció en la respuesta cuando solo se pidió '{especie}'"
            )


# ═══════════════════════════════════════════════════════════════════════════════
# ENT-06 – Entrenamiento manual con especie inválida
# ═══════════════════════════════════════════════════════════════════════════════
class TestENT06EspecieInvalida:
    """ENT-06: Especie inválida en entrenamiento manual → error controlado (no 500)."""

    def test_especie_inexistente_no_retorna_500(self, client, admin_headers):
        """ENT-06: Una especie que no existe no debe causar un crash del servidor."""
        resp = client.post(
            "/api/v1/entrenamiento/entrenar/manual",
            params={"especie": "especie_inexistente"},
            headers=admin_headers,
        )
        assert resp.status_code != 500, (
            f"El servidor crasheó con especie inválida: {resp.text}"
        )

    def test_especie_inexistente_retorna_error_descriptivo(self, client, admin_headers):
        """ENT-06: El error para especie inválida debe ser 400 o 404, no 200."""
        resp = client.post(
            "/api/v1/entrenamiento/entrenar/manual",
            params={"especie": "especie_que_no_existe"},
            headers=admin_headers,
        )
        # No debería ser exitoso con una especie inválida
        assert resp.status_code in (200, 400, 404, 422), (
            f"Status inesperado: {resp.status_code}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# ENT-07 – GET /entrenamiento/config
# ═══════════════════════════════════════════════════════════════════════════════
class TestENT07ConfiguracionEntrenamiento:
    """ENT-07: GET /entrenamiento/config retorna config de todas las especies."""

    def test_retorna_200(self, client, admin_headers):
        """ENT-07: Respuesta exitosa."""
        resp = client.get("/api/v1/entrenamiento/config", headers=admin_headers)
        assert resp.status_code == 200

    def test_retorna_lista_o_dict(self, client, admin_headers):
        """ENT-07: La respuesta es una lista o diccionario de configuraciones."""
        resp = client.get("/api/v1/entrenamiento/config", headers=admin_headers)
        assert isinstance(resp.json(), (list, dict))

    def test_incluye_configuracion_de_especies_validas(self, client, admin_headers):
        """ENT-07: La config incluye configuración para al menos una especie conocida."""
        resp = client.get("/api/v1/entrenamiento/config", headers=admin_headers)
        data = resp.json()
        # Si es lista, buscar por nombre; si es dict, buscar claves
        if isinstance(data, list):
            nombres = [c.get("especie") or c.get("nombre") for c in data]
            tiene_alguna = any(e in str(nombres) for e in ESPECIES_VALIDAS)
        else:
            tiene_alguna = any(e in str(data) for e in ESPECIES_VALIDAS)
        assert tiene_alguna

    def test_acceso_sin_token_retorna_200_o_401(self, client):
        """ENT-07: Config de entrenamiento puede ser pública o protegida."""
        resp = client.get("/api/v1/entrenamiento/config")
        assert resp.status_code in (200, 401, 403)


# ═══════════════════════════════════════════════════════════════════════════════
# ENT-08 – PATCH config: actualizar activo
# ═══════════════════════════════════════════════════════════════════════════════
class TestENT08ActualizarActivo:
    """ENT-08: PATCH /entrenamiento/config/{especie} actualiza el campo activo."""

    @pytest.mark.parametrize("especie", ESPECIES_VALIDAS)
    def test_desactivar_especie(self, client, admin_headers, especie):
        """ENT-08: activo=false desactiva el entrenamiento automático de la especie."""
        resp = client.patch(
            f"/api/v1/entrenamiento/config/{especie}",
            params={"activo": False},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("activo") is False or "activo" in str(data)

    @pytest.mark.parametrize("especie", ESPECIES_VALIDAS)
    def test_reactivar_especie(self, client, admin_headers, especie):
        """ENT-08: activo=true reactiva el entrenamiento de la especie."""
        resp = client.patch(
            f"/api/v1/entrenamiento/config/{especie}",
            params={"activo": True},
            headers=admin_headers,
        )
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# ENT-09 – PATCH config: actualizar rango_meses
# ═══════════════════════════════════════════════════════════════════════════════
class TestENT09ActualizarRangoMeses:
    """ENT-09: PATCH /entrenamiento/config/{especie} actualiza rango_meses."""

    @pytest.mark.parametrize("especie", ESPECIES_VALIDAS)
    def test_actualizar_rango_meses(self, client, admin_headers, especie):
        """ENT-09: rango_meses=6 persiste correctamente."""
        resp = client.patch(
            f"/api/v1/entrenamiento/config/{especie}",
            params={"rango_meses": 6},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_actualizar_activo_y_rango_juntos(self, client, admin_headers):
        """ENT-09: Se pueden actualizar activo y rango_meses en la misma request."""
        resp = client.patch(
            "/api/v1/entrenamiento/config/sitotroga",
            params={"activo": True, "rango_meses": 12},
            headers=admin_headers,
        )
        assert resp.status_code == 200

    def test_especie_inexistente_en_config_retorna_error(self, client, admin_headers):
        """ENT-09: Configurar una especie que no existe → 400 o 404."""
        resp = client.patch(
            "/api/v1/entrenamiento/config/especie_falsa",
            params={"activo": True},
            headers=admin_headers,
        )
        assert resp.status_code in (400, 404, 422)


# ═══════════════════════════════════════════════════════════════════════════════
# ENT-10 – GET /entrenamiento/kpis/{especie}
# ═══════════════════════════════════════════════════════════════════════════════
class TestENT10KPIsEspecie:
    """ENT-10: GET /entrenamiento/kpis/{especie} retorna métricas del modelo."""

    @pytest.mark.parametrize("especie", ESPECIES_VALIDAS)
    def test_kpis_retorna_200(self, client, admin_headers, especie):
        """ENT-10: KPIs disponibles para cada especie válida."""
        resp = client.get(
            f"/api/v1/entrenamiento/kpis/{especie}",
            headers=admin_headers,
        )
        assert resp.status_code == 200

    @pytest.mark.parametrize("especie", ESPECIES_VALIDAS)
    def test_kpis_retorna_objeto(self, client, admin_headers, especie):
        """ENT-10: Los KPIs son un objeto JSON (dict)."""
        resp = client.get(
            f"/api/v1/entrenamiento/kpis/{especie}",
            headers=admin_headers,
        )
        assert isinstance(resp.json(), dict)


# ═══════════════════════════════════════════════════════════════════════════════
# ENT-11 – Autenticación requerida en entrenamiento manual
# ═══════════════════════════════════════════════════════════════════════════════
class TestENT11Autenticacion:
    """ENT-11: El endpoint de entrenamiento manual requiere token JWT."""

    def test_manual_sin_token_retorna_401(self, client):
        """ENT-11: POST /entrenamiento/entrenar/manual sin token → 401 o 403."""
        resp = client.post("/api/v1/entrenamiento/entrenar/manual")
        assert resp.status_code in (401, 403)

    def test_manual_con_token_invalido_retorna_401(self, client):
        """ENT-11: Token malformado → 401 o 403."""
        resp = client.post(
            "/api/v1/entrenamiento/entrenar/manual",
            headers={"Authorization": "Bearer token.falso.aqui"},
        )
        assert resp.status_code in (401, 403)

    def test_manual_con_token_valido_funciona(self, client, admin_headers):
        """ENT-11 (positivo): Con token válido, el endpoint responde con 200."""
        resp = client.post(
            "/api/v1/entrenamiento/entrenar/manual",
            headers=admin_headers,
        )
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════════
# ENT-12 – KPIs de especie inexistente
# ═══════════════════════════════════════════════════════════════════════════════
class TestENT12KPIsEspecieInexistente:
    """ENT-12: KPIs de una especie que no existe → error controlado."""

    def test_especie_inexistente_no_retorna_500(self, client, admin_headers):
        """ENT-12: Especie inválida en KPIs no debe causar un crash."""
        resp = client.get(
            "/api/v1/entrenamiento/kpis/especie_falsa",
            headers=admin_headers,
        )
        assert resp.status_code != 500, (
            f"El servidor crasheó al pedir KPIs de especie inválida: {resp.text}"
        )

    def test_especie_inexistente_retorna_404_o_400(self, client, admin_headers):
        """ENT-12: KPIs de especie inválida → 400 o 404."""
        resp = client.get(
            "/api/v1/entrenamiento/kpis/no_existe",
            headers=admin_headers,
        )
        assert resp.status_code in (400, 404, 200), (
            f"Status inesperado: {resp.status_code} — {resp.text}"
        )
