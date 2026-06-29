'''
This is the seed script to load the seed data from data/providers.json into the database

This uses ON CONFLICT DO NOTHING for npi so the script can be ran multiple times without duplicating data

A note - seeded providers skip the verification svc flow and get verified_at set directly since the seed data is trusted.

You can run this with python seed.py. If you do this from the docker image then leave the URL in the env as postgres host, but if you do this from just your local terminal then you'll need the localhost in the hostname.
'''
import asyncio
import json
from pathlib import Path
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.dialects.postgresql import insert
from app.models.provider import Provider
from app.database import Base
from config import settings

async def seed():
    url = settings.async_database_url

    engine = create_async_engine(url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    seed_file = Path(__file__).parent.parent.parent / "data" / "providers.seed.json"
    with open(seed_file) as f:
        data = json.load(f)

    async with session_factory() as session:
        for item in data:
            stmt = insert(Provider).values(
                npi=item["npi"],
                name=item["name"],
                taxonomy=item["taxonomy"],
                specialty=item["specialty"],
                accepting_new_patients=item.get("accepting_new_patients", True),
                region=item.get("region"),
                state=item.get("state"),
                status="active",
                verified_at=datetime.now(timezone.utc),
            ).on_conflict_do_nothing(index_elements=["npi"])
            await session.execute(stmt)
        await session.commit()

    await engine.dispose()
    print(f"Seeded {len(data)} providers")

if __name__ == "__main__":
    asyncio.run(seed())
