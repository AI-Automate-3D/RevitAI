"""
Utility to populate column_id field in columns dataframe.
column_id format: {alpha_grid}{numeric_grid}-{base_level}{top_level}
Example: A1-L0L1
"""
import pandas as pd


def populate_column_id(df):
    """
    Add or update column_id field in the dataframe.

    Args:
        df: pandas DataFrame with columns: alpha_grid, numeric_grid, base_level, top_level

    Returns:
        DataFrame with column_id populated
    """
    df["column_id"] = (
        df["alpha_grid"].astype(str)
        + df["numeric_grid"].astype(str)
        + "-"
        + df["base_level"].astype(str)
        + df["top_level"].astype(str)
    )
    return df


def populate_column_id_file(input_path, output_path=None):
    """
    Read CSV, populate column_id, and write back.

    Args:
        input_path: Path to input CSV file
        output_path: Path to output CSV file (if None, overwrites input)

    Returns:
        DataFrame with column_id populated
    """
    df = pd.read_csv(input_path)
    df = populate_column_id(df)

    output = output_path if output_path else input_path
    df.to_csv(output, index=False)

    return df


if __name__ == "__main__":
    # Standalone usage
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    v1_dir = os.path.dirname(script_dir)
    input_file = os.path.join(v1_dir, "columns.csv")

    df = populate_column_id_file(input_file)
    print(f"Populated column_id for {len(df)} rows")
    print(f"Updated: {input_file}")
