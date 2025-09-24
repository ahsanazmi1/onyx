"""
Tests for KYB verification CloudEvents validation.
"""

from onyx.ce import (
    create_kyb_verification_summary,
    create_kyb_verified_payload,
    emit_kyb_verified_ce,
    validate_ce_schema,
    validate_kyb_verification_payload,
)


def test_emit_kyb_verified_ce_basic() -> None:
    """Test basic CloudEvent emission for KYB verification."""
    trace_id = "test-trace-123"
    payload = {
        "verification_result": {
            "status": "verified",
            "checks": [
                {
                    "check_name": "jurisdiction_verification",
                    "status": "verified",
                    "details": {"jurisdiction": "US", "whitelisted": True},
                    "reason": "Jurisdiction US is whitelisted",
                }
            ],
            "reason": "All verification checks passed successfully",
            "entity_id": "test_entity_001",
            "verified_at": "2024-01-15T10:30:00Z",
        },
        "entity_info": {
            "business_name": "Test Corp",
            "jurisdiction": "US",
            "entity_age_days": 1000,
        },
        "timestamp": "2024-01-15T10:30:00Z",
        "metadata": {
            "service": "onyx",
            "version": "1.0.0",
            "feature": "kyb_verification",
        },
    }

    ce_event = emit_kyb_verified_ce(trace_id, payload)

    # Validate CloudEvent structure
    assert "specversion" in ce_event
    assert "type" in ce_event
    assert "source" in ce_event
    assert "id" in ce_event
    assert "time" in ce_event
    assert "subject" in ce_event
    assert "datacontenttype" in ce_event
    assert "data" in ce_event

    # Validate CloudEvent attributes
    assert ce_event["specversion"] == "1.0"
    assert ce_event["type"] == "ocn.onyx.kyb_verified.v1"
    assert ce_event["source"] == "onyx"
    assert ce_event["subject"] == trace_id
    assert ce_event["datacontenttype"] == "application/json"

    # Validate data payload
    data = ce_event["data"]
    assert data == payload


def test_emit_kyb_verified_ce_different_statuses() -> None:
    """Test CloudEvent emission for different KYB verification statuses."""
    trace_id = "test-trace-456"

    test_cases = [
        ("verified", "All verification checks passed successfully"),
        ("review", "Verification requires review due to entity age"),
        ("fail", "Verification failed due to jurisdiction verification"),
    ]

    for status, reason in test_cases:
        payload = {
            "verification_result": {
                "status": status,
                "checks": [],
                "reason": reason,
                "entity_id": f"test_entity_{status}",
                "verified_at": "2024-01-15T10:30:00Z",
            },
            "entity_info": {
                "business_name": "Test Corp",
                "jurisdiction": "US",
                "entity_age_days": 1000,
            },
            "timestamp": "2024-01-15T10:30:00Z",
            "metadata": {
                "service": "onyx",
                "version": "1.0.0",
                "feature": "kyb_verification",
            },
        }

        ce_event = emit_kyb_verified_ce(trace_id, payload)

        assert ce_event["type"] == "ocn.onyx.kyb_verified.v1"
        assert ce_event["subject"] == trace_id
        assert ce_event["data"]["verification_result"]["status"] == status
        assert ce_event["data"]["verification_result"]["reason"] == reason


def test_validate_ce_schema_valid() -> None:
    """Test CloudEvent schema validation with valid event."""
    valid_event = {
        "specversion": "1.0",
        "type": "ocn.onyx.kyb_verified.v1",
        "source": "onyx",
        "id": "test-event-id",
        "time": "2024-01-15T10:30:00Z",
        "subject": "test-trace-123",
        "datacontenttype": "application/json",
        "data": {
            "verification_result": {
                "status": "verified",
                "checks": [
                    {
                        "check_name": "jurisdiction_verification",
                        "status": "verified",
                        "details": {"jurisdiction": "US"},
                        "reason": "Jurisdiction US is whitelisted",
                    }
                ],
                "reason": "All verification checks passed successfully",
                "entity_id": "test_entity_001",
                "verified_at": "2024-01-15T10:30:00Z",
            },
            "entity_info": {
                "business_name": "Test Corp",
                "jurisdiction": "US",
                "entity_age_days": 1000,
            },
            "timestamp": "2024-01-15T10:30:00Z",
            "metadata": {
                "service": "onyx",
                "version": "1.0.0",
                "feature": "kyb_verification",
            },
        },
    }

    assert validate_ce_schema(valid_event) is True


