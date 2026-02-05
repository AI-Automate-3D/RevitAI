import pandas as pd

columns = pd.read_csv("original_columns.csv")

columns["column_id"] = (
    columns["alpha_grid"].astype(str)
    + columns["numeric_grid"].astype(str)
    + "-"
    + columns["base_level"].astype(str)
    + columns["top_level"].astype(str)
)

columns.to_csv("../02 - change column sizes/step_2_in - columns.csv", index=False)
