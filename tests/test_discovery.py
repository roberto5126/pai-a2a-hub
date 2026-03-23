import pytest
from tests.conftest import auth_headers


@pytest.mark.asyncio
async def test_discover_skills(client, agent_key):
    key, _ = agent_key
    # Register with skills
    await client.post(
        "/agents/register",
        headers=auth_headers(key),
        json={
            "name": "Test PAI",
            "description": "Test agent",
            "user_name": "Tester",
            "skills": [
                {
                    "skill_name": "Security",
                    "description": "Security analysis and penetration testing",
                    "tags": ["security", "pentest"],
                },
                {
                    "skill_name": "Research",
                    "description": "Comprehensive research and content extraction",
                    "tags": ["research", "analysis"],
                },
            ],
        },
    )

    # Search for security
    resp = await client.get(
        "/discover", params={"q": "security"}, headers=auth_headers(key)
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    skill_names = [r["skill_name"] for r in data["results"]]
    assert "Security" in skill_names


@pytest.mark.asyncio
async def test_discover_no_results(client, agent_key):
    key, _ = agent_key
    resp = await client.get(
        "/discover", params={"q": "nonexistent_xyz"}, headers=auth_headers(key)
    )
    assert resp.status_code == 200
    assert resp.json()["total"] == 0


@pytest.mark.asyncio
async def test_capabilities(client, agent_key):
    key, _ = agent_key
    await client.post(
        "/agents/register",
        headers=auth_headers(key),
        json={
            "name": "Test PAI",
            "description": "Test",
            "user_name": "Tester",
            "skills": [
                {"skill_name": "Research", "description": "Research", "tags": ["research", "analysis"]},
            ],
        },
    )
    resp = await client.get("/discover/capabilities", headers=auth_headers(key))
    assert resp.status_code == 200
    data = resp.json()
    assert data["total_agents"] >= 1
    assert data["total_skills"] >= 1
