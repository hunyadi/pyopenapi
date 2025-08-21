@echo off

rem Run static type checker and verify formatting guidelines
python -m ruff check
if errorlevel 1 goto error
python -m ruff format --check
if errorlevel 1 goto error
python -m mypy pyopenapi
if errorlevel 1 goto error
python -m mypy tests
if errorlevel 1 goto error

rem Run unit tests
python -m unittest discover tests
if errorlevel 1 goto error

goto :EOF

:error
exit /b 1
