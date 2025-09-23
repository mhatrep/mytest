import json

def generate_recommendations(stats_json: str, filename: str) -> str:
    """
    Generates a data modeling recommendation report from csvstat JSON output.
    """
    try:
        stats = json.loads(stats_json)
    except json.JSONDecodeError:
        return "Error: Could not decode the statistics data."

    report = []
    report.append("Data Modeling Recommendation Report")
    report.append("=" * 35)
    report.append(f"File: {filename}\n")

    if not stats or not isinstance(stats, dict):
        report.append("No valid statistics were generated for this file.")
        return "\n".join(report)

    # Get row count, which should be consistent across all columns
    first_col_name = next(iter(stats), None)
    if not first_col_name:
        report.append("Statistics object is empty.")
        return "\n".join(report)
    row_count = stats[first_col_name].get('row_count', 0)
    report.append(f"Total Rows: {row_count}\n")

    for col_name, col_stats in stats.items():
        report.append(f"Column: {col_name}")
        report.append("-" * (len(col_name) + 8))

        col_type = col_stats.get('type')
        report.append(f"- Inferred Type: {col_type}")

        # Uniqueness Analysis
        unique_count = col_stats.get('unique', 0)
        if row_count > 0:
            uniqueness_pct = (unique_count / row_count) * 100
            report.append(f"- Uniqueness: {unique_count} unique values ({uniqueness_pct:.1f}%)")
            if uniqueness_pct == 100:
                report.append("    - RECOMMENDATION: This is a strong candidate for a PRIMARY KEY.")
            elif uniqueness_pct > 95:
                report.append("    - RECOMMENDATION: Very high uniqueness. Good candidate for a UNIQUE constraint.")
            else:
                report.append("    - RECOMMENDATION: Not unique. If a key is needed, consider a Surrogate Key.")

        # Nullability Analysis
        null_count = col_stats.get('null_count', 0)
        if row_count > 0:
            null_pct = (null_count / row_count) * 100
            report.append(f"- Nulls: {null_count} null values ({null_pct:.1f}%)")
            if null_pct == 0:
                report.append("    - RECOMMENDATION: This column can be marked as NOT NULL.")
            elif null_pct < 5:
                report.append("    - RECOMMENDATION: Very few nulls. Consider making it NOT NULL after data cleansing.")
            else:
                report.append("    - RECOMMENDATION: This column should be nullable.")

        # Cardinality Analysis
        if row_count > 0:
            cardinality_ratio = unique_count / row_count
            if cardinality_ratio > 0.5:
                report.append("- Cardinality: High")
                report.append("    - RECOMMENDATION: Keep as a fact-level attribute. Avoid using as a dimension key.")
            elif unique_count <= 1:
                 report.append("- Cardinality: No variation")
                 report.append("    - RECOMMENDATION: This column has no variation. It may be a constant value.")
            elif unique_count < 20: # Arbitrary threshold for "low"
                report.append("- Cardinality: Low")
                report.append("    - RECOMMENDATION: Good candidate for normalization into a lookup/dimension table.")
            else:
                report.append("- Cardinality: Medium")

        # Numeric Stats
        if col_type in ['int', 'float']:
            report.append("- Numeric Stats:")
            for key in ['min', 'max', 'mean', 'median', 'std_dev']:
                if key in col_stats:
                    report.append(f"    - {key.capitalize()}: {col_stats[key]}")

        report.append("") # Add a blank line for readability

    report.append("\n---")
    report.append("NOTE: This report is auto-generated. Cross-column relationships (Foreign Keys) require manual analysis.")

    return "\n".join(report)
