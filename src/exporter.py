import pandas as pd
import os

def export_unique_values(df: pd.DataFrame, base_path: str, options: dict):
    """
    Extracts unique values and their frequencies from each column of a DataFrame
    and saves them to separate text files in a specified directory.

    Args:
        df (pd.DataFrame): The DataFrame to process.
        base_path (str): The base path for the output directory.
        options (dict): A dictionary with processing options:
                        'case_sensitive': bool
                        'include_frequency': bool
                        'sort_by': str
    """
    # Create the directory
    if not os.path.exists(base_path):
        os.makedirs(base_path)

    for column in df.columns:
        # Sanitize column name for use as a filename
        safe_col_name = "".join(c for c in column if c.isalnum() or c in (' ', '_')).rstrip()
        output_filename = os.path.join(base_path, f"{safe_col_name}.txt")

        # --- Core Logic Update ---
        # 1. Treat all data as strings, filling NaNs with a placeholder
        series = df[column].fillna('nan').astype(str)

        # 2. Handle case sensitivity
        if not options['case_sensitive']:
            # Group by lower case but keep original values
            # The first occurrence of a case variation is kept
            value_groups = series.groupby(series.str.lower())
            series = value_groups.first()
            # Recalculate frequencies after grouping
            frequencies = value_groups.size()
        else:
            frequencies = series.value_counts()

        # Create a DataFrame from the results
        result_df = pd.DataFrame({'value': series.unique()})
        result_df['frequency'] = result_df['value'].map(frequencies)

        # 3. Sort the results
        if options['sort_by'] == "Alphabetical (A-Z)":
            result_df = result_df.sort_values(by='value', ascending=True)
        else: # Frequency (High to Low)
            result_df = result_df.sort_values(by=['frequency', 'value'], ascending=[False, True])

        # 4. Save to file
        with open(output_filename, 'w', encoding='utf-8') as f:
            if options['include_frequency']:
                # Write header
                f.write(f"{'Value':<40} | {'Frequency'}\n")
                f.write(f"{'-'*40} | {'-'*10}\n")
                for _, row in result_df.iterrows():
                    f.write(f"{str(row['value']):<40} | {row['frequency']}\n")
            else:
                for _, row in result_df.iterrows():
                    f.write(f"{row['value']}\n")

    return f"Successfully exported unique values to the '{os.path.basename(base_path)}' directory."
