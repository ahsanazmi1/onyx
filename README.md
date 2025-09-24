# Onyx Trust Registry

[![CI](https://github.com/ahsanazmi1/onyx/workflows/CI/badge.svg)](https://github.com/ahsanazmi1/onyx/actions/workflows/ci.yml)
[![Contracts](https://github.com/ahsanazmi1/onyx/workflows/Contracts/badge.svg)](https://github.com/ahsanazmi1/onyx/actions/workflows/contracts.yml)
[![Security](https://github.com/ahsanazmi1/onyx/workflows/Security/badge.svg)](https://github.com/ahsanazmi1/onyx/actions/workflows/security.yml)

**Onyx** is the **Trust Registry and KYB (Know Your Business) service** for the [Open Checkout Network (OCN)](https://github.com/ahsanazmi1/ocn-common).

## Phase 2 — Explainability

🚧 **Currently in development** - Phase 2 focuses on AI-powered explainability and human-readable trust decision reasoning.

- **Status**: Active development on `phase-2-explainability` branch
- **Features**: LLM integration, explainability API endpoints, decision audit trails
- **Issue Tracker**: [Phase 2 Issues](https://github.com/ahsanazmi1/onyx/issues?q=is%3Aopen+is%3Aissue+label%3Aphase-2)
- **Timeline**: Weeks 4-8 of OCN development roadmap

Onyx provides centralized trust management, business verification, and compliance checking capabilities for the OCN ecosystem. Onyx maintains allowlists and denylists, performs business verification checks, and provides APIs for trust verification across all OCN services.

## OCN Ecosystem

This service is part of the Open Checkout Network (OCN) - a decentralized payment infrastructure. Learn more about the OCN ecosystem:

- [OCN Common](https://github.com/ahsanazmi1/ocn-common) - Shared schemas and utilities
- [Orca](https://github.com/ahsanazmi1/orca) - Core decision engine
- [Weave](https://github.com/ahsanazmi1/weave) - Audit and treasury receipts
- [Okra](https://github.com/ahsanazmi1/okra) - Credit services
- [Opal](https://github.com/ahsanazmi1/opal) - Wallet and virtual cards

## Quickstart (≤ 60s)

Get up and running with Onyx Trust Registry in under a minute:

```bash
# Clone the repository
git clone https://github.com/ahsanazmi1/onyx.git
cd onyx

# Setup everything (venv, deps, pre-commit hooks)
make setup

# Run tests to verify everything works
make test

# Start the service
make run
```

**That's it!** 🎉

The service will be running at `http://localhost:8000`. Test the trust registry:

```bash
# List all trusted providers
curl http://localhost:8000/trust/providers

# Check if a provider is allowed
curl http://localhost:8000/trust/allowed/trusted_bank_001

# Health check
curl http://localhost:8000/health
```

### Additional Makefile Targets

```bash
make lint        # Run code quality checks
make fmt         # Format code with black/ruff
make clean       # Remove virtual environment and cache
make help        # Show all available targets
```

## Manual Setup (Alternative)

If you prefer manual setup over the Makefile:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run tests
pytest -q

# Start the service
uvicorn onyx.api:app --reload
```

## API Endpoints

### Core Endpoints
- `GET /health` - Health check endpoint

### Trust Registry v0
- `GET /trust/providers` - List all trusted credential providers
- `GET /trust/allowed/{provider_id}` - Check if a provider is allowed

### KYB (Know Your Business) Verification
- `POST /kyb/verify` - Perform KYB verification with deterministic rule-based checks

#### KYB Verification Request Example
```bash
curl -X POST http://localhost:8000/kyb/verify \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "business_001",
    "business_name": "Acme Corporation Ltd",
    "jurisdiction": "US",
    "entity_age_days": 1000,
    "registration_status": "active",
    "sanctions_flags": [],
    "business_type": "corporation",
    "registration_number": "12345678"
  }'
```

#### KYB Verification Response Example
```json
{
  "status": "verified",
  "checks": [
    {
      "check_name": "jurisdiction_verification",
      "status": "verified",
      "details": {
        "jurisdiction": "US",
        "whitelisted": true
      },
      "reason": "Jurisdiction US is whitelisted"
    },
    {
      "check_name": "entity_age_verification",
      "status": "verified",
      "details": {
        "entity_age_days": 1000,
        "minimum_required_days": 365,
        "meets_requirement": true
      },
      "reason": "Entity age 1000 days meets minimum requirement of 365 days"
    }
  ],
  "reason": "All verification checks passed successfully",
  "entity_id": "business_001",
  "verified_at": "2024-01-15T10:30:00Z",
  "metadata": {
    "verification_version": "1.0.0",
    "rules_applied": 5,
    "jurisdiction": "US",
    "entity_age_days": 1000
  }
}
```

#### CloudEvents Integration
Enable CloudEvents emission with the `emit_ce=true` query parameter:

```bash
curl -X POST "http://localhost:8000/kyb/verify?emit_ce=true" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "business_001",
    "business_name": "Acme Corporation Ltd",
    "jurisdiction": "US",
    "entity_age_days": 1000,
    "registration_status": "active",
    "sanctions_flags": [],
    "business_type": "corporation"
  }'
```

### MCP (Model Context Protocol)
- `POST /mcp/invoke` - MCP protocol endpoint for trust operations
  - `getStatus` - Get the current status of the Onyx agent
  - `isAllowedProvider` - Check if a provider is allowed in the trust registry
  - `verifyKYB` - Perform KYB verification with deterministic rule-based checks

## Trust Registry Configuration

The Trust Registry can be configured using a YAML file:

```bash
# Copy sample configuration
cp config/trust_registry.sample.yaml config/trust_registry.yaml

# Customize the provider allowlist
# Edit config/trust_registry.yaml to add your trusted providers
```

**Built-in Providers** (fallback when no config file):
- `trusted_bank_001`, `verified_credit_union_002`, `authorized_fintech_003`
- `certified_payment_processor_004`, `licensed_lender_005`

See [docs/trust_registry.md](docs/trust_registry.md) for detailed configuration guide.

## Development

This project uses:
- **FastAPI** for the web framework
- **pytest** for testing
- **ruff** and **black** for code formatting
- **mypy** for type checking

## License

MIT License - see [LICENSE](LICENSE) file for details.
