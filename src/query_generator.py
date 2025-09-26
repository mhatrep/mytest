"""
Generates a standard set of SQL queries for data profiling.
"""

# A standard set of queries for profiling a table.
# Some queries are commented out as they are more advanced or require user input.
QUERY_TEMPLATES = {
    "table_level": [
        "-- Basic Exploration",
        "SELECT * FROM {table_name};",
        "SELECT COUNT(*) AS total_rows FROM {table_name};",
        "SELECT * FROM {table_name} LIMIT 10;",
    ],
    "column_level": [
        "\n-- Column-Level Checks for: {column_name}",
        "SELECT DISTINCT {column_name} FROM {table_name};",
        "SELECT COUNT(DISTINCT {column_name}) AS unique_count FROM {table_name};",
        "SELECT COUNT(*) AS null_count FROM {table_name} WHERE {column_name} IS NULL;",
        "SELECT COUNT(*) AS blank_count FROM {table_name} WHERE TRIM({column_name}) = '';",
        "\n-- Data Profiling for: {column_name}",
        "SELECT MIN({column_name}) AS min_val, MAX({column_name}) AS max_val FROM {table_name};",
        "SELECT AVG({column_name}) AS avg_val, STDDEV({column_name}) AS std_val, SUM({column_name}) AS total_val FROM {table_name}; -- (for numeric columns)",
        "SELECT {column_name}, COUNT(*) AS freq FROM {table_name} GROUP BY {column_name} ORDER BY freq DESC;",
        "\n-- Data Quality / Integrity for: {column_name}",
        "SELECT {column_name}, COUNT(*) AS dup_count FROM {table_name} GROUP BY {column_name} HAVING COUNT(*) > 1;",
        "\n-- Sampling & Debugging for: {column_name}",
        "SELECT * FROM {table_name} ORDER BY {column_name} DESC LIMIT 5;",
        "SELECT * FROM {table_name} ORDER BY RANDOM() LIMIT 10;"
    ]
}


def generate_queries(table_name: str, columns: list) -> str:
    """
    Generates a comprehensive string of SQL queries for a given table and columns.

    Args:
        table_name: The name of the table to query.
        columns: A list of all available column names in the table.

    Returns:
        A string containing all the generated SQL queries, one per line.
    """
    if not table_name:
        table_name = "your_table_name"

    output_queries = []

    # Generate table-level queries
    for query_template in QUERY_TEMPLATES["table_level"]:
        output_queries.append(query_template.format(table_name=table_name))

    # Generate column-level queries for each column
    for col_name in columns:
        for query_template in QUERY_TEMPLATES["column_level"]:
            # Basic check to avoid formatting comment lines that don't have placeholders
            if "{" in query_template:
                query = query_template.format(table_name=table_name, column_name=f'"{col_name}"')
            else:
                query = query_template
            output_queries.append(query)

    return "\n".join(output_queries)