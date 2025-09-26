"""
Generates common SQL queries for data profiling and exploration.
"""

# These can be expanded with more complex/dialect-specific queries
QUERY_TEMPLATES = {
    # Table-level queries
    "view_all": "SELECT * FROM {table_name};",
    "count_total": "SELECT COUNT(*) AS total_rows FROM {table_name};",
    "preview_sample": "SELECT * FROM {table_name} LIMIT 10;",
    "random_sample": "SELECT * FROM {table_name} ORDER BY RANDOM() LIMIT 10;",

    # Column-level queries
    "unique_values": "SELECT DISTINCT {column_name} FROM {table_name};",
    "count_distinct": "SELECT COUNT(DISTINCT {column_name}) AS unique_count FROM {table_name};",
    "check_nulls": "SELECT COUNT(*) AS null_count FROM {table_name} WHERE {column_name} IS NULL;",
    "check_blanks": "SELECT COUNT(*) AS blank_count FROM {table_name} WHERE TRIM({column_name}) = '';",
    "min_max_values": "SELECT MIN({column_name}) AS min_val, MAX({column_name}) AS max_val FROM {table_name};",
    "basic_stats": "SELECT AVG({column_name}) AS avg_val, STDDEV({column_name}) AS std_val, SUM({column_name}) AS total_val FROM {table_name};",
    "value_frequency": "SELECT {column_name}, COUNT(*) AS freq FROM {table_name} GROUP BY {column_name} ORDER BY freq DESC;",
    "duplicate_check": "SELECT {column_name}, COUNT(*) AS dup_count FROM {table_name} GROUP BY {column_name} HAVING COUNT(*) > 1;",
    "top_n_by_column": "SELECT * FROM {table_name} ORDER BY {column_name} DESC LIMIT 5;"
}


def generate_queries(table_name: str, selected_queries: dict, all_columns: list) -> str:
    """
    Generates a string of SQL queries based on user selections.

    Args:
        table_name: The name of the table to query.
        selected_queries: A dictionary with query types as keys and boolean/list of columns as values.
                          e.g., {'table_level': ['view_all'], 'column_level': {'my_col': ['unique_values']}}
        all_columns: A list of all available column names in the table.

    Returns:
        A string containing all the generated SQL queries, one per line.
    """
    if not table_name:
        table_name = "your_table_name"

    output_queries = []

    # Generate table-level queries
    table_level_selections = selected_queries.get("table_level", [])
    for query_key in table_level_selections:
        if query_key in QUERY_TEMPLATES:
            output_queries.append(QUERY_TEMPLATES[query_key].format(table_name=table_name))

    # Generate column-level queries
    column_level_selections = selected_queries.get("column_level", {})
    for col_name, query_keys in column_level_selections.items():
        for query_key in query_keys:
            if query_key in QUERY_TEMPLATES:
                query = QUERY_TEMPLATES[query_key].format(table_name=table_name, column_name=col_name)
                output_queries.append(query)

    return "\n\n".join(output_queries)