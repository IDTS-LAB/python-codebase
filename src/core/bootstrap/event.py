from src.core.email.factory import create_email_service
from src.core.events.bus import EventBus, get_event_bus
from src.modules.user.contracts.events.emails.event import (
    PasswordResetRequestedEvent,
    UserRegisteredEvent,
    WelcomeEmailEvent,
)
from src.modules.user.contracts.events.emails.handler import (
    SendPasswordResetEmailHandler,
    SendVerificationEmailHandler,
    SendWelcomeEmailHandler,
)


def register_event_handlers(bus: EventBus | None = None) -> None:
    bus = bus or get_event_bus()
    email_service = create_email_service()
    bus.subscribe(
        UserRegisteredEvent.__name__, SendVerificationEmailHandler(email_service)
    )
    bus.subscribe(
        PasswordResetRequestedEvent.__name__,
        SendPasswordResetEmailHandler(email_service),
    )
    bus.subscribe(WelcomeEmailEvent.__name__, SendWelcomeEmailHandler(email_service))
