# System Design — LatticeAI Gateway

## Executive Summary
LatticeAI is a **centralized LLM gateway** that sits between applications (or AI frameworks) and multiple LLM providers. It standardizes access with an OpenAI‑compatible API while enforcing auth, rate limits, usage logging, and cost estimation. The system is designed to be **stateless at the API layer**, horizontally scalable, and observable with metrics and traces.

Key properties:
- **Single integration** for multiple providers (OpenAI, Anthropic, Groq, etc.).
- **Governance**: API keys, rate limits, and attribution by org/project/user.
- **Cost visibility**: token and cost logging per request.
- **Observability**: structured logs, metrics, tracing hooks.

---

## Goals and Non‑Goals

### Goals
- Provide a single OpenAI‑compatible API surface.
- Enforce API key authentication and rate limits.
- Track token usage and cost per request with org/project/user attribution.
- Support multi‑provider routing and future failover.
- Operate as a **stateless, horizontally scalable gateway**.

### Non‑Goals (Current Scope)
- Full provider abstraction for tool ecosystems (e.g., tool call semantics).
- Managed vector storage or RAG infrastructure.
- Provider‑specific fine‑tuning or training pipelines.
- Global multi‑region replication (future consideration).

---

## High‑Level Architecture

```
Client / Framework
    |
    v
Gateway API (FastAPI)
  |   |\
  |   | \-- Redis (rate limiting)
  |   |
  |   \---- Postgres (API keys, usage logs)
  |
  \---- Provider APIs (OpenAI / Anthropic / Groq)

Optional:
  \---- Worker (analytics/aggregation)
  \---- UI Dashboard
```

Core components:
- **Gateway API**: request validation, auth, rate limiting, provider routing.
- **Redis**: token bucket rate limiting.
- **Postgres**: durable logs, API keys, org/project/user data.
- **Providers**: OpenAI, Anthropic, Groq (OpenAI‑compatible proxy model).
- **Optional Workers**: aggregation and reporting.

---

## Request Lifecycle (Chat Example)
1. Client sends `POST /v1/chat/completions` with `Authorization: Bearer <key>`.
2. Gateway validates API key in Postgres and resolves org/project/owner.
3. Redis token bucket enforces per‑key RPM.
4. Request is routed to selected provider.
5. Response is normalized to OpenAI shape.
6. Usage + cost metadata is logged to Postgres.
7. Metrics/traces are emitted.

Failure points:
- **Invalid key** → 401
- **Rate limit exceeded** → 429
- **Provider error** → mapped to OpenAI error format
- **DB/Redis unavailable** → readiness fails (503/health degraded)

---

## Data Model (Core Tables)
- `orgs`: organization metadata
- `org_memberships`: user ↔ org with role
- `projects`: org projects (usage grouping)
- `users`: dashboard users
- `api_keys`: project‑scoped keys with optional owner
- `request_logs`: metadata per request (no prompts stored)

**Privacy decision**: prompts and completions are not stored; only metadata is logged (provider, model, tokens, latency, cost, status).

---

## Design Decisions (Rationales)

### Token Bucket Rate Limiting
- **Why**: Allows short bursts while enforcing a long‑term RPM budget. More predictable than fixed windows and less punitive for spiky traffic.
- **Behavior**: Tokens refill at steady rate; each request consumes a token.

### Redis for Rate Limiting
- **Why**: Sub‑millisecond latency, atomic operations via Lua, and high throughput. In‑memory operations are essential for rate limiting on the hot path.
- **Alternative**: Postgres would add latency and contention under high QPS.

### Postgres for Logs and Keys
- **Why**: Strong relational integrity between orgs, projects, keys, and logs. Mature indexing and query support for usage analytics.
- **Tradeoff**: High write volume at scale requires partitioning and aggregation strategies.

### Async API Layer
- **Why**: High concurrency without thread explosion; efficient for I/O‑bound workloads (provider calls, DB, Redis).

### Structured Logs + Metrics
- **Why**: Enables correlation across requests, usage audits, and SLO enforcement.

---

## Capacity and Scaling Calculations (Deep Modeling)

These calculations are **capacity planning estimates** based on the current schema. Use them to reason about scale and storage growth.

