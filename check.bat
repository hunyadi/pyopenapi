@echo off

rem Run static type checker and verify formatting guidelines
ruff check
if errorlevel 1 goto error
ruff format --check
if errorlevel 1 goto error
python -m mypy pyopenapi
if errorlevel 1 goto error
python -m mypy tests
if errorlevel 1 goto error

goto :EOF

:error
exit /b 1
