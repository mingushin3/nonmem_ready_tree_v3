"""CLASSIFY COVARIATE_LAYOUT — A7 공변량 부착 평가

srp_intent: CLASSIFY COVARIATE_LAYOUT
c_name_ko: A7 공변량 부착 평가
kind: detect  (A7 axis classifier; df read-only)

postcondition_predicate:
    meta.get('a7_state') in ['NONE-REQUIRED','BASELINE-CLEAN','BASELINE-IMPUTABLE','TIME-VARYING','EXTERNAL-JOIN','PEDIATRIC-MATURATION','KEY-MISSING','POLICY-MISSING']

Routing scope (can_route_to_q=[Q07,Q13]): route_to_q ∈ {None, Q07, Q13} only.
q_codes SSOT triggers (llm_prompt 산문 비사용 — c0203/c0206 선례):
  Q07 = A7 = POLICY-MISSING (자기축 disjunct).
  Q13 = A7 = KEY-MISSING    (자기축 disjunct; c0206 Q03 같은 교차축 trigger 없음).
  나머지 6 state → route_to_q=None, pass=True.

선언 1차 → df fallback 패턴(c0202/c0203/c0205 일관):
  meta['covariate_state'] 선언 descriptor(외부 경계 입력)가 1차. 없으면 df fallback 3-outcome:
    cov 컬럼 없음 → NONE-REQUIRED
    cov 컬럼 있고 결측 있음 → BASELINE-IMPUTABLE
    cov 컬럼 있고 결측 없음 → BASELINE-CLEAN
  ★ df만으로 Q07/Q13(POLICY-MISSING/KEY-MISSING)·도메인 state는 절대 날조하지 않는다(c0206 'Q 날조 금지').
  fallback은 8개 중 3개만 도달; 나머지 5개(TIME-VARYING/EXTERNAL-JOIN/PEDIATRIC-MATURATION/
  KEY-MISSING/POLICY-MISSING)는 covariate_state 선언 의존 — 문서화된 한계(c0202 GAP-9 동형).

입력계약 (issues/provenance_gaps.md GAP-11):
  meta['covariate_state'] = 생산 c 없는 sponsor/protocol 외부 경계 입력(orchestrator Phase 5 주입).
  df의 covariate 컬럼은 상류 normalization이 생산([[PRINCIPLE]] happy 입력=선행 출력).
c0207은 meta['a7_state']만 write한다. baseline_covariates/tv_covariates 리스트는 생산하지 않는다
  (하류 consumer c0022/c0023 사안 — GAP-3 유지). df read-only.
"""

import pandas as pd

VALID_A7_STATES = frozenset([
    "NONE-REQUIRED",
    "BASELINE-CLEAN",
    "BASELINE-IMPUTABLE",
    "TIME-VARYING",
    "EXTERNAL-JOIN",
    "PEDIATRIC-MATURATION",
    "KEY-MISSING",
    "POLICY-MISSING",
])

# declared covariate-layout descriptor -> a7_state
_COV_STATE_TO_STATE = {
    "none-required": "NONE-REQUIRED",
    "baseline-clean": "BASELINE-CLEAN",
    "baseline-imputable": "BASELINE-IMPUTABLE",
    "time-varying": "TIME-VARYING",
    "external-join": "EXTERNAL-JOIN",
    "pediatric-maturation": "PEDIATRIC-MATURATION",
    "key-missing": "KEY-MISSING",
    "policy-missing": "POLICY-MISSING",
}

# 알려진 covariate 컬럼명(대소문자 무시). NONMEM 구조 컬럼(ID/TIME/DV/...)은 제외.
_COVARIATE_COLS = frozenset([
    "wt", "bw", "weight", "age", "sex", "gender", "race", "ethnic",
    "ht", "height", "bmi", "bsa", "crcl", "egfr", "alb", "alt", "ast",
    "bili", "scr", "geno", "genotype", "smok", "smoke", "formulation",
])


def _norm_descriptor(val) -> str | None:
    if not isinstance(val, str):
        return None
    norm = val.strip().lower().replace("_", "-").replace(" ", "-")
    return norm or None


def _covariate_columns(df: pd.DataFrame) -> list:
    return [c for c in df.columns if str(c).strip().lower() in _COVARIATE_COLS]


def _classify_a7(df: pd.DataFrame, meta: dict) -> str:
    # 1차: 선언 descriptor (외부 경계 입력)
    state = _norm_descriptor(meta.get("covariate_state"))
    if state in _COV_STATE_TO_STATE:
        return _COV_STATE_TO_STATE[state]

    # df fallback 3-outcome (선언 부재). Q07/Q13·도메인 state는 날조 금지.
    cov_cols = _covariate_columns(df)
    if not cov_cols:
        return "NONE-REQUIRED"
    if df[cov_cols].isna().any().any():
        return "BASELINE-IMPUTABLE"
    return "BASELINE-CLEAN"


def _route_a7(a7_state: str):
    # q_codes SSOT. 둘 다 자기축 A7 disjunct.
    if a7_state == "POLICY-MISSING":
        return "Q07"
    if a7_state == "KEY-MISSING":
        return "Q13"
    return None


def classify_covariate_layout(df: pd.DataFrame, meta: dict) -> dict:
    state = _classify_a7(df, meta)
    meta["a7_state"] = state
    route = _route_a7(state)
    return {"a7_state": state, "pass": route is None, "route_to_q": route}
