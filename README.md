# LatticeAI Gateway

Production-grade, multi-provider LLM infrastructure layer.

LatticeAI is a centralized gateway that sits between your application and LLM providers (OpenAI, Anthropic, Groq, and more). It gives you one OpenAI-compatible API with built-in auth, rate limiting, cost tracking, and observability so you can ship AI features safely and consistently.

**What LatticeAI Does**
- Proxies OpenAI-compatible requests for chat and embeddings.
- Routes to multiple providers with a single API surface.
- Enforces API key auth and per-key rate limits.
- Logs token usage and costs to Postgres with org/project/user attribution.
- Exposes health, readiness, and Prometheus metrics.

**Advantages**
- One integration for multiple LLM providers.
- Centralized governance for keys, limits, and usage.
- Usage visibility by org, project, and API key owner.
- Predictable costs with built-in tracking.
- Observability hooks for logs, metrics, and traces.
- Clear path to production features (routing, caching, retries).

**Quick Start (Docker Compose)**
1. Copy `.env.example` to `.env` and set provider API keys.
2. Start the stack:

```bash
cd docker
docker compose up --build
```

3. Migrations run automatically on container startup by default. If no migration files exist, the container will autogenerate an initial revision, then apply it. The container will retry if Postgres isn’t ready yet. You can disable this by setting `AUTO_MIGRATE=false` in `.env`.

4. Login to the UI using the default admin credentials from `.env`:

- `ADMIN_EMAIL` (default: `admin@lattice.com`)
- `ADMIN_PASSWORD` (default: `admin@lattice`)

5. Create an API key:

```bash
docker compose exec gateway python scripts/create_api_key.py --email admin@lattice.com
```

**Quick Start (Local)**
1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Export env vars from `.env`.
3. Start the server:

```bash
uvicorn api.main:app --reload
```

4. If you run with Docker, migrations are automatic. For local runs, you can still run `alembic upgrade head` manually if needed.

5. Login to the UI using the default admin credentials from `.env`.

**UI Setup (React + TypeScript)**
1. From repo root:

```bash
cd ui
npm install
npm run dev
```

2. Ensure `CORS_ORIGINS` in `.env` includes `http://localhost:5173`.

**Auth Hashing**
- Passwords are hashed with Argon2id.
- Older bcrypt hashes are not supported; existing users must reset passwords.

**Integration Examples**

OpenAI SDK (OpenAI-compatible):

```python
from openai import OpenAI

client = OpenAI(
    api_key="LATTICE_API_KEY",
    base_url="http://your-lattice-host:8000"
)

resp = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Hello"}],
    extra_body={"provider": "openai"}
)
print(resp.choices[0].message.content)
```

curl:

```bash
curl http://your-lattice-host:8000/v1/chat/completions \
  -H "Authorization: Bearer LATTICE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model":"gpt-4o-mini",
    "provider":"openai",
    "messages":[{"role":"user","content":"Hello"}]
  }'
```

**Feature Overview**

| Area | MVP | Roadmap |
| --- | --- | --- |
| Providers | OpenAI + Anthropic + Groq (chat), OpenAI embeddings | Multi-provider routing and failover |
| Auth | API keys + user accounts | Idempotency keys, org policies |
| Reliability | Basic retries per provider | Retry on schema validation failures |
| Cost/Usage | Token and cost logging | Alerts and budgets |
| Observability | Logs + metrics + tracing hooks | Full dashboards and alerts |
| Caching | Not in MVP | Prompt caching via Redis |

**Tech Stack (Async)**
- FastAPI + SQLAlchemy async (`asyncpg`)
- Redis asyncio client
- OpenAI, Anthropic, Groq async SDKs
- React + Vite + TypeScript (UI)

**Documentation**
- Technical README: `docs/TECHNICAL.md`
- API: `docs/api.md`
- UI: `docs/ui.md`
- Architecture: `docs/architecture.md`
- System Design: `docs/system-design.md`
- Operations: `docs/operations.md`
