"""
Trust Registry v1 implementation for Onyx Phase 4.

Provides API-backed trust registry with comprehensive CRUD operations,
provider verification, and trust signal integration for payment processor
evaluation during negotiation.
"""

import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from pydantic import ValidationError

from onyx.models import (
    TrustRegistryProvider, AddProviderRequest, RevokeProviderRequest,
    ListProvidersRequest, ListProvidersResponse, ProviderVerificationRequest,
    ProviderVerificationResponse, TrustRegistryStats,
    ProviderType, ProviderStatus, TrustLevel, ProviderCapability
)

logger = logging.getLogger(__name__)


class TrustRegistryV1:
    """
    Trust Registry v1 - API-backed provider management.
    
    Provides comprehensive CRUD operations for trust registry providers
    with verification, compliance monitoring, and trust signal integration.
    """
    
    def __init__(self, storage_backend: str = "memory"):
        """
        Initialize Trust Registry v1.
        
        Args:
            storage_backend: Storage backend type ("memory", "database", "file")
        """
        self.storage_backend = storage_backend
        self._providers: Dict[str, TrustRegistryProvider] = {}
        self._provider_indexes: Dict[str, Set[str]] = {
            "by_status": {},
            "by_type": {},
            "by_trust_level": {},
            "by_capability": {},
            "by_jurisdiction": {}
        }
        self._verification_history: List[ProviderVerificationResponse] = []
        
        # Load default providers
        self._load_default_providers()
        
        logger.info(f"Trust Registry v1 initialized with {storage_backend} backend")
    
    def _load_default_providers(self) -> None:
        """Load default trusted providers."""
        default_providers = [
            {
                "provider_id": "stripe",
                "provider_name": "Stripe",
                "provider_type": ProviderType.PAYMENT_PROCESSOR,
                "organization": "Stripe, Inc.",
                "jurisdiction": "US",
                "website": "https://stripe.com",
                "contact_email": "trust@stripe.com",
                "capabilities": [
                    ProviderCapability.PAYMENT_PROCESSING,
                    ProviderCapability.FRAUD_DETECTION,
                    ProviderCapability.RISK_SCORING
                ],
                "supported_rails": ["ACH", "debit", "credit"],
                "trust_level": TrustLevel.CRITICAL,
                "trust_score": 0.95,
                "verification_status": "verified",
                "compliance_status": "compliant",
                "metadata": {
                    "pci_compliant": True,
                    "soc2_certified": True,
                    "established_year": 2010
                }
            },
            {
                "provider_id": "adyen",
                "provider_name": "Adyen",
                "provider_type": ProviderType.PAYMENT_PROCESSOR,
                "organization": "Adyen N.V.",
                "jurisdiction": "NL",
                "website": "https://adyen.com",
                "contact_email": "trust@adyen.com",
                "capabilities": [
                    ProviderCapability.PAYMENT_PROCESSING,
                    ProviderCapability.FRAUD_DETECTION,
                    ProviderCapability.RISK_SCORING,
                    ProviderCapability.AML_SCREENING
                ],
                "supported_rails": ["ACH", "debit", "credit"],
                "trust_level": TrustLevel.CRITICAL,
                "trust_score": 0.93,
                "verification_status": "verified",
                "compliance_status": "compliant",
                "metadata": {
                    "pci_compliant": True,
                    "iso27001_certified": True,
                    "established_year": 2006
                }
            },
            {
                "provider_id": "carat",
                "provider_name": "Carat",
                "provider_type": ProviderType.PAYMENT_PROCESSOR,
                "organization": "Carat, LLC",
                "jurisdiction": "US",
                "website": "https://carat.com",
                "contact_email": "trust@carat.com",
                "capabilities": [
                    ProviderCapability.PAYMENT_PROCESSING,
                    ProviderCapability.RISK_SCORING
                ],
                "supported_rails": ["ACH", "debit"],
                "trust_level": TrustLevel.HIGH,
                "trust_score": 0.88,
                "verification_status": "verified",
                "compliance_status": "compliant",
                "metadata": {
                    "pci_compliant": True,
                    "established_year": 2018
                }
            }
        ]
        
        for provider_data in default_providers:
            try:
                provider = TrustRegistryProvider(**provider_data)
                self._providers[provider.provider_id] = provider
                self._update_indexes(provider)
                logger.info(f"Loaded default provider: {provider.provider_id}")
            except ValidationError as e:
                logger.error(f"Failed to load default provider {provider_data['provider_id']}: {e}")
    
    def _update_indexes(self, provider: TrustRegistryProvider) -> None:
        """Update provider indexes for efficient querying."""
        provider_id = provider.provider_id
        
        # Update status index
        if provider.status not in self._provider_indexes["by_status"]:
            self._provider_indexes["by_status"][provider.status] = set()
        self._provider_indexes["by_status"][provider.status].add(provider_id)
        
        # Update type index
        if provider.provider_type not in self._provider_indexes["by_type"]:
            self._provider_indexes["by_type"][provider.provider_type] = set()
        self._provider_indexes["by_type"][provider.provider_type].add(provider_id)
        
        # Update trust level index
        if provider.trust_level not in self._provider_indexes["by_trust_level"]:
            self._provider_indexes["by_trust_level"][provider.trust_level] = set()
        self._provider_indexes["by_trust_level"][provider.trust_level].add(provider_id)
        
        # Update capability index
        for capability in provider.capabilities:
            if capability not in self._provider_indexes["by_capability"]:
                self._provider_indexes["by_capability"][capability] = set()
            self._provider_indexes["by_capability"][capability].add(provider_id)
        
        # Update jurisdiction index
        if provider.jurisdiction not in self._provider_indexes["by_jurisdiction"]:
            self._provider_indexes["by_jurisdiction"][provider.jurisdiction] = set()
        self._provider_indexes["by_jurisdiction"][provider.jurisdiction].add(provider_id)
    
    def add_provider(self, request: AddProviderRequest) -> TrustRegistryProvider:
        """
        Add a new provider to the trust registry.
        
        Args:
            request: Add provider request
            
        Returns:
            Created provider entry
            
        Raises:
            ValueError: If provider already exists
        """
        if request.provider_id in self._providers:
            raise ValueError(f"Provider {request.provider_id} already exists")
        
        # Create provider entry
        provider = TrustRegistryProvider(
            provider_id=request.provider_id,
            provider_name=request.provider_name,
            provider_type=request.provider_type,
            status=ProviderStatus.PENDING,
            trust_level=request.initial_trust_level,
            organization=request.organization,
            jurisdiction=request.jurisdiction,
            website=request.website,
            contact_email=request.contact_email,
            capabilities=request.capabilities,
            supported_rails=request.supported_rails,
            trust_score=0.0,  # Initial trust score
            metadata=request.metadata,
            notes=request.notes
        )
        
        # Store provider
        self._providers[provider.provider_id] = provider
        self._update_indexes(provider)
        
        logger.info(f"Added provider {provider.provider_id} to trust registry")
        return provider
    
    def revoke_provider(self, request: RevokeProviderRequest) -> TrustRegistryProvider:
        """
        Revoke a provider from the trust registry.
        
        Args:
            request: Revoke provider request
            
        Returns:
            Updated provider entry
            
        Raises:
            ValueError: If provider doesn't exist
        """
        if request.provider_id not in self._providers:
            raise ValueError(f"Provider {request.provider_id} not found")
        
        provider = self._providers[request.provider_id]
        
        # Update provider status
        provider.status = ProviderStatus.REVOKED
        provider.revoked_at = request.effective_date or datetime.now()
        provider.last_updated = datetime.now()
        
        # Update notes
        if provider.notes:
            provider.notes += f"\nRevoked: {request.reason}"
        else:
            provider.notes = f"Revoked: {request.reason}"
        
        if request.notes:
            provider.notes += f"\nAdditional notes: {request.notes}"
        
        logger.info(f"Revoked provider {provider.provider_id}: {request.reason}")
        return provider
    
    def list_providers(self, request: ListProvidersRequest) -> ListProvidersResponse:
        """
        List providers from the trust registry with filtering.
        
        Args:
            request: List providers request with filters
            
        Returns:
            Filtered list of providers
        """
        # Start with all providers
        provider_ids = set(self._providers.keys())
        
        # Apply filters
        if request.status:
            status_ids = self._provider_indexes["by_status"].get(request.status, set())
            provider_ids = provider_ids.intersection(status_ids)
        
        if request.provider_type:
            type_ids = self._provider_indexes["by_type"].get(request.provider_type, set())
            provider_ids = provider_ids.intersection(type_ids)
        
        if request.trust_level:
            trust_ids = self._provider_indexes["by_trust_level"].get(request.trust_level, set())
            provider_ids = provider_ids.intersection(trust_ids)
        
        if request.capability:
            capability_ids = self._provider_indexes["by_capability"].get(request.capability, set())
            provider_ids = provider_ids.intersection(capability_ids)
        
        if request.jurisdiction:
            jurisdiction_ids = self._provider_indexes["by_jurisdiction"].get(request.jurisdiction, set())
            provider_ids = provider_ids.intersection(jurisdiction_ids)
        
        # Convert to list and sort
        filtered_providers = [self._providers[pid] for pid in provider_ids]
        filtered_providers.sort(key=lambda p: p.provider_name)
        
        # Apply pagination
        total_count = len(filtered_providers)
        start_idx = request.offset
        end_idx = start_idx + request.limit
        paginated_providers = filtered_providers[start_idx:end_idx]
        
        has_more = end_idx < total_count
        
        return ListProvidersResponse(
            providers=paginated_providers,
            total_count=total_count,
            limit=request.limit,
            offset=request.offset,
            has_more=has_more
        )
    
    def get_provider(self, provider_id: str) -> Optional[TrustRegistryProvider]:
        """
        Get a provider by ID.
        
        Args:
            provider_id: Provider identifier
            
        Returns:
            Provider entry or None if not found
        """
        return self._providers.get(provider_id)
    
    def verify_provider(self, request: ProviderVerificationRequest) -> ProviderVerificationResponse:
        """
        Verify a provider's credentials and capabilities.
        
        Args:
            request: Verification request
            
        Returns:
            Verification response
        """
        provider = self.get_provider(request.provider_id)
        if not provider:
            raise ValueError(f"Provider {request.provider_id} not found")
        
        # Simulate verification process
        verification_id = str(uuid.uuid4())
        verified = True
        verification_score = 0.85  # Simulated score
        issues = []
        verified_capabilities = []
        
        # Check requested capabilities
        for capability in request.requested_capabilities:
            if capability in provider.capabilities:
                verified_capabilities.append(capability)
            else:
                issues.append(f"Provider does not support capability: {capability}")
        
        # Simulate some verification issues
        if provider.trust_score < 0.5:
            issues.append("Low trust score detected")
            verified = False
        
        if provider.status != ProviderStatus.ACTIVE:
            issues.append(f"Provider status is {provider.status}")
            verified = False
        
        # Create verification response
        verification = ProviderVerificationResponse(
            verification_id=verification_id,
            provider_id=request.provider_id,
            verification_type=request.verification_type,
            verified=verified,
            verification_score=verification_score,
            verified_capabilities=verified_capabilities,
            issues=issues,
            notes=f"Verification completed for {request.verification_type}",
            verified_by="onyx-system"
        )
        
        # Store verification history
        self._verification_history.append(verification)
        
        # Update provider if verification successful
        if verified:
            provider.verified_at = datetime.now()
            provider.verification_status = "verified"
            provider.last_updated = datetime.now()
        
        logger.info(f"Verified provider {request.provider_id}: {verified}")
        return verification
    
    def get_trust_signal_for_provider(
        self,
        provider_id: str,
        rail_type: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate trust signal for a specific provider and rail.
        
        Args:
            provider_id: Provider identifier
            rail_type: Payment rail type
            context: Transaction context
            
        Returns:
            Trust signal data
        """
        provider = self.get_provider(provider_id)
        if not provider:
            return {
                "trust_score": 0.0,
                "risk_level": "critical",
                "confidence": 1.0,
                "recommendation": "block",
                "explanation": f"Provider {provider_id} not found in trust registry"
            }
        
        # Calculate trust score based on provider metrics
        base_trust_score = provider.trust_score
        
        # Adjust based on provider status
        status_multiplier = {
            ProviderStatus.ACTIVE: 1.0,
            ProviderStatus.SUSPENDED: 0.3,
            ProviderStatus.UNDER_REVIEW: 0.6,
            ProviderStatus.PENDING: 0.4,
            ProviderStatus.REVOKED: 0.0
        }
        
        adjusted_trust_score = base_trust_score * status_multiplier.get(provider.status, 0.0)
        
        # Adjust based on trust level
        trust_level_multiplier = {
            TrustLevel.CRITICAL: 1.0,
            TrustLevel.HIGH: 0.9,
            TrustLevel.MEDIUM: 0.7,
            TrustLevel.LOW: 0.4,
            TrustLevel.UNTRUSTED: 0.0
        }
        
        final_trust_score = adjusted_trust_score * trust_level_multiplier.get(provider.trust_level, 0.0)
        
        # Determine risk level
        if final_trust_score >= 0.8:
            risk_level = "low"
            recommendation = "allow"
        elif final_trust_score >= 0.6:
            risk_level = "medium"
            recommendation = "review"
        elif final_trust_score >= 0.3:
            risk_level = "high"
            recommendation = "restrict"
        else:
            risk_level = "critical"
            recommendation = "block"
        
        # Check if rail is supported
        if rail_type not in provider.supported_rails:
            final_trust_score *= 0.5  # Reduce trust for unsupported rails
            risk_level = "high"
            recommendation = "restrict"
        
        return {
            "trust_score": final_trust_score,
            "risk_level": risk_level,
            "confidence": 0.9,
            "recommendation": recommendation,
            "explanation": f"Provider {provider.provider_name} ({provider.trust_level} trust, {provider.status} status)",
            "trust_factors": {
                "base_trust_score": base_trust_score,
                "status_multiplier": status_multiplier.get(provider.status, 0.0),
                "trust_level_multiplier": trust_level_multiplier.get(provider.trust_level, 0.0),
                "rail_support": rail_type in provider.supported_rails
            },
            "provider_info": {
                "provider_id": provider.provider_id,
                "provider_name": provider.provider_name,
                "trust_level": provider.trust_level,
                "status": provider.status,
                "capabilities": [cap.value for cap in provider.capabilities]
            }
        }
    
    def get_stats(self) -> TrustRegistryStats:
        """
        Get comprehensive statistics about the trust registry.
        
        Returns:
            Trust registry statistics
        """
        total_providers = len(self._providers)
        
        # Count by status
        active_providers = len(self._provider_indexes["by_status"].get(ProviderStatus.ACTIVE, set()))
        suspended_providers = len(self._provider_indexes["by_status"].get(ProviderStatus.SUSPENDED, set()))
        revoked_providers = len(self._provider_indexes["by_status"].get(ProviderStatus.REVOKED, set()))
        
        # Count by type
        providers_by_type = {
            provider_type.value: len(provider_ids)
            for provider_type, provider_ids in self._provider_indexes["by_type"].items()
        }
        
        # Count by trust level
        providers_by_trust_level = {
            trust_level.value: len(provider_ids)
            for trust_level, provider_ids in self._provider_indexes["by_trust_level"].items()
        }
        
        # Count by capability
        providers_by_capability = {
            capability.value: len(provider_ids)
            for capability, provider_ids in self._provider_indexes["by_capability"].items()
        }
        
        # Count by jurisdiction
        providers_by_jurisdiction = {
            jurisdiction: len(provider_ids)
            for jurisdiction, provider_ids in self._provider_indexes["by_jurisdiction"].items()
        }
        
        # Calculate trust metrics
        trust_scores = [p.trust_score for p in self._providers.values()]
        average_trust_score = sum(trust_scores) / len(trust_scores) if trust_scores else 0.0
        
        high_trust_providers = sum(1 for p in self._providers.values() if p.trust_score >= 0.8)
        low_trust_providers = sum(1 for p in self._providers.values() if p.trust_score < 0.5)
        
        # Find latest timestamps
        last_provider_added = max((p.added_at for p in self._providers.values()), default=None)
        last_provider_verified = max((p.verified_at for p in self._providers.values() if p.verified_at), default=None)
        
        return TrustRegistryStats(
            total_providers=total_providers,
            active_providers=active_providers,
            suspended_providers=suspended_providers,
            revoked_providers=revoked_providers,
            providers_by_type=providers_by_type,
            providers_by_trust_level=providers_by_trust_level,
            providers_by_capability=providers_by_capability,
            providers_by_jurisdiction=providers_by_jurisdiction,
            average_trust_score=average_trust_score,
            high_trust_providers=high_trust_providers,
            low_trust_providers=low_trust_providers,
            last_provider_added=last_provider_added,
            last_provider_verified=last_provider_verified
        )


# Global instance
_trust_registry_v1 = None


def get_trust_registry_v1() -> TrustRegistryV1:
    """Get global Trust Registry v1 instance."""
    global _trust_registry_v1
    if _trust_registry_v1 is None:
        _trust_registry_v1 = TrustRegistryV1()
    return _trust_registry_v1








