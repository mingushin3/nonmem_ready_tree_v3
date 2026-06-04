"""VERIFY UNIT_DECLARATION — 단위 선언 완전성 검증 (Q10 trigger, A9/P5 helper)

srp_intent: VERIFY UNIT_DECLARATION
c_name_ko: 단위 선언 검증
kind: verify  (unit declaration completeness check; df read-only)

postcondition_predicate:
    meta.get('unit_declaration_complete', True)

precondition_predicate:
    len(df) > 0

Routing scope (can_route_to_q=[Q10]): route_to_q ∈ {None, Q10}. 모든 numeric 컬럼에 단위가
선언돼 있으면(meta['units'][col] 존재) complete=True → pass(→next); 하나라도 누락이면
incomplete=False → Q10. 우선순위: declared meta['unit_declaration_complete'](bool) >
meta['units'] 사전 점검. numeric 컬럼이 없으면 공허 complete=True(점검 대상 없음).

★ df-default divergence (GAP-32, GAP-28/31 동형): c0213 VERIFY TIME_ANCHOR는 '앵커 토큰이
  하나도 없으면 기본 consistent=True(scope-out, 날조 금지)'이나, 본 c0214는 numeric 컬럼이
  존재하고 units가 미선언이면(empty meta) incomplete→Q10이다(df-default=fail). 둘은 정반대
  df-default를 가지며, 본 c의 SSOT(llm_prompt '단위 사전 불완전 시 Q10' + snippet 'all(units...)')에
  충실하다. ★ 단, runtime Q10 ROUTE c는 부재 → Q10은 미실현(Phase 7 D-S4 conditional edge 소관, ②).
  meta['units']는 외부 경계 입력(① meta 주입 소관, GAP-30).
"""

import pandas as pd


def _numeric_cols(df: pd.DataFrame) -> list:
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]


def _unit_declaration_complete(df: pd.DataFrame, meta: dict) -> bool:
    declared = meta.get("unit_declaration_complete")
    if isinstance(declared, bool):
        return declared
    units = meta.get("units", {})
    return all(units.get(c) is not None for c in _numeric_cols(df))


def verify_unit_declaration(df: pd.DataFrame, meta: dict) -> dict:
    complete = _unit_declaration_complete(df, meta)
    meta["unit_declaration_complete"] = complete
    route = None if complete else "Q10"
    return {"unit_declaration_complete": complete, "pass": route is None, "route_to_q": route}
