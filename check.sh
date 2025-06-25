set -e

PYTHON=python3

# Run static type checker and verify formatting guidelines
ruff check
ruff format --check
$PYTHON -m mypy pyopenapi
$PYTHON -m mypy tests
