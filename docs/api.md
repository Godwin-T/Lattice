# API

## Authentication

Use `Authorization: Bearer <api_key>` for gateway requests.
Dashboard endpoints use secure session cookies created via `/auth/login` or `/auth/register`.

### Auth Error Format

All auth errors return:

```json
{
  "error": {
    "code": "INVALID_CREDENTIALS",
    "message": "Invalid email or password",
    "details": {}
  }
}
```

Common error codes:
- `EMAIL_EXISTS`
- `INVALID_CREDENTIALS`
- `USER_INACTIVE`
- `PASSWORD_TOO_SHORT`

## Auth Endpoints

### POST /auth/register

```json
{
  "email": "you@example.com",
  "password": "strongpassword"
}
```

### POST /auth/login

```json
{
  "email": "you@example.com",
  "password": "strongpassword"
}
```

### POST /auth/logout

### GET /auth/me

## API Key Management
API keys are project-scoped and can optionally be assigned to an owner user.

### GET /keys

### POST /keys
Request body:

```json
{
  "project_id": "project-id",
  "owner_user_id": "optional-user-id"
}
```

### POST /keys/{key_id}/revoke

### DELETE /keys/{key_id}

## Org and Project Management

### GET /orgs/me

### GET /orgs/members

### POST /orgs/members/invite

```json
{
  "email": "teammate@example.com",
  "role": "member"
}
```

### PATCH /orgs/members/{member_id}

```json
{
  "role": "admin"
}
```

### GET /projects

### POST /projects

```json
{
  "name": "my-project"
}
```

### PATCH /projects/{project_id}

```json
{
  "name": "renamed-project"
}
```

## Usage and Requests

### GET /usage/overview
Optional query params: `org_id`, `project_id`.

### GET /usage/by-user
Optional query params: `org_id`.

### GET /usage/by-project
Optional query params: `org_id`.

### GET /usage/by-key
Required query param: `project_id`.

### GET /requests
Filters: `org_id`, `project_id`, `user_id`, `key_id`.

## LLM Endpoints

### POST /v1/chat/completions
OpenAI-compatible chat completion endpoint.

Request example:

```json
{
  "model": "gpt-4o-mini",
  "provider": "openai",
  "messages": [
    {"role": "system", "content": "You are helpful"},
    {"role": "user", "content": "Hello"}
  ],
  "temperature": 0.2
}
```

Groq example:

```json
{
  "model": "llama-3.1-8b-instant",
  "provider": "groq",
  "messages": [
    {"role": "user", "content": "Hello"}
  ]
}
```

### POST /v1/embeddings
OpenAI-compatible embeddings endpoint.

```json
{
  "model": "text-embedding-3-small",
  "provider": "openai",
  "input": "hello"
}
```

## Dashboard Endpoints

### GET /dashboard/overview

### GET /dashboard/usage

### GET /dashboard/requests

### GET /dashboard/providers

## System

### GET /health
Liveness probe.

### GET /ready
Readiness probe (checks DB and Redis).

### GET /metrics
Prometheus metrics.
