"""
LLM explanation generation for Onyx trust signals.

Provides optional LLM-powered explanations for trust signal decisions and rail adjustments.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from onyx.trust_signals import TrustSignalResponse, TrustContext, RailWeightAdjustment

logger = logging.getLogger(__name__)


class LLMExplanationRequest(BaseModel):
    """Request for LLM explanation generation."""
    
    trust_response: TrustSignalResponse = Field(..., description="Trust signal response")
    context: TrustContext = Field(..., description="Original trust context")
    merchant_context: Optional[Dict[str, Any]] = Field(None, description="Merchant context")
    cart_summary: Optional[Dict[str, Any]] = Field(None, description="Cart summary")
    rail_candidates: Optional[List[Dict[str, Any]]] = Field(None, description="Rail candidates")


class LLMExplanationResponse(BaseModel):
    """Response from LLM explanation generation."""
    
    explanation: str = Field(..., description="LLM-generated explanation")
    key_factors: List[str] = Field(default_factory=list, description="Key risk factors identified")
    rail_impact: Dict[str, str] = Field(default_factory=dict, description="Rail-specific impact explanations")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Explanation confidence")
    model_used: str = Field(..., description="LLM model used for explanation")


class TrustLLMExplainer:
    """LLM explainer for trust signal decisions."""
    
    def __init__(self):
        """Initialize the LLM explainer."""
        self.azure_openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        self.azure_openai_key = os.getenv("AZURE_OPENAI_API_KEY")
        self.azure_openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "onyx-llm")
        self.azure_openai_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        
        self.is_configured = bool(
            self.azure_openai_endpoint and 
            self.azure_openai_key and 
            self.azure_openai_deployment
        )
        
        if self.is_configured:
            logger.info(f"Trust LLM Explainer configured with deployment: {self.azure_openai_deployment}")
        else:
            logger.info("Trust LLM Explainer not configured - using fallback explanations")
    
    def get_configuration_status(self) -> Dict[str, Any]:
        """Get the configuration status of the LLM explainer."""
        return {
            "configured": self.is_configured,
            "endpoint": self.azure_openai_endpoint is not None,
            "api_key": self.azure_openai_key is not None,
            "deployment": self.azure_openai_deployment,
            "version": self.azure_openai_version,
        }
    
    def explain_trust_decision(self, request: LLMExplanationRequest) -> Optional[LLMExplanationResponse]:
        """
        Generate LLM explanation for trust signal decision.
        
        Args:
            request: LLM explanation request
            
        Returns:
            LLM explanation response or None if not configured
        """
        if not self.is_configured:
            return None
        
        try:
            # Prepare context for LLM
            trust_data = {
                "trust_score": request.trust_response.trust_score_result.trust_score,
                "risk_level": request.trust_response.trust_score_result.risk_level,
                "confidence": request.trust_response.trust_score_result.confidence,
                "feature_contributions": request.trust_response.trust_score_result.feature_contributions,
                "rail_adjustments": [
                    {
                        "rail_type": adj.rail_type,
                        "original_weight": adj.original_weight,
                        "adjusted_weight": adj.adjusted_weight,
                        "adjustment_factor": adj.adjustment_factor,
                        "reason": adj.reason,
                    }
                    for adj in request.trust_response.rail_adjustments
                ],
                "context_features": {
                    "device_reputation": request.context.device_reputation,
                    "velocity": request.context.velocity,
                    "ip_risk": request.context.ip_risk,
                    "history_len": request.context.history_len,
                    "channel": request.context.channel,
                },
                "merchant_context": request.merchant_context or {},
                "cart_summary": request.cart_summary or {},
            }
            
            # Create prompt for LLM
            prompt = self._create_trust_explanation_prompt(trust_data)
            
            # Call Azure OpenAI (stub implementation)
            # In a real implementation, this would make an actual API call
            explanation = self._generate_llm_explanation(prompt, trust_data)
            
            return LLMExplanationResponse(
                explanation=explanation["explanation"],
                key_factors=explanation["key_factors"],
                rail_impact=explanation["rail_impact"],
                confidence=explanation["confidence"],
                model_used=f"azure-openai-{self.azure_openai_deployment}",
            )
            
        except Exception as e:
            logger.error(f"LLM explanation generation failed: {e}")
            return None
    
    def _create_trust_explanation_prompt(self, trust_data: Dict[str, Any]) -> str:
        """Create prompt for trust explanation."""
        return f"""
You are an expert in payment risk assessment and trust signal analysis. 

Analyze the following trust signal data and provide a clear, concise explanation of the risk assessment and rail adjustments:

Trust Score: {trust_data['trust_score']:.3f}
Risk Level: {trust_data['risk_level']}
Confidence: {trust_data['confidence']:.3f}

