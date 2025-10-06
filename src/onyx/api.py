"""
FastAPI application for Onyx Trust Registry service.
"""

from typing import Any, Optional, List

from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field

from onyx.ce import create_kyb_verified_payload, emit_kyb_verified_ce, get_trace_id
from onyx.kyb import validate_kyb_payload, verify_kyb
from onyx.mcp.server import mcp_router
from onyx.trust_registry import get_trust_registry
from onyx.trust_signals import get_trust_signal, TrustContext
from onyx.trust_events import emit_trust_signal_event
from onyx.llm.explain import is_trust_llm_configured

# Import ML-enhanced trust signals
try:
    from .ml_enhanced_trust_signals import ml_enhanced_trust_signals
    ML_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ ML models not available: {e}")
    ML_AVAILABLE = False

# Phase 4 imports
from onyx.trust_registry_v1 import get_trust_registry_v1
from onyx.trust_signals_v1 import get_trust_signal_generator
from onyx.models import (
    AddProviderRequest, RevokeProviderRequest, ListProvidersRequest,
    TrustSignalRequest, ProviderVerificationRequest, TrustRegistryStats,
    TrustRegistryProvider, ListProvidersResponse, ProviderVerificationResponse,
    TrustSignalResponse
)

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


class TrustSignalRequest(BaseModel):
    """Trust signal generation request model."""
    
    trace_id: str = Field(..., description="Trace identifier")
    context: TrustContext = Field(..., description="Trust context with features")
    original_weights: dict[str, float] = Field(
        default_factory=lambda: {"ACH": 0.4, "debit": 0.3, "credit": 0.3},
        description="Original rail weights"
    )
    deterministic_seed: int = Field(42, description="Seed for deterministic results")
    merchant_context: dict[str, Any] = Field(
        default_factory=dict, description="Merchant context information"
    )
    cart_summary: dict[str, Any] = Field(
        default_factory=dict, description="Cart summary information"
    )
    rail_candidates: list[dict[str, Any]] = Field(
        default_factory=list, description="Available rail candidates"
    )


class TrustSignalResponse(BaseModel):
    """Trust signal generation response model."""
    
    trace_id: str = Field(..., description="Trace identifier")
    trust_score: float = Field(..., ge=0.0, le=1.0, description="Trust score (0-1)")
    risk_level: str = Field(..., description="Risk level: low, medium, high")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence")
    model_type: str = Field(..., description="Model type used")
    feature_contributions: dict[str, float] = Field(..., description="Feature contributions")
    rail_adjustments: list[dict[str, Any]] = Field(..., description="Rail weight adjustments")
    explanation: str = Field(..., description="Human-readable explanation")
    event_emitted: bool = Field(..., description="Whether CloudEvent was emitted")
    event_id: str | None = Field(None, description="CloudEvent ID if emitted")
    timestamp: str = Field(..., description="Response timestamp")
    metadata: dict[str, Any] = Field(..., description="Additional metadata")


@app.post("/trust/signal", response_model=TrustSignalResponse)
async def generate_trust_signal(
    request: TrustSignalRequest,
    emit_ce: bool = Query(True, description="Emit CloudEvent for trust signal")
) -> TrustSignalResponse:
    """
    Generate trust signal with ML scoring and rail adjustments.
    
    This endpoint provides trust signal generation with:
    - ML-powered trust scoring based on device reputation, velocity, IP risk, and history
    - Rail weight adjustments based on risk level
    - CloudEvent emission for trust signal (ocn.onyx.trust_signal.v1)
    - Human-readable explanations for trust decisions
    
    Args:
        request: Trust signal generation request
        emit_ce: Whether to emit CloudEvent
        
    Returns:
        Trust signal response with scoring and adjustments
    """
    try:
        # Generate trust signal (ML-enhanced if available)
        if ML_AVAILABLE:
            trust_response = ml_enhanced_trust_signals.generate_enhanced_trust_signal(
                trace_id=request.trace_id,
                context=request.context,
                original_weights=request.original_weights,
                deterministic_seed=request.deterministic_seed,
                transaction_amount=getattr(request, 'transaction_amount', None),
                merchant_id=getattr(request, 'merchant_id', None),
                user_id=getattr(request, 'user_id', None)
            )
        else:
            trust_response = get_trust_signal(
                trace_id=request.trace_id,
                context=request.context,
                original_weights=request.original_weights,
                deterministic_seed=request.deterministic_seed
            )
        
        # Emit CloudEvent if requested
        event_emitted = False
        event_id = None
        
        if emit_ce:
            try:
                event = emit_trust_signal_event(
                    trust_response=trust_response,
                    context=request.context,
                    merchant_context=request.merchant_context,
                    cart_summary=request.cart_summary,
                    rail_candidates=request.rail_candidates
                )
                event_emitted = True
                event_id = event.id
            except Exception as e:
                # Log error but don't fail the request
                pass
        
        # Format rail adjustments
        rail_adjustments = [
            {
                "rail_type": adj.rail_type,
                "original_weight": adj.original_weight,
                "adjusted_weight": adj.adjusted_weight,
                "adjustment_factor": adj.adjustment_factor,
                "reason": adj.reason,
            }
            for adj in trust_response.rail_adjustments
        ]
        
        return TrustSignalResponse(
            trace_id=trust_response.trace_id,
            trust_score=trust_response.trust_score_result.trust_score,
            risk_level=trust_response.trust_score_result.risk_level,
            confidence=trust_response.trust_score_result.confidence,
            model_type=trust_response.trust_score_result.model_type,
            feature_contributions=trust_response.trust_score_result.feature_contributions,
            rail_adjustments=rail_adjustments,
            explanation=trust_response.explanation,
            event_emitted=event_emitted,
            event_id=event_id,
            timestamp=trust_response.timestamp.isoformat(),
            metadata=trust_response.metadata,
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating trust signal: {str(e)}",
        ) from e


