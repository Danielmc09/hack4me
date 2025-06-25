# app/routers/scan.py
from fastapi import APIRouter, HTTPException, status
from pydantic import ValidationError
from app.models.scan_request import ScanRequest
from app.services.scan_service import perform_scan
from app.factories.logger_factory import LoggerFactory

router = APIRouter()
logger = LoggerFactory.create_logger("scan_router")

@router.post(
    "/",
    summary="Ejecuta un escaneo de dominio y entrega resultados",
    response_model=dict,
    status_code=status.HTTP_200_OK
)
async def scan_endpoint(request: ScanRequest):
    """
    Recibe dominio y email, orquesta el escaneo completo y devuelve:
      - resultados de Nmap
      - informe de seguridad
      - URL firmada del PDF (si aplica)
    """
    try:
        result = await perform_scan(request.domain, request.email)
        return result

    except ValidationError as ve:
        logger.error(f"Error de validación en request: {ve}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=ve.errors()
        )

    except HTTPException:
        # Los errores de negocio ya vienen lanzados desde perform_scan
        raise

    except Exception as e:
        logger.exception("Fallo inesperado en scan_endpoint")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar el escaneo"
        )
