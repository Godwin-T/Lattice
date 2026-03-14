# Technical README

This document explains how LatticeAI Gateway works and how to run or contribute to it. It is intentionally simple and MVP-focused.

## Architecture Overview

```
Client
  │
  ▼
Gateway API (FastAPI)
  │  ├─ Auth + Sessions
  │  ├─ API keys
  │  ├─ Rate limit (Redis)
  │  ├─ Provider routing
  │  └─ Logging + metrics
  ▼
Provider APIs (OpenAI, Anthropic, Groq)
```

Reference: `docs/architecture.md`

## Core Components and File Map

| Component | Responsibility | Primary Files |
| --- | --- | --- |
| API entrypoint | FastAPI app, middleware, error handling | `app/main.py` |
| Auth routes | Register/login/logout/me | `app/api/auth.py` |
| Org routes | Org membership + invites | `app/api/orgs.py` |
| Projects routes | Project CRUD | `app/api/projects.py` |
| Keys routes | API key CRUD | `app/api/keys.py` |
| Usage routes | Usage by org/user/project/key | `app/api/usage.py` |
| Requests routes | Filtered request logs | `app/api/requests.py` |
| Dashboard routes | Overview, usage, requests, providers | `app/api/dashboard.py` |
| API routes | LLM proxy endpoints | `app/api/routes.py` |
| System routes | Health, readiness, metrics | `app/api/system.py` |
| Auth service | Password + session logic | `app/services/user_auth.py` |
| API key auth | Key hashing/validation | `app/services/auth.py` |
| Rate limiting | Redis token bucket | `app/services/rate_limit.py` |
| Providers | OpenAI, Anthropic, Groq clients | `app/services/providers/*` |
| Provider routing | Picks provider client | `app/services/providers/router.py` |
| Costing | Pricing table + cost calc | `app/core/pricing.py` |
| Logging | Request logs to Postgres | `app/services/request_logging.py` |
| Data models | SQLAlchemy models | `app/db/models.py` |
| Migrations | Alembic setup | `alembic/`, `alembic.ini` |
| Metrics | Prometheus counters/histograms | `app/observability/metrics.py` |

## Auth Flow
1. User registers or logs in.
2. Server sets an HTTP-only session cookie.
3. UI calls `/auth/me` to verify authentication.
4. Protected endpoints use the session to authorize access.

## Request Lifecycle (Chat)
1. Client sends `POST /v1/chat/completions` with `Authorization: Bearer <key>`.
2. API key is validated against Postgres.
3. Redis token bucket checks the rate limit.
4. Provider client is selected by `provider` field (default: `openai`).
5. Gateway forwards the request to the provider.
6. Response is normalized to OpenAI format.
7. Usage and cost are logged to Postgres.
8. Metrics are emitted and the response returns to the client.

## Configuration

Environment variables are loaded from `.env` using `app/core/settings.py`.

| Variable | Purpose | Default |
| --- | --- | --- |
| `ENVIRONMENT` | Environment name | `dev` |
| `SERVICE_NAME` | Service name for tracing | `latticeai-gateway` |
| `API_KEY_SECRET` | HMAC secret for API key hashing | `change-me` |
| `DATABASE_URL` | Async Postgres connection string | `postgresql+asyncpg://lattice:lattice@localhost:5432/lattice` |
| `REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `RATE_LIMIT_RPM` | Requests per minute per key | `60` |
| `OPENAI_API_KEY` | OpenAI provider key | empty |
| `ANTHROPIC_API_KEY` | Anthropic provider key | empty |
| `GROQ_API_KEY` | Groq provider key | empty |
| `GROQ_BASE_URL` | Groq API base URL override | empty |
| `SESSION_SECRET` | Session HMAC secret | `change-me` |
| `SESSION_COOKIE_NAME` | Session cookie name | `lattice_session` |
| `SESSION_TTL_HOURS` | Session TTL in hours | `168` |
| `SESSION_COOKIE_SECURE` | Secure cookies in production | `false` |
| `REQUEST_TIMEOUT_S` | Provider timeout in seconds | `30` |
| `OTEL_ENABLED` | Enable OpenTelemetry | `false` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | OTLP endpoint | empty |
| `LOG_LEVEL` | Log level | `INFO` |
| `CORS_ORIGINS` | Comma-separated CORS origins | `http://localhost:5173` |

