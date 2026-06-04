"""CONVERT TIME_FORMAT — 시간 형식 변환 (L-4->L-5 mess)

srp_intent: CONVERT TIME_FORMAT
c_name_ko: 시간 형식 변환
kind: transform  (mess:TIME_FORMAT)

postcondition_predicate:
    df['time_value'].apply(lambda x: isinstance(x, (int, float))).all()

precondition_predicate:
    meta.get('time_format_detected') is not None and c0310_passed

감지된 형식(meta['time_format_detected'])에 따라 time_value를 numeric(elapsed hours)으로
파싱한다. clock 'H:MM[:SS]'→시간, decimal/elapsed→그대로 numeric, datetime→첫 시각 기준
elapsed hours. 결정적 변환 불가(mixed/미상/파싱 실패·부분 NaN)면 can_route_to_q=[Q02]대로
route Q02(silent no-op·부분 NaN 통과 금지). requires_detection_by=c0310(D-S1). df.copy()로
원본 불변. 이 numeric time_value가 c0203(a3_state)·c0019(ASSIGN TIME)의 상류 입력계약을
충족한다(GAP-18 종결).
"""

import re

import pandas as pd

_CLOCK_RE = re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$")


def _clock_to_hours(v):
    m = _CLOCK_RE.match(str(v).strip())
    if not m:
        return float("nan")
    h, mnt, sec = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    return h + mnt / 60.0 + sec / 3600.0


def convert_time_format(df: pd.DataFrame, meta: dict) -> dict:
    fmt = meta.get("time_format_detected")
    out = df.copy()
    col = out["time_value"]
    if fmt == "clock":
        parsed = col.apply(_clock_to_hours)
    elif fmt in ("decimal", "elapsed"):
        parsed = pd.to_numeric(col, errors="coerce")
    elif fmt == "datetime":
        dt = pd.to_datetime(col, errors="coerce")
        parsed = (dt - dt.min()).dt.total_seconds() / 3600.0
    else:
        # mixed/미상 → 결정적 변환 불가 → Q02 (fail branch, conditional)
        return {"df": df, "success": False, "route_to_q": "Q02"}
    if parsed.isna().any():
        return {"df": df, "success": False, "route_to_q": "Q02"}
    out["time_value"] = parsed.astype(float)
    return {"df": out, "success": True, "route_to_q": None}
