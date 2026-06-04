"""ASSIGN RATE — RATE 부여

srp_intent: ASSIGN RATE
c_name_ko: RATE 부여

postcondition_predicate:
    'RATE' in df.columns and df['RATE'].apply(lambda x: x == 0 or x > 0 or x == -1 or x == -2).all()
    and (df.loc[df['RATE'] > 0, 'AMT'] > 0).all() if 'AMT' in df.columns else True
"""

import numpy as np
import pandas as pd


def assign_rate(df: pd.DataFrame, meta: dict | None = None) -> dict:
    df = df.copy()

    if "EVID" not in df.columns:
        return {"success": False, "df": df}

    df["RATE"] = 0.0

    if "rate_type" in df.columns:
        df.loc[df["rate_type"] == "model_rate", "RATE"] = -1.0
        df.loc[df["rate_type"] == "model_duration", "RATE"] = -2.0

    if "infusion_rate" in df.columns:
        inf_col = pd.to_numeric(df["infusion_rate"], errors="coerce")
        valid_inf = inf_col.notna() & (inf_col > 0)
        df.loc[valid_inf & (df["RATE"] == 0), "RATE"] = inf_col[valid_inf]

    if "AMT" in df.columns:
        bad = (df["RATE"] > 0) & (df["AMT"] <= 0)
        if bad.any():
            return {"success": False, "df": df}

    return {"success": True, "df": df}
