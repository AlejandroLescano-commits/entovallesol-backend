from fastapi import APIRouter
from app.api.v1.endpoints import auth, usuarios, produccion, reportes, importacion, configuracion, prediccion

api_router = APIRouter()

api_router.include_router(auth.router,          prefix="/auth",          tags=["Autenticación"])
api_router.include_router(usuarios.router,      prefix="/usuarios",      tags=["Usuarios"])
api_router.include_router(produccion.router,    prefix="/produccion",    tags=["Producción"])
api_router.include_router(reportes.router,      prefix="/reportes",      tags=["Reportes"])
api_router.include_router(importacion.router,   prefix="/importacion",   tags=["Importación"])
api_router.include_router(configuracion.router, prefix="/configuracion", tags=["Configuración"])
api_router.include_router(prediccion.router,    prefix="/prediccion",    tags=["Predicción"])