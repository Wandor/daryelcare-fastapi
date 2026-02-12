"""Async PostgreSQL connection pool using asyncpg."""

import os
import asyncpg

_pool: asyncpg.Pool | None = None


def _parse_database_url(url: str) -> dict:
    """Convert postgres:// URL to asyncpg connection kwargs."""
    url = url.replace("postgres://", "postgresql://", 1)
    return {"dsn": url}


async def init_pool():
    global _pool
    url = os.getenv("DATABASE_URL", "postgres://localhost:5432/readykids")
    _pool = await asyncpg.create_pool(**_parse_database_url(url), min_size=2, max_size=10)


async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool not initialized")
    return _pool
