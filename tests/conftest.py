import asyncio
import uuid
from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from hub.database import get_session
from hub.main import app
from hub.models.base import Base
from hub.services.auth import create_api_key

# Use SQLite for tests (no PostgreSQL needed)
TEST_DATABASE_URL = "sqlite+aiosqlite:///test.db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def admin_key() -> tuple[str, uuid.UUID]:
    """Create an admin API key and return (full_key, key_id)."""
    async with TestingSessionLocal() as session:
        api_key, full_key = await create_api_key(session, name="Test Admin", role="admin")
        return full_key, api_key.id


@pytest.fixture
async def agent_key() -> tuple[str, uuid.UUID]:
    """Create an agent API key and return (full_key, key_id)."""
    async with TestingSessionLocal() as session:
        api_key, full_key = await create_api_key(session, name="Test Agent", role="agent")
        return full_key, api_key.id


@pytest.fixture
async def second_agent_key() -> tuple[str, uuid.UUID]:
    """Create a second agent API key."""
    async with TestingSessionLocal() as session:
        api_key, full_key = await create_api_key(session, name="Second Agent", role="agent")
        return full_key, api_key.id


def auth_headers(api_key: str) -> dict:
    return {"Authorization": f"Bearer {api_key}"}
