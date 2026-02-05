# pyRevit script.py - ColumnsAI Chat Interface
# This script launches a chat window to get user input for column modifications,
# runs the AI pipeline, and archives the conversation history.

from pyrevit import revit, DB, forms
import os
import sys
import shutil
import subprocess
from datetime import datetime

# Get script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# File paths
USER_INPUT_FILE = os.path.join(SCRIPT_DIR, "user_input.txt")
INPUT_HISTORY_DIR = os.path.join(SCRIPT_DIR, "input_history")
RUN_PIPELINE_SCRIPT = os.path.join(SCRIPT_DIR, "run_pipeline.py")
COLUMNS_CSV = os.path.join(SCRIPT_DIR, "columns.csv")
SYNC_SCRIPT = os.path.join(SCRIPT_DIR, "python_scripts", "columns.py")

# Ensure directories exist
if not os.path.exists(INPUT_HISTORY_DIR):
    os.makedirs(INPUT_HISTORY_DIR)


def archive_input(content):
    """
    Archive the user input to input_history folder with timestamp.

    Args:
        content: The user input text to archive

    Returns:
        Path to archived file
    """
    if not content or not content.strip():
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_filename = "input_{}.txt".format(timestamp)
    archive_path = os.path.join(INPUT_HISTORY_DIR, archive_filename)

    try:
        with open(archive_path, "w") as f:
            f.write(content)
        return archive_path
    except Exception as e:
        forms.alert("Failed to archive input: {}".format(str(e)))
        return None


def save_user_input(content):
    """
    Save user input to user_input.txt file.

    Args:
        content: The user input text

    Returns:
        True if successful, False otherwise
    """
    try:
        with open(USER_INPUT_FILE, "w") as f:
            f.write(content)
        return True
    except Exception as e:
        forms.alert("Failed to save user input: {}".format(str(e)))
        return False


def clear_user_input():
    """Clear the user_input.txt file."""
    try:
        with open(USER_INPUT_FILE, "w") as f:
            f.write("")
        return True
    except Exception as e:
        forms.alert("Failed to clear user input: {}".format(str(e)))
        return False


