"""ROUTE COVARIATE_LAYOUT — A7 실패 라우팅

srp_intent: ROUTE COVARIATE_LAYOUT
c_name_ko: A7 실패 라우팅
kind: route  (cost 0; a7_state fail state → Q-terminal 라우팅)

postcondition_predicate:
    routing_decision in ['Q07', 'Q13']

precondition_predicate:
    meta.get('a7_state') in ['KEY-MISSING', 'POLICY-MISSING']

라우팅 매핑(★ SSOT = strands.json + q_codes.json):
    POLICY-MISSING → Q07  (QUARANTINE; strands 108)
    KEY-MISSING    → Q13  (QUARANTINE; strands 98)
    그 외(default) → INVALID(q_code=None)  — naive 'else Q07' 차단(pass-state 방어)
can_route_to_q=[Q07,Q13] == 실제 라우팅 {Q07,Q13}(GAP 없음).
requires_detection_by=c0207 (D-S1: a7_state는 c0207(classify_covariate_layout)이 생산).
slice 8 (Batch A) — c0251/c0253 패턴 동형.
"""

import pandas as pd

# a7 fail state -> Q-code (q_codes / strands.json SSOT 정합)
_A7_FAIL_TO_Q = {
    "POLICY-MISSING": "Q07",
    "KEY-MISSING": "Q13",
}


def route_covariate_layout(df: pd.DataFrame, meta: dict) -> dict:
    a7 = meta.get("a7_state")
    routing_decision = _A7_FAIL_TO_Q.get(a7, "INVALID")
    if routing_decision in ("Q07", "Q13"):
        terminal, q_code = "QUARANTINE", routing_decision
    else:
        terminal, q_code = "INVALID", None
    return {
        "routing_decision": routing_decision,
        "terminal": terminal,
        "q_code": q_code,
    }
