"""DETECT TIMEZONE — 시간대 감지 (L-4->L-5 mess)

srp_intent: DETECT TIMEZONE
c_name_ko: 시간대 감지
kind: detect  (mess:TIMEZONE; df read-only)

postcondition_predicate:
    isinstance(meta.get('tz_issues'), dict)

precondition_predicate:
    'time_value' in df.columns

time_value 문자열의 trailing 시간대 토큰(KST/JST/UTC 등 known set)을 수집해 시간대 불일치를
meta['tz_issues'] dict로 산출한다(has_mixed_tz / tz_tokens / n_distinct_tz). 토큰이 둘 이상이면
has_mixed_tz=True. 토큰 부재(numeric time_value 등)면 빈 집합 → has_mixed_tz=False(날조 없이 부재
표기). can_route_to_q=[] → route_to_q 항상 None(pass→c0313). 하류 c0313(NORMALIZE TIMEZONE)의
requires_detection_by=c0312(D-S1 cut-vertex). 시간대 offset 상수표는 c0313과 공유(_TZ_OFFSETS).
"""

import pandas as pd

# 시간대 → UTC offset(hours). c0313 정규화와 공유하는 결정적 상수표(Lock 3 deterministic).
_TZ_OFFSETS = {
    "UTC": 0.0, "GMT": 0.0, "Z": 0.0,
    "KST": 9.0, "JST": 9.0,
    "EST": -5.0, "EDT": -4.0, "CST": -6.0, "CDT": -5.0,
    "MST": -7.0, "PST": -8.0, "PDT": -7.0,
    "CET": 1.0, "CEST": 2.0, "BST": 1.0, "IST": 5.5,
}


def _extract_tz(v):
    """단일 time_value의 trailing 시간대 토큰(known set만). 부재/미상이면 None."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    parts = str(v).strip().split()
    if parts and parts[-1].upper() in _TZ_OFFSETS:
        return parts[-1].upper()
    return None


def detect_timezone(df: pd.DataFrame, meta: dict) -> dict:
    tokens = sorted({tz for tz in (_extract_tz(v) for v in df["time_value"]) if tz})
    tz_issues = {
        "has_mixed_tz": len(tokens) > 1,
        "tz_tokens": tokens,
        "n_distinct_tz": len(tokens),
    }
    meta["tz_issues"] = tz_issues
    return {"tz_issues": tz_issues, "pass": True, "route_to_q": None}
