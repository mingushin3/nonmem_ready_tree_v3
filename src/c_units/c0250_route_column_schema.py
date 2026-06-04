"""ROUTE COLUMN_SCHEMA — A0 실패 라우팅

srp_intent: ROUTE COLUMN_SCHEMA
c_name_ko: A0 실패 라우팅
kind: route  (cost 0; a0_state fail state → Q-terminal 라우팅)

postcondition_predicate:
    routing_decision == 'Q11'

precondition_predicate:
    meta.get('a0_state') == 'AIC-MISSING'

라우팅 매핑(★ SSOT = strands.json + q_codes.json):
    AIC-MISSING → Q11   (QUARANTINE; strands.json 720 strand 전부 c0250 last-c → (QUARANTINE,Q11))
    그 외(default) → INVALID(q_code=None)  — precond 밖 pass-state 방어(c0253 ABSENT 선례 동형)
A0는 단일 fail-state(AIC-MISSING)라 can_route_to_q=[Q11] == 실제 라우팅 {Q11}(GAP 없음).
requires_detection_by=c0200 (D-S1: a0_state는 c0200(verify_a0_analysis_intent)이 생산).
slice 8 (Batch A) — c0251(ROUTE TIME_FORMAT)/c0253(ROUTE BLQ_TOKEN) 패턴 동형.
"""

import pandas as pd

# a0 fail state -> Q-code (q_codes / strands.json SSOT 정합)
_A0_FAIL_TO_Q = {
    "AIC-MISSING": "Q11",
}


def route_column_schema(df: pd.DataFrame, meta: dict) -> dict:
    a0 = meta.get("a0_state")
    routing_decision = _A0_FAIL_TO_Q.get(a0, "INVALID")
    if routing_decision == "Q11":
        terminal, q_code = "QUARANTINE", routing_decision
    else:
        terminal, q_code = "INVALID", None
    return {
        "routing_decision": routing_decision,
        "terminal": terminal,
        "q_code": q_code,
    }
