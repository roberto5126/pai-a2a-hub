import uuid
from datetime import datetime

from pydantic import BaseModel


class APIKeyCreate(BaseModel):
    name: str
    role: str = "agent"
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 500
    can_register: bool = True
    can_discover: bool = True
    can_send_tasks: bool = True
    can_receive_tasks: bool = True


class APIKeyResponse(BaseModel):
    id: uuid.UUID
    key_prefix: str
    name: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class APIKeyCreated(APIKeyResponse):
    """Returned only on creation — includes the full key (shown once)."""
    api_key: str
