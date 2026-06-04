"""ASSIGN TIME_VARYING_COVARIATE — 시변 공변량 수치 코딩 + LOCF

srp_intent: ASSIGN TIME_VARYING_COVARIATE
c_name_ko: 시변 공변량 수치 코딩
kind: transform  (requires_detection_by: c0207 A7 axis · can_route_to_q: [Q07])

postcondition_predicate:
    all(df[cov].apply(lambda x: isinstance(x, (int, float, np.floating, np.integer))).all() for cov in meta.get('tv_covariates', []))

설계(plan): spec python_snippet의 df.groupby('ID')[cov].ffill() = LOCF(Last Observation Carried
Forward). vocabulary.md §A V10 PROPAGATE("값을 인접 행/셀로 전파한다 — forward-fill, carry-forward
등"; 전형 pairing 'PROPAGATE BASELINE_COVARIATE BY WITHIN_ID')가 정의하는 *정당* 연산이다 —
관측된 값을 동일 subject 내에서 전파하는 것이므로 §A가 금지하는 *자의적 IMPUTE*(모집단 통계로
없는 값을 날조)와 구분된다. 따라서 c0022의 FLAG-우선 override가 c0023에는 불필요하다(ffill 정당).
단 LOCF로 채울 수 없는 leading 결측(직전 관측 부재)은 carry-forward 대상이 없어 정책 필요 → Q07
(bfill·mean-fill은 날조이므로 금지).

분기/라우팅(D-S4 conditional edge):
  structural gate — 'ID' 부재 → Q07(within-ID groupby 키 부재; c0021 EVID-부재→Q01 게이트 동형,
    primary Q).
  axis gate — a7_state==POLICY-MISSING → Q07(can_route_to_q=[Q07] 내 자기축 disjunct).
  LOCF — 각 tv cov: pd.to_numeric(coerce, c0019 선례 방어적 변환) → df.groupby('ID')[cov].ffill()
    (within-ID 전파; ★cross-ID bleed 금지 — groupby 없는 ffill은 타 subject 값 오염 silent-error).
  ffill 후 residual NaN(leading) 존재 → Q07. 없으면 success.
c0207_passed는 orchestrator가 구조적으로 보장(D-S1) — 함수 내 미검사(c0019/c0021 동형).
입력계약(GAP-3): tv_covariates 컬럼명 리스트 생산자 부재 — meta 선언, fixture 주입(Phase 5 정산).
  groupby 키 'ID'는 L-1→L-2 시점 가용(c0018 ASSIGN ID 산출); c0141(L-2→L-3)의 subject_id와
  키 상이는 provenance_gaps GAP-17 기록. 컬럼값 생산자=상류 정규화([[PRINCIPLE]]).
"""

import pandas as pd
import numpy as np


def _resolve_tv_covariates(df: pd.DataFrame, meta: dict) -> list:
    declared = meta.get("tv_covariates") if meta else None
    if declared:
        return [c for c in declared if c in df.columns]
    return []


def assign_time_varying_covariate(df: pd.DataFrame, meta: dict) -> dict:
    df = df.copy()

    # structural gate: within-ID LOCF에 'ID' 필수 (c0021 EVID 게이트 동형, primary Q)
    if "ID" not in df.columns:
        return {"success": False, "route_to_q": "Q07", "df": df}

    # axis gate(D-S4): A7 자기축 disjunct → Q07
    a7_state = meta.get("a7_state") if meta else None
    if a7_state == "POLICY-MISSING":
        return {"success": False, "route_to_q": "Q07", "df": df}

    covs = _resolve_tv_covariates(df, meta)

    # LOCF(=PROPAGATE, not IMPUTE): to_numeric → within-ID forward-fill
    for cov in covs:
        df[cov] = pd.to_numeric(df[cov], errors="coerce")
        df[cov] = df.groupby("ID")[cov].ffill()

    # residual missing(leading, 직전 관측 부재) → Q07 (bfill·mean-fill 날조 금지)
    for cov in covs:
        if df[cov].isna().any():
            return {"success": False, "route_to_q": "Q07", "df": df}

    return {"success": True, "df": df}
