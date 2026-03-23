import pytest
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_create_api_key(client, admin_key):
    key, _ = admin_key
    resp = await client.post(
        "/admin/keys",
        headers=auth_headers(key),
        json={"name": "New Agent", "role": "agent"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "New Agent"
    assert data["role"] == "agent"
    assert "api_key" in data
    assert data["api_key"].startswith("pai_")


@pytest.mark.asyncio
async def test_list_keys(client, admin_key):
    key, _ = admin_key
    resp = await client.get("/admin/keys", headers=auth_headers(key))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_revoke_key(client, admin_key):
    key, _ = admin_key
    # Create a key to revoke
    create_resp = await client.post(
        "/admin/keys",
        headers=auth_headers(key),
        json={"name": "Doomed Key"},
    )
    key_id = create_resp.json()["id"]

    resp = await client.delete(f"/admin/keys/{key_id}", headers=auth_headers(key))
    assert resp.status_code == 200
    assert resp.json()["status"] == "revoked"


@pytest.mark.asyncio
async def test_stats(client, admin_key):
    key, _ = admin_key
    resp = await client.get("/admin/stats", headers=auth_headers(key))
    assert resp.status_code == 200
    data = resp.json()
    assert "active_agents" in data
    assert "total_skills" in data
    assert "total_tasks" in data


@pytest.mark.asyncio
async def test_non_admin_cannot_create_key(client, agent_key):
    key, _ = agent_key
    resp = await client.post(
        "/admin/keys",
        headers=auth_headers(key),
        json={"name": "Should fail"},
    )
    assert resp.status_code == 403
