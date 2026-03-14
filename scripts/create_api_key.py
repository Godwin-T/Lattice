from __future__ import annotations

import argparse
import asyncio
import secrets

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import get_settings
from app.db.base import Base
from app.db.models import APIKey, OrgMembership, User
from app.db.session import SessionLocal, engine
from app.services.auth import hash_api_key
from app.services.bootstrap import _ensure_admin_user
from app.services.orgs import get_membership
from app.services.projects import ensure_default_project


def _key_prefix(raw_key: str) -> str:
    return raw_key[:8]


async def generate_api_key(db: AsyncSession, user: User, project_id: str) -> str:
    while True:
        raw_key = f"lattice_{secrets.token_urlsafe(32)}"
        key_hash = hash_api_key(raw_key)
        result = await db.execute(select(APIKey).where(APIKey.key_hash == key_hash))
        existing = result.scalar_one_or_none()
        if existing:
            continue
        api_key = APIKey(
            project_id=project_id,
            owner_user_id=user.id,
            created_by_user_id=user.id,
            key_hash=key_hash,
            key_prefix=_key_prefix(raw_key),
        )
        db.add(api_key)
        await db.commit()
        return raw_key


async def main() -> None:
    parser = argparse.ArgumentParser(description="Create an API key for LatticeAI Gateway")
    parser.add_argument("--email", default=None, help="Owner email for the API key (defaults to ADMIN_EMAIL)")
    args = parser.parse_args()
    settings = get_settings()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with SessionLocal() as db:
        await _ensure_admin_user(db)
        email = (args.email or settings.admin_email).lower()
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        membership = await get_membership(db, user.id)
        if not membership:
            raise RuntimeError("Admin user has no organization membership")
        project = await ensure_default_project(db, membership.org_id)
        api_key = await generate_api_key(db, user, project.id)

    print(api_key)


if __name__ == "__main__":
    asyncio.run(main())
