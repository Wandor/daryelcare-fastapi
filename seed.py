"""Standalone seed script: creates schema and inserts sample data."""

import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
import asyncpg

load_dotenv()

DB_DIR = Path(__file__).resolve().parent / "db"


async def main():
    url = os.getenv("DATABASE_URL", "postgres://localhost:5432/readykids")
    dsn = url.replace("postgres://", "postgresql://", 1)
    conn = await asyncpg.connect(dsn)

    schema = (DB_DIR / "schema.sql").read_text()
    await conn.execute(schema)
    print("Database schema initialised")

    seed = (DB_DIR / "seed.sql").read_text()
    await conn.execute(seed)
    print("Seed data inserted")

    await conn.close()


if __name__ == "__main__":
    asyncio.run(main())
