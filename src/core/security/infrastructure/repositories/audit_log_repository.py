from src.core.security.audit import AuditEvent
from src.core.security.infrastructure.models.audit_log_model import AuditLogModel


class SQLAlchemyAuditRepository:
    def __init__(self, db):
        self._db = db

    async def save(self, event: AuditEvent) -> AuditEvent:
        self._db.add(
            AuditLogModel(
                id=event.id,
                action=event.action,
                actor_id=event.actor_id,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                request_id=event.request_id,
                meta=event.metadata,
                created_at=event.created_at,
            )
        )
        return event
