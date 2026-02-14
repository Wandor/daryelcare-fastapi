"""Unit tests for service utility functions."""

import pytest
from datetime import datetime, date
from app.services.application_service import (
    escape_html,
    calculate_progress,
    build_checks_from_form,
    build_connected_persons,
    build_premises_address,
    generate_id,
)


class TestEscapeHtml:
    """Test HTML escaping functionality."""

    def test_escape_html_basic(self):
        """Test basic HTML character escaping."""
        result = escape_html("<script>alert('xss')</script>")
        assert "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;" == result

    def test_escape_html_quotes(self):
        """Test that quotes are escaped."""
        result = escape_html('Hello "world"')
        assert "Hello &quot;world&quot;" == result

    def test_escape_html_ampersand(self):
        """Test ampersand escaping."""
        result = escape_html("Tom & Jerry")
        assert "Tom &amp; Jerry" == result

    def test_escape_html_empty_string(self):
        """Test empty string handling."""
        result = escape_html("")
        assert "" == result

    def test_escape_html_no_special_chars(self):
        """Test string with no special characters."""
        result = escape_html("Hello World")
        assert "Hello World" == result


class TestCalculateProgress:
    """Test progress calculation functionality."""

    def test_calculate_progress_none(self):
        """Test progress with None checks."""
        assert 0 == calculate_progress(None)

    def test_calculate_progress_empty_dict(self):
        """Test progress with empty checks dict."""
        assert 0 == calculate_progress({})

    def test_calculate_progress_no_complete(self):
        """Test progress with no complete checks."""
        checks = {
            "dbs": {"status": "not-started"},
            "ref_1": {"status": "pending"},
            "first_aid": {"status": "in-progress"},
        }
        assert 0 == calculate_progress(checks)

    def test_calculate_progress_all_complete(self):
        """Test progress with all checks complete."""
        checks = {
            "dbs": {"status": "complete"},
            "ref_1": {"status": "complete"},
            "first_aid": {"status": "complete"},
        }
        assert 100 == calculate_progress(checks)

    def test_calculate_progress_partial(self):
        """Test progress with partial completion."""
        checks = {
            "dbs": {"status": "complete"},
            "ref_1": {"status": "complete"},
            "first_aid": {"status": "pending"},
            "safeguarding": {"status": "not-started"},
        }
        # 2 out of 4 = 50%
        assert 50 == calculate_progress(checks)

    def test_calculate_progress_rounding(self):
        """Test progress calculation with rounding."""
        checks = {
            "check1": {"status": "complete"},
            "check2": {"status": "pending"},
            "check3": {"status": "pending"},
        }
        # 1 out of 3 = 33.333... rounds to 33
        assert 33 == calculate_progress(checks)


