import pytest
from sqlalchemy import select

from app.core.settings import get_settings
from app.db.models import Org, OrgMembership, Project, RequestLog, User
from app.services.bootstrap import _ensure_admin_user


@pytest.mark.asyncio
async def test_bootstrap_creates_org_membership(client, db_session):
    settings = get_settings()
    await _ensure_admin_user(db_session)
    result = await db_session.execute(select(User).where(User.email == settings.admin_email))
    user = result.scalar_one()

    result = await db_session.execute(select(OrgMembership).where(OrgMembership.user_id == user.id))
    membership = result.scalar_one_or_none()
    assert membership is not None
    assert membership.role == "admin"

    org = await db_session.get(Org, membership.org_id)
    assert org is not None

    project_result = await db_session.execute(
        select(Project).where(Project.org_id == membership.org_id, Project.name == "default")
    )
    assert project_result.scalar_one_or_none() is not None


@pytest.mark.asyncio
async def test_usage_by_key_and_requests(client, db_session):
    settings = get_settings()
    await _ensure_admin_user(db_session)
    response = await client.post(
        "/auth/login",
        json={"email": settings.admin_email, "password": settings.admin_password},
    )
    assert response.status_code == 200
    user_id = response.json()["id"]

    membership_result = await db_session.execute(select(OrgMembership).where(OrgMembership.user_id == user_id))
    membership = membership_result.scalar_one()

    project_result = await db_session.execute(
        select(Project).where(Project.org_id == membership.org_id, Project.name == "default")
    )
    project = project_result.scalar_one()

    key_response = await client.post(
        "/keys",
        json={"project_id": project.id},
    )
    assert key_response.status_code == 200
    key_id = key_response.json()["id"]

    log = RequestLog(
        org_id=membership.org_id,
        project_id=project.id,
        api_key_id=key_id,
        owner_user_id=user_id,
        provider="openai",
        model="gpt-4o-mini",
        endpoint="chat",
        status=200,
        latency_ms=120,
        prompt_tokens=5,
        completion_tokens=5,
        total_tokens=10,
        cost_usd=0.01,
    )
    db_session.add(log)
    await db_session.commit()

    usage_response = await client.get(f"/usage/by-key?project_id={project.id}")
    assert usage_response.status_code == 200
    items = usage_response.json()["items"]
    assert any(item["api_key_id"] == key_id for item in items)

    requests_response = await client.get(f"/requests?project_id={project.id}")
    assert requests_response.status_code == 200
    assert len(requests_response.json()["items"]) >= 1
