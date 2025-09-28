"""
Tests for Onyx trust signal functionality.

Tests trust signal generation, ML scoring, rail adjustments, and CloudEvent emission.
"""

import json
import pytest
from datetime import datetime
from typing import Dict, Any

from onyx.trust_signals import (
    TrustContext, TrustScoreResult, RailWeightAdjustment, TrustSignalResponse,
    TrustSignalMLModel, calculate_rail_adjustments, generate_trust_explanation,
    get_trust_signal
)
from onyx.trust_events import (
    TrustSignalData, TrustSignalEvent, create_trust_signal_payload,
    emit_trust_signal_event, validate_trust_signal_event, get_trust_signal_event_schema
)
from onyx.llm.explain import (
    TrustLLMExplainer, LLMExplanationRequest, LLMExplanationResponse,
    is_trust_llm_configured, explain_trust_signal_llm
)


class TestTrustSignalMLModel:
    """Test trust signal ML model functionality."""
    
    def test_ml_model_initialization(self):
        """Test ML model initialization with deterministic seed."""
        model = TrustSignalMLModel(deterministic_seed=42)
        
        assert model.deterministic_seed == 42
        assert "device_reputation" in model.feature_weights
        assert "velocity" in model.feature_weights
        assert "ip_risk" in model.feature_weights
        assert "history_len" in model.feature_weights
        assert sum(model.feature_weights.values()) == pytest.approx(1.0, abs=0.01)
    
    def test_trust_score_calculation_low_risk(self):
        """Test trust score calculation for low risk scenario."""
        model = TrustSignalMLModel(deterministic_seed=42)
        
        context = TrustContext(
            device_reputation=0.9,
            velocity=1.0,
            ip_risk=0.1,
            history_len=100
        )
        
        result = model.score_trust(context)
        
        assert isinstance(result, TrustScoreResult)
        assert 0.0 <= result.trust_score <= 1.0
        assert result.risk_level == "low"
        assert 0.0 <= result.confidence <= 1.0
        assert result.model_type == "trust_signal_ml_stub_v1"
        assert len(result.feature_contributions) == 4
    
    def test_trust_score_calculation_high_risk(self):
        """Test trust score calculation for high risk scenario."""
        model = TrustSignalMLModel(deterministic_seed=42)
        
        context = TrustContext(
            device_reputation=0.2,
            velocity=15.0,
            ip_risk=0.8,
            history_len=2
        )
        
        result = model.score_trust(context)
        
        assert isinstance(result, TrustScoreResult)
        assert 0.0 <= result.trust_score <= 1.0
        assert result.risk_level == "high"
        assert 0.0 <= result.confidence <= 1.0
    
    def test_deterministic_scoring(self):
        """Test that scoring is deterministic with same seed."""
        model1 = TrustSignalMLModel(deterministic_seed=42)
        model2 = TrustSignalMLModel(deterministic_seed=42)
        
        context = TrustContext(
            device_reputation=0.5,
            velocity=5.0,
            ip_risk=0.5,
            history_len=20
        )
        
        result1 = model1.score_trust(context)
        result2 = model2.score_trust(context)
        
        assert result1.trust_score == pytest.approx(result2.trust_score, abs=0.001)
        assert result1.risk_level == result2.risk_level
        assert result1.confidence == pytest.approx(result2.confidence, abs=0.001)


class TestRailAdjustments:
    """Test rail weight adjustment functionality."""
    
    def test_rail_adjustments_low_risk(self):
        """Test rail adjustments for low risk scenario."""
        original_weights = {"ACH": 0.4, "debit": 0.3, "credit": 0.3}
        
        adjustments = calculate_rail_adjustments(0.8, "low", original_weights)
        
        assert len(adjustments) == 3
        for adj in adjustments:
            assert isinstance(adj, RailWeightAdjustment)
            assert adj.rail_type in ["ACH", "debit", "credit"]
            assert adj.adjustment_factor == 1.0  # No change for low risk
            assert adj.original_weight == original_weights[adj.rail_type]
            assert adj.adjusted_weight == adj.original_weight
    
    def test_rail_adjustments_high_risk(self):
        """Test rail adjustments for high risk scenario."""
        original_weights = {"ACH": 0.4, "debit": 0.3, "credit": 0.3}
        
        adjustments = calculate_rail_adjustments(0.2, "high", original_weights)
        
        assert len(adjustments) == 3
        
        # Find ACH adjustment
        ach_adj = next(adj for adj in adjustments if adj.rail_type == "ACH")
        assert ach_adj.adjustment_factor == 0.3  # Significant reduction
        assert ach_adj.adjusted_weight < ach_adj.original_weight
        
        # Find credit adjustment
        credit_adj = next(adj for adj in adjustments if adj.rail_type == "credit")
        assert credit_adj.adjustment_factor == 1.0  # No change for credit
    
    def test_rail_adjustments_medium_risk(self):
        """Test rail adjustments for medium risk scenario."""
        original_weights = {"ACH": 0.4, "debit": 0.3, "credit": 0.3}
        
        adjustments = calculate_rail_adjustments(0.5, "medium", original_weights)
        
        assert len(adjustments) == 3
        
        # Find ACH adjustment
        ach_adj = next(adj for adj in adjustments if adj.rail_type == "ACH")
        assert ach_adj.adjustment_factor == 0.8  # Slight reduction
        assert ach_adj.adjusted_weight < ach_adj.original_weight


