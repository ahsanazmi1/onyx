# Contributing to Onyx

Thank you for your interest in contributing to Onyx! This document provides guidelines and information for contributors.

## Development Setup

1. **Fork and clone the repository**
   ```bash
   git clone https://github.com/ahsanazmi1/onyx.git
   cd onyx
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Run tests to verify setup**
   ```bash
   pytest -q
   ```

## Code Style

This project uses several tools to maintain code quality:

- **ruff**: Fast Python linter and formatter
- **black**: Code formatter
- **mypy**: Static type checker

Run all checks:
```bash
ruff check .
black .
mypy .
```

## Testing

- Write tests for all new functionality
- Ensure tests pass: `pytest`
- Maintain test coverage above 80%
- Use descriptive test names and docstrings

## Pull Request Process

1. Create a feature branch from `phase-1-foundations`
2. Make your changes with appropriate tests
3. Ensure all CI checks pass
4. Submit a pull request with a clear description
5. Request review from maintainers

## Commit Messages

Use clear, descriptive commit messages following conventional commits:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test additions/changes
- `refactor:` for code refactoring

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

## Questions?

Feel free to open an issue for questions or discussions.
