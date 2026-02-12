@echo off

setlocal
set PYTHON=python
set PYTHON_310="C:\Program Files\Python310\python.exe"
set PYTHON_311="C:\Program Files\Python311\python.exe"
set PYTHON_312="C:\Program Files\Python312\python.exe"
set PYTHON_313="C:\Program Files\Python313\python.exe"
set PYTHON_314="C:\Program Files\Python314\python.exe"

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
if exist %PYTHON_310% %PYTHON_310% -m unittest discover tests
if errorlevel 1 goto error
if exist %PYTHON_311% %PYTHON_311% -m unittest discover tests
if errorlevel 1 goto error
if exist %PYTHON_312% %PYTHON_312% -m unittest discover tests
if errorlevel 1 goto error
if exist %PYTHON_313% %PYTHON_313% -m unittest discover tests
if errorlevel 1 goto error
if exist %PYTHON_314% %PYTHON_314% -m unittest discover tests
if errorlevel 1 goto error

goto EOF

:error
exit /b %errorlevel%

:EOF
