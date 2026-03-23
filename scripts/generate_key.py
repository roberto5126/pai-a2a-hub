"""Generate an API key for a new PAI user."""
import asyncio
import sys

from hub.database import async_session, engine
from hub.services.auth import create_api_key


async def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/generate_key.py <name> [role]")
        print("  name: Human-friendly name (e.g., \"Roberto's PAI\")")
        print("  role: agent (default), admin, or readonly")
        sys.exit(1)

    name = sys.argv[1]
    role = sys.argv[2] if len(sys.argv) > 2 else "agent"

    async with async_session() as session:
        api_key, full_key = await create_api_key(session, name=name, role=role)
        print(f"\n{'='*60}")
        print(f"API key created for: {name}")
        print(f"{'='*60}")
        print(f"Key ID:  {api_key.id}")
        print(f"Role:    {role}")
        print(f"API Key: {full_key}")
        print(f"{'='*60}")
        print(f"\nSave this key — it will NOT be shown again.\n")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
