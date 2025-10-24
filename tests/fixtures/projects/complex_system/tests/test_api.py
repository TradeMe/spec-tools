"""Tests for REST API."""

import json

import pytest


class MockAPIResponse:
    """Mock API response."""

    def __init__(self, status_code, body):
        self.status_code = status_code
        self.body = body

    def json(self):
        """Return JSON body."""
        return json.loads(self.body)


class MockAPI:
    """Mock REST API for testing."""

    def __init__(self):
        self.sessions = {"valid_token": "user@example.com"}

    def request(self, method, path, headers=None, body=None):
        """Make an API request."""
        headers = headers or {}

        # Check authentication for protected endpoints
        if path.startswith("/api/v1/protected"):
            token = headers.get("Authorization", "").replace("Bearer ", "")
            if token not in self.sessions:
                return MockAPIResponse(
                    401, json.dumps({"error": {"code": "UNAUTHORIZED", "message": "Invalid token"}})
                )

        # Handle invalid JSON
        if body is not None:
            try:
                json.loads(body)
            except json.JSONDecodeError:
                return MockAPIResponse(
                    400,
                    json.dumps(
                        {
                            "error": {
                                "code": "INVALID_JSON",
                                "message": "Request body is not valid JSON",
                            }
                        }
                    ),
                )

        # Success response
        return MockAPIResponse(
            200,
            json.dumps(
                {
                    "data": {"result": "success"},
                    "meta": {"timestamp": "2025-10-24T12:00:00Z", "version": "v1"},
                }
            ),
        )


class TestAPIEndpoints:
    """Test suite for API endpoints."""

    @pytest.mark.req("SPEC-203/REQ-002")
    def test_api_versioning_in_url_path(self):
        """Test that API endpoints use versioning in URL path."""
        api = MockAPI()
        response = api.request("GET", "/api/v1/users")

        assert response.status_code == 200
        data = response.json()
        assert data["meta"]["version"] == "v1"

    @pytest.mark.req("SPEC-203/REQ-003")
    def test_appropriate_http_status_codes(self):
        """Test that API returns appropriate HTTP status codes."""
        api = MockAPI()

        # Success case
        response = api.request("GET", "/api/v1/users")
        assert response.status_code == 200

        # Unauthorized case
        response = api.request("GET", "/api/v1/protected/data")
        assert response.status_code == 401


class TestAPIAuthentication:
    """Test suite for API authentication."""

    @pytest.mark.req("SPEC-203/REQ-004", "SPEC-200/REQ-009")
    def test_protected_endpoints_require_valid_token(self):
        """Test that protected endpoints require valid session token."""
        api = MockAPI()

        # Request with valid token
        response = api.request(
            "GET", "/api/v1/protected/data", headers={"Authorization": "Bearer valid_token"}
        )
        assert response.status_code == 200

    @pytest.mark.req("SPEC-203/REQ-005")
    def test_missing_token_returns_401(self):
        """Test that requests without token return 401."""
        api = MockAPI()

        response = api.request("GET", "/api/v1/protected/data")
        assert response.status_code == 401

        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "UNAUTHORIZED"


class TestRequestHandling:
    """Test suite for request handling."""

    @pytest.mark.req("SPEC-203/REQ-007")
    def test_invalid_json_returns_400(self):
        """Test that invalid JSON returns 400 Bad Request."""
        api = MockAPI()

        response = api.request("POST", "/api/v1/users", body="invalid json {{{")

        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "INVALID_JSON"


class TestResponseFormat:
    """Test suite for response format."""

    @pytest.mark.req("SPEC-203/REQ-008")
    def test_json_responses_for_all_endpoints(self):
        """Test that all endpoints return JSON."""
        api = MockAPI()

        response = api.request("GET", "/api/v1/users")

        # Should be able to parse as JSON
        data = response.json()
        assert data is not None

    @pytest.mark.req("SPEC-203/REQ-009")
    def test_successful_responses_include_data_field(self):
        """Test that successful responses include data field."""
        api = MockAPI()

        response = api.request("GET", "/api/v1/users")
        data = response.json()

        assert "data" in data

    @pytest.mark.req("SPEC-203/REQ-010")
    def test_error_responses_include_error_field(self):
        """Test that error responses include error field."""
        api = MockAPI()

        response = api.request("GET", "/api/v1/protected/data")
        data = response.json()

        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]


# Note: Some requirements are intentionally not tested to simulate partial coverage:
# - SPEC-203/REQ-001 (REST principles - architectural)
# - SPEC-203/REQ-006 (JSON request bodies)
# - SPEC-203/REQ-011 (Structured error responses - partially covered)
# - SPEC-203/REQ-012 (Error logging)
# - SPEC-203/NFR-001 (95th percentile response time)
# - SPEC-203/NFR-002 (1000 requests per second)
