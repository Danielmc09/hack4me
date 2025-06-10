# app/main.py

from fastapi import FastAPI, HTTPException
from app.models.scan_request import ScanRequest
from app.factories.scanner_factory import ScannerFactory
import threading
from app.services.sqs_consumer import consumir_sqs

app = FastAPI()

@app.post("/scan")
def scan_domain(request: ScanRequest):
    """
    Recibe un correo electrónico, extrae el dominio y ejecuta el escaneo.
    """
    try:
        domain = request.domain
        scanner = ScannerFactory.create_scanner('nmap')
        result = scanner.scan_domain(domain)
        return {"domain": domain, "scan_result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
def start_background_consumer():
    """ 
    Inicia el consumidor de SQS en segundo plano.
    """
    pass
    #thread = threading.Thread(target=consumir_sqs)
    #thread.daemon = True
    #thread.start()
