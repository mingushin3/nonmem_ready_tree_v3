"""CLASSIFY ROW_ORDERING — A6 이벤트 행 분류 평가

srp_intent: CLASSIFY ROW_ORDERING
c_name_ko: A6 이벤트 행 분류 평가
kind: detect  (A6 axis classifier; df read-only)

postcondition_predicate:
    meta.get('a6_state') in ['SEPARABLE','SAME-TIME-RESOLVABLE','COVARIATE-CHANGE','RESET-NEEDED','URINE-INTERVAL','AMBIGUOUS']

Routing scope (can_route_to_q=[Q03,Q04]): route_to_q ∈ {None, Q03, Q04} only.
q_codes SSOT triggers (llm_prompt 산문 비사용 — c0203 선례):
  Q04 = A6 = AMBIGUOUS (자기축 disjunct; Q04의 A4=INFUSION-STOP-RESTART disjunct는 c0204 소관, scope 밖).
  Q03 = AIC-POPPK + occasion partition rule 미기재 (교차축). a0_state는 c0200(A0)이 생산 → read-only 참조;
        occasion_partition_rule은 sponsor/protocol 외부 경계 입력. 동시 충족 시 Q04 우선(자기축 row-type blocker).
입력계약 (issues/provenance_gaps.md GAP-10):
  meta['event_row_state'] 선언 descriptor(외부 경계; 부재 시 df fallback로 SEPARABLE/SAME-TIME-RESOLVABLE 구분),
  meta['a0_state'](c0200 생산, read-only), meta['occasion_partition_rule'](외부 경계).
c0206은 meta['a6_state']만 write한다. a0_state는 write 금지(read-only).
"""

import pandas as pd

VALID_A6_STATES = frozenset([
    "SEPARABLE",
    "SAME-TIME-RESOLVABLE",
    "COVARIATE-CHANGE",
    "RESET-NEEDED",
    "URINE-INTERVAL",
    "AMBIGUOUS",
])

# declared event-row descriptor -> a6_state
_DESCRIPTOR_TO_STATE = {
    "separable": "SEPARABLE",
    "same-time-resolvable": "SAME-TIME-RESOLVABLE",
    "covariate-change": "COVARIATE-CHANGE",
    "reset-needed": "RESET-NEEDED",
    "urine-interval": "URINE-INTERVAL",
    "ambiguous": "AMBIGUOUS",
}

_SUBJECT_COLS = ("subject_id", "ID", "id")
_TIME_COLS = ("time_value", "TIME", "time")
_EVENT_COLS = ("event_type", "EVID", "evid")

# EVID dose codes (1=dose, 3=reset+dose, 4=ss dose); 0=obs
_DOSE_EVID = frozenset([1, 3, 4])


def _norm_descriptor(val) -> str | None:
    if not isinstance(val, str):
        return None
    norm = val.strip().lower().replace("_", "-").replace(" ", "-")
    return norm or None


def _col(df: pd.DataFrame, names) -> str | None:
    return next((c for c in names if c in df.columns), None)


def _event_kind(value, is_evid: bool) -> str:
    """단일 row의 event 종류: 'dose' | 'obs' | 'other'."""
    if is_evid:
        try:
            num = int(float(value))
        except (ValueError, TypeError):
            return "other"
        if num in _DOSE_EVID:
            return "dose"
        if num == 0:
            return "obs"
        return "other"
    text = str(value).strip().lower()
    if "dose" in text:
        return "dose"
    if "obs" in text or text in ("sample", "observation", "conc", "concentration"):
        return "obs"
    return "other"


def _has_same_time_dose_obs(df: pd.DataFrame) -> bool:
    """동일 (subject, time) 그룹에 dose+obs가 공존하는가 (df fallback 신호)."""
    subj = _col(df, _SUBJECT_COLS)
    time = _col(df, _TIME_COLS)
    ev = _col(df, _EVENT_COLS)
    if subj is None or time is None or ev is None:
        return False
    is_evid = ev in ("EVID", "evid")
    kinds = df[ev].map(lambda v: _event_kind(v, is_evid))
    grouped = pd.DataFrame({
        "s": df[subj].astype(str),
        "t": pd.to_numeric(df[time], errors="coerce"),
        "k": kinds,
    }).dropna(subset=["t"])
    for _, sub in grouped.groupby(["s", "t"]):
        ks = set(sub["k"])
        if "dose" in ks and "obs" in ks:
            return True
    return False


def _classify_a6(df: pd.DataFrame, meta: dict) -> str:
    state = _norm_descriptor(meta.get("event_row_state"))
    if state in _DESCRIPTOR_TO_STATE:
        return _DESCRIPTOR_TO_STATE[state]
    # df fallback: 동시각 dose+obs를 SEPARABLE로 silent 격하 금지.
    # 나머지 4 state(COVARIATE-CHANGE/RESET-NEEDED/URINE-INTERVAL/AMBIGUOUS)는
    # 도메인 신호 필요 → descriptor로만 결정(fallback이 임의 생성 금지).
    if _has_same_time_dose_obs(df):
        return "SAME-TIME-RESOLVABLE"
    return "SEPARABLE"


def _route_a6(a6_state: str, meta: dict):
    # q_codes SSOT. Q04(자기축 AMBIGUOUS) 우선, 그다음 Q03(교차축 occasion gate).
    if a6_state == "AMBIGUOUS":
        return "Q04"
    if meta.get("a0_state") == "AIC-POPPK" and not meta.get("occasion_partition_rule"):
        return "Q03"
    return None


def classify_row_ordering(df: pd.DataFrame, meta: dict) -> dict:
    state = _classify_a6(df, meta)
    meta["a6_state"] = state
    route = _route_a6(state, meta)
    return {"a6_state": state, "pass": route is None, "route_to_q": route}
