"""navigator — precondition-gated DETECT 서브시퀀스 + run_strand(무수정) 호출.

★ 핵심 정직성 규칙: run_strand는 precondition 위반에 raise하지 않는다(SliceBoundary만 잡음).
  detector는 조용히 degrade한다(c0203은 time_value 없으면 a3_state='UNRECOVERABLE' 날조).
  따라서 precondition gate는 **navigator가 스스로** 건다 — run_strand에 위임하지 않는다(D-G2).

Fork 1(사용자 승인): faithful tidy df를 못 만들면(honest-stop) **file-property 축
c0201(A1)·c0210(A10)만** dispatch한다 — 둘은 conc/dv/time 무관(cite-verify:
  c0201 input_schema='file inventory, study metadata' · c0210 input_schema='file metadata,
  format indicators', docstring "df 생기기 전 맨 앞 게이트"). conc 의존 detector는 전부 제외.

navigable band(전원 requires_detection_by=None → D-S1 gate 무, RuntimeError 무): 13개.
"""

# Fork 1: conc/dv/time 무관(file-property) — honest-stop에서도 dispatch
_FILE_PROPERTY = ("c0201", "c0210")
# conc/data 의존 — faithful tidy df가 있을 때만 dispatch
_DATA_DEPENDENT = ("c0203", "c0205", "c0211", "c0212", "c0214", "c0215", "c0216",
                   "c0305", "c0310", "c0312", "c0314")
_CANON_ORDER = ("c0201", "c0203", "c0205", "c0210", "c0211", "c0212", "c0214",
                "c0215", "c0216", "c0305", "c0310", "c0312", "c0314")


def _nonempty(df):
    return df is not None and len(df) > 0


def _has(df, *cols):
    return df is not None and all(c in df.columns for c in cols)


def _precondition_ok(c_id: str, df, meta: dict) -> bool:
    """각 c의 precondition을 cite-verify된 표대로 navigator가 직접 평가."""
    if c_id == "c0201":                       # len(df)>0 (study metadata descriptor-driven)
        return _nonempty(df)
    if c_id == "c0210":                       # len(df)>0 or file_exists
        return _nonempty(df) or bool(meta.get("file_exists"))
    if c_id in ("c0214", "c0215", "c0216", "c0314"):   # len(df)>0
        return _nonempty(df)
    if c_id == "c0203":                       # 'time_value' or 'TIME' in df
        return df is not None and ("time_value" in df.columns or "TIME" in df.columns)
    if c_id in ("c0310", "c0312"):            # 'time_value' in df (hard)
        return _has(df, "time_value")
    if c_id in ("c0205", "c0211", "c0305"):   # dv_value/DV/dv in df
        return df is not None and any(x in df.columns for x in ("dv_value", "DV", "dv"))
    if c_id == "c0212":                       # subject_id + time_value + dv_value (tightest)
        return _has(df, "subject_id", "time_value", "dv_value")
    return False


def choose_detect_sequence(df, meta: dict, faithful_tidy: bool) -> list:
    """precondition-gated DETECT 서브시퀀스(canonical order). honest-stop이면 file-property만."""
    chosen = {c for c in _FILE_PROPERTY if _precondition_ok(c, df, meta)}
    if faithful_tidy:
        chosen |= {c for c in _DATA_DEPENDENT if _precondition_ok(c, df, meta)}
    return [c for c in _CANON_ORDER if c in chosen]


def navigate(df, meta: dict, faithful_tidy: bool) -> dict:
    """엔진 run_strand를 무수정 호출. df+meta를 그대로 태운다."""
    from src.orchestrator import run_strand  # lazy: import src.adapter 자체는 엔진 import 무유발
    seq = choose_detect_sequence(df, meta, faithful_tidy)
    record = run_strand(seq, df, meta=meta, stop_at_boundary=True)
    return {"c_sequence": seq, "run_strand_record": record}
