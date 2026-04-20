"""
Crea todas las tablas en la base de datos sin Alembic.
Ejecutar una vez al arrancar o llamar desde main.py.
"""
from app.infrastructure.database.base import Base, engine

# Importar TODOS los modelos para que Base los conozca
from app.domain.entities.usuario import Usuario          # noqa: F401
from app.domain.entities.refresh_token import RefreshToken  # noqa: F401
from app.domain.entities.produccion_sitotroga import ProduccionSitotroga  # noqa: F401
from app.domain.entities.produccion_trichogramma import ProduccionTrichogramma  # noqa: F401
from app.domain.entities.produccion_galleria import ProduccionGalleria  # noqa: F401
from app.domain.entities.produccion_paratheresia import ProduccionParatheresia  # noqa: F401
from app.domain.entities.finca import Finca              # noqa: F401


def init_db() -> None:
    """Crea tablas que no existen. Seguro de ejecutar múltiples veces."""
    Base.metadata.create_all(bind=engine)
    print("✅  Tablas creadas / verificadas en la base de datos.")
