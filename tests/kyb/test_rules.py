"""
Tests for KYB verification rules and deterministic behavior.
"""

from onyx.kyb import validate_kyb_payload, verify_kyb


def test_kyb_verification_verified_entity() -> None:
    """Test KYB verification for a fully compliant entity."""
    payload = {
        "entity_id": "test_entity_001",
        "business_name": "Acme Corporation Ltd",
        "jurisdiction": "US",
        "entity_age_days": 1000,
        "registration_status": "active",
        "sanctions_flags": [],
        "business_type": "corporation",
        "registration_number": "12345678",
    }

    result = verify_kyb(payload)

    assert result["status"] == "verified"
    assert result["entity_id"] == "test_entity_001"
    assert len(result["checks"]) == 5
    assert "All verification checks passed successfully" in result["reason"]

    # Check individual verification results
    check_names = [check["check_name"] for check in result["checks"]]
    assert "jurisdiction_verification" in check_names
    assert "entity_age_verification" in check_names
    assert "sanctions_screening" in check_names
    assert "business_name_validation" in check_names
    assert "registration_status_verification" in check_names


def test_kyb_verification_failed_jurisdiction() -> None:
    """Test KYB verification failure due to non-whitelisted jurisdiction."""
    payload = {
        "entity_id": "test_entity_002",
        "business_name": "Test Corp",
        "jurisdiction": "XX",  # Non-whitelisted jurisdiction
        "entity_age_days": 1000,
        "registration_status": "active",
        "sanctions_flags": [],
        "business_type": "corporation",
    }

    result = verify_kyb(payload)

    assert result["status"] == "fail"
    assert "jurisdiction_verification" in result["reason"]

    # Find jurisdiction check
    jurisdiction_check = next(
        check
        for check in result["checks"]
        if check["check_name"] == "jurisdiction_verification"
    )
    assert jurisdiction_check["status"] == "fail"
    assert jurisdiction_check["details"]["jurisdiction"] == "XX"
    assert not jurisdiction_check["details"]["whitelisted"]


def test_kyb_verification_review_age() -> None:
    """Test KYB verification review due to entity age."""
    payload = {
        "entity_id": "test_entity_003",
        "business_name": "New Corp",
        "jurisdiction": "US",
        "entity_age_days": 100,  # Below minimum age
        "registration_status": "active",
        "sanctions_flags": [],
        "business_type": "corporation",
    }

    result = verify_kyb(payload)

    assert result["status"] == "review"
    assert "entity_age_verification" in result["reason"]

    # Find age check
    age_check = next(
        check
        for check in result["checks"]
        if check["check_name"] == "entity_age_verification"
    )
    assert age_check["status"] == "review"
    assert age_check["details"]["entity_age_days"] == 100
    assert age_check["details"]["minimum_required_days"] == 365
    assert not age_check["details"]["meets_requirement"]


def test_kyb_verification_failed_sanctions() -> None:
    """Test KYB verification failure due to sanctions flags."""
    payload = {
        "entity_id": "test_entity_004",
        "business_name": "Test Corp",
        "jurisdiction": "US",
        "entity_age_days": 1000,
        "registration_status": "active",
        "sanctions_flags": ["money_laundering", "terrorist_organization"],
        "business_type": "corporation",
    }

    result = verify_kyb(payload)

    assert result["status"] == "fail"
    assert "sanctions_screening" in result["reason"]

    # Find sanctions check
    sanctions_check = next(
        check
        for check in result["checks"]
        if check["check_name"] == "sanctions_screening"
    )
    assert sanctions_check["status"] == "fail"
    assert sanctions_check["details"]["sanctions_detected"] is True
    assert "money_laundering" in sanctions_check["details"]["sanctions_flags"]


def test_kyb_verification_review_business_name() -> None:
    """Test KYB verification review due to suspicious business name."""
    payload = {
        "entity_id": "test_entity_005",
        "business_name": "Test Demo Company",  # Contains "test" and "demo"
        "jurisdiction": "US",
        "entity_age_days": 1000,
        "registration_status": "active",
        "sanctions_flags": [],
        "business_type": "corporation",
    }

    result = verify_kyb(payload)

    assert result["status"] == "review"
    assert "business_name_validation" in result["reason"]

    # Find business name check
    name_check = next(
        check
        for check in result["checks"]
        if check["check_name"] == "business_name_validation"
    )
    assert name_check["status"] == "review"
    assert name_check["details"]["contains_suspicious"] is True


