"""DETECT BLQ_TOKEN — BLQ 토큰 감지 (mess 층 L-4->L-5)

srp_intent: DETECT BLQ_TOKEN
c_name_ko: BLQ 토큰 감지
kind: detect  (mess 층 L-4->L-5; df read-only, meta에 변종/LLOQ 기록)

postcondition_predicate:
    isinstance(meta.get('blq_variants_found'), list)

함수명 detect_blq_token_mess — c0205 detect_blq_token(L-3->L-4 A5 축 평가)와 구분.
c0205(A5 axis: a5_state 분류·정책 라우팅)와 달리 본 c는 mess 층에서 BLQ *토큰 변종*의
존재와 numeric LLOQ 값을 감지한다(하류 c0306 NORMALIZE의 trigger; verify_visualization
pass_route_to=c0306). can_route_to_q=[] — 감지만 하고 라우팅은 A5 축(c0205/c0253) 소관.
★ postcond는 list-타입만 검사(빈 []도 통과) — 토큰이 실재하는데 silent []면 vacuous(GAP-27 패턴).
  trap fixture가 실재 토큰의 실제 감지를 behavioral하게 강제(silent-miss 차단).
ref: universe_sm §6 BLQ_TOKEN
"""

import re

import pandas as pd

_DV_COLS = ("dv_value", "DV", "dv")
# spec python_snippet 패턴(re.I). c0306 postcond·c0306 mask와 동일 토큰 어휘.
_BLQ_PATTERN = re.compile(r"<|BLQ|ND|LOD|이하", re.I)
_NUM_PATTERN = re.compile(r"[\d.]+")


def _dv_column(df: pd.DataFrame):
    return next((c for c in _DV_COLS if c in df.columns), None)


def detect_blq_token_mess(df: pd.DataFrame, meta: dict) -> dict:
    col = _dv_column(df)
    if col is None:
        variants: list = []
        lloq_values: list = []
    else:
        s = df[col].astype(str)
        hit = s[s.str.contains(_BLQ_PATTERN, na=False)]
        variants = hit.unique().tolist()
        lloq_values = []
        for v in variants:
            m = _NUM_PATTERN.search(v)
            if m:
                try:
                    lloq_values.append(float(m.group()))
                except ValueError:
                    pass
    meta["blq_variants_found"] = variants
    meta["lloq_values"] = lloq_values
    return {
        "blq_variants_found": variants,
        "lloq_values": lloq_values,
        "pass": True,
        "route_to_q": None,
    }
