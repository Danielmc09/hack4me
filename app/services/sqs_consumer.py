# app/services/sqs_consumer.py

import boto3
import json
import time
import os
from app.factories.scanner_factory import ScannerFactory
from app.services.report_service import guardar_en_dynamodb, generar_pdf_en_s3

QUEUE_URL = os.getenv('SQS_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/tu-queue')

# Intentar crear el cliente de SQS
try:
    sqs = boto3.client('sqs')
    print("[INFO] Cliente SQS inicializado.")
except Exception as e:
    print(f"[ERROR] No se pudo inicializar el cliente SQS: {e}")
    sqs = None

def consumir_sqs():
    print("[INFO] Consumidor de SQS iniciado.")
    while True:
        try:
            if sqs is None:
                print("[WARNING] Cliente SQS no disponible. Modo simulación local.")
                time.sleep(10)
                continue

            response = sqs.receive_message(
                QueueUrl=QUEUE_URL,
                MaxNumberOfMessages=5,
                WaitTimeSeconds=20
            )
            messages = response.get('Messages', [])
            for message in messages:
                body = json.loads(message['Body'])
                domain = body.get('domain')
                if domain:
                    procesar_dominio(domain)
                    # Borrar mensaje de la cola
                    sqs.delete_message(
                        QueueUrl=QUEUE_URL,
                        ReceiptHandle=message['ReceiptHandle']
                    )
        except Exception as e:
            print(f"[ERROR] Al procesar SQS: {e}")
        time.sleep(5)

def procesar_dominio(domain):
    try:
        print(f"[INFO] Procesando dominio: {domain}")
        scanner = ScannerFactory.create_scanner('nmap')
        result = scanner.scan_domain(domain)
        guardar_en_dynamodb(domain, result)
        generar_pdf_en_s3(domain, result)
    except Exception as e:
        print(f"[ERROR] Al procesar dominio {domain}: {e}")
