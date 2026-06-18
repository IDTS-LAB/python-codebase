from src.core.security.audit import ErrorTrace
from src.core.security.infrastructure.models.error_trace_model import ErrorTraceModel


class SQLAlchemyErrorTraceRepository:
    def __init__(self, db):
        self._db = db

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
                meta=trace.metadata,
                created_at=trace.created_at,
            )
        )
        return trace
