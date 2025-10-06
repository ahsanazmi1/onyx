#!/usr/bin/env python3
"""
Onyx Phase 4 Demo Script

Demonstrates Trust Registry v1 with comprehensive CRUD operations,
trust signal generation during negotiation, and provider verification
for payment processor evaluation and risk assessment.
"""

import json
import sys
import os
from datetime import datetime, timedelta
from typing import List

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from onyx.models import (
    AddProviderRequest, RevokeProviderRequest, ListProvidersRequest,
    TrustSignalRequest, ProviderVerificationRequest,
    ProviderType, ProviderStatus, TrustLevel, ProviderCapability
)
from onyx.trust_registry_v1 import get_trust_registry_v1
from onyx.trust_signals_v1 import get_trust_signal_generator


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def print_subsection(title: str):
    """Print a formatted subsection header."""
    print(f"\n{'-'*40}")
    print(f"  {title}")
    print(f"{'-'*40}")


def demo_trust_registry_crud():
    """Demonstrate Trust Registry v1 CRUD operations."""
    print_section("TRUST REGISTRY v1 - CRUD OPERATIONS")
    
    registry = get_trust_registry_v1()
    
    print(f"✅ Trust Registry v1 initialized")
    
    # Show default providers
    print_subsection("Default Providers")
    request = ListProvidersRequest()
    response = registry.list_providers(request)
    
    print(f"📊 Total providers: {response.total_count}")
    for provider in response.providers:
        print(f"   - {provider.provider_name} ({provider.provider_id})")
        print(f"     Type: {provider.provider_type}, Trust: {provider.trust_level}, Status: {provider.status}")
        print(f"     Capabilities: {', '.join([cap.value for cap in provider.capabilities])}")
    
    # Add a new provider
    print_subsection("Adding New Provider")
    
    add_request = AddProviderRequest(
        provider_id="demo_processor",
        provider_name="Demo Payment Processor",
        provider_type=ProviderType.PAYMENT_PROCESSOR,
        organization="Demo Corp",
        jurisdiction="US",
        website="https://demo-processor.com",
        contact_email="trust@demo-processor.com",
        capabilities=[
            ProviderCapability.PAYMENT_PROCESSING,
            ProviderCapability.FRAUD_DETECTION
        ],
        supported_rails=["ACH", "debit", "credit"],
        initial_trust_level=TrustLevel.MEDIUM,
        metadata={"demo": True, "established_year": 2023},
        notes="Demo processor for testing purposes"
    )
    
    provider = registry.add_provider(add_request)
    print(f"✅ Added provider: {provider.provider_name}")
    print(f"   ID: {provider.provider_id}")
    print(f"   Status: {provider.status}")
    print(f"   Trust Level: {provider.trust_level}")
    
    # Verify the provider
    print_subsection("Verifying Provider")
    
    verify_request = ProviderVerificationRequest(
        provider_id="demo_processor",
        verification_type="initial_verification",
        verification_data={
            "business_license": "demo_license.pdf",
            "pci_compliance": "pci_report.pdf"
        },
        requested_capabilities=[
            ProviderCapability.PAYMENT_PROCESSING,
            ProviderCapability.FRAUD_DETECTION
        ]
    )
    
    verification = registry.verify_provider(verify_request)
    print(f"✅ Verification completed: {verification.verified}")
    print(f"   Score: {verification.verification_score:.2f}")
    print(f"   Verified capabilities: {', '.join([cap.value for cap in verification.verified_capabilities])}")
    if verification.issues:
        print(f"   Issues: {', '.join(verification.issues)}")
    
    # List providers with filters
    print_subsection("Filtered Provider Listing")
    
    # Filter by trust level
    high_trust_request = ListProvidersRequest(trust_level=TrustLevel.CRITICAL)
    high_trust_response = registry.list_providers(high_trust_request)
    print(f"📊 Critical trust providers: {high_trust_response.total_count}")
    for provider in high_trust_response.providers:
        print(f"   - {provider.provider_name}: {provider.trust_score:.2f}")
    
    # Filter by capability
    fraud_detection_request = ListProvidersRequest(capability=ProviderCapability.FRAUD_DETECTION)
    fraud_response = registry.list_providers(fraud_detection_request)
    print(f"📊 Providers with fraud detection: {fraud_response.total_count}")
    
    # Get registry statistics
    print_subsection("Registry Statistics")
    
    stats = registry.get_stats()
    print(f"📈 Registry Statistics:")
    print(f"   Total providers: {stats.total_providers}")
    print(f"   Active providers: {stats.active_providers}")
    print(f"   Average trust score: {stats.average_trust_score:.2f}")
    print(f"   High trust providers: {stats.high_trust_providers}")
    print(f"   Low trust providers: {stats.low_trust_providers}")
    
    print(f"   By type: {stats.providers_by_type}")
    print(f"   By trust level: {stats.providers_by_trust_level}")
    print(f"   By jurisdiction: {stats.providers_by_jurisdiction}")