def test_kyb_verification_failed_business_name() -> None:
    """Test KYB verification failure due to invalid business name."""
    payload = {
        "entity_id": "test_entity_006",
        "business_name": "",  # Empty business name
        "jurisdiction": "US",
        "entity_age_days": 1000,
        "registration_status": "active",
        "sanctions_flags": [],
        "business_type": "corporation",
    }

    result = verify_kyb(payload)

    assert result["status"] == "fail"
    assert "business_name_validation" in result["reason"]

    # Find business name check
    name_check = next(
        check
        for check in result["checks"]
        if check["check_name"] == "business_name_validation"
    )
    assert name_check["status"] == "fail"
    assert name_check["details"]["name_length"] == 0
    assert not name_check["details"]["has_content"]


def test_kyb_verification_deterministic_behavior() -> None:
    """Test that same inputs always produce identical results."""
    payload = {
        "entity_id": "test_entity_007",
        "business_name": "Deterministic Corp",
        "jurisdiction": "CA",
        "entity_age_days": 500,
        "registration_status": "incorporated",
        "sanctions_flags": [],
        "business_type": "corporation",
    }

    # Run verification multiple times
    results = []
    for _ in range(3):
        result = verify_kyb(payload)
        results.append(result)

    # All results should be identical
    first_result = results[0]
    for result in results[1:]:
        assert result["status"] == first_result["status"]
        assert result["checks"] == first_result["checks"]
        assert result["reason"] == first_result["reason"]
        assert result["entity_id"] == first_result["entity_id"]


def test_kyb_verification_jurisdiction_whitelist() -> None:
    """Test jurisdiction whitelist functionality."""
    # Test whitelisted jurisdictions
    whitelisted_jurisdictions = ["US", "CA", "GB", "AU", "DE", "FR", "NL", "SG"]

    for jurisdiction in whitelisted_jurisdictions:
        payload = {
            "entity_id": f"test_{jurisdiction.lower()}",
            "business_name": "Test Corp",
            "jurisdiction": jurisdiction,
            "entity_age_days": 1000,
            "registration_status": "active",
            "sanctions_flags": [],
            "business_type": "corporation",
        }

        result = verify_kyb(payload)

        # Find jurisdiction check
        jurisdiction_check = next(
            check
            for check in result["checks"]
            if check["check_name"] == "jurisdiction_verification"
        )
        assert jurisdiction_check["status"] == "verified"
        assert jurisdiction_check["details"]["whitelisted"] is True

    # Test non-whitelisted jurisdiction
    payload = {
        "entity_id": "test_xx",
        "business_name": "Test Corp",
        "jurisdiction": "XX",
        "entity_age_days": 1000,
        "registration_status": "active",
        "sanctions_flags": [],
        "business_type": "corporation",
    }

    result = verify_kyb(payload)
    jurisdiction_check = next(
        check
        for check in result["checks"]
        if check["check_name"] == "jurisdiction_verification"
    )
    assert jurisdiction_check["status"] == "fail"
    assert jurisdiction_check["details"]["whitelisted"] is False


def test_kyb_verification_sanctions_keywords() -> None:
    """Test sanctions keyword detection."""
    sanctions_keywords = [
        "sanctions",
        "embargo",
        "terrorist",
        "money_laundering",
        "drug_trafficking",
    ]

    for keyword in sanctions_keywords:
        payload = {
            "entity_id": f"test_sanctions_{keyword}",
            "business_name": "Test Corp",
            "jurisdiction": "US",
            "entity_age_days": 1000,
            "registration_status": "active",
            "sanctions_flags": [keyword],
            "business_type": "corporation",
        }

        result = verify_kyb(payload)

        # Find sanctions check
        sanctions_check = next(
            check
            for check in result["checks"]
            if check["check_name"] == "sanctions_screening"
        )
        assert sanctions_check["status"] == "fail"
        assert sanctions_check["details"]["sanctions_detected"] is True


def test_kyb_verification_registration_status() -> None:
    """Test registration status validation."""
    valid_statuses = ["active", "registered", "incorporated", "good_standing"]

    for status in valid_statuses:
        payload = {
            "entity_id": f"test_{status}",
            "business_name": "Test Corp",
            "jurisdiction": "US",
            "entity_age_days": 1000,
            "registration_status": status,
            "sanctions_flags": [],
            "business_type": "corporation",
        }

        result = verify_kyb(payload)

        # Find registration check
        registration_check = next(
            check
            for check in result["checks"]
            if check["check_name"] == "registration_status_verification"
        )
        assert registration_check["status"] == "verified"
        assert registration_check["details"]["is_valid"] is True

    # Test invalid status
    payload = {
        "entity_id": "test_invalid",
        "business_name": "Test Corp",
        "jurisdiction": "US",
        "entity_age_days": 1000,
        "registration_status": "invalid_status",
        "sanctions_flags": [],
        "business_type": "corporation",
    }

    result = verify_kyb(payload)
    registration_check = next(
        check
        for check in result["checks"]
        if check["check_name"] == "registration_status_verification"
    )
    assert registration_check["status"] == "review"
    assert registration_check["details"]["is_valid"] is False


