# app/main.py
from fastapi import FastAPI
from app.routers.scan import router as scan_router
from app.factories.logger_factory import LoggerFactory

app = FastAPI()
logger = LoggerFactory.create_logger("api")

# Registrar routers
app.include_router(scan_router, prefix="/scan", tags=["scan"])

@app.get("/")
async def read_root():
    """
    Ruta raíz de la API.
    """
    logger.info("Acceso a la ruta raíz")
    return {"message": "Bienvenido a la API de Escaneo de Dominios"}
