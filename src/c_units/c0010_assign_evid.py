"""ASSIGN EVID — EVID 부여

srp_intent: ASSIGN EVID
c_name_ko: EVID 부여

postcondition_predicate:
    'EVID' in df.columns and df['EVID'].isin([0,1,2,3,4]).all() and df['EVID'].notna().all()
"""

import pandas as pd

EVID_MAP = {"obs": 0, "dose": 1, "reset": 2, "reset_dose": 3, "ss_dose": 4}


def assign_evid(df: pd.DataFrame, meta: dict | None = None) -> dict:
    df = df.copy()

    if "event_type" not in df.columns:
        return {"success": False, "route_to_q": "Q04", "df": df,
                "failed_rows": list(df.index)}

    df["EVID"] = df["event_type"].map(EVID_MAP)

    unmapped = df["EVID"].isna()
    if unmapped.any():
        return {"success": False, "route_to_q": "Q04", "df": df,
                "failed_rows": df.index[unmapped].tolist()}

    df["EVID"] = df["EVID"].astype(int)
    return {"success": True, "df": df}
