"""Tests for the to_dashboard_shape transformation function."""

import pytest
from datetime import datetime, date, timezone
from app.services.application_service import to_dashboard_shape


class TestToDashboardShape:
    """Test the dashboard data transformation function."""

    def test_to_dashboard_shape_basic(self):
        """Test basic transformation with minimal data."""
        row = {
            "id": "RK-2026-00001",
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "1234567890",
            "dob": date(1990, 1, 15),
            "stage": "new",
            "start_date": date(2026, 2, 1),
            "registration_date": None,
            "last_updated": datetime.now(timezone.utc),
            "risk": "low",
            "progress": 0,
            "premises_type": "domestic",
            "premises_address": "123 Main St",
            "local_authority": "London",
        }

        timeline = []

        result = to_dashboard_shape(row, timeline)

        assert "RK-2026-00001" == result["id"]
        assert "John Doe" == result["name"]
        assert "john@example.com" == result["email"]
        assert "1234567890" == result["phone"]
        assert "1990-01-15" == result["dob"]
        assert "new" == result["stage"]
        assert "2026-02-01" == result["startDate"]
        assert result["registrationDate"] is None
        assert "low" == result["risk"]
        assert 0 == result["progress"]
        assert [] == result["timeline"]

    def test_to_dashboard_shape_with_timeline(self):
        """Test transformation with timeline events."""
        row = {
            "id": "RK-2026-00001",
            "name": "Jane Smith",
            "email": "jane@example.com",
            "phone": None,
            "dob": None,
            "stage": "form-submitted",
            "start_date": date(2026, 2, 1),
            "registration_date": None,
            "last_updated": datetime.now(timezone.utc),
            "risk": "low",
            "progress": 25,
            "premises_type": "domestic",
            "premises_address": "456 Park Ave",
            "local_authority": "Manchester",
        }

        timeline = [
            {
                "event": "Application started",
                "type": "action",
                "created_at": datetime(2026, 2, 1, 10, 0, 0),
            },
            {
                "event": "Form submitted",
                "type": "complete",
                "created_at": datetime(2026, 2, 1, 11, 30, 0),
            }
        ]

        result = to_dashboard_shape(row, timeline)

        assert 2 == len(result["timeline"])
        # Timeline should be reversed (newest first)
        assert "Form submitted" == result["timeline"][0]["event"]
        assert "Application started" == result["timeline"][1]["event"]
        assert "2026-02-01 11:30" == result["timeline"][0]["date"]

    def test_to_dashboard_shape_days_in_stage(self):
        """Test days in stage calculation."""
        # Set last_updated to 5 days ago
        past_date = datetime.now(timezone.utc).replace(day=datetime.now(timezone.utc).day - 5)

        row = {
            "id": "RK-2026-00001",
            "name": "Test User",
            "email": "test@example.com",
            "phone": None,
            "dob": None,
            "stage": "checks",
            "start_date": None,
            "registration_date": None,
            "last_updated": past_date,
            "risk": "low",
            "progress": 50,
            "premises_type": "domestic",
            "premises_address": None,
            "local_authority": None,
        }

        result = to_dashboard_shape(row, [])

        assert result["daysInStage"] >= 4  # At least 4 days

    def test_to_dashboard_shape_with_json_fields(self):
        """Test transformation with JSON fields."""
        row = {
            "id": "RK-2026-00001",
            "name": "Test User",
            "email": "test@example.com",
            "phone": None,
            "dob": None,
            "stage": "new",
            "start_date": None,
            "registration_date": None,
            "last_updated": datetime.now(timezone.utc),
            "risk": "low",
            "progress": 0,
            "premises_type": "domestic",
            "premises_address": None,
            "local_authority": None,
            "checks": '{"dbs": {"status": "complete"}}',
            "connected_persons": '[{"name": "John Doe"}]',
            "registers": '["0-5", "5-8"]',
            "ofsted_check": '{"status": "approved"}',
            "household": '{"adults": []}',
            "service": '{"type": "childminding"}',
            "premises_details": '{"outdoor_space": "garden"}',
        }

        result = to_dashboard_shape(row, [])

        assert {"dbs": {"status": "complete"}} == result["checks"]
        assert [{"name": "John Doe"}] == result["connectedPersons"]
        assert ["0-5", "5-8"] == result["registers"]
        assert {"status": "approved"} == result["ofstedCheck"]
        assert {"adults": []} == result["household"]
        assert {"type": "childminding"} == result["service"]
        assert {"outdoor_space": "garden"} == result["premisesDetails"]

    def test_to_dashboard_shape_with_optional_fields(self):
        """Test transformation with optional fields present."""
        row = {
            "id": "RK-2026-00001",
            "name": "Test User",
            "email": "test@example.com",
            "phone": None,
            "dob": None,
            "stage": "registered",
            "start_date": None,
            "registration_date": date(2026, 2, 15),
            "last_updated": datetime.now(timezone.utc),
            "risk": "low",
            "progress": 100,
            "premises_type": "domestic",
            "premises_address": None,
            "local_authority": None,
            "ni_number": "AB123456C",
            "registration_number": "REG-12345",
        }

        result = to_dashboard_shape(row, [])

        assert "AB123456C" == result["niNumber"]
        assert "REG-12345" == result["registrationNumber"]
        assert "2026-02-15" == result["registrationDate"]

    def test_to_dashboard_shape_empty_values(self):
        """Test transformation handles empty/null values."""
        row = {
            "id": "RK-2026-00001",
            "name": None,
            "email": None,
            "phone": None,
            "dob": None,
            "stage": None,
            "start_date": None,
            "registration_date": None,
            "last_updated": None,
            "risk": None,
            "progress": None,
            "premises_type": None,
            "premises_address": None,
            "local_authority": None,
        }

        result = to_dashboard_shape(row, [])

        assert "" == result["name"]
        assert "" == result["email"]
        assert "" == result["phone"]
        assert result["dob"] is None
        assert "new" == result["stage"]  # Default value
        assert 0 == result["progress"]  # Default value
        assert "low" == result["risk"]  # Default value

    def test_to_dashboard_shape_date_formatting(self):
        """Test that dates are formatted correctly."""
        row = {
            "id": "RK-2026-00001",
            "name": "Test",
            "email": "test@example.com",
            "phone": None,
            "dob": date(1990, 1, 15),
            "stage": "new",
            "start_date": date(2026, 2, 1),
            "registration_date": date(2026, 2, 15),
            "last_updated": datetime(2026, 2, 14, 15, 30, 0),
            "risk": "low",
            "progress": 0,
            "premises_type": "domestic",
            "premises_address": None,
            "local_authority": None,
        }

        result = to_dashboard_shape(row, [])

        assert "1990-01-15" == result["dob"]
        assert "2026-02-01" == result["startDate"]
        assert "2026-02-15" == result["registrationDate"]
        assert "2026-02-14" == result["lastUpdated"]

    def test_to_dashboard_shape_datetime_formatting(self):
        """Test that datetime values are formatted correctly."""
        row = {
            "id": "RK-2026-00001",
            "name": "Test",
            "email": "test@example.com",
            "phone": None,
            "dob": None,
            "stage": "new",
            "start_date": None,
            "registration_date": None,
            "last_updated": datetime.now(timezone.utc),
            "risk": "low",
            "progress": 0,
            "premises_type": "domestic",
            "premises_address": None,
            "local_authority": None,
        }

        timeline = [
            {
                "event": "Test event",
                "type": "action",
                "created_at": datetime(2026, 2, 14, 10, 30, 45),
            }
        ]

        result = to_dashboard_shape(row, timeline)

        assert "2026-02-14 10:30" == result["timeline"][0]["date"]

    def test_to_dashboard_shape_handles_date_as_last_updated(self):
        """Test that date objects for last_updated are handled correctly."""
        row = {
            "id": "RK-2026-00001",
            "name": "Test",
            "email": "test@example.com",
            "phone": None,
            "dob": None,
            "stage": "new",
            "start_date": None,
            "registration_date": None,
            "last_updated": date(2026, 2, 10),  # date instead of datetime
            "risk": "low",
            "progress": 0,
            "premises_type": "domestic",
            "premises_address": None,
            "local_authority": None,
        }

        result = to_dashboard_shape(row, [])

        # Should calculate days in stage from the date
        assert result["daysInStage"] >= 0

    def test_to_dashboard_shape_handles_naive_datetime(self):
        """Test that naive datetimes are handled correctly."""
        row = {
            "id": "RK-2026-00001",
            "name": "Test",
            "email": "test@example.com",
            "phone": None,
            "dob": None,
            "stage": "new",
            "start_date": None,
            "registration_date": None,
            "last_updated": datetime(2026, 2, 10, 10, 0, 0),  # naive datetime
            "risk": "low",
            "progress": 0,
            "premises_type": "domestic",
            "premises_address": None,
            "local_authority": None,
        }

        result = to_dashboard_shape(row, [])

        # Should handle naive datetime and calculate days
        assert result["daysInStage"] >= 0
