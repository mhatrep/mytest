import pandas as pd
from typing import List, Dict, Any

def normalize_chunk(chunk: pd.DataFrame, config: dict) -> pd.DataFrame:
    """
    Applies normalization rules to a DataFrame chunk.
    - Fills NaNs
    - Strips whitespace
    - Lowercases (optional)
    """
    normalized_chunk = chunk.copy()
    for col in normalized_chunk.columns:
        # Convert all to string type for consistent processing
        series = normalized_chunk[col].fillna('').astype(str)

        # Strip leading/trailing whitespace
        series = series.str.strip()

        # Collapse multiple internal spaces to a single space
        series = series.str.replace(r'\s+', ' ', regex=True)

        # Lowercase if configured
        if config.get("case_insensitive", True):
            series = series.str.lower()

        normalized_chunk[col] = series

    return normalized_chunk

def update_profiles(profiles: Dict, chunk: pd.DataFrame, config: dict):
    """
    Updates column profiles with data from a new chunk.
    """
    null_markers_lower = [str(m).lower() for m in config.get("null_markers", [])]

    for col in chunk.columns:
        # Get the set of distinct values for the current column
        distinct_set = profiles[col]['distinct_values']

        # Update null count
        # A value is null if it's in the null markers list
        # Note: case_insensitive is handled during normalization
        null_mask = chunk[col].isin(null_markers_lower)
        profiles[col]['null_count'] += null_mask.sum()

        # Update distinct values, excluding nulls
        non_null_values = chunk[col][~null_mask]
        distinct_set.update(non_null_values)

def evaluate_uniqueness(profiles: Dict, total_rows: int, config: dict) -> List[Dict]:
    """
    Evaluates each column's profile to determine its quality as a key.
    """
    candidates = []
    if total_rows == 0:
        return []

    for col, profile in profiles.items():
        distinct_count = len(profile['distinct_values'])
        null_count = profile['null_count']

        # Uniqueness is calculated on non-null rows
        non_null_rows = total_rows - null_count

        if non_null_rows > 0:
            uniqueness_ratio = distinct_count / non_null_rows
        else:
            # If all rows are null, uniqueness is effectively 0
            uniqueness_ratio = 0.0

        null_rate = null_count / total_rows

        # Check against heuristics
        is_candidate = True
        notes = []
        if uniqueness_ratio != 1.0:
            is_candidate = False
            notes.append("Not 100% unique.")

        if null_rate > config.get("null_threshold", 0.0):
            is_candidate = False
            notes.append(f"Null rate ({null_rate:.2%}) exceeds threshold.")

        candidates.append({
            "column": col,
            "is_candidate": is_candidate,
            "uniqueness_ratio": uniqueness_ratio,
            "null_rate": null_rate,
            "distinct_count": distinct_count,
            "row_count": total_rows, # For context
            "notes": " | ".join(notes)
        })

    return candidates

def rank_candidates(candidates: List[Dict]) -> List[Dict]:
    """
    Ranks candidates based on specified heuristics.
    - Uniqueness ratio (descending)
    - Null rate (ascending)
    - Column name (lexical ascending)
    """
    return sorted(
        candidates,
        key=lambda c: (
            -c['uniqueness_ratio'], # Note the negative for descending sort
            c['null_rate'],
            c['column']
        )
    )

def detect_single_column_keys(
    csv_path: str,
    delimiter: str = ",",
    chunk_size: int = 10000, # Smaller chunk size for more responsive status updates
    null_threshold: float = 0.0,
    case_insensitive: bool = True
) -> Dict[str, Any]:
    """
    High-level orchestrator for detecting single-column primary key candidates.
    """
    config = {
        "case_insensitive": case_insensitive,
        "null_threshold": null_threshold,
        "null_markers": ["", "na", "n/a", "null"] # Already lowercased
    }

    # Initialize profiles for each column
    try:
        header = pd.read_csv(csv_path, sep=delimiter, nrows=0).columns.tolist()
    except Exception as e:
        raise ValueError(f"Could not read header from CSV: {e}")

    profiles = {col: {'distinct_values': set(), 'null_count': 0} for col in header}
    total_rows = 0

    # Read and process the CSV in chunks
    for chunk in pd.read_csv(
        csv_path,
        sep=delimiter,
        chunksize=chunk_size,
        dtype=str,
        keep_default_na=False # Important for custom null handling
    ):
        total_rows += len(chunk)
        normalized_chunk = normalize_chunk(chunk, config)
        update_profiles(profiles, normalized_chunk, config)
        # In a real UI, we would yield progress here
        # yield f"Processed {total_rows} rows..."

    # Final evaluation
    candidates = evaluate_uniqueness(profiles, total_rows, config)
    ranked_candidates = rank_candidates(candidates)

    return {
        "candidates": ranked_candidates,
        "total_rows": total_rows,
        "profiles": profiles # For later use
    }
