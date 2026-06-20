from abc import ABC, abstractmethod

from src.shared.email.base import EmailMessage


class EmailProvider(ABC):
    """Abstract base class for email providers"""

    @abstractmethod
    async def send(self, message: EmailMessage) -> bool:
        """Send an email. Returns True if successful."""
        pass

    @abstractmethod
    def is_configured(self) -> bool:
        """Check if provider is properly configured"""
        pass
