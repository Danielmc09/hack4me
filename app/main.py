# app/main.py
from fastapi import FastAPI, HTTPException
from app.models.scan_request import ScanRequest
from app.factories.scanner_factory import ScannerFactory
from app.factories.logger_factory import LoggerFactory
from app.factories.ia_factory import IAFactory
from app.services.report_service import guardar_en_dynamodb, generar_pdf_en_s3, generar_pdf_en_memoria, subir_pdf_memoria_a_s3
from app.services.email_service import enviar_correo

app = FastAPI()
logger = LoggerFactory.create_logger("api")

@app.get("/")
def read_root():
    """
    Ruta raíz de la API.
    """
    logger.info("Acceso a la ruta raíz")
    return {"message": "Bienvenido a la API de Escaneo de Dominios"}

@app.post("/scan")
def scan_domain(request: ScanRequest):
    """
    Recibe dominio y email, ejecuta el escaneo y genera reportes.
    """
    try:
        domain = request.domain
        email = request.email
        logger.info(f"Iniciando escaneo para el dominio: {domain} y email: {email}")
        
        # 1️⃣ Escanear con Nmap
        scanner = ScannerFactory.create_scanner('nmap')
        scan_result = scanner.scan_domain(domain)

        # 2️⃣ Analizar con IA (Gemini)
        analyzer = IAFactory.create_analyzer("gemini")
        report_data = analyzer.analyze_scan(domain, scan_result)

        # 3️⃣ Guardar info en DynamoDB (Dominio=PK, Email=SK)
        guardar_en_dynamodb(domain, email)

        # 4️⃣ Generar PDF en memoria
        pdf_bytes = generar_pdf_en_memoria(domain, report_data)
        pdf_url = None
        # 5️⃣ Subir PDF a S3 si se generó
        if pdf_bytes:
            pdf_url = subir_pdf_memoria_a_s3(domain, pdf_bytes)
            asunto = f"Reporte de Seguridad para {domain}"
            cuerpo = f"Adjunto el reporte de seguridad generado para el dominio {domain}.\n\nEnlace al PDF: {pdf_url if pdf_url else 'No disponible'}"
            enviar_correo(email, asunto, cuerpo)
        logger.info(f"Escaneo completado para el dominio: {domain}")
        return {
            "domain": domain,
            "email": email,
            "scan_result": scan_result,
            "security_report": report_data,
            "pdf_url": pdf_url
        }
    except Exception as e:
        logger.error(f"Error durante el escaneo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))