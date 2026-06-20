from dataclasses import dataclass

from src.modules.user.contracts.events.base import Event


@dataclass
class UserRegisteredEvent(Event):
    """Fired when a new user registers"""

    user_id: str
    email: str
    verification_token: str


@dataclass
class PasswordResetRequestedEvent(Event):
    """Fired when user requests password reset"""

    user_id: str
    email: str
    reset_token: str


@dataclass
class WelcomeEmailEvent(Event):
    """Fired after email verification"""

    user_id: str
    email: str
    username: str
