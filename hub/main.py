import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from hub.config import settings
from hub.database import async_session
from hub.routers import admin, agents, discovery, tasks, wellknown
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
