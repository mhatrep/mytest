import pandas as pd
import os

def export_unique_values(df: pd.DataFrame, base_path: str, case_sensitive: bool):
    """
    Extracts unique values from each column of a DataFrame and saves them
    to separate text files in a specified directory.

    Args:
        df (pd.DataFrame): The DataFrame to process.
        base_path (str): The base path for the output directory. The directory
                         will be named after this path.
        case_sensitive (bool): Whether the uniqueness check is case-sensitive.
    """
    # Create the directory
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    for column in df.columns:
        # Sanitize column name for use as a filename
        safe_col_name = "".join(c for c in column if c.isalnum() or c in (' ', '_')).rstrip()
        output_filename = os.path.join(base_path, f"{safe_col_name}.txt")

        # Get unique values
        if case_sensitive:
            unique_values = df[column].dropna().unique()
        else:
            # For case-insensitive, convert to string and then to lower case
            unique_values = df[column].dropna().astype(str).str.lower().unique()

        # Save to file
        with open(output_filename, 'w', encoding='utf-8') as f:
            for value in sorted(unique_values):
                f.write(f"{value}\n")

    return f"Successfully exported unique values to the '{os.path.basename(base_path)}' directory."
