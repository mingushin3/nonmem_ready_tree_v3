"""DETECT MERGED_CELL — 병합 셀 감지

srp_intent: DETECT MERGED_CELL
c_name_ko: 병합 셀 감지
kind: detect  (§6 mess detector; df read-only, meta에 has_merged_cells 기록)

postcondition_predicate:
    isinstance(meta.get('has_merged_cells'), bool)

Routing scope (can_route_to_q=[]): route_to_q는 항상 None — 이 §6 mess detector는
Q-code를 트리거하지 않는다. verify_visualization: pass_route_to=c0341, fail_route_to=null.

"병합 잔존"(merged residue) = 같은 컬럼에서 비-NaN 값 직후에 오는 NaN
(series.isna() & series.shift().notna()). forward-fill의 대상이다.
선행 NaN(위에 anchor 없음)은 채울 소스가 없으므로 잔존이 아니다 → naive
"any NaN" 감지기가 오탐(silent over-detect)하지 않도록 구분한다.

precondition_predicate: len(df) > 0
ref: universe_sm §6 MERGED_CELL
"""

import pandas as pd


def _has_merged_run(series: pd.Series) -> bool:
    """비-NaN 값 직후 NaN(=forward-fill 대상 병합 잔존)이 하나라도 있는가."""
    return bool((series.isna() & series.shift().notna()).any())


def detect_merged_cell(df: pd.DataFrame, meta: dict) -> dict:
    has_merged = any(_has_merged_run(df[c]) for c in df.columns)
    meta["has_merged_cells"] = bool(has_merged)
    return {"has_merged_cells": bool(has_merged), "pass": True, "route_to_q": None}
