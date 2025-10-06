"""
Enhanced models for Onyx Phase 4 Trust Registry v1.

Provides comprehensive models for trust registry management, provider verification,
and trust signal generation with API-backed CRUD operations.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProviderType(str, Enum):
    """Types of providers in the trust registry."""
    PAYMENT_PROCESSOR = "payment_processor"
    CREDENTIAL_PROVIDER = "credential_provider"
    IDENTITY_VERIFIER = "identity_verifier"
    RISK_ASSESSOR = "risk_assessor"
    COMPLIANCE_MONITOR = "compliance_monitor"
    DATA_PROVIDER = "data_provider"


class ProviderStatus(str, Enum):
    """Status of providers in the trust registry."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"
    PENDING = "pending"
    UNDER_REVIEW = "under_review"


class TrustLevel(str, Enum):
    """Trust levels for providers."""
    CRITICAL = "critical"  # Highest trust - can handle sensitive operations
    HIGH = "high"          # High trust - can handle most operations
    MEDIUM = "medium"      # Medium trust - limited operations
    LOW = "low"           # Low trust - minimal operations
    UNTRUSTED = "untrusted"  # No trust - blocked


class ProviderCapability(str, Enum):
    """Capabilities that providers can offer."""
    PAYMENT_PROCESSING = "payment_processing"
    IDENTITY_VERIFICATION = "identity_verification"
    RISK_SCORING = "risk_scoring"
    FRAUD_DETECTION = "fraud_detection"
    COMPLIANCE_CHECKING = "compliance_checking"
    DATA_ANALYTICS = "data_analytics"
    KYB_VERIFICATION = "kyb_verification"
    AML_SCREENING = "aml_screening"


class TrustRegistryProvider(BaseModel):
    """Trust registry provider entry."""
    
    provider_id: str = Field(..., description="Unique provider identifier")
    provider_name: str = Field(..., description="Human-readable provider name")
    provider_type: ProviderType = Field(..., description="Type of provider")
    status: ProviderStatus = Field(default=ProviderStatus.PENDING, description="Current status")
    trust_level: TrustLevel = Field(..., description="Trust level assigned to provider")
    
    # Provider details
    organization: str = Field(..., description="Organization name")
    jurisdiction: str = Field(..., description="Legal jurisdiction")
    website: Optional[str] = Field(None, description="Provider website URL")
    contact_email: Optional[str] = Field(None, description="Contact email")
    
    # Capabilities
    capabilities: List[ProviderCapability] = Field(default_factory=list, description="Provider capabilities")
    supported_rails: List[str] = Field(default_factory=list, description="Supported payment rails")
    
    # Trust metrics
    trust_score: float = Field(0.0, ge=0.0, le=1.0, description="Current trust score")
    verification_status: str = Field("unverified", description="Verification status")
    compliance_status: str = Field("unknown", description="Compliance status")
    
    # Audit trail
    added_at: datetime = Field(default_factory=datetime.now, description="When provider was added")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    verified_at: Optional[datetime] = Field(None, description="When provider was verified")
    revoked_at: Optional[datetime] = Field(None, description="When provider was revoked")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional provider metadata")
    notes: Optional[str] = Field(None, description="Administrative notes")


class AddProviderRequest(BaseModel):
    """Request to add a new provider to the trust registry."""
    
    provider_id: str = Field(..., description="Unique provider identifier")
    provider_name: str = Field(..., description="Human-readable provider name")
    provider_type: ProviderType = Field(..., description="Type of provider")
    organization: str = Field(..., description="Organization name")
    jurisdiction: str = Field(..., description="Legal jurisdiction")
    website: Optional[str] = Field(None, description="Provider website URL")
    contact_email: Optional[str] = Field(None, description="Contact email")
    capabilities: List[ProviderCapability] = Field(default_factory=list, description="Provider capabilities")
    supported_rails: List[str] = Field(default_factory=list, description="Supported payment rails")
    initial_trust_level: TrustLevel = Field(default=TrustLevel.MEDIUM, description="Initial trust level")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    notes: Optional[str] = Field(None, description="Administrative notes")


class RevokeProviderRequest(BaseModel):
    """Request to revoke a provider from the trust registry."""
    
    provider_id: str = Field(..., description="Provider identifier to revoke")
    reason: str = Field(..., description="Reason for revocation")
    effective_date: Optional[datetime] = Field(None, description="When revocation takes effect")
    notes: Optional[str] = Field(None, description="Additional revocation notes")


class ListProvidersRequest(BaseModel):
    """Request to list providers from the trust registry."""
    
    status: Optional[ProviderStatus] = Field(None, description="Filter by status")
    provider_type: Optional[ProviderType] = Field(None, description="Filter by provider type")
    trust_level: Optional[TrustLevel] = Field(None, description="Filter by trust level")
    capability: Optional[ProviderCapability] = Field(None, description="Filter by capability")
    jurisdiction: Optional[str] = Field(None, description="Filter by jurisdiction")
    limit: int = Field(default=100, ge=1, le=1000, description="Maximum number of providers to return")
    offset: int = Field(default=0, ge=0, description="Number of providers to skip")


