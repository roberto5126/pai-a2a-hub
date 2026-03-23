import uuid
from datetime import datetime

from sqlalchemy import JSON, Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from hub.models.base import Base, TimestampMixin, new_uuid


class Agent(Base, TimestampMixin):
    __tablename__ = "agents"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    api_key_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("api_keys.id"), index=True)
    user_name: Mapped[str] = mapped_column(String(255))
    user_email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    version: Mapped[str] = mapped_column(String(20), default="1.0.0")

    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_heartbeat: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    skills: Mapped[list["AgentSkill"]] = relationship(
        back_populates="agent", cascade="all, delete-orphan"
    )


class AgentSkill(Base, TimestampMixin):
    __tablename__ = "agent_skills"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=new_uuid)
    agent_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"), index=True)

    skill_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text)
    tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), default="org")  # org, team, private
    allowed_callers: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    agent: Mapped["Agent"] = relationship(back_populates="skills")
