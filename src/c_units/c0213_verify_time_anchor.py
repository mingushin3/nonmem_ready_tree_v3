"""VERIFY TIME_ANCHOR — 시간 기준점 검증 (A3 보조)

srp_intent: VERIFY TIME_ANCHOR
c_name_ko: 시간 기준점 검증
kind: verify  (A3 time anchor sub-check; df read-only)

postcondition_predicate:
    meta.get('time_anchor_consistent', True)

precondition_predicate:
    'time_anchor' in meta or 'time_value' in df.columns

Routing scope (can_route_to_q=[Q02]): route_to_q ∈ {None, Q02}. 시간 기준점이
일관·해석가능하면 pass(→c0203), 유형이 혼재('Day 1'·'Visit 1'·절대날짜 등 mixed)하면
inconsistent → Q02. 우선순위: declared meta['time_anchor_consistent'](bool) >
meta['time_anchor'] 토큰 유형 일관성 > df 'time_anchor' 컬럼 fallback. 앵커 토큰이
하나도 없으면(time_value만) 기본 consistent=True(날조 금지, scope-out).
time_anchor는 sponsor/protocol 외부 경계 입력 — issues/provenance_gaps.md GAP-7.
"""

import re

import pandas as pd

# YYYY-M-D 또는 D/M/Y · D.M.Y 형태의 절대 날짜
_DATE_RE = re.compile(r"\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/.]\d{1,2}[/.]\d{2,4}")


def _anchor_type(token) -> str | None:
    """anchor 토큰을 유형으로 분류. 분류 불가/공백이면 None(집계 제외)."""
    if token is None:
        return None
    s = str(token).strip().lower()
    if not s:
        return None
    if _DATE_RE.search(s):
        return "absolute-date"
    if "visit" in s or "cycle" in s or "week" in s:
        return "period-relative"
    if "day" in s:
        return "day-relative"
    try:
        float(s)
        return "numeric"
    except ValueError:
        return "other"


def _anchor_tokens(df: pd.DataFrame, meta: dict) -> list:
    """meta['time_anchor'] 선언(1차) → df 'time_anchor' 컬럼(2차)에서 토큰 수집."""
    raw = meta.get("time_anchor")
    if raw is not None:
        return list(raw) if isinstance(raw, (list, tuple)) else [raw]
    if "time_anchor" in df.columns:
        return [v for v in df["time_anchor"].dropna().unique()]
    return []


def _check_time_anchor_consistency(df: pd.DataFrame, meta: dict) -> bool:
    declared = meta.get("time_anchor_consistent")
    if isinstance(declared, bool):
        return declared
    types = {t for t in (_anchor_type(tok) for tok in _anchor_tokens(df, meta)) if t}
    # 유형이 둘 이상 혼재하면 비일관(해석 불가). 토큰 부재/단일유형이면 일관(날조 금지).
    return len(types) <= 1


def verify_time_anchor(df: pd.DataFrame, meta: dict) -> dict:
    consistent = _check_time_anchor_consistency(df, meta)
    meta["time_anchor_consistent"] = consistent
    route = None if consistent else "Q02"
    return {"time_anchor_consistent": consistent, "pass": route is None, "route_to_q": route}
