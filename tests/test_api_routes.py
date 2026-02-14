"""API route tests using TestClient."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """Create a TestClient instance."""
    return TestClient(app)


@pytest.fixture
def mock_get_pool():
    """Mock the get_pool function."""
    with patch("app.routes.applications.get_pool") as mock:
        yield mock


class TestHealthEndpoint:
    """Test the health check endpoint."""

    def test_health_check_success(self, client):
        """Test health endpoint returns ok status."""
        response = client.get("/health")
        assert 200 == response.status_code
        assert {"status": "ok"} == response.json()

    def test_health_check_has_security_headers(self, client):
        """Test health endpoint includes security headers."""
        response = client.get("/health")
        assert "nosniff" == response.headers["X-Content-Type-Options"]
        assert "DENY" == response.headers["X-Frame-Options"]
        assert "1; mode=block" == response.headers["X-XSS-Protection"]


class TestListApplications:
    """Test GET /api/applications/ endpoint."""

    def test_list_applications_success(self, client, mock_get_pool):
        """Test listing applications successfully."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.get_all_applications") as mock_get_all:
            mock_get_all.return_value = [
                {
                    "id": "RK-2026-00001",
                    "name": "John Doe",
                    "email": "john@example.com",
                    "stage": "new",
                },
                {
                    "id": "RK-2026-00002",
                    "name": "Jane Smith",
                    "email": "jane@example.com",
                    "stage": "form-submitted",
                }
            ]

            response = client.get("/api/applications/")
            assert 200 == response.status_code
            data = response.json()
            assert 2 == len(data)
            assert "RK-2026-00001" == data[0]["id"]

    def test_list_applications_empty(self, client, mock_get_pool):
        """Test listing applications when none exist."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.get_all_applications") as mock_get_all:
            mock_get_all.return_value = []

            response = client.get("/api/applications/")
            assert 200 == response.status_code
            assert [] == response.json()

    def test_list_applications_has_security_headers(self, client, mock_get_pool):
        """Test list endpoint includes security headers."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.get_all_applications") as mock_get_all:
            mock_get_all.return_value = []

            response = client.get("/api/applications/")
            assert "nosniff" == response.headers["X-Content-Type-Options"]
            assert "DENY" == response.headers["X-Frame-Options"]


class TestGetApplication:
    """Test GET /api/applications/{app_id} endpoint."""

    def test_get_application_success(self, client, mock_get_pool):
        """Test getting a single application successfully."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.get_application") as mock_get:
            mock_get.return_value = {
                "id": "RK-2026-00001",
                "name": "John Doe",
                "email": "john@example.com",
                "stage": "new",
            }

            response = client.get("/api/applications/RK-2026-00001")
            assert 200 == response.status_code
            data = response.json()
            assert "RK-2026-00001" == data["id"]
            assert "John Doe" == data["name"]

    def test_get_application_not_found(self, client, mock_get_pool):
        """Test getting a non-existent application."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.get_application") as mock_get:
            mock_get.return_value = None

            response = client.get("/api/applications/RK-2026-99999")
            assert 404 == response.status_code
            assert "Application not found" == response.json()["detail"]


