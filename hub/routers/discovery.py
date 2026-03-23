from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from hub.database import get_session
from hub.middleware.auth import require_permission
from hub.models.auth import APIKey
from hub.schemas.discovery import CapabilitiesResponse, DiscoverResponse
from hub.services.discovery import get_capabilities, search_skills

router = APIRouter(prefix="/discover", tags=["discovery"])


@router.get("", response_model=DiscoverResponse)
async def discover(
    q: str = Query(..., description="Search query for skills"),
    limit: int = Query(20, ge=1, le=100),
    api_key: APIKey = Depends(require_permission("can_discover")),
    session: AsyncSession = Depends(get_session),
):
    """Search for skills across all registered PAI agents."""
    return await search_skills(session, q, limit)


@router.get("/capabilities", response_model=CapabilitiesResponse)
async def capabilities(
    api_key: APIKey = Depends(require_permission("can_discover")),
    session: AsyncSession = Depends(get_session),
):
    """List all unique skill tags in the organization."""
    return await get_capabilities(session)
