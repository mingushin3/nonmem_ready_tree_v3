"""CLASSIFY ANALYTE_COLUMN — A8 다약물/CMT 평가

srp_intent: CLASSIFY ANALYTE_COLUMN
c_name_ko: A8 다약물/CMT 평가

postcondition_predicate:
    meta.get('a8_state') in ['SINGLE-DRUG','MULTI-CMT-DEFINED','DDI-VICTIM-ONLY','DDI-VICTIM-PERPETRATOR','METABOLITE-DEFINED','CMT-POLICY-MISSING']
"""

import pandas as pd

VALID_A8_STATES = frozenset([
    "SINGLE-DRUG",
    "MULTI-CMT-DEFINED",
    "DDI-VICTIM-ONLY",
    "DDI-VICTIM-PERPETRATOR",
    "METABOLITE-DEFINED",
    "CMT-POLICY-MISSING",
])


def _count_unique_analytes(df: pd.DataFrame) -> int:
    if "analyte_label" not in df.columns:
        return 1
    labels = df["analyte_label"].dropna().str.strip().str.lower()
    n = labels.nunique()
    return max(n, 1)


def _count_unique_routes(df: pd.DataFrame) -> int:
    if "admin_route" not in df.columns:
        return 1
    routes = df["admin_route"].dropna().str.strip().str.lower()
    n = routes.nunique()
    return max(n, 1)


def _perpetrator_present_in_df(df: pd.DataFrame, perpetrator_analytes: list) -> bool:
    if not perpetrator_analytes:
        return False
    if "analyte_label" not in df.columns:
        return False
    df_analytes = set(df["analyte_label"].dropna().str.strip().str.lower())
    perp_set = {a.strip().lower() for a in perpetrator_analytes}
    return bool(df_analytes & perp_set)


def _metabolite_present_in_df(df: pd.DataFrame, parent_metabolite_map: dict) -> bool:
    if not parent_metabolite_map:
        return False
    if "analyte_label" not in df.columns:
        return False
    metabolite_names = {
        k.strip().lower()
        for k, v in parent_metabolite_map.items()
        if v == "metabolite"
    }
    if not metabolite_names:
        return False
    df_analytes = set(df["analyte_label"].dropna().str.strip().str.lower())
    return bool(df_analytes & metabolite_names)


def _make_result(state: str) -> dict:
    is_pass = state != "CMT-POLICY-MISSING"
    route = "Q09" if not is_pass else None
    return {"a8_state": state, "pass": is_pass, "route_to_q": route}


def classify_analyte_column(df: pd.DataFrame, meta: dict) -> dict:
    # Step 1: DDI (highest priority — study-level property)
    if meta.get("study_type") == "DDI":
        perp_list = meta.get("perpetrator_analytes", [])
        if perp_list and _perpetrator_present_in_df(df, perp_list):
            state = "DDI-VICTIM-PERPETRATOR"
        else:
            state = "DDI-VICTIM-ONLY"
        meta["a8_state"] = state
        return _make_result(state)

    # Step 2: Metabolite
    pm_map = meta.get("parent_metabolite_map", {})
    if pm_map and _metabolite_present_in_df(df, pm_map):
        state = "METABOLITE-DEFINED"
        meta["a8_state"] = state
        return _make_result(state)

    # Step 3: Count analytes and routes
    n_analytes = _count_unique_analytes(df)
    n_routes = _count_unique_routes(df)

    # Step 4: Single drug
    if n_analytes <= 1 and n_routes <= 1:
        state = "SINGLE-DRUG"
        meta["a8_state"] = state
        return _make_result(state)

    # Step 5: Multi-CMT with policy
    cmt_map = meta.get("cmt_map", {})
    if cmt_map and len(cmt_map) > 0:
        state = "MULTI-CMT-DEFINED"
        meta["a8_state"] = state
        return _make_result(state)

    # Step 6: Fallback — no policy
    state = "CMT-POLICY-MISSING"
    meta["a8_state"] = state
    return _make_result(state)