def run_pipeline():
    """
    Execute the run_pipeline.py script using external Python (not IronPython).

    Returns:
        True if successful, False otherwise
    """
    error_log = []

    try:
        error_log.append("Starting run_pipeline()")
        error_log.append("SCRIPT_DIR: {}".format(SCRIPT_DIR))
        error_log.append("RUN_PIPELINE_SCRIPT: {}".format(RUN_PIPELINE_SCRIPT))

        # Find Python executable
        python_exe = None

        # Try common Python locations (full paths first, then PATH)
        possible_pythons = [
            r"C:\Users\{}\AppData\Local\Programs\Python\Python313\python.exe".format(os.environ.get("USERNAME", "")),
            r"C:\Users\{}\AppData\Local\Programs\Python\Python312\python.exe".format(os.environ.get("USERNAME", "")),
            r"C:\Users\{}\AppData\Local\Programs\Python\Python311\python.exe".format(os.environ.get("USERNAME", "")),
            r"C:\Users\{}\AppData\Local\Programs\Python\Python310\python.exe".format(os.environ.get("USERNAME", "")),
            r"C:\Users\{}\AppData\Local\Programs\Python\Python39\python.exe".format(os.environ.get("USERNAME", "")),
            r"C:\Python313\python.exe",
            r"C:\Python312\python.exe",
            r"C:\Python311\python.exe",
            r"C:\Python310\python.exe",
            r"C:\Python39\python.exe",
            "python",  # System PATH (last resort)
            "python3",
        ]

        error_log.append("Searching for Python...")
        for py in possible_pythons:
            try:
                error_log.append("Trying: {}".format(py))
                # Check if file exists for full paths
                if py.startswith("C:") and not os.path.isfile(py):
                    error_log.append("Not found: {}".format(py))
                    continue

                # Test if this python works and has pandas
                test_result = subprocess.call(
                    [py, "-c", "import pandas"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False
                )
                if test_result == 0:
                    python_exe = py
                    error_log.append("Found Python with pandas: {}".format(py))
                    print("Found Python with pandas: {}".format(py))
                    break
                else:
                    error_log.append("Python found but pandas not available: {}".format(py))
            except Exception as e:
                error_log.append("Failed {}: {}".format(py, str(e)))
                continue

        if not python_exe:
            error_log.append("ERROR: No Python found!")
            forms.alert(
                "Could not find Python installation!\n\n"
                "Please install Python 3.9+ from python.org\n"
                "and make sure it's in your system PATH.",
                title="Python Not Found"
            )
            return False

        # Run the pipeline script with external Python
        error_log.append("Starting pipeline execution...")
        print("Running AI pipeline with external Python...")
        print("Python: {}".format(python_exe))
        print("Script: {}".format(RUN_PIPELINE_SCRIPT))

        process = subprocess.Popen(
            [python_exe, RUN_PIPELINE_SCRIPT],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=SCRIPT_DIR,
            shell=False
        )

        stdout, stderr = process.communicate()

        error_log.append("Pipeline completed with return code: {}".format(process.returncode))

        # Write debug log
        debug_log_path = os.path.join(SCRIPT_DIR, "debug_pipeline.log")
        try:
            with open(debug_log_path, "w") as f:
                f.write("=== Pipeline Execution Debug Log ===\n")
                f.write("Return code: {}\n\n".format(process.returncode))
                f.write("=== ERROR LOG ===\n")
                f.write("\n".join(error_log))
                f.write("\n\n=== STDOUT ===\n")
                f.write(stdout.decode('utf-8', errors='ignore'))
                f.write("\n\n=== STDERR ===\n")
                f.write(stderr.decode('utf-8', errors='ignore'))
            error_log.append("Debug log written to: {}".format(debug_log_path))
        except Exception as log_error:
            error_log.append("Failed to write debug log: {}".format(str(log_error)))

        # Print output
        if stdout:
            print("\n=== Pipeline Output ===")
            print(stdout.decode('utf-8', errors='ignore'))

        if stderr:
            print("\n=== Pipeline Errors ===")
            print(stderr.decode('utf-8', errors='ignore'))

        if process.returncode != 0:
            # Write error log before showing alert
            error_summary = "\n".join(error_log[-10:])
            forms.alert(
                "Pipeline failed with error code: {}\n\nLast 10 log entries:\n{}".format(
                    process.returncode, error_summary
                ),
                title="Pipeline Error"
            )
            return False

        return True

    except Exception as e:
        error_log.append("EXCEPTION: {}".format(str(e)))
        # Try to write error log
        try:
            debug_log_path = os.path.join(SCRIPT_DIR, "debug_pipeline.log")
            with open(debug_log_path, "w") as f:
                f.write("=== EXCEPTION LOG ===\n")
                f.write("\n".join(error_log))
        except:
            pass

        forms.alert(
            "Pipeline execution failed!\n\nError: {}\n\nType: {}\n\nLog:\n{}".format(
                str(e), type(e).__name__, "\n".join(error_log[-5:])
            ),
            title="Pipeline Error"
        )
        import traceback
        print(traceback.format_exc())
        return False


def sync_columns_with_revit():
    """
    Execute the columns.py script to sync the CSV with Revit.

    Returns:
        True if successful, False otherwise
    """
    try:
        if not os.path.isfile(COLUMNS_CSV):
            forms.alert(
                "Columns CSV not found!\n\nPath: {}".format(COLUMNS_CSV),
                title="File Not Found"
            )
            return False

        print("\nSyncing columns with Revit...")

        # Import and execute the columns sync script
        sys.path.insert(0, os.path.join(SCRIPT_DIR, "python_scripts"))

        # Read the columns.py script
        with open(SYNC_SCRIPT, "r") as f:
            code = f.read()

        # Replace the file picker line with our CSV path
        # Find: csv_path = forms.pick_file(file_ext="csv", title="Select columns CSV")
        # Replace with: csv_path = r"OUR_PATH"
        code = code.replace(
            'csv_path = forms.pick_file(file_ext="csv", title="Select columns CSV")',
            'csv_path = r"{}"'.format(COLUMNS_CSV)
        )

        # Execute in the current context with necessary imports
        exec_globals = {
            "__file__": SYNC_SCRIPT,
            "revit": revit,
            "DB": DB,
            "forms": forms
        }
        exec(code, exec_globals)

        return True

    except Exception as e:
        forms.alert(
            "Column sync failed!\n\nError: {}\n\nType: {}".format(
                str(e), type(e).__name__
            ),
            title="Sync Error"
        )
        import traceback
        print(traceback.format_exc())
        return False


# =============================================================================
# MAIN EXECUTION
# =============================================================================

try:
    # Create custom WPF dialog with larger text box
    import clr
    clr.AddReference('PresentationCore')
    clr.AddReference('PresentationFramework')
    clr.AddReference('WindowsBase')
    from System.Windows import Window, Thickness, TextWrapping, WindowStartupLocation
    from System.Windows.Controls import TextBox, Button, StackPanel, Label, ScrollBarVisibility

    class InputDialog(Window):
        def __init__(self):
            self.Title = "ColumnsAI - Natural Language Input"
            self.Width = 700
            self.Height = 400
            self.WindowStartupLocation = WindowStartupLocation.CenterScreen

            panel = StackPanel()
            panel.Margin = Thickness(20)

            # Label
            label = Label()
            label.Content = "Enter your column modification request:"
            label.FontSize = 14
            label.Margin = Thickness(0, 0, 0, 10)
            panel.Children.Add(label)

            # Text box
            self.textbox = TextBox()
            self.textbox.Height = 250
            self.textbox.TextWrapping = TextWrapping.Wrap
            self.textbox.AcceptsReturn = True
            self.textbox.VerticalScrollBarVisibility = ScrollBarVisibility.Auto
            self.textbox.FontSize = 12
            self.textbox.Margin = Thickness(0, 0, 0, 20)
            panel.Children.Add(self.textbox)

            # OK Button
            ok_btn = Button()
            ok_btn.Content = "OK"
            ok_btn.Height = 35
            ok_btn.FontSize = 14
            ok_btn.Click += self.ok_click
            panel.Children.Add(ok_btn)

            self.Content = panel
            self.user_input = None

        def ok_click(self, sender, e):
            self.user_input = self.textbox.Text
            self.Close()

    # Show dialog
    dialog = InputDialog()
    dialog.ShowDialog()

    user_input = dialog.user_input

    # Check if user cancelled
    if user_input is None:
        forms.alert("Operation cancelled.", exitscript=True)

    # Check if input is empty
    user_input = user_input.strip() if user_input else ""
    if not user_input:
        forms.alert("No input provided!", exitscript=True)

    # Show confirmation
    proceed = forms.alert(
        "You entered:\n\n\"{}\"\n\nProceed with processing?".format(user_input),
        title="Confirm Input",
        yes=True,
        no=True
    )

    if not proceed:
        forms.alert("Operation cancelled.", exitscript=True)

    # Save user input to file
    if not save_user_input(user_input):
        forms.alert("Failed to save input. Aborting.", exitscript=True)

    print("User input saved to: {}".format(USER_INPUT_FILE))

    # Run the AI pipeline (external Python)
    print("\nRunning AI pipeline...")
    if not run_pipeline():
        forms.alert("Pipeline execution failed. Check console for details.", exitscript=True)

    print("\nPipeline completed successfully!")

    # Archive the input
    archive_path = archive_input(user_input)
    if archive_path:
        print("Input archived to: {}".format(archive_path))

    # Clear user_input.txt
    if clear_user_input():
        print("user_input.txt cleared.")

    # Now sync the modified CSV with Revit
    print("\n" + "="*50)
    print("Syncing modified CSV with Revit...")
    print("="*50)

    if not sync_columns_with_revit():
        forms.alert("Column sync failed. Check console for details.", exitscript=True)

    # Show success message
    forms.alert(
        "ColumnsAI completed successfully!\n\nYour column modifications have been processed and synced with Revit.",
        title="Success"
    )

    print("\n" + "="*50)
    print("ColumnsAI execution complete!")
    print("="*50)

except Exception as e:
    forms.alert(
        "CRITICAL ERROR: {}\n\nType: {}".format(str(e), type(e).__name__),
        title="Script Failed"
    )
    import traceback
    print(traceback.format_exc())