@app.get("/trust/signal/status")
async def get_trust_signal_status() -> dict[str, Any]:
    """
    Get trust signal service status and capabilities.
    
    Returns:
        Status information including LLM configuration
    """
    return {
        "service": "onyx-trust-signals",
        "version": "0.3.0",
        "status": "operational",
        "capabilities": {
            "ml_scoring": True,
            "rail_adjustments": True,
            "cloud_events": True,
            "llm_explanations": is_trust_llm_configured(),
        },
        "features": {
            "device_reputation_scoring": True,
            "velocity_analysis": True,
            "ip_risk_assessment": True,
            "history_length_evaluation": True,
            "deterministic_scoring": True,
        },
        "supported_rails": ["ACH", "debit", "credit"],
        "risk_levels": ["low", "medium", "high"],
    }


@app.get("/ml/status", response_model=dict[str, Any])
async def get_ml_status():
    """Get ML model status and configuration."""
    if not ML_AVAILABLE:
        return {
            "ml_enabled": False,
            "error": "ML models not available"
        }
    
    try:
        from .ml.trust_scoring import get_trust_scorer
        from .ml.risk_assessment import get_risk_assessor
        
        trust_scorer = get_trust_scorer()
        risk_assessor = get_risk_assessor()
        
        return {
            "ml_enabled": ml_enhanced_trust_signals.use_ml,
            "ml_weight": ml_enhanced_trust_signals.ml_weight,
            "models": {
                "trust_scoring": {
                    "loaded": trust_scorer.is_loaded,
                    "model_type": trust_scorer.metadata.get("model_type", "unknown"),
                    "version": trust_scorer.metadata.get("version", "unknown"),
                    "training_date": trust_scorer.metadata.get("trained_on", "unknown"),
                    "features": len(trust_scorer.feature_names) if trust_scorer.feature_names else 0
                },
                "risk_assessment": {
                    "loaded": risk_assessor.is_loaded,
                    "model_type": risk_assessor.metadata.get("model_type", "unknown"),
                    "version": risk_assessor.metadata.get("version", "unknown"),
                    "training_date": risk_assessor.metadata.get("trained_on", "unknown"),
                    "features": len(risk_assessor.feature_names) if risk_assessor.feature_names else 0
                }
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get ML status: {str(e)}",
        )


@app.get("/trust/signal/sample-context")
async def get_sample_trust_context() -> dict[str, Any]:
    """
    Get sample trust context for testing.
    
    Returns:
        Sample trust context data
    """
    return {
        "low_risk_context": {
            "device_reputation": 0.9,
            "velocity": 1.0,
            "ip_risk": 0.1,
            "history_len": 100,
            "user_id": "user_001",
            "session_id": "session_001",
            "merchant_id": "merchant_001",
            "channel": "online",
            "amount": 50.0,
        },
        "medium_risk_context": {
            "device_reputation": 0.6,
            "velocity": 4.0,
            "ip_risk": 0.5,
            "history_len": 15,
            "user_id": "user_002",
            "session_id": "session_002",
            "merchant_id": "merchant_002",
            "channel": "online",
            "amount": 150.0,
        },
        "high_risk_context": {
            "device_reputation": 0.2,
            "velocity": 15.0,
            "ip_risk": 0.8,
            "history_len": 2,
            "user_id": "user_003",
            "session_id": "session_003",
            "merchant_id": "merchant_003",
            "channel": "online",
            "amount": 500.0,
        },
    }


# Phase 4 - Trust Registry v1 API Endpoints

@app.post("/v1/trust-registry/providers", response_model=TrustRegistryProvider, status_code=status.HTTP_201_CREATED)
async def add_provider(request: AddProviderRequest) -> TrustRegistryProvider:
    """
    Add a new provider to the trust registry.
    
    - **provider_id**: Unique identifier for the provider
    - **provider_name**: Human-readable name for the provider
    - **provider_type**: Type of provider (payment_processor, credential_provider, etc.)
    - **organization**: Organization name
    - **jurisdiction**: Legal jurisdiction
    - **capabilities**: List of provider capabilities
    - **supported_rails**: List of supported payment rails
    """
    try:
        registry = get_trust_registry_v1()
        provider = registry.add_provider(request)
        return provider
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/v1/trust-registry/providers/{provider_id}/revoke", response_model=TrustRegistryProvider)
async def revoke_provider(provider_id: str, request: RevokeProviderRequest) -> TrustRegistryProvider:
    """
    Revoke a provider from the trust registry.
    
    - **provider_id**: Provider identifier to revoke
    - **reason**: Reason for revocation
    - **effective_date**: When revocation takes effect (optional)
    """
    try:
        registry = get_trust_registry_v1()
        if request.provider_id != provider_id:
            request.provider_id = provider_id  # Ensure consistency
        provider = registry.revoke_provider(request)
        return provider
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/v1/trust-registry/providers", response_model=ListProvidersResponse)
async def list_providers(
    status: Optional[str] = Query(None, description="Filter by provider status"),
    provider_type: Optional[str] = Query(None, description="Filter by provider type"),
    trust_level: Optional[str] = Query(None, description="Filter by trust level"),
    capability: Optional[str] = Query(None, description="Filter by capability"),
    jurisdiction: Optional[str] = Query(None, description="Filter by jurisdiction"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of providers to return"),
    offset: int = Query(0, ge=0, description="Number of providers to skip")
) -> ListProvidersResponse:
    """
    List providers from the trust registry with optional filtering.
    
    - **status**: Filter by provider status (active, suspended, revoked, pending, under_review)
    - **provider_type**: Filter by provider type (payment_processor, credential_provider, etc.)
    - **trust_level**: Filter by trust level (critical, high, medium, low, untrusted)
    - **capability**: Filter by specific capability
    - **jurisdiction**: Filter by legal jurisdiction
    - **limit**: Maximum number of providers to return (1-1000)
    - **offset**: Number of providers to skip for pagination
    """
    try:
        registry = get_trust_registry_v1()
        
        # Create request object
        request = ListProvidersRequest(
            status=status,
            provider_type=provider_type,
            trust_level=trust_level,
            capability=capability,
            jurisdiction=jurisdiction,
            limit=limit,
            offset=offset
        )
        
        response = registry.list_providers(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/v1/trust-registry/providers/{provider_id}", response_model=TrustRegistryProvider)
async def get_provider(provider_id: str) -> TrustRegistryProvider:
    """
    Get a specific provider by ID.
    
    - **provider_id**: Provider identifier
    """
    try:
        registry = get_trust_registry_v1()
        provider = registry.get_provider(provider_id)
        if not provider:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Provider {provider_id} not found")
        return provider
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/v1/trust-registry/providers/{provider_id}/verify", response_model=ProviderVerificationResponse)
async def verify_provider(provider_id: str, request: ProviderVerificationRequest) -> ProviderVerificationResponse:
    """
    Verify a provider's credentials and capabilities.
    
    - **provider_id**: Provider identifier to verify
    - **verification_type**: Type of verification to perform
    - **verification_data**: Data required for verification
    - **requested_capabilities**: Capabilities to verify
    """
    try:
        registry = get_trust_registry_v1()
        if request.provider_id != provider_id:
            request.provider_id = provider_id  # Ensure consistency
        verification = registry.verify_provider(request)
        return verification
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.get("/v1/trust-registry/stats", response_model=TrustRegistryStats)
async def get_trust_registry_stats() -> TrustRegistryStats:
    """
    Get comprehensive statistics about the trust registry.
    
    Returns statistics including provider counts by status, type, trust level,
    capabilities, and jurisdiction, along with trust metrics.
    """
    try:
        registry = get_trust_registry_v1()
        stats = registry.get_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/v1/trust-signals", response_model=TrustSignalResponse)
async def generate_trust_signal(request: TrustSignalRequest) -> TrustSignalResponse:
    """
    Generate trust signal for negotiation.
    
    - **trace_id**: Transaction trace ID
    - **provider_id**: Provider identifier to evaluate
    - **rail_type**: Payment rail type
    - **transaction_context**: Transaction context data
    - **user_context**: User context data
    - **merchant_context**: Merchant context data
    - **amount**: Transaction amount
    - **currency**: Currency code
    """
    try:
        generator = get_trust_signal_generator()
        signal = generator.generate_trust_signal(request)
        return signal
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@app.post("/v1/trust-signals/batch", response_model=List[TrustSignalResponse])
async def batch_generate_trust_signals(requests: List[TrustSignalRequest]) -> List[TrustSignalResponse]:
    """
    Generate trust signals for multiple providers in batch.
    
    - **requests**: List of trust signal requests
    
    Returns list of trust signal responses for all requested providers.
    """
    try:
        generator = get_trust_signal_generator()
        signals = generator.batch_generate_signals(requests)
        return signals
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


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
