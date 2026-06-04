"""DETECT ENCODING — 인코딩 문제 감지 (A9 보조)

srp_intent: DETECT ENCODING
c_name_ko: 인코딩 문제 감지 (A9 보조)
kind: detect  (A9 ENCODING-FIX helper; df read-only)

postcondition_predicate:
    isinstance(meta.get('has_encoding_issues'), bool)

precondition_predicate:
    len(df) > 0

Routing scope (can_route_to_q=[]): route_to_q 항상 None, pass 항상 True. A9 평가 시
ENCODING-FIX state 결정을 위한 보조 정보(Phase 2d 인코딩 정규화 후 잔존 결함 확인). 문자열
컬럼 값에 비-ASCII([^\\x00-\\x7F])가 있으면 True; 문자열 컬럼 부재면 False(점검 대상 없음, 날조 금지).
★ has_encoding_issues는 Python bool 캐스팅(numpy.bool_은 isinstance(.,bool)=False라 postcond 위반).
"""

import pandas as pd

_NON_ASCII = r"[^\x00-\x7F]"


def detect_encoding(df: pd.DataFrame, meta: dict) -> dict:
    # 모든 컬럼을 str로 캐스팅해 비-ASCII 점검 — 숫자 컬럼은 ASCII로 캐스팅돼 no-op이므로
    # snippet의 string_cols 제한과 결과 동치이며, pandas3 select_dtypes('object') deprecation을 회피한다.
    flag = bool(any(
        df[col].astype(str).str.contains(_NON_ASCII, regex=True).any()
        for col in df.columns
    ))
    meta["has_encoding_issues"] = flag
    return {"has_encoding_issues": flag, "pass": True, "route_to_q": None}

