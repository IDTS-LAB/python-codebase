import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from src.core.config import settings
from src.core.email.providers.base import EmailMessage, EmailProvider


class SMTPProvider(EmailProvider):
    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.use_tls = settings.SMTP_USE_TLS

    async def send(self, message: EmailMessage) -> bool:
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = message.subject
            msg["From"] = (
                f"{message.from_name or ''} <{message.from_email or settings.SMTP_FROM_EMAIL}>".strip()
            )
            msg["To"] = message.to

            if message.text_body:
                msg.attach(MIMEText(message.text_body, "plain"))
            msg.attach(MIMEText(message.html_body, "html"))

            with smtplib.SMTP(self.host, self.port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f"SMTP error: {e}")
            return False

    def is_configured(self) -> bool:
        return bool(self.host and self.port)
