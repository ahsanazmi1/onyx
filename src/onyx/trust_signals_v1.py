"""
Enhanced trust signal generation for Onyx Phase 4.

Provides trust signal generation during negotiation with provider evaluation,
rail preference adjustment, and CloudEvent emission for trust-based decision making.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from onyx.models import (
    TrustSignalRequest, TrustSignalResponse, TrustRegistryProvider,
    ProviderType, TrustLevel, ProviderStatus
)
from onyx.trust_registry_v1 import get_trust_registry_v1
from onyx.trust_events import emit_trust_signal_event

logger = logging.getLogger(__name__)


class TrustSignalGenerator:
    """
    Enhanced trust signal generator for Phase 4.
    
    Generates comprehensive trust signals during negotiation with provider
    evaluation, rail preference adjustment, and risk assessment.
    """
    
    def __init__(self):
        """Initialize trust signal generator."""
        self.trust_registry = get_trust_registry_v1()
        logger.info("Trust signal generator initialized")
    
    def generate_trust_signal(self, request: TrustSignalRequest) -> TrustSignalResponse:
        """
        Generate trust signal for negotiation.
        
        Args:
            request: Trust signal request
            
        Returns:
            Trust signal response with provider evaluation and rail adjustment
        """
        # Get provider from trust registry
        provider = self.trust_registry.get_provider(request.provider_id)
        
        if not provider:
            # Provider not found in registry
            return self._create_negative_signal(request, "Provider not found in trust registry")
        
        # Generate comprehensive trust assessment
        trust_assessment = self.trust_registry.get_trust_signal_for_provider(
            request.provider_id,
            request.rail_type,
            request.transaction_context
        )
        
        # Calculate rail preference adjustment
        original_preference = 1.0  # Default preference
        adjusted_preference, adjustment = self._calculate_rail_preference_adjustment(
            trust_assessment, request.transaction_context
        )
        
        # Generate explanation
        explanation = self._generate_explanation(trust_assessment, provider, request)
        
        # Generate recommendation
        recommendation = self._generate_recommendation(trust_assessment, adjusted_preference)
        
        # Create trust signal response
        signal = TrustSignalResponse(
            signal_id=str(uuid.uuid4()),
            trace_id=request.trace_id,
            provider_id=request.provider_id,
            rail_type=request.rail_type,
            trust_score=trust_assessment["trust_score"],
            risk_level=trust_assessment["risk_level"],
            confidence=trust_assessment["confidence"],
            original_rail_preference=original_preference,
            adjusted_rail_preference=adjusted_preference,
            preference_adjustment=adjustment,
            trust_factors=trust_assessment.get("trust_factors", {}),
            risk_factors=self._extract_risk_factors(trust_assessment, request),
            explanation=explanation,
            recommendation=recommendation,
            expires_at=datetime.now() + timedelta(hours=1),
            metadata={
                "generation_method": "trust_registry_v1",
                "provider_verified": provider.verified_at is not None,
                "rail_supported": request.rail_type in provider.supported_rails,
                "transaction_context": request.transaction_context
            }
        )
        
        # Emit trust signal event
        try:
            event = emit_trust_signal_event(signal)
            logger.info(f"Emitted trust signal event for provider {request.provider_id}")
        except Exception as e:
            logger.error(f"Failed to emit trust signal event: {e}")
        
        logger.info(f"Generated trust signal for {request.provider_id}: {trust_assessment['risk_level']} risk")
        return signal
    
    def _create_negative_signal(
        self,
        request: TrustSignalRequest,
        reason: str
    ) -> TrustSignalResponse:
        """Create negative trust signal for problematic providers."""
        return TrustSignalResponse(
            signal_id=str(uuid.uuid4()),
            trace_id=request.trace_id,
            provider_id=request.provider_id,
            rail_type=request.rail_type,
            trust_score=0.0,
            risk_level="critical",
            confidence=1.0,
            original_rail_preference=1.0,
            adjusted_rail_preference=0.0,
            preference_adjustment=-1.0,
            trust_factors={},
            risk_factors={"provider_not_found": 1.0},
            explanation=f"Provider {request.provider_id} not found in trust registry: {reason}",
            recommendation="block",
            expires_at=datetime.now() + timedelta(hours=1),
            metadata={
                "generation_method": "trust_registry_v1",
                "error": reason
            }
        )
    
    def _calculate_rail_preference_adjustment(
        self,
        trust_assessment: Dict[str, Any],
        context: Dict[str, Any]
    ) -> tuple[float, float]:
        """
        Calculate rail preference adjustment based on trust assessment.
        
        Args:
            trust_assessment: Trust assessment from registry
            context: Transaction context
            
        Returns:
            Tuple of (adjusted_preference, adjustment_amount)
        """
        trust_score = trust_assessment["trust_score"]
        risk_level = trust_assessment["risk_level"]
        
        # Base adjustment from trust score
        base_adjustment = (trust_score - 0.5) * 2.0  # Scale to [-1, 1]
        
        # Risk level adjustments
        risk_adjustments = {
            "low": 0.2,
            "medium": -0.2,
            "high": -0.5,
            "critical": -1.0
        }
        
        risk_adjustment = risk_adjustments.get(risk_level, -0.5)
        
        # Context-based adjustments
        context_adjustment = 0.0
        
        # Adjust for transaction amount
        amount = context.get("amount", 0)
        if amount > 10000:  # High value transaction
            context_adjustment -= 0.1  # Require higher trust
        elif amount < 100:  # Low value transaction
            context_adjustment += 0.1  # Allow lower trust
        
        # Adjust for merchant risk
        merchant_risk = context.get("merchant_risk_score", 0.5)
        if merchant_risk > 0.7:  # High risk merchant
            context_adjustment -= 0.2
        elif merchant_risk < 0.3:  # Low risk merchant
            context_adjustment += 0.1
        
        # Calculate final adjustment
        total_adjustment = base_adjustment + risk_adjustment + context_adjustment
        
        # Clamp to valid range
        total_adjustment = max(-1.0, min(1.0, total_adjustment))
        
        # Calculate adjusted preference
        original_preference = 1.0
        adjusted_preference = max(0.0, min(1.0, original_preference + total_adjustment))
        
        return adjusted_preference, total_adjustment
    
    def _extract_risk_factors(
        self,
        trust_assessment: Dict[str, Any],
        request: TrustSignalRequest
    ) -> Dict[str, float]:
        """Extract risk factors from trust assessment and context."""
        risk_factors = {}
        
        # Provider risk factors
        provider_info = trust_assessment.get("provider_info", {})
        if provider_info.get("status") != ProviderStatus.ACTIVE:
            risk_factors["provider_inactive"] = 0.8
        
        if provider_info.get("trust_level") in [TrustLevel.LOW, TrustLevel.UNTRUSTED]:
            risk_factors["low_trust_level"] = 0.6
        
        # Transaction context risk factors
        context = request.transaction_context
        
        # Amount-based risks
        amount = context.get("amount", 0)
        if amount > 50000:
            risk_factors["high_amount"] = 0.4
        elif amount < 10:
            risk_factors["low_amount"] = 0.2
        
        # Velocity-based risks
        velocity = context.get("velocity", 0)
        if velocity > 100:  # High transaction velocity
            risk_factors["high_velocity"] = 0.5
        
        # Geographic risks
        if context.get("cross_border", False):
            risk_factors["cross_border"] = 0.3
        
        # Time-based risks
        if context.get("off_hours", False):
            risk_factors["off_hours"] = 0.2
        
        return risk_factors
    
    def _generate_explanation(
        self,
        trust_assessment: Dict[str, Any],
        provider: TrustRegistryProvider,
        request: TrustSignalRequest
    ) -> str:
        """Generate human-readable explanation of trust assessment."""
        explanation_parts = []
        
        # Provider information
        explanation_parts.append(f"Provider {provider.provider_name} ({provider.trust_level} trust level)")
        
        # Trust score
        trust_score = trust_assessment["trust_score"]
        explanation_parts.append(f"Trust score: {trust_score:.2f}")
        
        # Risk level
        risk_level = trust_assessment["risk_level"]
        explanation_parts.append(f"Risk assessment: {risk_level}")
        
        # Status information
        if provider.status != ProviderStatus.ACTIVE:
            explanation_parts.append(f"Provider status: {provider.status}")
        
        # Rail support
        if request.rail_type not in provider.supported_rails:
            explanation_parts.append(f"Rail {request.rail_type} not supported by provider")
        
        # Trust factors
        trust_factors = trust_assessment.get("trust_factors", {})
        if trust_factors:
            factor_explanations = []
            if trust_factors.get("rail_support") is False:
                factor_explanations.append("unsupported rail")
            if trust_factors.get("status_multiplier", 1.0) < 1.0:
                factor_explanations.append("inactive status")
            
            if factor_explanations:
                explanation_parts.append(f"Risk factors: {', '.join(factor_explanations)}")
        
        return ". ".join(explanation_parts) + "."
    
    def _generate_recommendation(
        self,
        trust_assessment: Dict[str, Any],
        adjusted_preference: float
    ) -> str:
        """Generate recommendation based on trust assessment."""
        risk_level = trust_assessment["risk_level"]
        trust_score = trust_assessment["trust_score"]
        
        if risk_level == "critical" or trust_score < 0.3:
            return "Block transaction - critical risk detected"
        elif risk_level == "high" or trust_score < 0.5:
            return "Restrict transaction - high risk detected"
        elif risk_level == "medium" or trust_score < 0.7:
            return "Review transaction - medium risk detected"
        elif adjusted_preference < 0.3:
            return "Consider alternative rails - low preference"
        else:
            return "Allow transaction - acceptable risk level"
    
    def batch_generate_signals(
        self,
        requests: List[TrustSignalRequest]
    ) -> List[TrustSignalResponse]:
        """
        Generate trust signals for multiple providers in batch.
        
        Args:
            requests: List of trust signal requests
            
        Returns:
            List of trust signal responses
        """
        signals = []
        
        for request in requests:
            try:
                signal = self.generate_trust_signal(request)
                signals.append(signal)
            except Exception as e:
                logger.error(f"Failed to generate trust signal for {request.provider_id}: {e}")
                # Create error signal
                error_signal = self._create_negative_signal(request, f"Generation failed: {str(e)}")
                signals.append(error_signal)
        
        logger.info(f"Generated {len(signals)} trust signals in batch")
        return signals


# Global instance
_trust_signal_generator = None


def get_trust_signal_generator() -> TrustSignalGenerator:
    """Get global trust signal generator instance."""
    global _trust_signal_generator
    if _trust_signal_generator is None:
        _trust_signal_generator = TrustSignalGenerator()
    return _trust_signal_generator








