"""ROUTE CROSS_COLUMN_INVARIANT — A9 실패 라우팅

srp_intent: ROUTE CROSS_COLUMN_INVARIANT
c_name_ko: A9 실패 라우팅
kind: route  (cost 0; a9_state fail state → Q-terminal 라우팅)

postcondition_predicate:
    routing_decision in ['Q06', 'Q15D', 'INVALID']

precondition_predicate:
    meta.get('a9_state') in ['PROTOCOL-DEVIATION-NO-POLICY', 'REANALYSIS-FINAL-MISSING', 'IRRECONCILABLE']

라우팅 매핑(★ SSOT = strands.json + q_codes.json):
    PROTOCOL-DEVIATION-NO-POLICY → Q06   (QUARANTINE; strands 26)
    REANALYSIS-FINAL-MISSING     → Q15D  (QUARANTINE; strands 22)
    IRRECONCILABLE               → INVALID(q_code=None; default; strands 30)
    그 외(default)               → INVALID(q_code=None)
IRRECONCILABLE→INVALID: universe_sm상 ->INVALID이며 c0209는 분류만(route_to_q=None), INVALID 종착은
본 ROUTE c 책임(c0209 docstring 정합; c0204 GAP-5 / c0205 GAP-8 선례 동형). spec snippet과 SSOT 정합.
can_route_to_q=[Q06,Q15D] ⊆ 실제 라우팅 {Q06,Q15D,INVALID}(GAP 없음 — INVALID는 postcond 내).
requires_detection_by=c0209 (D-S1: a9_state는 c0209(verify_cross_column_invariant)가 생산).
slice 8 (Batch A) — c0251/c0253 패턴 동형.
"""

import pandas as pd

# a9 fail state -> Q-code (q_codes / strands.json SSOT 정합; postcond ['Q06','Q15D','INVALID'] 준수)
_A9_FAIL_TO_Q = {
    "PROTOCOL-DEVIATION-NO-POLICY": "Q06",
    "REANALYSIS-FINAL-MISSING": "Q15D",
    # IRRECONCILABLE / 그 외 → INVALID (default)
}


def route_cross_column_invariant(df: pd.DataFrame, meta: dict) -> dict:
    a9 = meta.get("a9_state")
    routing_decision = _A9_FAIL_TO_Q.get(a9, "INVALID")
    if routing_decision in ("Q06", "Q15D"):
        terminal, q_code = "QUARANTINE", routing_decision
    else:
        terminal, q_code = "INVALID", None
    return {
        "routing_decision": routing_decision,
        "terminal": terminal,
        "q_code": q_code,
    }
