from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from sqlalchemy.ext.asyncio import AsyncEngine

from src.core.config.setting import Settings


def setup_tracing(settings: Settings) -> TracerProvider | None:
    if not settings.OTEL_ENABLED:
        return None

    resource = Resource.create(
        {
            "service.name": settings.OTEL_SERVICE_NAME,
            "service.version": "1.0.0",
            "deployment.environment": settings.APP_ENV,
        }
    )

    provider = TracerProvider(resource=resource)

    if settings.OTEL_EXPORTER_OTLP_ENDPOINT:
        exporter = OTLPSpanExporter(
            endpoint=settings.OTEL_EXPORTER_OTLP_ENDPOINT,
            headers=settings.OTEL_EXPORTER_OTLP_HEADERS,
        )
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)
    elif not settings.is_production:
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    trace.set_tracer_provider(provider)
    return provider


def instrument_app(
    app: FastAPI,
    db_engine: AsyncEngine | None = None,
    settings: Settings | None = None,
) -> None:
    if settings is not None and not settings.OTEL_ENABLED:
        return

    FastAPIInstrumentor.instrument_app(app)

    if db_engine is not None:
        SQLAlchemyInstrumentor().instrument(engine=db_engine.sync_engine)

    RedisInstrumentor().instrument()


def shutdown_tracing() -> None:
    provider = trace.get_tracer_provider()
    if isinstance(provider, TracerProvider):
        provider.shutdown()
