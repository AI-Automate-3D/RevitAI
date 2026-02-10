@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   ColumnsAI Installer
echo ============================================
echo.

REM --- Revit version ---
set /p REVIT_VERSION="Enter your Revit version (e.g. 2024): "
if "%REVIT_VERSION%"=="" (
    echo No version entered. Aborting.
    pause
    exit /b 1
)

REM --- Paths ---
set "INSTALL_DIR=%APPDATA%\ColumnsAI"
set "ADDIN_DIR=%APPDATA%\Autodesk\Revit\Addins\%REVIT_VERSION%"
set "SCRIPT_DIR=%~dp0"

echo.
echo Install directory : %INSTALL_DIR%
echo Addin manifest dir: %ADDIN_DIR%
echo.

REM --- Check that the DLL exists ---
set "DLL_PATH=%SCRIPT_DIR%ColumnsAI\bin\Release\ColumnsAI.dll"
if not exist "%DLL_PATH%" (
    echo ERROR: ColumnsAI.dll not found at:
    echo   %DLL_PATH%
    echo.
    echo Please build the solution first in Visual Studio:
    echo   Open ColumnsAI.sln ^> Build ^> Build Solution ^(Release^)
    echo.
    pause
    exit /b 1
)

REM --- Create directories ---
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%INSTALL_DIR%\python_scripts" mkdir "%INSTALL_DIR%\python_scripts"
if not exist "%INSTALL_DIR%\APIs" mkdir "%INSTALL_DIR%\APIs"
if not exist "%INSTALL_DIR%\backups" mkdir "%INSTALL_DIR%\backups"
if not exist "%INSTALL_DIR%\input_history" mkdir "%INSTALL_DIR%\input_history"
if not exist "%INSTALL_DIR%\log" mkdir "%INSTALL_DIR%\log"
if not exist "%ADDIN_DIR%" mkdir "%ADDIN_DIR%"

REM --- Copy files ---
echo Copying files...
copy /Y "%DLL_PATH%" "%INSTALL_DIR%\" >nul
copy /Y "%SCRIPT_DIR%run_pipeline.py" "%INSTALL_DIR%\" >nul
copy /Y "%SCRIPT_DIR%columns.csv" "%INSTALL_DIR%\" >nul
copy /Y "%SCRIPT_DIR%python_scripts\ai_parser.py" "%INSTALL_DIR%\python_scripts\" >nul
copy /Y "%SCRIPT_DIR%python_scripts\populate_column_id.py" "%INSTALL_DIR%\python_scripts\" >nul

REM --- Create .addin manifest with correct path ---
echo Creating Revit add-in manifest...
(
echo ^<?xml version="1.0" encoding="utf-8"?^>
echo ^<RevitAddIns^>
echo   ^<AddIn Type="Application"^>
echo     ^<Name^>ColumnsAI^</Name^>
echo     ^<Assembly^>%INSTALL_DIR%\ColumnsAI.dll^</Assembly^>
echo     ^<FullClassName^>ColumnsAI.App^</FullClassName^>
echo     ^<AddInId^>B5A7C9E1-3F42-4D6B-8E1A-2C4F6A8B0D3E^</AddInId^>
echo     ^<VendorId^>AI-Automate-3D^</VendorId^>
echo     ^<VendorDescription^>AI-Automate-3D - AI-powered Revit tools^</VendorDescription^>
echo   ^</AddIn^>
echo ^</RevitAddIns^>
) > "%ADDIN_DIR%\ColumnsAI.addin"

echo.
echo ============================================
echo   Installation complete!
echo ============================================
echo.
echo   Add-in manifest : %ADDIN_DIR%\ColumnsAI.addin
echo   Plugin files    : %INSTALL_DIR%\
echo.
echo   IMPORTANT: Place your OpenAI API key in:
echo     %INSTALL_DIR%\APIs\api_config.json
echo.
echo   File format:
echo     {"OPENAI_API_KEY": "sk-your-key-here"}
echo.
echo   Or set the OPENAI_API_KEY environment variable.
echo.
echo   Restart Revit to load the add-in.
echo.
pause
