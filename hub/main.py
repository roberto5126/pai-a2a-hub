import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hub.config import settings
from hub.database import async_session, engine
from hub.models import Base
from hub.routers import admin, agents, discovery, tasks, wellknown
from hub.services.auth import create_api_key
from hub.services.task_manager import expire_stale_tasks


async def task_expiry_loop():
    """Background task that expires stale tasks periodically."""
    while True:
        try:
            async with async_session() as session:
                count = await expire_stale_tasks(session)
                if count:
                    print(f"Expired {count} stale tasks")
        except Exception as e:
            print(f"Task expiry error: {e}")
        await asyncio.sleep(settings.task_expiry_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (idempotent)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Start background task expiry
    expiry_task = asyncio.create_task(task_expiry_loop())
    yield
    expiry_task.cancel()
    try:
        await expiry_task
    except asyncio.CancelledError:
        pass


app = FastAPI(
    title=settings.hub_name,
    description="Centralized A2A hub for connecting PAI instances across an organization",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(wellknown.router)
app.include_router(agents.router)
app.include_router(tasks.router)
app.include_router(discovery.router)
app.include_router(admin.router)


@app.get("/health")
async def health():
    return {"status": "ok", "hub": settings.hub_name}


@app.post("/setup/seed")
async def seed():
    """One-time seed: create admin API key. Only works if no keys exist yet."""
    async with async_session() as session:
        from sqlalchemy import select, func
        from hub.models.auth import APIKey
        count = await session.execute(select(func.count(APIKey.id)))
        if (count.scalar() or 0) > 0:
            return {"error": "Database already seeded. Use /admin/keys to create more."}

        api_key, full_key = await create_api_key(session, name="Admin", role="admin")
        return {
            "message": "Admin key created. Save it — shown only once.",
            "key_id": str(api_key.id),
            "api_key": full_key,
        }
