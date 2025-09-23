# Makefile for Onyx Trust Registry
# Provides common development targets for setup, testing, and running

.PHONY: help setup lint fmt test run clean install-dev install-precommit

# Default target
help:
	@echo "Available targets:"
	@echo "  setup       - Create venv, install deps + dev extras, install pre-commit hooks"
	@echo "  lint        - Run ruff + black checks"
	@echo "  fmt         - Format code with black"
	@echo "  test        - Run pytest with coverage"
	@echo "  run         - Start FastAPI application with uvicorn"
	@echo "  clean       - Remove virtual environment and cache files"
	@echo "  install-dev - Install development dependencies"
	@echo "  install-precommit - Install pre-commit hooks"

# Setup target - create venv, install deps, install pre-commit hooks
setup: install-dev install-precommit
	@echo "✅ Setup complete! Virtual environment created and dependencies installed."
	@echo "💡 Run 'make test' to verify everything works."

# Install development dependencies
install-dev:
	@echo "📦 Installing development dependencies..."
	python -m venv .venv
	.venv/bin/python -m pip install --upgrade pip
	.venv/bin/pip install -e ".[dev]"
	@echo "✅ Development dependencies installed."

# Install pre-commit hooks
install-precommit:
	@echo "🔧 Installing pre-commit hooks..."
	.venv/bin/pip install pre-commit
	.venv/bin/pre-commit install
	@echo "✅ Pre-commit hooks installed."

# Lint target - run ruff and black checks
lint:
	@echo "🔍 Running linting checks..."
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .
	@echo "✅ Linting checks passed."

# Format target - format code with black
fmt:
	@echo "🎨 Formatting code..."
	.venv/bin/black .
	.venv/bin/ruff format .
	@echo "✅ Code formatted."

# Test target - run pytest with coverage
test:
	@echo "🧪 Running tests with coverage..."
	.venv/bin/pytest --cov=src/onyx --cov-report=term-missing --cov-report=html
	@echo "✅ Tests completed."

# Run target - start FastAPI application
run:
	@echo "🚀 Starting Onyx Trust Registry service..."
	@if [ -f "src/onyx/api.py" ]; then \
		.venv/bin/uvicorn onyx.api:app --reload --host 0.0.0.0 --port 8000; \
	else \
		echo "❌ Error: src/onyx/api.py not found. Cannot start FastAPI application."; \
		exit 1; \
	fi

# Clean target - remove virtual environment and cache files
clean:
	@echo "🧹 Cleaning up..."
	rm -rf .venv
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf .ruff_cache
	rm -rf __pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Cleanup complete."

# Development workflow targets
dev-setup: setup
	@echo "🎯 Development setup complete!"
	@echo "Next steps:"
	@echo "  1. make test    # Run tests"
	@echo "  2. make run     # Start the service"
	@echo "  3. make lint    # Check code quality"

# CI/CD targets
ci-lint: install-dev
	.venv/bin/ruff check .
	.venv/bin/ruff format --check .
	.venv/bin/black --check .

ci-test: install-dev
	.venv/bin/pytest --cov=src/onyx --cov-report=xml --cov-fail-under=80

# Quick development targets
quick-test: install-dev
	.venv/bin/pytest -q

quick-lint: install-dev
	.venv/bin/ruff check . --fix
	.venv/bin/black .

# Show project info
info:
	@echo "📋 Onyx Trust Registry Project Info:"
	@echo "  Python version: $(shell .venv/bin/python --version 2>/dev/null || echo 'Not installed')"
	@echo "  Virtual env: $(shell [ -d .venv ] && echo '✅ Active' || echo '❌ Not found')"
	@echo "  Pre-commit: $(shell [ -f .git/hooks/pre-commit ] && echo '✅ Installed' || echo '❌ Not installed')"
	@echo "  FastAPI app: $(shell [ -f src/onyx/api.py ] && echo '✅ Found' || echo '❌ Not found')"
	@echo "  Trust registry: $(shell [ -f src/onyx/trust_registry.py ] && echo '✅ Found' || echo '❌ Not found')"

# Check if all required files exist
check-files:
	@echo "📁 Checking required files..."
	@for file in src/onyx/api.py src/onyx/trust_registry.py pyproject.toml README.md; do \
		if [ -f "$$file" ]; then \
			echo "  ✅ $$file"; \
		else \
			echo "  ❌ $$file (missing)"; \
		fi; \
	done
