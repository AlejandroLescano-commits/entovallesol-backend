from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.infrastructure.database.init_db import init_db

# Crea las tablas al iniciar (reemplaza Alembic)
init_db()

app = FastAPI(
    title="EntomológicaValleSol API",
    description="Sistema de Control y Registro de Producción Entomológica — ValleSol S.A.C.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok", "app": settings.APP_NAME}
