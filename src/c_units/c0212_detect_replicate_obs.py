"""DETECT REPLICATE_OBS — 반복 관측 감지 (A5 P3 sub-pattern)

srp_intent: DETECT REPLICATE_OBS
c_name_ko: 반복 관측 감지
kind: detect  (A5 REPLICATE-SAME-TIME sub-detector; df read-only)

postcondition_predicate:
    isinstance(meta.get('has_replicates'), bool)

precondition_predicate:
    'subject_id' in df.columns and 'time_value' in df.columns and 'dv_value' in df.columns

Routing scope (can_route_to_q=[Q01]): route_to_q ∈ {None, Q01}. 같은 (ID,TIME)에 유효 DV가
≥2이고 값이 서로 달라 정당 replicate면(정책 부재 시 REPLICATE-NO-POLICY) → Q01; 정책 있으면
REPLICATE-SAME-TIME(REPAIR, route None); 없으면 pass(→c0205).
★ DUPLICATE-EXACT(전체 행 일치, A9/c0215 소관)과 구분 — exact 중복은 dedup 후 1행이 되어
replicate로 세지 않는다(날조 금지). ★ has_replicates는 Python bool 캐스팅(np.bool_ 차단).
★ runtime Q01 라우팅 실주체는 c0253; can_route_to_q=[Q01]은 Phase 7 D-S4 선언(GAP-28 동형).
"""

import pandas as pd


_NEEDED = ("subject_id", "time_value", "dv_value")


def _has_replicates(df: pd.DataFrame, meta: dict) -> bool:
    # 필요한 컬럼이 없으면 replicate 판정 불가 → False(silent-error 0, 날조 금지).
    if not set(_NEEDED).issubset(df.columns):
        return False
    obs = df[df["dv_value"].notna()]
    if obs.empty:
        return False
    # 전체 행 일치(DUPLICATE-EXACT)는 제거 후 같은 (ID,TIME) ≥2 = 정당 replicate
    dedup = obs.drop_duplicates()
    sizes = dedup.groupby(["subject_id", "time_value"]).size()
    return bool((sizes >= 2).any())


def detect_replicate_obs(df: pd.DataFrame, meta: dict) -> dict:
    flag = _has_replicates(df, meta)
    meta["has_replicates"] = flag
    route = "Q01" if flag and not meta.get("replicate_policy") else None
    return {"has_replicates": flag, "pass": route is None, "route_to_q": route}
