"""DETECT TIME_ANCHOR — 시간 기준점 감지 (L-4->L-5 mess)

srp_intent: DETECT TIME_ANCHOR
c_name_ko: 시간 기준점 감지
kind: detect  (mess:TIME_ANCHOR; df read-only)

postcondition_predicate:
    meta.get('time_anchor_type') is not None

precondition_predicate:
    len(df) > 0

앵커 토큰을 유형(day-relative/period-relative/absolute-date/numeric)으로 분류해
meta['time_anchor_type'] 설정. 둘 이상 혼재면 'mixed', 토큰 부재면 'none'(None 아님 —
postcond는 not None이며, 부재를 'none' 문자열로 정직 표기·날조 금지). 선언 meta['time_anchor_type']
있으면 우선. 토큰 출처: meta['time_anchor'](1차) → df 'time_anchor' 컬럼(2차). can_route_to_q=[]
→ route None(pass→c0315).
"""

import re

import pandas as pd

_DATE_RE = re.compile(r"\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/.]\d{1,2}[/.]\d{2,4}")


def _token_type(token):
    if token is None or (isinstance(token, float) and pd.isna(token)):
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
    raw = meta.get("time_anchor")
    if raw is not None:
        return list(raw) if isinstance(raw, (list, tuple)) else [raw]
    if "time_anchor" in df.columns:
        return [v for v in df["time_anchor"].dropna().unique()]
    return []


def detect_time_anchor(df: pd.DataFrame, meta: dict) -> dict:
    declared = meta.get("time_anchor_type")
    if isinstance(declared, str) and declared.strip():
        atype = declared.strip()
    else:
        types = {t for t in (_token_type(tok) for tok in _anchor_tokens(df, meta)) if t}
        if not types:
            atype = "none"
        elif len(types) > 1:
            atype = "mixed"
        else:
            atype = next(iter(types))
    meta["time_anchor_type"] = atype
    return {"time_anchor_type": atype, "pass": True, "route_to_q": None}
