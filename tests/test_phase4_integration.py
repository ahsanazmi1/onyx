"""
Integration tests for Onyx Phase 4 Trust Registry v1 functionality.

Tests trust registry CRUD operations, trust signal generation during negotiation,
and comprehensive API functionality with provider verification.
"""

import pytest
from datetime import datetime, timedelta
from typing import List

from onyx.models import (
    TrustRegistryProvider, AddProviderRequest, RevokeProviderRequest,
    ListProvidersRequest, TrustSignalRequest, ProviderVerificationRequest,
    ProviderType, ProviderStatus, TrustLevel, ProviderCapability
)
from onyx.trust_registry_v1 import TrustRegistryV1
from onyx.trust_signals_v1 import TrustSignalGenerator


class TestTrustRegistryV1:
    """Test Trust Registry v1 functionality."""
    
    def test_registry_initialization(self):
        """Test trust registry initialization with default providers."""
        registry = TrustRegistryV1()
        
        # Should have default providers
        assert len(registry._providers) >= 3
        
        # Check default providers exist
        assert "stripe" in registry._providers
        assert "adyen" in registry._providers
        assert "carat" in registry._providers
        
        # Verify default provider properties
        stripe = registry.get_provider("stripe")
        assert stripe.provider_name == "Stripe"
        assert stripe.provider_type == ProviderType.PAYMENT_PROCESSOR
        assert stripe.trust_level == TrustLevel.CRITICAL
        assert stripe.status == ProviderStatus.ACTIVE
    
    def test_add_provider(self):
        """Test adding a new provider to the registry."""
        registry = TrustRegistryV1()
        
        # Create add request
        request = AddProviderRequest(
            provider_id="test_processor",
            provider_name="Test Payment Processor",
            provider_type=ProviderType.PAYMENT_PROCESSOR,
            organization="Test Corp",
            jurisdiction="US",
            website="https://test.com",
            contact_email="trust@test.com",
            capabilities=[ProviderCapability.PAYMENT_PROCESSING],
            supported_rails=["ACH", "debit"],
            initial_trust_level=TrustLevel.MEDIUM,
            metadata={"test": True}
        )
        
        # Add provider
        provider = registry.add_provider(request)
        
        # Verify provider was added
        assert provider.provider_id == "test_processor"
        assert provider.provider_name == "Test Payment Processor"
        assert provider.status == ProviderStatus.PENDING
        assert provider.trust_level == TrustLevel.MEDIUM
        
        # Verify provider can be retrieved
        retrieved = registry.get_provider("test_processor")
        assert retrieved is not None
        assert retrieved.provider_id == "test_processor"
    
    def test_add_duplicate_provider(self):
        """Test adding a duplicate provider fails."""
        registry = TrustRegistryV1()
        
        request = AddProviderRequest(
            provider_id="stripe",  # Already exists
            provider_name="Duplicate Stripe",
            provider_type=ProviderType.PAYMENT_PROCESSOR,
            organization="Duplicate Corp",
            jurisdiction="US"
        )
        
        with pytest.raises(ValueError, match="already exists"):
            registry.add_provider(request)
    
    def test_revoke_provider(self):
        """Test revoking a provider from the registry."""
        registry = TrustRegistryV1()
        
        # Create revoke request
        request = RevokeProviderRequest(
            provider_id="carat",
            reason="Security breach detected",
            notes="Immediate revocation required"
        )
        
        # Revoke provider
        provider = registry.revoke_provider(request)
        
        # Verify provider was revoked
        assert provider.status == ProviderStatus.REVOKED
        assert provider.revoked_at is not None
        assert "Security breach detected" in provider.notes
        
        # Verify revoked provider can still be retrieved
        retrieved = registry.get_provider("carat")
        assert retrieved.status == ProviderStatus.REVOKED
    
    def test_revoke_nonexistent_provider(self):
        """Test revoking a non-existent provider fails."""
        registry = TrustRegistryV1()
        
        request = RevokeProviderRequest(
            provider_id="nonexistent",
            reason="Test revocation"
        )
        
        with pytest.raises(ValueError, match="not found"):
            registry.revoke_provider(request)
    
    def test_list_providers_no_filters(self):
        """Test listing all providers without filters."""
        registry = TrustRegistryV1()
        
        request = ListProvidersRequest()
        response = registry.list_providers(request)
        
        # Should return all providers
        assert len(response.providers) >= 3
        assert response.total_count >= 3
        assert response.has_more is False
        
        # Providers should be sorted by name
        provider_names = [p.provider_name for p in response.providers]
        assert provider_names == sorted(provider_names)
    
    def test_list_providers_with_filters(self):
        """Test listing providers with various filters."""
        registry = TrustRegistryV1()
        
        # Filter by provider type
        request = ListProvidersRequest(provider_type=ProviderType.PAYMENT_PROCESSOR)
        response = registry.list_providers(request)
        
        assert all(p.provider_type == ProviderType.PAYMENT_PROCESSOR for p in response.providers)
        
        # Filter by trust level
        request = ListProvidersRequest(trust_level=TrustLevel.CRITICAL)
        response = registry.list_providers(request)
        
        assert all(p.trust_level == TrustLevel.CRITICAL for p in response.providers)
        
        # Filter by capability
        request = ListProvidersRequest(capability=ProviderCapability.PAYMENT_PROCESSING)
        response = registry.list_providers(request)
        
        assert all(ProviderCapability.PAYMENT_PROCESSING in p.capabilities for p in response.providers)
        
        # Filter by jurisdiction
        request = ListProvidersRequest(jurisdiction="US")
        response = registry.list_providers(request)
        
        assert all(p.jurisdiction == "US" for p in response.providers)
    
    def test_list_providers_pagination(self):
        """Test listing providers with pagination."""
        registry = TrustRegistryV1()
        
        # Add more providers for pagination testing
        for i in range(5):
            request = AddProviderRequest(
                provider_id=f"test_provider_{i}",
                provider_name=f"Test Provider {i}",
                provider_type=ProviderType.PAYMENT_PROCESSOR,
                organization=f"Test Corp {i}",
                jurisdiction="US"
            )
            registry.add_provider(request)
        
        # Test pagination
        request = ListProvidersRequest(limit=3, offset=0)
        response = registry.list_providers(request)
        
        assert len(response.providers) == 3
        assert response.total_count >= 8  # 3 default + 5 added
        assert response.has_more is True
        
        # Test second page
        request = ListProvidersRequest(limit=3, offset=3)
        response = registry.list_providers(request)
        
        assert len(response.providers) == 3
        assert response.has_more is True
    
    def test_verify_provider(self):
        """Test provider verification."""
        registry = TrustRegistryV1()
        
        # Create verification request
        request = ProviderVerificationRequest(
            provider_id="stripe",
            verification_type="compliance_check",
            verification_data={"compliance_doc": "soc2_report.pdf"},
            requested_capabilities=[ProviderCapability.PAYMENT_PROCESSING]
        )
        
        # Verify provider
        verification = registry.verify_provider(request)
        
        # Verify verification response
        assert verification.provider_id == "stripe"
        assert verification.verification_type == "compliance_check"
        assert verification.verified is True
        assert verification.verification_score > 0.0
        assert ProviderCapability.PAYMENT_PROCESSING in verification.verified_capabilities
        
        # Verify provider was updated
        provider = registry.get_provider("stripe")
        assert provider.verified_at is not None
        assert provider.verification_status == "verified"
    
    def test_verify_nonexistent_provider(self):
        """Test verifying a non-existent provider fails."""
        registry = TrustRegistryV1()
        
        request = ProviderVerificationRequest(
            provider_id="nonexistent",
            verification_type="test",
            verification_data={}
        )
        
        with pytest.raises(ValueError, match="not found"):
            registry.verify_provider(request)
    
    def test_get_trust_signal_for_provider(self):
        """Test getting trust signal for a provider."""
        registry = TrustRegistryV1()
        
        # Test with existing provider
        signal = registry.get_trust_signal_for_provider(
            "stripe", "ACH", {"amount": 100.0}
        )
        
        assert signal["trust_score"] > 0.0
        assert signal["risk_level"] in ["low", "medium", "high", "critical"]
        assert "explanation" in signal
        assert "provider_info" in signal
        
        # Test with non-existent provider
        signal = registry.get_trust_signal_for_provider(
            "nonexistent", "ACH", {}
        )
        
        assert signal["trust_score"] == 0.0
        assert signal["risk_level"] == "critical"
        assert "not found" in signal["explanation"]
    
    def test_get_stats(self):
        """Test getting trust registry statistics."""
        registry = TrustRegistryV1()
        
        stats = registry.get_stats()
        
        # Verify basic stats
        assert stats.total_providers >= 3
        assert stats.active_providers >= 3
        assert stats.average_trust_score > 0.0
        
        # Verify breakdowns
        assert "payment_processor" in stats.providers_by_type
        assert "critical" in stats.providers_by_trust_level
        assert "payment_processing" in stats.providers_by_capability
        assert "US" in stats.providers_by_jurisdiction


