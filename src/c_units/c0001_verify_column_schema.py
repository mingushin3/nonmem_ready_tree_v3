"""VERIFY COLUMN_SCHEMA — L-2 컬럼 스키마 검증

postcondition_predicate:
    all(col in df.columns for col in ['subject_id', 'event_type', 'time_value', 'dv_value'])
    and df[['subject_id', 'event_type', 'time_value']].notna().all().all()
"""

import pandas as pd

REQUIRED_COLUMNS = ["subject_id", "event_type", "time_value", "dv_value"]
NOTNA_COLUMNS = ["subject_id", "event_type", "time_value"]


def verify_column_schema(df: pd.DataFrame, meta: dict | None = None) -> dict:
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return {"pass": False, "route_to": "INVALID", "missing_columns": missing}

    has_na = not df[NOTNA_COLUMNS].notna().all().all()
    if has_na:
        return {"pass": False, "route_to": "INVALID", "missing_columns": []}

    return {"pass": True, "route_to": "c0010", "missing_columns": []}