class TestCreateApplication:
    """Test POST /api/applications/ endpoint."""

    def test_create_application_success(self, client, mock_get_pool):
        """Test creating an application successfully."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.create_application") as mock_create:
            mock_create.return_value = "RK-2026-00001"

            body = {
                "personal": {
                    "firstName": "John",
                    "lastName": "Doe",
                    "email": "john@example.com",
                }
            }

            response = client.post("/api/applications/", json=body)
            assert 201 == response.status_code
            data = response.json()
            assert "RK-2026-00001" == data["id"]
            assert "Application submitted successfully" == data["message"]

    def test_create_application_missing_first_name(self, client, mock_get_pool):
        """Test creating application with missing first name."""
        body = {
            "personal": {
                "lastName": "Doe",
                "email": "john@example.com",
            }
        }

        response = client.post("/api/applications/", json=body)
        assert 400 == response.status_code
        assert "First name, last name, and email are required" in response.json()["detail"]

    def test_create_application_missing_last_name(self, client, mock_get_pool):
        """Test creating application with missing last name."""
        body = {
            "personal": {
                "firstName": "John",
                "email": "john@example.com",
            }
        }

        response = client.post("/api/applications/", json=body)
        assert 400 == response.status_code
        assert "First name, last name, and email are required" in response.json()["detail"]

    def test_create_application_missing_email(self, client, mock_get_pool):
        """Test creating application with missing email."""
        body = {
            "personal": {
                "firstName": "John",
                "lastName": "Doe",
            }
        }

        response = client.post("/api/applications/", json=body)
        assert 400 == response.status_code
        assert "First name, last name, and email are required" in response.json()["detail"]

    def test_create_application_empty_first_name(self, client, mock_get_pool):
        """Test creating application with empty first name."""
        body = {
            "personal": {
                "firstName": "   ",
                "lastName": "Doe",
                "email": "john@example.com",
            }
        }

        response = client.post("/api/applications/", json=body)
        assert 400 == response.status_code

    def test_create_application_first_name_too_long(self, client, mock_get_pool):
        """Test creating application with first name exceeding max length."""
        body = {
            "personal": {
                "firstName": "A" * 201,
                "lastName": "Doe",
                "email": "john@example.com",
            }
        }

        response = client.post("/api/applications/", json=body)
        assert 400 == response.status_code
        assert "First name must not exceed 200 characters" in response.json()["detail"]

    def test_create_application_last_name_too_long(self, client, mock_get_pool):
        """Test creating application with last name exceeding max length."""
        body = {
            "personal": {
                "firstName": "John",
                "lastName": "B" * 201,
                "email": "john@example.com",
            }
        }

        response = client.post("/api/applications/", json=body)
        assert 400 == response.status_code
        assert "Last name must not exceed 200 characters" in response.json()["detail"]

    def test_create_application_email_too_long(self, client, mock_get_pool):
        """Test creating application with email exceeding max length."""
        body = {
            "personal": {
                "firstName": "John",
                "lastName": "Doe",
                "email": "a" * 250 + "@test.com",
            }
        }

        response = client.post("/api/applications/", json=body)
        assert 400 == response.status_code
        assert "Email must not exceed 254 characters" in response.json()["detail"]

    def test_create_application_invalid_email_format(self, client, mock_get_pool):
        """Test creating application with invalid email format."""
        invalid_emails = [
            "notanemail",
            "missing@domain",
            "@nodomain.com",
            "no@.com",
            "spaces in@email.com",
            "double@@domain.com",
        ]

        for email in invalid_emails:
            body = {
                "personal": {
                    "firstName": "John",
                    "lastName": "Doe",
                    "email": email,
                }
            }

            response = client.post("/api/applications/", json=body)
            assert 400 == response.status_code
            assert "Invalid email format" in response.json()["detail"]

    def test_create_application_valid_email_formats(self, client, mock_get_pool):
        """Test creating application with valid email formats."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        valid_emails = [
            "simple@example.com",
            "user.name@example.com",
            "user+tag@example.co.uk",
            "first_last@example-domain.com",
            "123@numbers.com",
        ]

        with patch("app.services.application_service.create_application") as mock_create:
            mock_create.return_value = "RK-2026-00001"

            for email in valid_emails:
                body = {
                    "personal": {
                        "firstName": "John",
                        "lastName": "Doe",
                        "email": email,
                    }
                }

                response = client.post("/api/applications/", json=body)
                assert 201 == response.status_code

    def test_create_application_trims_whitespace(self, client, mock_get_pool):
        """Test creating application trims whitespace from fields."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.create_application") as mock_create:
            mock_create.return_value = "RK-2026-00001"

            body = {
                "personal": {
                    "firstName": "  John  ",
                    "lastName": "  Doe  ",
                    "email": "  john@example.com  ",
                }
            }

            response = client.post("/api/applications/", json=body)
            assert 201 == response.status_code

            # Check that trimmed values were passed to service
            call_args = mock_create.call_args[0][1]
            assert "John" == call_args["personal"]["firstName"]
            assert "Doe" == call_args["personal"]["lastName"]
            assert "john@example.com" == call_args["personal"]["email"]

    def test_create_application_missing_personal_object(self, client, mock_get_pool):
        """Test creating application with missing personal object."""
        response = client.post("/api/applications/", json={})
        assert 400 == response.status_code


class TestUpdateApplication:
    """Test PATCH /api/applications/{app_id} endpoint."""

    def test_update_application_success(self, client, mock_get_pool):
        """Test updating an application successfully."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.update_application") as mock_update:
            mock_update.return_value = True

            body = {"stage": "form-submitted"}
            response = client.patch("/api/applications/RK-2026-00001", json=body)
            assert 200 == response.status_code
            assert "Application updated" == response.json()["message"]

    def test_update_application_not_found(self, client, mock_get_pool):
        """Test updating a non-existent application."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.update_application") as mock_update:
            mock_update.return_value = False

            body = {"stage": "checks"}
            response = client.patch("/api/applications/RK-2026-99999", json=body)
            assert 404 == response.status_code

    def test_update_application_valid_stages(self, client, mock_get_pool):
        """Test updating application with all valid stages."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        valid_stages = [
            "new", "form-submitted", "checks", "review",
            "approved", "blocked", "registered"
        ]

        with patch("app.services.application_service.update_application") as mock_update:
            mock_update.return_value = True

            for stage in valid_stages:
                body = {"stage": stage}
                response = client.patch("/api/applications/RK-2026-00001", json=body)
                assert 200 == response.status_code

    def test_update_application_invalid_stage(self, client, mock_get_pool):
        """Test updating application with invalid stage."""
        body = {"stage": "invalid-stage"}
        response = client.patch("/api/applications/RK-2026-00001", json=body)
        assert 400 == response.status_code
        assert "Invalid stage" in response.json()["detail"]

    def test_update_application_empty_stage(self, client, mock_get_pool):
        """Test updating application with empty stage."""
        body = {"stage": ""}
        response = client.patch("/api/applications/RK-2026-00001", json=body)
        assert 400 == response.status_code

    def test_update_application_other_fields(self, client, mock_get_pool):
        """Test updating application with non-stage fields."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.update_application") as mock_update:
            mock_update.return_value = True

            body = {"risk": "high", "progress": 75}
            response = client.patch("/api/applications/RK-2026-00001", json=body)
            assert 200 == response.status_code


class TestDeleteApplication:
    """Test DELETE /api/applications/{app_id} endpoint."""

    def test_delete_application_success(self, client, mock_get_pool):
        """Test deleting an application successfully."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.delete_application") as mock_delete:
            mock_delete.return_value = True

            response = client.delete("/api/applications/RK-2026-00001")
            assert 200 == response.status_code
            assert "Application deleted" == response.json()["message"]

    def test_delete_application_not_found(self, client, mock_get_pool):
        """Test deleting a non-existent application."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.delete_application") as mock_delete:
            mock_delete.return_value = False

            response = client.delete("/api/applications/RK-2026-99999")
            assert 404 == response.status_code
            assert "Application not found" == response.json()["detail"]


class TestAddTimelineEvent:
    """Test POST /api/applications/{app_id}/timeline endpoint."""

    def test_add_timeline_event_success(self, client, mock_get_pool):
        """Test adding a timeline event successfully."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.add_timeline_event") as mock_add:
            mock_add.return_value = {
                "id": 1,
                "application_id": "RK-2026-00001",
                "event": "DBS check completed",
                "type": "complete",
            }

            body = {"event": "DBS check completed", "type": "complete"}
            response = client.post("/api/applications/RK-2026-00001/timeline", json=body)
            assert 201 == response.status_code
            data = response.json()
            assert "DBS check completed" == data["event"]

    def test_add_timeline_event_missing_event(self, client, mock_get_pool):
        """Test adding timeline event with missing event text."""
        body = {"type": "action"}
        response = client.post("/api/applications/RK-2026-00001/timeline", json=body)
        assert 400 == response.status_code
        assert "Event text is required" in response.json()["detail"]

    def test_add_timeline_event_empty_event(self, client, mock_get_pool):
        """Test adding timeline event with empty event text."""
        body = {"event": "", "type": "action"}
        response = client.post("/api/applications/RK-2026-00001/timeline", json=body)
        assert 400 == response.status_code

    def test_add_timeline_event_too_long(self, client, mock_get_pool):
        """Test adding timeline event exceeding max length."""
        body = {"event": "A" * 2001, "type": "action"}
        response = client.post("/api/applications/RK-2026-00001/timeline", json=body)
        assert 400 == response.status_code
        assert "Event text must not exceed 2000 characters" in response.json()["detail"]

    def test_add_timeline_event_max_length(self, client, mock_get_pool):
        """Test adding timeline event at max length."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.add_timeline_event") as mock_add:
            mock_add.return_value = {"id": 1, "event": "A" * 2000, "type": "action"}

            body = {"event": "A" * 2000, "type": "action"}
            response = client.post("/api/applications/RK-2026-00001/timeline", json=body)
            assert 201 == response.status_code

    def test_add_timeline_event_valid_types(self, client, mock_get_pool):
        """Test adding timeline event with all valid types."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        valid_types = ["action", "complete", "alert", "note"]

        with patch("app.services.application_service.add_timeline_event") as mock_add:
            mock_add.return_value = {"id": 1, "event": "Test", "type": "action"}

            for event_type in valid_types:
                body = {"event": "Test event", "type": event_type}
                response = client.post("/api/applications/RK-2026-00001/timeline", json=body)
                assert 201 == response.status_code

    def test_add_timeline_event_invalid_type(self, client, mock_get_pool):
        """Test adding timeline event with invalid type."""
        body = {"event": "Test event", "type": "invalid-type"}
        response = client.post("/api/applications/RK-2026-00001/timeline", json=body)
        assert 400 == response.status_code
        assert "Invalid type" in response.json()["detail"]

    def test_add_timeline_event_default_type(self, client, mock_get_pool):
        """Test adding timeline event with default type."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.add_timeline_event") as mock_add:
            mock_add.return_value = {"id": 1, "event": "Test", "type": "action"}

            body = {"event": "Test event"}
            response = client.post("/api/applications/RK-2026-00001/timeline", json=body)
            assert 201 == response.status_code


class TestGlobalExceptionHandler:
    """Test global exception handler."""

    @pytest.fixture
    def error_client(self):
        """Client that captures server errors instead of re-raising them."""
        return TestClient(app, raise_server_exceptions=False)

    def test_global_exception_handler(self, error_client, mock_get_pool):
        """Test that unhandled exceptions return 500 with generic message."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.get_all_applications") as mock_get_all:
            mock_get_all.side_effect = Exception("Database connection failed")

            response = error_client.get("/api/applications/")
            assert 500 == response.status_code
            assert "Internal server error" == response.json()["detail"]

    def test_global_exception_handler_no_stack_trace(self, error_client, mock_get_pool):
        """Test that exception handler doesn't leak error details."""
        mock_pool = AsyncMock()
        mock_get_pool.return_value = mock_pool

        with patch("app.services.application_service.get_all_applications") as mock_get_all:
            mock_get_all.side_effect = Exception("Sensitive internal error message")

            response = error_client.get("/api/applications/")
            data = response.json()
            # Should not contain the actual exception message
            assert "Sensitive internal error message" not in str(data)
            assert "Internal server error" == data["detail"]
