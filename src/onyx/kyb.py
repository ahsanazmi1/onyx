"""
Onyx KYB (Know Your Business) verification module.

Provides deterministic KYB verification with rule-based checks.
"""

from datetime import UTC
from typing import Any

# KYB verification constants
VERIFIED_STATUS = "verified"
REVIEW_STATUS = "review"
FAIL_STATUS = "fail"

# Jurisdiction whitelist (countries with favorable regulatory environments)
JURISDICTION_WHITELIST = {
    "US",
    "CA",
    "GB",
    "AU",
    "DE",
    "FR",
    "NL",
    "SG",
    "CH",
    "LU",
    "IE",
    "DK",
    "SE",
    "NO",
    "FI",
}

# Minimum entity age in days (1 year)
MIN_ENTITY_AGE_DAYS = 365

# Sanctions-related keywords to flag
SANCTIONS_KEYWORDS = {
    "sanctions",
    "embargo",
    "terrorist",
    "money_laundering",
    "drug_trafficking",
    "corruption",
    "fraud",
    "tax_evasion",
    "regulatory_violation",
}


def verify_kyb(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Perform deterministic KYB verification based on business entity information.

    Args:
        payload: KYB verification payload containing entity information

    Returns:
        Dictionary with verification status, checks performed, and reason
    """
    # Extract and validate payload fields
    entity_info = _extract_entity_info(payload)

    # Perform verification checks
    checks = []

    # Check 1: Jurisdiction verification
    jurisdiction_check = _check_jurisdiction(entity_info["jurisdiction"])
    checks.append(jurisdiction_check)

    # Check 2: Entity age verification
    age_check = _check_entity_age(entity_info["entity_age_days"])
    checks.append(age_check)

    # Check 3: Sanctions screening
    sanctions_check = _check_sanctions(entity_info["sanctions_flags"])
    checks.append(sanctions_check)

    # Check 4: Business name validation
    name_check = _check_business_name(entity_info["business_name"])
    checks.append(name_check)

    # Check 5: Registration status
    registration_check = _check_registration_status(entity_info["registration_status"])
    checks.append(registration_check)

    # Determine overall status based on checks
    status, reason = _determine_overall_status(checks)

    return {
        "status": status,
        "checks": checks,
        "reason": reason,
        "entity_id": entity_info.get("entity_id"),
        "verified_at": _get_current_timestamp(),
        "metadata": {
            "verification_version": "1.0.0",
            "rules_applied": len(checks),
            "jurisdiction": entity_info["jurisdiction"],
            "entity_age_days": entity_info["entity_age_days"],
        },
    }


def _extract_entity_info(payload: dict[str, Any]) -> dict[str, Any]:
    """Extract and normalize entity information from payload."""
    return {
        "entity_id": payload.get("entity_id", ""),
        "business_name": payload.get("business_name", "").strip(),
        "jurisdiction": payload.get("jurisdiction", "").upper(),
        "entity_age_days": int(payload.get("entity_age_days", 0)),
        "registration_status": payload.get("registration_status", "unknown"),
        "sanctions_flags": payload.get("sanctions_flags", []),
        "business_type": payload.get("business_type", "unknown"),
        "registration_number": payload.get("registration_number", ""),
    }


def _check_jurisdiction(jurisdiction: str) -> dict[str, Any]:
    """Check if jurisdiction is in whitelist."""
    is_whitelisted = jurisdiction in JURISDICTION_WHITELIST

    return {
        "check_name": "jurisdiction_verification",
        "status": VERIFIED_STATUS if is_whitelisted else FAIL_STATUS,
        "details": {
            "jurisdiction": jurisdiction,
            "whitelisted": is_whitelisted,
            "whitelist_countries": list(JURISDICTION_WHITELIST),
        },
        "reason": f"Jurisdiction {jurisdiction} is {'whitelisted' if is_whitelisted else 'not whitelisted'}",
    }


def _check_entity_age(entity_age_days: int) -> dict[str, Any]:
    """Check if entity meets minimum age requirement."""
    meets_minimum_age = entity_age_days >= MIN_ENTITY_AGE_DAYS

    return {
        "check_name": "entity_age_verification",
        "status": VERIFIED_STATUS if meets_minimum_age else REVIEW_STATUS,
        "details": {
            "entity_age_days": entity_age_days,
            "minimum_required_days": MIN_ENTITY_AGE_DAYS,
            "meets_requirement": meets_minimum_age,
        },
        "reason": f"Entity age {entity_age_days} days {'meets' if meets_minimum_age else 'does not meet'} minimum requirement of {MIN_ENTITY_AGE_DAYS} days",
    }


def _check_sanctions(sanctions_flags: list[str]) -> dict[str, Any]:
    """Check for sanctions-related flags."""
    # Convert flags to lowercase for case-insensitive matching
    flags_lower = [flag.lower() for flag in sanctions_flags]

    # Check for sanctions keywords
    sanctions_detected = any(
        keyword in flag for flag in flags_lower for keyword in SANCTIONS_KEYWORDS
    )

    return {
        "check_name": "sanctions_screening",
        "status": FAIL_STATUS if sanctions_detected else VERIFIED_STATUS,
        "details": {
            "sanctions_flags": sanctions_flags,
            "flags_checked": len(sanctions_flags),
            "sanctions_detected": sanctions_detected,
            "keywords_checked": list(SANCTIONS_KEYWORDS),
        },
        "reason": f"Sanctions screening {'failed' if sanctions_detected else 'passed'} with {len(sanctions_flags)} flags checked",
    }


def _check_business_name(business_name: str) -> dict[str, Any]:
    """Validate business name format and content."""
    if not business_name:
        return {
            "check_name": "business_name_validation",
            "status": FAIL_STATUS,
            "details": {
                "business_name": business_name,
                "name_length": 0,
                "has_content": False,
            },
            "reason": "Business name is empty or missing",
        }

    # Basic validation rules
    name_length = len(business_name)
    has_minimum_length = name_length >= 2
    has_maximum_length = name_length <= 200
    contains_letters = any(c.isalpha() for c in business_name)

    # Check for suspicious patterns
    suspicious_patterns = ["test", "demo", "example", "fake", "invalid"]
    contains_suspicious = any(
        pattern in business_name.lower() for pattern in suspicious_patterns
    )

    if not has_minimum_length or not has_maximum_length or not contains_letters:
        status = FAIL_STATUS
        reason = "Business name does not meet format requirements"
    elif contains_suspicious:
        status = REVIEW_STATUS
        reason = "Business name contains suspicious patterns requiring review"
    else:
        status = VERIFIED_STATUS
        reason = "Business name validation passed"

    return {
        "check_name": "business_name_validation",
        "status": status,
        "details": {
            "business_name": business_name,
            "name_length": name_length,
            "has_minimum_length": has_minimum_length,
            "has_maximum_length": has_maximum_length,
            "contains_letters": contains_letters,
            "contains_suspicious": contains_suspicious,
        },
        "reason": reason,
    }


def _check_registration_status(registration_status: str) -> dict[str, Any]:
    """Check business registration status."""
    valid_statuses = ["active", "registered", "incorporated", "good_standing"]
    status_lower = registration_status.lower()

    is_valid_status = status_lower in valid_statuses

    return {
        "check_name": "registration_status_verification",
        "status": VERIFIED_STATUS if is_valid_status else REVIEW_STATUS,
        "details": {
            "registration_status": registration_status,
            "valid_statuses": valid_statuses,
            "is_valid": is_valid_status,
        },
        "reason": f"Registration status '{registration_status}' is {'valid' if is_valid_status else 'invalid or requires review'}",
    }


def _determine_overall_status(checks: list[dict[str, Any]]) -> tuple[str, str]:
    """
    Determine overall verification status based on individual checks.

    Rules:
    - If any check fails: overall status = FAIL
    - If any check requires review: overall status = REVIEW
    - If all checks pass: overall status = VERIFIED
    """
    statuses = [check["status"] for check in checks]

    if FAIL_STATUS in statuses:
        failed_checks = [
            check["check_name"] for check in checks if check["status"] == FAIL_STATUS
        ]
        reason = f"Verification failed due to: {', '.join(failed_checks)}"
        return FAIL_STATUS, reason

    if REVIEW_STATUS in statuses:
        review_checks = [
            check["check_name"] for check in checks if check["status"] == REVIEW_STATUS
        ]
        reason = f"Verification requires review due to: {', '.join(review_checks)}"
        return REVIEW_STATUS, reason

    # All checks passed
    reason = "All verification checks passed successfully"
    return VERIFIED_STATUS, reason


def _get_current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    from datetime import datetime

    return datetime.now(UTC).isoformat()


def validate_kyb_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and normalize KYB verification payload.

    Args:
        payload: Raw KYB payload

    Returns:
        Validated and normalized payload
    """
    # Handle sanctions_flags properly - don't convert string to list of characters
    sanctions_flags = payload.get("sanctions_flags", [])
    if not isinstance(sanctions_flags, list):
        if isinstance(sanctions_flags, str):
            sanctions_flags = [
                sanctions_flags
            ]  # Single string becomes single-item list
        else:
            sanctions_flags = []  # Non-list, non-string becomes empty list

    validated = {
        "entity_id": str(payload.get("entity_id", "")),
        "business_name": str(payload.get("business_name", "")).strip(),
        "jurisdiction": str(payload.get("jurisdiction", "")).upper(),
        "entity_age_days": max(0, int(payload.get("entity_age_days", 0))),
        "registration_status": str(
            payload.get("registration_status", "unknown")
        ).lower(),
        "sanctions_flags": sanctions_flags,
        "business_type": str(payload.get("business_type", "unknown")),
        "registration_number": str(payload.get("registration_number", "")),
    }

    # Ensure all sanctions_flags are strings
    validated["sanctions_flags"] = [str(flag) for flag in validated["sanctions_flags"]]

    return validated


def get_kyb_verification_summary(verification_result: dict[str, Any]) -> str:
    """
    Generate human-readable summary of KYB verification result.

    Args:
        verification_result: Result from verify_kyb function

    Returns:
        Human-readable summary string
    """
    status = verification_result["status"]
    checks = verification_result["checks"]
    reason = verification_result["reason"]

    summary = f"KYB Verification Result: {status.upper()}\n\n"
    summary += f"Reason: {reason}\n\n"

    summary += "Individual Checks:\n"
    for check in checks:
        check_status = check["status"]
        check_name = check["check_name"].replace("_", " ").title()
        check_reason = check["reason"]
        summary += f"• {check_name}: {check_status.upper()} - {check_reason}\n"

    # Add metadata
    metadata = verification_result.get("metadata", {})
    if metadata:
        summary += "\nMetadata:\n"
        summary += f"• Jurisdiction: {metadata.get('jurisdiction', 'N/A')}\n"
        summary += f"• Entity Age: {metadata.get('entity_age_days', 0)} days\n"
        summary += f"• Rules Applied: {metadata.get('rules_applied', 0)}\n"

    return summary
