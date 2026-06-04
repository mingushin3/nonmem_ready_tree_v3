"""ASSIGN ADDL — ADDL 부여

srp_intent: ASSIGN ADDL
c_name_ko: ADDL 부여

postcondition_predicate:
    'ADDL' in df.columns and (df['ADDL'] >= 0).all() and df['ADDL'].apply(lambda x: isinstance(x, (int, np.integer))).all()
"""

import numpy as np
import pandas as pd

# ADDL 압축 대상은 일반 유지투여(EVID==1)만. reset/SS(2,3,4)·obs(0)는 압축하지 않는다.
ADDL_DOSE_EVID = 1
# subject 그룹 키 우선순위(먼저 발견되는 컬럼 사용).
_ID_COLS = ("ID", "subject_id")
# TIME 간격 동일성 판정 허용오차.
_INTERVAL_TOL = 1e-9


def _subject_col(df: pd.DataFrame):
    for col in _ID_COLS:
        if col in df.columns:
            return col
    return None


def assign_addl(df: pd.DataFrame, meta: dict) -> dict:
    df = df.copy()

    # 1) 선행조건: EVID/AMT/TIME 존재(누락은 detection 미통과 = hard fail, Q 아님).
    if not {"EVID", "AMT", "TIME"}.issubset(df.columns):
        return {"success": False, "df": df}

    # 2) A4 = ADDL-ACTUAL-CONFLICT면 implied dose vs actual dose 충돌 → 사람 결정 필요(Q14).
    if meta.get("a4_state") == "ADDL-ACTUAL-CONFLICT":
        return {"success": False, "route_to_q": "Q14", "df": df}

    # 3) 기본값 0. 반복 dose가 식별되면 첫 행에만 횟수를 기재한다.
    df["ADDL"] = 0

    id_col = _subject_col(df)
    # subject 컬럼이 없으면 전체를 단일 subject로 본다.
    groups = df.groupby(id_col, sort=False) if id_col is not None else [(None, df)]

    rows_to_drop = []
    for _, g in groups:
        doses = g[g["EVID"] == ADDL_DOSE_EVID]
        # 동일 AMT의 반복투여 묶음만 압축 후보.
        for _amt, block in doses.groupby("AMT", sort=False):
            if len(block) < 2:
                continue
            block = block.sort_values("TIME")
            diffs = block["TIME"].diff().dropna().to_numpy()
            # 모든 간격이 동일하고 양수일 때만 등간격 반복투여로 압축.
            regular = (diffs > 0).all() and np.allclose(diffs, diffs[0], atol=_INTERVAL_TOL)
            if not regular:
                continue
            first_idx = block.index[0]
            df.at[first_idx, "ADDL"] = len(block) - 1
            rows_to_drop.extend(block.index[1:])

    if rows_to_drop:
        df = df.drop(index=rows_to_drop)

    df["ADDL"] = df["ADDL"].astype(int)
    return {"success": True, "df": df}
