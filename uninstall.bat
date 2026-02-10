@echo off
setlocal enabledelayedexpansion

echo ============================================
echo   ColumnsAI Uninstaller
echo ============================================
echo.

set /p REVIT_VERSION="Enter your Revit version (e.g. 2024): "
if "%REVIT_VERSION%"=="" (
    echo No version entered. Aborting.
    pause
    exit /b 1
)

set "INSTALL_DIR=%APPDATA%\ColumnsAI"
set "ADDIN_FILE=%APPDATA%\Autodesk\Revit\Addins\%REVIT_VERSION%\ColumnsAI.addin"

echo.
echo This will remove:
echo   %ADDIN_FILE%
echo   %INSTALL_DIR%
echo.
set /p CONFIRM="Are you sure? (Y/N): "
if /i not "%CONFIRM%"=="Y" (
    echo Cancelled.
    pause
    exit /b 0
)

REM --- Remove .addin manifest ---
if exist "%ADDIN_FILE%" (
    del "%ADDIN_FILE%"
    echo Removed: %ADDIN_FILE%
)

REM --- Remove install directory ---
if exist "%INSTALL_DIR%" (
    rmdir /s /q "%INSTALL_DIR%"
    echo Removed: %INSTALL_DIR%
)

echo.
echo ============================================
echo   Uninstall complete!
echo ============================================
echo.
echo   Restart Revit to fully unload the add-in.
echo.
pause
