"""DETECT TIME_FORMAT — A3 시간 유도 정책 평가

srp_intent: DETECT TIME_FORMAT
c_name_ko: A3 시간 유도 정책 평가
kind: detect  (A3 axis classifier; df read-only)

postcondition_predicate:
    meta.get('a3_state') in ['ACTUAL','NOMINAL-ONLY','ACTUAL-PREFERRED','NOMINAL-PREFERRED','ELAPSED','INTERVAL','AMBIGUOUS','UNRECOVERABLE']

Routing scope (can_route_to_q=[Q02,Q12]): route_to_q ∈ {None, Q02, Q12} only.
q_codes triggers: Q02 = (A3 = AMBIGUOUS), Q12 = (A3 = UNRECOVERABLE). The llm_prompt
prose says "UNRECOVERABLE→INVALID", but Q12 (recover_to_c c0203) IS in can_route_to_q
and its human_decision_point is "복원 데이터 제공 또는 INVALID 판정 수용" — so
UNRECOVERABLE→Q12 is in-scope (the INVALID terminal is a human decision past Q12).
This is NOT a routing-scope gap. See issues/provenance_gaps.md GAP-7 (input provenance).

precondition_predicate: 'time_value' in df.columns or 'TIME' in df.columns
"""

import pandas as pd

VALID_A3_STATES = frozenset([
    "ACTUAL", "NOMINAL-ONLY", "ACTUAL-PREFERRED", "NOMINAL-PREFERRED",
    "ELAPSED", "INTERVAL", "AMBIGUOUS", "UNRECOVERABLE",
])

# declared time-derivation policy descriptor -> a3_state
_POLICY_TO_STATE = {
    "actual": "ACTUAL",
    "nominal-only": "NOMINAL-ONLY",
    "actual-preferred": "ACTUAL-PREFERRED",
    "nominal-preferred": "NOMINAL-PREFERRED",
    "elapsed": "ELAPSED",
    "interval": "INTERVAL",
    "ambiguous": "AMBIGUOUS",
    "unrecoverable": "UNRECOVERABLE",
}


def _norm_descriptor(val) -> str | None:
    if not isinstance(val, str):
        return None
    norm = val.strip().lower().replace("_", "-").replace(" ", "-")
    return norm or None


def _time_column(df: pd.DataFrame):
    if "time_value" in df.columns:
        return "time_value"
    if "TIME" in df.columns:
        return "TIME"
    return None


def _classify_a3(df: pd.DataFrame, meta: dict) -> str:
    policy = _norm_descriptor(meta.get("time_policy"))
    if policy in _POLICY_TO_STATE:
        return _POLICY_TO_STATE[policy]

    # df fallback: inspect the time column the precondition guarantees.
    col = _time_column(df)
    if col is None:
        return "UNRECOVERABLE"
    series = df[col]
    if series.dropna().empty:
        return "UNRECOVERABLE"
    numeric = pd.to_numeric(series, errors="coerce")
    if numeric.notna().all():
        return "ACTUAL"
    # values present but some/all unparseable → cannot derive deterministically
    return "AMBIGUOUS"


def _route_a3(state: str, meta: dict):
    if state == "AMBIGUOUS":
        return "Q02"
    if state == "UNRECOVERABLE":
        return "Q12"
    return None


def detect_time_format(df: pd.DataFrame, meta: dict) -> dict:
    state = _classify_a3(df, meta)
    meta["a3_state"] = state
    route = _route_a3(state, meta)
    return {"a3_state": state, "pass": route is None, "route_to_q": route}
