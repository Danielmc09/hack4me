# app/services/sqs_consumer.py

import boto3
import json
import time
import os
from app.factories.logger_factory import LoggerFactory
from app.factories.scanner_factory import ScannerFactory
from app.services.report_service import guardar_en_dynamodb, generar_pdf_en_s3

logger = LoggerFactory.create_logger("sqs_consumer")

QUEUE_URL = os.getenv('SQS_URL', 'https://sqs.us-east-1.amazonaws.com/123456789012/tu-queue')

# Intentar crear el cliente de SQS
try:
    sqs = boto3.client('sqs')
    logger.info("Cliente SQS inicializado correctamente")
except Exception as e:
    logger.error(f"No se pudo inicializar el cliente SQS: {str(e)}")
    sqs = None

def consumir_sqs():
    logger.info("Consumidor de SQS iniciado")
    while True:
        try:
            if sqs is None:
                logger.warning("Cliente SQS no disponible. Modo simulación local")
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
                    logger.info(f"Mensaje recibido para procesar dominio: {domain}")
                    procesar_dominio(domain)
                    # Borrar mensaje de la cola
                    sqs.delete_message(
                        QueueUrl=QUEUE_URL,
                        ReceiptHandle=message['ReceiptHandle']
                    )
                    logger.debug(f"Mensaje procesado y eliminado de la cola para: {domain}")
        except Exception as e:
            logger.error(f"Error al procesar SQS: {str(e)}")
        time.sleep(5)

def procesar_dominio(domain):
    try:
        logger.info(f"Iniciando procesamiento para dominio: {domain}")
        scanner = ScannerFactory.create_scanner('nmap')
        result = scanner.scan_domain(domain)
        guardar_en_dynamodb(domain, result)
        generar_pdf_en_s3(domain, result)
        logger.info(f"Procesamiento completado para dominio: {domain}")
    except Exception as e:
        logger.error(f"Error al procesar dominio {domain}: {str(e)}")
