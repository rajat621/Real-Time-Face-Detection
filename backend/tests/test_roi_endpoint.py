from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from types import SimpleNamespace
from uuid import UUID

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.session import get_async_session
from app.main import app


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def scalar_one(self):
        return len(self.rows)

    def scalars(self):
        return SimpleNamespace(all=lambda: self.rows)


class FakeSession:
    def __init__(self, rows):
        self.rows = rows

    async def execute(self, stmt):
        return FakeResult(self.rows)


def test_roi_endpoint_returns_expected_shape():
    session_id = "12345678-1234-5678-1234-567812345678"
    rows = [
        SimpleNamespace(
            id=1,
            session_id=UUID(session_id),
            frame_index=7,
            timestamp=datetime.now(timezone.utc),
            x_min=10,
            y_min=20,
            x_max=110,
            y_max=220,
            width=100,
            height=200,
            confidence=0.99,
            frame_width=640,
            frame_height=480,
        )
    ]

    async def override_db():
        yield FakeSession(rows)

    async def run_request():
        app.dependency_overrides[get_async_session] = override_db
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://testserver") as async_client:
            return await async_client.get("/roi", params={"session_id": session_id, "limit": 50, "offset": 0})

    response = asyncio.run(run_request())
    app.dependency_overrides.clear()

    assert response.status_code == 200
    payload = response.json()
    assert payload["session_id"] == session_id
    assert payload["total"] == 1
    assert payload["limit"] == 50
    assert payload["offset"] == 0
    assert len(payload["items"]) == 1
    assert payload["items"][0]["x_min"] == 10
