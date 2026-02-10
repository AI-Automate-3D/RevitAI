@echo off
setlocal
echo ============================================
echo   ColumnsAI Build Script
echo ============================================
echo.

REM --- Build .NET Framework 4.8 (Revit 2019-2024) ---
echo [1/2] Building for .NET Framework 4.8 (Revit 2019-2024)...
dotnet build ColumnsAI\ColumnsAI.csproj -c Release -f net48
if errorlevel 1 (
    echo.
    echo WARNING: net48 build failed. Revit 2019-2024 DLL will not be available.
    echo          Make sure the .NET Framework 4.8 targeting pack is installed
    echo          and RevitInstallDir points to a valid Revit 2019-2024 folder.
    echo.
)

REM --- Build .NET 8 (Revit 2025-2027) ---
echo [2/2] Building for .NET 8.0 (Revit 2025-2027)...
dotnet build ColumnsAI\ColumnsAI.csproj -c Release -f net8.0-windows
if errorlevel 1 (
    echo.
    echo WARNING: net8.0-windows build failed. Revit 2025-2027 DLL will not be available.
    echo          Make sure the .NET 8 SDK is installed
    echo          and RevitInstallDir points to a valid Revit 2025+ folder.
    echo.
)

echo.
echo ============================================
echo   Build complete — check for warnings above
echo ============================================
echo.
echo   net48  DLL: ColumnsAI\bin\Release\net48\ColumnsAI.dll
echo   net8   DLL: ColumnsAI\bin\Release\net8.0-windows\ColumnsAI.dll
echo.
echo   To create the installer:
echo     1. Install Inno Setup 6+ from https://jrsoftware.org/isinfo.php
echo     2. Open Installer\ColumnsAI.iss in Inno Setup
echo     3. Compile (Ctrl+F9)
echo     4. The EXE will be at Installer\Output\ColumnsAI_Setup.exe
echo.
pause
