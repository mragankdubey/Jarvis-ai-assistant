@echo off
setlocal enabledelayedexpansion

echo ========================================================================
echo   J.A.R.V.I.S. - Windows Executable Build Pipeline (PyInstaller)
echo ========================================================================

set "ROOT=%~dp0"
cd /d "%ROOT%"

set "PYTHON_EXE=%ROOT%.venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" (
    echo [ERROR] Virtual environment Python not found at: %PYTHON_EXE%
    echo         Create it with: python -m venv .venv
    exit /b 1
)

echo [1/4] Verifying Python and PyInstaller environment...
"%PYTHON_EXE%" --version
if errorlevel 1 (
    echo [ERROR] Failed to execute %PYTHON_EXE%
    exit /b 1
)

"%PYTHON_EXE%" -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] PyInstaller not found in .venv. Installing PyInstaller...
    "%PYTHON_EXE%" -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERROR] Failed to install PyInstaller.
        exit /b 1
    )
)

echo [2/4] Verifying required icon and spec files...
if not exist "%ROOT%assets\icons\jarvis.ico" (
    echo [ERROR] Missing icon asset: assets\icons\jarvis.ico
    exit /b 1
)
if not exist "%ROOT%JARVIS.spec" (
    echo [ERROR] Missing spec file: JARVIS.spec
    exit /b 1
)

echo [3/4] Running PyInstaller ONEDIR build using JARVIS.spec...
"%PYTHON_EXE%" -m PyInstaller --noconfirm --clean "%ROOT%JARVIS.spec"
if errorlevel 1 (
    echo.
    echo [BUILD FAILED] PyInstaller encountered errors. See output above.
    exit /b 1
)

echo [4/4] Verifying build output...
if not exist "%ROOT%dist\JARVIS\JARVIS.exe" (
    echo [ERROR] Expected executable missing: dist\JARVIS\JARVIS.exe
    exit /b 1
)

echo.
echo ========================================================================
echo   BUILD SUCCEEDED!
echo   Output Executable: %ROOT%dist\JARVIS\JARVIS.exe
echo ========================================================================
exit /b 0
