from dataclasses import dataclass, field
from datetime import UTC, datetime
from uuid import UUID, uuid4


@dataclass(kw_only=True)
class Event:
    """Base class for all domain events"""

    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    event_type: str = ""

    def __post_init__(self):
        if not self.event_type:
            self.event_type = self.__class__.__name__