class TestTrustExplanations:
    """Test trust signal explanation generation."""
    
    def test_trust_explanation_high_risk(self):
        """Test explanation generation for high risk scenario."""
        # Create mock trust score result
        trust_score_result = TrustScoreResult(
            trust_score=0.2,
            risk_level="high",
            confidence=0.8,
            model_type="test_model",
            feature_contributions={
                "device_reputation": 0.1,
                "velocity": 0.2,
                "ip_risk": 0.3,
                "history_len": 0.1,
            }
        )
        
        # Create mock rail adjustments
        rail_adjustments = [
            RailWeightAdjustment(
                rail_type="ACH",
                original_weight=0.4,
                adjusted_weight=0.12,
                adjustment_factor=0.3,
                reason="High risk affects ACH preference"
            )
        ]
        
        # Create context
        context = TrustContext(
            device_reputation=0.2,
            velocity=10.0,
            ip_risk=0.8,
            history_len=2
        )
        
        explanation = generate_trust_explanation(
            trust_score_result, rail_adjustments, context
        )
        
        assert isinstance(explanation, str)
        assert "High risk detected" in explanation
        assert "0.20" in explanation  # Trust score
        assert "device reputation" in explanation or "high velocity" in explanation or "IP risk" in explanation
        assert "ACH down-weighted" in explanation
    
    def test_trust_explanation_low_risk(self):
        """Test explanation generation for low risk scenario."""
        trust_score_result = TrustScoreResult(
            trust_score=0.9,
            risk_level="low",
            confidence=0.9,
            model_type="test_model",
            feature_contributions={
                "device_reputation": 0.3,
                "velocity": 0.2,
                "ip_risk": 0.2,
                "history_len": 0.2,
            }
        )
        
        rail_adjustments = [
            RailWeightAdjustment(
                rail_type="ACH",
                original_weight=0.4,
                adjusted_weight=0.4,
                adjustment_factor=1.0,
                reason="Low risk maintains ACH preference"
            )
        ]
        
        context = TrustContext(
            device_reputation=0.9,
            velocity=1.0,
            ip_risk=0.1,
            history_len=100
        )
        
        explanation = generate_trust_explanation(
            trust_score_result, rail_adjustments, context
        )
        
        assert isinstance(explanation, str)
        assert "Low risk detected" in explanation
        assert "0.90" in explanation  # Trust score
        assert "strong transaction history" in explanation


