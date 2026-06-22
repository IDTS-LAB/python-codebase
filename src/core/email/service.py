from typing import Optional

from src.core.email.providers.base import EmailMessage, EmailProvider
from src.core.email.template_renderer import EmailTemplateRenderer


class EmailService:
    """
    High-level email service that handles provider selection and template rendering.
    Supports fallback to alternative providers if primary fails.
    """

    def __init__(self, providers: list[EmailProvider]):
        self.providers = providers
        self.renderer = EmailTemplateRenderer()

    async def send_email(
        self,
        to: str,
        subject: str,
        template_name: Optional[str] = None,
        template_context: Optional[dict] = None,
        html_body: Optional[str] = None,
        text_body: Optional[str] = None,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
    ) -> bool:
        """
        Send an email with template rendering support.

        Args:
            to: Recipient email
            subject: Email subject
            template_name: HTML template file name (optional)
            template_context: Variables for template (optional)
            html_body: Direct HTML content (if not using template)
            text_body: Plain text version (optional)
            from_email: Sender email (optional, uses default)
            from_name: Sender name (optional)

        Returns:
            True if sent successfully by any provider
        """
        # Render template if provided
        if template_name and template_context:
            html_body = self.renderer.render(template_name, template_context)

        if not html_body:
            raise ValueError("Either template_name or html_body must be provided")

        message = EmailMessage(
            to=to,
            subject=subject,
            html_body=html_body,
            text_body=text_body,
            from_email=from_email,
            from_name=from_name,
        )

        # Try providers in order (fallback strategy)
        for provider in self.providers:
            if not provider.is_configured():
                continue

            success = await provider.send(message)
            if success:
                return True

        # All providers failed
        return False
