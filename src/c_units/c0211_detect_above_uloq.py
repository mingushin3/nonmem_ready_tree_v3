"""DETECT ABOVE_ULOQ — ULOQ 초과 관측 감지 (A5 P1 sub-pattern)

srp_intent: DETECT ABOVE_ULOQ
c_name_ko: ULOQ 초과 관측 감지
kind: detect  (A5 ABOVE-ULOQ sub-detector; df read-only)

postcondition_predicate:
    isinstance(meta.get('has_above_uloq'), bool)

precondition_predicate:
    'dv_value' in df.columns or 'DV' in df.columns

Routing scope (can_route_to_q=[Q01]): route_to_q ∈ {None, Q01}. ULOQ 초과 관측이 감지되고
(>ULOQ 토큰 또는 dv_value > meta['uloq']) policy가 없으면(ABOVE-ULOQ-NO-POLICY) → Q01(subtype
uloq); policy 있으면 ABOVE-ULOQ(REPAIR, route None); 초과 없으면 pass(→c0205).
★ has_above_uloq는 Python bool로 캐스팅 — numpy.bool_은 isinstance(.,bool)=False라 postcond 위반.
★ '>100' 같은 토큰 표기는 숫자 비교만으로는 silent miss → 토큰 경로를 먼저 점검(날조 금지).
★ runtime Q01 라우팅 실주체는 c0253(A5 ROUTE); 본 can_route_to_q=[Q01]은 Phase 7 D-S4 선언
(GAP-28 동형). uloq/uloq_policy는 외부 경계 입력(① meta 주입 소관, GAP-30).
"""

import pandas as pd

_DV_COLS = ("dv_value", "DV", "dv")


def _dv_column(df: pd.DataFrame):
    return next((c for c in _DV_COLS if c in df.columns), None)


def _has_above_uloq(df: pd.DataFrame, meta: dict) -> bool:
    col = _dv_column(df)
    if col is None:
        return False
    series = df[col].dropna()
    if series.empty:
        return False
    # 토큰 경로: '>'-접두 표기(예: '>100', '> ULOQ') — 숫자 비교로는 놓침
    tokens = series.astype(str).str.strip()
    if tokens.str.startswith(">").any():
        return True
    # 숫자 경로: dv_value > uloq (uloq 선언 시에만; 날조 금지)
    uloq = meta.get("uloq")
    if uloq is not None:
        numeric = pd.to_numeric(series, errors="coerce")
        return bool((numeric > uloq).any())
    return False


def detect_above_uloq(df: pd.DataFrame, meta: dict) -> dict:
    flag = _has_above_uloq(df, meta)
    meta["has_above_uloq"] = flag
    route = "Q01" if flag and not meta.get("uloq_policy") else None
    return {"has_above_uloq": flag, "pass": route is None, "route_to_q": route}
