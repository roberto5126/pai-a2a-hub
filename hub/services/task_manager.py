import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from hub.models.agent import Agent
from hub.models.task import Task, TaskMessage, TaskState
from hub.schemas.a2a import TaskSendRequest


async def create_task(
    session: AsyncSession,
    from_agent_id: uuid.UUID,
    request: TaskSendRequest,
) -> Task:
    """Submit a new task to another agent."""
    now = datetime.now(timezone.utc)
    task = Task(
        from_agent_id=from_agent_id,
        to_agent_id=request.to_agent_id,
        target_skill=request.target_skill,
        title=request.title,
        description=request.description,
        input_data=request.input_data,
        submitted_at=now,
        ttl_seconds=request.ttl_seconds,
        expires_at=now + timedelta(seconds=request.ttl_seconds),
    )
    session.add(task)
    await session.commit()
    # Reload with messages relationship
    result = await session.execute(
        select(Task).options(selectinload(Task.messages)).where(Task.id == task.id)
    )
    return result.scalar_one()


async def get_task(session: AsyncSession, task_id: uuid.UUID) -> Task | None:
    result = await session.execute(
        select(Task).options(selectinload(Task.messages)).where(Task.id == task_id)
    )
    return result.scalar_one_or_none()


async def poll_tasks(session: AsyncSession, agent_id: uuid.UUID) -> list[Task]:
    """Get all submitted tasks for an agent."""
    result = await session.execute(
        select(Task)
        .options(selectinload(Task.messages))
        .where(Task.to_agent_id == agent_id, Task.state == TaskState.SUBMITTED)
        .order_by(Task.submitted_at)
    )
    return list(result.scalars().all())


async def respond_to_task(
    session: AsyncSession,
    task_id: uuid.UUID,
    agent_id: uuid.UUID,
    status: str,
    output_data: dict | None = None,
    error_message: str | None = None,
    message: str | None = None,
) -> Task | None:
    """Update task with a response from the receiving agent."""
    task = await get_task(session, task_id)
    if not task or task.to_agent_id != agent_id:
        return None

    now = datetime.now(timezone.utc)

    if status == "completed":
        task.state = TaskState.COMPLETED
        task.output_data = output_data
        task.completed_at = now
    elif status == "failed":
        task.state = TaskState.FAILED
        task.error_message = error_message
        task.completed_at = now
    elif status == "input-required":
        task.state = TaskState.INPUT_REQUIRED
    elif status == "working":
        task.state = TaskState.WORKING
        task.started_at = task.started_at or now

    if message:
        task_message = TaskMessage(
            task_id=task_id,
            role="receiver",
            content=message,
        )
        session.add(task_message)

    await session.commit()
    # Reload with messages
    return await get_task(session, task_id)


async def cancel_task(
    session: AsyncSession, task_id: uuid.UUID, agent_id: uuid.UUID
) -> Task | None:
    """Cancel a task (only the sender can cancel)."""
    task = await get_task(session, task_id)
    if not task or task.from_agent_id != agent_id:
        return None
    if task.state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED):
        return None

    task.state = TaskState.CANCELED
    task.completed_at = datetime.now(timezone.utc)
    await session.commit()
    # Reload with messages
    return await get_task(session, task_id)


async def expire_stale_tasks(session: AsyncSession) -> int:
    """Cancel tasks that have exceeded their TTL. Returns count of expired tasks."""
    now = datetime.now(timezone.utc)
    result = await session.execute(
        update(Task)
        .where(
            Task.state.in_([TaskState.SUBMITTED, TaskState.WORKING]),
            Task.expires_at < now,
        )
        .values(
            state=TaskState.CANCELED,
            error_message="Task expired (TTL exceeded)",
            completed_at=now,
        )
        .returning(Task.id)
    )
    await session.commit()
    return len(result.all())


async def get_agent_for_key(session: AsyncSession, api_key_id: uuid.UUID) -> Agent | None:
    """Get the agent registered to an API key."""
    result = await session.execute(
        select(Agent).where(Agent.api_key_id == api_key_id, Agent.is_active == True)
    )
    return result.scalar_one_or_none()
