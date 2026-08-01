from src.core.security.audit import ErrorTrace
from src.core.security.infrastructure.models.error_trace_model import ErrorTraceModel


class SQLAlchemyErrorTraceRepository:
    def __init__(self, db, tenant_id: str | None = None):
        self._db = db
        self._tenant_id = tenant_id

    async def save(self, trace: ErrorTrace) -> ErrorTrace:
        self._db.add(
            ErrorTraceModel(
                id=trace.id,
                error_type=trace.error_type,
                message=trace.message,
                traceback=trace.traceback,
                method=trace.method,
                path=trace.path,
                actor_id=trace.actor_id,
                request_id=trace.request_id,
                tenant_id=self._tenant_id,
                meta=trace.metadata,
                created_at=trace.created_at,
            )
        )
        return trace
