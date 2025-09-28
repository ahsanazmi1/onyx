"""
CloudEvent emission for trust signals in Onyx Phase 3.

Emits ocn.onyx.trust_signal.v1 events for trust signal generation and rail adjustments.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from onyx.trust_signals import TrustSignalResponse, TrustContext

logger = logging.getLogger(__name__)


class TrustSignalData(BaseModel):
    """Data payload for trust signal CloudEvent."""
    
    # Core trust signal data
    trace_id: str = Field(..., description="Trace identifier")
    trust_score: float = Field(..., ge=0.0, le=1.0, description="Trust score (0-1)")
    risk_level: str = Field(..., description="Risk level: low, medium, high")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Model confidence")
    
    # Context information
    merchant_context: Dict[str, Any] = Field(default_factory=dict, description="Merchant context")
    cart_summary: Dict[str, Any] = Field(default_factory=dict, description="Cart summary")
    
    # Rail candidates and scores
    rail_candidates: List[Dict[str, Any]] = Field(default_factory=list, description="Available rail candidates")
    scores: Dict[str, float] = Field(default_factory=dict, description="Trust-influenced scores")
    
    # Trust features
    device_reputation: float = Field(..., ge=0.0, le=1.0, description="Device reputation score")
    velocity: float = Field(..., ge=0.0, description="Transaction velocity")
    ip_risk: float = Field(..., ge=0.0, le=1.0, description="IP risk score")
    history_len: int = Field(..., ge=0, description="Transaction history length")
    
    # Rail adjustments
    rail_adjustments: List[Dict[str, Any]] = Field(default_factory=list, description="Rail weight adjustments")
    original_weights: Dict[str, float] = Field(default_factory=dict, description="Original rail weights")
    adjusted_weights: Dict[str, float] = Field(default_factory=dict, description="Adjusted rail weights")
    
    # Explanation and metadata
    explanation: str = Field(..., description="Human-readable explanation")
    feature_contributions: Dict[str, float] = Field(default_factory=dict, description="Feature contributions")
    model_type: str = Field(..., description="Model type used")
    
    # Timestamps
    generated_at: datetime = Field(default_factory=datetime.now, description="Trust signal generation time")
    expires_at: Optional[datetime] = Field(None, description="Trust signal expiration time")


class TrustSignalEvent(BaseModel):
    """CloudEvent for trust signal generation."""
    
    # CloudEvent standard fields
    specversion: str = Field("1.0", description="CloudEvents specification version")
    type: str = Field("ocn.onyx.trust_signal.v1", description="Event type")
    source: str = Field("onyx-trust-registry", description="Event source")
    id: str = Field(..., description="Unique event identifier")
    time: datetime = Field(default_factory=datetime.now, description="Event timestamp")
    datacontenttype: str = Field("application/json", description="Content type")
    subject: str = Field(..., description="Event subject (trace_id)")
    
    # Trust signal data
    data: TrustSignalData = Field(..., description="Trust signal data payload")


def create_trust_signal_payload(
    trust_response: TrustSignalResponse,
    context: TrustContext,
    merchant_context: Optional[Dict[str, Any]] = None,
    cart_summary: Optional[Dict[str, Any]] = None,
    rail_candidates: Optional[List[Dict[str, Any]]] = None
) -> TrustSignalData:
    """
    Create trust signal data payload for CloudEvent.
    
    Args:
        trust_response: Trust signal response
        context: Original trust context
        merchant_context: Merchant context information
        cart_summary: Cart summary information
        rail_candidates: Available rail candidates
        
    Returns:
        Trust signal data payload
    """
    # Prepare rail candidates if not provided
    if rail_candidates is None:
        rail_candidates = [
            {"rail_type": "ACH", "base_cost": 0.25, "settlement_days": 1},
            {"rail_type": "debit", "base_cost": 0.75, "settlement_days": 0},
            {"rail_type": "credit", "base_cost": 1.5, "settlement_days": 0},
        ]
    
    # Calculate adjusted weights from rail adjustments
    adjusted_weights = {}
    for adjustment in trust_response.rail_adjustments:
        adjusted_weights[adjustment.rail_type] = adjustment.adjusted_weight
    
    # Create trust-influenced scores (example)
    scores = {
        "trust_score": trust_response.trust_score_result.trust_score,
        "risk_penalty": 1.0 - trust_response.trust_score_result.trust_score,
        "confidence": trust_response.trust_score_result.confidence,
    }
    
    return TrustSignalData(
        # Core trust signal data
        trace_id=trust_response.trace_id,
        trust_score=trust_response.trust_score_result.trust_score,
        risk_level=trust_response.trust_score_result.risk_level,
        confidence=trust_response.trust_score_result.confidence,
        
        # Context information
        merchant_context=merchant_context or {},
        cart_summary=cart_summary or {},
        
        # Rail candidates and scores
        rail_candidates=rail_candidates,
        scores=scores,
        
        # Trust features
        device_reputation=context.device_reputation,
        velocity=context.velocity,
        ip_risk=context.ip_risk,
        history_len=context.history_len,
        
        # Rail adjustments
        rail_adjustments=[adj.model_dump() for adj in trust_response.rail_adjustments],
        original_weights=trust_response.metadata.get("original_weights", {}),
        adjusted_weights=adjusted_weights,
        
        # Explanation and metadata
        explanation=trust_response.explanation,
        feature_contributions=trust_response.trust_score_result.feature_contributions,
        model_type=trust_response.trust_score_result.model_type,
    )


def emit_trust_signal_event(
    trust_response: TrustSignalResponse,
    context: TrustContext,
    merchant_context: Optional[Dict[str, Any]] = None,
    cart_summary: Optional[Dict[str, Any]] = None,
    rail_candidates: Optional[List[Dict[str, Any]]] = None
) -> TrustSignalEvent:
    """
    Emit trust signal CloudEvent.
    
    Args:
        trust_response: Trust signal response
        context: Original trust context
        merchant_context: Merchant context information
        cart_summary: Cart summary information
        rail_candidates: Available rail candidates
        
    Returns:
        Trust signal CloudEvent
    """
    # Create data payload
    data = create_trust_signal_payload(
        trust_response=trust_response,
        context=context,
        merchant_context=merchant_context,
        cart_summary=cart_summary,
        rail_candidates=rail_candidates
    )
    
    # Generate unique event ID
    event_id = f"trust-signal-{trust_response.trace_id}-{int(datetime.now().timestamp())}"
    
    # Create CloudEvent
    event = TrustSignalEvent(
        id=event_id,
        subject=trust_response.trace_id,
        data=data,
    )
    
    # Log the event (in a real implementation, this would be sent to an event broker)
    logger.info(
        f"Trust signal event emitted: {event_id} for trace {trust_response.trace_id}",
        extra={
            "event_id": event_id,
            "trace_id": trust_response.trace_id,
            "trust_score": trust_response.trust_score_result.trust_score,
            "risk_level": trust_response.trust_score_result.risk_level,
            "rail_adjustments": len(trust_response.rail_adjustments),
        }
    )
    
    # In a real implementation, you would send this to an event broker like:
    # - Azure Event Grid
    # - AWS EventBridge
    # - Google Cloud Pub/Sub
    # - Apache Kafka
    
    return event


def validate_trust_signal_event(event: TrustSignalEvent) -> bool:
    """
    Validate trust signal CloudEvent structure.
    
    Args:
        event: Trust signal CloudEvent to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        # Validate CloudEvent structure
        if not event.specversion or event.specversion != "1.0":
            logger.error("Invalid CloudEvent specversion")
            return False
        
        if not event.type or event.type != "ocn.onyx.trust_signal.v1":
            logger.error("Invalid CloudEvent type")
            return False
        
        if not event.id or not event.subject:
            logger.error("Missing required CloudEvent fields")
            return False
        
        # Validate data payload
        data = event.data
        if not (0.0 <= data.trust_score <= 1.0):
            logger.error("Invalid trust score range")
            return False
        
        if data.risk_level not in ["low", "medium", "high"]:
            logger.error("Invalid risk level")
            return False
        
        if not (0.0 <= data.confidence <= 1.0):
            logger.error("Invalid confidence range")
            return False
        
        # Validate trust features
        if not (0.0 <= data.device_reputation <= 1.0):
            logger.error("Invalid device reputation range")
            return False
        
        if data.velocity < 0.0:
            logger.error("Invalid velocity value")
            return False
        
        if not (0.0 <= data.ip_risk <= 1.0):
            logger.error("Invalid IP risk range")
            return False
        
        if data.history_len < 0:
            logger.error("Invalid history length")
            return False
        
        logger.debug(f"Trust signal event validation passed: {event.id}")
        return True
        
    except Exception as e:
        logger.error(f"Trust signal event validation failed: {e}")
        return False


