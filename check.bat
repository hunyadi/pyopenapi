@echo off

setlocal
set PYTHON=python

rem Run static type checker and verify formatting guidelines
%PYTHON% -m ruff check
if errorlevel 1 goto error
%PYTHON% -m ruff format --check
if errorlevel 1 goto error
%PYTHON% -m mypy pyopenapi
if errorlevel 1 goto error
%PYTHON% -m mypy tests
if errorlevel 1 goto error

rem Run unit tests
%PYTHON% -m unittest discover tests
if errorlevel 1 goto error

goto EOF

:error
exit /b %errorlevel%

:EOF
