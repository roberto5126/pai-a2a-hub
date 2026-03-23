import pytest
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_register_agent(client, agent_key):
    key, key_id = agent_key
    resp = await client.post(
        "/agents/register",
        headers=auth_headers(key),
        json={
            "name": "Roberto's PAI",
            "description": "Security research and AI infrastructure",
            "user_name": "Roberto",
            "skills": [
                {
                    "skill_name": "Research",
                    "description": "Comprehensive research with multi-agent parallel research",
                    "tags": ["research", "analysis"],
                    "visibility": "org",
                },
                {
                    "skill_name": "Security",
                    "description": "Security analysis and penetration testing",
                    "tags": ["security", "pentest"],
                    "visibility": "org",
                },
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Roberto's PAI"
    assert len(data["skills"]) == 2


@pytest.mark.asyncio
async def test_register_agent_upserts(client, agent_key):
    key, key_id = agent_key
    # Register once
    await client.post(
        "/agents/register",
        headers=auth_headers(key),
        json={
            "name": "PAI v1",
            "description": "Version 1",
            "user_name": "Roberto",
            "skills": [{"skill_name": "Research", "description": "Research stuff"}],
        },
    )
    # Register again — should upsert
    resp = await client.post(
        "/agents/register",
        headers=auth_headers(key),
        json={
            "name": "PAI v2",
            "description": "Version 2",
            "user_name": "Roberto",
            "skills": [
                {"skill_name": "Security", "description": "Security stuff"},
            ],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "PAI v2"
    assert len(data["skills"]) == 1
    assert data["skills"][0]["skill_name"] == "Security"

    # Should still be only one agent
    list_resp = await client.get("/agents", headers=auth_headers(key))
    assert len(list_resp.json()) == 1


@pytest.mark.asyncio
async def test_list_agents(client, agent_key):
    key, key_id = agent_key
    await client.post(
        "/agents/register",
        headers=auth_headers(key),
        json={
            "name": "Test PAI",
            "description": "Test",
            "user_name": "Test User",
        },
    )
    resp = await client.get("/agents", headers=auth_headers(key))
    assert resp.status_code == 200
    assert len(resp.json()) >= 1


@pytest.mark.asyncio
async def test_get_agent(client, agent_key):
    key, key_id = agent_key
    reg = await client.post(
        "/agents/register",
        headers=auth_headers(key),
        json={
            "name": "Test PAI",
            "description": "Test",
            "user_name": "Test User",
        },
    )
    agent_id = reg.json()["id"]
    resp = await client.get(f"/agents/{agent_id}", headers=auth_headers(key))
    assert resp.status_code == 200
    assert resp.json()["id"] == agent_id


@pytest.mark.asyncio
async def test_delete_agent(client, agent_key):
    key, key_id = agent_key
    reg = await client.post(
        "/agents/register",
        headers=auth_headers(key),
        json={
            "name": "Doomed PAI",
            "description": "Will be deleted",
            "user_name": "Test User",
        },
    )
    agent_id = reg.json()["id"]
    resp = await client.delete(f"/agents/{agent_id}", headers=auth_headers(key))
    assert resp.status_code == 200

    # Verify it's gone
    get_resp = await client.get(f"/agents/{agent_id}", headers=auth_headers(key))
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_without_key(client):
    resp = await client.get("/agents")
    assert resp.status_code == 401
