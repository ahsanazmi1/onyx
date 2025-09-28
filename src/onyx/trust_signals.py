"""
Trust signal generation and ML scoring for Onyx Phase 3.

Provides trust scoring based on device reputation, velocity, IP risk, and history length.
Generates rail weight adjustments and trust signal explanations.
"""

import json
import logging
import random
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TrustContext(BaseModel):
    """Context data for trust signal generation."""
    
    device_reputation: float = Field(..., ge=0.0, le=1.0, description="Device reputation score (0-1)")
    velocity: float = Field(..., ge=0.0, description="Transaction velocity (transactions per hour)")
    ip_risk: float = Field(..., ge=0.0, le=1.0, description="IP risk score (0-1)")
    history_len: int = Field(..., ge=0, description="Transaction history length")
    user_id: Optional[str] = Field(None, description="User identifier")
    session_id: Optional[str] = Field(None, description="Session identifier")
    merchant_id: Optional[str] = Field(None, description="Merchant identifier")
    channel: str = Field("online", description="Transaction channel")
    amount: Optional[float] = Field(None, description="Transaction amount")


class TrustScoreResult(BaseModel):
    """Result of trust score calculation."""
    
    trust_score: float = Field(..., ge=0.0, le=1.0, description="Overall trust score (0-1)")
    risk_level: str = Field(..., description="Risk level: low, medium, high")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence (0-1)")
    model_type: str = Field(..., description="Model type used for scoring")
    feature_contributions: Dict[str, float] = Field(..., description="Individual feature contributions")
    timestamp: datetime = Field(default_factory=datetime.now, description="Score generation timestamp")


class RailWeightAdjustment(BaseModel):
    """Rail weight adjustment based on trust signals."""
    
    rail_type: str = Field(..., description="Rail type: ACH, debit, credit")
    original_weight: float = Field(..., ge=0.0, le=1.0, description="Original weight")
    adjusted_weight: float = Field(..., ge=0.0, le=1.0, description="Adjusted weight")
    adjustment_factor: float = Field(..., description="Multiplicative adjustment factor")
    reason: str = Field(..., description="Reason for adjustment")


class TrustSignalResponse(BaseModel):
    """Complete trust signal response."""
    
    trace_id: str = Field(..., description="Trace identifier")
    trust_score_result: TrustScoreResult = Field(..., description="Trust score calculation")
    rail_adjustments: List[RailWeightAdjustment] = Field(..., description="Rail weight adjustments")
    explanation: str = Field(..., description="Human-readable explanation")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")


class TrustSignalMLModel:
    """ML stub for trust signal scoring."""
    
    def __init__(self, deterministic_seed: int = 42):
        """Initialize the ML model with deterministic seed."""
        self.deterministic_seed = deterministic_seed
        random.seed(deterministic_seed)
        np.random.seed(deterministic_seed)
        
        # Model parameters (simulated)
        self.feature_weights = {
            "device_reputation": 0.35,
            "velocity": 0.25,
            "ip_risk": 0.25,
            "history_len": 0.15,
        }
        
        # Risk thresholds
        self.risk_thresholds = {
            "low": 0.7,
            "medium": 0.4,
            "high": 0.0,
        }
        
        logger.info(f"TrustSignalMLModel initialized with seed {deterministic_seed}")
    
    def score_trust(self, context: TrustContext) -> TrustScoreResult:
        """
        Calculate trust score using ML stub.
        
        Args:
            context: Trust context with features
            
        Returns:
            Trust score result with confidence and feature contributions
        """
        # Normalize features
        normalized_velocity = min(1.0, context.velocity / 10.0)  # Cap at 10 tx/hour
        normalized_history = min(1.0, context.history_len / 100.0)  # Cap at 100 transactions
        
        # Calculate weighted score
        features = {
            "device_reputation": context.device_reputation,
            "velocity": 1.0 - normalized_velocity,  # Invert velocity (higher = riskier)
            "ip_risk": 1.0 - context.ip_risk,  # Invert IP risk (higher = riskier)
            "history_len": normalized_history,
        }
        
        # Weighted sum
        trust_score = sum(
            features[feature] * weight 
            for feature, weight in self.feature_weights.items()
        )
        
        # Add some deterministic noise for realism (but keep it deterministic)
        # Use a hash of the context for deterministic noise
        import hashlib
        context_hash = hashlib.md5(str(context.model_dump()).encode()).hexdigest()
        noise_seed = int(context_hash[:8], 16) % 1000
        np.random.seed(noise_seed)
        noise = np.random.normal(0, 0.05)
        trust_score = max(0.0, min(1.0, trust_score + noise))
        
        # Determine risk level
        risk_level = "low"
        if trust_score < self.risk_thresholds["medium"]:
            risk_level = "high"
        elif trust_score < self.risk_thresholds["low"]:
            risk_level = "medium"
        
        # Calculate confidence based on feature consistency
        feature_std = np.std(list(features.values()))
        confidence = max(0.5, 1.0 - feature_std)
        
        # Feature contributions (for explainability)
        feature_contributions = {
            feature: features[feature] * weight 
            for feature, weight in self.feature_weights.items()
        }
        
        return TrustScoreResult(
            trust_score=trust_score,
            risk_level=risk_level,
            confidence=confidence,
            model_type="trust_signal_ml_stub_v1",
            feature_contributions=feature_contributions,
        )


