"""
test_produccion_funcional.py – Pruebas Funcionales del módulo de Producción Biológica
EntoValleSOL Backend

Casos cubiertos:
  CP-01 – POST /produccion/sitotroga → HTTP 201 con campos correctos
  CP-02 – GET  /produccion/sitotroga con filtros de fecha + exclusión de anulados
  CP-03 – POST /produccion/notas/sitodroga tipo T.exiguum → crea trichogramma automático
  CP-04 – POST /produccion/notas/sitodroga con cantidad ≤ 0 → HTTP 422
  CP-05 – DELETE /produccion/sitotroga/{id} → soft-delete; 404 en doble anulación
  CP-06 – POST /produccion/notas/galleria tipo Paratheresia → crea paratheresia con ratio
  CP-07 – POST /produccion/notas/avispitas tipo Liberacion con id_lugarliberacion
  CP-08 – Endpoints protegidos rechazan requests sin token / token expirado

Ejecutar:
  pytest tests/integration/test_produccion_funcional.py -v
  pytest tests/integration/test_produccion_funcional.py -v -k "CP01"
"""
import pytest
from datetime import date
from fastapi.testclient import TestClient

# ─── Imports del proyecto ─────────────────────────────────────────────────────
from app.main import app
from app.infrastructure.database.session import get_db, SessionLocal
from app.domain.entities.usuario import Usuario
from app.core.security import hash_password

# ─── Credenciales del usuario de prueba ───────────────────────────────────────
TEST_EMAIL    = "test@entovallesol.com"
TEST_PASSWORD = "Test1234!"


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module", autouse=True)
def seed_test_user():
    """
    Crea el usuario de prueba en Supabase si no existe.
    Se ejecuta una sola vez por módulo y NO elimina el usuario al final
    (para no afectar la BD de producción).
    """
    db = SessionLocal()
    try:
        existe = db.query(Usuario).filter(Usuario.email == TEST_EMAIL).first()
        if not existe:
            usuario = Usuario(
                nombre="Usuario Test Pytest",
                email=TEST_EMAIL,
                password_hash=hash_password(TEST_PASSWORD),
                rol="admin",
                activo=True,
            )
            db.add(usuario)
            db.commit()
            print(f"\n✓ Usuario de prueba creado: {TEST_EMAIL}")
        else:
            print(f"\n✓ Usuario de prueba ya existe: {TEST_EMAIL}")
    finally:
        db.close()


