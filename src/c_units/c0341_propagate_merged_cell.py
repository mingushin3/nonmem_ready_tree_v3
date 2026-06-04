"""PROPAGATE MERGED_CELL — 병합 셀 전파

srp_intent: PROPAGATE MERGED_CELL
c_name_ko: 병합 셀 전파
kind: transform
requires_detection_by: c0340  (★ D-S1: 대응 DETECT 통과 후에만 호출)

postcondition_predicate:
    not meta.get('has_merged_cells', False) or not any((df[c].isna() & df[c].shift().notna()).any() for c in df.columns)

병합 잔존을 컬럼별 수직 forward-fill(axis=0)로 해소한다. 선행 NaN(anchor 없음)은
채울 소스가 없어 보존된다(역방향 backfill 금지). 교차컬럼 bleed 방지를 위해
axis=0을 고정한다. R 등가: tidyr::fill(everything(), .direction='down').

★ has_merged_cells를 False로 뒤집지 않는다 — True로 유지해야 postcondition의 둘째 절
(잔존 검사)이 살아있어 silent no-op(미변환)을 잡는다.

precondition_predicate: c0340_passed
ref: universe_sm §6 MERGED_CELL
"""

import pandas as pd


def propagate_merged_cell(df: pd.DataFrame, meta: dict) -> dict:
    # ★ D-S1 cut-vertex: 대응 DETECT(c0340)가 has_merged_cells를 기록하지 않았다면
    # fix-c precondition(c0340_passed) 미성립 → silent 진행 금지.
    if "has_merged_cells" not in meta:
        return {"success": False, "df": df, "route_to_q": None}
    # 컬럼별 수직 forward-fill(병합 잔존 해소). 기본 axis=0 — 교차컬럼 bleed 없음.
    df = df.ffill()
    return {"success": True, "df": df}
