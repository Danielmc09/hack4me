# app/services/report_service.py
import os
import json
from datetime import datetime
import pdfkit
from app.factories.logger_factory import LoggerFactory
from jinja2 import Environment, FileSystemLoader


logger = LoggerFactory.create_logger("report_service")

# Importaciones AWS (comentadas temporalmente)
# import boto3

# Configuración desde variables de entorno
# AWS Config (comentado temporalmente)
# TABLE_NAME = 'nmap-scan-reports'  # Ajustar a tu tabla real
# BUCKET_NAME = 'nmap-scan-reports-bucket' 

# Configuración local
REPORTS_DIR = 'reports'
JSON_DIR = os.path.join(REPORTS_DIR, 'json')
PDF_DIR = os.path.join(REPORTS_DIR, 'pdf')

# Crear directorios si no existen
for directory in [REPORTS_DIR, JSON_DIR, PDF_DIR]:
    os.makedirs(directory, exist_ok=True)

# Inicialización AWS (comentada temporalmente)
# try:
#     dynamodb = boto3.resource('dynamodb')
#     s3 = boto3.client('s3')
# except Exception as e:
#     print(f"Error al inicializar servicios AWS: {e}")
#     dynamodb = None
#     s3 = None

# Función para AWS DynamoDB (comentada temporalmente)
# def guardar_en_dynamodb(domain, scan_result):
#     table = dynamodb.Table(TABLE_NAME)
#     item = {
#         'domain': domain,
#         'timestamp': datetime.utcnow().isoformat(),
#         'scan_result': scan_result
#     }
#     try:
#         table.put_item(Item=item)
#         print(f"Reporte guardado en DynamoDB para {domain}")
#     except Exception as e:
#         print(f"Error al guardar en DynamoDB: {e}")

# Función local que reemplaza a DynamoDB temporalmente
def guardar_en_dynamodb(domain, scan_result):
    timestamp = datetime.utcnow().isoformat()
    report_data = {
        'domain': domain,
        'timestamp': timestamp,
        'scan_result': scan_result
    }
    
    json_filename = f"{domain}_{timestamp}.json"
    json_path = os.path.join(JSON_DIR, json_filename)
    try:
        with open(json_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        logger.info(f"Reporte JSON guardado exitosamente: {json_path}")
    except Exception as e:
        logger.error(f"Error al guardar el reporte JSON para {domain}: {str(e)}")

# Función para AWS S3 (comentada temporalmente)
# def generar_pdf_en_s3(domain, scan_result):
#     html = f"""
#     <html>
#     <head><title>Reporte de Nmap</title></head>
#     <body>
#     <h1>Reporte de escaneo para: {domain}</h1>
#     <pre>{scan_result}</pre>
#     </body>
#     </html>
#     """
#     pdf_path = f"/tmp/{domain}_report.pdf"
#     try:
#         pdfkit.from_string(html, pdf_path)
#         s3.upload_file(pdf_path, BUCKET_NAME, f"{domain}_report.pdf")
#         print(f"PDF subido a S3: {domain}_report.pdf")
#     except Exception as e:
#         print(f"Error al generar o subir PDF: {e}")
#     finally:
#         if os.path.exists(pdf_path):
#             os.remove(pdf_path)

# Función local que reemplaza a S3 temporalmente
def generar_pdf_en_s3(domain, data):
    logger.info(f"Iniciando generación de PDF para: {domain}")
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    try:
        TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), '..', '..', 'templates')
        TEMPLATES_DIR = os.path.abspath(TEMPLATES_DIR)
        env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
        template = env.get_template('oscp_report_template.html')

        rendered_html = template.render(
            student_email="auditor@hack4me.com",
            osid=f"HACK4ME-{timestamp}",
            exam_date=datetime.utcnow().date(),
            summary=data.get("summary", "No summary available."),
            table_of_contents=data.get("table_of_contents", []),
            objective=data.get("objective", ""),
            requirements=data.get("requirements", []),
            high_level_summary=data.get("high_level_summary", ""),
            recommendations=data.get("recommendations", []),
            methodology=data.get("methodology", []),
            information_gathering=data.get("information_gathering", ""),
            service_enumeration=data.get("service_enumeration", []),
            penetration=data.get("penetration", []),
            maintaining_access=data.get("maintaining_access", ""),
            house_cleaning=data.get("house_cleaning", ""),
            additional_notes=data.get("additional_notes", "")
        )

        pdf_filename = f"OSCP_{domain}_{timestamp}.pdf"
        pdf_path = os.path.join(PDF_DIR, pdf_filename)

        pdfkit.from_string(rendered_html, pdf_path)
        logger.info(f"PDF generado exitosamente: {pdf_path}")

    except Exception as e:
        logger.error(f"Error al generar PDF para {domain}: {str(e)}")
