import uuid
from datetime import datetime

from pydantic import BaseModel


# --- Agent Card schemas ---

class SkillInput(BaseModel):
    skill_name: str
    description: str
    tags: list[str] | None = None
    visibility: str = "org"
    allowed_callers: list[str] | None = None


class AgentRegisterRequest(BaseModel):
    name: str
    description: str
    user_name: str
    user_email: str | None = None
    version: str = "1.0.0"
    skills: list[SkillInput] = []


class SkillResponse(BaseModel):
    id: uuid.UUID
    skill_name: str
    description: str
    tags: list[str] | None
    visibility: str

    model_config = {"from_attributes": True}


class AgentResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str
    user_name: str
    version: str
    is_active: bool
    last_heartbeat: datetime | None
    skills: list[SkillResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class AgentCardResponse(BaseModel):
    """A2A-compliant Agent Card format."""
    name: str
    description: str
    url: str
    version: str
    capabilities: list[dict]


# --- Task schemas ---

class TaskSendRequest(BaseModel):
    to_agent_id: uuid.UUID
    target_skill: str | None = None
    title: str
    description: str
    input_data: dict | None = None
    ttl_seconds: int = 3600


class TaskRespondRequest(BaseModel):
    status: str  # completed, failed, input-required
    output_data: dict | None = None
    error_message: str | None = None
    message: str | None = None


class TaskMessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    content_type: str
    created_at: datetime

    model_config = {"from_attributes": True}


class TaskResponse(BaseModel):
    id: uuid.UUID
    from_agent_id: uuid.UUID
    to_agent_id: uuid.UUID
    target_skill: str | None
    state: str
    title: str
    description: str
    input_data: dict | None
    output_data: dict | None
    error_message: str | None
    submitted_at: datetime
    started_at: datetime | None
    completed_at: datetime | None
    messages: list[TaskMessageResponse] = []

    model_config = {"from_attributes": True}


class TaskPollResponse(BaseModel):
    tasks: list[TaskResponse]
