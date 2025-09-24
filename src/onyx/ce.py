"""
Onyx CloudEvents module.

Provides utilities for emitting and validating CloudEvents related to KYB verification.
"""

import json
import uuid
from datetime import UTC, datetime
from typing import Any

from cloudevents.http import CloudEvent, to_structured


def emit_kyb_verified_ce(trace_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    """
    Emit a CloudEvent for KYB verification result.

    Args:
        trace_id: Trace ID for the request.
        payload: KYB verification payload.

    Returns:
        CloudEvent envelope.
    """
    attributes = {
        "type": "ocn.onyx.kyb_verified.v1",
        "source": "onyx",
        "id": str(uuid.uuid4()),
        "time": datetime.now(UTC).isoformat(),
        "subject": trace_id,
        "datacontenttype": "application/json",
    }

    event = CloudEvent(attributes, payload)

    # Return in structured content mode for easier logging/storage
    structured_event = to_structured(event)
    if isinstance(structured_event, tuple):
        # Handle tuple return format
        structured_event_str = structured_event[1].decode("utf-8")
    else:
        # Handle bytes return format
        structured_event_str = structured_event.decode("utf-8")
    return json.loads(structured_event_str)


def validate_ce_schema(event: dict[str, Any]) -> bool:
    """
    Validate CloudEvent against ocn.onyx.kyb_verified.v1 schema.

    Args:
        event: CloudEvent to validate.

    Returns:
        True if valid, False otherwise.
    """
    try:
        required_fields = [
            "specversion",
            "type",
            "source",
            "id",
            "time",
            "subject",
            "datacontenttype",
            "data",
        ]

        for field in required_fields:
            if field not in event:
                return False

        if event["specversion"] != "1.0":
            return False
        if event["type"] != "ocn.onyx.kyb_verified.v1":
            return False
        if event["source"] != "onyx":
            return False
        if event["datacontenttype"] != "application/json":
            return False

        data = event["data"]
        if not isinstance(data, dict):
            return False

        # Validate data structure for KYB verification
        required_data_fields = [
            "verification_result",
            "entity_info",
            "timestamp",
            "metadata",
        ]
        for field in required_data_fields:
            if field not in data:
                return False

        # Validate 'verification_result' sub-structure
        verification_result = data["verification_result"]
        required_verification_fields = [
            "status",
            "checks",
            "reason",
            "entity_id",
            "verified_at",
        ]
        for field in required_verification_fields:
            if field not in verification_result:
                return False

        # Validate status is one of the allowed values
        if verification_result["status"] not in ["verified", "review", "fail"]:
            return False

        # Validate 'checks' is a list
        if not isinstance(verification_result["checks"], list):
            return False

        # Validate 'entity_info' sub-structure (basic check)
        entity_info = data["entity_info"]
        required_entity_fields = ["business_name", "jurisdiction", "entity_age_days"]
        for field in required_entity_fields:
            if field not in entity_info:
                return False

        # Validate 'metadata' sub-structure (basic check)
        if not isinstance(data["metadata"], dict):
            return False

        return True

    except Exception:
        return False


def create_kyb_verified_payload(
    verification_result: dict[str, Any], entity_info: dict[str, Any]
) -> dict[str, Any]:
    """
    Create KYB verification payload for CloudEvent.

    Args:
        verification_result: The KYB verification result.
        entity_info: The original entity information.

    Returns:
        Payload dictionary.
    """
    return {
        "verification_result": verification_result,
        "entity_info": entity_info,
        "timestamp": datetime.now(UTC).isoformat(),
        "metadata": {
            "service": "onyx",
            "version": "1.0.0",  # Placeholder, should be dynamic
            "feature": "kyb_verification",
            "trace_id": verification_result.get("entity_id", ""),
        },
    }


def get_trace_id() -> str:
    """
    Generate or retrieve trace ID.

    Returns:
        Trace ID string.
    """
    # In a real scenario, this would come from request headers or a tracing context
    return str(uuid.uuid4())


def format_ce_for_logging(event: dict[str, Any]) -> str:
    """
    Format CloudEvent for logging purposes.

    Args:
        event: CloudEvent dictionary.

    Returns:
        Formatted string for logging.
    """
    ce_type = event.get("type", "unknown")
    ce_id = event.get("id", "unknown")
    ce_subject = event.get("subject", "unknown")
    return f"CloudEvent Type: {ce_type}, ID: {ce_id}, Subject: {ce_subject}"


def validate_kyb_verification_payload(payload: dict[str, Any]) -> bool:
    """
    Validate KYB verification payload structure.

    Args:
        payload: KYB verification payload.

    Returns:
        True if payload is valid, False otherwise.
    """
    try:
        # Check required top-level fields
        required_fields = [
            "verification_result",
            "entity_info",
            "timestamp",
            "metadata",
        ]
        for field in required_fields:
            if field not in payload:
                return False

        # Validate verification_result structure
        verification_result = payload["verification_result"]
        required_verification_fields = [
            "status",
            "checks",
            "reason",
            "entity_id",
            "verified_at",
        ]
        for field in required_verification_fields:
            if field not in verification_result:
                return False

        # Validate entity_info structure
        entity_info = payload["entity_info"]
        required_entity_fields = ["business_name", "jurisdiction", "entity_age_days"]
        for field in required_entity_fields:
            if field not in entity_info:
                return False

        # Validate metadata structure
        metadata = payload["metadata"]
        required_metadata_fields = ["service", "version", "feature"]
        for field in required_metadata_fields:
            if field not in metadata:
                return False

        return True

    except Exception:
        return False


def create_kyb_verification_summary(
    verification_result: dict[str, Any],
) -> dict[str, Any]:
    """
    Create a summary of KYB verification for reporting purposes.

    Args:
        verification_result: KYB verification result.

    Returns:
        Summary dictionary.
    """
    status = verification_result.get("status", "unknown")
    checks = verification_result.get("checks", [])

    # Count check results
    status_counts = {"verified": 0, "review": 0, "fail": 0}
    for check in checks:
        check_status = check.get("status", "unknown")
        if check_status in status_counts:
            status_counts[check_status] += 1

    return {
        "overall_status": status,
        "total_checks": len(checks),
        "check_results": status_counts,
        "entity_id": verification_result.get("entity_id", ""),
        "verified_at": verification_result.get("verified_at", ""),
        "reason": verification_result.get("reason", ""),
        "metadata": verification_result.get("metadata", {}),
    }