def get_trust_signal_event_schema() -> Dict[str, Any]:
    """
    Get JSON schema for trust signal CloudEvent.
    
    Returns:
        JSON schema for trust signal events
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "specversion": {
                "type": "string",
                "const": "1.0"
            },
            "type": {
                "type": "string",
                "const": "ocn.onyx.trust_signal.v1"
            },
            "source": {
                "type": "string",
                "pattern": "^onyx-trust-registry$"
            },
            "id": {
                "type": "string",
                "pattern": "^trust-signal-.*$"
            },
            "time": {
                "type": "string",
                "format": "date-time"
            },
            "datacontenttype": {
                "type": "string",
                "const": "application/json"
            },
            "subject": {
                "type": "string"
            },
            "data": {
                "type": "object",
                "properties": {
                    "trace_id": {"type": "string"},
                    "trust_score": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
                    "confidence": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "device_reputation": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "velocity": {"type": "number", "minimum": 0.0},
                    "ip_risk": {"type": "number", "minimum": 0.0, "maximum": 1.0},
                    "history_len": {"type": "integer", "minimum": 0},
                    "explanation": {"type": "string"},
                    "model_type": {"type": "string"},
                    "rail_adjustments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "rail_type": {"type": "string"},
                                "original_weight": {"type": "number"},
                                "adjusted_weight": {"type": "number"},
                                "adjustment_factor": {"type": "number"},
                                "reason": {"type": "string"}
                            }
                        }
                    }
                },
                "required": [
                    "trace_id", "trust_score", "risk_level", "confidence",
                    "device_reputation", "velocity", "ip_risk", "history_len",
                    "explanation", "model_type"
                ]
            }
        },
        "required": [
            "specversion", "type", "source", "id", "time", 
            "datacontenttype", "subject", "data"
        ]
    }
