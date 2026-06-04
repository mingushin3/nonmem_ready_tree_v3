"""ASSIGN TIME_VARYING_COVARIATE — 시변 공변량 부착 (L-2→L-3)

srp_intent: ASSIGN TIME_VARYING_COVARIATE
c_name_ko: 시변 공변량 부착
kind: transform  (requires_detection_by: c0207 A7 axis · can_route_to_q: [Q07])

postcondition_predicate:
    all(df[cov].notna().all() for cov in meta.get('tv_covariates', []))

설계(c0023 L-1→L-2 형제 동형 — key='subject_id'): spec python_snippet
df.groupby('subject_id')[cov].ffill() = LOCF(Last Observation Carried Forward). vocabulary.md §A V10
PROPAGATE("forward-fill, carry-forward")가 정의하는 *정당* 연산 — 관측값을 동일 subject 내에서
전파하는 것이므로 §A가 금지하는 *자의적 IMPUTE*(모집단 통계로 없는 값 날조)와 구분된다. 따라서
c0022의 FLAG-우선 override가 본 c에는 불필요(ffill 정당). LOCF로 채울 수 없는 leading 결측(직전
관측 부재)은 carry-forward 대상이 없어 정책 필요 → Q07(bfill·mean-fill은 날조이므로 금지).

GAP-17(키): c0023은 'ID'(L-1→L-2 시점 c0018 산출 가용)로 group하나, c0141은 L-2→L-3 시점이라
ID 미부여 가능 → 'subject_id'로 group(c0140과 일관). provenance_gaps GAP-17 기록.

분기/라우팅(D-S4 conditional edge):
  structural gate — 'subject_id' 부재 → Q07(within-subject groupby 키 부재; c0023 'ID' 게이트 동형, primary Q).
  axis gate — a7_state==POLICY-MISSING → Q07(can_route_to_q=[Q07] 내 자기축 disjunct).
  LOCF — 각 tv cov: pd.to_numeric(coerce, c0019 선례 방어적 변환) → df.groupby('subject_id')[cov].ffill()
    (within-subject 전파; ★cross-subject bleed 금지 — groupby 없는 ffill은 타 subject 값 오염 silent-error).
  ffill 후 residual NaN(leading) 존재 → Q07. 없으면 success.
c0207_passed는 orchestrator가 구조적으로 보장(D-S1) — 함수 내 미검사(c0022/c0023 동형).
입력계약(GAP-3): tv_covariates 컬럼명 리스트 생산자 부재 — meta 선언, fixture 주입(Phase 5 정산).
  컬럼값 생산자=상류 정규화([[PRINCIPLE]] happy 입력=선행 출력).
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

    # structural gate: within-subject LOCF에 'subject_id' 필수 (c0023 'ID' 게이트 동형; GAP-17)
    if "subject_id" not in df.columns:
        return {"success": False, "route_to_q": "Q07", "df": df}

    # axis gate(D-S4): A7 자기축 disjunct → Q07
    a7_state = meta.get("a7_state") if meta else None
    if a7_state == "POLICY-MISSING":
        return {"success": False, "route_to_q": "Q07", "df": df}

    covs = _resolve_tv_covariates(df, meta)

    # LOCF(=PROPAGATE, not IMPUTE): to_numeric → within-subject forward-fill
    for cov in covs:
        df[cov] = pd.to_numeric(df[cov], errors="coerce")
        df[cov] = df.groupby("subject_id")[cov].ffill()

    # residual missing(leading, 직전 관측 부재) → Q07 (bfill·mean-fill 날조 금지)
    for cov in covs:
        if df[cov].isna().any():
            return {"success": False, "route_to_q": "Q07", "df": df}

    return {"success": True, "df": df}
