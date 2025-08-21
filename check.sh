set -e

PYTHON_EXECUTABLE=${PYTHON:-python3}

# Run static type checker and verify formatting guidelines
$PYTHON_EXECUTABLE -m ruff check
$PYTHON_EXECUTABLE -m ruff format --check
$PYTHON_EXECUTABLE -m mypy pyopenapi
$PYTHON_EXECUTABLE -m mypy tests

# Run unit tests
$PYTHON_EXECUTABLE -m unittest discover tests
