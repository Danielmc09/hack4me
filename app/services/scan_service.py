# app/services/scan_service.py

from datetime import datetime
from app.factories.nmap_creator   import NmapScannerCreator
from app.factories.gemini_creator import GeminiAnalyzerCreator
from app.services.report_service  import (
    guardar_en_dynamodb,
    generar_pdf_en_memoria,
    subir_pdf_memoria_a_s3,
)
from app.services.email_service   import render_scan_email, send_email
from app.services.exceptions      import ScanError, AnalysisError, ReportError, EmailError

async def perform_scan(domain: str, email: str) -> dict:
    """
    Orquesta:
      1) Nmap
      2) IA
      3) DynamoDB
      4) PDF en memoria
      5) Subida a S3 + URL
      6) Email con HTML
    """
    try:
        # 1️⃣ Nmap
        scanner_creator = NmapScannerCreator()
        scan_result     = scanner_creator.scan(domain)

        # 2️⃣ IA
        analyzer_creator = GeminiAnalyzerCreator()
        report_data      = analyzer_creator.analyze(domain, scan_result)

        # 3️⃣ Guardar metadatos
        guardar_en_dynamodb(domain, email)

        # 4️⃣ Generar PDF en memoria
        pdf_bytes = generar_pdf_en_memoria(domain=domain, scan_result=scan_result, report_data=report_data)
        pdf_url   = None

        if pdf_bytes:
            # 5️⃣ Subir a S3
            pdf_url = subir_pdf_memoria_a_s3(domain, pdf_bytes)

            # 6️⃣ Enviar email HTML
            asunto      = f"Reporte Hack4Me: {domain}"
            cuerpo_html = render_scan_email(domain=domain, pdf_url=pdf_url)

            if not send_email(destinatario=email, asunto=asunto, cuerpo_html=cuerpo_html):
                raise EmailError(f"No se pudo enviar el email a {email}")

        return {
            "domain":          domain,
            "email":           email,
            "scan_result":     scan_result,
            "security_report": report_data,
            "pdf_url":         pdf_url,
        }

    except (ScanError, AnalysisError, ReportError, EmailError):
        # Propaga para el router o main
        raise

    except Exception as e:
        # Error inesperado durante el flujo
        raise ReportError(f"Fallo inesperado en perform_scan: {e}")
