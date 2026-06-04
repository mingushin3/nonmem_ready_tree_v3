"""ROUTE TIME_FORMAT — A3 실패 라우팅

srp_intent: ROUTE TIME_FORMAT
c_name_ko: A3 실패 라우팅
kind: route  (cost 0; a3_state fail state → Q-terminal 라우팅)

postcondition_predicate:
    routing_decision in ['Q02', 'Q12', 'INVALID']

precondition_predicate:
    meta.get('a3_state') in ['AMBIGUOUS', 'UNRECOVERABLE']

라우팅 매핑(★ SSOT = strands.json + q_codes.json + issues/provenance_gaps.md GAP-7):
    AMBIGUOUS    → Q02   (q_codes Q02 trigger: 'A3 = AMBIGUOUS')
    UNRECOVERABLE → Q12  (q_codes Q12 trigger: 'A3 = UNRECOVERABLE')
spec python_snippet 산문은 "UNRECOVERABLE→INVALID"라 적었으나, can_route_to_q=[Q02,Q12]
이고 strands.json의 모든 UNRECOVERABLE 경로(397개)가 c0251 last-c로 Q12에 도달한다
(INVALID는 Q12 이후 사람 결정). 따라서 postcond(Q12 허용)·SSOT를 따라 UNRECOVERABLE→Q12로
구현한다 — spec snippet은 frozen 유지, 구현이 postcond/SSOT 우선(c0019·c0203 '산문 무시',
GAP-7, GAP-19 선례 동형). Q02/Q12 도달 terminal=QUARANTINE(strands.json 정합).
requires_detection_by=c0203 (D-S1: a3_state는 c0203이 생산).
"""

import pandas as pd

# a3 fail state -> Q-code (GAP-7 / q_codes 정합)
_A3_FAIL_TO_Q = {
    "AMBIGUOUS": "Q02",
    "UNRECOVERABLE": "Q12",
}


def route_time_format(df: pd.DataFrame, meta: dict) -> dict:
    a3 = meta.get("a3_state")
    routing_decision = _A3_FAIL_TO_Q.get(a3, "INVALID")
    if routing_decision in ("Q02", "Q12"):
        terminal, q_code = "QUARANTINE", routing_decision
    else:
        terminal, q_code = "INVALID", None
    return {
        "routing_decision": routing_decision,
        "terminal": terminal,
        "q_code": q_code,
    }
