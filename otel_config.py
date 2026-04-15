import os

from opentelemetry import metrics, trace
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.sqlite3 import SQLite3Instrumentor
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def setup_otel(app):
    service_name = os.getenv("OTEL_SERVICE_NAME", "library-portal")
    otlp_base    = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4318")

    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("OTEL_ENV", "local"),
    })

    # ── Traces ──────────────────────────────────────────────────────────────
    trace_provider = TracerProvider(resource=resource)
    trace_provider.add_span_processor(
        BatchSpanProcessor(OTLPSpanExporter(endpoint=f"{otlp_base}/v1/traces"))
    )
    trace.set_tracer_provider(trace_provider)

    # ── Metrics ─────────────────────────────────────────────────────────────
    meter_provider = MeterProvider(
        resource=resource,
        metric_readers=[PeriodicExportingMetricReader(
            OTLPMetricExporter(endpoint=f"{otlp_base}/v1/metrics"),
            export_interval_millis=5000,
        )],
    )
    metrics.set_meter_provider(meter_provider)

    # ── Auto-instrumentation ─────────────────────────────────────────────────
    FlaskInstrumentor().instrument_app(app)
    SQLite3Instrumentor().instrument()
