# app/main.py

from fastapi import FastAPI, HTTPException
from app.models.scan_request import ScanRequest
from app.factories.scanner_factory import ScannerFactory
from app.factories.logger_factory import LoggerFactory
from app.factories.ia_factory import IAFactory
import threading
from app.services.sqs_consumer import consumir_sqs
from app.services.report_service import guardar_en_dynamodb, generar_pdf_en_s3

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
    Recibe un dominio y ejecuta el escaneo.
    """
    try:
        domain = request.domain
        logger.info(f"Iniciando escaneo para el dominio: {domain}")
        
        # 1️⃣ Escanear con Nmap
        scanner = ScannerFactory.create_scanner('nmap')
        scan_result = scanner.scan_domain(domain)

        # 2️⃣ Analizar con Gemini
        analyzer = IAFactory.create_analyzer("gemini")
        report_data = analyzer.analyze_scan(domain, scan_result)

        # 3️⃣ Guardar JSON localmente
        guardar_en_dynamodb(domain, report_data)

        # 4️⃣ Generar PDF con la plantilla
        generar_pdf_en_s3(domain, report_data)
        
        logger.info(f"Escaneo completado para el dominio: {domain}")
        return {
            "domain": domain,
            "scan_result": scan_result,
            "security_report": report_data
        }
    except Exception as e:
        logger.error(f"Error durante el escaneo: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
def start_background_consumer():
    """ 
    Inicia el consumidor de SQS en segundo plano.
    """
    logger.info("Iniciando la aplicación")
    pass
    #thread = threading.Thread(target=consumir_sqs)
    #thread.daemon = True
    #thread.start()
