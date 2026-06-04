"""DETECT DUPLICATE_ROW — 완전 중복 행 감지 (A9 보조)

srp_intent: DETECT DUPLICATE_ROW
c_name_ko: 중복 행 감지 (A9 보조)
kind: detect  (A9 DUPLICATE-EXACT helper; df read-only)

postcondition_predicate:
    isinstance(meta.get('has_exact_duplicates'), bool)

precondition_predicate:
    len(df) > 0

Routing scope (can_route_to_q=[]): route_to_q 항상 None, pass 항상 True. A9 Data Defect
Repairability 평가의 보조 정보일 뿐, 종착 routing은 c0209/A9 ROUTE 소관. 전체 행이 일치하는
exact duplicate만 True — 같은 (ID,TIME) 다른 DV(A5 replicate, c0212 소관)는 exact dup 아님(직교).
★ has_exact_duplicates는 Python bool 캐스팅(numpy.bool_은 isinstance(.,bool)=False라 postcond 위반).
"""

import pandas as pd


def detect_duplicate_row(df: pd.DataFrame, meta: dict) -> dict:
    flag = bool(df.duplicated().any())
    meta["has_exact_duplicates"] = flag
    return {"has_exact_duplicates": flag, "pass": True, "route_to_q": None}
