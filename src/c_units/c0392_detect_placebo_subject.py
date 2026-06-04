"""DETECT PLACEBO_SUBJECT — 위약군 피험자 감지 (L-4->L-5 mess)

srp_intent: DETECT PLACEBO_SUBJECT
c_name_ko: 위약군 피험자 감지
kind: detect  (mess:PLACEBO_SUBJECT; df read-only)

postcondition_predicate:
    isinstance(meta.get('has_placebo'), bool)

precondition_predicate:
    len(df) > 0

위약(placebo) 피험자 존재 여부를 식별만 한다(분류/태깅은 c0393 소관). 핵심 구분(verify_visualization
criterion): **AMT=0(의도적 위약) vs dose 누락(데이터 결함)**. dose_amount==0 이 있으면 has_placebo=True,
누락(NaN)은 placebo가 아니다 — NaN==0 은 False 이므로 비교가 자연히 구분한다(mess_catalog M103/M104=AMT=0
→ placebo, M105=dose 행 부재 → placebo 아님).
postcond는 타입(bool) 멤버십만 검사 → has_placebo를 False/True로 하드코딩하면 vacuous 통과가 구조상 가능하나,
trap(누락 dose를 placebo로 오판 금지 / AMT=0를 놓치지 않음)·adversarial이 실제 감지를 강제한다. can_route_to_q=[]
→ route_to_q 항상 None(pass→c0393). 하류 c0393(CLASSIFY)의 requires_detection_by=c0392(D-S1 cut-vertex).
★ (series==0).any()는 numpy.bool_ 을 돌려줘 isinstance(...,bool)이 False가 된다 → bool()로 캐스팅 필수.
dose_amount는 raw에서 문자열일 수 있어 pd.to_numeric(errors='coerce')로 정규화(누락/비수치 → NaN, snippet의
충실하되 견고한 표현). df read-only(detect SRP).
"""

import pandas as pd


def detect_placebo_subject(df: pd.DataFrame, meta: dict) -> dict:
    if "dose_amount" in df.columns:
        # AMT=0 존재 여부만 본다. NaN(누락)==0 → False 이므로 dose 누락은 placebo로 집계되지 않음.
        has = bool((pd.to_numeric(df["dose_amount"], errors="coerce") == 0).any())
    else:
        has = False                      # dose 컬럼 전무 → placebo 날조 금지(False)
    meta["has_placebo"] = has
    return {"has_placebo": has, "pass": True, "route_to_q": None}
