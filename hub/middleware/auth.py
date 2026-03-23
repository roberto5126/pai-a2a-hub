from fastapi import Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from hub.database import get_session
from hub.models.auth import APIKey
from hub.services.auth import validate_api_key


async def get_current_api_key(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> APIKey:
    """Extract and validate the API key from the Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    raw_key = auth_header.removeprefix("Bearer ").strip()
    if not raw_key.startswith("pai_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")

    api_key = await validate_api_key(session, raw_key)
    if not api_key:
        raise HTTPException(status_code=401, detail="Invalid or inactive API key")

    return api_key


def require_permission(permission: str):
    """Dependency factory that checks a specific permission on the API key."""

    async def check(api_key: APIKey = Depends(get_current_api_key)) -> APIKey:
        if not getattr(api_key, permission, False):
            raise HTTPException(
                status_code=403, detail=f"API key lacks permission: {permission}"
            )
        return api_key

    return check


def require_role(role: str):
    """Dependency factory that checks the API key role."""

    async def check(api_key: APIKey = Depends(get_current_api_key)) -> APIKey:
        if api_key.role != role and api_key.role != "admin":
            raise HTTPException(status_code=403, detail=f"Requires role: {role}")
        return api_key

    return check
