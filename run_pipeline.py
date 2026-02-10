import os
import sys

# Add script directory and python_scripts to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_SCRIPTS_DIR = os.path.join(SCRIPT_DIR, "python_scripts")
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, PYTHON_SCRIPTS_DIR)

import json
import shutil
from datetime import datetime
import pandas as pd
from ai_parser import parse_request
from populate_column_id import populate_column_id

# =============================================================================
# CONFIGURATION
# =============================================================================
# SCRIPT_DIR is now the V1 folder (or columnsAI.pushbutton)
COLUMNS_FILE = os.path.join(SCRIPT_DIR, "columns.csv")
BACKUP_DIR = os.path.join(SCRIPT_DIR, "backups")
LOG_DIR = os.path.join(SCRIPT_DIR, "log")
PROMPT_FILE = os.path.join(SCRIPT_DIR, "user_input.txt")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)
if not os.path.exists(BACKUP_DIR):
    os.makedirs(BACKUP_DIR)

# =============================================================================
# LOGGING & BACKUP
# =============================================================================
def write_log(log_entry):
    log_filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
    log_path = os.path.join(LOG_DIR, log_filename)
    with open(log_path, "w") as f:
        json.dump(log_entry, f, indent=2)
    return log_path


def create_backup(file_path):
    """Create a timestamped backup of the columns file."""
    if not os.path.isfile(file_path):
        return None

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = "columns_backup_{}.csv".format(timestamp)
    backup_path = os.path.join(BACKUP_DIR, backup_filename)

    shutil.copy2(file_path, backup_path)
    print("Backup created: {}".format(backup_path))
    return backup_path

# =============================================================================
# FILTER LOGIC
# =============================================================================
def extract_level_number(level_str):
    """Extract numeric part from level string like 'L0', 'L1', '0', '1', etc."""
    s = str(level_str).strip().upper()
    if s.startswith("L"):
        return int(s[1:])
    return int(s)

def get_filter_mask(df, query):
    mask = pd.Series([True] * len(df), index=df.index)

    # Create numeric level column for comparisons
    df_level_num = df["base_level"].apply(extract_level_number)

    if "level" in query:
        level_val = str(query["level"]).strip()
        if level_val.startswith(">="):
            mask &= df_level_num >= int(level_val[2:])
        elif level_val.startswith(">"):
            mask &= df_level_num > int(level_val[1:])
        elif level_val.startswith("<="):
            mask &= df_level_num <= int(level_val[2:])
        elif level_val.startswith("<"):
            mask &= df_level_num < int(level_val[1:])
        elif "-" in level_val:
            parts = [p.strip() for p in level_val.split("-")]
            mask &= df_level_num >= int(parts[0])
            mask &= df_level_num <= int(parts[1])
        else:
            mask &= df_level_num == int(level_val)

    if "type" in query:
        mask &= df["column_type"] == query["type"]

    if "size" in query:
        mask &= df["size"] == query["size"]

    if "alpha" in query:
        alpha_val = str(query["alpha"]).strip()
        if "-" in alpha_val:
            lo, hi = [p.strip() for p in alpha_val.split("-")]
            mask &= df["alpha_grid"] >= lo
            mask &= df["alpha_grid"] <= hi
        else:
            mask &= df["alpha_grid"] == alpha_val

    if "numeric" in query:
        numeric_val = str(query["numeric"]).strip()
        if "-" in numeric_val:
            lo, hi = [p.strip() for p in numeric_val.split("-")]
            mask &= df["numeric_grid"] >= int(lo)
            mask &= df["numeric_grid"] <= int(hi)
        else:
            mask &= df["numeric_grid"] == int(numeric_val)

    return mask

# =============================================================================
# PIPELINE
# =============================================================================
def run_pipeline(user_text):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {
        "timestamp": timestamp,
        "input": user_text,
        "operations": [],
        "total_count": 0,
        "status": "started",
        "error": None,
    }

    try:
        if not os.path.isfile(COLUMNS_FILE):
            raise IOError("Columns CSV not found: {}".format(COLUMNS_FILE))

        # Create backup before processing
        backup_path = create_backup(COLUMNS_FILE)
        log_entry["backup_file"] = backup_path

        # Load CSV
        columns = pd.read_csv(COLUMNS_FILE)

        # Populate column_id before processing (ensures all existing columns have IDs)
        columns = populate_column_id(columns)
        log_entry["total_count"] = int(len(columns))

        # Parse request
        result = parse_request(user_text)
        log_entry["ai_response"] = result

        ops = result.get("operations", [])
        if not ops:
            raise RuntimeError("AI parsing produced no operations. Parser response: {}".format(result))

        columns["numeric_grid"] = pd.to_numeric(columns["numeric_grid"], errors="coerce")

        # Apply each operation
        for op in ops:
            query = op.get("query", {})
            change = op.get("change", {})

            mask = get_filter_mask(columns, query)
            filtered_count = int(mask.sum())

            op_log = {
                "query": query,
                "change": change,
                "matched_count": filtered_count,
            }

            # Apply changes
            if change:
                if "size" in change:
                    columns.loc[mask, "size"] = change["size"]
                if "type" in change:
                    columns.loc[mask, "column_type"] = change["type"]

            log_entry["operations"].append(op_log)

        # Populate column_id after processing (in case new columns were added)
        columns = populate_column_id(columns)

        # Save output (overwrites original file)
        columns.to_csv(COLUMNS_FILE, index=False)
        log_entry["status"] = "completed"
        print("Output saved to: {}".format(COLUMNS_FILE))
        print("Backup saved to: {}".format(backup_path))

    except Exception as e:
        log_entry["status"] = "failed"
        log_entry["error"] = str(e)
        print("Error: {}".format(e))

    finally:
        # Always write the log
        log_path = write_log(log_entry)
        print("Log saved to: {}".format(log_path))

    return COLUMNS_FILE


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    try:
        with open(PROMPT_FILE, "r") as f:
            user_input = f.read().strip()
        print("Prompt: {}\n".format(user_input))
        run_pipeline(user_input)
    except Exception as e:
        print("\nFATAL ERROR: {}".format(e))
        import traceback
        traceback.print_exc()
        sys.exit(1)
