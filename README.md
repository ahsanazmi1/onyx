# Onyx Trust Registry

[![CI](https://github.com/ahsanazmi1/onyx/workflows/CI/badge.svg)](https://github.com/ahsanazmi1/onyx/actions/workflows/ci.yml)
[![Contracts](https://github.com/ahsanazmi1/onyx/workflows/Contracts/badge.svg)](https://github.com/ahsanazmi1/onyx/actions/workflows/contracts.yml)
[![Security](https://github.com/ahsanazmi1/onyx/workflows/Security/badge.svg)](https://github.com/ahsanazmi1/onyx/actions/workflows/security.yml)

Onyx is the Trust Registry and KYB (Know Your Business) service for the [Open Checkout Network (OCN)](https://github.com/ahsanazmi1/ocn-common). It provides centralized trust management, business verification, and compliance checking capabilities for the OCN ecosystem. Onyx maintains allowlists and denylists, performs business verification checks, and provides APIs for trust verification across all OCN services.

## OCN Ecosystem

This service is part of the Open Checkout Network (OCN) - a decentralized payment infrastructure. Learn more about the OCN ecosystem:

- [OCN Common](https://github.com/ahsanazmi1/ocn-common) - Shared schemas and utilities
- [Orca](https://github.com/ahsanazmi1/orca) - Core decision engine
- [Weave](https://github.com/ahsanazmi1/weave) - Audit and treasury receipts
- [Okra](https://github.com/ahsanazmi1/okra) - Credit services
- [Opal](https://github.com/ahsanazmi1/opal) - Wallet and virtual cards

## Quick Start

```bash
# Clone the repository
git clone https://github.com/ahsanazmi1/onyx.git
cd onyx

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest -q

# Start the service
uvicorn onyx.api:app --reload
```

## API Endpoints

- `GET /health` - Health check endpoint

## Development

This project uses:
- **FastAPI** for the web framework
- **pytest** for testing
- **ruff** and **black** for code formatting
- **mypy** for type checking

## License

MIT License - see [LICENSE](LICENSE) file for details.
