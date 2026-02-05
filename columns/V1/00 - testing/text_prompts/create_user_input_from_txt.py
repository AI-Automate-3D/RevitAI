import os
import json
import re
import sys
import traceback
from datetime import datetime

# =============================================================================
# CONFIGURATION
# =============================================================================
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PROMPT_JSON = os.path.join(SCRIPT_DIR, "test_prompts.json")
LOG_DIR = os.path.join(SCRIPT_DIR, "log")
OUTPUT_FILENAME = "01 - user prompt.txt"

os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(
    LOG_DIR,
    f"create_user_input_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
)

def log(msg: str) -> None:
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{ts}] {msg}\n")

def resolve_txt_file() -> str:
    """
    Returns the absolute path to the txt file.
    Priority:
      1) argv[1] if provided
      2) the only .txt file in SCRIPT_DIR
    """
    if len(sys.argv) > 1 and sys.argv[1].strip():
        candidate = sys.argv[1].strip()
        txt_path = candidate if os.path.isabs(candidate) else os.path.join(SCRIPT_DIR, candidate)
        log(f"TXT filename provided via argument: {candidate}")
        return txt_path

    txt_files = [f for f in os.listdir(SCRIPT_DIR) if f.lower().endswith(".txt")]
    log(f"TXT files found in directory: {txt_files}")

    if len(txt_files) == 0:
        raise ValueError("No .txt file found in the script folder (and no filename argument provided).")
    if len(txt_files) > 1:
        raise ValueError(f"Multiple .txt files found in the script folder; cannot choose: {txt_files}")

    txt_path = os.path.join(SCRIPT_DIR, txt_files[0])
    log(f"Using detected TXT file: {txt_files[0]}")
    return txt_path

def extract_number_from_filename(txt_path: str) -> int:
    base = os.path.basename(txt_path)
    m = re.match(r"(\d+)\.txt$", base)
    if not m:
        raise ValueError(f"TXT filename must be numeric like 1.txt, 2.txt, etc. Got: {base}")
    return int(m.group(1))

def load_prompt_text(prompt_number: int) -> str:
    log(f"Loading prompt JSON: {PROMPT_JSON}")
    with open(PROMPT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    prompts = data.get("prompts", [])
    log(f"Loaded {len(prompts)} prompts from JSON")

    matched = next((p for p in prompts if p.get("number") == prompt_number), None)
    if not matched:
        raise ValueError(f"No prompt found in JSON for number {prompt_number}")

    if "example_prompt" not in matched:
        raise ValueError(f"Prompt #{prompt_number} missing 'example_prompt' field")

    return matched["example_prompt"]

def read_output_folder_from_txt(txt_path: str) -> str:
    with open(txt_path, "r", encoding="utf-8") as f:
        output_folder = f.read().strip()

    if not output_folder:
        raise ValueError("TXT file is empty; expected a path like ../../")

    # Keep relative paths relative; normalize separators.
    return os.path.normpath(output_folder)

def write_user_input_file(resolved_output_folder: str, prompt_text: str) -> str:
    output_file_path = os.path.join(resolved_output_folder, OUTPUT_FILENAME)
    with open(output_file_path, "w", encoding="utf-8") as f:
        f.write(prompt_text)
    return output_file_path

# =============================================================================
# MAIN
# =============================================================================
try:
    log("Script started")

    txt_path = resolve_txt_file()
    if not os.path.isfile(txt_path):
        raise FileNotFoundError(f"TXT file not found: {txt_path}")
    log(f"Resolved TXT path: {txt_path}")

    prompt_number = extract_number_from_filename(txt_path)
    log(f"Extracted prompt number: {prompt_number}")

    output_folder = read_output_folder_from_txt(txt_path)
    log(f"Output folder read from TXT (raw/normalized): {output_folder}")

    # Resolve output folder relative to script directory (so ../../ works as expected)
    resolved_output_folder = os.path.abspath(os.path.join(SCRIPT_DIR, output_folder))
    log(f"Resolved output folder absolute path: {resolved_output_folder}")

    if not os.path.isdir(resolved_output_folder):
        raise ValueError(f"Resolved output folder does not exist: {resolved_output_folder}")

    prompt_text = load_prompt_text(prompt_number)
    log(f"Matched prompt text: {prompt_text}")

    output_file_path = write_user_input_file(resolved_output_folder, prompt_text)
    log(f"Wrote user input file to: {output_file_path}")

    log("Script completed successfully")

    print(f"Created: {output_file_path}")
    print(f"output_folder = {resolved_output_folder}")

except Exception as e:
    log("ERROR occurred")
    log(str(e))
    log(traceback.format_exc())
    print("Script failed. Check log file for details.")
