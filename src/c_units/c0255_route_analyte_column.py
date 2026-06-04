"""ROUTE ANALYTE_COLUMN — A8 실패 라우팅

srp_intent: ROUTE ANALYTE_COLUMN
c_name_ko: A8 실패 라우팅
kind: route  (cost 0; a8_state fail state → Q-terminal 라우팅)

postcondition_predicate:
    routing_decision == 'Q09'

precondition_predicate:
    meta.get('a8_state') == 'CMT-POLICY-MISSING'

라우팅 매핑(★ SSOT = strands.json + q_codes.json):
    CMT-POLICY-MISSING → Q09  (QUARANTINE; strands.json 239 last-c 전부 (QUARANTINE,Q09))
    그 외(default)     → INVALID(q_code=None)  — precond 밖 pass-state(SINGLE-DRUG 등) 방어
A8는 단일 fail-state(CMT-POLICY-MISSING)라 can_route_to_q=[Q09] == 실제 라우팅 {Q09}(GAP 없음).
requires_detection_by=c0208 (D-S1: a8_state는 c0208(classify_analyte_column)이 생산).
slice 8 (Batch A) — c0251/c0253 패턴 동형.
"""

import pandas as pd

# a8 fail state -> Q-code (q_codes / strands.json SSOT 정합)
_A8_FAIL_TO_Q = {
    "CMT-POLICY-MISSING": "Q09",
}


def route_analyte_column(df: pd.DataFrame, meta: dict) -> dict:
    a8 = meta.get("a8_state")
    routing_decision = _A8_FAIL_TO_Q.get(a8, "INVALID")
    if routing_decision == "Q09":
        terminal, q_code = "QUARANTINE", routing_decision
    else:
        terminal, q_code = "INVALID", None
    return {
        "routing_decision": routing_decision,
        "terminal": terminal,
        "q_code": q_code,
    }
