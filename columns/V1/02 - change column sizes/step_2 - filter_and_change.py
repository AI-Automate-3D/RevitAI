import pandas as pd

columns = pd.read_csv("step_2_in - columns.csv")

# =============================================================================
# FILTER QUERY - Write your filter as a simple dictionary
# =============================================================================
# Examples:
#   "all columns above level 5"
#       query = {"level": ">5"}
#
#   "all columns that are RC"
#       query = {"type": "RC"}
#
#   "all columns above level 5 that are sized at 500x500"
#       query = {"level": ">5", "size": "500x500"}
#
#   "all columns between grids B and D, and above level 5"
#       query = {"alpha": "B-D", "level": ">5"}
#
#   "all columns between B and D and 2 and 4"
#       query = {"alpha": "B-D", "numeric": "2-4"}
#
#   "all columns at level 3"
#       query = {"level": "3"}
#
#   "all columns between levels 2 and 5"
#       query = {"level": "2-5"}
# =============================================================================

query = {}

# =============================================================================
# CHANGE VALUES - What to change on the filtered columns
# =============================================================================
# Examples:
#   "change to 400x400"
#       change = {"size": "400x400"}
#
#   "change to RC"
#       change = {"type": "RC"}
#
#   "change to 400x400 RC"
#       change = {"size": "400x400", "type": "RC"}
#
#   "change to 600x600 SC"
#       change = {"size": "600x600", "type": "SC"}
#
# Set to {} to not change anything (filter only)
# =============================================================================

change = {}

# =============================================================================
# FILTERING LOGIC - Do not modify below
# =============================================================================

def get_filter_mask(df, query):
    """Returns a boolean mask for rows matching the query"""
    mask = pd.Series([True] * len(df), index=df.index)

    # Parse and apply level filter
    if "level" in query:
        level_val = query["level"]
        if level_val.startswith(">="):
            mask &= df["base_level"] >= int(level_val[2:])
        elif level_val.startswith(">"):
            mask &= df["base_level"] > int(level_val[1:])
        elif level_val.startswith("<="):
            mask &= df["base_level"] <= int(level_val[2:])
        elif level_val.startswith("<"):
            mask &= df["base_level"] < int(level_val[1:])
        elif "-" in level_val:
            parts = level_val.split("-")
            mask &= df["base_level"] >= int(parts[0])
            mask &= df["base_level"] <= int(parts[1])
        else:
            mask &= df["base_level"] == int(level_val)

    # Parse and apply type filter
    if "type" in query:
        mask &= df["column_type"] == query["type"]

    # Parse and apply size filter
    if "size" in query:
        mask &= df["size"] == query["size"]

    # Parse and apply alpha grid filter
    if "alpha" in query:
        alpha_val = query["alpha"]
        if "-" in alpha_val:
            parts = alpha_val.split("-")
            mask &= df["alpha_grid"] >= parts[0]
            mask &= df["alpha_grid"] <= parts[1]
        else:
            mask &= df["alpha_grid"] == alpha_val

    # Parse and apply numeric grid filter
    if "numeric" in query:
        numeric_val = query["numeric"]
        if "-" in str(numeric_val):
            parts = str(numeric_val).split("-")
            mask &= df["numeric_grid"] >= int(parts[0])
            mask &= df["numeric_grid"] <= int(parts[1])
        else:
            mask &= df["numeric_grid"] == int(numeric_val)

    return mask

# Get the filter mask
mask = get_filter_mask(columns, query)
filtered_count = mask.sum()

print(f"Filtered {filtered_count} columns from {len(columns)} total")

# Apply changes if any
if change:
    if "size" in change:
        columns.loc[mask, "size"] = change["size"]
    if "type" in change:
        columns.loc[mask, "column_type"] = change["type"]
    print(f"Changed {filtered_count} columns: {change}")

# Show filtered results
print(columns[mask])

# Export full dataframe (with changes applied)
columns.to_csv("../output_columns.csv", index=False)
