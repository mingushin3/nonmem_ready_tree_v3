"""ASSIGN ID — ID 정수화

srp_intent: ASSIGN ID
c_name_ko: ID 정수화

postcondition_predicate:
    'ID' in df.columns and (df['ID'] > 0).all() and df['ID'].apply(lambda x: isinstance(x, (int, np.integer))).all()
"""

import numpy as np
import pandas as pd


def assign_id(df: pd.DataFrame, meta: dict | None = None) -> dict:
    df = df.copy()

    if "subject_id" not in df.columns:
        return {"success": False, "df": df}

    if df["subject_id"].isna().any():
        return {"success": False, "df": df}

    # 혼합 dtype에서도 안정적인 정렬을 위해 문자열 키로 정렬
    uniq = sorted(df["subject_id"].unique(), key=str)
    id_map = {sid: i + 1 for i, sid in enumerate(uniq)}
    df["ID"] = df["subject_id"].map(id_map).astype(int)

    return {"success": True, "df": df}
