"""ASSIGN DV — DV 부여

srp_intent: ASSIGN DV
c_name_ko: DV 부여

postcondition_predicate:
    'DV' in df.columns and not ((df['EVID']==0) & (df['MDV']==0) & (df['DV'].isna())).any()
"""

import numpy as np
import pandas as pd


def assign_dv(df: pd.DataFrame, meta: dict | None = None) -> dict:
    df = df.copy()

    for col in ("EVID", "MDV", "dv_value"):
        if col not in df.columns:
            return {"success": False, "df": df}

    dv_num = pd.to_numeric(df["dv_value"], errors="coerce")
    df["DV"] = np.where(df["MDV"] == 0, dv_num, 0.0)

    # silent-error guard: 유효 obs(EVID=0,MDV=0)에 측정값 결측이면 DV=NaN → postcond 위반
    obs_missing = (df["EVID"] == 0) & (df["MDV"] == 0) & (df["DV"].isna())
    if obs_missing.any():
        return {"success": False, "df": df}

    return {"success": True, "df": df}
