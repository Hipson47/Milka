"""Observability setup: OpenTelemetry tracing, Prometheus metrics, structured logging."""

import os
import time
import logging
from typing import Any, Dict, Optional
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Request, Response
from fastapi.responses import PlainTextResponse
import structlog
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.instrumentation.logging import LoggingInstrumentor


# Prometheus metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status_code']
)

REQUEST_SIZE = Histogram(
    'http_request_size_bytes',
    'HTTP request size in bytes',
    ['method', 'endpoint']
)

RESPONSE_SIZE = Histogram(
    'http_response_size_bytes',
    'HTTP response size in bytes',
    ['method', 'endpoint', 'status_code']
)

ACTIVE_REQUESTS = Gauge(
    'http_requests_active',
    'Number of active HTTP requests'
)

NANOBANANA_REQUESTS = Counter(
    'nanobanana_requests_total',
    'Total requests to NanoBanana API',
    ['status_code', 'endpoint']
)

NANOBANANA_DURATION = Histogram(
    'nanobanana_request_duration_seconds',
    'NanoBanana API request duration',
    ['endpoint']
)

IMAGE_PROCESSING_DURATION = Histogram(
    'image_processing_duration_seconds',
    'Image processing duration',
    ['operation']  # validate, resize, convert, etc.
)

MASK_OPERATIONS = Counter(
    'mask_operations_total',
    'Mask processing operations',
    ['operation', 'status']  # draw, erase, export, success/error
)


def setup_structured_logging() -> None:
    """Setup structured logging with JSON output."""
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="ISO"),
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.set_exc_info,
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        context_class=dict,
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=False,
    )
    
    # Configure standard logging
    logging.basicConfig(
        format='%(message)s',
        level=logging.INFO,
        handlers=[logging.StreamHandler()]
    )


def setup_tracing(app: FastAPI, service_name: str = "inpaint-backend") -> None:
    """Setup OpenTelemetry tracing."""
    
    # Create resource
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
        "deployment.environment": os.getenv("ENVIRONMENT", "development"),
    })
    
    # Setup tracer provider
    trace.set_tracer_provider(TracerProvider(resource=resource))
    tracer_provider = trace.get_tracer_provider()
    
    # Setup OTLP exporter if endpoint is configured
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if otlp_endpoint:
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
                headers=_parse_otlp_headers()
            )
            span_processor = BatchSpanProcessor(otlp_exporter)
            tracer_provider.add_span_processor(span_processor)
            
            logger = structlog.get_logger()
            logger.info("OTLP tracing configured", endpoint=otlp_endpoint)
            
        except ImportError:
            logger = structlog.get_logger()
            logger.warning("OTLP exporter not available, tracing to console only")
    
    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument HTTPX for NanoBanana API calls
    HTTPXClientInstrumentor().instrument()
    
    # Instrument logging
    LoggingInstrumentor().instrument()


def _parse_otlp_headers() -> Dict[str, str]:
    """Parse OTEL_EXPORTER_OTLP_HEADERS environment variable."""
    headers = {}
    headers_env = os.getenv("OTEL_EXPORTER_OTLP_HEADERS", "")
    
    if headers_env:
        for header in headers_env.split(","):
            if "=" in header:
                key, value = header.strip().split("=", 1)
                headers[key] = value
    
    return headers


def setup_metrics_endpoint(app: FastAPI) -> None:
    """Setup Prometheus metrics endpoint."""
    
    @app.get("/metrics", response_class=PlainTextResponse)
    async def metrics():
        """Prometheus metrics endpoint."""
        return generate_latest()


def record_request_metrics(
    method: str,
    endpoint: str,
    status_code: int,
    duration: float,
    request_size: Optional[int] = None,
    response_size: Optional[int] = None
) -> None:
    """Record HTTP request metrics."""
    
    REQUEST_COUNT.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=method,
        endpoint=endpoint,
        status_code=status_code
    ).observe(duration)
    
    if request_size is not None:
        REQUEST_SIZE.labels(
            method=method,
            endpoint=endpoint
        ).observe(request_size)
    
    if response_size is not None:
        RESPONSE_SIZE.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).observe(response_size)


def record_nanobanana_metrics(
    endpoint: str,
    status_code: int,
    duration: float
) -> None:
    """Record NanoBanana API metrics."""
    
    NANOBANANA_REQUESTS.labels(
        status_code=status_code,
        endpoint=endpoint
    ).inc()
    
    NANOBANANA_DURATION.labels(
        endpoint=endpoint
    ).observe(duration)


def record_image_processing_metrics(
    operation: str,
    duration: float
) -> None:
    """Record image processing metrics."""
    
    IMAGE_PROCESSING_DURATION.labels(
        operation=operation
    ).observe(duration)


def record_mask_operation_metrics(
    operation: str,
    status: str
) -> None:
    """Record mask operation metrics."""
    
    MASK_OPERATIONS.labels(
        operation=operation,
        status=status
    ).inc()


class MetricsMiddleware:
    """Middleware to collect HTTP metrics."""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        start_time = time.time()
        ACTIVE_REQUESTS.inc()
        
        request_size = 0
        response_size = 0
        status_code = 500
        
        async def receive_wrapper():
            nonlocal request_size
            message = await receive()
            if message["type"] == "http.request":
                body = message.get("body", b"")
                request_size += len(body)
            return message
        
        async def send_wrapper(message):
            nonlocal response_size, status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            elif message["type"] == "http.response.body":
                body = message.get("body", b"")
                response_size += len(body)
            await send(message)
        
        try:
            await self.app(scope, receive_wrapper, send_wrapper)
        finally:
            ACTIVE_REQUESTS.dec()
            duration = time.time() - start_time
            
            method = scope.get("method", "UNKNOWN")
            path = scope.get("path", "/unknown")
            
            # Normalize endpoint for metrics (remove dynamic parts)
            endpoint = _normalize_endpoint(path)
            
            record_request_metrics(
                method=method,
                endpoint=endpoint,
                status_code=status_code,
                duration=duration,
                request_size=request_size,
                response_size=response_size
            )


def _normalize_endpoint(path: str) -> str:
    """Normalize endpoint path for metrics to avoid high cardinality."""
    
    # Common patterns to normalize
    normalizations = {
        "/api/edit": "/api/edit",
        "/api/health": "/api/health",
        "/metrics": "/metrics",
        "/docs": "/docs",
        "/redoc": "/redoc",
        "/openapi.json": "/openapi.json"
    }
    
    # Check exact matches first
    if path in normalizations:
        return normalizations[path]
    
    # Handle dynamic paths
    if path.startswith("/api/"):
        return "/api/*"
    
    return "/other"


def get_logger() -> Any:
    """Get structured logger instance."""
    return structlog.get_logger()


def setup_observability(app: FastAPI) -> None:
    """Setup all observability components."""
    
    # Setup structured logging
    setup_structured_logging()
    
    # Setup tracing
    setup_tracing(app)
    
    # Setup metrics endpoint
    setup_metrics_endpoint(app)
    
    # Add metrics middleware
    app.add_middleware(MetricsMiddleware)
    
    logger = get_logger()
    logger.info(
        "Observability configured",
        tracing_enabled=bool(os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")),
        metrics_endpoint="/metrics",
        structured_logging=True
    )