class TestTrustSignalGenerator:
    """Test trust signal generation functionality."""
    
    def test_generate_trust_signal_existing_provider(self):
        """Test generating trust signal for existing provider."""
        generator = TrustSignalGenerator()
        
        # Create trust signal request
        request = TrustSignalRequest(
            trace_id="test-trace-123",
            provider_id="stripe",
            rail_type="ACH",
            transaction_context={
                "amount": 1000.0,
                "merchant_risk_score": 0.3,
                "velocity": 5.0
            },
            user_context={"user_id": "user123"},
            merchant_context={"merchant_id": "merchant123"},
            amount=1000.0,
            currency="USD"
        )
        
        # Generate trust signal
        signal = generator.generate_trust_signal(request)
        
        # Verify signal properties
        assert signal.signal_id is not None
        assert signal.trace_id == "test-trace-123"
        assert signal.provider_id == "stripe"
        assert signal.rail_type == "ACH"
        assert 0.0 <= signal.trust_score <= 1.0
        assert signal.risk_level in ["low", "medium", "high", "critical"]
        assert 0.0 <= signal.confidence <= 1.0
        assert signal.explanation is not None
        assert signal.recommendation is not None
        
        # Verify rail preference adjustment
        assert 0.0 <= signal.adjusted_rail_preference <= 1.0
        assert signal.preference_adjustment != 0.0  # Should have some adjustment
    
    def test_generate_trust_signal_nonexistent_provider(self):
        """Test generating trust signal for non-existent provider."""
        generator = TrustSignalGenerator()
        
        request = TrustSignalRequest(
            trace_id="test-trace-456",
            provider_id="nonexistent_provider",
            rail_type="ACH",
            transaction_context={},
            amount=100.0
        )
        
        signal = generator.generate_trust_signal(request)
        
        # Should create negative signal
        assert signal.trust_score == 0.0
        assert signal.risk_level == "critical"
        assert signal.confidence == 1.0
        assert signal.recommendation == "block"
        assert "not found" in signal.explanation.lower()
    
    def test_trust_signal_lowers_preference_for_risky_rails(self):
        """Test that trust signals lower preference for risky rails."""
        generator = TrustSignalGenerator()
        
        # Test with high-risk context
        high_risk_request = TrustSignalRequest(
            trace_id="high-risk-trace",
            provider_id="stripe",
            rail_type="ACH",
            transaction_context={
                "amount": 50000.0,  # High amount
                "merchant_risk_score": 0.8,  # High risk merchant
                "velocity": 100.0,  # High velocity
                "cross_border": True
            },
            amount=50000.0
        )
        
        high_risk_signal = generator.generate_trust_signal(high_risk_request)
        
        # Test with low-risk context
        low_risk_request = TrustSignalRequest(
            trace_id="low-risk-trace",
            provider_id="stripe",
            rail_type="ACH",
            transaction_context={
                "amount": 50.0,  # Low amount
                "merchant_risk_score": 0.2,  # Low risk merchant
                "velocity": 1.0  # Low velocity
            },
            amount=50.0
        )
        
        low_risk_signal = generator.generate_trust_signal(low_risk_request)
        
        # High-risk should have lower rail preference
        assert high_risk_signal.adjusted_rail_preference < low_risk_signal.adjusted_rail_preference
        
        # High-risk should have more negative adjustment
        assert high_risk_signal.preference_adjustment < low_risk_signal.preference_adjustment
    
    def test_trust_signal_unsupported_rail(self):
        """Test trust signal for unsupported rail."""
        generator = TrustSignalGenerator()
        
        # Request unsupported rail for a provider
        request = TrustSignalRequest(
            trace_id="unsupported-rail-trace",
            provider_id="stripe",
            rail_type="crypto",  # Not supported by Stripe
            transaction_context={},
            amount=100.0
        )
        
        signal = generator.generate_trust_signal(request)
        
        # Should have lower trust score due to unsupported rail
        assert signal.trust_score < 0.9  # Lower than normal Stripe score
        assert signal.risk_level in ["medium", "high"]  # Higher risk due to unsupported rail
        assert "not supported" in signal.explanation.lower()
    
    def test_batch_generate_signals(self):
        """Test batch generation of trust signals."""
        generator = TrustSignalGenerator()
        
        # Create multiple requests
        requests = [
            TrustSignalRequest(
                trace_id=f"batch-trace-{i}",
                provider_id="stripe" if i % 2 == 0 else "adyen",
                rail_type="ACH",
                transaction_context={"amount": 100.0 + i * 10},
                amount=100.0 + i * 10
            )
            for i in range(5)
        ]
        
        # Generate batch signals
        signals = generator.batch_generate_signals(requests)
        
        # Verify all signals were generated
        assert len(signals) == 5
        
        # Verify each signal
        for i, signal in enumerate(signals):
            assert signal.trace_id == f"batch-trace-{i}"
            assert signal.provider_id in ["stripe", "adyen"]
            assert signal.trust_score > 0.0
            assert signal.explanation is not None
    
    def test_trust_signal_risk_factors(self):
        """Test trust signal risk factor extraction."""
        generator = TrustSignalGenerator()
        
        request = TrustSignalRequest(
            trace_id="risk-factors-trace",
            provider_id="stripe",
            rail_type="ACH",
            transaction_context={
                "amount": 60000.0,  # High amount
                "velocity": 150.0,  # High velocity
                "cross_border": True,
                "off_hours": True
            },
            amount=60000.0
        )
        
        signal = generator.generate_trust_signal(request)
        
        # Should have various risk factors
        assert len(signal.risk_factors) > 0
        assert "high_amount" in signal.risk_factors
        assert "high_velocity" in signal.risk_factors
        assert "cross_border" in signal.risk_factors
        assert "off_hours" in signal.risk_factors
        
        # Risk factors should have positive values
        for factor, value in signal.risk_factors.items():
            assert 0.0 <= value <= 1.0


