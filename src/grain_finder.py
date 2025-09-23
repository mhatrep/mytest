import pandas as pd
import itertools
from typing import List, Dict, Any, Tuple, Optional

def infer_grain_from_csv(
    csv_path: str,
    delimiter: str = ",",
    encoding: str = "utf-8",
    combo_max: int = 3,
    sample_rows: Optional[int] = None,
    normalize_whitespace: bool = True,
    lowercase_strings: bool = False,
    na_token: str = "<NULL>",
    drop_cols: Optional[List[str]] = None,
    dtype: str = "string"  # keeps values as strings for stable distinct counting
) -> Dict[str, Any]:
    """
    Infer table grain (minimal composite key(s)) by counting distinct values
    for every column and their combinations, similar to:
      SELECT COUNT(DISTINCT colA, colB, ...) ...

    Returns a dict with:
      - total_rows
      - per_column_distinct (dict)
      - candidate_grains (list of tuples of column names)
      - uniqueness_summary (DataFrame-like list of dicts)
    """

    # 1) Load
    df = pd.read_csv(
        csv_path,
        sep=delimiter,
        encoding=encoding,
        dtype=dtype,
        nrows=sample_rows
    )

    # Optional column drops
    if drop_cols:
        df = df.drop(columns=[c for c in drop_cols if c in df.columns], errors="ignore")

    # 2) Normalize values for stable distinct counting
    #    - Treat NaN explicitly via fillna(na_token)
    #    - Optional: trim whitespace, lowercase strings
    def _normalize_series(s: pd.Series) -> pd.Series:
        s = s.fillna(na_token).astype("string")
        if normalize_whitespace:
            s = s.str.strip()
        if lowercase_strings:
            s = s.str.lower()
        return s

    for c in df.columns:
        df[c] = _normalize_series(df[c])

    total_rows = len(df)

    # 3) Per-column distinct counts
    per_column_distinct = {c: int(df[c].nunique(dropna=False)) for c in df.columns}

    # 4) Build a compact “uniqueness summary” like your SQL example
    #    For all single columns, plus incremental combos up to combo_max
    rows_summary: List[Dict[str, Any]] = []
    # Singles
    for c in df.columns:
        rows_summary.append({
            "columns": (c,),
            "combo_size": 1,
            "distinct_count": per_column_distinct[c],
            "distinct_pct": per_column_distinct[c] / total_rows if total_rows else 0.0,
            "is_unique": per_column_distinct[c] == total_rows
        })

    # Combos (2..combo_max)
    def _combo_distinct(cols: Tuple[str, ...]) -> int:
        # Fast distinct on tuples of selected columns
        return int(df[list(cols)].drop_duplicates().shape[0])

    tested_combos = set()
    for k in range(2, min(combo_max, len(df.columns)) + 1):
        for cols in itertools.combinations(df.columns, k):
            if cols in tested_combos:
                continue
            tested_combos.add(cols)
            dcount = _combo_distinct(cols)
            rows_summary.append({
                "columns": cols,
                "combo_size": k,
                "distinct_count": dcount,
                "distinct_pct": dcount / total_rows if total_rows else 0.0,
                "is_unique": dcount == total_rows
            })

    # 5) Find minimal (by size) unique combos = candidate grains
    unique_combos = [r for r in rows_summary if r["is_unique"]]
    if unique_combos:
        min_size = min(r["combo_size"] for r in unique_combos)
        candidate_grains = sorted([tuple(r["columns"]) for r in unique_combos if r["combo_size"] == min_size])
    else:
        candidate_grains = []  # none found up to combo_max

    # 6) Prepare a friendly, ordered summary (singles first, then combos)
    def _fmt_cols(tup: Tuple[str, ...]) -> str:
        return ", ".join(tup)

    summary_table = sorted(
        [
            {
                "Columns": _fmt_cols(r["columns"]),
                "Size": r["combo_size"],
                "Distinct": r["distinct_count"],
                "Distinct %": round(r["distinct_pct"] * 100, 3),
                "Is Unique?": "YES" if r["is_unique"] else "NO"
            }
            for r in rows_summary
        ],
        key=lambda x: (x["Size"], -x["Distinct"])
    )

    result = {
        "total_rows": total_rows,
        "per_column_distinct": per_column_distinct,
        "candidate_grains": candidate_grains,
        "uniqueness_summary": summary_table
    }
    return result

# ---------- Example usage ----------
if __name__ == "__main__":
    # csv_path = "order_lines.csv"
    # res = infer_grain_from_csv(csv_path, combo_max=3)
    # print("Total rows:", res["total_rows"])
    # print("Per-column distinct:", res["per_column_distinct"])
    # print("Candidate grain(s):", res["candidate_grains"])
    # from pprint import pprint
    # pprint(res["uniqueness_summary"])
    pass
