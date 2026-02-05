"""
DEPRECATED: This script is kept for reference only.
Use ../populate_column_id.py instead, which is now integrated into run_pipeline.py
"""
import pandas as pd

columns = pd.read_csv("original_columns.csv")

columns["column_id"] = (
    columns["alpha_grid"].astype(str)
    + columns["numeric_grid"].astype(str)
    + "-"
    + columns["base_level"].astype(str)
    + columns["top_level"].astype(str)
)

# Updated to use new columns.csv location
columns.to_csv("../columns.csv", index=False)
print("Note: This script is deprecated. Use ../populate_column_id.py instead.")
