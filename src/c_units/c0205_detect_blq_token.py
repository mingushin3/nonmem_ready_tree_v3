"""DETECT BLQ_TOKEN — A5 관측/BLQ 평가

srp_intent: DETECT BLQ_TOKEN
c_name_ko: A5 관측/BLQ 평가
kind: detect  (A5 axis classifier; df read-only)

postcondition_predicate:
    meta.get('a5_state') in ['CLEAN','BLQ-FLAGGED','BLQ-TEXT','BLQ-ZERO','MULTI-ANALYTE','LLOQ-CHANGED','MISSING-MDV1','BIOANALYTICAL-FINAL-FLAG-MISSING','ABOVE-ULOQ','ABOVE-ULOQ-NO-POLICY','REPLICATE-SAME-TIME','REPLICATE-NO-POLICY','BLQ-NO-POLICY','LLOQ-MISSING','ABSENT']

Routing scope (can_route_to_q=[Q01,Q15D]): route_to_q ∈ {None, Q01, Q15D} only.
q_codes triggers: Q01 = A5 ∈ {BLQ-NO-POLICY, LLOQ-MISSING, ABOVE-ULOQ-NO-POLICY(P1),
REPLICATE-NO-POLICY(P3)}; Q15D = A5 = BIOANALYTICAL-FINAL-FLAG-MISSING.
ABSENT → INVALID is OUT of can_route_to_q scope: classify only, route_to_q=None
(downstream ROUTE c handles the INVALID terminal). See issues/provenance_gaps.md GAP-8.
"""

import pandas as pd

VALID_A5_STATES = frozenset([
    "CLEAN", "BLQ-FLAGGED", "BLQ-TEXT", "BLQ-ZERO", "MULTI-ANALYTE",
    "LLOQ-CHANGED", "MISSING-MDV1", "BIOANALYTICAL-FINAL-FLAG-MISSING",
    "ABOVE-ULOQ", "ABOVE-ULOQ-NO-POLICY", "REPLICATE-SAME-TIME",
    "REPLICATE-NO-POLICY", "BLQ-NO-POLICY", "LLOQ-MISSING", "ABSENT",
])

# declared observation/BLQ descriptor -> a5_state
_BLQ_TO_STATE = {
    "clean": "CLEAN",
    "blq-flagged": "BLQ-FLAGGED",
    "blq-text": "BLQ-TEXT",
    "blq-zero": "BLQ-ZERO",
    "multi-analyte": "MULTI-ANALYTE",
    "lloq-changed": "LLOQ-CHANGED",
    "missing-mdv1": "MISSING-MDV1",
    "bioanalytical-final-flag-missing": "BIOANALYTICAL-FINAL-FLAG-MISSING",
    "above-uloq": "ABOVE-ULOQ",
    "above-uloq-no-policy": "ABOVE-ULOQ-NO-POLICY",
    "replicate-same-time": "REPLICATE-SAME-TIME",
    "replicate-no-policy": "REPLICATE-NO-POLICY",
    "blq-no-policy": "BLQ-NO-POLICY",
    "lloq-missing": "LLOQ-MISSING",
    "absent": "ABSENT",
}

# states routing to Q01 (BLQ/LLOQ/ULOQ/replicate policy missing)
_Q01_STATES = frozenset([
    "BLQ-NO-POLICY", "LLOQ-MISSING", "ABOVE-ULOQ-NO-POLICY", "REPLICATE-NO-POLICY",
])

_DV_COLS = ("dv_value", "DV", "dv")
_BLQ_TOKEN_PATTERN = r"<|BLQ|LLOQ|ULOQ"


def _norm_descriptor(val) -> str | None:
    if not isinstance(val, str):
        return None
    norm = val.strip().lower().replace("_", "-").replace(" ", "-")
    return norm or None


def _dv_column(df: pd.DataFrame):
    return next((c for c in _DV_COLS if c in df.columns), None)


def _classify_a5(df: pd.DataFrame, meta: dict) -> str:
    state = _norm_descriptor(meta.get("obs_blq_state"))
    if state in _BLQ_TO_STATE:
        return _BLQ_TO_STATE[state]

    # df fallback
    col = _dv_column(df)
    if col is None or df[col].dropna().empty:
        return "ABSENT"
    series = df[col].dropna().astype(str).str.strip()
    if series.str.contains(_BLQ_TOKEN_PATTERN, case=False, regex=True).any():
        return "BLQ-TEXT"
    return "CLEAN"


def _route_a5(state: str, meta: dict):
    if state in _Q01_STATES:
        return "Q01"
    if state == "BIOANALYTICAL-FINAL-FLAG-MISSING":
        return "Q15D"
    return None


def detect_blq_token(df: pd.DataFrame, meta: dict) -> dict:
    state = _classify_a5(df, meta)
    meta["a5_state"] = state
    route = _route_a5(state, meta)
    return {"a5_state": state, "pass": route is None, "route_to_q": route}
