"""NORMALIZE TIMEZONE — 시간대 정규화 (L-4->L-5 mess)

srp_intent: NORMALIZE TIMEZONE
c_name_ko: 시간대 정규화
kind: transform  (mess:TIMEZONE)

postcondition_predicate:
    meta.get('tz_normalized', True)

precondition_predicate:
    c0312_passed

★ verbatim postcond는 default=True라 flag 미설정 no-op도 vacuously 통과한다(silent error 위험,
GAP-27; GAP-3/21(C) 동형). spec frozen(토큰 변경 금지) — 대신 구현이 silent/vacuous no-op을
구조적으로 차단한다:
  (1) tz_issues 존재 + 토큰 ≥1 : 모든 time_value를 단일 target tz로 실제 변환, 변환 성공 시에만
      meta['tz_normalized']=True. (DST/offset = _TZ_OFFSETS 결정적, Lock 3)
  (2) 정규화 대상 부재(토큰 0) : 정당한 idempotent — flag 설정 + success(부재≠silent no-op,
      c0311 edge 'already-numeric' 동형).
  (3) requires_detection_by(c0312) 산출물 meta['tz_issues'] 부재 : 감지 미선행 → success=False,
      route_to_q=None(can_route_to_q=[] → Q 날조 금지, GAP-21(C) 선례). flag 미설정.
target tz = meta['tz_target'](유효 시) > 'UTC' 존재 시 'UTC' > sorted(tokens)[0] (결정적). df.copy()로
원본 불변. 파싱 불가 시각이 토큰과 함께 있으면 결정적 변환 불가 → success=False(no Q).
"""

import re

import pandas as pd

from src.c_units.c0312_detect_timezone import _TZ_OFFSETS, _extract_tz

_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$")
_DAY = 24 * 60


def _to_minutes(timestr: str):
    """'HH:MM[:SS]' → 자정 기준 분(float). 미상이면 None."""
    m = _TIME_RE.match(timestr.strip())
    if not m:
        return None
    h, mi, se = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    return h * 60 + mi + se / 60.0


def _choose_target(tokens, meta):
    declared = meta.get("tz_target")
    if isinstance(declared, str) and declared.upper() in _TZ_OFFSETS:
        return declared.upper()
    if "UTC" in tokens:
        return "UTC"
    return tokens[0] if tokens else None


def _convert_one(v, target):
    """tokened 'HH:MM TZ' → target tz로 변환한 'HH:MM TARGET'. 토큰 없으면 원본 유지.
    토큰 있으나 시각 파싱 불가면 None(결정적 변환 불가 신호)."""
    tz = _extract_tz(v)
    if tz is None:
        return v  # 토큰 부재 → 변환 대상 아님(원본 유지)
    parts = str(v).strip().split()
    local = _to_minutes(" ".join(parts[:-1]))
    if local is None:
        return None  # 토큰 有 + 시각 파싱 불가 → 비결정 → fail 신호
    utc = local - _TZ_OFFSETS[tz] * 60
    tgt = (utc + _TZ_OFFSETS[target] * 60) % _DAY
    h, mi = int(tgt // 60), int(round(tgt % 60))
    if mi == 60:  # 반올림 경계 보정
        h, mi = (h + 1) % 24, 0
    return f"{h:02d}:{mi:02d} {target}"


def normalize_timezone(df: pd.DataFrame, meta: dict) -> dict:
    issues = meta.get("tz_issues")
    if not isinstance(issues, dict):
        # (3) 감지(c0312) 미선행 → silent no-op 금지: 실패 신호(Q 날조 없음)
        return {"df": df, "success": False, "route_to_q": None}

    out = df.copy()
    tokens = sorted({tz for tz in (_extract_tz(v) for v in out["time_value"]) if tz})
    if not tokens:
        # (2) 정규화 대상 부재 → 정당한 idempotent
        meta["tz_normalized"] = True
        return {"df": out, "success": True, "route_to_q": None}

    target = _choose_target(tokens, meta)
    converted = out["time_value"].apply(lambda v: _convert_one(v, target))
    if converted.isna().any():
        # 토큰 有 + 비결정 변환 → silent no-op/부분 변환 금지
        return {"df": df, "success": False, "route_to_q": None}

    out["time_value"] = converted
    meta["tz_normalized"] = True
    return {"df": out, "success": True, "route_to_q": None}