class TestTrustSignalGeneration:
    """Test complete trust signal generation."""
    
    def test_get_trust_signal_low_risk(self):
        """Test trust signal generation for low risk scenario."""
        context = TrustContext(
            device_reputation=0.9,
            velocity=1.0,
            ip_risk=0.1,
            history_len=100
        )
        
        response = get_trust_signal(
            trace_id="test-trace-001",
            context=context,
            original_weights={"ACH": 0.4, "debit": 0.3, "credit": 0.3},
            deterministic_seed=42
        )
        
        assert isinstance(response, TrustSignalResponse)
        assert response.trace_id == "test-trace-001"
        assert 0.0 <= response.trust_score_result.trust_score <= 1.0
        assert response.trust_score_result.risk_level in ["low", "medium", "high"]
        assert len(response.rail_adjustments) == 3
        assert isinstance(response.explanation, str)
        assert "deterministic_seed" in response.metadata
    
    def test_get_trust_signal_high_risk(self):
        """Test trust signal generation for high risk scenario."""
        context = TrustContext(
            device_reputation=0.2,
            velocity=15.0,
            ip_risk=0.8,
            history_len=2
        )
        
        response = get_trust_signal(
            trace_id="test-trace-002",
            context=context,
            original_weights={"ACH": 0.4, "debit": 0.3, "credit": 0.3},
            deterministic_seed=42
        )
        
        assert isinstance(response, TrustSignalResponse)
        assert response.trace_id == "test-trace-002"
        assert response.trust_score_result.risk_level == "high"
        
        # Check that ACH is down-weighted
        ach_adj = next(adj for adj in response.rail_adjustments if adj.rail_type == "ACH")
        assert ach_adj.adjustment_factor < 0.5  # Significant reduction
    
    def test_deterministic_trust_signals(self):
        """Test that trust signals are deterministic with same seed."""
        context = TrustContext(
            device_reputation=0.5,
            velocity=5.0,
            ip_risk=0.5,
            history_len=20
        )
        
        response1 = get_trust_signal(
            trace_id="test-trace-003",
            context=context,
            deterministic_seed=42
        )
        
        response2 = get_trust_signal(
            trace_id="test-trace-003",
            context=context,
            deterministic_seed=42
        )
        
        assert response1.trust_score_result.trust_score == pytest.approx(
            response2.trust_score_result.trust_score, abs=0.001
        )
        assert response1.trust_score_result.risk_level == response2.trust_score_result.risk_level


class TestTrustSignalCloudEvents:
    """Test CloudEvent emission for trust signals."""
    
    def test_trust_signal_data_creation(self):
        """Test trust signal data payload creation."""
        # Create mock trust response
        trust_score_result = TrustScoreResult(
            trust_score=0.7,
            risk_level="medium",
            confidence=0.8,
            model_type="test_model",
            feature_contributions={
                "device_reputation": 0.2,
                "velocity": 0.2,
                "ip_risk": 0.2,
                "history_len": 0.1,
            }
        )
        
        rail_adjustments = [
            RailWeightAdjustment(
                rail_type="ACH",
                original_weight=0.4,
                adjusted_weight=0.32,
                adjustment_factor=0.8,
                reason="Medium risk affects ACH preference"
            )
        ]
        
        trust_response = TrustSignalResponse(
            trace_id="test-trace-004",
            trust_score_result=trust_score_result,
            rail_adjustments=rail_adjustments,
            explanation="Medium risk detected with minor adjustments",
            metadata={"test": "data"}
        )
        
        context = TrustContext(
            device_reputation=0.7,
            velocity=3.0,
            ip_risk=0.4,
            history_len=25
        )
        
        data = create_trust_signal_payload(
            trust_response=trust_response,
            context=context,
            merchant_context={"merchant_id": "test_merchant"},
            cart_summary={"total": 100.0, "items": 2}
        )
        
        assert isinstance(data, TrustSignalData)
        assert data.trace_id == "test-trace-004"
        assert data.trust_score == 0.7
        assert data.risk_level == "medium"
        assert data.device_reputation == 0.7
        assert data.velocity == 3.0
        assert data.ip_risk == 0.4
        assert data.history_len == 25
        assert len(data.rail_adjustments) == 1
        assert data.merchant_context["merchant_id"] == "test_merchant"
        assert data.cart_summary["total"] == 100.0
    
    def test_trust_signal_event_emission(self):
        """Test trust signal CloudEvent emission."""
        trust_score_result = TrustScoreResult(
            trust_score=0.6,
            risk_level="medium",
            confidence=0.75,
            model_type="test_model",
            feature_contributions={
                "device_reputation": 0.2,
                "velocity": 0.2,
                "ip_risk": 0.2,
                "history_len": 0.1,
            }
        )
        
        rail_adjustments = [
            RailWeightAdjustment(
                rail_type="ACH",
                original_weight=0.4,
                adjusted_weight=0.32,
                adjustment_factor=0.8,
                reason="Medium risk affects ACH preference"
            )
        ]
        
        trust_response = TrustSignalResponse(
            trace_id="test-trace-005",
            trust_score_result=trust_score_result,
            rail_adjustments=rail_adjustments,
            explanation="Medium risk detected with minor adjustments",
            metadata={"test": "data"}
        )
        
        context = TrustContext(
            device_reputation=0.6,
            velocity=4.0,
            ip_risk=0.5,
            history_len=15
        )
        
        event = emit_trust_signal_event(
            trust_response=trust_response,
            context=context
        )
        
        assert isinstance(event, TrustSignalEvent)
        assert event.specversion == "1.0"
        assert event.type == "ocn.onyx.trust_signal.v1"
        assert event.source == "onyx-trust-registry"
        assert event.subject == "test-trace-005"
        assert event.data.trace_id == "test-trace-005"
        assert event.data.trust_score == 0.6
        assert event.data.risk_level == "medium"
    
    def test_trust_signal_event_validation(self):
        """Test trust signal CloudEvent validation."""
        # Create valid event
        trust_score_result = TrustScoreResult(
            trust_score=0.5,
            risk_level="medium",
            confidence=0.7,
            model_type="test_model",
            feature_contributions={
                "device_reputation": 0.2,
                "velocity": 0.2,
                "ip_risk": 0.2,
                "history_len": 0.1,
            }
        )
        
        trust_response = TrustSignalResponse(
            trace_id="test-trace-006",
            trust_score_result=trust_score_result,
            rail_adjustments=[],
            explanation="Test explanation",
            metadata={}
        )
        
        context = TrustContext(
            device_reputation=0.5,
            velocity=2.0,
            ip_risk=0.3,
            history_len=10
        )
        
        event = emit_trust_signal_event(
            trust_response=trust_response,
            context=context
        )
        
        # Validate event
        assert validate_trust_signal_event(event) is True
        
        # Test invalid event
        event.specversion = "2.0"  # Invalid version
        assert validate_trust_signal_event(event) is False
    
    def test_trust_signal_event_schema(self):
        """Test trust signal event JSON schema."""
        schema = get_trust_signal_event_schema()
        
        assert isinstance(schema, dict)
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
        assert schema["type"] == "object"
        assert "properties" in schema
        assert "specversion" in schema["properties"]
        assert "type" in schema["properties"]
        assert "data" in schema["properties"]


