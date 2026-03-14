# Operations

## Local (Docker Compose)

1. Copy `.env.example` to `.env` and fill in provider API keys.
2. Start dependencies and gateway:

```bash
cd docker
docker compose up --build
```

3. Apply database migrations:

```bash
docker compose exec gateway alembic upgrade head
```

4. Create an API key:

```bash
docker compose exec gateway python scripts/create_api_key.py --org default --project default
```

## Local (No Docker)

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Export environment variables from `.env`.
3. Run migrations:

```bash
alembic upgrade head
```

4. Start the server:

```bash
uvicorn app.main:app --reload
```
