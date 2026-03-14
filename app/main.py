from __future__ import annotations

import uuid

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.auth import router as auth_router
from app.api.dashboard import router as dashboard_router
from app.api.keys import router as keys_router
from app.api.pricing import router as pricing_router
from app.api.test import router as test_router
from app.api.orgs import router as orgs_router
from app.api.projects import router as projects_router
from app.api.requests import router as requests_router
from app.api.routes import router as api_router
from app.api.system import router as system_router
from app.api.usage import router as usage_router

from app.core.logging import configure_logging
from app.core.settings import get_settings
from app.schemas.errors import OpenAIError, openai_error_response
from app.services.auth_errors import AuthError, auth_error_response
from app.services.bootstrap import ensure_admin_user


settings = get_settings()
configure_logging(settings.log_level)
logger = structlog.get_logger()


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(request_id=request_id)
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


app = FastAPI(title="LatticeAI Gateway", version="0.1.0")

app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(system_router)
app.include_router(auth_router)
app.include_router(keys_router)
app.include_router(pricing_router)
app.include_router(test_router)
app.include_router(orgs_router)
app.include_router(projects_router)
app.include_router(usage_router)
app.include_router(requests_router)
app.include_router(dashboard_router)


@app.exception_handler(OpenAIError)
async def openai_error_handler(request: Request, exc: OpenAIError):
    response = openai_error_response(exc)
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


@app.exception_handler(AuthError)
async def auth_error_handler(request: Request, exc: AuthError):
    response = auth_error_response(exc)
    request_id = getattr(request.state, "request_id", None)
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response


@app.on_event("startup")
async def startup_event():
    if settings.otel_enabled:
        _init_otel(app)
        logger.info("otel_initialized")
    await ensure_admin_user()
    logger.info("admin_bootstrap_complete", admin_email=settings.admin_email)


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("shutdown")


def _init_otel(app: FastAPI) -> None:
    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

    resource = Resource.create({"service.name": settings.service_name})
    tracer_provider = TracerProvider(resource=resource)

    if settings.otel_exporter_otlp_endpoint:
        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
    else:
        exporter = ConsoleSpanExporter()

    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(tracer_provider)

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()
