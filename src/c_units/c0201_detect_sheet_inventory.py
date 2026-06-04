"""DETECT SHEET_INVENTORY BY ACROSS_FILE — A1 연구 통합 수준 평가

srp_intent: DETECT SHEET_INVENTORY BY ACROSS_FILE
c_name_ko: A1 연구 통합 수준 평가
kind: detect  (A1 axis classifier; df read-only)

postcondition_predicate:
    meta.get('a1_state') in ['SINGLE','MULTI-HOMO','MULTI-HETERO','MULTI-SITE','INTERIM']

Routing scope (can_route_to_q=[Q05]): route_to_q ∈ {None, Q05} only.
q_codes Q05 trigger: A1 ∈ {MULTI-HOMO, MULTI-HETERO, MULTI-SITE} AND harmonization
policy 부재. SINGLE/INTERIM never route. The MULTI-* states are policy-gated by
meta['harmonization_policy_present'] (정책 有 pass / 無 Q05).

Inputs are external file-inventory / study-metadata boundary inputs (no producing c).
See issues/provenance_gaps.md GAP-6.
"""

import pandas as pd

VALID_A1_STATES = frozenset([
    "SINGLE", "MULTI-HOMO", "MULTI-HETERO", "MULTI-SITE", "INTERIM",
])

# declared study-integration descriptor -> a1_state
_INTEGRATION_TO_STATE = {
    "single": "SINGLE",
    "multi-homo": "MULTI-HOMO",
    "multi-hetero": "MULTI-HETERO",
    "multi-site": "MULTI-SITE",
    "interim": "INTERIM",
}

# states whose routing is gated by harmonization_policy_present (정책 有 pass / 無 Q05)
_POLICY_GATED = frozenset(["MULTI-HOMO", "MULTI-HETERO", "MULTI-SITE"])

_STUDY_ID_COLS = ("study_id", "STUDYID", "study", "STUDY")


def _norm_descriptor(val) -> str | None:
    if not isinstance(val, str):
        return None
    norm = val.strip().lower().replace("_", "-").replace(" ", "-")
    return norm or None


def _count_studies(df: pd.DataFrame, meta: dict) -> int:
    studies = meta.get("studies")
    if isinstance(studies, list) and studies:
        return len({str(s).strip() for s in studies})
    n = meta.get("n_studies")
    if isinstance(n, int) and not isinstance(n, bool):
        return max(n, 1)
    for col in _STUDY_ID_COLS:
        if col in df.columns:
            uniq = df[col].dropna().astype(str).str.strip().nunique()
            return max(int(uniq), 1)
    return 1


def _classify_a1(df: pd.DataFrame, meta: dict) -> str:
    integ = _norm_descriptor(meta.get("study_integration"))
    if integ in _INTEGRATION_TO_STATE:
        return _INTEGRATION_TO_STATE[integ]
    if meta.get("interim_analysis"):
        return "INTERIM"
    return "SINGLE" if _count_studies(df, meta) <= 1 else "MULTI-HOMO"


def _route_a1(state: str, meta: dict):
    if state in _POLICY_GATED:
        return None if meta.get("harmonization_policy_present") else "Q05"
    return None


def detect_sheet_inventory(df: pd.DataFrame, meta: dict) -> dict:
    state = _classify_a1(df, meta)
    meta["a1_state"] = state
    route = _route_a1(state, meta)
    return {"a1_state": state, "pass": route is None, "route_to_q": route}
