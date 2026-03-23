import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from hub.database import get_session
from hub.middleware.auth import get_current_api_key, require_permission
from hub.models.auth import APIKey
from hub.schemas.a2a import TaskPollResponse, TaskRespondRequest, TaskResponse, TaskSendRequest
from hub.services.registry import get_agent
from hub.services.task_manager import (
    cancel_task,
    create_task,
    get_agent_for_key,
    get_task,
    poll_tasks,
    respond_to_task,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/send", response_model=TaskResponse)
async def send_task(
    request: TaskSendRequest,
    api_key: APIKey = Depends(require_permission("can_send_tasks")),
    session: AsyncSession = Depends(get_session),
):
    """Submit a task to another PAI agent."""
    # Validate sender has a registered agent
    sender = await get_agent_for_key(session, api_key.id)
    if not sender:
        raise HTTPException(status_code=400, detail="You must register an agent before sending tasks")

    # Validate target agent exists
    target = await get_agent(session, request.to_agent_id)
    if not target or not target.is_active:
        raise HTTPException(status_code=404, detail="Target agent not found or inactive")

    # Validate target skill exists on target agent (if specified)
    if request.target_skill:
        skill_names = [s.skill_name for s in target.skills if s.visibility in ("org", "team")]
        if request.target_skill not in skill_names:
            raise HTTPException(
                status_code=400,
                detail=f"Skill '{request.target_skill}' not found on target agent",
            )

    task = await create_task(session, sender.id, request)
    return task


@router.get("/poll", response_model=TaskPollResponse)
async def poll(
    api_key: APIKey = Depends(require_permission("can_receive_tasks")),
    session: AsyncSession = Depends(get_session),
):
    """Poll for tasks assigned to this PAI agent."""
    agent = await get_agent_for_key(session, api_key.id)
    if not agent:
        raise HTTPException(status_code=400, detail="No agent registered for this API key")

    tasks = await poll_tasks(session, agent.id)
    return TaskPollResponse(tasks=tasks)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_one(
    task_id: uuid.UUID,
    api_key: APIKey = Depends(get_current_api_key),
    session: AsyncSession = Depends(get_session),
):
    """Get task status and result."""
    task = await get_task(session, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Only sender or receiver can view
    agent = await get_agent_for_key(session, api_key.id)
    if agent and task.from_agent_id != agent.id and task.to_agent_id != agent.id:
        raise HTTPException(status_code=403, detail="Not authorized to view this task")

    return task


@router.post("/{task_id}/respond", response_model=TaskResponse)
async def respond(
    task_id: uuid.UUID,
    request: TaskRespondRequest,
    api_key: APIKey = Depends(require_permission("can_receive_tasks")),
    session: AsyncSession = Depends(get_session),
):
    """Submit a response to a received task."""
    agent = await get_agent_for_key(session, api_key.id)
    if not agent:
        raise HTTPException(status_code=400, detail="No agent registered for this API key")

    task = await respond_to_task(
        session,
        task_id,
        agent.id,
        status=request.status,
        output_data=request.output_data,
        error_message=request.error_message,
        message=request.message,
    )
    if not task:
        raise HTTPException(status_code=404, detail="Task not found or not assigned to you")
    return task


@router.post("/{task_id}/cancel", response_model=TaskResponse)
async def cancel(
    task_id: uuid.UUID,
    api_key: APIKey = Depends(get_current_api_key),
    session: AsyncSession = Depends(get_session),
):
    """Cancel a pending task (sender only)."""
    agent = await get_agent_for_key(session, api_key.id)
    if not agent:
        raise HTTPException(status_code=400, detail="No agent registered for this API key")

    task = await cancel_task(session, task_id, agent.id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found, not yours, or already completed")
    return task
