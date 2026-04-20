from fastapi import APIRouter, Depends
from app.core.dependencies import require_admin

router = APIRouter()

@router.get("/")
def obtener_config(_=Depends(require_admin)):
    return {
        "especies": ["sitotroga", "trichogramma_exiguum", "trichogramma_pretiosum", "galleria", "paratheresia"],
        "fincas": ["San Ricardo A", "San Ricardo B", "Quemazón", "Trapiche", "2do Jirón", "Pabellón Alto", "Sacachique", "La Encantada"],
        "roles": ["admin", "supervisor", "operario"],
        "version": "1.0.0"
    }
