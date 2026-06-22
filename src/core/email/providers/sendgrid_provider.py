import sendgrid
from sendgrid.helpers.mail import Content, Email, Mail, To

from src.core.config import settings
from src.core.email.providers.base import EmailMessage, EmailProvider


class SendGridProvider(EmailProvider):
    def __init__(self):
        self.client = sendgrid.SendGridAPIClient(api_key=settings.SENDGRID_API_KEY)

    async def send(self, message: EmailMessage) -> bool:
        try:
            from_email = Email(message.from_email or settings.SENDGRID_FROM_EMAIL)
            to_email = To(message.to)
            subject = message.subject
            content = Content("text/html", message.html_body)

            mail = Mail(from_email, to_email, subject, content)

            if message.text_body:
                mail.add_content(Content("text/plain", message.text_body))

            response = self.client.send(mail)
            return 200 <= response.status_code < 300
        except Exception as e:
            print(f"SendGrid error: {e}")
            return False

    def is_configured(self) -> bool:
        return bool(settings.SENDGRID_API_KEY)
