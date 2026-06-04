"""PIVOT COVARIATE_LAYOUT — 공변량 레이아웃 변환 (L-2→L-3)

srp_intent: PIVOT COVARIATE_LAYOUT
c_name_ko: 공변량 레이아웃 변환
kind: transform
requires_detection_by: c0207 (명목; 실효 detection = c0380/c0381, 둘 다 미구현 — GAP-16)
can_route_to_q: []  (q_codes.json에 c0121 참조 0건; scope-out 라우팅은 None)

postcondition_predicate:
    all(df[col].apply(lambda x: not isinstance(x, (list, dict))).all() for col in meta.get('covariate_columns', []))

설계(사용자 ★★★ 확정):
  - 출력 shape = REFINED wide→long. verbatim postcond가 plural meta['covariate_columns']를 순회하며
    base별 값 컬럼(df['WT'], df['AGE'])을 요구하므로 refined만 충족한다. spec python_snippet/r_snippet의
    plain melt(단일 'cov_value')는 postcond를 위반(단일 컬럼) → 미준수. SSOT 위계: postcond > snippet/toy.
    snippet은 frozen 유지(수정 없음), 구현이 postcond 우선(GAP-19 'snippet frozen, 구현 override' 선례 동형).
    snippet↔postcond 충돌은 GAP-21로 기록. WT_V1,WT_V2 → 'visit' 컬럼 + 'WT' 값 컬럼(toy_example).
    multi-cov(WT_V*,AGE_V*) → 별도 WT,AGE 컬럼(한 컬럼 혼합 금지).
  - 분기키 cov_layout(∈{wide,long,none})는 c0207이 아니라 mess층 c0380(DETECT)/c0381(CLASSIFY, 둘 다
    L-4→L-5 미구현)이 생산(GAP-16). 단위테스트는 fixture meta로 cov_layout 직접 주입. c0207_passed는
    orchestrator가 구조적으로 보장(D-S1) — 함수 내 미검사(c0022/c0140/c0023/c0141 동형).
  - ★ silent no-op 방지(Lock 3): cov_layout 부재/미인식이면 pivot 미수행 상태로 조용히 통과하지 않는다.
    fail + route_to_q=None을 명시 반환(can_route_to_q=[] → in-scope Q 없음 → scope-out None, Q 날조 금지;
    GAP-5/8/13 선례). 'wide'인데 변환 대상 공변량 컬럼 부재(빈 분기)도 동일 처리.
  - pivot 무결성: wide→long 행 수 = subjects×visits, 비결측 covariate 값 손실/중복 0(변환 전후 count 검증).
    deterministic outcome(Lock 3): id_cols+visit 사전식 정렬. pivot 중 생성 결측(ragged wide)은 NaN 보존
    (IMPUTE 금지 — vocabulary §A; pivot은 재배열이지 결측보충 아님). NaN은 scalar라 postcond 통과.
  - covariate base 해석(=wide_to_long stubname=출력 값 컬럼명=postcond 대상): meta['covariate_columns']
    1차, 부재 시 df fallback({base}_{visit}에서 base가 _COVARIATE_COLS면 채택; c0207/c0140 동형). 생산자 부재(GAP-21).
입력계약(GAP-16/GAP-21): cov_layout(c0380/c0381 미구현)·covariate_columns(생산 c 없음)·wide covariate 컬럼(상류) 참조.
"""

import re

import pandas as pd

# 알려진 covariate 컬럼 base(소문자). c0207/c0140 _COVARIATE_COLS 동형 — meta 미선언 시 df fallback용.
_COVARIATE_COLS = frozenset([
    "wt", "bw", "weight", "age", "sex", "gender", "race", "ethnic",
    "ht", "height", "bmi", "bsa", "crcl", "egfr", "alb", "alt", "ast",
    "bili", "scr", "geno", "genotype", "smok", "smoke", "formulation",
])

# {base}_{visit}: visit은 마지막 '_' 뒤 비-underscore 토큰(WT_V1 → base=WT, visit=V1).
_VISIT_SPLIT = re.compile(r"^(?P<base>.+)_(?P<visit>[^_]+)$")


def _fail(df: pd.DataFrame) -> dict:
    # scope-out / blocked: can_route_to_q=[] → Q 날조 금지, route_to_q=None(+GAP). silent no-op 아님.
    return {"success": False, "route_to_q": None, "df": df}


def _resolve_bases(df: pd.DataFrame, meta: dict) -> list:
    declared = meta.get("covariate_columns") if meta else None
    if declared:
        return [str(b) for b in declared]
    # df fallback(GAP-21): 선언 부재 시 {base}_{visit}에서 base가 알려진 covariate면 채택(순서 보존).
    bases = []
    for col in df.columns:
        m = _VISIT_SPLIT.match(str(col))
        if m and m.group("base").strip().lower() in _COVARIATE_COLS:
            base = m.group("base")
            if base not in bases:
                bases.append(base)
    return bases


def _wide_columns(df: pd.DataFrame, candidate_bases) -> list:
    base_set = set(candidate_bases)
    cols = []
    for col in df.columns:
        m = _VISIT_SPLIT.match(str(col))
        if m and m.group("base") in base_set:
            cols.append(col)
    return cols


def pivot_covariate_layout(df: pd.DataFrame, meta: dict) -> dict:
    df = df.copy()

    layout = meta.get("cov_layout") if meta else None

    # 이미 long / 공변량 불요 → pass-through(명시 분류이므로 silent no-op 아님).
    if layout in ("long", "none"):
        return {"success": True, "df": df}

    # ★ cov_layout 부재/미인식 → 명시 fail(silent no-op 금지, Lock 3; scope-out route_to_q=None).
    if layout != "wide":
        return _fail(df)

    # wide: 변환 대상 wide 공변량 컬럼 식별(meta 1차, df fallback). base는 매칭 컬럼에서 역도출.
    wide_cols = _wide_columns(df, _resolve_bases(df, meta))
    bases = []
    for col in wide_cols:
        base = _VISIT_SPLIT.match(str(col)).group("base")
        if base not in bases:
            bases.append(base)
    id_cols = [c for c in df.columns if c not in set(wide_cols)]

    # 빈 분기(변환 대상 공변량/식별자 부재) → 조용히 통과 금지(명시 fail).
    if not bases or not id_cols:
        return _fail(df)

    # 식별자가 wide 행을 유일 식별 못함 → wide_to_long 집계/중복 위험 → 명시 fail(silent corruption 금지).
    if df.duplicated(subset=id_cols).any():
        return _fail(df)

    n_before = int(df[wide_cols].notna().to_numpy().sum())

    long_df = pd.wide_to_long(
        df, stubnames=bases, i=id_cols, j="visit", sep="_", suffix=r".+"
    ).reset_index()

    # deterministic outcome(Lock 3): id_cols + visit 사전식 정렬.
    long_df = long_df.sort_values(id_cols + ["visit"]).reset_index(drop=True)

    # pivot 무결성: 비결측 covariate 값 보존(손실/중복 0). 위반 시 명시 fail(silent corruption 금지).
    n_after = int(long_df[bases].notna().to_numpy().sum())
    if n_after != n_before:
        return _fail(long_df)

    return {"success": True, "df": long_df}