def test_kyb_verification_metadata() -> None:
    """Test that verification result includes proper metadata."""
    payload = {
        "entity_id": "test_metadata",
        "business_name": "Test Corp",
        "jurisdiction": "US",
        "entity_age_days": 1000,
        "registration_status": "active",
        "sanctions_flags": [],
        "business_type": "corporation",
    }

    result = verify_kyb(payload)

    assert "metadata" in result
    metadata = result["metadata"]

    assert "verification_version" in metadata
    assert "rules_applied" in metadata
    assert "jurisdiction" in metadata
    assert "entity_age_days" in metadata

    assert metadata["verification_version"] == "1.0.0"
    assert metadata["rules_applied"] == 5
    assert metadata["jurisdiction"] == "US"
    assert metadata["entity_age_days"] == 1000


def test_validate_kyb_payload() -> None:
    """Test KYB payload validation and normalization."""
    raw_payload = {
        "entity_id": 12345,  # Should be converted to string
        "business_name": "  Test Corp  ",  # Should be stripped
        "jurisdiction": "us",  # Should be uppercase
        "entity_age_days": "1000",  # Should be converted to int
        "registration_status": "ACTIVE",  # Should be lowercase
        "sanctions_flags": "not_a_list",  # Should be converted to list
        "business_type": "corporation",
        "registration_number": 987654321,
    }

    validated = validate_kyb_payload(raw_payload)

    assert isinstance(validated["entity_id"], str)
    assert validated["entity_id"] == "12345"

    assert validated["business_name"] == "Test Corp"  # Stripped

    assert validated["jurisdiction"] == "US"  # Uppercase

    assert isinstance(validated["entity_age_days"], int)
    assert validated["entity_age_days"] == 1000

    assert validated["registration_status"] == "active"  # Lowercase

    assert isinstance(validated["sanctions_flags"], list)
    assert validated["sanctions_flags"] == ["not_a_list"]

    assert isinstance(validated["registration_number"], str)
    assert validated["registration_number"] == "987654321"


def test_kyb_verification_edge_cases() -> None:
    """Test KYB verification with edge case inputs."""
    # Test with minimum valid data
    minimal_payload = {
        "entity_id": "minimal",
        "business_name": "AB",  # Minimum length
        "jurisdiction": "US",
        "entity_age_days": 0,
        "registration_status": "unknown",
        "sanctions_flags": [],
        "business_type": "unknown",
    }

    result = verify_kyb(minimal_payload)
    assert "status" in result
    assert "checks" in result
    assert "reason" in result

    # Test with maximum age
    max_age_payload = {
        "entity_id": "max_age",
        "business_name": "Old Corp",
        "jurisdiction": "US",
        "entity_age_days": 36500,  # 100 years
        "registration_status": "active",
        "sanctions_flags": [],
        "business_type": "corporation",
    }

    result = verify_kyb(max_age_payload)
    age_check = next(
        check
        for check in result["checks"]
        if check["check_name"] == "entity_age_verification"
    )
    assert age_check["status"] == "verified"
    assert age_check["details"]["meets_requirement"] is True


def test_kyb_verification_multiple_failures() -> None:
    """Test KYB verification with multiple failing conditions."""
    payload = {
        "entity_id": "multi_fail",
        "business_name": "",  # Fail: empty name
        "jurisdiction": "XX",  # Fail: non-whitelisted
        "entity_age_days": 50,  # Review: too young
        "registration_status": "invalid",  # Review: invalid status
        "sanctions_flags": ["terrorist"],  # Fail: sanctions
        "business_type": "corporation",
    }

    result = verify_kyb(payload)

    # Should fail due to multiple failure conditions
    assert result["status"] == "fail"

    # Check that we have multiple failing checks
    failing_checks = [check for check in result["checks"] if check["status"] == "fail"]
    assert len(failing_checks) >= 2  # At least jurisdiction and sanctions should fail

    failing_check_names = [check["check_name"] for check in failing_checks]
    assert "jurisdiction_verification" in failing_check_names
    assert "sanctions_screening" in failing_check_names
