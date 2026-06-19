from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol
from uuid import UUID, uuid4


@dataclass
class AuditEvent:
    action: str
    actor_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    request_id: str | None = None
    metadata: dict = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class AuditRepository(Protocol):
    async def save(self, event: AuditEvent) -> AuditEvent:
        pass


class AuditService:
    def __init__(self, repository: AuditRepository | None = None):
        self._repository = repository

    async def record(self, event: AuditEvent) -> None:
        if self._repository is None:
            return
        await self._repository.save(event)


@dataclass
class ErrorTrace:
    error_type: str
    message: str
    traceback: str
    method: str
    path: str
    actor_id: str | None = None
    request_id: str | None = None
    metadata: dict = field(default_factory=dict)
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ErrorTraceRepository(Protocol):
    async def save(self, trace: ErrorTrace) -> ErrorTrace:
        pass


class ErrorTraceService:
    def __init__(self, repository: ErrorTraceRepository | None = None):
        self._repository = repository

    async def record(self, trace: ErrorTrace) -> None:
        if self._repository is None:
            return
        await self._repository.save(trace)
