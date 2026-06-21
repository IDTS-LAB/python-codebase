from typing import Protocol

from src.shared.events.base import Event


class EventHandler(Protocol):
    """Protocol for event handlers"""

    async def handle(self, event: Event) -> None:
        pass
