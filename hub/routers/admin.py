import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from hub.database import get_session
from hub.middleware.auth import require_role
from hub.models.agent import Agent, AgentSkill
from hub.models.auth import APIKey
from hub.models.task import Task
from hub.schemas.auth import APIKeyCreate, APIKeyCreated, APIKeyResponse
from hub.services.auth import create_api_key

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/keys", response_model=APIKeyCreated)
async def create_key(
    request: APIKeyCreate,
    api_key: APIKey = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Generate a new API key for a PAI user."""
    db_key, full_key = await create_api_key(
        session,
        name=request.name,
        role=request.role,
        rate_limit_per_minute=request.rate_limit_per_minute,
        rate_limit_per_hour=request.rate_limit_per_hour,
        can_register=request.can_register,
        can_discover=request.can_discover,
        can_send_tasks=request.can_send_tasks,
        can_receive_tasks=request.can_receive_tasks,
    )
    return APIKeyCreated(
        id=db_key.id,
        key_prefix=db_key.key_prefix,
        name=db_key.name,
        role=db_key.role,
        is_active=db_key.is_active,
        created_at=db_key.created_at,
        api_key=full_key,
    )


@router.get("/keys", response_model=list[APIKeyResponse])
async def list_keys(
    api_key: APIKey = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """List all API keys."""
    result = await session.execute(select(APIKey).order_by(APIKey.created_at.desc()))
    return list(result.scalars().all())


@router.delete("/keys/{key_id}")
async def revoke_key(
    key_id: uuid.UUID,
    api_key: APIKey = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Revoke an API key."""
    result = await session.execute(select(APIKey).where(APIKey.id == key_id))
    target = result.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="API key not found")
    target.is_active = False
    await session.commit()
    return {"status": "revoked"}


@router.get("/stats")
async def stats(
    api_key: APIKey = Depends(require_role("admin")),
    session: AsyncSession = Depends(get_session),
):
    """Hub statistics."""
    agents = await session.execute(
        select(func.count(Agent.id)).where(Agent.is_active == True)
    )
    skills = await session.execute(
        select(func.count(AgentSkill.id))
        .join(Agent)
        .where(Agent.is_active == True)
    )
    tasks_total = await session.execute(select(func.count(Task.id)))
    keys = await session.execute(
        select(func.count(APIKey.id)).where(APIKey.is_active == True)
    )

    return {
        "active_agents": agents.scalar() or 0,
        "total_skills": skills.scalar() or 0,
        "total_tasks": tasks_total.scalar() or 0,
        "active_api_keys": keys.scalar() or 0,
    }
