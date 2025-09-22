"""
Tests for health check endpoint.
"""

from fastapi.testclient import TestClient

from onyx.api import app

client = TestClient(app)


def test_health_check() -> None:
    """Test that the health check endpoint returns expected response."""
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert data["ok"] is True
    assert data["repo"] == "onyx"


def test_health_check_response_format() -> None:
    """Test that the health check response has the correct format."""
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert isinstance(data, dict)
    assert "ok" in data
    assert "repo" in data
    assert len(data) == 2  # Should only have these two fields
