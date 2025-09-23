"""
Tests for Trust Registry API endpoints.
"""

from fastapi.testclient import TestClient

from onyx.api import app

client = TestClient(app)


def test_list_trusted_providers() -> None:
    """Test GET /trust/providers endpoint returns 200 with provider list."""
    response = client.get("/trust/providers")

    assert response.status_code == 200

    data = response.json()
    assert "providers" in data
    assert "count" in data
    assert "stats" in data

    # Should be a list of providers
    assert isinstance(data["providers"], list)
    assert isinstance(data["count"], int)
    assert data["count"] == len(data["providers"])

    # Should have built-in providers
    assert "trusted_bank_001" in data["providers"]
    assert "verified_credit_union_002" in data["providers"]

    # Stats should be present
    assert isinstance(data["stats"], dict)
    assert "total_providers" in data["stats"]
    assert "allowlist_size" in data["stats"]


def test_check_provider_allowed_true() -> None:
    """Test GET /trust/allowed/{provider_id} returns 200 for allowed provider."""
    response = client.get("/trust/allowed/trusted_bank_001")

    assert response.status_code == 200

    data = response.json()
    assert "provider_id" in data
    assert "allowed" in data
    assert "reason" in data

    assert data["provider_id"] == "trusted_bank_001"
    assert data["allowed"] is True
    assert "trust registry" in data["reason"]


def test_check_provider_allowed_false() -> None:
    """Test GET /trust/allowed/{provider_id} returns 200 for non-allowed provider."""
    response = client.get("/trust/allowed/unknown_provider")

    assert response.status_code == 200

    data = response.json()
    assert "provider_id" in data
    assert "allowed" in data
    assert "reason" in data

    assert data["provider_id"] == "unknown_provider"
    assert data["allowed"] is False
    assert "not found" in data["reason"]


def test_check_provider_allowed_multiple_providers() -> None:
    """Test GET /trust/allowed/{provider_id} with multiple built-in providers."""
    builtin_providers = [
        "trusted_bank_001",
        "verified_credit_union_002",
        "authorized_fintech_003",
        "certified_payment_processor_004",
        "licensed_lender_005",
    ]

    for provider_id in builtin_providers:
        response = client.get(f"/trust/allowed/{provider_id}")

        assert response.status_code == 200

        data = response.json()
        assert data["provider_id"] == provider_id
        assert data["allowed"] is True
        assert "trust registry" in data["reason"]


def test_check_provider_allowed_edge_cases() -> None:
    """Test GET /trust/allowed/{provider_id} with edge cases."""
    # Test valid provider IDs that should work
    valid_cases = [
        ("trusted_bank_001   ", True),  # Should handle whitespace
        ("TRUSTED_BANK_001", False),  # Case sensitive
        ("malicious_provider", False),
        ("blocked_provider", False),
    ]

    for provider_id, expected_allowed in valid_cases:
        response = client.get(f"/trust/allowed/{provider_id}")

        assert response.status_code == 200

        data = response.json()
        assert data["provider_id"] == provider_id
        assert data["allowed"] is expected_allowed

    # Test edge cases
    # Empty path results in 404
    response = client.get("/trust/allowed/")
    assert response.status_code == 404

    # Whitespace-only provider ID works but returns False
    response = client.get("/trust/allowed/   ")
    assert response.status_code == 200
    data = response.json()
    assert data["provider_id"] == "   "
    assert data["allowed"] is False


def test_check_provider_allowed_special_characters() -> None:
    """Test GET /trust/allowed/{provider_id} with special characters."""
    # Test provider IDs with special characters that should work
    valid_special_cases = [
        ("provider-with-dash", False),
        ("provider_with_underscore", False),
        ("provider.with.dots", False),
        ("provider@with@symbols", False),
    ]

    for provider_id, expected_allowed in valid_special_cases:
        response = client.get(f"/trust/allowed/{provider_id}")

        assert response.status_code == 200

        data = response.json()
        assert data["provider_id"] == provider_id
        assert data["allowed"] is expected_allowed

    # Test provider IDs with slashes (results in 404 from FastAPI)
    response = client.get("/trust/allowed/provider/with/slashes")
    assert response.status_code == 404

    # Test provider IDs with spaces (URL encoding required)
    response = client.get("/trust/allowed/provider%20with%20spaces")
    assert response.status_code == 200
    data = response.json()
    assert data["provider_id"] == "provider with spaces"
    assert data["allowed"] is False


def test_api_response_schema_consistency() -> None:
    """Test that API responses have consistent schema."""
    # Test providers endpoint
    providers_response = client.get("/trust/providers")
    assert providers_response.status_code == 200

    providers_data = providers_response.json()
    required_keys = ["providers", "count", "stats"]
    for key in required_keys:
        assert key in providers_data

    # Test allowed endpoint
    allowed_response = client.get("/trust/allowed/trusted_bank_001")
    assert allowed_response.status_code == 200

    allowed_data = allowed_response.json()
    required_keys = ["provider_id", "allowed", "reason"]
    for key in required_keys:
        assert key in allowed_data


def test_api_deterministic_responses() -> None:
    """Test that API responses are deterministic."""
    # Make multiple requests to same endpoints
    for _ in range(3):
        # Test providers endpoint
        response1 = client.get("/trust/providers")
        response2 = client.get("/trust/providers")
        assert response1.json() == response2.json()

        # Test allowed endpoint
        response3 = client.get("/trust/allowed/trusted_bank_001")
        response4 = client.get("/trust/allowed/trusted_bank_001")
        assert response3.json() == response4.json()


def test_api_performance() -> None:
    """Test that API endpoints respond quickly."""
    import time

    # Test providers endpoint performance
    start_time = time.time()
    response = client.get("/trust/providers")
    end_time = time.time()

    assert response.status_code == 200
    assert (end_time - start_time) < 1.0  # Should respond within 1 second

    # Test allowed endpoint performance
    start_time = time.time()
    response = client.get("/trust/allowed/trusted_bank_001")
    end_time = time.time()

    assert response.status_code == 200
    assert (end_time - start_time) < 1.0  # Should respond within 1 second