def test_validate_ce_schema_missing_fields() -> None:
    """Test CloudEvent schema validation with missing required fields."""
    invalid_events = [
        # Missing specversion
        {
            "type": "ocn.onyx.kyb_verified.v1",
            "source": "onyx",
            "id": "test-id",
            "time": "2024-01-15T10:30:00Z",
            "subject": "test-trace",
            "datacontenttype": "application/json",
            "data": {},
        },
        # Wrong type
        {
            "specversion": "1.0",
            "type": "ocn.onyx.wrong_type.v1",
            "source": "onyx",
            "id": "test-id",
            "time": "2024-01-15T10:30:00Z",
            "subject": "test-trace",
            "datacontenttype": "application/json",
            "data": {},
        },
        # Wrong source
        {
            "specversion": "1.0",
            "type": "ocn.onyx.kyb_verified.v1",
            "source": "wrong_source",
            "id": "test-id",
            "time": "2024-01-15T10:30:00Z",
            "subject": "test-trace",
            "datacontenttype": "application/json",
            "data": {},
        },
        # Missing data
        {
            "specversion": "1.0",
            "type": "ocn.onyx.kyb_verified.v1",
            "source": "onyx",
            "id": "test-id",
            "time": "2024-01-15T10:30:00Z",
            "subject": "test-trace",
            "datacontenttype": "application/json",
        },
    ]

    for invalid_event in invalid_events:
        assert validate_ce_schema(invalid_event) is False


def test_validate_ce_schema_invalid_data_structure() -> None:
    """Test CloudEvent schema validation with invalid data structure."""
    invalid_data_events = [
        # Missing verification_result
        {
            "specversion": "1.0",
            "type": "ocn.onyx.kyb_verified.v1",
            "source": "onyx",
            "id": "test-id",
            "time": "2024-01-15T10:30:00Z",
            "subject": "test-trace",
            "datacontenttype": "application/json",
            "data": {
                "entity_info": {},
                "timestamp": "2024-01-15T10:30:00Z",
                "metadata": {},
            },
        },
        # Invalid status
        {
            "specversion": "1.0",
            "type": "ocn.onyx.kyb_verified.v1",
            "source": "onyx",
            "id": "test-id",
            "time": "2024-01-15T10:30:00Z",
            "subject": "test-trace",
            "datacontenttype": "application/json",
            "data": {
                "verification_result": {
                    "status": "invalid_status",
                    "checks": [],
                    "reason": "Test",
                    "entity_id": "test",
                    "verified_at": "2024-01-15T10:30:00Z",
                },
                "entity_info": {
                    "business_name": "Test",
                    "jurisdiction": "US",
                    "entity_age_days": 1000,
                },
                "timestamp": "2024-01-15T10:30:00Z",
                "metadata": {
                    "service": "onyx",
                    "version": "1.0.0",
                    "feature": "kyb_verification",
                },
            },
        },
        # Missing entity_info
        {
            "specversion": "1.0",
            "type": "ocn.onyx.kyb_verified.v1",
            "source": "onyx",
            "id": "test-id",
            "time": "2024-01-15T10:30:00Z",
            "subject": "test-trace",
            "datacontenttype": "application/json",
            "data": {
                "verification_result": {
                    "status": "verified",
                    "checks": [],
                    "reason": "Test",
                    "entity_id": "test",
                    "verified_at": "2024-01-15T10:30:00Z",
                },
                "timestamp": "2024-01-15T10:30:00Z",
                "metadata": {},
            },
        },
    ]

    for invalid_event in invalid_data_events:
        assert validate_ce_schema(invalid_event) is False


