"""ASSIGN TIME — TIME 표준화

srp_intent: ASSIGN TIME
c_name_ko: TIME 표준화
kind: transform  (requires_detection_by: c0203 A3 axis · can_route_to_q: [Q02, Q12])

postcondition_predicate:
    'TIME' in df.columns and df['TIME'].apply(lambda x: isinstance(x, (int, float, np.floating, np.integer))).all() and df['TIME'].notna().all()

설계(사용자 확정): spec python_snippet 1:1 — df['TIME'] = pd.to_numeric(df['time_value']).
a3_state는 *라우팅 게이트*로만 사용한다(AMBIGUOUS→Q02, UNRECOVERABLE→Q12). spec에 없는
per-state derivation(nominal_time/elapsed offset/interval midpoint)은 만들지 않는다
(hallucination 차단 — CLAUDE.md Hallucination 규칙). 6개 유도가능 state는 동일 derivation.
precondition의 c0203_passed는 orchestrator가 구조적으로 보장(D-S1) — 함수 내 검사 안 함
(c0017이 c0011_passed를 직접 검사하지 않는 것과 동형).
입력계약: time_value 생산자는 상류 L-4→L-5 시간 정규화 mess c(미구현) —
issues/provenance_gaps.md GAP-18(↔GAP-7) 참조. 단위테스트는 fixture로 time_value 주입.
"""

import pandas as pd


def assign_time(df: pd.DataFrame, meta: dict) -> dict:
    df = df.copy()

    # precondition: time_value 컬럼(상류 mess c 산출, GAP-18) 부재 → fail
    if "time_value" not in df.columns:
        return {"success": False, "route_to_q": "Q02", "df": df}

    # precondition: a3_state(c0203 산출) 부재 → fail
    a3_state = meta.get("a3_state") if meta else None
    if a3_state is None:
        return {"success": False, "route_to_q": "Q02", "df": df}

    # 라우팅 전용 분기(c0203 scope) — 비유도 state는 사람 결정 게이트로
    if a3_state == "AMBIGUOUS":
        return {"success": False, "route_to_q": "Q02", "df": df}
    if a3_state == "UNRECOVERABLE":
        return {"success": False, "route_to_q": "Q12", "df": df}

    # spec python_snippet 1:1 — 6개 유도가능 state 모두 동일 derivation
    df["TIME"] = pd.to_numeric(df["time_value"], errors="coerce")

    # silent-error guard: parse 실패(NaN) 또는 음수 시간 → postcond가 못 잡는 결함 → fail
    if df["TIME"].isna().any() or (df["TIME"] < 0).any():
        return {"success": False, "route_to_q": "Q02", "df": df}

    df["TIME"] = df["TIME"].astype(float)
    return {"success": True, "df": df}
