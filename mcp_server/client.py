"""HTTP client for the PAI A2A Hub API."""
import json
import os

import httpx


class HubClient:
    def __init__(
        self,
        hub_url: str | None = None,
        api_key: str | None = None,
    ):
        self.hub_url = (hub_url or os.environ.get("A2A_HUB_URL", "")).rstrip("/")
        self.api_key = api_key or os.environ.get("A2A_API_KEY", "")
        if not self.hub_url:
            raise ValueError("A2A_HUB_URL is required")
        if not self.api_key:
            raise ValueError("A2A_API_KEY is required")

    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"}

    async def register(self, payload: dict) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.hub_url}/agents/register",
                json=payload,
                headers=self._headers,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    async def list_agents(self) -> list[dict]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.hub_url}/agents",
                headers=self._headers,
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()

    async def discover(self, query: str, limit: int = 20) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.hub_url}/discover",
                params={"q": query, "limit": limit},
                headers=self._headers,
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()

    async def send_task(
        self,
        to_agent_id: str,
        title: str,
        description: str,
        target_skill: str | None = None,
        input_data: dict | None = None,
        ttl_seconds: int = 3600,
    ) -> dict:
        payload = {
            "to_agent_id": to_agent_id,
            "title": title,
            "description": description,
            "ttl_seconds": ttl_seconds,
        }
        if target_skill:
            payload["target_skill"] = target_skill
        if input_data:
            payload["input_data"] = input_data

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.hub_url}/tasks/send",
                json=payload,
                headers=self._headers,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()

    async def check_task(self, task_id: str) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.hub_url}/tasks/{task_id}",
                headers=self._headers,
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()

    async def poll_incoming(self) -> dict:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{self.hub_url}/tasks/poll",
                headers=self._headers,
                timeout=15,
            )
            resp.raise_for_status()
            return resp.json()

    async def respond_task(
        self,
        task_id: str,
        status: str,
        output_data: dict | None = None,
        error_message: str | None = None,
        message: str | None = None,
    ) -> dict:
        payload: dict = {"status": status}
        if output_data:
            payload["output_data"] = output_data
        if error_message:
            payload["error_message"] = error_message
        if message:
            payload["message"] = message

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self.hub_url}/tasks/{task_id}/respond",
                json=payload,
                headers=self._headers,
                timeout=30,
            )
            resp.raise_for_status()
            return resp.json()
