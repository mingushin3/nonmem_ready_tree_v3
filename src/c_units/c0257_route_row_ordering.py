"""ROUTE ROW_ORDERING — A6 실패 라우팅

srp_intent: ROUTE ROW_ORDERING
c_name_ko: A6 실패 라우팅
kind: route  (cost 0; a6_state fail state → Q-terminal 라우팅)

postcondition_predicate:
    routing_decision in ['Q03', 'Q04']

precondition_predicate:
    meta.get('a6_state') == 'AMBIGUOUS'

라우팅 매핑(★ SSOT = strands.json + q_codes.json):
    AMBIGUOUS                                                      → Q04  (QUARANTINE; strands 124)
    COVARIATE-CHANGE / RESET-NEEDED / SAME-TIME-RESOLVABLE / SEPARABLE → Q03  (QUARANTINE; strands 합 10)
    그 외(URINE-INTERVAL 등 pass-state)                            → INVALID(q_code=None; default 방어)
★ precond(meta['a6_state']=='AMBIGUOUS')·spec python_snippet('routing=Q04')는 Q04만 산문화하나,
  can_route_to_q=[Q03,Q04] + postcond in ['Q03','Q04']가 Q03을 허용하고, strands.json이 4개 a6 state→Q03
  (10 strand, A0=AIC-POPPK 교차축 미해소 경로)를 c0257 last-c로 확정한다. 따라서 c0251(ROUTE TIME_FORMAT)
  선례(산문/precond 무시·postcond+SSOT 우선)대로 Q03 state를 구현한다. Q03 ∈ postcond이라 GAP 불요
  (Q04∉postcond였던 c0252 INFUSION-STOP-RESTART의 GAP-31과 대조). 교차축 조건은 상류(strand 진입 여부)에서
  걸러지므로, c0257에 도달한 a6 state는 SSOT 매핑대로 단순 분기한다(c0206._route_a6 cross-axis는 라우팅
  여부 판정, 본 c는 도달 state→Q 매핑).
requires_detection_by=c0206 (D-S1: a6_state는 c0206(classify_row_ordering)이 생산).
slice 8 (Batch A) — c0251/c0253 패턴 동형.
"""

import pandas as pd

# a6 fail state -> Q-code (q_codes / strands.json SSOT 정합; postcond ['Q03','Q04'] 준수)
_A6_FAIL_TO_Q = {
    "AMBIGUOUS": "Q04",
    "COVARIATE-CHANGE": "Q03",
    "RESET-NEEDED": "Q03",
    "SAME-TIME-RESOLVABLE": "Q03",
    "SEPARABLE": "Q03",
}


def route_row_ordering(df: pd.DataFrame, meta: dict) -> dict:
    a6 = meta.get("a6_state")
    routing_decision = _A6_FAIL_TO_Q.get(a6, "INVALID")
    if routing_decision in ("Q03", "Q04"):
        terminal, q_code = "QUARANTINE", routing_decision
    else:
        terminal, q_code = "INVALID", None
    return {
        "routing_decision": routing_decision,
        "terminal": terminal,
        "q_code": q_code,
    }
