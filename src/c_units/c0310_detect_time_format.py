"""DETECT TIME_FORMAT — 시간 형식 감지 (L-4->L-5 mess)

srp_intent: DETECT TIME_FORMAT
c_name_ko: 시간 형식 감지
kind: detect  (mess:TIME_FORMAT; df read-only)

postcondition_predicate:
    meta.get('time_format_detected') in ['clock','elapsed','decimal','datetime','mixed']

precondition_predicate:
    'time_value' in df.columns

함수명 detect_time_format_mess — c0203(DETECT TIME_FORMAT, L-3->L-4 축 a3_state 분류기,
detect_time_format)와 동음이의 srp이나 layer·역할이 다르다(c0310은 L-5 표기형식 유형 감지).
Phase 6 semantic merge 후보(현재 별개 유지). 선언 meta['time_format'](∈5형식) 있으면 우선,
없으면 값별 형식 분류 후 유형이 둘 이상이면 'mixed'(naive 첫값-추정 차단). can_route_to_q=[]
→ route_to_q 항상 None(pass→c0311).
"""

import re

import pandas as pd

_FORMATS = frozenset(["clock", "elapsed", "decimal", "datetime", "mixed"])
_CLOCK_RE = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$")
_DATE_RE = re.compile(r"\d{4}-\d{1,2}-\d{1,2}|\d{1,2}[/.]\d{1,2}[/.]\d{2,4}")


def _value_format(v):
    """단일 시간값의 표기 형식. 미상/공백이면 None(집계 제외)."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    s = str(v).strip()
    if not s:
        return None
    if _CLOCK_RE.match(s):
        return "clock"
    if _DATE_RE.search(s):
        return "datetime"
    try:
        float(s)
        return "decimal"
    except ValueError:
        return None


def detect_time_format_mess(df: pd.DataFrame, meta: dict) -> dict:
    declared = meta.get("time_format")
    if isinstance(declared, str) and declared.strip().lower() in _FORMATS:
        fmt = declared.strip().lower()
    else:
        formats = {f for f in (_value_format(v) for v in df["time_value"]) if f}
        if len(formats) > 1:
            fmt = "mixed"
        elif len(formats) == 1:
            fmt = next(iter(formats))
        else:
            fmt = "decimal"  # 식별 불가/빈 컬럼 → 기본 numeric(postcond 충족, 형식 날조 최소화)
    meta["time_format_detected"] = fmt
    return {"time_format_detected": fmt, "pass": True, "route_to_q": None}
