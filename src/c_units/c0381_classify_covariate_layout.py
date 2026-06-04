"""CLASSIFY COVARIATE_LAYOUT — 공변량 레이아웃 분류 (L-4->L-5 mess)

srp_intent: CLASSIFY COVARIATE_LAYOUT
c_name_ko: 공변량 레이아웃 분류
kind: detect  (mess:COVARIATE_LAYOUT; df read-only)
requires_detection_by: c0380

postcondition_predicate:
    meta.get('cov_layout_classified', False)

★ 함수명은 classify_covariate_layout_mess — c0207(A7 axis)의 classify_covariate_layout과 이름
충돌 회피(slice 2 c0310 detect_time_format_mess 선례).

★ verbatim postcond는 단순 flag(default=False)다. 순수 no-op(flag 미설정)은 default-False로 postcond에서
잡히나, c0380 산출(cov_layout) 없이도 flag=True로 만들면 vacuous classification(silent no-op)이 된다.
spec frozen(토큰 변경 금지, override 아님) — 대신 구현이 detection 산출에 gate한다(GAP-27 4-case 동형):
  ① cov_layout(c0380 산출)가 유효(∈{wide,long,none}) → 분류 확정 후에만 meta['cov_layout_classified']=True.
  ② cov_layout=='none'(공변량 불요) → 정당한 분류(pivot 불요), flag 설정(부재≠silent no-op).
  ③ requires_detection_by(c0380) 산출물 meta['cov_layout'] 부재 → success=False·route_to_q=None
     (can_route_to_q=[] → Q 날조 금지, GAP-21(C) 선례)·flag 미설정.
  ④ cov_layout가 set이나 무효값 → success=False, flag 미설정(silent 통과 금지).
pivot은 수행하지 않는다(Phase 2b/L-2->L-3 c0121 소관 — toy_example "pivot deferred to 2b").
orchestrator는 c0381을 detect로 등록하나(D-S1 orchestrator gate는 transform/route 대상), c0380 의존은
본 함수가 cov_layout artifact를 직접 guard해 enforce한다(c0313 선례 — gate는 보조, artifact 체크가 본 enforcement).
df read-only(SRP).
"""

import pandas as pd

_VALID_LAYOUTS = ("wide", "long", "none")


def classify_covariate_layout_mess(df: pd.DataFrame, meta: dict) -> dict:
    layout = meta.get("cov_layout")
    if layout not in _VALID_LAYOUTS:
        # ③/④ detection(c0380) 미선행/무효 → silent 통과 금지(Q 날조 없음), flag 미설정.
        return {"success": False, "route_to_q": None}
    # ①/② 유효 분류 확정 후 flag 명시 설정('none' 포함 — 부재≠silent no-op).
    meta["cov_layout_classified"] = True
    return {"cov_layout_classified": True, "success": True, "route_to_q": None}
