from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from hub.models.agent import Agent, AgentSkill
from hub.schemas.discovery import CapabilitiesResponse, DiscoverResponse, SkillMatch


async def search_skills(session: AsyncSession, query: str, limit: int = 20) -> DiscoverResponse:
    """Search skills across all agents using keyword matching on descriptions and tags."""
    query_lower = query.lower()
    keywords = query_lower.split()

    # Build a relevance score: count how many keywords appear in description + skill_name
    # Simple approach: ILIKE matching on description and tags
    stmt = (
        select(AgentSkill, Agent)
        .join(Agent, AgentSkill.agent_id == Agent.id)
        .where(Agent.is_active == True)
        .where(AgentSkill.visibility.in_(["org", "team"]))
    )

    # Filter: at least one keyword must match description, skill_name, or tags
    from sqlalchemy import or_

    keyword_filters = []
    for kw in keywords:
        keyword_filters.append(AgentSkill.description.ilike(f"%{kw}%"))
        keyword_filters.append(AgentSkill.skill_name.ilike(f"%{kw}%"))

    if keyword_filters:
        stmt = stmt.where(or_(*keyword_filters))

    result = await session.execute(stmt.limit(limit))
    rows = result.all()

    matches = []
    for skill, agent in rows:
        # Simple relevance: count keyword hits in description + skill_name
        text = f"{skill.description} {skill.skill_name}".lower()
        tag_text = " ".join(skill.tags or []).lower()
        hits = sum(1 for kw in keywords if kw in text or kw in tag_text)
        score = hits / len(keywords) if keywords else 0.0

        matches.append(
            SkillMatch(
                agent_id=agent.id,
                agent_name=agent.name,
                skill_name=skill.skill_name,
                description=skill.description,
                tags=skill.tags,
                relevance_score=round(score, 2),
            )
        )

    matches.sort(key=lambda m: m.relevance_score, reverse=True)
    return DiscoverResponse(results=matches[:limit], total=len(matches))


async def get_capabilities(session: AsyncSession) -> CapabilitiesResponse:
    """List all unique tags and counts across the organization."""
    # Count distinct agents
    agent_count = await session.execute(
        select(func.count(distinct(Agent.id))).where(Agent.is_active == True)
    )
    total_agents = agent_count.scalar() or 0

    # Count skills and get unique tags
    skill_count = await session.execute(
        select(func.count(AgentSkill.id))
        .join(Agent)
        .where(Agent.is_active == True, AgentSkill.visibility.in_(["org", "team"]))
    )
    total_skills = skill_count.scalar() or 0

    # Get all tags (flatten JSON arrays in Python for cross-DB compat)
    tags_result = await session.execute(
        select(AgentSkill.tags)
        .join(Agent)
        .where(Agent.is_active == True, AgentSkill.visibility.in_(["org", "team"]))
    )
    all_tags: set[str] = set()
    for (tag_list,) in tags_result.all():
        if tag_list:
            all_tags.update(tag_list)
    tags = sorted(all_tags)

    return CapabilitiesResponse(tags=tags, total_skills=total_skills, total_agents=total_agents)
