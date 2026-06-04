"""DETECT COVARIATE_LAYOUT — 공변량 레이아웃 감지 (L-4->L-5 mess)

srp_intent: DETECT COVARIATE_LAYOUT
c_name_ko: 공변량 레이아웃 감지
kind: detect  (mess:COVARIATE_LAYOUT; df read-only)

postcondition_predicate:
    meta.get('cov_layout') in ['wide', 'long', 'none']

precondition_predicate:
    len(df) > 0

covariate 컬럼의 레이아웃을 wide/long/none으로 식별만 한다(pivot 미수행 — c0121 L-2->L-3 소관).
  - wide : 알려진 covariate base가 visit 접미사로 ≥2개 컬럼 반복(WT_V1,WT_V2,WT_V3).
  - long : wide 시그널 없으나 covariate 컬럼(plain 'WT' 또는 단일 suffix)이 존재.
  - none : covariate 컬럼 전무.
postcond는 멤버십({wide,long,none})만 검사 → 'none' 하드코딩 vacuous 통과가 구조상 가능하나,
trap(WT_V1,WT_V2를 'none'으로 오판 금지)·adversarial이 실제 식별을 강제한다. can_route_to_q=[]
→ route_to_q 항상 None(pass→c0381). 하류 c0381(CLASSIFY)의 requires_detection_by=c0380(D-S1 cut-vertex).
covariate 어휘(_COVARIATE_COLS)·visit 분해(_VISIT_SPLIT)는 c0121(PIVOT)/c0207(A7)과 동일 정의 —
c0380='wide' 판정이 c0121 pivot 대상과 정합해야 한다(활성화 chain drift guard:
tests/test_strands.py::test_c0121_activation_chain_dynamic). df read-only(detect SRP).
"""

import re

import pandas as pd

# 알려진 covariate 컬럼 base(소문자). c0121/c0207 _COVARIATE_COLS와 동일 정의(정합 필수).
_COVARIATE_COLS = frozenset([
    "wt", "bw", "weight", "age", "sex", "gender", "race", "ethnic",
    "ht", "height", "bmi", "bsa", "crcl", "egfr", "alb", "alt", "ast",
    "bili", "scr", "geno", "genotype", "smok", "smoke", "formulation",
])

# {base}_{visit}: visit은 마지막 '_' 뒤 비-underscore 토큰(WT_V1 → base=WT, visit=V1). c0121와 동일.
_VISIT_SPLIT = re.compile(r"^(?P<base>.+)_(?P<visit>[^_]+)$")


def _is_covariate(name) -> bool:
    return str(name).strip().lower() in _COVARIATE_COLS


def detect_covariate_layout(df: pd.DataFrame, meta: dict) -> dict:
    # visit 접미사로 반복되는 covariate base 집계(WT_V1,WT_V2 → {'WT':2}). plain covariate 별도 표기.
    wide_groups: dict = {}
    plain_cov = False
    for col in df.columns:
        if _is_covariate(col):
            plain_cov = True
            continue
        m = _VISIT_SPLIT.match(str(col))
        if m and _is_covariate(m.group("base")):
            base = m.group("base")
            wide_groups[base] = wide_groups.get(base, 0) + 1

    if any(n >= 2 for n in wide_groups.values()):
        layout = "wide"            # 한 base가 시점별로 다중 컬럼 → wide(pivot 필요)
    elif plain_cov or wide_groups:
        layout = "long"            # covariate 존재하나 wide 시그널 없음(이미 tidy)
    else:
        layout = "none"            # covariate 컬럼 전무(날조 금지)

    meta["cov_layout"] = layout
    return {"cov_layout": layout, "pass": True, "route_to_q": None}