class TestIntegrationScenarios:
    """Test end-to-end integration scenarios."""
    
    def test_trust_signal_integration_flow(self):
        """Test complete trust signal integration flow."""
        # Initialize components
        registry = TrustRegistryV1()
        generator = TrustSignalGenerator()
        
        # Add a new provider
        add_request = AddProviderRequest(
            provider_id="new_processor",
            provider_name="New Payment Processor",
            provider_type=ProviderType.PAYMENT_PROCESSOR,
            organization="New Corp",
            jurisdiction="CA",
            capabilities=[ProviderCapability.PAYMENT_PROCESSING],
            supported_rails=["ACH", "debit"],
            initial_trust_level=TrustLevel.MEDIUM
        )
        
        provider = registry.add_provider(add_request)
        assert provider.status == ProviderStatus.PENDING
        
        # Verify the provider
        verify_request = ProviderVerificationRequest(
            provider_id="new_processor",
            verification_type="initial_verification",
            verification_data={"documents": "business_license.pdf"},
            requested_capabilities=[ProviderCapability.PAYMENT_PROCESSING]
        )
        
        verification = registry.verify_provider(verify_request)
        assert verification.verified is True
        
        # Generate trust signal for the new provider
        signal_request = TrustSignalRequest(
            trace_id="integration-test",
            provider_id="new_processor",
            rail_type="ACH",
            transaction_context={"amount": 500.0},
            amount=500.0
        )
        
        signal = generator.generate_trust_signal(signal_request)
        
        # Verify trust signal
        assert signal.provider_id == "new_processor"
        assert signal.trust_score > 0.0
        assert signal.explanation is not None
        
        # Verify provider is now in registry stats
        stats = registry.get_stats()
        assert stats.total_providers >= 4  # 3 default + 1 new
    
    def test_provider_revocation_affects_trust_signals(self):
        """Test that provider revocation affects trust signal generation."""
        registry = TrustRegistryV1()
        generator = TrustSignalGenerator()
        
        # Generate trust signal for active provider
        request = TrustSignalRequest(
            trace_id="before-revocation",
            provider_id="carat",
            rail_type="ACH",
            transaction_context={},
            amount=100.0
        )
        
        before_signal = generator.generate_trust_signal(request)
        assert before_signal.trust_score > 0.5  # Should have reasonable trust score
        
        # Revoke the provider
        revoke_request = RevokeProviderRequest(
            provider_id="carat",
            reason="Security incident"
        )
        
        registry.revoke_provider(revoke_request)
        
        # Generate trust signal after revocation
        request.trace_id = "after-revocation"
        after_signal = generator.generate_trust_signal(request)
        
        # Trust score should be significantly lower after revocation
        assert after_signal.trust_score < before_signal.trust_score
        assert after_signal.risk_level in ["high", "critical"]
    
    def test_filtered_provider_listing(self):
        """Test comprehensive provider listing with filters."""
        registry = TrustRegistryV1()
        
        # Test various filter combinations
        filters = [
            {"provider_type": ProviderType.PAYMENT_PROCESSOR},
            {"trust_level": TrustLevel.CRITICAL},
            {"capability": ProviderCapability.PAYMENT_PROCESSING},
            {"jurisdiction": "US"},
            {"provider_type": ProviderType.PAYMENT_PROCESSOR, "jurisdiction": "US"}
        ]
        
        for filter_params in filters:
            request = ListProvidersRequest(**filter_params)
            response = registry.list_providers(request)
            
            # Verify all returned providers match filters
            for provider in response.providers:
                if "provider_type" in filter_params:
                    assert provider.provider_type == filter_params["provider_type"]
                if "trust_level" in filter_params:
                    assert provider.trust_level == filter_params["trust_level"]
                if "capability" in filter_params:
                    assert filter_params["capability"] in provider.capabilities
                if "jurisdiction" in filter_params:
                    assert provider.jurisdiction == filter_params["jurisdiction"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])