def test_create_kyb_verified_payload() -> None:
    """Test creation of KYB verification payload for CloudEvent."""
    verification_result = {
        "status": "verified",
        "checks": [
            {
                "check_name": "jurisdiction_verification",
                "status": "verified",
                "details": {"jurisdiction": "US"},
                "reason": "Jurisdiction US is whitelisted",
            }
        ],
        "reason": "All verification checks passed successfully",
        "entity_id": "test_entity_001",
        "verified_at": "2024-01-15T10:30:00Z",
        "metadata": {"verification_version": "1.0.0", "rules_applied": 5},
    }

    entity_info = {
        "business_name": "Test Corp",
        "jurisdiction": "US",
        "entity_age_days": 1000,
        "registration_status": "active",
    }

    payload = create_kyb_verified_payload(verification_result, entity_info)

    # Validate payload structure
    assert "verification_result" in payload
    assert "entity_info" in payload
    assert "timestamp" in payload
    assert "metadata" in payload

    # Validate verification_result
    assert payload["verification_result"] == verification_result

    # Validate entity_info
    assert payload["entity_info"] == entity_info

    # Validate metadata
    metadata = payload["metadata"]
    assert metadata["service"] == "onyx"
    assert metadata["version"] == "1.0.0"
    assert metadata["feature"] == "kyb_verification"
    assert metadata["trace_id"] == "test_entity_001"


def test_validate_kyb_verification_payload() -> None:
    """Test validation of KYB verification payload."""
    valid_payload = {
        "verification_result": {
            "status": "verified",
            "checks": [],
            "reason": "All checks passed",
            "entity_id": "test_entity",
            "verified_at": "2024-01-15T10:30:00Z",
        },
        "entity_info": {
            "business_name": "Test Corp",
            "jurisdiction": "US",
            "entity_age_days": 1000,
        },
        "timestamp": "2024-01-15T10:30:00Z",
        "metadata": {
            "service": "onyx",
            "version": "1.0.0",
            "feature": "kyb_verification",
        },
    }

    assert validate_kyb_verification_payload(valid_payload) is True

    # Test invalid payloads
    invalid_payloads = [
        # Missing verification_result
        {"entity_info": {}, "timestamp": "2024-01-15T10:30:00Z", "metadata": {}},
        # Missing entity_info
        {
            "verification_result": {
                "status": "verified",
                "checks": [],
                "reason": "Test",
                "entity_id": "test",
                "verified_at": "2024-01-15T10:30:00Z",
            },
            "timestamp": "2024-01-15T10:30:00Z",
            "metadata": {},
        },
        # Missing metadata
        {
            "verification_result": {
                "status": "verified",
                "checks": [],
                "reason": "Test",
                "entity_id": "test",
                "verified_at": "2024-01-15T10:30:00Z",
            },
            "entity_info": {
                "business_name": "Test",
                "jurisdiction": "US",
                "entity_age_days": 1000,
            },
            "timestamp": "2024-01-15T10:30:00Z",
        },
    ]

    for invalid_payload in invalid_payloads:
        assert validate_kyb_verification_payload(invalid_payload) is False


def test_create_kyb_verification_summary() -> None:
    """Test creation of KYB verification summary."""
    verification_result = {
        "status": "verified",
        "checks": [
            {"check_name": "jurisdiction_verification", "status": "verified"},
            {"check_name": "entity_age_verification", "status": "verified"},
            {"check_name": "sanctions_screening", "status": "verified"},
        ],
        "reason": "All verification checks passed successfully",
        "entity_id": "test_entity_001",
        "verified_at": "2024-01-15T10:30:00Z",
        "metadata": {"verification_version": "1.0.0", "rules_applied": 3},
    }

    summary = create_kyb_verification_summary(verification_result)

    assert summary["overall_status"] == "verified"
    assert summary["total_checks"] == 3
    assert summary["check_results"]["verified"] == 3
    assert summary["check_results"]["review"] == 0
    assert summary["check_results"]["fail"] == 0
    assert summary["entity_id"] == "test_entity_001"
    assert summary["reason"] == "All verification checks passed successfully"
    assert summary["metadata"]["verification_version"] == "1.0.0"


