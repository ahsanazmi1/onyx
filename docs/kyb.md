# KYB (Know Your Business) Verification

The Onyx service provides deterministic KYB (Know Your Business) verification with rule-based checks and CloudEvents integration.

## Overview

KYB verification is a critical compliance requirement for financial services. The Onyx KYB module provides:

- **Deterministic verification** based on configurable rules
- **Multiple verification checks** for comprehensive compliance
- **CloudEvents integration** for audit trails and event-driven workflows
- **REST API and MCP endpoints** for flexible integration

## Verification Rules

The KYB verification process evaluates entities against five key criteria:

### 1. Jurisdiction Verification
- **Rule**: Entity must be registered in a whitelisted jurisdiction
- **Whitelisted Jurisdictions**: US, CA, GB, AU, DE, FR, NL, SG, CH, LU, IE, DK, SE, NO, FI
- **Status**: `verified` if whitelisted, `fail` if not

### 2. Entity Age Verification
- **Rule**: Entity must meet minimum age requirement
- **Minimum Age**: 365 days (1 year)
- **Status**: `verified` if meets requirement, `review` if below minimum

### 3. Sanctions Screening
- **Rule**: Entity must not have sanctions-related flags
- **Keywords Checked**: sanctions, embargo, terrorist, money_laundering, drug_trafficking, corruption, fraud, tax_evasion, regulatory_violation
- **Status**: `verified` if no sanctions detected, `fail` if sanctions found

### 4. Business Name Validation
- **Rule**: Business name must meet format requirements
- **Requirements**:
  - Length: 2-200 characters
  - Must contain letters
  - Must not contain suspicious patterns (test, demo, example, fake, invalid)
- **Status**: `verified` if valid, `review` if suspicious, `fail` if invalid

### 5. Registration Status Verification
- **Rule**: Entity must have valid registration status
- **Valid Statuses**: active, registered, incorporated, good_standing
- **Status**: `verified` if valid, `review` if unknown/invalid

## Overall Status Determination

The overall verification status is determined by the following rules:

1. **Fail**: If any check returns `fail`
2. **Review**: If any check returns `review` (and no failures)
3. **Verified**: If all checks return `verified`

## API Usage

### REST API Endpoint

```http
POST /kyb/verify
Content-Type: application/json

{
  "entity_id": "business_001",
  "business_name": "Acme Corporation Ltd",
  "jurisdiction": "US",
  "entity_age_days": 1000,
  "registration_status": "active",
  "sanctions_flags": [],
  "business_type": "corporation",
  "registration_number": "12345678"
}
```

### Response Format

```json
{
  "status": "verified",
  "checks": [
    {
      "check_name": "jurisdiction_verification",
      "status": "verified",
      "details": {
        "jurisdiction": "US",
        "whitelisted": true,
        "whitelist_countries": ["US", "CA", "GB", ...]
      },
      "reason": "Jurisdiction US is whitelisted"
    },
    {
      "check_name": "entity_age_verification",
      "status": "verified",
      "details": {
        "entity_age_days": 1000,
        "minimum_required_days": 365,
        "meets_requirement": true
      },
      "reason": "Entity age 1000 days meets minimum requirement of 365 days"
    },
    {
      "check_name": "sanctions_screening",
      "status": "verified",
      "details": {
        "sanctions_flags": [],
        "flags_checked": 0,
        "sanctions_detected": false,
        "keywords_checked": ["sanctions", "embargo", ...]
      },
      "reason": "Sanctions screening passed with 0 flags checked"
    },
    {
      "check_name": "business_name_validation",
      "status": "verified",
      "details": {
        "business_name": "Acme Corporation Ltd",
        "name_length": 19,
        "has_minimum_length": true,
        "has_maximum_length": true,
        "contains_letters": true,
        "contains_suspicious": false
      },
      "reason": "Business name validation passed"
    },
    {
      "check_name": "registration_status_verification",
      "status": "verified",
      "details": {
        "registration_status": "active",
        "valid_statuses": ["active", "registered", "incorporated", "good_standing"],
        "is_valid": true
      },
      "reason": "Registration status 'active' is valid"
    }
  ],
  "reason": "All verification checks passed successfully",
  "entity_id": "business_001",
  "verified_at": "2024-01-15T10:30:00Z",
  "metadata": {
    "verification_version": "1.0.0",
    "rules_applied": 5,
    "jurisdiction": "US",
    "entity_age_days": 1000
  }
}
```

