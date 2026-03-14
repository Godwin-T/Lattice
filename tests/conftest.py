import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("DATABASE_URL_SYNC", "sqlite+pysqlite:///:memory:")
os.environ.setdefault("API_KEY_SECRET", "test-secret")

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.db.base import Base
from app.db.models import APIKey, Org, Project, User
from app.db.session import SessionLocal, engine
from app.main import app
from app.services.auth import hash_api_key
from app.services.user_auth import hash_password


@pytest.fixture(scope="session", autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    async with SessionLocal() as session:
        yield session


@pytest.fixture
async def api_key(db_session):
    result = await db_session.execute(select(Org).where(Org.name == "test-org"))
    org = result.scalar_one_or_none()
    if not org:
        org = Org(name="test-org")
        db_session.add(org)
        await db_session.commit()
        await db_session.refresh(org)

    result = await db_session.execute(select(Project).where(Project.org_id == org.id, Project.name == "test-project"))
    project = result.scalar_one_or_none()
    if not project:
        project = Project(org_id=org.id, name="test-project")
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)

    result = await db_session.execute(select(User).where(User.email == "test@example.com"))
    user = result.scalar_one_or_none()
    if not user:
        user = User(email="test@example.com", password_hash=hash_password("strongpassword"))
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

    raw_key = "test_key_123"
    key_hash = hash_api_key(raw_key)
    result = await db_session.execute(select(APIKey).where(APIKey.key_hash == key_hash))
    api_key_obj = result.scalar_one_or_none()
    if not api_key_obj:
        api_key_obj = APIKey(
            project_id=project.id,
            owner_user_id=user.id,
            created_by_user_id=user.id,
            key_hash=key_hash,
            key_prefix=raw_key[:8],
        )
        db_session.add(api_key_obj)
        await db_session.commit()
    return raw_key


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
