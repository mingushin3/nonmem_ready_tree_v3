"""ROUTE BLQ_TOKEN — A5 실패 라우팅

srp_intent: ROUTE BLQ_TOKEN
c_name_ko: A5 실패 라우팅
kind: route  (cost 0; a5_state fail state → Q-terminal 라우팅)

postcondition_predicate:
    routing_decision in ['Q01', 'Q15D', 'INVALID']

precondition_predicate:
    meta.get('a5_state') in ['BLQ-NO-POLICY','LLOQ-MISSING','ABOVE-ULOQ-NO-POLICY','REPLICATE-NO-POLICY','BIOANALYTICAL-FINAL-FLAG-MISSING','ABSENT']

라우팅 매핑(★ SSOT = strands.json + q_codes.json, c0205._route_a5 동형):
    BLQ-NO-POLICY / LLOQ-MISSING / ABOVE-ULOQ-NO-POLICY / REPLICATE-NO-POLICY → Q01   (QUARANTINE)
    BIOANALYTICAL-FINAL-FLAG-MISSING                                          → Q15D  (QUARANTINE)
    ABSENT (그 외 precond state)                                              → INVALID(q_code=None)
strands.json에서 c0253은 645개 strand 전부의 last-c이며 (QUARANTINE,Q01)=445 /
(QUARANTINE,Q15D)=89 / (INVALID,None)=111로 정확히 분해된다(cite-verify). q_codes Q01 trigger
('A5 ∈ {BLQ-NO-POLICY,LLOQ-MISSING,ABOVE-ULOQ-NO-POLICY,REPLICATE-NO-POLICY}')와 정합.
★ can_route_to_q=[Q01]은 실제 라우팅 {Q01,Q15D,INVALID}의 부분집합 — Q15D/INVALID는 Phase 7 D-S4에서
  c0205.can_route_to_q=[Q01,Q15D] + GAP-8(c0205 ABSENT→INVALID scope-out)으로 conditional edge
  재구성된다(issues/provenance_gaps.md GAP-28). c0251(ROUTE TIME_FORMAT) 패턴 동형.
requires_detection_by=c0205 (D-S1: a5_state는 c0205가 생산).
"""

import pandas as pd

# a5 fail state -> Q-code (c0205._route_a5 / q_codes / strands.json SSOT 정합)
_A5_FAIL_TO_Q = {
    "BLQ-NO-POLICY": "Q01",
    "LLOQ-MISSING": "Q01",
    "ABOVE-ULOQ-NO-POLICY": "Q01",
    "REPLICATE-NO-POLICY": "Q01",
    "BIOANALYTICAL-FINAL-FLAG-MISSING": "Q15D",
}


def route_blq_token(df: pd.DataFrame, meta: dict) -> dict:
    a5 = meta.get("a5_state")
    routing_decision = _A5_FAIL_TO_Q.get(a5, "INVALID")
    if routing_decision in ("Q01", "Q15D"):
        terminal, q_code = "QUARANTINE", routing_decision
    else:
        terminal, q_code = "INVALID", None
    return {
        "routing_decision": routing_decision,
        "terminal": terminal,
        "q_code": q_code,
    }
