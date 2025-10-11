import pandas as pd
import re
from unidecode import unidecode

def _apply_to_selection(df, apply_to_headers_only, func):
    if apply_to_headers_only:
        # Convert index to series, apply function, and convert back to list
        df.columns = func(pd.Series(df.columns)).tolist()
    else:
        # Apply to all string columns in the dataframe
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = func(df[col])
    return df

def clean_data(df, options):
    """
    Applies a series of cleaning operations to a pandas DataFrame.
    """
    df_copy = df.copy()

    # Determine scope
    apply_to_headers_only = options.get('scope_headers_only', False)

    # Trim whitespace
    if options.get('trim_whitespace', False):
        df_copy = _apply_to_selection(df_copy, apply_to_headers_only, lambda s: s.str.strip())

    # Replace whitespace
    if 'whitespace_to' in options:
        replace_char = options['whitespace_to']
        df_copy = _apply_to_selection(df_copy, apply_to_headers_only, lambda s: s.str.replace(r'\s+', replace_char, regex=True))

    # Collapse repeats
    if options.get('collapse_repeats', False):
        df_copy = _apply_to_selection(df_copy, apply_to_headers_only, lambda s: s.str.replace(r'__+', '_', regex=True).str.replace(r'--+', '-', regex=True))

    # Remove invalid characters
    if options.get('remove_invalid_chars', False):
        allowed_chars = options.get('allowed_chars', '[A-Za-z0-9_ -]')
        remove_pattern = f'[^{allowed_chars.strip("[]")}]'
        df_copy = _apply_to_selection(df_copy, apply_to_headers_only, lambda s: s.str.replace(remove_pattern, '', regex=True))

    # Tidy punctuation
    if options.get('tidy_punctuation', False):
        df_copy = _apply_to_selection(df_copy, apply_to_headers_only, lambda s: s.str.strip('_-'))

    # Custom replace
    if options.get('custom_replace_from'):
        from_str = options['custom_replace_from']
        to_str = options.get('custom_replace_to', '')
        df_copy = _apply_to_selection(df_copy, apply_to_headers_only, lambda s: s.str.replace(from_str, to_str, regex=False))

    # Transliterate
    if options.get('transliterate', False):
        df_copy = _apply_to_selection(df_copy, apply_to_headers_only, lambda s: s.apply(unidecode))

    # Case conversion
    case_option = options.get('case_conversion')
    if case_option != 'none':
        if case_option == 'UPPERCASE':
            df_copy = _apply_to_selection(df_copy, apply_to_headers_only, lambda s: s.str.upper())
        elif case_option == 'lowercase':
            df_copy = _apply_to_selection(df_copy, apply_to_headers_only, lambda s: s.str.lower())
        elif case_option == 'TitleCase':
            df_copy = _apply_to_selection(df_copy, apply_to_headers_only, lambda s: s.str.title())

    # SQL-safe headers
    if options.get('sql_safe_headers', False):
        df_copy.columns = [sql_safe_identifier(col, options) for col in df_copy.columns]

    # Deduplicate headers
    if options.get('deduplicate_headers', False):
        df_copy.columns = deduplicate(df_copy.columns)

    # Handle null/empty headers
    new_cols = []
    i = 1
    for col in df_copy.columns:
        if col is None or str(col).strip() == '':
            new_cols.append(f'col_{i}')
            i += 1
        else:
            new_cols.append(col)
    df_copy.columns = new_cols


    return df_copy

def sql_safe_identifier(col_name, options=None):
    col_name = str(col_name)
    # Transliterate
    col_name = unidecode(col_name)
    # Replace whitespace with underscores
    col_name = re.sub(r'\s+', '_', col_name)
    # Remove invalid characters
    col_name = re.sub(r'[^A-Za-z0-9_]', '', col_name)
    # Collapse repeating underscores
    col_name = re.sub(r'__+', '_', col_name)
    # Remove leading/trailing underscores
    col_name = col_name.strip('_')
    # Prefix if starts with a digit
    if col_name and col_name[0].isdigit():
        col_name = 'c_' + col_name
    # Handle empty names
    if not col_name:
        return 'unnamed_col'
    # Max length
    return col_name[:63]

def deduplicate(columns):
    cols = pd.Series(columns)
    counts = cols.groupby(cols).cumcount()
    new_columns = [f"{col}_{count}" if count > 0 else col for col, count in zip(columns, counts)]
    return new_columns