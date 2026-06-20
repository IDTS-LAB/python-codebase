from src.core.config import settings
from src.core.email.providers.sendgrid_provider import SendGridProvider
from src.core.email.providers.ses_provider import SESProvider
from src.core.email.providers.smtp_provider import SMTPProvider
from src.core.email.service import EmailService


def create_email_service() -> EmailService:
    """
    Create email service with configured providers.
    Providers are ordered by priority (first configured provider is used).
    """
    providers = []

    # Add providers based on configuration
    if settings.EMAIL_PROVIDER == "ses":
        ses = SESProvider()
        if ses.is_configured():
            providers.append(ses)
    elif settings.EMAIL_PROVIDER == "sendgrid":
        sendgrid = SendGridProvider()
        if sendgrid.is_configured():
            providers.append(sendgrid)
    elif settings.EMAIL_PROVIDER == "smtp":
        smtp = SMTPProvider()
        if smtp.is_configured():
            providers.append(smtp)

    # Fallback: always add SMTP as last resort if configured
    if settings.SMTP_HOST and not any(isinstance(p, SMTPProvider) for p in providers):
        smtp = SMTPProvider()
        if smtp.is_configured():
            providers.append(smtp)

    return EmailService(providers)