Reference: `.env.example`

## System Design
- Detailed design: `docs/system-design.md`

## API Surface Summary

| Endpoint | Purpose |
| --- | --- |
| `POST /auth/register` | Register user |
| `POST /auth/login` | Login user |
| `POST /auth/logout` | Logout user |
| `GET /auth/me` | Current user |
| `GET /keys` | List API keys |
| `POST /keys` | Create API key |
| `POST /keys/{key_id}/revoke` | Revoke API key |
| `DELETE /keys/{key_id}` | Delete API key |
| `GET /orgs/me` | Current org |
| `GET /orgs/members` | List org members |
| `POST /orgs/members/invite` | Invite member |
| `PATCH /orgs/members/{member_id}` | Update member role |
| `GET /projects` | List projects |
| `POST /projects` | Create project |
| `PATCH /projects/{project_id}` | Update project |
| `GET /usage/overview` | Usage totals |
| `GET /usage/by-user` | Usage by user |
| `GET /usage/by-project` | Usage by project |
| `GET /usage/by-key` | Usage by API key |
| `GET /requests` | Filtered request logs |
| `GET /dashboard/overview` | Dashboard KPIs |
| `GET /dashboard/usage` | Usage by day |
| `GET /dashboard/requests` | Recent requests |
| `GET /dashboard/providers` | Provider status |
| `POST /v1/chat/completions` | OpenAI-compatible chat completions |
| `POST /v1/embeddings` | OpenAI-compatible embeddings |
| `GET /health` | Liveness probe |
| `GET /ready` | Readiness probe (DB + Redis) |
| `GET /metrics` | Prometheus metrics |

Reference: `docs/api.md`

## Data Model Overview

| Table | Purpose |
| --- | --- |
| `orgs` | Organizations |
| `org_memberships` | User ↔ org membership and roles |
| `projects` | Projects under orgs |
| `users` | User accounts |
| `sessions` | Auth sessions |
| `api_keys` | Hashed API keys and metadata |
| `request_logs` | Usage, cost, and error metadata |

Primary file: `app/db/models.py`

## Rate Limiting
- Token bucket per API key, stored in Redis.
- Key pattern: `rl:<api_key_id>`.
- Capacity and refill are derived from `RATE_LIMIT_RPM`.

## Observability
- Logs: structured JSON via `structlog`.
- Metrics: Prometheus counters and histograms at `GET /metrics`.
- Tracing: OpenTelemetry hooks when `OTEL_ENABLED=true`.

## Async Stack
- FastAPI async endpoints
- SQLAlchemy async + `asyncpg`
- Redis asyncio client
- OpenAI, Anthropic, Groq async SDKs

## UI
- React + Vite + TypeScript in `ui/`
- Light/dark themes with CSS variables
- React Query for data fetching

## Local Development

Docker Compose:

```bash
cd docker
docker compose up --build
```

Migrations:

```bash
docker compose exec gateway alembic upgrade head
```

Create an API key:

```bash
docker compose exec gateway python scripts/create_api_key.py --email admin@example.com
```

Local (no Docker):

```bash
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

UI:

```bash
cd ui
npm install
npm run dev
```

## Tests

```bash
pytest
```

## Troubleshooting
- 401 errors usually mean missing or invalid API key.
- 429 errors indicate the rate limit was exceeded.
- 503 errors indicate Redis or the rate limiter is unavailable.
- Provider errors often mean missing provider API keys.
- Alembic errors usually indicate the DB URL is not sync-compatible for migrations.

## Contribution Basics
- Keep changes focused and small.
- Update or add tests for new logic.
- Run `pytest` before opening a PR.
- Keep docs updated when behavior changes.
