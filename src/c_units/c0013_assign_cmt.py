"""ASSIGN CMT — CMT 부여

srp_intent: ASSIGN CMT
c_name_ko: CMT 부여

postcondition_predicate:
    'CMT' in df.columns and (df.loc[df['EVID'].isin([0,1,3,4]), 'CMT'] > 0).all() and df['CMT'].apply(lambda x: isinstance(x, (int, np.integer)) and x > 0 if pd.notna(x) else True).all()
"""

import numpy as np
import pandas as pd

_SIMPLE_STATES = frozenset(["SINGLE-DRUG", "DDI-VICTIM-ONLY"])
_MAP_STATES = frozenset(["MULTI-CMT-DEFINED", "DDI-VICTIM-PERPETRATOR", "METABOLITE-DEFINED"])


def assign_cmt(df: pd.DataFrame, meta: dict) -> dict:
    df = df.copy()

    if "EVID" not in df.columns:
        return {"success": False, "route_to_q": "Q09", "df": df}

    a8_state = meta.get("a8_state")
    if a8_state is None or a8_state == "CMT-POLICY-MISSING":
        return {"success": False, "route_to_q": "Q09", "df": df}

    if a8_state in _SIMPLE_STATES:
        df["CMT"] = np.where(df["EVID"].isin([1, 2, 3, 4]), 1, 2).astype(int)
        return {"success": True, "df": df}

    if a8_state in _MAP_STATES:
        cmt_map = meta.get("cmt_map", {})
        if not cmt_map:
            return {"success": False, "route_to_q": "Q09", "df": df}

        def _row_cmt(row):
            analyte = row.get("analyte_label")
            if pd.isna(analyte):
                return np.nan
            analyte_entry = cmt_map.get(str(analyte).strip())
            if analyte_entry is None:
                return np.nan
            cat = "dose" if row["EVID"] in (1, 2, 3, 4) else "obs"
            val = analyte_entry.get(cat)
            return val if val is not None else np.nan

        df["CMT"] = df.apply(_row_cmt, axis=1)

        active = df["EVID"].isin([0, 1, 3, 4])
        if df.loc[active, "CMT"].isna().any():
            return {"success": False, "route_to_q": "Q09", "df": df}

        df["CMT"] = df["CMT"].astype(int)
        return {"success": True, "df": df}

    return {"success": False, "route_to_q": "Q09", "df": df}
