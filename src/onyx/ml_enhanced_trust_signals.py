"""
ML-enhanced trust signals for Onyx.

Integrates advanced ML models with the existing trust signal system for improved
trust scoring and risk assessment.
"""

import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import ML models
from .ml.trust_scoring import get_trust_scorer, calculate_trust_score
from .ml.risk_assessment import get_risk_assessor, assess_transaction_risk

# Import existing trust signals
from .trust_signals import (
    TrustContext, TrustScoreResult, RailWeightAdjustment, 
    TrustSignalResponse, calculate_rail_adjustments, generate_trust_explanation
)

logger = logging.getLogger(__name__)


class MLEnhancedTrustSignals:
    """ML-enhanced trust signal generation with advanced scoring and risk assessment."""

    def __init__(self, ml_weight: float = 0.8, use_ml: bool = True):
        """
        Initialize ML-enhanced trust signals.
        
        Args:
            ml_weight: Weight of ML predictions vs traditional scoring (0-1)
            use_ml: Whether to use ML models for scoring
        """
        self.ml_weight = ml_weight
        self.use_ml = use_ml
        self.trust_scorer = get_trust_scorer()
        self.risk_assessor = get_risk_assessor()

    def generate_enhanced_trust_signal(
        self,
        trace_id: str,
        context: TrustContext,
        original_weights: Optional[Dict[str, float]] = None,
        deterministic_seed: int = 42,
        transaction_amount: Optional[float] = None,
        merchant_id: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> TrustSignalResponse:
        """
        Generate enhanced trust signal using ML models.
        
        Args:
            trace_id: Trace identifier
            context: Trust context with features
            original_weights: Original rail weights
            deterministic_seed: Seed for deterministic results
            transaction_amount: Transaction amount for risk assessment
            merchant_id: Merchant identifier
            user_id: User identifier
            
        Returns:
            Enhanced trust signal response
        """
        if not self.use_ml:
            # Fallback to traditional scoring
            from .trust_signals import get_trust_signal
            return get_trust_signal(trace_id, context, original_weights, deterministic_seed)
        
        # Default rail weights if not provided
        if original_weights is None:
            original_weights = {"ACH": 0.4, "debit": 0.3, "credit": 0.3}
        
        # Enhanced trust scoring with ML
        ml_trust_result = self._calculate_ml_trust_score(context, transaction_amount, merchant_id, user_id)
        
        # Risk assessment for additional context
        risk_result = self._assess_transaction_risk(context, transaction_amount, merchant_id, user_id)
        
        # Combine ML and traditional scoring
        final_trust_score = self._combine_scores(ml_trust_result, risk_result)
        
        # Calculate rail adjustments based on enhanced scoring
        rail_adjustments = self._calculate_enhanced_rail_adjustments(
            final_trust_score, original_weights, risk_result
        )
        
        # Generate enhanced explanation
        explanation = self._generate_enhanced_explanation(
            final_trust_score, ml_trust_result, risk_result, context
        )
        
        # Create enhanced response
        response = TrustSignalResponse(
            trace_id=trace_id,
            trust_score_result=TrustScoreResult(
                trust_score=final_trust_score.trust_score,
                risk_level=final_trust_score.risk_level,
                confidence=final_trust_score.confidence,
                model_type="ml_enhanced_trust_v1",
                feature_contributions=final_trust_score.feature_importance,
                timestamp=datetime.now()
            ),
            rail_adjustments=rail_adjustments,
            explanation=explanation,
            metadata={
                "ml_enhanced": True,
                "ml_weight": self.ml_weight,
                "trust_model_version": ml_trust_result.model_version,
                "risk_model_version": risk_result.model_version,
                "deterministic_seed": deterministic_seed,
                "context_features": context.model_dump(),
                "original_weights": original_weights,
                "risk_assessment": {
                    "risk_score": risk_result.risk_score,
                    "fraud_probability": risk_result.fraud_probability,
                    "recommended_actions": risk_result.recommended_actions
                }
            }
        )
        
        logger.info(
            f"ML-enhanced trust signal generated for trace {trace_id}: "
            f"score={final_trust_score.trust_score:.3f}, "
            f"risk={final_trust_score.risk_level}, "
            f"fraud_prob={risk_result.fraud_probability:.3f}"
        )
        
        return response

    def _calculate_ml_trust_score(
        self, 
        context: TrustContext, 
        transaction_amount: Optional[float] = None,
        merchant_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Calculate trust score using ML model."""
        # Extract features for ML model
        device_reputation = context.device_reputation
        velocity = context.velocity
        ip_risk = context.ip_risk
        history_len = context.history_len
        
        # Additional features (with defaults if not available)
        user_age_days = 365  # Default to 1 year
        session_duration_min = 30.0  # Default to 30 minutes
        device_consistency = 0.8  # Default device consistency
        location_consistency = 0.8  # Default location consistency
        payment_method_age_days = 180  # Default to 6 months
        transaction_amount_val = transaction_amount or context.amount or 100.0
        merchant_trust_score = 0.7  # Default merchant trust
        time_since_last_login_hours = 2.0  # Default to 2 hours
        failed_attempts_24h = 0  # Default to no failed attempts
        account_verification_level = 2  # Default to level 2 verification
        is_mobile_device = False  # Default to desktop
        is_vpn_connection = False  # Default to no VPN
        transaction_hour = datetime.now().hour
        transaction_day_of_week = datetime.now().weekday()
        
        return calculate_trust_score(
            device_reputation=device_reputation,
            velocity=velocity,
            ip_risk=ip_risk,
            history_len=history_len,
            user_age_days=user_age_days,
            session_duration_min=session_duration_min,
            device_consistency=device_consistency,
            location_consistency=location_consistency,
            payment_method_age_days=payment_method_age_days,
            transaction_amount=transaction_amount_val,
            merchant_trust_score=merchant_trust_score,
            time_since_last_login_hours=time_since_last_login_hours,
            failed_attempts_24h=failed_attempts_24h,
            account_verification_level=account_verification_level,
            is_mobile_device=is_mobile_device,
            is_vpn_connection=is_vpn_connection,
            transaction_hour=transaction_hour,
            transaction_day_of_week=transaction_day_of_week
        )

    def _assess_transaction_risk(
        self,
        context: TrustContext,
        transaction_amount: Optional[float] = None,
        merchant_id: Optional[str] = None,
        user_id: Optional[str] = None
    ):
        """Assess transaction risk using ML model."""
        # Extract features for risk assessment
        transaction_amount_val = transaction_amount or context.amount or 100.0
        merchant_risk_score = 0.5  # Default merchant risk
        user_trust_score = context.device_reputation  # Use device reputation as proxy
        device_risk_score = 1.0 - context.device_reputation  # Invert device reputation
        ip_risk_score = context.ip_risk
        velocity_24h = context.velocity
        velocity_7d = context.velocity * 7  # Estimate 7-day velocity
        avg_transaction_amount = transaction_amount_val
        time_since_last_transaction_hours = 24.0 / max(1, context.velocity)  # Estimate
        payment_method_age_days = 180  # Default to 6 months
        user_age_days = 365  # Default to 1 year
        is_high_value = transaction_amount_val > 1000.0
        is_international = False  # Default to domestic
        is_new_merchant = merchant_id is None  # Assume new if no merchant ID
        is_weekend = datetime.now().weekday() >= 5
        is_off_hours = datetime.now().hour < 6 or datetime.now().hour > 22
        failed_attempts_24h = 0  # Default to no failed attempts
        account_verification_level = 2  # Default to level 2 verification
        
        return assess_transaction_risk(
            transaction_amount=transaction_amount_val,
            merchant_risk_score=merchant_risk_score,
            user_trust_score=user_trust_score,
            device_risk_score=device_risk_score,
            ip_risk_score=ip_risk_score,
            velocity_24h=velocity_24h,
            velocity_7d=velocity_7d,
            avg_transaction_amount=avg_transaction_amount,
            time_since_last_transaction_hours=time_since_last_transaction_hours,
            payment_method_age_days=payment_method_age_days,
            user_age_days=user_age_days,
            is_high_value=is_high_value,
            is_international=is_international,
            is_new_merchant=is_new_merchant,
            is_weekend=is_weekend,
            is_off_hours=is_off_hours,
            failed_attempts_24h=failed_attempts_24h,
            account_verification_level=account_verification_level
        )

    def _combine_scores(self, trust_result, risk_result):
        """Combine trust scoring and risk assessment results."""
        # Weight the trust score based on risk assessment
        risk_adjustment = 1.0 - (risk_result.risk_score * 0.3)  # Reduce trust by up to 30% based on risk
        
        final_trust_score = trust_result.trust_score * risk_adjustment
        final_trust_score = max(0.0, min(1.0, final_trust_score))  # Clamp to [0, 1]
        
        # Determine final risk level
        if final_trust_score >= 0.7 and risk_result.risk_level in ["low", "medium"]:
            risk_level = "low"
        elif final_trust_score >= 0.4 and risk_result.risk_level in ["low", "medium", "high"]:
            risk_level = "medium"
        else:
            risk_level = "high"
        
        # Combine confidence scores
        combined_confidence = (trust_result.confidence + risk_result.confidence) / 2.0
        
        # Combine feature importance
        combined_features = {}
        for feature, importance in trust_result.feature_importance.items():
            combined_features[f"trust_{feature}"] = importance
        for feature, importance in risk_result.feature_importance.items():
            combined_features[f"risk_{feature}"] = importance
        
        return type('CombinedScore', (), {
            'trust_score': final_trust_score,
            'risk_level': risk_level,
            'confidence': combined_confidence,
            'feature_importance': combined_features,
            'model_version': f"combined_v1.0"
        })()

    def _calculate_enhanced_rail_adjustments(
        self, 
        final_score, 
        original_weights: Dict[str, float],
        risk_result
    ) -> List[RailWeightAdjustment]:
        """Calculate enhanced rail adjustments based on ML scoring and risk assessment."""
        adjustments = []
        
        # Base adjustments from trust score
        base_adjustments = calculate_rail_adjustments(
            final_score.trust_score, 
            final_score.risk_level, 
            original_weights
        )
        
        # Additional risk-based adjustments
        risk_multiplier = 1.0 - (risk_result.risk_score * 0.5)  # Reduce weights by up to 50% based on risk
        
        for base_adj in base_adjustments:
            # Apply risk-based adjustment
            enhanced_adjustment_factor = base_adj.adjustment_factor * risk_multiplier
            enhanced_weight = base_adj.original_weight * enhanced_adjustment_factor
            
            # Normalize weights
            total_weight = sum(
                original_weights[rail] * enhanced_adjustment_factor 
                for rail in original_weights.keys()
            )
            if total_weight > 0:
                enhanced_weight = enhanced_weight / total_weight
            
            adjustments.append(RailWeightAdjustment(
                rail_type=base_adj.rail_type,
                original_weight=base_adj.original_weight,
                adjusted_weight=enhanced_weight,
                adjustment_factor=enhanced_adjustment_factor,
                reason=f"ML-enhanced: {base_adj.reason} + risk adjustment (risk_score: {risk_result.risk_score:.2f})"
            ))
        
        return adjustments

    def _generate_enhanced_explanation(
        self, 
        final_score, 
        trust_result, 
        risk_result, 
        context: TrustContext
    ) -> str:
        """Generate enhanced explanation combining trust scoring and risk assessment."""
        base_explanation = f"ML-enhanced trust score: {final_score.trust_score:.2f} ({final_score.risk_level} risk)"
        
        # Add trust scoring details
        if trust_result.trust_score < 0.5:
            base_explanation += f". Trust factors: device_reputation={context.device_reputation:.2f}, velocity={context.velocity:.1f}"
        
        # Add risk assessment details
        if risk_result.risk_level in ["high", "critical"]:
            base_explanation += f". Risk factors: fraud_probability={risk_result.fraud_probability:.2f}"
            if risk_result.recommended_actions:
                base_explanation += f", recommended: {', '.join(risk_result.recommended_actions[:2])}"
        
        # Add rail adjustment explanation
        if final_score.risk_level == "high":
            base_explanation += ". Enhanced risk detection applied to rail weights"
        
        return base_explanation


# Global instance
ml_enhanced_trust_signals = MLEnhancedTrustSignals()