def calculate_rail_adjustments(
    trust_score: float, 
    risk_level: str,
    original_weights: Dict[str, float]
) -> List[RailWeightAdjustment]:
    """
    Calculate rail weight adjustments based on trust score.
    
    Args:
        trust_score: Overall trust score (0-1)
        risk_level: Risk level (low, medium, high)
        original_weights: Original rail weights
        
    Returns:
        List of rail weight adjustments
    """
    adjustments = []
    
    # Define adjustment factors based on risk level
    adjustment_factors = {
        "low": {
            "ACH": 1.0,      # No change for low risk
            "debit": 1.0,
            "credit": 1.0,
        },
        "medium": {
            "ACH": 0.8,      # Slight reduction for ACH
            "debit": 1.0,
            "credit": 1.0,
        },
        "high": {
            "ACH": 0.3,      # Significant reduction for ACH
            "debit": 0.7,    # Moderate reduction for debit
            "credit": 1.0,   # No change for credit (most secure)
        },
    }
    
    factors = adjustment_factors.get(risk_level, adjustment_factors["low"])
    
    for rail_type, original_weight in original_weights.items():
        if rail_type in factors:
            adjustment_factor = factors[rail_type]
            adjusted_weight = original_weight * adjustment_factor
            
            # Normalize to ensure weights sum to 1.0
            total_adjusted = sum(
                original_weights[rt] * adjustment_factors[risk_level].get(rt, 1.0)
                for rt in original_weights.keys()
            )
            if total_adjusted > 0:
                adjusted_weight = adjusted_weight / total_adjusted
            
            adjustments.append(RailWeightAdjustment(
                rail_type=rail_type,
                original_weight=original_weight,
                adjusted_weight=adjusted_weight,
                adjustment_factor=adjustment_factor,
                reason=f"Trust score {trust_score:.2f} ({risk_level} risk) affects {rail_type} preference"
            ))
    
    return adjustments


def generate_trust_explanation(
    trust_score_result: TrustScoreResult,
    rail_adjustments: List[RailWeightAdjustment],
    context: TrustContext
) -> str:
    """
    Generate human-readable explanation for trust signal.
    
    Args:
        trust_score_result: Trust score calculation result
        rail_adjustments: Rail weight adjustments
        context: Original trust context
        
    Returns:
        Human-readable explanation
    """
    risk_level = trust_score_result.risk_level
    trust_score = trust_score_result.trust_score
    
    # Identify key risk factors
    key_factors = []
    if context.device_reputation < 0.5:
        key_factors.append("device reputation")
    if context.velocity > 5.0:
        key_factors.append("high velocity")
    if context.ip_risk > 0.7:
        key_factors.append("IP risk")
    if context.history_len < 10:
        key_factors.append("limited history")
    
    # Generate explanation
    if risk_level == "high":
        explanation = f"High risk detected (score: {trust_score:.2f})"
        if key_factors:
            explanation += f" due to {', '.join(key_factors)}"
        
        # Add rail-specific adjustments
        ach_adjustment = next((adj for adj in rail_adjustments if adj.rail_type == "ACH"), None)
        if ach_adjustment and ach_adjustment.adjustment_factor < 0.5:
            explanation += ". ACH down-weighted due to elevated risk"
        
    elif risk_level == "medium":
        explanation = f"Medium risk detected (score: {trust_score:.2f})"
        if key_factors:
            explanation += f" due to {', '.join(key_factors)}"
        explanation += ". Minor rail adjustments applied"
        
    else:  # low risk
        explanation = f"Low risk detected (score: {trust_score:.2f})"
        if context.history_len > 50:
            explanation += " with strong transaction history"
        explanation += ". No significant rail adjustments needed"
    
    return explanation


def get_trust_signal(
    trace_id: str,
    context: TrustContext,
    original_weights: Optional[Dict[str, float]] = None,
    deterministic_seed: int = 42
) -> TrustSignalResponse:
    """
    Generate trust signal with ML scoring and rail adjustments.
    
    Args:
        trace_id: Trace identifier
        context: Trust context with features
        original_weights: Original rail weights (defaults to equal weights)
        deterministic_seed: Seed for deterministic results
        
    Returns:
        Complete trust signal response
    """
    # Set deterministic seed
    random.seed(deterministic_seed)
    np.random.seed(deterministic_seed)
    
    # Default rail weights if not provided
    if original_weights is None:
        original_weights = {"ACH": 0.4, "debit": 0.3, "credit": 0.3}
    
    # Initialize ML model
    ml_model = TrustSignalMLModel(deterministic_seed)
    
    # Calculate trust score
    trust_score_result = ml_model.score_trust(context)
    
    # Calculate rail adjustments
    rail_adjustments = calculate_rail_adjustments(
        trust_score_result.trust_score,
        trust_score_result.risk_level,
        original_weights
    )
    
    # Generate explanation
    explanation = generate_trust_explanation(
        trust_score_result,
        rail_adjustments,
        context
    )
    
    # Create response
    response = TrustSignalResponse(
        trace_id=trace_id,
        trust_score_result=trust_score_result,
        rail_adjustments=rail_adjustments,
        explanation=explanation,
        metadata={
            "deterministic_seed": deterministic_seed,
            "model_version": "trust_signal_v1",
            "context_features": context.model_dump(),
            "original_weights": original_weights,
        }
    )
    
    logger.info(
        f"Trust signal generated for trace {trace_id}: "
        f"score={trust_score_result.trust_score:.3f}, "
        f"risk={trust_score_result.risk_level}, "
        f"confidence={trust_score_result.confidence:.3f}"
    )
    
    return response
