"""ASSIGN BASELINE_COVARIATE — 기저 공변량 수치 코딩

srp_intent: ASSIGN BASELINE_COVARIATE
c_name_ko: 기저 공변량 수치 코딩
kind: transform  (requires_detection_by: c0207 A7 axis · can_route_to_q: [Q07, Q13])

postcondition_predicate:
    all(df[cov].apply(lambda x: isinstance(x, (int, float, np.floating, np.integer)) or pd.isna(x) == False).all() for cov in meta.get('baseline_covariates', []))

설계(사용자 ★★★ 확정 — IMPUTE override): spec python_snippet의 fillna(median())은 *따르지 않는다*.
vocabulary.md §A 전역 규칙 "IMPUTE 제외(자의적 결측보충 금지 — FLAG 후 정책 결정)" > 개별 snippet.
결측 공변량은 median 대입 없이 명시 NaN으로 보존(FLAG)하고 Q07로 라우팅한다(정책 결정 요청).
결측 없는 정상 공변량만 numeric ASSIGN(범주형 SEX→int, 연속형→to_numeric). 마커 컬럼 미추가 →
output_schema_delta("covariate→numeric") 준수. provenance_gaps GAP-19(snippet↔vocab 불일치);
c0019 산문 무시 / GAP-17 / DECISION-D3 선례 동형(spec snippet frozen, 구현 레벨 override).
★verbatim postcond 검증: NaN-as-float(isinstance(nan, float)=True)를 통과시켜 "결측 0"을 강제하지
않으므로 fillna 미준수가 postcond 위반 아님(STOP 조건 미발동).

분기/라우팅(D-S4 conditional edge):
  axis gate — a7_state==KEY-MISSING→Q13(external linkage key), POLICY-MISSING→Q07(imputation
    policy). c0021 a5_state==LLOQ-MISSING 게이트와 동형(precond이 배제하는 state를 함수가 명시
    라우팅 — D-S4 + 단위테스트 self-contained).
  coding — SEX/GENDER 범주형(object)→{M:0,F:1} 매핑(spec snippet; IMPUTE와 무관), 그 외→
    pd.to_numeric(coerce, c0019 선례 방어적 변환 — 결측을 None 아닌 np.nan으로 만들어 postcond
    통과 보장). 매핑 불가 범주/파싱 불가→NaN(날조 금지).
  residual missing(NaN) 존재 → Q07(no impute). 없으면 범주형 int 확정 후 success.
c0207_passed는 orchestrator가 구조적으로 보장(D-S1) — 함수 내 미검사(c0019/c0021 동형).
입력계약(GAP-3): baseline_covariates 컬럼명 리스트 생산자 부재 — meta 선언 1차, 부재 시 df
  covariate 컬럼 fallback(빈 리스트 silent no-op 방지, Lock 3). 컬럼값 생산자=상류 정규화
  ([[PRINCIPLE]] happy 입력=선행 출력). 단위테스트는 fixture로 baseline_covariates 주입.
"""

import pandas as pd
import numpy as np

# spec snippet 범주형 매핑(M/F→0/1). IMPUTE와 무관한 코딩 규칙.
_SEX_MAP = {"M": 0, "F": 1}
_CATEGORICAL_COLS = frozenset(["sex", "gender"])

# c0207 _COVARIATE_COLS 동형 — meta 리스트 부재 시 df fallback(GAP-3 silent no-op 방지)
_COVARIATE_COLS = frozenset([
    "wt", "bw", "weight", "age", "sex", "gender", "race", "ethnic",
    "ht", "height", "bmi", "bsa", "crcl", "egfr", "alb", "alt", "ast",
    "bili", "scr", "geno", "genotype", "smok", "smoke", "formulation",
])


def _resolve_covariates(df: pd.DataFrame, meta: dict) -> list:
    declared = meta.get("baseline_covariates") if meta else None
    if declared:
        return [c for c in declared if c in df.columns]
    # df fallback(GAP-3): 선언 부재 시 알려진 covariate 컬럼 탐지
    return [c for c in df.columns if str(c).strip().lower() in _COVARIATE_COLS]


def _is_categorical(col_name) -> bool:
    return str(col_name).strip().lower() in _CATEGORICAL_COLS


def assign_baseline_covariate(df: pd.DataFrame, meta: dict) -> dict:
    df = df.copy()

    # axis gate(D-S4): A7 자기축 disjunct → Q-code (c0021 동형)
    a7_state = meta.get("a7_state") if meta else None
    if a7_state == "KEY-MISSING":
        return {"success": False, "route_to_q": "Q13", "df": df}
    if a7_state == "POLICY-MISSING":
        return {"success": False, "route_to_q": "Q07", "df": df}

    covs = _resolve_covariates(df, meta)

    # 코딩: 범주형→매핑(int 후보), 연속형→numeric coerce. 매핑/파싱 불가→np.nan(날조 금지).
    for cov in covs:
        if _is_categorical(cov):
            s = df[cov]
            if not pd.api.types.is_numeric_dtype(s):
                df[cov] = s.astype(str).str.strip().str.upper().map(_SEX_MAP)
        else:
            df[cov] = pd.to_numeric(df[cov], errors="coerce")

    # 결측 FLAG(no impute): residual NaN 존재 → Q07 (median 대입 금지, 사용자 ★★★)
    for cov in covs:
        if df[cov].isna().any():
            return {"success": False, "route_to_q": "Q07", "df": df}

    # 결측 없는 정상 공변량만 ASSIGN — 범주형은 정수 코딩 확정
    for cov in covs:
        if _is_categorical(cov):
            df[cov] = df[cov].astype(int)

    return {"success": True, "df": df}
