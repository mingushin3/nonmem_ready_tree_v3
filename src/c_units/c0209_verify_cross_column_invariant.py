"""VERIFY CROSS_COLUMN_INVARIANT — A9 데이터 결함 수리 가능성 평가

srp_intent: VERIFY CROSS_COLUMN_INVARIANT
c_name_ko: A9 데이터 결함 수리 가능성 평가
kind: verify  (A9 axis classifier; df read-only)

postcondition_predicate:
    meta.get('a9_state') in ['CLEAN','DUPLICATE-EXACT','UNSORTED','COLUMN-SYNONYM','UNIT-CONVERSION','ENCODING-FIX','PRE-DOSE-SAMPLE','PLANNED-VS-ACTUAL','PROTOCOL-DEVIATION','REANALYSIS-FINAL-DEFINED','REANALYSIS-FINAL-MISSING','PROTOCOL-DEVIATION-NO-POLICY','IRRECONCILABLE']

★ AUDIT: srp_intent NOUN은 CROSS_COLUMN_INVARIANT(컬럼 간 불변식 검증을 시사)이나, 실제 postcond/
output(meta['a9_state'])/layer(L-3->L-4 axis 평가)는 A9 axis-state 분류기다. EVID/AMT/DV/CMT 등 NONMEM
특수컬럼을 교차검증하지 않는다(그 컬럼은 하류 L-1->L-2 transform 산출, A9 평가 시점엔 부재).
입력계약·근거: issues/provenance_gaps.md GAP-12.

Routing scope (can_route_to_q=[Q06,Q15D]): route_to_q ∈ {None, Q06, Q15D} only.
q_codes SSOT triggers (llm_prompt 산문 비사용 — c0203/c0206/c0207 선례):
  Q06  = A9 = PROTOCOL-DEVIATION-NO-POLICY (자기축 disjunct).
  Q15D = A9 = REANALYSIS-FINAL-MISSING     (q_codes Q15D는 A5=BIOANALYTICAL-FINAL-FLAG-MISSING과 OR; A5는 c0205 소관).
  IRRECONCILABLE은 universe_sm상 ->INVALID이나 INVALID 종착은 하류 ROUTE c 책임 → 분류만, route_to_q=None
    (c0204 GAP-5 / c0205 GAP-8 선례; 분류 범위 ≠ 라우팅 범위). 나머지 9 state → route_to_q=None, pass=True.

선언 1차 → df fallback 패턴(c0202/c0203/c0205/c0207 일관):
  meta['defect_state'] 선언 descriptor(외부 경계 입력)가 1차. 없으면 df fallback 3-outcome:
    완전중복(full-row) 행 존재 → DUPLICATE-EXACT
    id별 time 비오름차순     → UNSORTED
    그 외                   → CLEAN
  ★ df만으로 Q06/Q15D(PROTOCOL-DEVIATION-NO-POLICY/REANALYSIS-FINAL-MISSING)·도메인 state는 날조하지 않는다
    (c0206/c0207 'Q 날조 금지'). fallback은 13개 중 3개만 도달; 나머지 10개는 선언 의존 — 문서화된 한계.
  ★ P3(universe_sm §6 L154): DUPLICATE-EXACT(완전중복 행 전체 일치)는 동일 (ID,TIME)에 *다른* DV가 있는
    replicate(A5 소관)와 다르다. fallback은 full-row 완전중복만 DUPLICATE-EXACT로 보아 정당 replicate의
    silent data loss를 차단한다.
"""

import pandas as pd

VALID_A9_STATES = frozenset([
    "CLEAN",
    "DUPLICATE-EXACT",
    "UNSORTED",
    "COLUMN-SYNONYM",
    "UNIT-CONVERSION",
    "ENCODING-FIX",
    "PRE-DOSE-SAMPLE",
    "PLANNED-VS-ACTUAL",
    "PROTOCOL-DEVIATION",
    "REANALYSIS-FINAL-DEFINED",
    "REANALYSIS-FINAL-MISSING",
    "PROTOCOL-DEVIATION-NO-POLICY",
    "IRRECONCILABLE",
])

# declared data-defect descriptor -> a9_state
_DEFECT_STATE_TO_STATE = {
    "clean": "CLEAN",
    "duplicate-exact": "DUPLICATE-EXACT",
    "unsorted": "UNSORTED",
    "column-synonym": "COLUMN-SYNONYM",
    "unit-conversion": "UNIT-CONVERSION",
    "encoding-fix": "ENCODING-FIX",
    "pre-dose-sample": "PRE-DOSE-SAMPLE",
    "planned-vs-actual": "PLANNED-VS-ACTUAL",
    "protocol-deviation": "PROTOCOL-DEVIATION",
    "reanalysis-final-defined": "REANALYSIS-FINAL-DEFINED",
    "reanalysis-final-missing": "REANALYSIS-FINAL-MISSING",
    "protocol-deviation-no-policy": "PROTOCOL-DEVIATION-NO-POLICY",
    "irreconcilable": "IRRECONCILABLE",
}

_ID_COLS = ("subject_id", "ID", "id")
_TIME_COLS = ("time_value", "TIME", "time")


def _norm_descriptor(val) -> str | None:
    if not isinstance(val, str):
        return None
    norm = val.strip().lower().replace("_", "-").replace(" ", "-")
    return norm or None


def _first_present(df: pd.DataFrame, candidates) -> str | None:
    for col in candidates:
        if col in df.columns:
            return col
    return None


def _has_exact_duplicate(df: pd.DataFrame) -> bool:
    return bool(df.duplicated(keep="first").any())


def _is_unsorted_within_id(df: pd.DataFrame) -> bool:
    time_col = _first_present(df, _TIME_COLS)
    if time_col is None:
        return False
    times = pd.to_numeric(df[time_col], errors="coerce")
    id_col = _first_present(df, _ID_COLS)
    if id_col is None:
        return bool((times.diff() < 0).any())
    return bool(times.groupby(df[id_col]).diff().lt(0).any())


def _classify_a9(df: pd.DataFrame, meta: dict) -> str:
    # 1차: 선언 descriptor (외부 경계 입력)
    state = _norm_descriptor(meta.get("defect_state"))
    if state in _DEFECT_STATE_TO_STATE:
        return _DEFECT_STATE_TO_STATE[state]

    # df fallback 3-outcome (선언 부재). Q06/Q15D·도메인 state는 날조 금지.
    if _has_exact_duplicate(df):
        return "DUPLICATE-EXACT"
    if _is_unsorted_within_id(df):
        return "UNSORTED"
    return "CLEAN"


def _route_a9(a9_state: str):
    # q_codes SSOT. 둘 다 자기축 A9 disjunct. IRRECONCILABLE->INVALID은 하류 ROUTE c (GAP-12).
    if a9_state == "PROTOCOL-DEVIATION-NO-POLICY":
        return "Q06"
    if a9_state == "REANALYSIS-FINAL-MISSING":
        return "Q15D"
    return None


def verify_cross_column_invariant(df: pd.DataFrame, meta: dict) -> dict:
    state = _classify_a9(df, meta)
    meta["a9_state"] = state
    route = _route_a9(state)
    return {"a9_state": state, "pass": route is None, "route_to_q": route}
