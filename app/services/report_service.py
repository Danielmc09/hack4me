# app/services/report_service.py

import os
import json
import io
import shutil
import pdfkit
import boto3
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from app.factories.logger_factory import LoggerFactory

logger = LoggerFactory.create_logger("report_service")

# ─── Configuración de rutas y AWS ────────────────────────────────────────────

BASE_DIR       = os.getenv("PROJECT_ROOT", os.getcwd())
TEMPLATE_DIR   = os.path.join(BASE_DIR, "templates")
REPORTS_DIR    = os.path.join(BASE_DIR, "reports")
PDF_FALLBACK   = os.path.join(REPORTS_DIR, "pdf")
os.makedirs(PDF_FALLBACK, exist_ok=True)

AWS_REGION     = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
TABLE_NAME     = os.getenv("DYNAMODB_TABLE_NAME", "companies")
BUCKET_NAME    = os.getenv("S3_BUCKET_NAME", "hacker4me")

# ─── Inicialización de clientes AWS ──────────────────────────────────────────

_session = boto3.session.Session(region_name=AWS_REGION)
_dynamodb = _session.resource("dynamodb")
_s3       = _session.client("s3")

try:
    _dynamodb.Table(TABLE_NAME).load()
    _s3.head_bucket(Bucket=BUCKET_NAME)
    aws_disponible = True
    logger.info("AWS disponible: DynamoDB y S3 conectados correctamente")
except Exception as e:
    aws_disponible = False
    logger.warning(f"AWS no disponible ({e}), se usará fallback local")

# ─── DynamoDB / Fallback JSON ────────────────────────────────────────────────

def guardar_en_dynamodb(domain: str, email: str) -> None:
    """
    Guarda un ítem con PK=domain y SK=email en DynamoDB.
    Si falla o AWS no está disponible, lo vuelca a JSON local en reports/<domain>/.
    """
    timestamp = datetime.utcnow().isoformat()
    item = {"domain": domain, "email": email, "timestamp": timestamp}

    if aws_disponible:
        try:
            _dynamodb.Table(TABLE_NAME).put_item(Item=item)
            logger.info(f"Guardado en DynamoDB: domain={domain}, email={email}")
            return
        except Exception as e:
            logger.error(f"Error en DynamoDB ({e}), usando fallback local")

    # Fallback: JSON local
    domain_dir = os.path.join(REPORTS_DIR, domain)
    os.makedirs(domain_dir, exist_ok=True)
    filename = f"{domain}_{email}_{timestamp.replace(':','-')}.json"
    filepath = os.path.join(domain_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(item, f, indent=2)
    logger.info(f"Reporte JSON guardado localmente: {filepath}")

# ─── Generación de PDF en memoria ────────────────────────────────────────────

def generar_pdf_en_memoria(domain: str, data: dict) -> bytes:
    """
    Renderiza la plantilla HTML y devuelve un PDF en bytes.
    """
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    env = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
    tpl = env.get_template("oscp_report_template.html")

    # Inyectamos tanto el scan_result como el resto de datos
    html = tpl.render(
        student_email=data.get("email", ""),
        osid=f"HACK4ME-{ts}",
        exam_date=datetime.utcnow().date(),
        scan_result=data.get("scan_result", {}),
        **data
    )

    try:
        pdf_bytes = pdfkit.from_string(html, False)
        logger.info(f"PDF generado en memoria para {domain}")
        return pdf_bytes
    except Exception as e:
        logger.error(f"Error generando PDF en memoria: {e}")
        return b""

# ─── Subida de PDF a S3 con URL firmada ──────────────────────────────────────

def subir_pdf_memoria_a_s3(domain: str, pdf_bytes: bytes) -> str:
    """
    Sube el PDF (bytes) a S3 en la carpeta reports/<domain>/ y retorna
    una URL prefirmada con 1h de expiración.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    key = f"reports/{domain}/OSCP_{domain}_{timestamp}.pdf"

    try:
        _s3.upload_fileobj(
            io.BytesIO(pdf_bytes),
            BUCKET_NAME,
            key,
            ExtraArgs={"ContentType": "application/pdf"}
        )
        url = _s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": key},
            ExpiresIn=3600
        )
        logger.info(f"PDF subido a S3 y URL firmada generada: {url}")
        return url
    except Exception as e:
        logger.error(f"Error subiendo PDF a S3: {e}")
        return ""

# ─── Fallback local de PDF ──────────────────────────────────────────────────

def guardar_pdf_fallback(domain: str, pdf_bytes: bytes) -> str:
    """
    Si falla la subida a S3, guarda el PDF bytes en reports/pdf/
    y retorna la ruta local.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"OSCP_{domain}_{timestamp}.pdf"
    path = os.path.join(PDF_FALLBACK, filename)

    try:
        with open(path, "wb") as f:
            f.write(pdf_bytes)
        logger.info(f"PDF guardado en fallback local: {path}")
        return path
    except Exception as e:
        logger.error(f"No se pudo guardar PDF localmente: {e}")
        return ""