### Baseline Formulas
- **Requests/sec (RPS)** = RPM / 60
- **Log rows/day** = RPM × 60 × 24
- **Raw storage/day** = row_size_bytes × rows/day
- **Effective storage/day** = raw × (index + WAL + bloat multiplier)
- **Redis memory** ≈ keys × (key_size + value + metadata)

### Assumptions (Conservative)
- `request_logs` row size ≈ **600 bytes** (UUID strings, ints, timestamps, varchars, overhead).
- Index/WAL/bloat multiplier ≈ **2.5×** (1.3× indexes + 0.7× WAL + 0.5× bloat).
- Redis per rate‑limit key ≈ **200 bytes** (key + token bucket state + metadata).

> These are estimates. Exact values depend on Postgres tuple layout, fillfactor, and index design.

### Worked Scenarios

#### Scenario A — 1k RPM
- RPS: 1,000 / 60 ≈ **16.7 RPS**
- Rows/day: 1,000 × 60 × 24 = **1.44M rows**
- Raw storage/day: 1.44M × 600B ≈ **864 MB/day**
- Effective storage/day (×2.5): **~2.2 GB/day**
- Monthly (~30 days): **~66 GB/month**
- Redis keys (10k API keys): 10k × 200B ≈ **2 MB**

#### Scenario B — 10k RPM
- RPS: **166.7 RPS**
- Rows/day: **14.4M rows**
- Raw storage/day: **8.6 GB/day**
- Effective storage/day: **~21.6 GB/day**
- Monthly: **~648 GB/month**
- Redis keys (100k keys): **~20 MB**

#### Scenario C — 100k RPM
- RPS: **1,667 RPS**
- Rows/day: **144M rows**
- Raw storage/day: **86.4 GB/day**
- Effective storage/day: **~216 GB/day**
- Monthly: **~6.5 TB/month**
- Redis keys (1M keys): **~200 MB**

### Write IOPS Implications
Each insert touches:
- Table heap
- 3–4 indexes (org_id, project_id, owner_user_id, api_key_id)

At 100k RPM (~1,667 RPS):
- ~1,667 inserts/sec
- ~6,000–8,000 index writes/sec

**Implication**: A single Postgres instance can handle low/medium workloads but will require partitioning + replication at high RPM.

---

## Scaling Strategy

### API Layer
- Stateless: add instances behind a load balancer.
- Scale horizontally with CPU/RPS metrics.

### Redis
- Start with single instance.
- Move to Redis Sentinel or Cluster for HA and scale.

### Postgres
- Add read replicas for analytics.
- Partition `request_logs` by time (daily/monthly) at scale.
- Consider background aggregation into rollup tables.
- Use connection pooling (PgBouncer) under high concurrency.

### Async Workers
- Offload aggregation to workers (Celery/async tasks).
- Write to summary tables per day/week/org.

---

## Load Balancing & High Availability

- **Load balancer**: ALB/NGINX/Envoy with health checks.
- **Gateway**: multiple instances, no sticky sessions required.
- **Postgres**: primary + replicas; async failover.
- **Redis**: sentinel/cluster for failover and sharding.

---

## Reliability & Failure Modes

- **Redis outage**: rate limiting fails → return 503 or degrade to best‑effort.
- **Provider outage**: retry with exponential backoff; optional failover.
- **DB latency**: consider async logging buffer or queue.

---

## Observability and SLOs

### Core SLIs
- Gateway latency (p95/p99)
- Provider error rate
- Rate‑limit hit rate
- Log ingestion delay

### Example SLOs
- p95 gateway latency < 200ms (excluding provider)
- Error rate < 1%
- Log ingestion delay < 5s

---

## Future Considerations
- Prompt caching (Redis)
- Idempotency keys
- Adaptive routing (cost/latency based)
- Budget alerts and anomaly detection
- Multi‑region deployment

---

## Operational Runbook Snippets

### If logs stop appearing
1. Check Postgres connectivity.
2. Check request logging errors in gateway logs.
3. Confirm `request_logs` table growth.

### If rate limits fail
1. Check Redis connectivity and latency.
2. Confirm token bucket Lua script is loaded.

### Scaling Postgres
- Add partitions for `request_logs`.
- Add read replicas for analytics.
- Implement retention or archive policies.
