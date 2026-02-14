"""Pytest configuration and shared fixtures."""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_pool():
    """Mock asyncpg pool for database operations."""
    pool = MagicMock()
    connection = AsyncMock()
    transaction = AsyncMock()

    # Configure the connection to return itself for async context manager
    connection.__aenter__ = AsyncMock(return_value=connection)
    connection.__aexit__ = AsyncMock(return_value=None)

    # Configure the transaction as a sync callable returning an async context manager
    transaction.__aenter__ = AsyncMock(return_value=None)
    transaction.__aexit__ = AsyncMock(return_value=None)
    connection.transaction = MagicMock(return_value=transaction)

    # Configure pool.acquire()
    pool.acquire.return_value.__aenter__ = AsyncMock(return_value=connection)
    pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

    return pool
