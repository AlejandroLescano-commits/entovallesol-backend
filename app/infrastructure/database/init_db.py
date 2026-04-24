from app.infrastructure.database.base import Base, engine
from app.domain.entities.usuario import Usuario                          # noqa
from app.domain.entities.refresh_token import RefreshToken               # noqa
from app.domain.entities.unidades import (                               # noqa
    UnidadMedidasitodroga, UnidadMedidaAvispas,
    UnidadDeMedidaGalleria, UnidadDeMedidaMoscas,
)
from app.domain.entities.lugares import (                                # noqa
    LugarLiberacionAvispitas, LugarLiberacionMoscas,
)
from app.domain.entities.produccion_sitotroga import ProduccionSitotroga        # noqa
from app.domain.entities.produccion_trichogramma import ProduccionTrichogramma  # noqa
from app.domain.entities.produccion_galleria import ProduccionGalleria          # noqa
from app.domain.entities.produccion_paratheresia import ProduccionParatheresia  # noqa
from app.domain.entities.notas_salida import (                          # noqa
    NotaSalidaSitodroga, DetalleNotaSalidaSitodroga,
    NotaSalidaAvispitas, DetalleNotaSalidaAvispitas,
    NotaSalidaMoscas, DetalleNotaSalidaMoscas,
    NotaSalidaGalleriamelonella, DetalleNotaSalidaGalleriamelonella,
)

def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    print("✅  Tablas creadas / verificadas en la base de datos.")