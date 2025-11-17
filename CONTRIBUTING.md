# Contributing to LDAP Health Monitor

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/ldap-health-monitor.git`
3. Create a branch: `git checkout -b feature/your-feature`
4. Make your changes
5. Run tests: `pytest`
6. Commit your changes: `git commit -am 'Add new feature'`
7. Push to your fork: `git push origin feature/your-feature`
8. Create a Pull Request

## Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Code Style

- Follow PEP 8
- Use type hints
- Write docstrings (Google style)
- Run black: `black src/`
- Run ruff: `ruff check src/`
- Run mypy: `mypy src/`

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_connector.py
```

## Documentation

- Update README.md if adding features
- Add docstrings to all functions/classes
- Update relevant docs in docs/ folder

## Pull Request Process

1. Update the README.md with details of changes if applicable
2. Update the documentation
3. Add tests for new features
4. Ensure all tests pass
5. Update the CHANGELOG.md

## Code Review

All submissions require review. We use GitHub pull requests for this purpose.

## Questions?

Open an issue or contact the maintainers.

Thank you for contributing!
