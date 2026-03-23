import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from hub.models.agent import Agent, AgentSkill
from hub.schemas.a2a import AgentRegisterRequest


async def register_agent(
    session: AsyncSession,
    api_key_id: uuid.UUID,
    request: AgentRegisterRequest,
) -> Agent:
    """Register or update an agent card. Upserts by api_key_id."""
    result = await session.execute(
        select(Agent)
        .options(selectinload(Agent.skills))
        .where(Agent.api_key_id == api_key_id)
    )
    agent = result.scalar_one_or_none()

    if agent:
        agent.name = request.name
        agent.description = request.description
        agent.user_name = request.user_name
        agent.user_email = request.user_email
        agent.version = request.version
        agent.last_heartbeat = datetime.now(timezone.utc)
        # Replace skills
        agent.skills.clear()
    else:
        agent = Agent(
            api_key_id=api_key_id,
            name=request.name,
            description=request.description,
            user_name=request.user_name,
            user_email=request.user_email,
            version=request.version,
            last_heartbeat=datetime.now(timezone.utc),
        )
        session.add(agent)

    for skill_input in request.skills:
        skill = AgentSkill(
            skill_name=skill_input.skill_name,
            description=skill_input.description,
            tags=skill_input.tags,
            visibility=skill_input.visibility,
            allowed_callers=skill_input.allowed_callers,
        )
        agent.skills.append(skill)

    await session.commit()
    await session.refresh(agent)
    # Reload with skills
    result = await session.execute(
        select(Agent).options(selectinload(Agent.skills)).where(Agent.id == agent.id)
    )
    return result.scalar_one()


async def get_agent(session: AsyncSession, agent_id: uuid.UUID) -> Agent | None:
    result = await session.execute(
        select(Agent).options(selectinload(Agent.skills)).where(Agent.id == agent_id)
    )
    return result.scalar_one_or_none()


async def list_agents(session: AsyncSession, active_only: bool = True) -> list[Agent]:
    stmt = select(Agent).options(selectinload(Agent.skills))
    if active_only:
        stmt = stmt.where(Agent.is_active == True)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def delete_agent(
    session: AsyncSession, agent_id: uuid.UUID, api_key_id: uuid.UUID, is_admin: bool = False
) -> bool:
    agent = await get_agent(session, agent_id)
    if not agent:
        return False
    if not is_admin and agent.api_key_id != api_key_id:
        return False
    await session.delete(agent)
    await session.commit()
    return True
