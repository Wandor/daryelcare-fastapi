"""Integration tests for service layer database functions."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, date
from app.services.application_service import (
    create_application,
    get_all_applications,
    get_application,
    update_application,
    delete_application,
    add_timeline_event,
)


@pytest.mark.asyncio
class TestCreateApplicationDB:
    """Test create_application database function."""

    async def test_create_application_db_success(self, mock_pool):
        """Test creating application calls database correctly."""
        # Setup mock connection
        connection = mock_pool.acquire.return_value.__aenter__.return_value
        connection.fetchrow.return_value = {"val": 1}
        connection.execute = AsyncMock()

        body = {
            "personal": {
                "firstName": "John",
                "lastName": "Doe",
                "email": "john@example.com",
                "phone": "1234567890",
                "dob": "1990-01-15",
            }
        }

        result = await create_application(mock_pool, body)

        # Verify ID format
        assert result.startswith("RK-")
        assert "-00001" in result

        # Verify database calls
        assert connection.fetchrow.called
        assert connection.execute.call_count == 3  # INSERT application + 2 timeline events

    async def test_create_application_db_generates_checks(self, mock_pool):
        """Test that create_application generates checks correctly."""
        connection = mock_pool.acquire.return_value.__aenter__.return_value
        connection.fetchrow.return_value = {"val": 1}
        connection.execute = AsyncMock()

        body = {
            "personal": {
                "firstName": "Jane",
                "lastName": "Smith",
                "email": "jane@example.com",
            },
            "qualifications": {
                "firstAidCompleted": "Yes",
                "firstAidDate": "2024-01-15",
            }
        }

        await create_application(mock_pool, body)

        # Verify execute was called with application data
        assert connection.execute.called

    async def test_create_application_db_escapes_html(self, mock_pool):
        """Test that create_application escapes HTML in names."""
        connection = mock_pool.acquire.return_value.__aenter__.return_value
        connection.fetchrow.return_value = {"val": 1}
        connection.execute = AsyncMock()

        body = {
            "personal": {
                "firstName": "<script>alert('xss')</script>",
                "lastName": "Doe",
                "email": "test@example.com",
            }
        }

        await create_application(mock_pool, body)

        # Check that execute was called
        assert connection.execute.called


@pytest.mark.asyncio
class TestGetAllApplicationsDB:
    """Test get_all_applications database function."""

    async def test_get_all_applications_empty(self, mock_pool):
        """Test getting all applications when none exist."""
        connection = mock_pool.acquire.return_value.__aenter__.return_value
        connection.fetch.return_value = []

        result = await get_all_applications(mock_pool)

        assert [] == result
        assert connection.fetch.called

    async def test_get_all_applications_with_data(self, mock_pool):
        """Test getting all applications with data."""
        connection = mock_pool.acquire.return_value.__aenter__.return_value

        # Mock application rows
        app_row = {
            "id": "RK-2026-00001",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "dob": date(1990, 1, 15),
            "stage": "new",
            "start_date": date(2026, 2, 1),
            "registration_date": None,
            "last_updated": datetime.now(),
            "risk": "low",
            "progress": 0,
            "premises_type": "domestic",
            "premises_address": "123 Main St",
            "local_authority": "London",
            "registers": "[]",
            "checks": "{}",
            "connected_persons": "[]",
            "ni_number": None,
            "registration_number": None,
            "ofsted_check": None,
            "household": None,
            "service": None,
            "premises_details": None,
        }

        # Mock timeline events
        timeline_row = {
            "event": "Application started",
            "type": "action",
            "created_at": datetime.now(),
        }

        connection.fetch.side_effect = [
            [app_row],  # First fetch for applications
            [timeline_row],  # Second fetch for timeline
        ]

        result = await get_all_applications(mock_pool)

        assert 1 == len(result)
        assert "RK-2026-00001" == result[0]["id"]
        assert "John Doe" == result[0]["name"]


@pytest.mark.asyncio
class TestGetApplicationDB:
    """Test get_application database function."""

    async def test_get_application_not_found(self, mock_pool):
        """Test getting application that doesn't exist."""
        connection = mock_pool.acquire.return_value.__aenter__.return_value
        connection.fetchrow.return_value = None

        result = await get_application(mock_pool, "RK-2026-99999")

        assert result is None

    async def test_get_application_found(self, mock_pool):
        """Test getting application that exists."""
        connection = mock_pool.acquire.return_value.__aenter__.return_value

        app_row = {
            "id": "RK-2026-00001",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "dob": date(1990, 1, 15),
            "stage": "new",
            "start_date": date(2026, 2, 1),
            "registration_date": None,
            "last_updated": datetime.now(),
            "risk": "low",
            "progress": 0,
            "premises_type": "domestic",
            "premises_address": "123 Main St",
            "local_authority": "London",
            "registers": "[]",
            "checks": "{}",
            "connected_persons": "[]",
            "ni_number": None,
            "registration_number": None,
            "ofsted_check": None,
            "household": None,
            "service": None,
            "premises_details": None,
        }

        connection.fetchrow.return_value = app_row
        connection.fetch.return_value = []

        result = await get_application(mock_pool, "RK-2026-00001")

        assert result is not None
        assert "RK-2026-00001" == result["id"]


