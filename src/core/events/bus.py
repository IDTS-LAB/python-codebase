from functools import lru_cache

from shared.events.base import Event
from shared.events.handler import EventHandler


class EventBus:
    """
    General-purpose event bus for publishing and subscribing to events.
    Supports multiple handlers per event type.
    """

    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = {}

    def subscribe(self, event_type: str, handler: EventHandler):
        """Register a handler for a specific event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def unsubscribe(self, event_type: str, handler: EventHandler):
        """Remove a handler for a specific event type"""
        if event_type in self._handlers:
            self._handlers[event_type] = [
                h for h in self._handlers[event_type] if h != handler
            ]

    async def publish(self, event: Event):
        """Publish an event to all subscribed handlers"""
        event_type = event.event_type
        handlers = self._handlers.get(event_type, [])

        for handler in handlers:
            try:
                await handler.handle(event)
            except Exception as e:
                # Log error but don't stop other handlers
                print(
                    f"Error in handler {handler.__class__.__name__} for event {event_type}: {e}"
                )
                # In production, use proper logging and error tracking (Sentry, etc.)


@lru_cache
def get_event_bus() -> EventBus:
    return EventBus()