def test_create_kyb_verification_summary_mixed_results() -> None:
    """Test creation of KYB verification summary with mixed check results."""
    verification_result = {
        "status": "review",
        "checks": [
            {"check_name": "jurisdiction_verification", "status": "verified"},
            {"check_name": "entity_age_verification", "status": "review"},
            {"check_name": "sanctions_screening", "status": "verified"},
            {"check_name": "business_name_validation", "status": "fail"},
        ],
        "reason": "Verification requires review due to business name validation",
        "entity_id": "test_entity_002",
        "verified_at": "2024-01-15T10:30:00Z",
        "metadata": {"verification_version": "1.0.0", "rules_applied": 4},
    }

    summary = create_kyb_verification_summary(verification_result)

    assert summary["overall_status"] == "review"
    assert summary["total_checks"] == 4
    assert summary["check_results"]["verified"] == 2
    assert summary["check_results"]["review"] == 1
    assert summary["check_results"]["fail"] == 1


def test_emit_kyb_verified_ce_deterministic() -> None:
    """Test that CloudEvent emission is deterministic for same inputs."""
    trace_id = "test-trace-deterministic"
    payload = {
        "verification_result": {
            "status": "verified",
            "checks": [],
            "reason": "All checks passed",
            "entity_id": "test_entity",
            "verified_at": "2024-01-15T10:30:00Z",
        },
        "entity_info": {
            "business_name": "Test Corp",
            "jurisdiction": "US",
            "entity_age_days": 1000,
        },
        "timestamp": "2024-01-15T10:30:00Z",
        "metadata": {
            "service": "onyx",
            "version": "1.0.0",
            "feature": "kyb_verification",
        },
    }

    # Emit multiple events with same inputs
    events = []
    for _ in range(3):
        event = emit_kyb_verified_ce(trace_id, payload)
        events.append(event)

    # All events should have same structure and data
    first_event = events[0]
    for event in events[1:]:
        assert event["specversion"] == first_event["specversion"]
        assert event["type"] == first_event["type"]
        assert event["source"] == first_event["source"]
        assert event["subject"] == first_event["subject"]
        assert event["datacontenttype"] == first_event["datacontenttype"]
        assert event["data"] == first_event["data"]

        # Only the ID and time should be different (generated values)
        assert event["id"] != first_event["id"]
        assert event["time"] != first_event["time"]


def test_cloud_event_schema_validation_edge_cases() -> None:
    """Test CloudEvent schema validation with edge cases."""
    # Test with empty data
    empty_data_event = {
        "specversion": "1.0",
        "type": "ocn.onyx.kyb_verified.v1",
        "source": "onyx",
        "id": "test-id",
        "time": "2024-01-15T10:30:00Z",
        "subject": "test-trace",
        "datacontenttype": "application/json",
        "data": {},
    }

    assert validate_ce_schema(empty_data_event) is False

    # Test with non-dict data
    non_dict_data_event = {
        "specversion": "1.0",
        "type": "ocn.onyx.kyb_verified.v1",
        "source": "onyx",
        "id": "test-id",
        "time": "2024-01-15T10:30:00Z",
        "subject": "test-trace",
        "datacontenttype": "application/json",
        "data": "not a dictionary",
    }

    assert validate_ce_schema(non_dict_data_event) is False

    # Test with malformed verification_result
    malformed_verification_event = {
        "specversion": "1.0",
        "type": "ocn.onyx.kyb_verified.v1",
        "source": "onyx",
        "id": "test-id",
        "time": "2024-01-15T10:30:00Z",
        "subject": "test-trace",
        "datacontenttype": "application/json",
        "data": {
            "verification_result": "not a dictionary",
            "entity_info": {
                "business_name": "Test",
                "jurisdiction": "US",
                "entity_age_days": 1000,
            },
            "timestamp": "2024-01-15T10:30:00Z",
            "metadata": {
                "service": "onyx",
                "version": "1.0.0",
                "feature": "kyb_verification",
            },
        },
    }

    assert validate_ce_schema(malformed_verification_event) is False