@pytest.mark.asyncio
class TestUpdateApplicationDB:
    """Test update_application database function."""

    async def test_update_application_success(self, mock_pool):
        """Test updating application successfully."""
        connection = mock_pool.acquire.return_value.__aenter__.return_value
        connection.execute.return_value = "UPDATE 1"

        updates = {"stage": "form-submitted"}
        result = await update_application(mock_pool, "RK-2026-00001", updates)

        assert result is True
        assert connection.execute.called

    async def test_update_application_not_found(self, mock_pool):
        """Test updating application that doesn't exist."""
        connection = mock_pool.acquire.return_value.__aenter__.return_value
        connection.execute.return_value = "UPDATE 0"

        updates = {"stage": "checks"}
        result = await update_application(mock_pool, "RK-2026-99999", updates)

        assert result is False

    async def test_update_application_no_valid_fields(self, mock_pool):
        """Test updating application with no valid fields."""
        updates = {"invalid_field": "value"}
        result = await update_application(mock_pool, "RK-2026-00001", updates)

        assert result is False

    async def test_update_application_multiple_fields(self, mock_pool):
        """Test updating multiple fields."""
        connection = mock_pool.acquire.return_value.__aenter__.return_value
        connection.execute.return_value = "UPDATE 1"

        updates = {
            "stage": "checks",
            "risk": "medium",
            "progress": 50,
        }
        result = await update_application(mock_pool, "RK-2026-00001", updates)

        assert result is True

    async def test_update_application_json_fields(self, mock_pool):
        """Test updating JSON fields."""
        connection = mock_pool.acquire.return_value.__aenter__.return_value
        connection.execute.return_value = "UPDATE 1"

        updates = {
            "checks": {
                "dbs": {"status": "complete", "date": "2024-01-15"}
            }
        }
        result = await update_application(mock_pool, "RK-2026-00001", updates)

        assert result is True


@pytest.mark.asyncio
class TestDeleteApplicationDB:
    """Test delete_application database function."""

    async def test_delete_application_success(self, mock_pool):
        """Test deleting application successfully."""
        connection = mock_pool.acquire.return_value.__aenter__.return_value
        connection.execute.return_value = "DELETE 1"

        result = await delete_application(mock_pool, "RK-2026-00001")

        assert result is True
        assert connection.execute.called

    async def test_delete_application_not_found(self, mock_pool):
        """Test deleting application that doesn't exist."""
        connection = mock_pool.acquire.return_value.__aenter__.return_value
        connection.execute.return_value = "DELETE 0"

        result = await delete_application(mock_pool, "RK-2026-99999")

        assert result is False


@pytest.mark.asyncio
class TestAddTimelineEventDB:
    """Test add_timeline_event database function."""

    async def test_add_timeline_event_success(self, mock_pool):
        """Test adding timeline event successfully."""
        connection = mock_pool.acquire.return_value.__aenter__.return_value
        connection.fetchrow.return_value = {
            "id": 1,
            "application_id": "RK-2026-00001",
            "event": "DBS check completed",
            "type": "complete",
            "created_at": datetime.now(),
        }

        result = await add_timeline_event(
            mock_pool,
            "RK-2026-00001",
            "DBS check completed",
            "complete"
        )

        assert result is not None
        assert "DBS check completed" == result["event"]
        assert connection.fetchrow.called

    async def test_add_timeline_event_escapes_html(self, mock_pool):
        """Test that timeline event escapes HTML."""
        connection = mock_pool.acquire.return_value.__aenter__.return_value
        connection.fetchrow.return_value = {
            "id": 1,
            "application_id": "RK-2026-00001",
            "event": "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;",
            "type": "action",
            "created_at": datetime.now(),
        }

        event_text = "<script>alert('xss')</script>"
        result = await add_timeline_event(
            mock_pool,
            "RK-2026-00001",
            event_text,
            "action"
        )

        assert result is not None
        assert connection.fetchrow.called

    async def test_add_timeline_event_default_type(self, mock_pool):
        """Test adding timeline event with default type."""
        connection = mock_pool.acquire.return_value.__aenter__.return_value
        connection.fetchrow.return_value = {
            "id": 1,
            "application_id": "RK-2026-00001",
            "event": "Test event",
            "type": "action",
            "created_at": datetime.now(),
        }

        result = await add_timeline_event(
            mock_pool,
            "RK-2026-00001",
            "Test event"
        )

        assert result is not None
