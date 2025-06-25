import json
import re
import boto3
from datetime import datetime, timedelta
from utils.domain_validator import is_valid_domain
import os

# SQS
sqs = boto3.client('sqs')
dynamo = boto3.client('dynamodb')
SQS_URL = os.getenv('SQS_URL')

# Datos quemados simulando la tabla DynamoDB
SIMULATED_DATA = {
    'scanme.nmap.org': {
        'timestamp': datetime.utcnow() - timedelta(hours=8),  # Simula un reporte hace 8 horas
        'emails': ['user1@example.com', 'user2@example.com']
    },
    'example.com': {
        'timestamp': datetime.utcnow() - timedelta(hours=15),  # Simula un reporte hace 15 horas
        'emails': ['admin@example.com']
    }
}

def lambda_handler(event, context):
    try:
        print("Evento recibido:", event)

        # 1️⃣ Extraer dominio del evento
        body = json.loads(event['body'])
        email = body.get('email')
        domain = email.split('@')[-1] if email else None
        if not domain:
            return response(400, {"error": "Domain is required."})

        # 2️⃣ Validar dominio con regex
        if not is_valid_domain(domain):
            return response(400, {"error": "Invalid domain format."})

        # 3️⃣ Simular búsqueda en DynamoDB (con datos quemados)
        last_report = SIMULATED_DATA.get(domain)
        if last_report:
            report_time = last_report['timestamp']
            emails_sent = last_report['emails']
            if datetime.utcnow() - report_time < timedelta(hours=12):
                return response(200, {
                    "status": "report_sent",
                    "last_report_time": report_time.isoformat(),
                    "emails_sent": emails_sent
                })
        company = dynamo.get_item(TableName='companies', Key={'domain': {'S': domain},'email': {'S': email}})
        if company.get('Item'):
            return response(200, {"status": "success"})

        # 4️⃣ Si no existe o es mayor a 12 horas, enviar a SQS
        sqs.send_message(
            QueueUrl=SQS_URL,
            MessageBody=json.dumps({"domain": domain, "email": email})
        )

        return response(200, {"status": "success"})

    except Exception as e:
        print(f"Error: {e}")
        return response(500, {"error": "Internal server error."})

def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body)
    }
