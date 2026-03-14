from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from starlette.responses import Response

REQUEST_COUNT = Counter(
    "gateway_requests_total",
    "Total gateway requests",
    ["endpoint", "provider", "status"],
)

REQUEST_LATENCY = Histogram(
    "gateway_request_latency_seconds",
    "Gateway request latency",
    ["endpoint", "provider"],
)

RATE_LIMIT_BLOCKS = Counter(
    "gateway_rate_limit_block_total",
    "Rate limit blocks",
    ["endpoint"],
)


def record_request(endpoint: str, provider: str, status: int, latency_seconds: float) -> None:
    REQUEST_COUNT.labels(endpoint=endpoint, provider=provider, status=str(status)).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint, provider=provider).observe(latency_seconds)


def record_rate_limit(endpoint: str) -> None:
    RATE_LIMIT_BLOCKS.labels(endpoint=endpoint).inc()


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