class ListProvidersResponse(BaseModel):
    """Response for listing providers from the trust registry."""
    
    providers: List[TrustRegistryProvider] = Field(..., description="List of providers")
    total_count: int = Field(..., description="Total number of providers matching filters")
    limit: int = Field(..., description="Limit applied to query")
    offset: int = Field(..., description="Offset applied to query")
    has_more: bool = Field(..., description="Whether there are more providers available")


class TrustSignalRequest(BaseModel):
    """Request for trust signal generation."""
    
    trace_id: str = Field(..., description="Transaction trace ID")
    provider_id: str = Field(..., description="Provider identifier to evaluate")
    rail_type: str = Field(..., description="Payment rail type")
    transaction_context: Dict[str, Any] = Field(default_factory=dict, description="Transaction context")
    user_context: Dict[str, Any] = Field(default_factory=dict, description="User context")
    merchant_context: Dict[str, Any] = Field(default_factory=dict, description="Merchant context")
    amount: Optional[float] = Field(None, description="Transaction amount")
    currency: str = Field(default="USD", description="Currency code")


class TrustSignalResponse(BaseModel):
    """Response for trust signal generation."""
    
    signal_id: str = Field(..., description="Unique trust signal identifier")
    trace_id: str = Field(..., description="Transaction trace ID")
    provider_id: str = Field(..., description="Provider identifier")
    rail_type: str = Field(..., description="Payment rail type")
    
    # Trust assessment
    trust_score: float = Field(..., ge=0.0, le=1.0, description="Trust score (0-1)")
    risk_level: str = Field(..., description="Risk level (low/medium/high/critical)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in assessment")
    
    # Rail preference adjustment
    original_rail_preference: float = Field(..., description="Original rail preference")
    adjusted_rail_preference: float = Field(..., description="Adjusted rail preference")
    preference_adjustment: float = Field(..., description="Preference adjustment amount")
    
    # Trust factors
    trust_factors: Dict[str, float] = Field(default_factory=dict, description="Individual trust factors")
    risk_factors: Dict[str, float] = Field(default_factory=dict, description="Individual risk factors")
    
    # Explanation
    explanation: str = Field(..., description="Human-readable explanation of trust assessment")
    recommendation: str = Field(..., description="Recommendation based on trust assessment")
    
    # Metadata
    generated_at: datetime = Field(default_factory=datetime.now, description="Signal generation timestamp")
    expires_at: Optional[datetime] = Field(None, description="Signal expiration timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional signal metadata")


class ProviderVerificationRequest(BaseModel):
    """Request to verify a provider's credentials and capabilities."""
    
    provider_id: str = Field(..., description="Provider identifier to verify")
    verification_type: str = Field(..., description="Type of verification to perform")
    verification_data: Dict[str, Any] = Field(..., description="Data required for verification")
    requested_capabilities: List[ProviderCapability] = Field(default_factory=list, description="Capabilities to verify")


class ProviderVerificationResponse(BaseModel):
    """Response for provider verification."""
    
    verification_id: str = Field(..., description="Unique verification identifier")
    provider_id: str = Field(..., description="Provider identifier")
    verification_type: str = Field(..., description="Type of verification performed")
    
    # Verification results
    verified: bool = Field(..., description="Whether verification was successful")
    verification_score: float = Field(0.0, ge=0.0, le=1.0, description="Verification score")
    verified_capabilities: List[ProviderCapability] = Field(default_factory=list, description="Verified capabilities")
    
    # Issues and notes
    issues: List[str] = Field(default_factory=list, description="Issues found during verification")
    notes: str = Field(..., description="Verification notes")
    
    # Audit trail
    verified_at: datetime = Field(default_factory=datetime.now, description="Verification timestamp")
    verified_by: str = Field(..., description="Who performed the verification")
    expires_at: Optional[datetime] = Field(None, description="Verification expiration")


class TrustRegistryStats(BaseModel):
    """Statistics about the trust registry."""
    
    total_providers: int = Field(..., description="Total number of providers")
    active_providers: int = Field(..., description="Number of active providers")
    suspended_providers: int = Field(..., description="Number of suspended providers")
    revoked_providers: int = Field(..., description="Number of revoked providers")
    
    # By type
    providers_by_type: Dict[str, int] = Field(default_factory=dict, description="Provider count by type")
    
    # By trust level
    providers_by_trust_level: Dict[str, int] = Field(default_factory=dict, description="Provider count by trust level")
    
    # By capability
    providers_by_capability: Dict[str, int] = Field(default_factory=dict, description="Provider count by capability")
    
    # By jurisdiction
    providers_by_jurisdiction: Dict[str, int] = Field(default_factory=dict, description="Provider count by jurisdiction")
    
    # Trust metrics
    average_trust_score: float = Field(..., description="Average trust score across all providers")
    high_trust_providers: int = Field(..., description="Number of high trust providers")
    low_trust_providers: int = Field(..., description="Number of low trust providers")
    
    # Timestamps
    generated_at: datetime = Field(default_factory=datetime.now, description="Stats generation timestamp")
    last_provider_added: Optional[datetime] = Field(None, description="When last provider was added")
    last_provider_verified: Optional[datetime] = Field(None, description="When last provider was verified")








