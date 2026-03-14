# Architecture

## Overview

Client → Gateway API → Provider APIs

Supporting services:
- Redis: rate limiting
- Postgres: API keys, request logs, cost tracking
- Optional workers: analytics and reporting

## Data Flow (Chat)
1. Client sends OpenAI-compatible request with `Authorization: Bearer <key>`.
2. Gateway authenticates API key from Postgres.
3. Redis token bucket enforces rate limits per key.
4. Gateway routes to provider (OpenAI or Anthropic).
5. Response is normalized to OpenAI shape.
6. Usage and cost are logged to Postgres.
7. Metrics and traces are emitted for observability.
