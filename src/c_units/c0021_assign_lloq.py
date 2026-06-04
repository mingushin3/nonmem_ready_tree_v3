"""ASSIGN LLOQ — LLOQ 부여

srp_intent: ASSIGN LLOQ
c_name_ko: LLOQ 부여
kind: transform  (requires_detection_by: c0205 A5 axis · can_route_to_q: [Q01])

postcondition_predicate:
    ('LLOQ' not in df.columns) or ((df.loc[df['EVID']==0, 'LLOQ'] > 0).all() and (df.loc[df.get('BLQ_FLAG', pd.Series())==1, 'LLOQ'] > 0).all() if 'BLQ_FLAG' in df.columns else True)

설계(plan): 분기 변수 = 'BLQ_FLAG' in df.columns (c0020 형제 transform 산출의 런타임 존재) —
c0020의 blq_policy enum 분기와 구조가 달라 D-G4상 1:1(batch 아님). BLQ_FLAG 존재 시 LLOQ를
pd.to_numeric(lloq_value, errors='coerce')로 생성한다(c0019 선례의 방어적 변환 — bare
df['LLOQ']=df['lloq_value']는 object dtype 토큰에서 TypeError, 결측 silent 통과 위험).
이후 obs행(EVID==0)·BLQ행(BLQ_FLAG==1) 부분집합에 대해:
  Guard1(비수치/결측): NaN을 >0 비교 *전에* 명시 차단 → "non-numeric이라 fail"과 "≤0이라 fail"을 구분.
  Guard2(≤0): >0 위반 차단.
위반 시 fail+Q01. dose행(EVID≠0, non-BLQ)은 postcond·guard 모두 미제약(NaN 허용).
BLQ_FLAG 부재 → LLOQ 미생성(M1/M5 하류, postcond 1번째 disjunct로 valid).
precond gate: BLQ_FLAG 존재 + a5_state=LLOQ-MISSING → 사람 결정(Q01).
c0205_passed는 orchestrator가 구조적으로 보장(D-S1) — 함수 내 검사 안 함(c0019 동형).
★postcond는 _check_postcond에 토큰 단위 그대로 복사; guard는 구현 로직에만 존재(postcond 식 불변).
입력계약: lloq_value 생산자=mess 층 c0306(NORMALIZE BLQ_TOKEN, 미구현, cross-layer),
BLQ_FLAG=c0020 형제 transform — issues/provenance_gaps.md GAP-15(DECISION-D3).
requires_detection_by=c0205는 a5_state만 보장(c0306 산출은 보장 안 함). 단위테스트는 fixture 주입.
"""

import pandas as pd


def assign_lloq(df: pd.DataFrame, meta: dict) -> dict:
    df = df.copy()

    # precondition: EVID 컬럼(c0010 산출) 부재 → fail
    if "EVID" not in df.columns:
        return {"success": False, "route_to_q": "Q01", "df": df}

    # precond gate: BLQ_FLAG 존재 + a5_state=LLOQ-MISSING → 사람 결정(Q01)
    a5_state = meta.get("a5_state") if meta else None
    if "BLQ_FLAG" in df.columns and a5_state == "LLOQ-MISSING":
        return {"success": False, "route_to_q": "Q01", "df": df}

    # 분기: BLQ_FLAG 존재 시 LLOQ 부여(>0 필수), 부재 시 미생성(M1/M5 하류)
    if "BLQ_FLAG" in df.columns:
        if "lloq_value" not in df.columns:
            return {"success": False, "route_to_q": "Q01", "df": df}
        # c0019 선례: 방어적 numeric 변환(object 토큰·결측 → NaN)
        df["LLOQ"] = pd.to_numeric(df["lloq_value"], errors="coerce")

        obs_lloq = df.loc[df["EVID"] == 0, "LLOQ"]
        blq_lloq = df.loc[df["BLQ_FLAG"] == 1, "LLOQ"]

        # Guard1(비수치/결측): NaN을 >0 비교 *전에* 명시 차단(≤0 fail과 구분)
        if obs_lloq.isna().any() or blq_lloq.isna().any():
            return {"success": False, "route_to_q": "Q01", "df": df}
        # Guard2(≤0)
        if not (obs_lloq > 0).all() or not (blq_lloq > 0).all():
            return {"success": False, "route_to_q": "Q01", "df": df}
        return {"success": True, "df": df}

    # BLQ_FLAG 부재 → LLOQ 컬럼 미생성 (postcond disjunct 1)
    return {"success": True, "df": df}