### CloudEvents Integration

Enable CloudEvents emission with the `emit_ce=true` query parameter:

```http
POST /kyb/verify?emit_ce=true
Content-Type: application/json

{
  "entity_id": "business_001",
  "business_name": "Acme Corporation Ltd",
  "jurisdiction": "US",
  "entity_age_days": 1000,
  "registration_status": "active",
  "sanctions_flags": [],
  "business_type": "corporation"
}
```

The response will include a CloudEvent envelope:

```json
{
  "status": "verified",
  "checks": [...],
  "reason": "All verification checks passed successfully",
  "entity_id": "business_001",
  "verified_at": "2024-01-15T10:30:00Z",
  "metadata": {...},
  "cloud_event": {
    "specversion": "1.0",
    "type": "ocn.onyx.kyb_verified.v1",
    "source": "onyx",
    "id": "uuid-generated",
    "time": "2024-01-15T10:30:00Z",
    "subject": "trace-id",
    "datacontenttype": "application/json",
    "data": {
      "verification_result": {...},
      "entity_info": {...},
      "timestamp": "2024-01-15T10:30:00Z",
      "metadata": {...}
    }
  },
  "trace_id": "trace-id"
}
```

### MCP Integration

Use the MCP `verifyKYB` verb for agent-based integrations:

```json
{
  "verb": "verifyKYB",
  "args": {
    "entity_id": "business_001",
    "business_name": "Acme Corporation Ltd",
    "jurisdiction": "US",
    "entity_age_days": 1000,
    "registration_status": "active",
    "sanctions_flags": [],
    "business_type": "corporation"
  }
}
```

## Example Payloads and Outcomes

### Verified Entity Example

**Input:**
```json
{
  "entity_id": "acme_corp_001",
  "business_name": "Acme Corporation Ltd",
  "jurisdiction": "US",
  "entity_age_days": 1500,
  "registration_status": "active",
  "sanctions_flags": [],
  "business_type": "corporation",
  "registration_number": "12345678"
}
```

**Output Status:** `verified`

### Review Required Example

**Input:**
```json
{
  "entity_id": "new_startup_001",
  "business_name": "NewTech Startup",
  "jurisdiction": "CA",
  "entity_age_days": 200,
  "registration_status": "registered",
  "sanctions_flags": [],
  "business_type": "startup"
}
```

**Output Status:** `review` (due to entity age below minimum)

### Failed Verification Example

**Input:**
```json
{
  "entity_id": "blocked_entity_001",
  "business_name": "Suspicious Corp",
  "jurisdiction": "XX",
  "entity_age_days": 1000,
  "registration_status": "active",
  "sanctions_flags": ["money_laundering"],
  "business_type": "corporation"
}
```

**Output Status:** `fail` (due to non-whitelisted jurisdiction and sanctions flags)

## Error Handling

The API returns appropriate HTTP status codes:

- **200 OK**: Successful verification (regardless of verification status)
- **422 Unprocessable Entity**: Invalid request payload
- **500 Internal Server Error**: Server-side error during processing

## Deterministic Behavior

The KYB verification is designed to be deterministic:

- Same inputs always produce identical outputs
- No random or time-based factors in verification logic
- Consistent rule application across all requests
- Reproducible results for testing and compliance

## Compliance and Audit

- All verification decisions are logged with full audit trails
- CloudEvents provide structured event data for compliance reporting
- Detailed check results provide transparency in decision-making
- Metadata includes version information for traceability

## Configuration

The verification rules can be configured by modifying constants in the KYB module:

- `JURISDICTION_WHITELIST`: List of approved jurisdictions
- `MIN_ENTITY_AGE_DAYS`: Minimum entity age requirement
- `SANCTIONS_KEYWORDS`: Keywords to flag for sanctions screening

## Testing

The KYB verification includes comprehensive test coverage:

- Unit tests for individual verification checks
- Integration tests for API endpoints
- CloudEvents validation tests
- Deterministic behavior verification
- Edge case and error condition testing
