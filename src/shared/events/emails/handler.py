from src.core.config import settings
from src.core.email.service import EmailService
from src.shared.events.emails.event import (
    PasswordResetRequestedEvent,
    UserRegisteredEvent,
    WelcomeEmailEvent,
)
from src.shared.events.handler import EventHandler


class SendVerificationEmailHandler(EventHandler):
    """Sends verification email when user registers"""

    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    async def handle(self, event: UserRegisteredEvent):
        verification_url = (
            f"{settings.FRONTEND_URL}/verify-email?token={event.verification_token}"
        )

        success = await self.email_service.send_email(
            to=event.email,
            subject="Verify your email address",
            template_name="verification.html",
            template_context={
                "verification_url": verification_url,
                "user_email": event.email,
            },
        )

        if not success:
            print(f"Failed to send verification email to {event.email}")


class SendPasswordResetEmailHandler(EventHandler):
    """Sends password reset email"""

    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    async def handle(self, event: PasswordResetRequestedEvent):
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={event.reset_token}"

        success = await self.email_service.send_email(
            to=event.email,
            subject="Reset your password",
            template_name="password_reset.html",
            template_context={"reset_url": reset_url, "user_email": event.email},
        )

        if not success:
            print(f"Failed to send password reset email to {event.email}")


class SendWelcomeEmailHandler(EventHandler):
    """Sends welcome email after verification"""

    def __init__(self, email_service: EmailService):
        self.email_service = email_service

    async def handle(self, event: WelcomeEmailEvent):
        success = await self.email_service.send_email(
            to=event.email,
            subject="Welcome to Todo Modulith!",
            template_name="welcome.html",
            template_context={"username": event.username, "user_email": event.email},
        )

        if not success:
            print(f"Failed to send welcome email to {event.email}")
