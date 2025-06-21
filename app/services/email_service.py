import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import os

def enviar_correo(destinatario, asunto, cuerpo, remitente=None):
    """
    Envía un correo electrónico simple usando SMTP.
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
        return True
    except Exception as e:
        print(f"Error enviando correo: {e}")
        return False
