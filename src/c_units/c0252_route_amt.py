"""ROUTE AMT — A4 실패 라우팅

srp_intent: ROUTE AMT
c_name_ko: A4 실패 라우팅
kind: route  (cost 0; a4_state fail state → Q-terminal 라우팅)

postcondition_predicate:
    routing_decision in ['Q04', 'Q08', 'Q14', 'INVALID']

precondition_predicate:
    meta.get('a4_state') in ['MISSING-NO-POLICY', 'ADDL-ACTUAL-CONFLICT', 'INFUSION-STOP-RESTART', 'UNRECOVERABLE']

라우팅 매핑(★ SSOT = strands.json + q_codes.json):
    MISSING-NO-POLICY     → Q08  (QUARANTINE; strands 203)
    ADDL-ACTUAL-CONFLICT  → Q14  (QUARANTINE; strands 191)
    INFUSION-STOP-RESTART → Q04  (QUARANTINE; strands 168)
    UNRECOVERABLE         → INVALID(q_code=None; default; strands 174)
    그 외(default)        → INVALID(q_code=None)
★ GAP-31 RESOLVED (Phase 7 결정 A, 사용자 승인): INFUSION-STOP-RESTART → Q04(168 strand)를 본 c의
  precond·postcond·can_route_to_q·매핑에 정합 반영했다. 근거(cite-verify): universe_sm §3 A4
  'INFUSION-STOP-RESTART(有 REPAIR / 無 Q04)' + q_codes Q04.trigger '(A4=INFUSION-STOP-RESTART
  AND policy 부재)'. strands SSOT ↔ c spec divergence 해소 — 이제 Q04 ∈ postcond이므로 INVALID
  default fallthrough가 아니다(c0251 'Q12∈postcond→SSOT 채택' 선례 동형).
can_route_to_q=[Q08,Q14,Q04] ⊆ 실제 라우팅 {Q04,Q08,Q14,INVALID}(Q15D 없음).
requires_detection_by=c0204 (D-S1: a4_state는 c0204(verify_amt)가 생산).
slice 8 (Batch A) — c0251/c0253 패턴 동형.
"""

import pandas as pd

# a4 fail state -> Q-code (q_codes / strands.json SSOT 정합; postcond ['Q04','Q08','Q14','INVALID'] 준수)
_A4_FAIL_TO_Q = {
    "MISSING-NO-POLICY": "Q08",
    "ADDL-ACTUAL-CONFLICT": "Q14",
    "INFUSION-STOP-RESTART": "Q04",   # GAP-31 RESOLVED: 정책 부재 시 Q04 (universe_sm §3 A4 '無 Q04')
    # UNRECOVERABLE / 그 외 → INVALID (default)
}


def route_amt(df: pd.DataFrame, meta: dict) -> dict:
    a4 = meta.get("a4_state")
    routing_decision = _A4_FAIL_TO_Q.get(a4, "INVALID")
    if routing_decision in ("Q04", "Q08", "Q14"):
        terminal, q_code = "QUARANTINE", routing_decision
    else:
        terminal, q_code = "INVALID", None
    return {
        "routing_decision": routing_decision,
        "terminal": terminal,
        "q_code": q_code,
    }
