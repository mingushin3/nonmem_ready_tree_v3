"""CLASSIFY REGIMEN_DESCRIPTOR — A2 연구 설계 분류

srp_intent: CLASSIFY REGIMEN_DESCRIPTOR
c_name_ko: A2 연구 설계 분류
kind: detect  (A2 axis classifier; df read-only)

postcondition_predicate:
    meta.get('a2_state') in ['PARALLEL','SAD-MAD','CROSSOVER','BE','DDI','FOOD-EFFECT','SPECIAL-POP','PEDIATRIC','TDM-RWD','PRECLINICAL']

Routing scope (can_route_to_q=[]): pure classifier. route_to_q는 항상 None, pass는 항상 True.
universe_sm §3 A2(L124-125)는 10개 state 모두 Q/INVALID 라우팅 주석이 없다(A1→Q05, A3→Q02/INVALID,
A4→Q14/Q08과 대조). 따라서 라우팅 scope 불일치가 없다(GAP-5/GAP-8과 다름).

입력 provenance: 선언 meta['study_design'](1차) → meta['protocol'](2차, clean token만)는 sponsor/
protocol 외부 경계 입력으로 생산 c가 없다(GAP-4 A0 / GAP-6 A1 동형). A2에는 UNKNOWN/MISSING state가
없어 선언 부재 시에도 df fallback이 deterministic하게 10개 중 하나를 반환해야 한다. df fallback은
period+sequence 컬럼 동시 존재 → CROSSOVER, 그 외 → PARALLEL 기본값만 구분 가능하며 나머지 8개 design은
선언 없이는 구분하지 못한다(문서화된 한계). 정확한 A2는 study_design 선언에 의존한다.
See issues/provenance_gaps.md GAP-9.
"""

import pandas as pd

VALID_A2_STATES = frozenset([
    "PARALLEL", "SAD-MAD", "CROSSOVER", "BE", "DDI",
    "FOOD-EFFECT", "SPECIAL-POP", "PEDIATRIC", "TDM-RWD", "PRECLINICAL",
])

# declared study-design descriptor -> a2_state (canonical + obvious aliases)
_DESIGN_TO_STATE = {
    "parallel": "PARALLEL",
    "sad-mad": "SAD-MAD",
    "sad": "SAD-MAD",
    "mad": "SAD-MAD",
    "crossover": "CROSSOVER",
    "be": "BE",
    "bioequivalence": "BE",
    "ddi": "DDI",
    "drug-drug-interaction": "DDI",
    "food-effect": "FOOD-EFFECT",
    "food": "FOOD-EFFECT",
    "special-pop": "SPECIAL-POP",
    "special-population": "SPECIAL-POP",
    "pediatric": "PEDIATRIC",
    "paediatric": "PEDIATRIC",
    "tdm-rwd": "TDM-RWD",
    "tdm": "TDM-RWD",
    "rwd": "TDM-RWD",
    "preclinical": "PRECLINICAL",
    "nonclinical": "PRECLINICAL",
}


def _norm_descriptor(val) -> str | None:
    if not isinstance(val, str):
        return None
    norm = val.strip().lower().replace("_", "-").replace(" ", "-")
    return norm or None


def _has_crossover_columns(df: pd.DataFrame) -> bool:
    # crossover fingerprint: both period and sequence columns present
    cols = {str(c).strip().lower() for c in df.columns}
    return "period" in cols and ("sequence" in cols or "seq" in cols)


def _classify_a2(df: pd.DataFrame, meta: dict) -> str:
    desc = _norm_descriptor(meta.get("study_design")) or _norm_descriptor(meta.get("protocol"))
    if desc in _DESIGN_TO_STATE:
        return _DESIGN_TO_STATE[desc]
    # df fallback (deterministic): only CROSSOVER vs PARALLEL distinguishable — GAP-9
    if _has_crossover_columns(df):
        return "CROSSOVER"
    return "PARALLEL"


def _route_a2(state: str, meta: dict):
    # can_route_to_q=[] : pure classifier, never routes (universe_sm §3 A2 no Q/INVALID)
    return None


def classify_regimen_descriptor(df: pd.DataFrame, meta: dict) -> dict:
    state = _classify_a2(df, meta)
    meta["a2_state"] = state
    route = _route_a2(state, meta)
    return {"a2_state": state, "pass": route is None, "route_to_q": route}
