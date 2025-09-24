"""
FastAPI application for Onyx Trust Registry service.
"""

from typing import Any

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

from onyx.ce import create_kyb_verified_payload, emit_kyb_verified_ce, get_trace_id
from onyx.kyb import validate_kyb_payload, verify_kyb
from onyx.mcp.server import mcp_router
from onyx.trust_registry import get_trust_registry

# Create FastAPI application
app = FastAPI(
    title="Onyx Trust Registry",
    description="Trust Registry and KYB (Know Your Business) service for the Open Checkout Network",
    version="0.1.0",
    contact={
        "name": "OCN Team",
        "email": "team@ocn.ai",
        "url": "https://github.com/ahsanazmi1/onyx",
    },
    license_info={
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT",
    },
)

# Include MCP router
app.include_router(mcp_router)


class KYBVerificationRequest(BaseModel):
    """KYB verification request model."""

    entity_id: str = Field(..., description="Unique identifier for the business entity")
    business_name: str = Field(..., description="Legal business name")
    jurisdiction: str = Field(..., description="Country/jurisdiction of registration")
    entity_age_days: int = Field(..., ge=0, description="Age of entity in days")
    registration_status: str = Field(
        "unknown", description="Current registration status"
    )
    sanctions_flags: list[str] = Field(
        default_factory=list, description="List of sanctions-related flags"
    )
    business_type: str = Field("unknown", description="Type of business entity")
    registration_number: str = Field("", description="Official registration number")


class KYBVerificationResponse(BaseModel):
    """KYB verification response model."""

    status: str = Field(..., description="Overall verification status")
    checks: list[dict[str, Any]] = Field(
        ..., description="Individual verification checks"
    )
    reason: str = Field(..., description="Human-readable reason for the status")
    entity_id: str = Field(..., description="Entity identifier")
    verified_at: str = Field(..., description="Verification timestamp")
    metadata: dict[str, Any] = Field(..., description="Verification metadata")


@app.get("/health")
async def health_check() -> dict[str, Any]:
    """
    Health check endpoint.

    Returns:
        dict: Health status information
    """
    return {"ok": True, "repo": "onyx"}


@app.get("/trust/providers")
async def list_trusted_providers() -> dict[str, Any]:
    """
    List all trusted credential providers.

    Returns:
        dict: List of trusted provider IDs
    """
    registry = get_trust_registry()
    providers = registry.list_providers()
    stats = registry.get_stats()

    return {"providers": providers, "count": len(providers), "stats": stats}


@app.get("/trust/allowed/{provider_id}")
async def check_provider_allowed(provider_id: str) -> dict[str, Any]:
    """
    Check if a specific provider is allowed in the trust registry.

    Args:
        provider_id: Unique identifier for the provider

    Returns:
        dict: Provider status information
    """
    registry = get_trust_registry()
    allowed = registry.is_allowed(provider_id)

    return {
        "provider_id": provider_id,
        "allowed": allowed,
        "reason": (
            "Provider is in trust registry"
            if allowed
            else "Provider not found in trust registry"
        ),
    }


@app.post("/kyb/verify", response_model=KYBVerificationResponse)
async def verify_kyb_endpoint(
    request: KYBVerificationRequest,
    emit_ce: bool = Query(False, description="Emit CloudEvent for KYB verification"),
) -> dict[str, Any]:
    """
    Perform KYB (Know Your Business) verification with deterministic rule-based checks.

    Args:
        request: KYB verification request with entity information
        emit_ce: Whether to emit CloudEvent for the verification

    Returns:
        KYB verification response with status, checks, and reason
    """
    try:
        # Validate and normalize inputs
        validated_payload = validate_kyb_payload(request.model_dump())

        # Perform KYB verification
        verification_result = verify_kyb(validated_payload)

        # Create response dictionary
        response_dict = {
            "status": verification_result["status"],
            "checks": verification_result["checks"],
            "reason": verification_result["reason"],
            "entity_id": verification_result["entity_id"],
            "verified_at": verification_result["verified_at"],
            "metadata": verification_result["metadata"],
        }

        # Emit CloudEvent if requested
        if emit_ce:
            trace_id = get_trace_id()
            ce_payload = create_kyb_verified_payload(
                verification_result, validated_payload
            )
            ce_event = emit_kyb_verified_ce(trace_id, ce_payload)

            # Add CloudEvent to response (for testing purposes)
            # In production, this would be emitted to an event bus
            response_dict["cloud_event"] = ce_event
            response_dict["trace_id"] = trace_id

        return response_dict

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing KYB verification request: {str(e)}",
        ) from e


def main() -> None:
    """Main entry point for running the application."""
    import uvicorn

    uvicorn.run(
        "onyx.api:app",
        host="127.0.0.1",  # Use localhost for development security
        port=8000,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    main()
