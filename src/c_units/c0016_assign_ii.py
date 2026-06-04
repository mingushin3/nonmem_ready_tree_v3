"""ASSIGN II — II 부여

srp_intent: ASSIGN II
c_name_ko: II 부여

postcondition_predicate:
    'II' in df.columns and (df.loc[df['ADDL'] > 0, 'II'] > 0).all() and (df.loc[df['ADDL'] == 0, 'II'] == 0).all()
"""

import numpy as np
import pandas as pd

# ADDL 압축 시 산출되는 등간격 투여간격을 운반하는 입력 컬럼.
_INTERVAL_COL = "dose_interval"


def assign_ii(df: pd.DataFrame, meta: dict | None = None) -> dict:
    df = df.copy()

    # 1) 선행조건: ADDL/TIME 존재(누락은 c0015 detection 미통과 = hard fail, Q 아님).
    if not {"ADDL", "TIME"}.issubset(df.columns):
        return {"success": False, "df": df}

    # 2) ADDL>0이면 dose_interval, ADDL=0이면 II=0(interval 값과 무관하게 강제).
    #    interval 부재 시 NaN으로 두고 아래 invariant 검사에서 검출한다.
    interval = df[_INTERVAL_COL] if _INTERVAL_COL in df.columns else np.nan
    df["II"] = np.where(df["ADDL"] > 0, interval, 0)

    # 3) ADDL>0인데 II가 양수로 도출되지 않으면(결측/0/음수) 불변식 ADDL>0 ⟹ II>0 위반 → Q14.
    addl_pos = df["ADDL"] > 0
    if not (df.loc[addl_pos, "II"] > 0).all():
        return {"success": False, "route_to_q": "Q14", "df": df}

    return {"success": True, "df": df}
