"""CONVERT TIME_ANCHOR — 시간 기준점 파싱 (L-4->L-5 mess)

srp_intent: CONVERT TIME_ANCHOR
c_name_ko: 시간 기준점 파싱
kind: transform  (mess:TIME_ANCHOR)

postcondition_predicate:
    df.get('time_anchor_parsed', pd.Series()).notna().all() if 'time_anchor_parsed' in df.columns else True

precondition_predicate:
    c0314_passed

time_anchor 토큰을 comparable 수치(elapsed hours)로 파싱해 df['time_anchor_parsed'] 생성.
'Day N'→(N-1)*24h, 'Visit/Week/Cycle N'→(N-1)*168h, 이미 numeric→그대로. time_anchor 컬럼이
없으면 변환 대상 없음(postcond vacuous True). 파싱 실패(절대날짜 등 비교 불가 혼재로 부분 NaN)면
can_route_to_q=[Q02]대로 route Q02(부분 NaN parsed 통과 금지 — postcond notna 강제).
requires_detection_by=c0314(D-S1). df.copy()로 원본 불변.
"""

import re

import pandas as pd

_DAY_RE = re.compile(r"day\s*(\d+)", re.IGNORECASE)
_PERIOD_RE = re.compile(r"(?:visit|week|cycle)\s*(\d+)", re.IGNORECASE)


def _anchor_to_hours(token):
    s = str(token).strip()
    m = _DAY_RE.search(s)
    if m:
        return (int(m.group(1)) - 1) * 24.0
    m = _PERIOD_RE.search(s)
    if m:
        return (int(m.group(1)) - 1) * 24.0 * 7
    try:
        return float(s)
    except ValueError:
        return float("nan")


def convert_time_anchor(df: pd.DataFrame, meta: dict) -> dict:
    out = df.copy()
    if "time_anchor" not in out.columns:
        # 파싱 대상 컬럼 없음 → 변환 없음(postcond vacuous True)
        return {"df": out, "success": True, "route_to_q": None}
    parsed = out["time_anchor"].apply(_anchor_to_hours)
    if parsed.isna().any():
        return {"df": df, "success": False, "route_to_q": "Q02"}
    out["time_anchor_parsed"] = parsed.astype(float)
    return {"df": out, "success": True, "route_to_q": None}