class TestBuildChecksFromForm:
    """Test check building from form data."""

    def test_build_checks_from_form_empty(self):
        """Test building checks with empty form."""
        result = build_checks_from_form({})
        assert 11 == len(result)
        assert "dbs" in result
        assert "not-started" == result["dbs"]["status"]
        assert result["dbs"]["date"] is None

    def test_build_checks_from_form_with_dbs(self):
        """Test building checks with DBS data."""
        body = {
            "suitability": {
                "hasDBS": "Yes",
                "dbsNumber": "001234567890",
            }
        }
        result = build_checks_from_form(body)
        assert "pending" == result["dbs"]["status"]
        assert result["dbs"]["date"] is not None
        assert "001234567890" == result["dbs"]["certificate"]

    def test_build_checks_from_form_without_dbs_number(self):
        """Test building checks with DBS Yes but no number."""
        body = {
            "suitability": {
                "hasDBS": "Yes",
            }
        }
        result = build_checks_from_form(body)
        # Should remain not-started if no DBS number
        assert "not-started" == result["dbs"]["status"]

    def test_build_checks_from_form_with_first_aid(self):
        """Test building checks with first aid qualification."""
        body = {
            "qualifications": {
                "firstAidCompleted": "Yes",
                "firstAidDate": "2024-01-15",
                "firstAidOrg": "Red Cross",
            }
        }
        result = build_checks_from_form(body)
        assert "complete" == result["first_aid"]["status"]
        assert "2024-01-15" == result["first_aid"]["date"]
        assert "Red Cross" == result["first_aid"]["provider"]

    def test_build_checks_from_form_with_safeguarding(self):
        """Test building checks with safeguarding qualification."""
        body = {
            "qualifications": {
                "safeguardingCompleted": "Yes",
                "safeguardingDate": "2024-02-01",
                "safeguardingOrg": "Local Council",
            }
        }
        result = build_checks_from_form(body)
        assert "complete" == result["safeguarding"]["status"]
        assert "2024-02-01" == result["safeguarding"]["date"]
        assert "Local Council" == result["safeguarding"]["provider"]

    def test_build_checks_from_form_with_food_hygiene(self):
        """Test building checks with food hygiene qualification."""
        body = {
            "qualifications": {
                "foodHygieneCompleted": "Yes",
                "foodHygieneDate": "2023-12-10",
                "foodHygieneOrg": "Food Safety Council",
            }
        }
        result = build_checks_from_form(body)
        assert "complete" == result["food_hygiene"]["status"]
        assert "2023-12-10" == result["food_hygiene"]["date"]
        assert "Food Safety Council" == result["food_hygiene"]["provider"]

    def test_build_checks_from_form_with_references(self):
        """Test building checks with reference data."""
        body = {
            "references": {
                "ref1": {
                    "name": "John Smith",
                    "relationship": "Previous employer",
                },
                "ref2": {
                    "name": "Jane Doe",
                    "relationship": "Colleague",
                },
            }
        }
        result = build_checks_from_form(body)
        assert "pending" == result["ref_1"]["status"]
        assert "John Smith" == result["ref_1"]["referee"]
        assert "Previous employer" == result["ref_1"]["relationship"]
        assert "pending" == result["ref_2"]["status"]
        assert "Jane Doe" == result["ref_2"]["referee"]

    def test_build_checks_from_form_all_11_keys(self):
        """Test that all 11 expected check keys are present."""
        result = build_checks_from_form({})
        expected_keys = {
            "dbs", "dbs_update", "la_check", "ofsted", "gp_health",
            "ref_1", "ref_2", "first_aid", "safeguarding",
            "food_hygiene", "insurance"
        }
        assert expected_keys == set(result.keys())


class TestBuildConnectedPersons:
    """Test building connected persons from form data."""

    def test_build_connected_persons_empty(self):
        """Test building connected persons with empty data."""
        result = build_connected_persons({})
        assert [] == result

    def test_build_connected_persons_no_household(self):
        """Test building connected persons with no household data."""
        result = build_connected_persons({"household": {}})
        assert [] == result

    def test_build_connected_persons_single_adult(self):
        """Test building connected persons with single adult."""
        body = {
            "household": {
                "adults": [
                    {
                        "firstName": "John",
                        "lastName": "Doe",
                        "relationship": "Spouse",
                        "dob": "1980-05-15",
                    }
                ]
            }
        }
        result = build_connected_persons(body)
        assert 1 == len(result)
        assert "CP-NEW-001" == result[0]["id"]
        assert "John Doe" == result[0]["name"]
        assert "household" == result[0]["type"]
        assert "Spouse" == result[0]["relationship"]
        assert "1980-05-15" == result[0]["dob"]
        assert "not-started" == result[0]["formStatus"]
        assert "CMA-H2" == result[0]["formType"]

    def test_build_connected_persons_multiple_adults(self):
        """Test building connected persons with multiple adults."""
        body = {
            "household": {
                "adults": [
                    {"firstName": "John", "lastName": "Doe"},
                    {"firstName": "Jane", "lastName": "Smith"},
                    {"firstName": "Bob", "lastName": "Johnson"},
                ]
            }
        }
        result = build_connected_persons(body)
        assert 3 == len(result)
        assert "CP-NEW-001" == result[0]["id"]
        assert "CP-NEW-002" == result[1]["id"]
        assert "CP-NEW-003" == result[2]["id"]
        assert "Jane Smith" == result[1]["name"]

    def test_build_connected_persons_missing_names(self):
        """Test building connected persons with missing names."""
        body = {
            "household": {
                "adults": [
                    {"firstName": "John"},  # Missing lastName
                    {"lastName": "Doe"},    # Missing firstName
                    {"firstName": "Jane", "lastName": "Smith"},  # Complete
                ]
            }
        }
        result = build_connected_persons(body)
        # Only the complete entry should be included
        assert 1 == len(result)
        assert "Jane Smith" == result[0]["name"]

    def test_build_connected_persons_default_relationship(self):
        """Test building connected persons with default relationship."""
        body = {
            "household": {
                "adults": [
                    {"firstName": "John", "lastName": "Doe"}
                ]
            }
        }
        result = build_connected_persons(body)
        assert "Household member" == result[0]["relationship"]

    def test_build_connected_persons_checks_structure(self):
        """Test that connected persons have correct checks structure."""
        body = {
            "household": {
                "adults": [
                    {"firstName": "John", "lastName": "Doe"}
                ]
            }
        }
        result = build_connected_persons(body)
        checks = result[0]["checks"]
        assert "dbs" in checks
        assert "la_check" in checks
        assert "not-started" == checks["dbs"]["status"]
        assert checks["dbs"]["date"] is None


