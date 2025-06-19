# app/services/report_service.py
import os
import json
from datetime import datetime
import pdfkit
from app.factories.logger_factory import LoggerFactory
from jinja2 import Environment, FileSystemLoader
import boto3

logger = LoggerFactory.create_logger("report_service")

# Configuración AWS desde variables de entorno
tables_env = {
    'AWS_REGION': os.getenv('AWS_REGION', os.getenv('AWS_DEFAULT_REGION', 'us-east-1')),
    'TABLE_NAME': os.getenv('DYNAMODB_TABLE_NAME', 'companies'),
    'BUCKET_NAME': os.getenv('S3_BUCKET_NAME', 'hacker4me')
}
AWS_REGION = tables_env['AWS_REGION']
TABLE_NAME = tables_env['TABLE_NAME']
BUCKET_NAME = tables_env['BUCKET_NAME']

# Configuración local
def ensure_local_dir(path):
    os.makedirs(path, exist_ok=True)

BASE_REPORTS_DIR = 'reports'
ensure_local_dir(BASE_REPORTS_DIR)

# Inicializar servicios AWS def
def inicializar_servicios_aws():
    """Inicializa los servicios AWS con credenciales del entorno."""
    if not (os.getenv('AWS_ACCESS_KEY_ID') and os.getenv('AWS_SECRET_ACCESS_KEY')):
        logger.warning("Credenciales AWS no configuradas. Usando almacenamiento local.")
        return None, None

    try:
        # boto3 cargará automáticamente AWS_SESSION_TOKEN
        dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
        s3 = boto3.client('s3', region_name=AWS_REGION)

        # Validar DynamoDB
        try:
            table = dynamodb.Table(TABLE_NAME)
            table.load()
            logger.info(f"Conexión a DynamoDB validada: {TABLE_NAME}")
        except Exception as e:
            logger.warning(f"No se pudo acceder a la tabla DynamoDB {TABLE_NAME}: {e}")

        # Validar S3
        try:
            s3.head_bucket(Bucket=BUCKET_NAME)
            logger.info(f"Conexión a S3 validada: {BUCKET_NAME}")
        except Exception as e:
            logger.warning(f"No se pudo acceder al bucket S3 {BUCKET_NAME}: {e}")

        logger.info("Servicios AWS inicializados correctamente")
        return dynamodb, s3

    except Exception as e:
        logger.error(f"Error al inicializar servicios AWS: {e}")
        return None, None

# Ejecutar inicialización
dynamodb, s3 = inicializar_servicios_aws()
aws_disponible = dynamodb is not None and s3 is not None


def guardar_en_dynamodb(domain, email):
    """
    Guarda el resultado en DynamoDB usando:
      - domain  como clave de partición (PK)
      - email   como clave de ordenación (SK)
    O, si falla, lo vuelca a un JSON local en reports/<domain>/
    """
    timestamp = datetime.utcnow().isoformat()

    if aws_disponible:
        try:
            table = dynamodb.Table(TABLE_NAME)
            item = {
                'domain': domain,      # PK – debe llamarse exactamente 'domain'
                'email': email,        # SK – debe llamarse exactamente 'email'
                'timestamp': timestamp # atributo adicional
            }
            table.put_item(Item=item)
            logger.info(f"Guardado en DynamoDB: domain={domain}, email={email}")
            return
        except Exception as e:
            logger.error(f"Error al guardar en DynamoDB: {e}. Fallback local.")

    # Fallback local JSON
    domain_dir = os.path.join(BASE_REPORTS_DIR, domain)
    ensure_local_dir(domain_dir)
    json_filename = f"{domain}_{email}_{timestamp.replace(':','-')}.json"
    json_path = os.path.join(domain_dir, json_filename)
    data = {'domain': domain, 'email': email, 'timestamp': timestamp}
    try:
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Reporte JSON local: {json_path}")
    except Exception as e:
        logger.error(f"Error al guardar JSON local: {e}")



def generar_pdf_en_s3(domain, data):
    """Genera PDF y sube a S3/reports/<domain>/ o guarda localmente."""
    logger.info(f"Generando PDF para: {domain}")
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    try:
        # Render HTML con Jinja2
        templates_dir = os.path.abspath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'templates')
        )
        env = Environment(loader=FileSystemLoader(templates_dir))
        template = env.get_template('oscp_report_template.html')
        rendered = template.render(
            student_email="auditor@hack4me.com",
            osid=f"HACK4ME-{timestamp}",
            exam_date=datetime.utcnow().date(),
            **data
        )
        filename = f"OSCP_{domain}_{timestamp}.pdf"

        if aws_disponible:
            # Subida a S3 en reports/<domain>/
            tmp = f"/tmp/{filename}"
            pdfkit.from_string(rendered, tmp)
            s3_key = f"reports/{domain}/{filename}"
            s3.upload_file(tmp, BUCKET_NAME, s3_key)
            logger.info(f"PDF S3: s3://{BUCKET_NAME}/{s3_key}")
            os.remove(tmp)
            return

        # Fallback local
        domain_dir = os.path.join(BASE_REPORTS_DIR, domain)
        ensure_local_dir(domain_dir)
        local_pdf = os.path.join(domain_dir, filename)
        pdfkit.from_string(rendered, local_pdf)
        logger.info(f"PDF local: {local_pdf}")

    except Exception as e:
        logger.error(f"Error generando PDF: {e}")
