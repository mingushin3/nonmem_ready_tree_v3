"""NORMALIZE BLQ_TOKEN — BLQ 토큰 정규화 (mess 층 L-4->L-5)

srp_intent: NORMALIZE BLQ_TOKEN
c_name_ko: BLQ 토큰 정규화
kind: transform  (requires_detection_by: c0305 · can_route_to_q: [Q01])

postcondition_predicate:
    not df['dv_value'].astype(str).str.contains(r'<|BLQ|ND|LOD|이하', case=False, na=False).any()

설계(plan): spec python_snippet 1:1 — mask=BLQ 토큰 포함행, df['blq_detected']=mask,
df.loc[mask,'lloq_value']=토큰서 추출한 numeric LLOQ(NaN 처리 *전*), df.loc[mask,'dv_value']=NaN.
★ postcond는 NON-vacuous — BLQ 토큰이 잔존하면 곧장 fail이라 silent no-op 0이 자동 강제된다
  (c0393류 list-타입 vacuous 아님). 따라서 GAP-27 artifact-guard 불요; trap이 실제 제거 재확인.
★ can_route_to_q=[Q01]은 Phase 7 D-S4 *선언*이며 runtime 라우팅이 아니다 — 본 c는 terminal 키를
  반환하지 않는다. Q01 strand 라우팅의 실주체는 c0253(ROUTE BLQ_TOKEN, A5 fail). issues GAP-28
  (slice 2 GAP-26: 'c0019가 아니라 c0251' 동형).
입력계약: 산출 blq_detected/lloq_value를 하류 c0020(ASSIGN BLQ_FLAG)·c0021(ASSIGN LLOQ)가
  cross-layer 소비한다(GAP-15 효과적 producer). c0305_passed는 orchestrator D-S1 gate가 구조적
  보장 — 함수 내 미검사(c0311 CONVERT 동형).
ref: universe_sm §6 BLQ_TOKEN
"""

import numpy as np
import pandas as pd

_DV_COLS = ("dv_value", "DV", "dv")
# postcond와 동일 토큰 어휘(string pattern, case=False).
_BLQ_PATTERN = r"<|BLQ|ND|LOD|이하"


def _dv_column(df: pd.DataFrame):
    return next((c for c in _DV_COLS if c in df.columns), None)


def normalize_blq_token(df: pd.DataFrame, meta: dict) -> dict:
    df = df.copy()
    col = _dv_column(df)
    if col is None:
        return {"df": df, "success": True}  # dv 컬럼 부재 → 정규화 대상 없음(vacuous True)

    s = df[col].astype(str)
    mask = s.str.contains(_BLQ_PATTERN, case=False, na=False, regex=True)
    df["blq_detected"] = mask
    # LLOQ 수치 추출은 dv_value=NaN 치환 *전*에 수행(spec snippet 순서). 토큰서 첫 numeric run.
    extracted = s.where(mask).str.extract(r"([\d.]+)", expand=False)
    df["lloq_value"] = pd.to_numeric(extracted, errors="coerce")
    # canonical marker: BLQ 토큰 dv → NaN (postcond: 토큰 잔존 0)
    df.loc[mask, col] = np.nan
    return {"df": df, "success": True}