@pytest.fixture
def client():
    """TestClient usando la BD real de Supabase (sin override)."""
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture
def auth_headers(client):
    """Obtiene un token JWT válido haciendo login con el usuario de prueba."""
    response = client.post(
        "/api/v1/auth/login",
        json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
    )
    assert response.status_code == 200, (
        f"Login falló ({response.status_code}): {response.text}\n"
        f"→ Verifica que '{TEST_EMAIL}' exista en Supabase con activo=True."
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ═══════════════════════════════════════════════════════════════════════════════
# CP-01 – Registro de Producción Sitotroga
# ═══════════════════════════════════════════════════════════════════════════════

class TestCP01RegistroSitotroga:
    """CP-01: POST /produccion/sitotroga crea el registro correctamente."""

    def test_http_201_y_campos_correctos(self, client, auth_headers):
        """CP-01: Registro válido devuelve HTTP 201 con todos los campos."""
        payload = {"fecha": "2025-05-20", "id_unidad": 1, "cantidad": 500.0}

        response = client.post("/api/v1/produccion/sitotroga", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["fecha"] == "2025-05-20"
        assert data["cantidad"] == pytest.approx(500.0)
        assert data["activo"] is True
        assert data["id"] is not None
        assert data["registrado_por"] is not None

    def test_id_asignado_es_entero_positivo(self, client, auth_headers):
        """CP-01: El id retornado debe ser un entero positivo."""
        payload = {"fecha": "2025-05-21", "cantidad": 300.0}
        response = client.post("/api/v1/produccion/sitotroga", json=payload, headers=auth_headers)

        assert response.status_code == 201
        assert isinstance(response.json()["id"], int)
        assert response.json()["id"] > 0

    def test_sin_autenticacion_retorna_401(self, client):
        """CP-01 (seguridad): Sin token debe retornar 401 o 403."""
        payload = {"fecha": "2025-05-20", "cantidad": 100.0}
        response = client.post("/api/v1/produccion/sitotroga", json=payload)

        assert response.status_code in (401, 403)


# ═══════════════════════════════════════════════════════════════════════════════
# CP-02 – Listado Sitotroga con filtros de fecha
# ═══════════════════════════════════════════════════════════════════════════════

class TestCP02ListadoSitotroga:
    """CP-02: GET /produccion/sitotroga filtra por rango de fechas y excluye anulados."""

    @pytest.fixture(autouse=True)
    def seed_data(self, client, auth_headers):
        """Inserta 3 registros activos con fechas distintas."""
        for fecha, cantidad in [("2025-01-10", 100), ("2025-03-15", 200), ("2025-05-20", 300)]:
            client.post(
                "/api/v1/produccion/sitotroga",
                json={"fecha": fecha, "cantidad": cantidad},
                headers=auth_headers,
            )

    def test_filtrar_por_rango_de_fechas(self, client, auth_headers):
        """CP-02: Solo retorna registros dentro del rango fecha_inicio–fecha_fin."""
        response = client.get(
            "/api/v1/produccion/sitotroga",
            params={"fecha_inicio": "2025-03-01", "fecha_fin": "2025-05-31"},
            headers=auth_headers,
        )

        assert response.status_code == 200
        records = response.json()
        fechas = [r["fecha"] for r in records]
        assert all("2025-03-01" <= f <= "2025-05-31" for f in fechas)

    def test_sin_filtros_retorna_todos_los_activos(self, client, auth_headers):
        """CP-02: Sin parámetros retorna todos los registros activos."""
        response = client.get("/api/v1/produccion/sitotroga", headers=auth_headers)

        assert response.status_code == 200
        assert len(response.json()) >= 3

    def test_anulados_no_aparecen_en_listado(self, client, auth_headers):
        """CP-02: Un registro anulado no debe aparecer en el listado."""
        create_resp = client.post(
            "/api/v1/produccion/sitotroga",
            json={"fecha": "2025-04-01", "cantidad": 50.0},
            headers=auth_headers,
        )
        record_id = create_resp.json()["id"]
        client.delete(f"/api/v1/produccion/sitotroga/{record_id}", headers=auth_headers)

        list_resp = client.get("/api/v1/produccion/sitotroga", headers=auth_headers)
        ids_en_lista = [r["id"] for r in list_resp.json()]
        assert record_id not in ids_en_lista


# ═══════════════════════════════════════════════════════════════════════════════
# CP-03 – Nota Sitodroga tipo T.exiguum → crea Trichogramma automático
# ═══════════════════════════════════════════════════════════════════════════════

class TestCP03NotaSitodrogaTExiguum:
    """CP-03: Nota T.exiguum genera automáticamente un registro en produccion_trichogramma."""

    def test_crea_trichogramma_con_factor(self, client, auth_headers):
        """CP-03: cantidad_trichogramma = cantidad_nota × factor."""
        payload = {
            "tiposalida": "T.exiguum",
            "fecha": "2025-05-20",
            "cantidad": 1000.0,
            "factor": 1.5,
            "id_unidad": 1,
        }
        nota_resp = client.post("/api/v1/produccion/notas/sitodroga", json=payload, headers=auth_headers)
        assert nota_resp.status_code == 201
        nota_id = nota_resp.json()["id"]

        trich_resp = client.get("/api/v1/produccion/trichogramma", headers=auth_headers)
        assert trich_resp.status_code == 200
        trich_records = trich_resp.json()
        vinculado = next((r for r in trich_records if r.get("nota_origen_id") == nota_id), None)

        assert vinculado is not None
        assert vinculado["cantidad"] == pytest.approx(1500.0)

    def test_nota_tipo_ventas_no_crea_trichogramma(self, client, auth_headers):
        """CP-03 (negativo): Tipo Ventas NO debe generar trichogramma automático."""
        before = client.get("/api/v1/produccion/trichogramma", headers=auth_headers).json()
        count_before = len(before)

        client.post(
            "/api/v1/produccion/notas/sitodroga",
            json={"tiposalida": "Ventas", "fecha": "2025-05-20", "cantidad": 200.0},
            headers=auth_headers,
        )

        after = client.get("/api/v1/produccion/trichogramma", headers=auth_headers).json()
        assert len(after) == count_before


# ═══════════════════════════════════════════════════════════════════════════════
# CP-04 – Validación cantidad ≤ 0 en Notas de Salida Sitodroga
# ═══════════════════════════════════════════════════════════════════════════════

class TestCP04ValidacionCantidad:
    """CP-04: Cantidad ≤ 0 debe retornar HTTP 422 (Unprocessable Entity)."""

    def test_cantidad_cero_retorna_422(self, client, auth_headers):
        """CP-04: cantidad=0 debe rechazarse con HTTP 422."""
        response = client.post(
            "/api/v1/produccion/notas/sitodroga",
            json={"tiposalida": "T.exiguum", "fecha": "2025-05-20", "cantidad": 0},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_cantidad_negativa_retorna_422(self, client, auth_headers):
        """CP-04: cantidad negativa debe rechazarse con HTTP 422."""
        response = client.post(
            "/api/v1/produccion/notas/sitodroga",
            json={"tiposalida": "Infestacion", "fecha": "2025-05-20", "cantidad": -100},
            headers=auth_headers,
        )
        assert response.status_code == 422

    def test_cantidad_positiva_retorna_201(self, client, auth_headers):
        """CP-04 (positivo): cantidad válida debe aceptarse con HTTP 201."""
        response = client.post(
            "/api/v1/produccion/notas/sitodroga",
            json={"tiposalida": "Ventas", "fecha": "2025-05-20", "cantidad": 0.01},
            headers=auth_headers,
        )
        assert response.status_code == 201


# ═══════════════════════════════════════════════════════════════════════════════
# CP-05 – Anulación (soft-delete) de Producción Galleria
# ═══════════════════════════════════════════════════════════════════════════════

class TestCP05AnulacionGalleria:
    """CP-05: DELETE /produccion/galleria/{id} realiza soft-delete."""

    def test_anulacion_exitosa_retorna_200_con_activo_false(self, client, auth_headers):
        """CP-05: Anulación devuelve HTTP 200 y activo=false."""
        create_resp = client.post(
            "/api/v1/produccion/galleria",
            json={"fecha": "2025-05-20", "cantidad": 150.0},
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        record_id = create_resp.json()["id"]

        delete_resp = client.delete(f"/api/v1/produccion/galleria/{record_id}", headers=auth_headers)

        assert delete_resp.status_code == 200
        data = delete_resp.json()
        assert data["activo"] is False
        assert data["anulado_por"] is not None
        assert data["anulado_en"] is not None

    def test_anulado_no_aparece_en_listado(self, client, auth_headers):
        """CP-05: Registro anulado no debe retornarse en el listado."""
        create_resp = client.post(
            "/api/v1/produccion/galleria",
            json={"fecha": "2025-05-20", "cantidad": 80.0},
            headers=auth_headers,
        )
        record_id = create_resp.json()["id"]
        client.delete(f"/api/v1/produccion/galleria/{record_id}", headers=auth_headers)

        list_resp = client.get("/api/v1/produccion/galleria", headers=auth_headers)
        ids = [r["id"] for r in list_resp.json()]
        assert record_id not in ids

    def test_doble_anulacion_retorna_404(self, client, auth_headers):
        """CP-05: Segunda anulación del mismo registro debe retornar HTTP 404."""
        create_resp = client.post(
            "/api/v1/produccion/galleria",
            json={"fecha": "2025-05-20", "cantidad": 50.0},
            headers=auth_headers,
        )
        record_id = create_resp.json()["id"]

        client.delete(f"/api/v1/produccion/galleria/{record_id}", headers=auth_headers)
        second_delete = client.delete(f"/api/v1/produccion/galleria/{record_id}", headers=auth_headers)

        assert second_delete.status_code == 404

    def test_anular_id_inexistente_retorna_404(self, client, auth_headers):
        """CP-05: id que no existe debe retornar HTTP 404."""
        response = client.delete("/api/v1/produccion/galleria/99999", headers=auth_headers)
        assert response.status_code == 404


# ═══════════════════════════════════════════════════════════════════════════════
# CP-06 – Nota Galleria tipo Paratheresia → crea Paratheresia con ratio
# ═══════════════════════════════════════════════════════════════════════════════

class TestCP06NotaGalleriaParatheresia:
    """CP-06: Nota Galleria tipo Paratheresia genera paratheresia automático con ratio."""

    def test_crea_paratheresia_con_ratio(self, client, auth_headers):
        """CP-06: cantidad_paratheresia = cantidad_nota × ratio."""
        payload = {
            "tiposalida": "Paratheresia",
            "fecha": "2025-05-20",
            "cantidad": 200.0,
            "ratio": 0.8,
            "id_unidad": 1,
        }
        nota_resp = client.post("/api/v1/produccion/notas/galleria", json=payload, headers=auth_headers)
        assert nota_resp.status_code == 201
        nota_id = nota_resp.json()["id"]

        paratheresia_resp = client.get("/api/v1/produccion/paratheresia", headers=auth_headers)
        paratheresia_records = paratheresia_resp.json()
        vinculado = next((r for r in paratheresia_records if r.get("nota_origen_id") == nota_id), None)

        assert vinculado is not None
        assert vinculado["cantidad"] == pytest.approx(160.0)

    def test_nota_tipo_instalacion_no_crea_paratheresia(self, client, auth_headers):
        """CP-06 (negativo): Tipo Instalacion NO debe generar paratheresia."""
        before = client.get("/api/v1/produccion/paratheresia", headers=auth_headers).json()
        count_before = len(before)

        client.post(
            "/api/v1/produccion/notas/galleria",
            json={"tiposalida": "Instalacion", "fecha": "2025-05-20", "cantidad": 100.0},
            headers=auth_headers,
        )

        after = client.get("/api/v1/produccion/paratheresia", headers=auth_headers).json()
        assert len(after) == count_before


# ═══════════════════════════════════════════════════════════════════════════════
# CP-07 – Nota Avispitas tipo Liberacion con lugar de liberación
# ═══════════════════════════════════════════════════════════════════════════════

class TestCP07NotaAvispitasLiberacion:
    """CP-07: Nota de avispitas tipo Liberacion guarda id_lugarliberacion."""

    def test_registro_con_lugar_liberacion(self, client, auth_headers):
        """CP-07: id_lugarliberacion debe persistirse en la nota."""
        payload = {
            "tiposalida": "Liberacion",
            "fecha": "2025-05-20",
            "cantidad": 5000.0,
            "id_lugarliberacion": 1,
        }
        response = client.post("/api/v1/produccion/notas/avispitas", json=payload, headers=auth_headers)

        assert response.status_code == 201
        data = response.json()
        assert data["tiposalida"] == "Liberacion"
        assert data["id_lugarliberacion"] == 1
        assert data["cantidad"] == pytest.approx(5000.0)
        assert data["activo"] is True

    def test_registro_sin_lugar_liberacion_es_opcional(self, client, auth_headers):
        """CP-07: id_lugarliberacion es opcional y puede ser null."""
        payload = {"tiposalida": "Parasitacion", "fecha": "2025-05-20", "cantidad": 1000.0}
        response = client.post("/api/v1/produccion/notas/avispitas", json=payload, headers=auth_headers)

        assert response.status_code == 201
        assert response.json()["id_lugarliberacion"] is None


# ═══════════════════════════════════════════════════════════════════════════════
# CP-08 – Autenticación JWT
# ═══════════════════════════════════════════════════════════════════════════════

class TestCP08Autenticacion:
    """CP-08: Todos los endpoints protegidos rechazan requests sin token o con token expirado."""

    ENDPOINTS_GET = [
        "/api/v1/produccion/sitotroga",
        "/api/v1/produccion/trichogramma",
        "/api/v1/produccion/galleria",
        "/api/v1/produccion/paratheresia",
        "/api/v1/produccion/notas/sitodroga",
        "/api/v1/produccion/notas/avispitas",
        "/api/v1/produccion/notas/moscas",
        "/api/v1/produccion/notas/galleria",
    ]

    @pytest.mark.parametrize("endpoint", ENDPOINTS_GET)
    def test_sin_token_retorna_401_o_403(self, client, endpoint):
        """CP-08: GET sin Authorization header → 401 o 403."""
        response = client.get(endpoint)
        assert response.status_code in (401, 403), (
            f"Endpoint {endpoint} no está protegido (retornó {response.status_code})"
        )

    def test_token_expirado_retorna_401(self, client):
        """CP-08: Token expirado/inválido debe retornar 401 o 403."""
        fake_expired_token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiIxMjM0NTY3ODkwIiwiZXhwIjoxfQ."
            "invalid_signature"
        )
        response = client.get(
            "/api/v1/produccion/sitotroga",
            headers={"Authorization": f"Bearer {fake_expired_token}"},
        )
        assert response.status_code in (401, 403)

    def test_post_sin_token_retorna_401(self, client):
        """CP-08: POST sin token debe retornar 401 o 403."""
        response = client.post(
            "/api/v1/produccion/sitotroga",
            json={"fecha": "2025-05-20", "cantidad": 100.0},
        )
        assert response.status_code in (401, 403)

    def test_delete_sin_token_retorna_401(self, client):
        """CP-08: DELETE sin token debe retornar 401 o 403."""
        response = client.delete("/api/v1/produccion/sitotroga/1")
        assert response.status_code in (401, 403)

    def test_con_token_valido_retorna_200(self, client, auth_headers):
        """CP-08 (positivo): Token válido permite acceder al endpoint."""
        response = client.get("/api/v1/produccion/sitotroga", headers=auth_headers)
        assert response.status_code == 200
