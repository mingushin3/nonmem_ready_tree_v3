"""column_canonicalizer — 실물 컬럼명 → 엔진 canonical 명({time_value,dv_value,subject_id}).

wired DETECT 밴드가 읽는 정확한 컬럼명(코드 확인):
  time_value (c0203/c0310/c0312/c0314/c0212) · dv_value (c0205/c0305/c0211/c0212) ·
  subject_id (c0212, 별칭 없음). dose/amt 컬럼은 밴드 내 소비자 없음 → 만들지 않는다.

★ rename만 — melt/pivot로 dv_value를 조립하지 않는다(subject-wide는 ingester가 이미 df=None).
충실 매핑 불가하면 missing에 기록(navigator가 precondition-gate). 날조 0.
"""
import re

_TIME = re.compile(r"(time|tad|tafd|시간|nominal)", re.I)
_DV = re.compile(r"(conc|concentration|\bdv\b|농도|observation)", re.I)
_SUBJ = re.compile(r"(subject|animal|개체|동물|^id$)", re.I)
_CANON = ("time_value", "dv_value", "subject_id")


def canonicalize(df, structure: dict | None = None):
    """(df_renamed, report). df=None이면 (None, missing 전부)."""
    if df is None:
        return None, {"mapped": {}, "missing": list(_CANON), "reason": "df 없음"}
    rename = {}
    taken = set()
    for col in df.columns:
        cl = str(col)
        if "time_value" not in taken and _TIME.search(cl):
            rename[col], _ = "time_value", taken.add("time_value")
        elif "dv_value" not in taken and _DV.search(cl):
            rename[col], _ = "dv_value", taken.add("dv_value")
        elif "subject_id" not in taken and _SUBJ.search(cl):
            rename[col], _ = "subject_id", taken.add("subject_id")
    out = df.rename(columns=rename)
    return out, {
        "mapped": {v: k for k, v in rename.items()},
        "missing": [c for c in _CANON if c not in out.columns],
    }
