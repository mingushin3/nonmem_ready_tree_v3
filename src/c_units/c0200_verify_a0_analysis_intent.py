"""VERIFY COLUMN_SCHEMA — A0 분석 의도 평가

srp_intent: VERIFY COLUMN_SCHEMA
c_name_ko: A0 분석 의도 평가
kind: verify  (A0 axis classifier; df read-only)

postcondition_predicate:
    meta.get('a0_state') in ['AIC-MISSING','AIC-PK','AIC-POPPK','AIC-PKPD','AIC-ER','AIC-DDI','AIC-PEDS','AIC-SPECIAL','AIC-CUSTOM']

Reads meta['analysis_intent'] (declared AIC code, 1차 신호) and, when intent is
absent, falls back to meta['endpoint_data_type'] -> {AIC-PK, AIC-ER, AIC-PKPD}
(spec before_after_toy_example). AIC-MISSING -> Q11. Both inputs are external
(sponsor/protocol) boundary inputs — see issues/provenance_gaps.md GAP-4.
"""

import pandas as pd

VALID_A0_STATES = frozenset([
    "AIC-MISSING", "AIC-PK", "AIC-POPPK", "AIC-PKPD", "AIC-ER",
    "AIC-DDI", "AIC-PEDS", "AIC-SPECIAL", "AIC-CUSTOM",
])

_VALID_INTENTS = frozenset([
    "AIC-PK", "AIC-POPPK", "AIC-PKPD", "AIC-ER",
    "AIC-DDI", "AIC-PEDS", "AIC-SPECIAL", "AIC-CUSTOM",
])

# anchors.json endpoint_data_type_scope (SSOT)
_ENDPOINT_SCOPE = frozenset(["PK_CONCENTRATION", "EXPOSURE_METRIC", "CONTINUOUS_PD"])

# universe_sm §3 A0: endpoint required for these intents
_ENDPOINT_REQUIRED = frozenset(["AIC-PKPD", "AIC-ER"])

# endpoint-only fallback mapping (before_after_toy_example)
_ENDPOINT_TO_INTENT = {
    "PK_CONCENTRATION": "AIC-PK",
    "EXPOSURE_METRIC": "AIC-ER",
    "CONTINUOUS_PD": "AIC-PKPD",
}


def _norm_intent(val) -> str | None:
    if not isinstance(val, str):
        return None
    norm = val.strip().upper().replace("_", "-").replace(" ", "-")
    return norm or None


def _classify_a0(meta: dict) -> str:
    intent = _norm_intent(meta.get("analysis_intent"))
    edt = meta.get("endpoint_data_type")

    if intent in _VALID_INTENTS:
        if intent in _ENDPOINT_REQUIRED:
            return intent if edt in _ENDPOINT_SCOPE else "AIC-MISSING"
        if intent == "AIC-CUSTOM":
            return "AIC-CUSTOM" if meta.get("policy_document") else "AIC-MISSING"
        return intent

    if intent is None:
        return _ENDPOINT_TO_INTENT.get(edt, "AIC-MISSING")

    # intent declared but unrecognized (out-of-scope / hallucinated)
    return "AIC-MISSING"


def verify_a0_analysis_intent(df: pd.DataFrame, meta: dict) -> dict:
    state = _classify_a0(meta)
    meta["a0_state"] = state
    is_pass = state != "AIC-MISSING"
    route = None if is_pass else "Q11"
    return {"a0_state": state, "pass": is_pass, "route_to_q": route}
