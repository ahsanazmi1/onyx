# Onyx Trust Registry

Onyx is the Trust Registry and KYB (Know Your Business) service for the Open Checkout Network (OCN). It provides centralized trust management, business verification, and compliance checking capabilities for the OCN ecosystem. Onyx maintains allowlists and denylists, performs business verification checks, and provides APIs for trust verification across all OCN services.

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