# Changelog

All notable changes to this project will be documented in this file.

## v0.3.0 — Phase 3: Negotiation & Live Fee Bidding

### Added
- **Trust Signal Generation**: ML-powered trust scoring based on device reputation, velocity, IP risk, and history length
- **Rail Weight Adjustments**: Automatic adjustment of payment rail preferences based on risk level (high-risk → disfavor ACH)
- **CloudEvent Emission**: Emits `ocn.onyx.trust_signal.v1` events for audit and integration
- **LLM Explanations**: Optional LLM-powered explanations for trust decisions
- **MCP Integration**: `getTrustSignal` verb for Model Context Protocol
- **API Endpoints**: 
  - `POST /trust/signal` - Generate trust signal with ML scoring
  - `GET /trust/signal/status` - Service status and capabilities
  - `GET /trust/signal/sample-context` - Sample trust context for testing
- **Deterministic Scoring**: Consistent results with configurable seeds for testing
- **Comprehensive Tests**: 20+ test cases covering trust-influenced outcomes, rail adjustments, and CloudEvent validation

### Features
- Trust score calculation (0-1) with risk level classification (low/medium/high)
- Feature contribution analysis for explainability
- Rail-specific weight adjustments with reasoning
- CloudEvent validation and JSON schema
- Integration with existing KYB and trust registry functionality

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Phase 2 — Explainability scaffolding
- PR template for Phase 2 development

## [0.2.0] - 2025-01-25

### 🚀 Phase 2 Complete: KYB Verification & Explainability

This release completes Phase 2 development, delivering deterministic KYB (Know Your Business) verification, AI-powered trust decision explanations, and production-ready infrastructure for transparent business verification.

#### Highlights
- **Deterministic KYB Verification**: Rule-based verification with jurisdiction, age, sanctions, and business name validation
- **AI-Powered Trust Decisions**: Azure OpenAI integration for human-readable trust reasoning
- **CloudEvents Integration**: Complete CloudEvent emission for KYB verification with schema validation
- **Production Infrastructure**: Robust CI/CD workflows with security scanning
- **MCP Integration**: Enhanced Model Context Protocol verbs for explainability features

#### Core Features
- **KYB Verification Engine**: Deterministic business verification with comprehensive rule evaluation
- **Trust Registry**: Dynamic trust registry with credential provider validation and management
- **Decision Audit Trails**: Complete decision audit trails with explainable reasoning
- **API Endpoints**: RESTful endpoints for KYB verification and trust validation
- **Event Processing**: Advanced event handling and CloudEvent emission

#### Quality & Infrastructure
- **Test Coverage**: Comprehensive test suite with KYB verification and API validation
- **Security Hardening**: Enhanced security validation and risk assessment
- **CI/CD Pipeline**: Complete GitHub Actions workflow with security scanning
- **Documentation**: Comprehensive API and contract documentation

### Added
- Deterministic KYB verification with rule-based evaluation (jurisdiction, age, sanctions, business name)
- AI-powered trust decision explanations with Azure OpenAI integration
- LLM integration for human-readable trust reasoning
- Explainability API endpoints for trust validation
- Decision audit trail with explanations
- CloudEvents integration with ocn.onyx.kyb_verified.v1 schema
- Enhanced MCP verbs for explainability features
- Comprehensive trust registry functionality
- Advanced event processing capabilities
- Production-ready CI/CD infrastructure

### Changed
- Enhanced KYB verification with deterministic rule evaluation
- Improved trust registry with dynamic provider management
- Streamlined MCP integration for better explainability
- Optimized API performance and accuracy

### Deprecated
- None

### Removed
- None

### Fixed
- Resolved Bandit security issues (B101)
- Fixed mypy type checking issues in KYB implementation
- Resolved security workflow issues
- Enhanced error handling and validation

### Security
- Enhanced security validation for KYB verification
- Comprehensive risk assessment and mitigation
- Secure API endpoints with proper authentication
- Robust trust registry security measures

## [Unreleased] — Phase 2

### Added
- AI-powered trust decision explanations
- LLM integration for human-readable trust reasoning
- Explainability API endpoints for trust validation
- Decision audit trail with explanations
- Integration with Azure OpenAI for explanations
- Enhanced MCP verbs for explainability features

### Changed

### Deprecated

### Removed

### Fixed

### Security

## [0.1.0] - 2024-09-22

### Added
- Initial release
- Basic FastAPI application
- Health check endpoint
- Test suite
- CI/CD configuration
- Project documentation