class TestTrustLLMExplainer:
    """Test LLM explanation functionality."""
    
    def test_llm_explainer_initialization(self):
        """Test LLM explainer initialization."""
        explainer = TrustLLMExplainer()
        
        config = explainer.get_configuration_status()
        assert isinstance(config, dict)
        assert "configured" in config
        assert "endpoint" in config
        assert "api_key" in config
        assert "deployment" in config
    
    def test_llm_explanation_request_creation(self):
        """Test LLM explanation request creation."""
        trust_score_result = TrustScoreResult(
            trust_score=0.3,
            risk_level="high",
            confidence=0.8,
            model_type="test_model",
            feature_contributions={
                "device_reputation": 0.1,
                "velocity": 0.2,
                "ip_risk": 0.3,
                "history_len": 0.1,
            }
        )
        
        trust_response = TrustSignalResponse(
            trace_id="test-trace-007",
            trust_score_result=trust_score_result,
            rail_adjustments=[],
            explanation="Test explanation",
            metadata={}
        )
        
        context = TrustContext(
            device_reputation=0.3,
            velocity=8.0,
            ip_risk=0.7,
            history_len=5
        )
        
        request = LLMExplanationRequest(
            trust_response=trust_response,
            context=context,
            merchant_context={"merchant_id": "test_merchant"},
            cart_summary={"total": 50.0}
        )
        
        assert isinstance(request, LLMExplanationRequest)
        assert request.trust_response.trace_id == "test-trace-007"
        assert request.context.device_reputation == 0.3
        assert request.merchant_context["merchant_id"] == "test_merchant"
    
    def test_llm_explanation_generation(self):
        """Test LLM explanation generation (stub implementation)."""
        explainer = TrustLLMExplainer()
        
        trust_score_result = TrustScoreResult(
            trust_score=0.4,
            risk_level="medium",
            confidence=0.75,
            model_type="test_model",
            feature_contributions={
                "device_reputation": 0.2,
                "velocity": 0.2,
                "ip_risk": 0.2,
                "history_len": 0.1,
            }
        )
        
        rail_adjustments = [
            RailWeightAdjustment(
                rail_type="ACH",
                original_weight=0.4,
                adjusted_weight=0.32,
                adjustment_factor=0.8,
                reason="Medium risk affects ACH preference"
            )
        ]
        
        trust_response = TrustSignalResponse(
            trace_id="test-trace-008",
            trust_score_result=trust_score_result,
            rail_adjustments=rail_adjustments,
            explanation="Test explanation",
            metadata={}
        )
        
        context = TrustContext(
            device_reputation=0.4,
            velocity=6.0,
            ip_risk=0.6,
            history_len=8
        )
        
        request = LLMExplanationRequest(
            trust_response=trust_response,
            context=context
        )
        
        # Test stub explanation generation
        response = explainer.explain_trust_decision(request)
        
        if response:  # Only if LLM is configured
            assert isinstance(response, LLMExplanationResponse)
            assert isinstance(response.explanation, str)
            assert isinstance(response.key_factors, list)
            assert isinstance(response.rail_impact, dict)
            assert 0.0 <= response.confidence <= 1.0
            assert isinstance(response.model_used, str)
    
    def test_trust_llm_configuration_check(self):
        """Test trust LLM configuration check."""
        configured = is_trust_llm_configured()
        assert isinstance(configured, bool)


