import uuid

from pydantic import BaseModel


class SkillMatch(BaseModel):
    agent_id: uuid.UUID
    agent_name: str
    skill_name: str
    description: str
    tags: list[str] | None
    relevance_score: float


class DiscoverResponse(BaseModel):
    results: list[SkillMatch]
    total: int


class CapabilitiesResponse(BaseModel):
    tags: list[str]
    total_skills: int
    total_agents: int
