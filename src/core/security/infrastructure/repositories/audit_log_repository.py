from src.core.security.audit import AuditEvent
from src.core.security.infrastructure.models.audit_log_model import AuditLogModel


class SQLAlchemyAuditRepository:
    def __init__(self, db, tenant_id: str | None = None):
        self._db = db
        self._tenant_id = tenant_id

    async def save(self, event: AuditEvent) -> AuditEvent:
        self._db.add(
            AuditLogModel(
                id=event.id,
                action=event.action,
                actor_id=event.actor_id,
                resource_type=event.resource_type,
                resource_id=event.resource_id,
                request_id=event.request_id,
                tenant_id=self._tenant_id,
                meta=event.metadata,
                created_at=event.created_at,
            )
        )
        return event