class TestTrustSignalIntegration:
    """Test integration scenarios for trust signals."""
    
    def test_high_risk_flips_winner(self):
        """Test that high risk flips the rail winner."""
        # Start with ACH as preferred rail
        original_weights = {"ACH": 0.5, "debit": 0.3, "credit": 0.2}
        
        # High risk context
        context = TrustContext(
            device_reputation=0.1,
            velocity=20.0,
            ip_risk=0.9,
            history_len=1
        )
        
        response = get_trust_signal(
            trace_id="test-trace-009",
            context=context,
            original_weights=original_weights,
            deterministic_seed=42
        )
        
        # ACH should be significantly down-weighted
        ach_adj = next(adj for adj in response.rail_adjustments if adj.rail_type == "ACH")
        credit_adj = next(adj for adj in response.rail_adjustments if adj.rail_type == "credit")
        
        assert ach_adj.adjusted_weight < ach_adj.original_weight
        assert credit_adj.adjusted_weight >= credit_adj.original_weight  # Credit should be preferred
    
    def test_low_risk_leaves_winner_unchanged(self):
        """Test that low risk leaves the rail winner unchanged."""
        # Start with ACH as preferred rail
        original_weights = {"ACH": 0.5, "debit": 0.3, "credit": 0.2}
        
        # Low risk context
        context = TrustContext(
            device_reputation=0.9,
            velocity=0.5,
            ip_risk=0.1,
            history_len=200
        )
        
        response = get_trust_signal(
            trace_id="test-trace-010",
            context=context,
            original_weights=original_weights,
            deterministic_seed=42
        )
        
        # ACH should remain preferred
        ach_adj = next(adj for adj in response.rail_adjustments if adj.rail_type == "ACH")
        
        assert ach_adj.adjustment_factor == 1.0  # No change
        assert ach_adj.adjusted_weight == ach_adj.original_weight
    
    def test_explanation_json_snapshot(self):
        """Test that explanation includes structured JSON data."""
        context = TrustContext(
            device_reputation=0.6,
            velocity=4.0,
            ip_risk=0.5,
            history_len=15
        )
        
        response = get_trust_signal(
            trace_id="test-trace-011",
            context=context,
            deterministic_seed=42
        )
        
        # Check that explanation contains key elements
        explanation = response.explanation
        assert isinstance(explanation, str)
        assert len(explanation) > 0
        
        # Check that trust score is mentioned
        trust_score_str = f"{response.trust_score_result.trust_score:.2f}"
        assert trust_score_str in explanation
        
        # Check that risk level is mentioned (case-insensitive)
        assert response.trust_score_result.risk_level.lower() in explanation.lower()
        
        # Check that rail adjustments are mentioned
        for adj in response.rail_adjustments:
            if adj.adjustment_factor < 0.8:  # Significant adjustment
                assert adj.rail_type.lower() in explanation.lower()
    
    def test_deterministic_consistency(self):
        """Test that trust signals are consistent across multiple calls."""
        context = TrustContext(
            device_reputation=0.5,
            velocity=3.0,
            ip_risk=0.4,
            history_len=20
        )
        
        # Generate multiple responses with same seed
        responses = []
        for i in range(3):
            response = get_trust_signal(
                trace_id=f"test-trace-012-{i}",
                context=context,
                deterministic_seed=42
            )
            responses.append(response)
        
        # All should have same trust score and risk level
        for response in responses[1:]:
            assert response.trust_score_result.trust_score == pytest.approx(
                responses[0].trust_score_result.trust_score, abs=0.001
            )
            assert response.trust_score_result.risk_level == responses[0].trust_score_result.risk_level
            
            # Rail adjustments should be identical
            for i, adj in enumerate(response.rail_adjustments):
                original_adj = responses[0].rail_adjustments[i]
                assert adj.rail_type == original_adj.rail_type
                assert adj.adjustment_factor == original_adj.adjustment_factor
