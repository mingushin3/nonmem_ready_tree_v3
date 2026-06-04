"""VERIFY AMT — A4 투여 완결성 평가

srp_intent: VERIFY AMT
c_name_ko: A4 투여 완결성 평가
kind: verify  (A4 axis classifier; df read-only)

postcondition_predicate:
    meta.get('a4_state') in ['COMPLETE','WEIGHT-BASED','BSA-BASED','PLANNED-FALLBACK','ADDL-II','ADDL-ACTUAL-CONFLICT','TITRATION-ADAPTIVE','LOADING-MAINTENANCE','INFUSION-STOP-RESTART','PARTIAL-RECOVERY','COMBINATION','MISSING-NO-POLICY','UNRECOVERABLE']

Routing scope (can_route_to_q=[Q08,Q14]): route_to_q ∈ {None, Q08, Q14} only.
universe_sm routes INFUSION-STOP-RESTART→Q04 and UNRECOVERABLE→INVALID, but those
terminations are a downstream ROUTE c's job (D-S1/D-S4); here they classify with
route_to_q=None. See issues/provenance_gaps.md GAP-5.
priority: ADDL-ACTUAL-CONFLICT first (universe_sm §3 A4: 혼재+정책無 → conflict 우선).
"""

import pandas as pd

VALID_A4_STATES = frozenset([
    "COMPLETE", "WEIGHT-BASED", "BSA-BASED", "PLANNED-FALLBACK", "ADDL-II",
    "ADDL-ACTUAL-CONFLICT", "TITRATION-ADAPTIVE", "LOADING-MAINTENANCE",
    "INFUSION-STOP-RESTART", "PARTIAL-RECOVERY", "COMBINATION",
    "MISSING-NO-POLICY", "UNRECOVERABLE",
])

# declared regimen descriptor -> a4_state
_REGIMEN_TO_STATE = {
    "complete": "COMPLETE",
    "weight-based": "WEIGHT-BASED",
    "bsa-based": "BSA-BASED",
    "planned-fallback": "PLANNED-FALLBACK",
    "addl-ii": "ADDL-II",
    "titration": "TITRATION-ADAPTIVE",
    "loading-maintenance": "LOADING-MAINTENANCE",
    "infusion-stop-restart": "INFUSION-STOP-RESTART",
    "partial-recovery": "PARTIAL-RECOVERY",
    "combination": "COMBINATION",
    "missing": "MISSING-NO-POLICY",
    "unrecoverable": "UNRECOVERABLE",
}

# states whose routing is gated by dose_policy_present (정책 有 pass / 無 Q08)
_POLICY_GATED = frozenset(["TITRATION-ADAPTIVE", "LOADING-MAINTENANCE"])


def _has_dose_rows(df: pd.DataFrame) -> bool:
    if "EVID" in df.columns:
        evid = pd.to_numeric(df["EVID"], errors="coerce")
        if evid.isin([1, 4]).any():
            return True
    if "AMT" in df.columns:
        amt = pd.to_numeric(df["AMT"], errors="coerce").fillna(0)
        if (amt > 0).any():
            return True
    return False


def _norm_regimen(val) -> str | None:
    if not isinstance(val, str):
        return None
    norm = val.strip().lower().replace("_", "-").replace(" ", "-")
    return norm or None


def _classify_a4(df: pd.DataFrame, meta: dict) -> str:
    # 1. conflict-first (universe_sm §3 A4 line 136)
    if meta.get("has_addl_actual_conflict"):
        return "ADDL-ACTUAL-CONFLICT"

    regimen = _norm_regimen(meta.get("dose_regimen"))

    # 2. unrecoverable
    if regimen == "unrecoverable" or meta.get("unrecoverable"):
        return "UNRECOVERABLE"

    # 3. explicit declared regimen
    if regimen in _REGIMEN_TO_STATE:
        return _REGIMEN_TO_STATE[regimen]

    # 4. default from df dose-row presence
    return "COMPLETE" if _has_dose_rows(df) else "MISSING-NO-POLICY"


def _route_a4(state: str, meta: dict):
    if state == "ADDL-ACTUAL-CONFLICT":
        return "Q14"
    if state == "MISSING-NO-POLICY":
        return "Q08"
    if state in _POLICY_GATED:
        return None if meta.get("dose_policy_present") else "Q08"
    return None


def verify_amt(df: pd.DataFrame, meta: dict) -> dict:
    state = _classify_a4(df, meta)
    meta["a4_state"] = state
    route = _route_a4(state, meta)
    return {"a4_state": state, "pass": route is None, "route_to_q": route}
