import hashlib
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hub.models.auth import APIKey


def generate_api_key() -> tuple[str, str, str]:
    """Generate a new API key. Returns (full_key, key_hash, key_prefix)."""
    raw = secrets.token_hex(16)
    full_key = f"pai_{raw}"
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    key_prefix = full_key[:12]
    return full_key, key_hash, key_prefix


async def create_api_key(
    session: AsyncSession,
    name: str,
    role: str = "agent",
    **kwargs,
) -> tuple[APIKey, str]:
    """Create a new API key. Returns (db_record, full_key_plaintext)."""
    full_key, key_hash, key_prefix = generate_api_key()
    api_key = APIKey(
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=name,
        role=role,
        **kwargs,
    )
    session.add(api_key)
    await session.commit()
    await session.refresh(api_key)
    return api_key, full_key


async def validate_api_key(session: AsyncSession, raw_key: str) -> APIKey | None:
    """Validate an API key and return the record if valid."""
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    result = await session.execute(
        select(APIKey).where(APIKey.key_hash == key_hash, APIKey.is_active == True)
    )
    api_key = result.scalar_one_or_none()
    if api_key:
        api_key.last_used_at = datetime.now(timezone.utc)
        await session.commit()
    return api_key
