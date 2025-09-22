"""
Smoke tests for MCP (Model Context Protocol) endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from onyx.api import app

client = TestClient(app)


def test_mcp_get_status() -> None:
    """Test MCP getStatus verb returns expected response."""
    response = client.post(
        "/mcp/invoke",
        json={
            "verb": "getStatus",
            "args": {}
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["ok"] is True
    assert data["data"]["agent"] == "onyx"


def test_mcp_is_allowed_provider_allowed() -> None:
    """Test MCP isAllowedProvider verb with allowed provider."""
    response = client.post(
        "/mcp/invoke",
        json={
            "verb": "isAllowedProvider",
            "args": {
                "provider_id": "trusted_merchant_123"
            }
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["allowed"] is True
    assert data["data"]["provider_id"] == "trusted_merchant_123"
    assert "reason" in data["data"]


def test_mcp_is_allowed_provider_denied() -> None:
    """Test MCP isAllowedProvider verb with denied provider."""
    response = client.post(
        "/mcp/invoke",
        json={
            "verb": "isAllowedProvider",
            "args": {
                "provider_id": "blocked_merchant_456"
            }
        }
    )
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["allowed"] is False
    assert data["data"]["provider_id"] == "blocked_merchant_456"
    assert "reason" in data["data"]


def test_mcp_is_allowed_provider_deterministic() -> None:
    """Test MCP isAllowedProvider verb with deterministic behavior."""
    # Test even-length provider_id (should be allowed)
    response = client.post(
        "/mcp/invoke",
        json={
            "verb": "isAllowedProvider",
            "args": {
                "provider_id": "test12"
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["allowed"] is True
    
    # Test odd-length provider_id (should be denied)
    response = client.post(
        "/mcp/invoke",
        json={
            "verb": "isAllowedProvider",
            "args": {
                "provider_id": "test123"
            }
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["allowed"] is False


def test_mcp_is_allowed_provider_missing_param() -> None:
    """Test MCP isAllowedProvider verb with missing provider_id."""
    response = client.post(
        "/mcp/invoke",
        json={
            "verb": "isAllowedProvider",
            "args": {}
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "provider_id parameter is required" in data["detail"]


def test_mcp_unknown_verb() -> None:
    """Test MCP invoke with unknown verb."""
    response = client.post(
        "/mcp/invoke",
        json={
            "verb": "unknownVerb",
            "args": {}
        }
    )
    
    assert response.status_code == 400
    data = response.json()
    assert "Unknown verb: unknownVerb" in data["detail"]


def test_mcp_response_schema() -> None:
    """Test MCP response schema consistency."""
    response = client.post(
        "/mcp/invoke",
        json={
            "verb": "getStatus",
            "args": {}
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify response schema
    assert "success" in data
    assert "data" in data
    assert "error" in data
    assert isinstance(data["success"], bool)
    assert isinstance(data["data"], dict)
    assert data["error"] is None
