"""Seed the database with an initial admin API key."""
import asyncio
import sys

from hub.database import async_session, engine
from hub.models import Base
from hub.services.auth import create_api_key


async def main():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create admin key
    async with async_session() as session:
        api_key, full_key = await create_api_key(
            session,
            name="Admin",
            role="admin",
        )
        print(f"\n{'='*60}")
        print(f"Admin API key created successfully!")
        print(f"{'='*60}")
        print(f"Key ID:  {api_key.id}")
        print(f"API Key: {full_key}")
        print(f"{'='*60}")
        print(f"\nSave this key — it will NOT be shown again.\n")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
