# ColumnsAI - Standalone Revit Add-in

AI-powered structural column modifications for Autodesk Revit using natural language.

Supports **Revit 2019 through 2027**.

## Prerequisites

- **For end users:** Python 3.9+ with `pandas` and `openai` (`pip install pandas openai`)
- **For developers:** Visual Studio 2022+ and [Inno Setup 6+](https://jrsoftware.org/isinfo.php)
- An OpenAI API key

## Installing (end user)

1. Run `ColumnsAI_Setup.exe`.
2. Select the Revit versions you use.
3. After installation, create the file `C:\ProgramData\ColumnsAI\APIs\api_config.json`:
   ```json
   {"OPENAI_API_KEY": "sk-your-key-here"}
   ```
   Or set the `OPENAI_API_KEY` environment variable.
4. Restart Revit. A **ColumnsAI** tab will appear in the ribbon.

## Uninstalling

Use **Add or Remove Programs** in Windows Settings, or re-run the installer.

## Building the installer from source

1. Open `ColumnsAI.sln` in Visual Studio.
2. Check `RevitInstallDir` paths in `ColumnsAI\ColumnsAI.csproj` — they must point to local Revit installations (one for 2019-2024, one for 2025-2027).
3. Run `build.bat`, or build manually:
   ```
   dotnet build ColumnsAI\ColumnsAI.csproj -c Release -f net48
   dotnet build ColumnsAI\ColumnsAI.csproj -c Release -f net8.0-windows
   ```
4. Open `Installer\ColumnsAI.iss` in Inno Setup and compile (Ctrl+F9).
5. The installer EXE will be at `Installer\Output\ColumnsAI_Setup.exe`.

### Build targets

| Target              | Revit versions | Runtime            |
|---------------------|----------------|--------------------|
| `net48`             | 2019 – 2024    | .NET Framework 4.8 |
| `net8.0-windows`    | 2025 – 2027    | .NET 8             |

## Usage

1. Open a Revit project with structural columns, levels, and grids.
2. Go to the **ColumnsAI** ribbon tab and click **Columns AI**.
3. Type a natural language request describing the column changes you want.
4. Confirm. The AI pipeline parses your request, updates the CSV, and syncs changes into the Revit model.

## Project Structure

```
ColumnsAI.sln                 Visual Studio solution
ColumnsAI/                    C# source (Revit add-in)
  App.cs                        Ribbon tab + button setup
  ColumnsAICommand.cs           Main command (dialog -> pipeline -> sync)
  InputDialog.cs                WPF input dialog
  PipelineRunner.cs             External Python runner
  ColumnSyncer.cs               CSV-to-Revit sync (C# port of columns.py)
run_pipeline.py               AI pipeline orchestrator
columns.csv                   Column database
python_scripts/               Python helpers
  ai_parser.py                  OpenAI natural language parser
  populate_column_id.py         Column ID generator
Installer/
  ColumnsAI.iss                 Inno Setup script
build.bat                     Builds both targets
APIs/                         API config (api_config.json)
backups/                      Auto-created CSV backups
input_history/                Archived user inputs
```

## Test Prompts

### Prompt 1:

For all columns on gridlines B to E and 2 to 4, make those with base_level L0 to L4 600mm, base_level L5 to L7 450mm, and the levels above that should be 400mm

### Prompt 2:

For columns between L1 and L3, make them column type PT sq

### Prompt 3:

columns at gridline B to E and 2 to 4 need to get thinner at higher levels. Your sizing instructions are below

from L0 to L4 it should be column_type UC, size 356x406x634

from L5 to L7 it should be column_type UC, size 356x368x177

everything above that should be column_type UC, size 305x305x118

### Prompt 4:

make all of the columns column_type RC sq, size 500mm

### Prompt 5:

make all of the columns UC 356x368x177