Feature Contributions:
- Device Reputation: {trust_data['feature_contributions'].get('device_reputation', 0):.3f}
- Velocity: {trust_data['feature_contributions'].get('velocity', 0):.3f}
- IP Risk: {trust_data['feature_contributions'].get('ip_risk', 0):.3f}
- History Length: {trust_data['feature_contributions'].get('history_len', 0):.3f}

Context Features:
- Device Reputation: {trust_data['context_features']['device_reputation']:.3f}
- Transaction Velocity: {trust_data['context_features']['velocity']:.1f} tx/hour
- IP Risk Score: {trust_data['context_features']['ip_risk']:.3f}
- History Length: {trust_data['context_features']['history_len']} transactions
- Channel: {trust_data['context_features']['channel']}

Rail Adjustments:
{json.dumps(trust_data['rail_adjustments'], indent=2)}

Provide a structured explanation in JSON format with:
1. "explanation": A clear, human-readable explanation of the trust assessment
2. "key_factors": List of key risk factors that influenced the decision
3. "rail_impact": Object explaining the impact on each rail type
4. "confidence": Confidence score for the explanation (0-1)

Focus on:
- Why the trust score was calculated as it was
- Which features contributed most to the risk assessment
- How the rail adjustments reflect the risk level
- Specific recommendations for the payment rails
"""

    def _generate_llm_explanation(self, prompt: str, trust_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate LLM explanation (stub implementation).
        
        In a real implementation, this would call Azure OpenAI API.
        """
        # Stub implementation - generate deterministic explanation based on trust data
        trust_score = trust_data["trust_score"]
        risk_level = trust_data["risk_level"]
        
        # Identify key factors
        key_factors = []
        if trust_data["context_features"]["device_reputation"] < 0.5:
            key_factors.append("low device reputation")
        if trust_data["context_features"]["velocity"] > 5.0:
            key_factors.append("high transaction velocity")
        if trust_data["context_features"]["ip_risk"] > 0.7:
            key_factors.append("elevated IP risk")
        if trust_data["context_features"]["history_len"] < 10:
            key_factors.append("limited transaction history")
        
        # Generate explanation
        if risk_level == "high":
            explanation = f"High risk assessment (score: {trust_score:.2f}) due to {', '.join(key_factors) if key_factors else 'multiple risk factors'}. "
            explanation += "ACH rail significantly down-weighted due to elevated risk profile. Credit card recommended for enhanced security."
        elif risk_level == "medium":
            explanation = f"Medium risk assessment (score: {trust_score:.2f}) with {', '.join(key_factors) if key_factors else 'moderate risk indicators'}. "
            explanation += "Minor rail adjustments applied to balance risk and cost efficiency."
        else:
            explanation = f"Low risk assessment (score: {trust_score:.2f}) with strong trust indicators. "
            explanation += "All payment rails available with minimal restrictions."
        
        # Rail impact explanations
        rail_impact = {}
        for adj in trust_data["rail_adjustments"]:
            rail_type = adj["rail_type"]
            factor = adj["adjustment_factor"]
            
            if factor < 0.5:
                rail_impact[rail_type] = f"{rail_type.upper()} significantly down-weighted due to risk concerns"
            elif factor < 0.8:
                rail_impact[rail_type] = f"{rail_type.upper()} moderately adjusted for risk management"
            else:
                rail_impact[rail_type] = f"{rail_type.upper()} weight maintained with minimal risk impact"
        
        return {
            "explanation": explanation,
            "key_factors": key_factors,
            "rail_impact": rail_impact,
            "confidence": 0.85,  # High confidence for deterministic explanations
        }


def is_trust_llm_configured() -> bool:
    """Check if trust LLM is configured."""
    explainer = TrustLLMExplainer()
    return explainer.is_configured


def explain_trust_signal_llm(
    trust_response: TrustSignalResponse,
    context: TrustContext,
    merchant_context: Optional[Dict[str, Any]] = None,
    cart_summary: Optional[Dict[str, Any]] = None,
    rail_candidates: Optional[List[Dict[str, Any]]] = None
) -> Optional[LLMExplanationResponse]:
    """
    Generate LLM explanation for trust signal.
    
    Args:
        trust_response: Trust signal response
        context: Original trust context
        merchant_context: Merchant context information
        cart_summary: Cart summary information
        rail_candidates: Available rail candidates
        
    Returns:
        LLM explanation response or None if not configured
    """
    explainer = TrustLLMExplainer()
    
    request = LLMExplanationRequest(
        trust_response=trust_response,
        context=context,
        merchant_context=merchant_context,
        cart_summary=cart_summary,
        rail_candidates=rail_candidates
    )
    
    return explainer.explain_trust_decision(request)
