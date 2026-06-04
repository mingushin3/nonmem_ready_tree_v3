"""ASSIGN AMT — AMT 부여

srp_intent: ASSIGN AMT
c_name_ko: AMT 부여

postcondition_predicate:
    'AMT' in df.columns and (df.loc[df['EVID'].isin([1,3,4]), 'AMT'] > 0).all()
    and (df.loc[df['EVID'].isin([0,2]), 'AMT'] == 0).all()
"""

import numpy as np
import pandas as pd

DOSE_EVIDS = [1, 3, 4]
NON_DOSE_EVIDS = [0, 2]


def assign_amt(df: pd.DataFrame, meta: dict | None = None) -> dict:
    df = df.copy()

    if "EVID" not in df.columns or "dose_amount" not in df.columns:
        return {"success": False, "route_to_q": "Q08", "df": df,
                "failed_rows": list(df.index)}

    df["AMT"] = np.where(
        df["EVID"].isin(DOSE_EVIDS),
        pd.to_numeric(df["dose_amount"], errors="coerce").fillna(0),
        0.0,
    )

    dose_mask = df["EVID"].isin(DOSE_EVIDS)
    bad_dose = dose_mask & (df["AMT"] <= 0)
    if bad_dose.any():
        return {"success": False, "route_to_q": "Q08", "df": df,
                "failed_rows": df.index[bad_dose].tolist()}

    return {"success": True, "df": df}
