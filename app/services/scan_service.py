# app/services/scan_service.py

from datetime import datetime
from app.factories.nmap_creator   import NmapScannerCreator
from app.factories.gemini_creator import GeminiAnalyzerCreator
from app.services.report_service  import (
    guardar_en_dynamodb,
    generar_pdf_en_memoria,
    subir_pdf_memoria_a_s3,
    buscar_reporte_s3,
    s3,
    BUCKET_NAME,
)
from app.services.email_service   import render_scan_email, send_email
from app.services.exceptions      import ScanError, AnalysisError, ReportError, EmailError
from app.factories.logger_factory import LoggerFactory

logger = LoggerFactory.create_logger("scan_service")

async def perform_scan(domain: str, email: str) -> dict:
    try:

        # 0️⃣ ¿Ya existe un reporte reciente en S3?
        existing_key = buscar_reporte_s3(domain)
        if existing_key:
            logger.info(f"Reutilizando PDF existente en S3: {existing_key}")
            obj       = s3.get_object(Bucket=BUCKET_NAME, Key=existing_key)
            pdf_bytes = obj["Body"].read()
            filename  = existing_key.split("/")[-1]

            asunto      = f"Reporte Hack4Me: {domain}"
            cuerpo_html = render_scan_email(domain=domain)  # plantilla solo menciona "adjunto"
            if not send_email(
                destinatario=email,
                asunto=asunto,
                cuerpo_html=cuerpo_html,
                attachment=pdf_bytes,
                filename=filename
            ):
                raise EmailError(f"No se pudo enviar el email a {email}")
            logger.info("Email con reporte reutilizado enviado con éxito")
            return {
                "domain": domain,
                "email":  email,
                "reused": True,
            }

        # 1️⃣ Flujo completo (no había PDF reciente)
        scan_result = NmapScannerCreator().scan(domain)
        report_data = GeminiAnalyzerCreator().analyze(domain, scan_result)
        guardar_en_dynamodb(domain, email)

        # 4️⃣ Generar PDF en memoria
        pdf_bytes = generar_pdf_en_memoria(
            domain=domain,
            scan_result=scan_result,
            report_data=report_data,
        )
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename  = f"OSCP_{domain}_{timestamp}.pdf"

        # 5️⃣ Subir a S3 (ya no devuelve URL)
        key = subir_pdf_memoria_a_s3(domain, pdf_bytes)
        logger.info(f"PDF guardado en S3 con key: {key}")

        # 6️⃣ Enviar email CON el PDF adjunto
        asunto      = f"Reporte Hack4Me: {domain}"
        cuerpo_html = render_scan_email(domain=domain)
        if not send_email(
            destinatario=email,
            asunto=asunto,
            cuerpo_html=cuerpo_html,
            attachment=pdf_bytes,
            filename=filename
        ):
            raise EmailError(f"No se pudo enviar el email a {email}")

        return {
            "domain":          domain,
            "email":           email,
            "scan_result":     scan_result,
            "security_report": report_data,
            "reused":          False,
        }

    except (ScanError, AnalysisError, ReportError, EmailError):
        raise
    except Exception as e:
        raise ReportError(f"Fallo inesperado en perform_scan: {e}")
