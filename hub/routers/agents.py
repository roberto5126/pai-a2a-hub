import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from hub.database import get_session
from hub.middleware.auth import get_current_api_key, require_permission
from hub.models.auth import APIKey
from hub.schemas.a2a import AgentRegisterRequest, AgentResponse
from hub.services.registry import delete_agent, get_agent, list_agents, register_agent

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/register", response_model=AgentResponse)
async def register(
    request: AgentRegisterRequest,
    api_key: APIKey = Depends(require_permission("can_register")),
    session: AsyncSession = Depends(get_session),
):
    """Register or update this PAI's agent card and skills."""
    agent = await register_agent(session, api_key.id, request)
    return agent


@router.get("", response_model=list[AgentResponse])
async def list_all(
    api_key: APIKey = Depends(get_current_api_key),
    session: AsyncSession = Depends(get_session),
):
    """List all registered agents."""
    return await list_agents(session)


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_one(
    agent_id: uuid.UUID,
    api_key: APIKey = Depends(get_current_api_key),
    session: AsyncSession = Depends(get_session),
):
    """Get a specific agent's card."""
    agent = await get_agent(session, agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@router.delete("/{agent_id}")
async def remove(
    agent_id: uuid.UUID,
    api_key: APIKey = Depends(get_current_api_key),
    session: AsyncSession = Depends(get_session),
):
    """Deregister an agent (owner or admin only)."""
    is_admin = api_key.role == "admin"
    deleted = await delete_agent(session, agent_id, api_key.id, is_admin)
    if not deleted:
        raise HTTPException(status_code=404, detail="Agent not found or not authorized")
    return {"status": "deleted"}