def demo_trust_signal_generation():
    """Demonstrate trust signal generation during negotiation."""
    print_section("TRUST SIGNAL GENERATION")
    
    generator = get_trust_signal_generator()
    
    print(f"✅ Trust signal generator initialized")
    
    # Generate trust signals for different scenarios
    print_subsection("Low Risk Transaction")
    
    low_risk_request = TrustSignalRequest(
        trace_id="low-risk-demo-001",
        provider_id="stripe",
        rail_type="ACH",
        transaction_context={
            "amount": 100.0,
            "merchant_risk_score": 0.2,
            "velocity": 2.0,
            "cross_border": False
        },
        user_context={"user_id": "user123", "account_age_days": 365},
        merchant_context={"merchant_id": "merchant123", "established": True},
        amount=100.0,
        currency="USD"
    )
    
    low_risk_signal = generator.generate_trust_signal(low_risk_request)
    
    print(f"🎯 Trust Signal for Stripe (Low Risk):")
    print(f"   Trust Score: {low_risk_signal.trust_score:.3f}")
    print(f"   Risk Level: {low_risk_signal.risk_level}")
    print(f"   Confidence: {low_risk_signal.confidence:.3f}")
    print(f"   Rail Preference: {low_risk_signal.original_rail_preference:.3f} → {low_risk_signal.adjusted_rail_preference:.3f}")
    print(f"   Adjustment: {low_risk_signal.preference_adjustment:+.3f}")
    print(f"   Recommendation: {low_risk_signal.recommendation}")
    print(f"   Explanation: {low_risk_signal.explanation}")
    
    print_subsection("High Risk Transaction")
    
    high_risk_request = TrustSignalRequest(
        trace_id="high-risk-demo-002",
        provider_id="stripe",
        rail_type="ACH",
        transaction_context={
            "amount": 50000.0,
            "merchant_risk_score": 0.8,
            "velocity": 50.0,
            "cross_border": True,
            "off_hours": True
        },
        user_context={"user_id": "user456", "account_age_days": 7},
        merchant_context={"merchant_id": "merchant456", "established": False},
        amount=50000.0,
        currency="USD"
    )
    
    high_risk_signal = generator.generate_trust_signal(high_risk_request)
    
    print(f"🎯 Trust Signal for Stripe (High Risk):")
    print(f"   Trust Score: {high_risk_signal.trust_score:.3f}")
    print(f"   Risk Level: {high_risk_signal.risk_level}")
    print(f"   Confidence: {high_risk_signal.confidence:.3f}")
    print(f"   Rail Preference: {high_risk_signal.original_rail_preference:.3f} → {high_risk_signal.adjusted_rail_preference:.3f}")
    print(f"   Adjustment: {high_risk_signal.preference_adjustment:+.3f}")
    print(f"   Recommendation: {high_risk_signal.recommendation}")
    print(f"   Explanation: {high_risk_signal.explanation}")
    
    # Show risk factors
    print(f"   Risk Factors:")
    for factor, value in high_risk_signal.risk_factors.items():
        print(f"     - {factor}: {value:.3f}")
    
    print_subsection("Unsupported Rail Test")
    
    unsupported_request = TrustSignalRequest(
        trace_id="unsupported-rail-demo-003",
        provider_id="stripe",
        rail_type="crypto",  # Not supported by Stripe
        transaction_context={"amount": 1000.0},
        amount=1000.0
    )
    
    unsupported_signal = generator.generate_trust_signal(unsupported_request)
    
    print(f"🎯 Trust Signal for Stripe (Unsupported Rail):")
    print(f"   Trust Score: {unsupported_signal.trust_score:.3f}")
    print(f"   Risk Level: {unsupported_signal.risk_level}")
    print(f"   Recommendation: {unsupported_signal.recommendation}")
    print(f"   Explanation: {unsupported_signal.explanation}")
    
    print_subsection("Nonexistent Provider Test")
    
    nonexistent_request = TrustSignalRequest(
        trace_id="nonexistent-demo-004",
        provider_id="nonexistent_processor",
        rail_type="ACH",
        transaction_context={"amount": 100.0},
        amount=100.0
    )
    
    nonexistent_signal = generator.generate_trust_signal(nonexistent_request)
    
    print(f"🎯 Trust Signal for Nonexistent Provider:")
    print(f"   Trust Score: {nonexistent_signal.trust_score:.3f}")
    print(f"   Risk Level: {nonexistent_signal.risk_level}")
    print(f"   Recommendation: {nonexistent_signal.recommendation}")
    print(f"   Explanation: {nonexistent_signal.explanation}")


