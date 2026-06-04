"""ASSIGN BLQ_FLAG — BLQ_FLAG 부여

srp_intent: ASSIGN BLQ_FLAG
c_name_ko: BLQ_FLAG 부여
kind: transform  (requires_detection_by: c0205 A5 axis · can_route_to_q: [Q01])

postcondition_predicate:
    ('BLQ_FLAG' not in df.columns) or (df['BLQ_FLAG'].isin([0,1]).all() and (df.loc[df['BLQ_FLAG']==1, 'EVID']==0).all())

설계(plan): spec python_snippet 1:1 — blq_policy ∈ {M3,M4}(likelihood)이면
df['BLQ_FLAG'] = df['blq_detected'].astype(int); M1(exclusion)/M5(substitution)은 컬럼
미생성(postcond 1번째 disjunct로 valid). a5_state는 라우팅 게이트(None/BLQ-NO-POLICY → Q01)
이며 policy 분기보다 선행한다. silent-error guard: postcond가 요구하는 BLQ_FLAG∈{0,1} 및
"BLQ_FLAG=1 ⟹ EVID==0"(BLQ flag가 dose행에 붙지 않음)를 명시 검사해 위반 시 fail+Q01.
precondition의 c0205_passed는 orchestrator가 구조적으로 보장(D-S1) — 함수 내 검사 안 함
(c0019가 c0203_passed를 직접 검사하지 않는 것과 동형).
입력계약: blq_detected 생산자=mess 층 c0306(NORMALIZE BLQ_TOKEN, 미구현, cross-layer),
blq_policy=외부(sponsor/bioanalytical) 경계 입력 — issues/provenance_gaps.md GAP-15(DECISION-D3).
requires_detection_by=c0205는 a5_state만 보장(c0306 산출은 보장 안 함). 단위테스트는 fixture 주입.
"""

import pandas as pd


def assign_blq_flag(df: pd.DataFrame, meta: dict) -> dict:
    df = df.copy()

    # precondition: EVID 컬럼(c0010 산출) 부재 → fail
    if "EVID" not in df.columns:
        return {"success": False, "route_to_q": "Q01", "df": df}

    # routing gate: a5_state(c0205 산출) 부재 또는 BLQ-NO-POLICY → 사람 결정(Q01). policy 분기보다 선행.
    a5_state = meta.get("a5_state") if meta else None
    if a5_state is None or a5_state == "BLQ-NO-POLICY":
        return {"success": False, "route_to_q": "Q01", "df": df}

    # blq_policy enum 분기
    blq_policy = meta.get("blq_policy") if meta else None
    if blq_policy in ("M3", "M4"):
        # spec python_snippet 1:1 — BLQ → 1, non-BLQ → 0 (likelihood policy)
        if "blq_detected" not in df.columns:
            return {"success": False, "route_to_q": "Q01", "df": df}
        if df["blq_detected"].isna().any():
            return {"success": False, "route_to_q": "Q01", "df": df}
        df["BLQ_FLAG"] = df["blq_detected"].astype(int)

        # silent-error guard: 값∉{0,1} 또는 BLQ_FLAG=1이 dose행(EVID≠0)에 붙음 → postcond 위반, fail
        if not df["BLQ_FLAG"].isin([0, 1]).all():
            return {"success": False, "route_to_q": "Q01", "df": df}
        if not (df.loc[df["BLQ_FLAG"] == 1, "EVID"] == 0).all():
            return {"success": False, "route_to_q": "Q01", "df": df}
        return {"success": True, "df": df}

    # M1(exclusion)/M5(substitution)/기타 → BLQ_FLAG 컬럼 미생성 (postcond disjunct 1)
    return {"success": True, "df": df}