class TestBuildPremisesAddress:
    """Test building premises address from form data."""

    def test_build_premises_address_domestic_same_as_home(self):
        """Test building address for domestic premises same as home."""
        body = {
            "premises": {
                "type": "Domestic",
                "sameAsHome": True,
            },
            "homeAddress": {
                "line1": "123 Main St",
                "line2": "Apt 4B",
                "town": "London",
                "postcode": "SW1A 1AA",
            }
        }
        result = build_premises_address(body)
        assert "123 Main St, Apt 4B, London, SW1A 1AA" == result

    def test_build_premises_address_domestic_default_same_as_home(self):
        """Test domestic premises defaults to same as home."""
        body = {
            "premises": {
                "type": "Domestic",
            },
            "homeAddress": {
                "line1": "123 Main St",
                "town": "London",
                "postcode": "SW1A 1AA",
            }
        }
        result = build_premises_address(body)
        assert "123 Main St, London, SW1A 1AA" == result

    def test_build_premises_address_domestic_not_same_as_home(self):
        """Test domestic premises not same as home."""
        body = {
            "premises": {
                "type": "Domestic",
                "sameAsHome": False,
                "address": {
                    "line1": "456 Park Ave",
                    "town": "Manchester",
                    "postcode": "M1 1AA",
                }
            }
        }
        result = build_premises_address(body)
        assert "456 Park Ave, Manchester, M1 1AA" == result

    def test_build_premises_address_non_domestic(self):
        """Test non-domestic premises address."""
        body = {
            "premises": {
                "type": "Non-Domestic",
                "address": {
                    "line1": "789 Commercial Rd",
                    "line2": "Suite 100",
                    "town": "Birmingham",
                    "postcode": "B1 1AA",
                }
            }
        }
        result = build_premises_address(body)
        assert "789 Commercial Rd, Suite 100, Birmingham, B1 1AA" == result

    def test_build_premises_address_empty(self):
        """Test building address with empty data."""
        result = build_premises_address({})
        assert result is None

    def test_build_premises_address_partial_home_address(self):
        """Test building address with partial home address."""
        body = {
            "homeAddress": {
                "line1": "123 Main St",
                "postcode": "SW1A 1AA",
            }
        }
        result = build_premises_address(body)
        assert "123 Main St, SW1A 1AA" == result


class TestGenerateId:
    """Test ID generation functionality."""

    def test_generate_id_basic(self):
        """Test basic ID generation."""
        year = datetime.now().year
        result = generate_id(1)
        assert f"RK-{year}-00001" == result

    def test_generate_id_padding(self):
        """Test ID generation with proper padding."""
        year = datetime.now().year
        result = generate_id(42)
        assert f"RK-{year}-00042" == result

    def test_generate_id_large_number(self):
        """Test ID generation with large sequence number."""
        year = datetime.now().year
        result = generate_id(12345)
        assert f"RK-{year}-12345" == result

    def test_generate_id_max_padding(self):
        """Test ID generation with max padding."""
        year = datetime.now().year
        result = generate_id(99999)
        assert f"RK-{year}-99999" == result

    def test_generate_id_exceeds_padding(self):
        """Test ID generation when sequence exceeds padding."""
        year = datetime.now().year
        result = generate_id(100000)
        assert f"RK-{year}-100000" == result
