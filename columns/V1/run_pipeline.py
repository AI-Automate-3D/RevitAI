import os
import sys

# Add script directory to path so imports work when double-clicked
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

import json
from datetime import datetime
import pandas as pd
from ai_parser import parse_request

# =============================================================================
# CONFIGURATION
# =============================================================================
INPUT_FILE = os.path.join(SCRIPT_DIR, "02 - change column sizes", "step_2_in - columns.csv")
OUTPUT_FILE = os.path.join(SCRIPT_DIR, "output_columns.csv")
LOG_DIR = os.path.join(SCRIPT_DIR, "log")
PROMPT_FILE = os.path.join(SCRIPT_DIR, "01 - user prompt.txt")
os.makedirs(LOG_DIR, exist_ok=True)

# =============================================================================
# LOGGING
# =============================================================================
def write_log(log_entry):
    log_filename = datetime.now().strftime("%Y%m%d_%H%M%S") + ".json"
    log_path = os.path.join(LOG_DIR, log_filename)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log_entry, f, indent=2)
    return log_path

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
def run_pipeline(user_text: str) -> str:
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
        if not os.path.isfile(INPUT_FILE):
            raise FileNotFoundError(f"Input CSV not found: {INPUT_FILE}")

        # Parse request
        result = parse_request(user_text)
        log_entry["ai_response"] = result

        ops = result.get("operations", [])
        if not ops:
            raise RuntimeError(f"AI parsing produced no operations. Parser response: {result}")

        # Load CSV
        columns = pd.read_csv(INPUT_FILE)
        log_entry["total_count"] = int(len(columns))

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

        # Save output
        columns.to_csv(OUTPUT_FILE, index=False)
        log_entry["status"] = "completed"
        print(f"Output saved to: {OUTPUT_FILE}")

    except Exception as e:
        log_entry["status"] = "failed"
        log_entry["error"] = str(e)
        print(f"Error: {e}")

    finally:
        # Always write the log
        log_path = write_log(log_entry)
        print(f"Log saved to: {log_path}")

    return OUTPUT_FILE


# =============================================================================
# MAIN
# =============================================================================
if __name__ == "__main__":
    try:
        with open(PROMPT_FILE, "r", encoding="utf-8") as f:
            user_input = f.read().strip()
        print(f"Prompt: {user_input}\n")
        run_pipeline(user_input)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        input("\nPress Enter to exit...")
