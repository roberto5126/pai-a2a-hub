from fastapi import APIRouter, Request

from hub.config import settings

router = APIRouter()


@router.get("/.well-known/agent.json")
async def agent_card(request: Request):
    """Hub's own A2A Agent Card."""
    base_url = str(request.base_url).rstrip("/")
    return {
        "name": settings.hub_name,
        "description": "Centralized A2A hub for connecting PAI instances across an organization",
        "url": base_url,
        "version": "0.1.0",
        "capabilities": [
            {"name": "agent-registry", "description": "Register and discover PAI agents"},
            {"name": "task-routing", "description": "Route tasks between PAI instances"},
            {"name": "skill-discovery", "description": "Search skills across the organization"},
        ],
        "authentication": {"type": "bearer", "prefix": "pai_"},
    }
