import os
import json
import io
import pdfkit
import boto3
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from app.factories.logger_factory import LoggerFactory

logger = LoggerFactory.create_logger("report_service")

# Paths base
BASE_DIR     = os.path.abspath(os.getenv("PROJECT_ROOT", "."))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
REPORTS_DIR  = os.path.join(BASE_DIR, "reports")
PDF_FALLBACK = os.path.join(REPORTS_DIR, "pdf")
os.makedirs(PDF_FALLBACK, exist_ok=True)

# AWS config
AWS_REGION  = os.getenv("AWS_REGION", os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
TABLE_NAME  = os.getenv("DYNAMODB_TABLE_NAME", "companies")
BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "hacker4me")

# Inicializa sesión AWS
_session    = boto3.session.Session()
dynamodb    = _session.resource("dynamodb", region_name=AWS_REGION)
s3          = _session.client("s3", region_name=AWS_REGION)
try:
    dynamodb.Table(TABLE_NAME).load()
    s3.head_bucket(Bucket=BUCKET_NAME)
    aws_disponible = True
    logger.info("AWS OK: DynamoDB y S3 disponibles")
except Exception:
    aws_disponible = False
    logger.warning("Modo local: AWS no disponible")


def guardar_en_dynamodb(domain: str, email: str):
    ts   = datetime.utcnow().isoformat()
    item = {"domain": domain, "email": email, "timestamp": ts}

    if aws_disponible:
        try:
            dynamodb.Table(TABLE_NAME).put_item(Item=item)
            logger.info(f"Guardado en DynamoDB: {domain}/{email}")
            return
        except Exception as e:
            logger.error(f"DynamoDB falla, fallback local: {e}")

    # Fallback JSON local
    dir_ = os.path.join(REPORTS_DIR, domain)
    os.makedirs(dir_, exist_ok=True)
    path = os.path.join(dir_, f"{domain}_{email}_{ts}.json")
    with open(path, "w") as f:
        json.dump(item, f, indent=2)
    logger.info(f"Guardado JSON local: {path}")


def generar_pdf_en_memoria(domain: str, scan_result: dict, report_data: dict) -> bytes:
    """
    Genera un PDF en memoria y retorna los bytes.
    """
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    try:
        env      = Environment(loader=FileSystemLoader(TEMPLATE_DIR))
        template = env.get_template("oscp_report_template.html")

        html = template.render(
            student_email=report_data.get("email", ""),
            osid=f"HACK4ME-{ts}",
            exam_date=datetime.utcnow().date(),
            scan_result=scan_result,
            **report_data
        )

        pdf_bytes = pdfkit.from_string(html, False)
        logger.info("PDF generado en memoria")
        return pdf_bytes

    except Exception as e:
        logger.error(f"Error generando PDF en memoria: {e}")
        return b""


def subir_pdf_memoria_a_s3(domain: str, pdf_bytes: bytes) -> str:
    """
    Sube un PDF en memoria a S3 en reports/<domain>/ y retorna la URL firmada.
    """
    key = f"reports/{domain}/OSCP_{domain}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.pdf"
    try:
        s3.upload_fileobj(
            io.BytesIO(pdf_bytes),
            BUCKET_NAME,
            key,
            ExtraArgs={"ContentType": "application/pdf"}
        )
        url = s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": BUCKET_NAME, "Key": key},
            ExpiresIn=3600
        )
        logger.info("PDF subido a S3 y URL firmada generada")
        return url

    except Exception as e:
        logger.error(f"Error subiendo PDF a S3: {e}")
        return ""
