# ColumnsAI - Standalone Revit Add-in

AI-powered structural column modifications for Autodesk Revit using natural language.

## Prerequisites

- Autodesk Revit 2021-2024 (targets .NET Framework 4.8)
- Visual Studio 2019+ with .NET desktop development workload
- Python 3.9+ with `pandas` and `openai` packages
- An OpenAI API key

## Building

1. Open `ColumnsAI.sln` in Visual Studio.
2. If your Revit install is not at `C:\Program Files\Autodesk\Revit 2024`, edit the `RevitInstallDir` property in `ColumnsAI\ColumnsAI.csproj` to match your installation path.
3. Build in **Release** configuration: Build > Build Solution.

The DLL will be output to `ColumnsAI\bin\Release\ColumnsAI.dll`.

## Installing

1. Build the solution (see above).
2. Run `install.bat`.
3. Enter your Revit version when prompted (e.g. `2024`).
4. Place your OpenAI API key in `%APPDATA%\ColumnsAI\APIs\api_config.json`:
   ```json
   {"OPENAI_API_KEY": "sk-your-key-here"}
   ```
   Or set the `OPENAI_API_KEY` environment variable.
5. Restart Revit.

## Uninstalling

Run `uninstall.bat` and enter your Revit version.

## Usage

1. Open a Revit project with structural columns, levels, and grids.
2. Go to the **ColumnsAI** ribbon tab and click the **Columns AI** button.
3. Enter a natural language request describing the column modifications you want.
4. Confirm the input. The AI pipeline will parse your request and modify the columns CSV.
5. The modified CSV is automatically synced back into the Revit model.

## Project Structure

```
ColumnsAI.sln                 Visual Studio solution
ColumnsAI/                    C# source (Revit add-in)
  App.cs                      Ribbon tab and button setup
  ColumnsAICommand.cs         Main button command
  InputDialog.cs              WPF natural language input dialog
  PipelineRunner.cs           External Python executor
  ColumnSyncer.cs             CSV-to-Revit sync logic
run_pipeline.py               AI pipeline orchestrator
columns.csv                   Column database
python_scripts/               Python helpers
  ai_parser.py                OpenAI natural language parser
  populate_column_id.py       Column ID generator
APIs/                         API config directory
backups/                      Auto-created CSV backups
input_history/                Archived user inputs
ColumnsAI.addin               Revit manifest template
install.bat                   Installer
uninstall.bat                 Uninstaller
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
