# pyRevit script.py - ColumnsAI Chat Interface
# This script launches a chat window to get user input for column modifications,
# runs the AI pipeline, and archives the conversation history.

from pyrevit import revit, DB, forms
import os
import sys
import shutil
from datetime import datetime

# Get script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# File paths
USER_INPUT_FILE = os.path.join(SCRIPT_DIR, "user_input.txt")
INPUT_HISTORY_DIR = os.path.join(SCRIPT_DIR, "input_history")
RUN_PIPELINE_SCRIPT = os.path.join(SCRIPT_DIR, "run_pipeline.py")

# Ensure directories exist
os.makedirs(INPUT_HISTORY_DIR, exist_ok=True)


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
        with open(archive_path, "w", encoding="utf-8") as f:
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
        with open(USER_INPUT_FILE, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        forms.alert("Failed to save user input: {}".format(str(e)))
        return False


def clear_user_input():
    """Clear the user_input.txt file."""
    try:
        with open(USER_INPUT_FILE, "w", encoding="utf-8") as f:
            f.write("")
        return True
    except Exception as e:
        forms.alert("Failed to clear user input: {}".format(str(e)))
        return False


def run_pipeline():
    """
    Execute the run_pipeline.py script.

    Returns:
        True if successful, False otherwise
    """
    try:
        # Add script directory to Python path
        if SCRIPT_DIR not in sys.path:
            sys.path.insert(0, SCRIPT_DIR)

        # Import and run the pipeline
        import importlib
        import run_pipeline as pipeline_module

        # Reload the module to ensure fresh execution
        importlib.reload(pipeline_module)

        # Read the user input
        with open(USER_INPUT_FILE, "r", encoding="utf-8") as f:
            user_text = f.read().strip()

        if not user_text:
            forms.alert("No input to process!", exitscript=True)
            return False

        # Run the pipeline
        result = pipeline_module.run_pipeline(user_text)
        return True

    except Exception as e:
        forms.alert(
            "Pipeline execution failed!\n\nError: {}\n\nType: {}".format(
                str(e), type(e).__name__
            ),
            title="Pipeline Error"
        )
        import traceback
        print(traceback.format_exc())
        return False


# =============================================================================
# MAIN EXECUTION
# =============================================================================

try:
    # Show input dialog
    user_input = forms.ask_for_string(
        default="",
        prompt="Enter your column modification request:",
        title="ColumnsAI - Natural Language Input"
    )

    # Check if user cancelled
    if user_input is None:
        forms.alert("Operation cancelled.", exitscript=True)

    # Check if input is empty
    user_input = user_input.strip()
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

    # Run the AI pipeline
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

    # Show success message
    forms.alert(
        "Pipeline completed successfully!\n\nYour column modifications have been processed.",
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
