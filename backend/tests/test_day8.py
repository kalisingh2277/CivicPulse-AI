from uuid import uuid4

import httpx
import pytest
from sqlalchemy import text

from app.core.db import session_factory
from app.core.redis import redis_client
from app.main import app
from app.models.complaint import Complaint
from app.services.otp import _key
from app.services.pipeline import run_pipeline

pytestmark = pytest.mark.integration

BLR = (77.5946, 12.9716)


@pytest.fixture(autouse=True)
async def _reset_rate_limits() -> None:
    keys = await redis_client.keys("rl:*")
    if keys:
        await redis_client.delete(*keys)


def _client() -> httpx.AsyncClient:
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def _auth(t: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {t}"}


async def _citizen(client: httpx.AsyncClient) -> str:
    email = f"cit+{uuid4().hex[:8]}@example.com"
    pw = "supersecret123"
    await client.post(
        "/api/v1/auth/register", json={"email": email, "password": pw, "full_name": "C"}
    )
    otp = await redis_client.get(_key(email))
    await client.post("/api/v1/auth/verify-email", json={"email": email, "otp": otp})
    return (await client.post("/api/v1/auth/login", json={"email": email, "password": pw})).json()[
        "access_token"
    ]


async def _admin(client: httpx.AsyncClient) -> str:
    return (
        await client.post(
            "/api/v1/auth/login",
            json={"email": "admin@civicpulse.gov.in", "password": "civicpulse123"},
        )
    ).json()["access_token"]


async def _file_and_process(client: httpx.AsyncClient, token: str, desc: str) -> str:
    cid = (
        await client.post(
            "/api/v1/complaints",
            headers=_auth(token),
            json={"description": desc, "location": {"type": "Point", "coordinates": list(BLR)}},
        )
    ).json()["id"]
    await run_pipeline(cid)
    return cid


async def test_citizen_can_confirm_and_reopen() -> None:
    async with _client() as client:
        token = await _citizen(client)
        cid = await _file_and_process(client, token, "Streetlight out for confirm test")
        async with session_factory() as db:
            complaint = await db.get(Complaint, cid)
            issue_id = complaint.issue_id
            # force the issue into 'resolved' so the citizen can confirm/reopen
            await db.execute(
                text("UPDATE issues SET status='resolved', resolved_at=now() WHERE id=:i"),
                {"i": issue_id},
            )
            await db.commit()

        reopen = await client.post(
            f"/api/v1/issues/{issue_id}/reopen",
            headers=_auth(token),
            json={"reason": "Still not fixed, pothole remains"},
        )
        assert reopen.status_code == 200
        assert reopen.json()["status"] == "reopened"

        # resolve again, then confirm closes it
        async with session_factory() as db:
            await db.execute(
                text("UPDATE issues SET status='resolved', resolved_at=now() WHERE id=:i"),
                {"i": issue_id},
            )
            await db.commit()
        confirm = await client.post(
            f"/api/v1/issues/{issue_id}/confirm-resolution", headers=_auth(token)
        )
        assert confirm.status_code == 200
        assert confirm.json()["status"] == "closed"
