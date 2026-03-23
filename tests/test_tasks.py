import pytest
from tests.conftest import auth_headers


async def register_agent(client, key, name, skills=None):
    resp = await client.post(
        "/agents/register",
        headers=auth_headers(key),
        json={
            "name": name,
            "description": f"Agent {name}",
            "user_name": name,
            "skills": skills or [
                {"skill_name": "Research", "description": "Research", "tags": ["research"], "visibility": "org"}
            ],
        },
    )
    return resp.json()


@pytest.mark.asyncio
async def test_send_task(client, agent_key, second_agent_key):
    key_a, _ = agent_key
    key_b, _ = second_agent_key

    agent_a = await register_agent(client, key_a, "Agent A")
    agent_b = await register_agent(client, key_b, "Agent B")

    resp = await client.post(
        "/tasks/send",
        headers=auth_headers(key_a),
        json={
            "to_agent_id": agent_b["id"],
            "target_skill": "Research",
            "title": "Research AI trends",
            "description": "Find the latest AI agent frameworks",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "submitted"
    assert data["to_agent_id"] == agent_b["id"]
    assert data["from_agent_id"] == agent_a["id"]


@pytest.mark.asyncio
async def test_poll_tasks(client, agent_key, second_agent_key):
    key_a, _ = agent_key
    key_b, _ = second_agent_key

    await register_agent(client, key_a, "Agent A")
    agent_b = await register_agent(client, key_b, "Agent B")

    # Send a task to B
    await client.post(
        "/tasks/send",
        headers=auth_headers(key_a),
        json={
            "to_agent_id": agent_b["id"],
            "title": "Test Task",
            "description": "Just a test",
        },
    )

    # B polls for tasks
    resp = await client.get("/tasks/poll", headers=auth_headers(key_b))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tasks"]) == 1
    assert data["tasks"][0]["title"] == "Test Task"


@pytest.mark.asyncio
async def test_respond_to_task(client, agent_key, second_agent_key):
    key_a, _ = agent_key
    key_b, _ = second_agent_key

    await register_agent(client, key_a, "Agent A")
    agent_b = await register_agent(client, key_b, "Agent B")

    # Send task
    send_resp = await client.post(
        "/tasks/send",
        headers=auth_headers(key_a),
        json={
            "to_agent_id": agent_b["id"],
            "title": "Do something",
            "description": "Please do this",
        },
    )
    task_id = send_resp.json()["id"]

    # B responds
    resp = await client.post(
        f"/tasks/{task_id}/respond",
        headers=auth_headers(key_b),
        json={
            "status": "completed",
            "output_data": {"result": "Done!"},
            "message": "Task completed successfully",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["state"] == "completed"
    assert data["output_data"]["result"] == "Done!"


@pytest.mark.asyncio
async def test_cancel_task(client, agent_key, second_agent_key):
    key_a, _ = agent_key
    key_b, _ = second_agent_key

    await register_agent(client, key_a, "Agent A")
    agent_b = await register_agent(client, key_b, "Agent B")

    send_resp = await client.post(
        "/tasks/send",
        headers=auth_headers(key_a),
        json={
            "to_agent_id": agent_b["id"],
            "title": "Cancel me",
            "description": "Will be canceled",
        },
    )
    task_id = send_resp.json()["id"]

    # A cancels
    resp = await client.post(f"/tasks/{task_id}/cancel", headers=auth_headers(key_a))
    assert resp.status_code == 200
    assert resp.json()["state"] == "canceled"


@pytest.mark.asyncio
async def test_get_task(client, agent_key, second_agent_key):
    key_a, _ = agent_key
    key_b, _ = second_agent_key

    await register_agent(client, key_a, "Agent A")
    agent_b = await register_agent(client, key_b, "Agent B")

    send_resp = await client.post(
        "/tasks/send",
        headers=auth_headers(key_a),
        json={
            "to_agent_id": agent_b["id"],
            "title": "Check me",
            "description": "Status check",
        },
    )
    task_id = send_resp.json()["id"]

    resp = await client.get(f"/tasks/{task_id}", headers=auth_headers(key_a))
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id


@pytest.mark.asyncio
async def test_cannot_send_without_registration(client, agent_key, second_agent_key):
    key_a, _ = agent_key
    key_b, _ = second_agent_key

    # Register only B
    agent_b = await register_agent(client, key_b, "Agent B")

    # A tries to send without registering
    resp = await client.post(
        "/tasks/send",
        headers=auth_headers(key_a),
        json={
            "to_agent_id": agent_b["id"],
            "title": "Should fail",
            "description": "No agent registered",
        },
    )
    assert resp.status_code == 400
