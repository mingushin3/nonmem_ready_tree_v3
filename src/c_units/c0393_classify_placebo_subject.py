"""CLASSIFY PLACEBO_SUBJECT — 위약군 분류 (L-4->L-5 mess)

srp_intent: CLASSIFY PLACEBO_SUBJECT
c_name_ko: 위약군 분류
kind: detect  (mess:PLACEBO_SUBJECT; df read-only)
requires_detection_by: c0392

postcondition_predicate:
    isinstance(meta.get('placebo_subjects'), list)

★ verbatim postcond는 타입(list)만 검사한다 — 빈 list([])도 통과하므로, 실제 위약 피험자가 있는데도
silent [] 를 돌려주면 vacuous classification(silent no-op)이 된다. spec frozen(토큰 변경 금지, override 아님)
— 대신 구현이 detection 산출(c0392의 meta['has_placebo'])에 gate한다(GAP-27 4-case 동형, c0381 선례):
  ① has_placebo(bool)가 set → df의 dose_amount==0 피험자를 실제 산출(silent [] 금지).
  ② has_placebo==False 또는 식별 컬럼 부재 → [](정당한 빈 분류; 부재≠silent no-op, 빈 list도 명시 set).
  ③ requires_detection_by(c0392) 산출물 meta['has_placebo'] 부재 → success=False·route_to_q=None
     (can_route_to_q=[] → Q 날조 금지, GAP-21(C)/GAP-27 선례)·placebo_subjects 미설정
     (→ postcond isinstance(None, list) 자연 실패 = gate 작동).
  ④ has_placebo가 set이나 bool 아님(무효) → success=False, 미설정(silent 통과 금지).
orchestrator는 c0393을 detect로 등록하나(D-S1 orchestrator gate는 transform/route 대상) — c0392 의존은
본 함수가 has_placebo artifact를 직접 guard해 enforce한다(c0381/c0313 선례 — gate는 보조, artifact 체크가
본 enforcement). dose_amount는 pd.to_numeric(coerce)로 정규화해 누락(NaN)을 AMT=0과 구분(c0392와 정합).
unique().tolist()는 python-native list 산출(isinstance list 충족). df read-only(SRP).
"""

import pandas as pd


def classify_placebo_subject(df: pd.DataFrame, meta: dict) -> dict:
    has = meta.get("has_placebo")
    if not isinstance(has, bool):
        # ③/④ detection(c0392) 미선행/무효 → silent 통과 금지(Q 날조 없음), placebo_subjects 미설정.
        return {"success": False, "route_to_q": None}
    if "dose_amount" in df.columns and "subject_id" in df.columns:
        # ① AMT=0 피험자 실제 산출(NaN 누락은 제외 — c0392 구분 criterion과 정합).
        dose = pd.to_numeric(df["dose_amount"], errors="coerce")
        subjects = df.loc[dose == 0, "subject_id"].unique().tolist()
    else:
        subjects = []                    # ② has_placebo=False / 식별 컬럼 부재 → 빈 분류(명시 set)
    meta["placebo_subjects"] = subjects
    return {"placebo_subjects": subjects, "success": True, "route_to_q": None}
