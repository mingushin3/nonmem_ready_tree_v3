"""ASSIGN BASELINE_COVARIATE — 기저 공변량 부착 (L-2→L-3)

srp_intent: ASSIGN BASELINE_COVARIATE
c_name_ko: 기저 공변량 부착
kind: transform  (requires_detection_by: c0207 A7 axis · can_route_to_q: [Q07])

postcondition_predicate:
    all(df.groupby('subject_id')[cov].first().notna().all() for cov in meta.get('baseline_covariates', [])) if meta.get('a7_state') != 'NONE-REQUIRED' else True

설계(사용자 ★★★ 확정 — c0022 L-1→L-2 형제 + GAP-17/19 구현 레벨 override; spec snippet frozen):
  GAP-17(시점/키): spec snippet은 df['TIME']==0로 baseline 필터하나 TIME은 하류 c0019(L-1→L-2)가
    부여 → L-2→L-3 시점엔 부재 가능. df.get('TIME')이 None이면 df['time_value']==0로 fallback.
    groupby 키도 'subject_id' 우선, 없으면 'ID'. 둘 다 없으면 Q07(구조 게이트, c0023 'ID' 부재 동형).
    time 컬럼 둘 다 없으면 Q07(KeyError 방지).
  GAP-19(IMPUTE override): llm_prompt "BASELINE-IMPUTABLE이면 imputation 정책 적용"은 *따르지 않는다*.
    vocabulary.md §A "IMPUTE 제외(자의적 결측보충 금지)" > 개별 c. 결측 baseline은 median 대입 없이
    NaN 보존(FLAG) + Q07 라우팅. 정상 baseline만 부착. 마커 컬럼 미추가 → output_schema_delta 준수.
    (c0022 GAP-19 / c0019 산문 무시 / DECISION-D3 선례 동형.)
  GAP-20(a): verbatim postcond `.groupby('subject_id')[cov].first().notna().all()`는 GroupBy.first()의
    skipna=True로 "subject당 baseline 공변량 ≥1 non-null"을 요구할 뿐 "전 행 notna"(결측0)가 아니다 →
    자의적 IMPUTE 불요. postcond 충족은 *관측 baseline의 within-subject PROPAGATE*로만(§A V10
    PROPAGATE, c0023 ffill 동류; cross-subject bleed 금지). baseline 전무 subject만 Q07(STOP 미발동).

분기/라우팅(D-S4 conditional edge):
  axis gate — a7_state==POLICY-MISSING→Q07(imputation policy). c0140 can_route_to_q=[Q07]만(c0022와
    달리 Q13 미선언; KEY-MISSING은 D-S1상 c0207이 선차단 → c0140 Q13 라우팅 안 함, scope 준수).
  structural gate — groupby 키(subject_id/ID) 부재 → Q07; baseline 시점 컬럼(TIME/time_value) 부재 → Q07.
  coding — 범주형(sex/gender)→{M:0,F:1} 매핑, 그 외→pd.to_numeric(coerce). 매핑/파싱 불가→np.nan(날조 금지).
  propagate — baseline(time==0) 값을 subject별 전 행에 부착(df[key].map(per-subject baseline)).
  residual missing(baseline 전무 subject) → Q07(no impute). 없으면 범주형 int 확정 후 success.
c0207_passed는 orchestrator가 구조적으로 보장(D-S1) — 함수 내 미검사(c0022/c0023 동형).
입력계약(GAP-3): baseline_covariates 컬럼명 리스트 생산자 부재 — meta 선언 1차, 부재 시 df covariate
  컬럼 fallback(빈 리스트 silent no-op 방지, Lock 3). 단위테스트는 fixture로 주입.
"""

import pandas as pd
import numpy as np

# 범주형 매핑(c0022 동형). IMPUTE와 무관한 코딩 규칙.
_SEX_MAP = {"M": 0, "F": 1}
_CATEGORICAL_COLS = frozenset(["sex", "gender"])

# meta 리스트 부재 시 df fallback(GAP-3 silent no-op 방지) — c0022 _COVARIATE_COLS 동형
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


def _resolve_group_key(df: pd.DataFrame):
    # GAP-17: subject_id(L-2→L-3 가용) 우선, 없으면 ID
    if "subject_id" in df.columns:
        return "subject_id"
    if "ID" in df.columns:
        return "ID"
    return None


def _resolve_time_col(df: pd.DataFrame):
    # GAP-17: TIME(하류 c0019 산출) 부재 시 time_value(semantic)로 fallback
    if df.get("TIME") is not None:
        return "TIME"
    if "time_value" in df.columns:
        return "time_value"
    return None


def assign_baseline_covariate(df: pd.DataFrame, meta: dict) -> dict:
    df = df.copy()

    a7_state = meta.get("a7_state") if meta else None

    # NONE-REQUIRED: 공변량 불요 → postcond 단락(True), 부착 없이 success
    if a7_state == "NONE-REQUIRED":
        return {"success": True, "df": df}

    # axis gate(D-S4): A7 자기축 disjunct → Q07 (c0022 POLICY-MISSING 동형; Q13 미선언)
    if a7_state == "POLICY-MISSING":
        return {"success": False, "route_to_q": "Q07", "df": df}

    # structural gate: groupby 키(GAP-17) 부재 → Q07 (c0023 동형)
    key = _resolve_group_key(df)
    if key is None:
        return {"success": False, "route_to_q": "Q07", "df": df}

    # structural gate: baseline 시점 컬럼(GAP-17) 부재 → Q07 (KeyError 방지)
    time_col = _resolve_time_col(df)
    if time_col is None:
        return {"success": False, "route_to_q": "Q07", "df": df}

    covs = _resolve_covariates(df, meta)

    # 코딩(c0022 동형): 범주형→매핑, 연속형→numeric coerce. 매핑/파싱 불가→np.nan(날조 금지).
    for cov in covs:
        if _is_categorical(cov):
            s = df[cov]
            if not pd.api.types.is_numeric_dtype(s):
                df[cov] = s.astype(str).str.strip().str.upper().map(_SEX_MAP)
        else:
            df[cov] = pd.to_numeric(df[cov], errors="coerce")

    # baseline 추출 + within-subject PROPAGATE(§A V10; cross-subject bleed 불가 — key별 map)
    base_mask = pd.to_numeric(df[time_col], errors="coerce") == 0
    for cov in covs:
        baseline = df.loc[base_mask].groupby(key)[cov].first()  # subject별 baseline(skipna)
        df[cov] = df[key].map(baseline)

    # 결측 FLAG(no impute, GAP-19): baseline 전무 subject 존재 → Q07 (median 대입 금지)
    for cov in covs:
        if df[cov].isna().any():
            return {"success": False, "route_to_q": "Q07", "df": df}

    # 결측 없는 정상 공변량 — 범주형은 정수 코딩 확정
    for cov in covs:
        if _is_categorical(cov):
            df[cov] = df[cov].astype(int)

    return {"success": True, "df": df}
