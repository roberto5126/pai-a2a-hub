import pytest
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_wellknown_agent_card(client):
    resp = await client.get("/.well-known/agent.json")
    assert resp.status_code == 200
    data = resp.json()
    assert "name" in data
    assert "capabilities" in data
    assert len(data["capabilities"]) == 3
