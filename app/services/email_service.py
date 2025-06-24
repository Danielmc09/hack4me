# app/services/email_service.py

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader, select_autoescape
from app.factories.logger_factory import LoggerFactory

logger = LoggerFactory.create_logger("email_service")

# Configuramos Jinja
BASE_DIR     = os.path.abspath(os.getenv("PROJECT_ROOT", "."))
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(["html", "xml"])
)

def render_scan_email(domain: str, pdf_url: str) -> str:
    """
    Renderiza HTML con la plantilla scan_complete.html.
    """
    try:
        tpl = env.get_template("scan_complete.html")
        return tpl.render(domain=domain, pdf_url=pdf_url)
    except Exception as e:
        logger.error(f"Error al renderizar plantilla de email: {e}")
        raise

def send_email(destinatario: str, asunto: str, cuerpo_html: str, remitente: str = None) -> bool:
    """
    Envía un correo HTML usando SMTP.
    """
    remitente  = remitente or os.getenv("EMAIL_FROM", "noreply@hack4me.com")
    smtp_host  = os.getenv("SMTP_HOST", "localhost")
    smtp_port  = int(os.getenv("SMTP_PORT", 25))
    smtp_user  = os.getenv("SMTP_USER")
    smtp_pass  = os.getenv("SMTP_PASS")

    msg = MIMEMultipart("alternative")
    msg["From"]    = remitente
    msg["To"]      = destinatario
    msg["Subject"] = asunto

    msg.attach(MIMEText(cuerpo_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user and smtp_pass:
                server.starttls()
                server.login(smtp_user, smtp_pass)
            server.sendmail(remitente, destinatario, msg.as_string())
        logger.info(f"Email enviado a {destinatario}")
        return True

    except smtplib.SMTPException as e:
        logger.error(f"SMTP error enviando correo a {destinatario}: {e}")
        return False

    except Exception as e:
        logger.error(f"Error inesperado en send_email: {e}")
        return False