def demo_batch_processing():
    """Demonstrate batch trust signal generation."""
    print_section("BATCH TRUST SIGNAL PROCESSING")
    
    generator = get_trust_signal_generator()
    
    # Create multiple requests for different providers and scenarios
    requests = [
        TrustSignalRequest(
            trace_id=f"batch-demo-{i:03d}",
            provider_id="stripe" if i % 3 == 0 else "adyen" if i % 3 == 1 else "carat",
            rail_type="ACH",
            transaction_context={
                "amount": 1000.0 + i * 500,
                "merchant_risk_score": 0.3 + (i % 3) * 0.2,
                "velocity": 5.0 + i
            },
            amount=1000.0 + i * 500
        )
        for i in range(9)
    ]
    
    print(f"🚀 Generating trust signals for {len(requests)} transactions...")
    
    signals = generator.batch_generate_signals(requests)
    
    print(f"✅ Generated {len(signals)} trust signals")
    
    # Analyze results
    print_subsection("Batch Results Analysis")
    
    by_provider = {}
    by_risk_level = {}
    
    for signal in signals:
        provider = signal.provider_id
        risk = signal.risk_level
        
        if provider not in by_provider:
            by_provider[provider] = []
        by_provider[provider].append(signal)
        
        if risk not in by_risk_level:
            by_risk_level[risk] = []
        by_risk_level[risk].append(signal)
    
    print(f"📊 Results by Provider:")
    for provider, provider_signals in by_provider.items():
        avg_score = sum(s.trust_score for s in provider_signals) / len(provider_signals)
        avg_preference = sum(s.adjusted_rail_preference for s in provider_signals) / len(provider_signals)
        print(f"   {provider}: {len(provider_signals)} signals, avg trust: {avg_score:.3f}, avg preference: {avg_preference:.3f}")
    
    print(f"📊 Results by Risk Level:")
    for risk_level, risk_signals in by_risk_level.items():
        avg_score = sum(s.trust_score for s in risk_signals) / len(risk_signals)
        print(f"   {risk_level}: {len(risk_signals)} signals, avg trust: {avg_score:.3f}")


def demo_provider_revocation_impact():
    """Demonstrate how provider revocation affects trust signals."""
    print_section("PROVIDER REVOCATION IMPACT")
    
    registry = get_trust_registry_v1()
    generator = get_trust_signal_generator()
    
    # Generate trust signal before revocation
    print_subsection("Before Provider Revocation")
    
    before_request = TrustSignalRequest(
        trace_id="before-revocation-demo",
        provider_id="carat",
        rail_type="ACH",
        transaction_context={"amount": 1000.0},
        amount=1000.0
    )
    
    before_signal = generator.generate_trust_signal(before_request)
    print(f"🎯 Carat Trust Signal (Before Revocation):")
    print(f"   Trust Score: {before_signal.trust_score:.3f}")
    print(f"   Risk Level: {before_signal.risk_level}")
    print(f"   Recommendation: {before_signal.recommendation}")
    
    # Revoke the provider
    print_subsection("Revoking Provider")
    
    revoke_request = RevokeProviderRequest(
        provider_id="carat",
        reason="Demo revocation for testing purposes",
        notes="This is a demo revocation to test trust signal impact"
    )
    
    provider = registry.revoke_provider(revoke_request)
    print(f"🚫 Revoked provider: {provider.provider_name}")
    print(f"   Status: {provider.status}")
    print(f"   Revoked at: {provider.revoked_at}")
    
    # Generate trust signal after revocation
    print_subsection("After Provider Revocation")
    
    after_request = TrustSignalRequest(
        trace_id="after-revocation-demo",
        provider_id="carat",
        rail_type="ACH",
        transaction_context={"amount": 1000.0},
        amount=1000.0
    )
    
    after_signal = generator.generate_trust_signal(after_request)
    print(f"🎯 Carat Trust Signal (After Revocation):")
    print(f"   Trust Score: {after_signal.trust_score:.3f}")
    print(f"   Risk Level: {after_signal.risk_level}")
    print(f"   Recommendation: {after_signal.recommendation}")
    
    # Show impact
    print_subsection("Impact Analysis")
    
    trust_score_change = after_signal.trust_score - before_signal.trust_score
    preference_change = after_signal.adjusted_rail_preference - before_signal.adjusted_rail_preference
    
    print(f"📉 Trust Score Change: {trust_score_change:+.3f}")
    print(f"📉 Rail Preference Change: {preference_change:+.3f}")
    print(f"🔄 Risk Level Change: {before_signal.risk_level} → {after_signal.risk_level}")
    
    if after_signal.trust_score < before_signal.trust_score:
        print(f"✅ Revocation successfully reduced trust score")
    if after_signal.adjusted_rail_preference < before_signal.adjusted_rail_preference:
        print(f"✅ Revocation successfully reduced rail preference")


def main():
    """Run the complete Onyx Phase 4 demo."""
    print("🚀 Onyx Phase 4 Demo - Trust Registry v1 & Trust Signals")
    print(f"   Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        # Run all demo sections
        demo_trust_registry_crud()
        demo_trust_signal_generation()
        demo_batch_processing()
        demo_provider_revocation_impact()
        
        print_section("DEMO COMPLETED SUCCESSFULLY")
        print("✅ All Onyx Phase 4 features demonstrated successfully!")
        print("   - Trust Registry v1 with CRUD operations")
        print("   - Provider verification and management")
        print("   - Trust signal generation during negotiation")
        print("   - Rail preference adjustment based on trust")
        print("   - Batch processing capabilities")
        print("   - Provider revocation impact on trust signals")
        print("   - Comprehensive API endpoints")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()








