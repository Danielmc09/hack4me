# app/services/email_service.py

import io
import os
import smtplib
from smtplib import SMTPException
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from app.services.exceptions import EmailError
from app.factories.logger_factory import LoggerFactory

logger = LoggerFactory.create_logger("email_service")

def send_email(destinatario: str, asunto: str, cuerpo: str, remitente: str = None) -> None:
    """
    Envía un correo electrónico simple usando SMTP.
    Lanza EmailError si ocurre cualquier fallo.
    """
    remitente = remitente or os.getenv('EMAIL_FROM', 'noreply@hack4me.com')
    smtp_host = os.getenv('SMTP_HOST', 'localhost')
    smtp_port = int(os.getenv('SMTP_PORT', 25))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')

    msg = MIMEMultipart()
    msg['From'] = formataddr(('Hack4Me', remitente))
    msg['To'] = destinatario
    msg['Subject'] = asunto
    msg.attach(MIMEText(cuerpo, 'plain'))

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user and smtp_pass:
                server.starttls()
                server.login(smtp_user, smtp_pass)
            server.sendmail(remitente, destinatario, msg.as_string())
        logger.info(f"Email enviado a {destinatario}")
    except SMTPException as e:
        logger.error(f"SMTP error enviando correo a {destinatario}: {e}")
        raise EmailError(f"No se pudo enviar el email: {e}")
    except Exception as e:
        logger.error(f"Error inesperado enviando correo a {destinatario}: {e}")
        raise EmailError(f"No se pudo enviar el email: {e}")
