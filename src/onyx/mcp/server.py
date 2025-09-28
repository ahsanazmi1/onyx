"""
MCP (Model Context Protocol) server for Onyx Trust Registry.

Provides standardized interface for trust registry operations.
"""

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from onyx.kyb import validate_kyb_payload, verify_kyb
from onyx.trust_signals import get_trust_signal, TrustContext
from onyx.trust_events import emit_trust_signal_event

# Create MCP router
mcp_router = APIRouter(prefix="/mcp", tags=["mcp"])


class MCPRequest(BaseModel):
    """MCP request model."""

    verb: str
    args: dict[str, Any] = {}


class MCPResponse(BaseModel):
    """MCP response model."""

    success: bool
    data: dict[str, Any]
    error: str | None = None


@mcp_router.post("/invoke")
async def invoke_mcp(request: MCPRequest) -> MCPResponse:
    """
    MCP invoke endpoint.

    Handles Model Context Protocol requests for Onyx Trust Registry operations.

    Args:
        request: MCP request with verb and arguments

    Returns:
        MCP response with success status and data

    Raises:
        HTTPException: For invalid verbs or missing required parameters
    """
    try:
        if request.verb == "getStatus":
            return MCPResponse(success=True, data={"ok": True, "agent": "onyx"})

        elif request.verb == "isAllowedProvider":
            provider_id = request.args.get("provider_id")
            if not provider_id:
                raise HTTPException(
                    status_code=400, detail="provider_id parameter is required"
                )

            # Stub implementation - deterministic based on provider_id
            # In real implementation, this would query the trust registry
            allowed = _is_provider_allowed(provider_id)
            reason = (
                "Provider is in trust registry"
                if allowed
                else "Provider not found in trust registry"
            )

            return MCPResponse(
                success=True,
                data={"allowed": allowed, "provider_id": provider_id, "reason": reason},
            )

        elif request.verb == "verifyKYB":
            # Extract KYB verification parameters from args
            kyb_payload = {
                "entity_id": request.args.get("entity_id", ""),
                "business_name": request.args.get("business_name", ""),
                "jurisdiction": request.args.get("jurisdiction", ""),
                "entity_age_days": request.args.get("entity_age_days", 0),
                "registration_status": request.args.get(
                    "registration_status", "unknown"
                ),
                "sanctions_flags": request.args.get("sanctions_flags", []),
                "business_type": request.args.get("business_type", "unknown"),
                "registration_number": request.args.get("registration_number", ""),
            }

            # Validate and normalize inputs
            validated_payload = validate_kyb_payload(kyb_payload)

            # Perform KYB verification
            verification_result = verify_kyb(validated_payload)

            return MCPResponse(
                success=True,
                data={
                    "verification_id": verification_result["entity_id"],
                    "status": verification_result["status"],
                    "checks": verification_result["checks"],
                    "reason": verification_result["reason"],
                    "verified_at": verification_result["verified_at"],
                    "metadata": verification_result["metadata"],
                },
            )

        elif request.verb == "getTrustSignal":
            # Extract trust signal parameters from args
            trace_id = request.args.get("trace_id")
            if not trace_id:
                raise HTTPException(
                    status_code=400, detail="trace_id parameter is required"
                )

            # Extract trust context
            context_data = request.args.get("context", {})
            if not context_data:
                raise HTTPException(
                    status_code=400, detail="context parameter is required"
                )

            # Create trust context
            trust_context = TrustContext(
                device_reputation=context_data.get("device_reputation", 0.5),
                velocity=context_data.get("velocity", 1.0),
                ip_risk=context_data.get("ip_risk", 0.3),
                history_len=context_data.get("history_len", 10),
                user_id=context_data.get("user_id"),
                session_id=context_data.get("session_id"),
                merchant_id=context_data.get("merchant_id"),
                channel=context_data.get("channel", "online"),
                amount=context_data.get("amount"),
            )

            # Get original rail weights if provided
            original_weights = request.args.get("original_weights")
            deterministic_seed = request.args.get("deterministic_seed", 42)

            # Generate trust signal
            trust_response = get_trust_signal(
                trace_id=trace_id,
                context=trust_context,
                original_weights=original_weights,
                deterministic_seed=deterministic_seed
            )

            # Emit CloudEvent
            try:
                event = emit_trust_signal_event(
                    trust_response=trust_response,
                    context=trust_context,
                    merchant_context=request.args.get("merchant_context"),
                    cart_summary=request.args.get("cart_summary"),
                    rail_candidates=request.args.get("rail_candidates")
                )
                event_emitted = True
                event_id = event.id
            except Exception as e:
                # Log error but don't fail the request
                event_emitted = False
                event_id = None

            return MCPResponse(
                success=True,
                data={
                    "trace_id": trust_response.trace_id,
                    "trust_score": trust_response.trust_score_result.trust_score,
                    "risk_level": trust_response.trust_score_result.risk_level,
                    "confidence": trust_response.trust_score_result.confidence,
                    "model_type": trust_response.trust_score_result.model_type,
                    "feature_contributions": trust_response.trust_score_result.feature_contributions,
                    "rail_adjustments": [
                        {
                            "rail_type": adj.rail_type,
                            "original_weight": adj.original_weight,
                            "adjusted_weight": adj.adjusted_weight,
                            "adjustment_factor": adj.adjustment_factor,
                            "reason": adj.reason,
                        }
                        for adj in trust_response.rail_adjustments
                    ],
                    "explanation": trust_response.explanation,
                    "event_emitted": event_emitted,
                    "event_id": event_id,
                    "timestamp": trust_response.timestamp.isoformat(),
                    "metadata": trust_response.metadata,
                },
            )

        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown verb: {request.verb}. Supported verbs: getStatus, isAllowedProvider, verifyKYB, getTrustSignal"
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Internal server error: {str(e)}"
        ) from e


def _is_provider_allowed(provider_id: str) -> bool:
    """
    Determine if a provider is allowed in the trust registry.

    This is a stub implementation that returns deterministic results
    based on the provider_id for testing purposes.

    Args:
        provider_id: Unique identifier for the provider

    Returns:
        bool: True if provider is allowed, False otherwise
    """
    # Stub logic: allow providers with IDs starting with "trusted_"
    # or containing "verified", deny others
    provider_lower = provider_id.lower()

    if provider_lower.startswith("trusted_"):
        return True
    elif "verified" in provider_lower:
        return True
    elif provider_lower.startswith("blocked_"):
        return False
    elif "suspicious" in provider_lower:
        return False
    else:
        # Default: allow if provider_id length is even, deny if odd
        # This provides deterministic behavior for testing
        return len(provider_id) % 2 == 0
