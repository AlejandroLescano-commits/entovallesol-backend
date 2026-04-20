# entovallesol-backend

Backend del Sistema de Control y Registro de Producción Entomológica — **ValleSol S.A.C.**

## Stack
- **FastAPI** — framework REST
- **SQLAlchemy 2.0** — ORM
- **Alembic** — migraciones
- **PostgreSQL** — base de datos
- **Redis** — caché y sesiones
- **PyJWT / Passlib** — autenticación JWT

## Instalación
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env       # edita tus credenciales
alembic upgrade head
uvicorn app.main:app --reload
```

## Módulos principales
| Módulo | Descripción |
|--------|-------------|
| `auth` | Login, JWT, refresh token, roles |
| `usuarios` | CRUD de usuarios y permisos |
| `produccion` | Registro diario (Sitotroga, Trichogramma, Galleria, Paratheresia) |
| `distribucion` | Salidas a fincas y sectores |
| `inventario` | Saldos en tiempo real |
| `reportes` | Generación PDF y Excel |
| `insectos` | Catálogo de especies entomológicas |
| `configuracion` | Parámetros del sistema |
| `importacion` | Carga masiva desde Excel |
