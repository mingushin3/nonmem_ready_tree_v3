"""ASSIGN MDV — MDV 부여

srp_intent: ASSIGN MDV
c_name_ko: MDV 부여

postcondition_predicate:
    'MDV' in df.columns and df['MDV'].isin([0,1]).all()
    and (df.loc[df['EVID'].isin([1,2,3,4]), 'MDV'] == 1).all()
"""

import numpy as np
import pandas as pd

DOSE_EVIDS = [1, 2, 3, 4]


def assign_mdv(df: pd.DataFrame, meta: dict | None = None) -> dict:
    df = df.copy()

    if "EVID" not in df.columns:
        return {"success": False, "df": df}

    if df["EVID"].isna().any():
        return {"success": False, "df": df}

    df["MDV"] = np.where(
        df["EVID"].isin(DOSE_EVIDS), 1,
        np.where(df["dv_value"].notna(), 0, 1)
    ).astype(int)

    return {"success": True, "df": df}
