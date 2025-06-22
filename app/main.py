# app/main.py
from fastapi import FastAPI, HTTPException
from app.models.scan_request import ScanRequest
from app.factories.nmap_creator      import NmapScannerCreator
from app.factories.gemini_creator    import GeminiAnalyzerCreator
from app.factories.logger_factory    import LoggerFactory
from app.services.report_service     import (
    guardar_en_dynamodb,
    generar_pdf_en_memoria,
    subir_pdf_memoria_a_s3,
)
from app.services.email_service      import send_email
from app.services.exceptions         import ScanError, AnalysisError, ReportError, EmailError

app    = FastAPI()
logger = LoggerFactory.create_logger("api")


@app.get("/")
def read_root():
    """
    Ruta raíz de la API.
    """
    logger.info("Acceso a la ruta raíz")
    return {"message": "Bienvenido a la API de Escaneo de Dominios"}


@app.post("/scan")
def scan_domain(req: ScanRequest):
    """
    Escanea un dominio, genera reportes y envía enlace al PDF por email.
    """
    try:
        domain, email = req.domain, req.email
        logger.info(f"Escaneo inicio: {domain} / {email}")

        # 1️⃣ Escaneo con Nmap
        scanner_creator = NmapScannerCreator()
        scan_result     = scanner_creator.scan(domain)

        # 2️⃣ Análisis con IA
        analyzer_creator = GeminiAnalyzerCreator()
        report_data      = analyzer_creator.analyze(domain, scan_result)

        # 3️⃣ Guardar metadatos en DynamoDB
        guardar_en_dynamodb(domain, email)

        # 4️⃣ Generar PDF en memoria
        pdf_bytes = generar_pdf_en_memoria(domain, report_data)

        pdf_url = None
        if pdf_bytes:
            # 5️⃣ Subir a S3 y obtener URL firmada
            pdf_url = subir_pdf_memoria_a_s3(domain, pdf_bytes)

            # 6️⃣ Enviar email al cliente
            asunto = f"Reporte Hack4Me: {domain}"
            cuerpo = (
                f"Hola,\n\n"
                f"Tu reporte de seguridad para **{domain}** ha finalizado exitosamente.\n\n"
                f"🔗 Puedes descargarlo aquí:\n{pdf_url}\n\n"
                f"© 2025 Hack4Me. Todos los derechos reservados."
            )
            send_email(email, asunto, cuerpo)

        return {
            "domain":          domain,
            "email":           email,
            "scan_result":     scan_result,
            "security_report": report_data,
            "pdf_url":         pdf_url,
        }

    except (ScanError, AnalysisError, ReportError, EmailError) as e:
        # Errores esperados de flujo
        logger.error(f"Error de proceso: {e}")
        status = 400 if isinstance(e, (ScanError, AnalysisError)) else 502 if isinstance(e, EmailError) else 500
        raise HTTPException(status_code=status, detail=str(e))

    except Exception as e:
        # Cualquier otro error imprevisto
        logger.exception("Error inesperado durante /scan")
        raise HTTPException(status_code=500, detail="Error interno del servidor")
