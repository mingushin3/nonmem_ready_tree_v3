"""Adversarial trap tests — silent-error detection (Phase 4)."""

import pandas as pd
import numpy as np
import pytest

from src.c_units.c0001_verify_column_schema import verify_column_schema
from src.c_units.c0010_assign_evid import assign_evid
from src.c_units.c0011_assign_mdv import assign_mdv
from src.c_units.c0012_assign_amt import assign_amt
from src.c_units.c0014_assign_rate import assign_rate
from src.c_units.c0013_assign_cmt import assign_cmt
from src.c_units.c0015_assign_addl import assign_addl
from src.c_units.c0016_assign_ii import assign_ii
from src.c_units.c0208_classify_analyte_column import classify_analyte_column
from src.c_units.c0017_assign_dv import assign_dv
from src.c_units.c0018_assign_id import assign_id
from src.c_units.c0019_assign_time import assign_time
from src.c_units.c0020_assign_blq_flag import assign_blq_flag
from src.c_units.c0021_assign_lloq import assign_lloq
from src.c_units.c0022_assign_baseline_covariate import assign_baseline_covariate
from src.c_units.c0023_assign_time_varying_covariate import assign_time_varying_covariate
from src.c_units.c0140_assign_baseline_covariate import assign_baseline_covariate as assign_baseline_covariate_l3
from src.c_units.c0141_assign_time_varying_covariate import assign_time_varying_covariate as assign_time_varying_covariate_l3
from src.c_units.c0121_pivot_covariate_layout import pivot_covariate_layout
from src.c_units.c0200_verify_a0_analysis_intent import verify_a0_analysis_intent
from src.c_units.c0204_verify_amt import verify_amt
from src.c_units.c0201_detect_sheet_inventory import detect_sheet_inventory
from src.c_units.c0202_classify_regimen_descriptor import classify_regimen_descriptor
from src.c_units.c0203_detect_time_format import detect_time_format
from src.c_units.c0205_detect_blq_token import detect_blq_token
from src.c_units.c0206_classify_row_ordering import classify_row_ordering
from src.c_units.c0207_classify_covariate_layout import classify_covariate_layout
from src.c_units.c0209_verify_cross_column_invariant import verify_cross_column_invariant
from src.c_units.c0210_detect_source_format import detect_source_format
from src.c_units.c0211_detect_above_uloq import detect_above_uloq
from src.c_units.c0212_detect_replicate_obs import detect_replicate_obs
from src.c_units.c0214_verify_unit_declaration import verify_unit_declaration
from src.c_units.c0215_detect_duplicate_row import detect_duplicate_row
from src.c_units.c0216_detect_encoding import detect_encoding
from src.c_units.c0340_detect_merged_cell import detect_merged_cell
from src.c_units.c0341_propagate_merged_cell import propagate_merged_cell
from src.c_units.c0213_verify_time_anchor import verify_time_anchor
from src.c_units.c0251_route_time_format import route_time_format
from src.c_units.c0310_detect_time_format import detect_time_format_mess
from src.c_units.c0314_detect_time_anchor import detect_time_anchor
from src.c_units.c0311_convert_time_format import convert_time_format
from src.c_units.c0315_convert_time_anchor import convert_time_anchor
from src.c_units.c0312_detect_timezone import detect_timezone
from src.c_units.c0313_normalize_timezone import normalize_timezone
from src.c_units.c0380_detect_covariate_layout import detect_covariate_layout
from src.c_units.c0381_classify_covariate_layout import classify_covariate_layout_mess
from src.c_units.c0392_detect_placebo_subject import detect_placebo_subject
from src.c_units.c0393_classify_placebo_subject import classify_placebo_subject
from src.c_units.c0305_detect_blq_token import detect_blq_token_mess
from src.c_units.c0306_normalize_blq_token import normalize_blq_token
from src.c_units.c0253_route_blq_token import route_blq_token
# slice 8 — Batch A: L-3->L-4 axis-fail ROUTE c
from src.c_units.c0250_route_column_schema import route_column_schema
from src.c_units.c0252_route_amt import route_amt
from src.c_units.c0254_route_covariate_layout import route_covariate_layout
from src.c_units.c0255_route_analyte_column import route_analyte_column
from src.c_units.c0256_route_cross_column_invariant import route_cross_column_invariant
from src.c_units.c0257_route_row_ordering import route_row_ordering


class TestC0340Adversarial:
    """c0340 adversarial traps: silent over/under-detection 차단."""

    def test_residue_present_detected(self):
        """값-다음-NaN 병합 잔존 → 반드시 True (hardcoded-False 차단)."""
        df = pd.DataFrame({
            "subject_id": [1, 1, 1],
            "dose": [100.0, np.nan, np.nan],
        })
        meta = {}
        result = detect_merged_cell(df, meta)
        assert result["has_merged_cells"] is True
        assert meta["has_merged_cells"] is True

    def test_only_leading_nan_not_detected(self):
        """선행 NaN 블록만(값-다음-NaN 없음) → False (naive any-NaN 감지기 차단)."""
        df = pd.DataFrame({
            "subject_id": [1, 1, 1],
            "dose": [np.nan, np.nan, 100.0],
        })
        meta = {}
        result = detect_merged_cell(df, meta)
        assert result["has_merged_cells"] is False

    def test_all_nan_column_not_detected(self):
        """전체-NaN 컬럼 → 잔존 아님(채울 소스 없음) → False."""
        df = pd.DataFrame({
            "x": [1, 2, 3],
            "allna": [np.nan, np.nan, np.nan],
        })
        meta = {}
        result = detect_merged_cell(df, meta)
        assert result["has_merged_cells"] is False


class TestC0341Adversarial:
    """c0341 adversarial traps: silent no-op + 교차컬럼/구조 bleed + 역방향 차단."""

    def test_silent_noop_caught(self):
        """병합 잔존 입력인데 미변환(no-op)이면 postcond 잔존 검사가 잡는다."""
        df = pd.DataFrame({"dose": [100.0, np.nan, np.nan, 200.0]})
        meta = {"has_merged_cells": True}
        result = propagate_merged_cell(df, meta)
        df_out = result["df"]
        # postcondition (verbatim, df→df_out) — no-op이면 잔존 남아 실패
        assert not meta.get('has_merged_cells', False) or not any((df_out[c].isna() & df_out[c].shift().notna()).any() for c in df_out.columns)
        assert list(df_out["dose"]) == [100.0, 100.0, 100.0, 200.0]

    def test_cross_column_bleed(self):
        """수직 ffill만: axis=1 가로채우기/구조 bleed 금지(A값이 B로 새지 않음)."""
        df = pd.DataFrame({
            "A": [1.0, np.nan, 2.0, np.nan],
            "B": [np.nan, 9.0, np.nan, 8.0],
        })
        meta = {"has_merged_cells": True}
        result = propagate_merged_cell(df, meta)
        df_out = result["df"]
        assert list(df_out["A"]) == [1.0, 1.0, 2.0, 2.0]
        assert pd.isna(df_out["B"].iloc[0])
        assert list(df_out["B"].iloc[1:]) == [9.0, 9.0, 8.0]

    def test_no_backfill_direction(self):
        """역방향 backfill 금지: 선행 NaN 보존(bfill이면 채워져 실패)."""
        df = pd.DataFrame({"v": [np.nan, 5.0, np.nan, 8.0]})
        meta = {"has_merged_cells": True}
        result = propagate_merged_cell(df, meta)
        df_out = result["df"]
        assert pd.isna(df_out["v"].iloc[0])
        assert list(df_out["v"].iloc[1:]) == [5.0, 5.0, 8.0]

    def test_detection_mandatory(self):
        """★ D-S1: c0340 미감지(meta에 has_merged_cells 없음) → success=False, 변환 안 함."""
        df = pd.DataFrame({"dose": [100.0, np.nan, np.nan]})
        meta = {}
        result = propagate_merged_cell(df, meta)
        assert result["success"] is False

    @pytest.mark.xfail(
        reason="GAP-24: c0341 global ffill cannot prevent cross-subject row bleed "
               "(pre-subject layer; subject_id boundary unknown). Mitigation = downstream "
               "subject-boundary VERIFY cut-vertex before NONMEM-ready output.",
        strict=False,
    )
    def test_cross_subject_row_bleed_known_risk(self):
        """★ GAP-24 known-risk: subj2 첫 dose 결측이 global ffill로 subj1 값을 상속하면 안 된다.
        c0341은 pre-subject(L-4->L-5)라 subject 경계를 모르고 global ffill → 현재 FAIL = xfail.
        하류 subject-boundary VERIFY가 완화(별도 c, 미구현). [[GAP-24]]."""
        df = pd.DataFrame({
            "subject_id": [1, 1, 2, 2],
            "dose": [100.0, np.nan, np.nan, 300.0],  # subj2 첫 행 dose 결측(within-subject anchor 없음)
        })
        meta = {"has_merged_cells": True}
        result = propagate_merged_cell(df, meta)
        df_out = result["df"]
        # 원하는 안전 거동: subj2 첫 행은 subj1의 100을 상속하지 말고 결측 보존.
        subj2_first_dose = df_out.loc[df_out["subject_id"] == 2, "dose"].iloc[0]
        assert pd.isna(subj2_first_dose), (
            f"cross-subject bleed: subj2 첫 dose={subj2_first_dose} (subj1 100 상속)"
        )


class TestC0001Adversarial:
    """c0001 adversarial traps: inputs that would silently pass a naive implementation."""

    def test_case_mismatch_column_names(self):
        """Subject_ID (대문자 혼합)는 subject_id와 다르다 — fail해야 한다."""
        df = pd.DataFrame({
            "Subject_ID": [1, 2],
            "event_type": ["dose", "obs"],
            "time_value": [0.0, 1.0],
            "dv_value": [None, 5.2],
        })
        result = verify_column_schema(df)
        assert result["pass"] is False
        assert "subject_id" in result["missing_columns"]

    def test_empty_dataframe_with_columns(self):
        """컬럼은 존재하지만 행이 0개 — postcondition의 notna 검증이 vacuously true."""
        df = pd.DataFrame(columns=["subject_id", "event_type", "time_value", "dv_value"])
        result = verify_column_schema(df)
        assert result["pass"] is True

    def test_all_nan_in_critical_column(self):
        """subject_id가 전부 NaN — fail해야 한다."""
        df = pd.DataFrame({
            "subject_id": [None, None],
            "event_type": ["dose", "obs"],
            "time_value": [0.0, 1.0],
            "dv_value": [None, 5.2],
        })
        result = verify_column_schema(df)
        assert result["pass"] is False

    def test_extra_columns_dont_interfere(self):
        """필수 컬럼 외 추가 컬럼이 있어도 pass해야 한다."""
        df = pd.DataFrame({
            "subject_id": [1],
            "event_type": ["obs"],
            "time_value": [1.0],
            "dv_value": [5.2],
            "extra_col": ["noise"],
        })
        result = verify_column_schema(df)
        assert result["pass"] is True

    def test_partial_nan_in_time_value(self):
        """time_value 일부 행만 NaN — fail해야 한다."""
        df = pd.DataFrame({
            "subject_id": [1, 2],
            "event_type": ["dose", "obs"],
            "time_value": [0.0, None],
            "dv_value": [None, 5.2],
        })
        result = verify_column_schema(df)
        assert result["pass"] is False

    def test_event_type_all_nan(self):
        """event_type 전체 NaN(컬럼은 존재) — postcond ② notna 위반, fail해야 한다."""
        df = pd.DataFrame({
            "subject_id": [1, 2],
            "event_type": [None, None],
            "time_value": [0.0, 1.0],
            "dv_value": [5.2, 3.1],
        })
        result = verify_column_schema(df)
        assert result["pass"] is False
        assert result["route_to"] == "INVALID"


class TestC0010Adversarial:
    """c0010 adversarial traps: inputs that would silently pass a naive EVID assignment."""

    def test_event_type_whitespace(self):
        """' dose '(앞뒤 공백) — map 키에 매칭 안 됨, Q04 route해야 한다."""
        df = pd.DataFrame({
            "subject_id": [1],
            "event_type": [" dose "],
            "time_value": [0.0],
            "dv_value": [None],
        })
        result = assign_evid(df)
        assert result["success"] is False
        assert result["route_to_q"] == "Q04"

    def test_event_type_case_mismatch(self):
        """'Dose'(대문자 시작) — case-sensitive map이므로 매핑 실패해야 한다."""
        df = pd.DataFrame({
            "subject_id": [1, 2],
            "event_type": ["Dose", "Obs"],
            "time_value": [0.0, 1.0],
            "dv_value": [None, 5.2],
        })
        result = assign_evid(df)
        assert result["success"] is False
        assert result["route_to_q"] == "Q04"

    def test_empty_df_vacuous_pass(self):
        """0행 DataFrame(컬럼 존재) — postcondition vacuously true, success해야 한다."""
        df = pd.DataFrame(columns=["subject_id", "event_type", "time_value", "dv_value"])
        result = assign_evid(df)
        assert result["success"] is True
        df_out = result["df"]
        assert "EVID" in df_out.columns
        assert len(df_out) == 0


class TestC0011Adversarial:
    """c0011 adversarial traps: inputs that would silently produce wrong MDV."""

    def test_evid1_with_valid_dv_still_mdv1(self):
        """EVID=1(dose)인데 dv_value=5.2 — dose는 항상 MDV=1이어야 한다."""
        df = pd.DataFrame({
            "EVID": [1, 0],
            "dv_value": [5.2, 3.1],
        })
        result = assign_mdv(df)
        assert result["success"] is True
        assert list(result["df"]["MDV"]) == [1, 0]

    def test_evid0_nan_dv_gets_mdv1(self):
        """EVID=0(obs)인데 dv_value=NaN — 결측 관측은 MDV=1이어야 한다."""
        df = pd.DataFrame({
            "EVID": [0, 0],
            "dv_value": [None, 5.2],
        })
        result = assign_mdv(df)
        assert result["success"] is True
        assert list(result["df"]["MDV"]) == [1, 0]

    def test_dv_value_zero_is_valid_obs(self):
        """dv_value=0.0(falsy이지만 유효 관측) — MDV=0이어야 한다."""
        df = pd.DataFrame({
            "EVID": [0],
            "dv_value": [0.0],
        })
        result = assign_mdv(df)
        assert result["success"] is True
        assert list(result["df"]["MDV"]) == [0]


class TestC0012Adversarial:
    """c0012 adversarial traps: inputs that would silently produce wrong AMT."""

    def test_obs_row_nonzero_dose_amount(self):
        """EVID=0인데 dose_amount=100 — AMT는 반드시 0이어야 한다."""
        df = pd.DataFrame({
            "EVID": [0, 1],
            "dose_amount": [100.0, 200.0],
        })
        result = assign_amt(df)
        assert result["success"] is True
        assert list(result["df"]["AMT"]) == [0.0, 200.0]

    def test_evid4_ss_dose_positive_amt(self):
        """EVID=4(ss_dose) — AMT>0이어야 한다."""
        df = pd.DataFrame({
            "EVID": [4],
            "dose_amount": [50.0],
        })
        result = assign_amt(df)
        assert result["success"] is True
        assert result["df"]["AMT"].iloc[0] == 50.0

    def test_dose_amount_nan_for_dose(self):
        """EVID=1인데 dose_amount=NaN — Q08 route해야 한다."""
        df = pd.DataFrame({
            "EVID": [1, 0],
            "dose_amount": [None, None],
        })
        result = assign_amt(df)
        assert result["success"] is False
        assert result["route_to_q"] == "Q08"


class TestC0014Adversarial:
    """c0014 adversarial traps: inputs that would silently produce wrong RATE."""

    def test_all_bolus_no_infusion_columns(self):
        """infusion_rate/rate_type 컬럼 전무 — 전부 bolus(RATE=0)이어야 한다."""
        df = pd.DataFrame({
            "EVID": [1, 0],
            "AMT": [100.0, 0.0],
        })
        result = assign_rate(df)
        assert result["success"] is True
        assert list(result["df"]["RATE"]) == [0.0, 0.0]

    def test_infusion_rate_zero_is_bolus(self):
        """infusion_rate=0.0(명시적 0) — bolus로 처리, RATE=0이어야 한다."""
        df = pd.DataFrame({
            "EVID": [1],
            "AMT": [100.0],
            "infusion_rate": [0.0],
        })
        result = assign_rate(df)
        assert result["success"] is True
        assert result["df"]["RATE"].iloc[0] == 0.0

    def test_rate_without_amt_column(self):
        """rate_type=model_rate(RATE=-1)인데 AMT 컬럼 부재 — clause 3 vacuously True."""
        df = pd.DataFrame({
            "EVID": [1],
            "rate_type": ["model_rate"],
        })
        result = assign_rate(df)
        assert result["success"] is True
        assert result["df"]["RATE"].iloc[0] == -1.0


class TestC0208Adversarial:
    """c0208 adversarial traps: inputs that would silently misclassify a8_state."""

    def test_analyte_label_with_whitespace(self):
        """' DrugA '과 'DrugA' — strip 후 1종, SINGLE-DRUG."""
        df = pd.DataFrame({
            "subject_id": [1, 1],
            "event_type": ["dose", "obs"],
            "time_value": [0.0, 1.0],
            "dv_value": [None, 5.2],
            "analyte_label": [" DrugA ", "DrugA"],
            "admin_route": ["PO", "PO"],
        })
        meta = {}
        result = classify_analyte_column(df, meta)
        assert result["a8_state"] == "SINGLE-DRUG"

    def test_analyte_label_case_sensitivity(self):
        """'DrugA' vs 'druga' — case-insensitive 비교, SINGLE-DRUG."""
        df = pd.DataFrame({
            "subject_id": [1, 1],
            "event_type": ["dose", "obs"],
            "time_value": [0.0, 1.0],
            "dv_value": [None, 5.2],
            "analyte_label": ["DrugA", "druga"],
            "admin_route": ["PO", "PO"],
        })
        meta = {}
        result = classify_analyte_column(df, meta)
        assert result["a8_state"] == "SINGLE-DRUG"

    def test_df_readonly_not_modified(self):
        """kind=detect → df 변경 금지(SRP)."""
        df = pd.DataFrame({
            "subject_id": [1],
            "event_type": ["obs"],
            "time_value": [1.0],
            "dv_value": [5.2],
            "analyte_label": ["DrugA"],
            "admin_route": ["PO"],
        })
        original_cols = list(df.columns)
        original_shape = df.shape
        meta = {}
        classify_analyte_column(df, meta)
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_meta_a8_state_is_written(self):
        """meta['a8_state'] side-effect 기록 확인."""
        df = pd.DataFrame({
            "subject_id": [1],
            "event_type": ["obs"],
            "time_value": [1.0],
            "dv_value": [5.2],
        })
        meta = {}
        classify_analyte_column(df, meta)
        assert "a8_state" in meta
        assert meta["a8_state"] in [
            "SINGLE-DRUG", "MULTI-CMT-DEFINED", "DDI-VICTIM-ONLY",
            "DDI-VICTIM-PERPETRATOR", "METABOLITE-DEFINED", "CMT-POLICY-MISSING",
        ]

    def test_empty_perpetrator_list_means_victim_only(self):
        """perpetrator_analytes=[] → DDI-VICTIM-ONLY."""
        df = pd.DataFrame({
            "subject_id": [1],
            "event_type": ["obs"],
            "time_value": [1.0],
            "dv_value": [5.2],
            "analyte_label": ["Midazolam"],
            "admin_route": ["PO"],
        })
        meta = {"study_type": "DDI", "perpetrator_analytes": []}
        result = classify_analyte_column(df, meta)
        assert result["a8_state"] == "DDI-VICTIM-ONLY"

    def test_all_nan_analyte_label(self):
        """analyte_label 전부 NaN → 유효 analyte 0종, SINGLE-DRUG."""
        df = pd.DataFrame({
            "subject_id": [1, 2],
            "event_type": ["dose", "obs"],
            "time_value": [0.0, 1.0],
            "dv_value": [None, 5.2],
            "analyte_label": [None, None],
            "admin_route": ["PO", "PO"],
        })
        meta = {}
        result = classify_analyte_column(df, meta)
        assert result["a8_state"] == "SINGLE-DRUG"

    def test_ddi_takes_priority_over_metabolite(self):
        """DDI + metabolite 동시 존재 → DDI 우선 (decision tree step 1)."""
        df = pd.DataFrame({
            "subject_id": [1, 1],
            "event_type": ["obs", "obs"],
            "time_value": [1.0, 1.0],
            "dv_value": [5.2, 1.8],
            "analyte_label": ["DrugA", "DrugA_M1"],
            "admin_route": ["PO", "PO"],
        })
        meta = {
            "study_type": "DDI",
            "perpetrator_analytes": ["DrugA_M1"],
            "parent_metabolite_map": {"DrugA": "parent", "DrugA_M1": "metabolite"},
        }
        result = classify_analyte_column(df, meta)
        assert result["a8_state"] == "DDI-VICTIM-PERPETRATOR"


class TestC0013Adversarial:
    """c0013 adversarial traps: inputs that would silently produce wrong CMT."""

    def test_evid2_reset_gets_dose_cmt(self):
        """EVID=2(reset)는 dose 구획(CMT=1)이어야 한다(0이나 NA가 아님)."""
        df = pd.DataFrame({
            "EVID": [1, 2, 0],
            "analyte_label": ["DrugA", "DrugA", "DrugA"],
        })
        meta = {"a8_state": "SINGLE-DRUG"}
        result = assign_cmt(df, meta)
        assert result["success"] is True
        assert result["df"]["CMT"].iloc[1] == 1

    def test_obs_gets_obs_cmt_not_dose(self):
        """EVID=0(obs) + dose_amount 존재해도 CMT=2(obs), not 1(dose)."""
        df = pd.DataFrame({
            "EVID": [0],
            "analyte_label": ["DrugA"],
            "dose_amount": [100.0],
        })
        meta = {"a8_state": "SINGLE-DRUG"}
        result = assign_cmt(df, meta)
        assert result["success"] is True
        assert result["df"]["CMT"].iloc[0] == 2

    def test_cmt_is_int_not_float(self):
        """CMT dtype은 int여야 한다(float이면 postcond clause 3 위반)."""
        df = pd.DataFrame({
            "EVID": [1, 0],
            "analyte_label": ["DrugA", "DrugA"],
        })
        meta = {"a8_state": "SINGLE-DRUG"}
        result = assign_cmt(df, meta)
        assert result["success"] is True
        for val in result["df"]["CMT"]:
            assert isinstance(val, (int, np.integer))

    def test_input_df_not_mutated(self):
        """transform은 df.copy()를 사용해야 한다 — 원본 df 변경 금지."""
        df = pd.DataFrame({
            "EVID": [1, 0],
            "analyte_label": ["DrugA", "DrugA"],
        })
        original_cols = list(df.columns)
        meta = {"a8_state": "SINGLE-DRUG"}
        assign_cmt(df, meta)
        assert list(df.columns) == original_cols
        assert "CMT" not in df.columns

    def test_ddi_victim_only_same_as_single_drug(self):
        """DDI-VICTIM-ONLY는 SINGLE-DRUG과 CMT 출력이 동일해야 한다(상대 동치 invariant).

        값을 하드코딩하지 않고, 같은 df를 두 state로 통과시켜 출력이 서로 같은지만 본다.
        절대값 검증은 happy fixture(test_happy_ddi_victim_only)가 담당한다.
        """
        df = pd.DataFrame({
            "EVID": [1, 0, 4, 0],
            "analyte_label": ["Midazolam", "Midazolam", "Midazolam", "Midazolam"],
        })
        res_single = assign_cmt(df, {"a8_state": "SINGLE-DRUG"})
        res_victim = assign_cmt(df, {"a8_state": "DDI-VICTIM-ONLY"})
        assert res_single["success"] is True
        assert res_victim["success"] is True
        assert list(res_victim["df"]["CMT"]) == list(res_single["df"]["CMT"])


class TestC0015Adversarial:
    """c0015 adversarial traps: inputs that would silently produce wrong ADDL."""

    def test_input_df_not_mutated(self):
        """transform은 df.copy()를 사용해야 한다 — 원본 df 변경 금지."""
        df = pd.DataFrame({
            "ID": [1, 1, 1],
            "EVID": [1, 1, 0],
            "AMT": [100.0, 100.0, 0.0],
            "TIME": [0.0, 24.0, 1.0],
        })
        original_cols = list(df.columns)
        original_len = len(df)
        assign_addl(df, {})
        assert list(df.columns) == original_cols
        assert "ADDL" not in df.columns
        assert len(df) == original_len

    def test_unequal_interval_not_compressed(self):
        """불규칙 간격(@0/24/50)은 압축하면 안 된다 — 행 수 보존, 모든 ADDL=0."""
        df = pd.DataFrame({
            "ID": [1, 1, 1],
            "EVID": [1, 1, 1],
            "AMT": [100.0, 100.0, 100.0],
            "TIME": [0.0, 24.0, 50.0],
        })
        result = assign_addl(df, {})
        assert result["success"] is True
        df_out = result["df"]
        assert len(df_out) == 3
        assert list(df_out["ADDL"]) == [0, 0, 0]

    def test_addl_is_int_not_float(self):
        """ADDL dtype은 정수여야 한다(float이면 postcond clause 3 위반)."""
        df = pd.DataFrame({
            "ID": [1, 1, 1],
            "EVID": [1, 1, 1],
            "AMT": [100.0, 100.0, 100.0],
            "TIME": [0.0, 12.0, 24.0],
        })
        result = assign_addl(df, {})
        assert result["success"] is True
        for val in result["df"]["ADDL"]:
            assert isinstance(val, (int, np.integer))

    def test_conflict_routes_q14(self):
        """A4=ADDL-ACTUAL-CONFLICT면 silent 압축 금지 — fail, Q14."""
        df = pd.DataFrame({
            "ID": [1, 1],
            "EVID": [1, 1],
            "AMT": [100.0, 100.0],
            "TIME": [0.0, 24.0],
        })
        result = assign_addl(df, {"a4_state": "ADDL-ACTUAL-CONFLICT"})
        assert result["success"] is False
        assert result["route_to_q"] == "Q14"

    def test_equal_doses_compressed(self):
        """등간격 동일 dose 3회 → 첫 행 ADDL=2, 나머지 dose 행 제거(압축 누락 방지)."""
        df = pd.DataFrame({
            "ID": [1, 1, 1, 1],
            "EVID": [1, 1, 1, 0],
            "AMT": [100.0, 100.0, 100.0, 0.0],
            "TIME": [0.0, 12.0, 24.0, 6.0],
        })
        result = assign_addl(df, {})
        assert result["success"] is True
        df_out = result["df"]
        assert len(df_out) == 2
        assert df_out["ADDL"].iloc[0] == 2

    def test_separate_subjects_not_merged(self):
        """다른 subject의 동일 dose는 합쳐 압축하면 안 된다 — 각 subject 독립 ADDL."""
        df = pd.DataFrame({
            "ID": [1, 1, 2, 2],
            "EVID": [1, 1, 1, 1],
            "AMT": [100.0, 100.0, 100.0, 100.0],
            "TIME": [0.0, 24.0, 0.0, 24.0],
        })
        result = assign_addl(df, {})
        assert result["success"] is True
        df_out = result["df"]
        assert len(df_out) == 2
        assert list(df_out["ADDL"]) == [1, 1]


class TestC0016Adversarial:
    """c0016 adversarial traps: inputs that would silently produce wrong II."""

    def test_addl_pos_nan_interval_routes_q14(self):
        """ADDL>0인데 dose_interval 결측 → II=NaN을 silent 통과시키지 않고 Q14."""
        df = pd.DataFrame({
            "ADDL": [2, 0],
            "TIME": [0.0, 1.0],
            "dose_interval": [np.nan, np.nan],
        })
        result = assign_ii(df)
        assert result["success"] is False
        assert result["route_to_q"] == "Q14"

    def test_zero_addl_forces_ii_zero(self):
        """ADDL=0인데 dose_interval=24 — II는 반드시 0(ADDL==0⟹II==0)."""
        df = pd.DataFrame({
            "ADDL": [0],
            "TIME": [1.0],
            "dose_interval": [24.0],
        })
        result = assign_ii(df)
        assert result["success"] is True
        assert result["df"]["II"].iloc[0] == 0

    def test_addl_pos_zero_interval_routes_q14(self):
        """ADDL>0인데 dose_interval=0 → ADDL>0⟹II>0 위반, Q14."""
        df = pd.DataFrame({
            "ADDL": [3],
            "TIME": [0.0],
            "dose_interval": [0.0],
        })
        result = assign_ii(df)
        assert result["success"] is False
        assert result["route_to_q"] == "Q14"

    def test_input_df_not_mutated(self):
        """transform은 df.copy()를 사용해야 한다 — 원본 df 변경 금지."""
        df = pd.DataFrame({
            "ADDL": [1],
            "TIME": [0.0],
            "dose_interval": [24.0],
        })
        original_cols = list(df.columns)
        assign_ii(df)
        assert list(df.columns) == original_cols
        assert "II" not in df.columns

    def test_missing_addl_column_fails(self):
        """ADDL 컬럼 부재(c0015 미통과) → silent II 생성 금지, fail."""
        df = pd.DataFrame({
            "TIME": [0.0],
            "dose_interval": [24.0],
        })
        result = assign_ii(df)
        assert result["success"] is False


class TestC0200Adversarial:
    """c0200 adversarial traps: inputs that would silently misclassify a0_state."""

    def _df(self):
        return pd.DataFrame({"subject_id": [1, 1], "time_value": [0.0, 1.0], "dv_value": [None, 5.2]})

    def test_df_readonly_not_modified(self):
        """kind=verify → df 변경 금지(SRP)."""
        df = self._df()
        original_cols = list(df.columns)
        original_shape = df.shape
        verify_a0_analysis_intent(df, {"analysis_intent": "AIC-PK"})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_meta_a0_state_is_written(self):
        """meta['a0_state'] side-effect 기록 확인."""
        meta = {"analysis_intent": "AIC-DDI"}
        verify_a0_analysis_intent(self._df(), meta)
        assert "a0_state" in meta
        assert meta["a0_state"] in [
            "AIC-MISSING", "AIC-PK", "AIC-POPPK", "AIC-PKPD", "AIC-ER",
            "AIC-DDI", "AIC-PEDS", "AIC-SPECIAL", "AIC-CUSTOM",
        ]

    def test_analysis_intent_whitespace(self):
        """' AIC-PK ' (앞뒤 공백) → strip 후 AIC-PK."""
        result = verify_a0_analysis_intent(self._df(), {"analysis_intent": " AIC-PK "})
        assert result["a0_state"] == "AIC-PK"

    def test_analysis_intent_case_insensitive(self):
        """'aic-pkpd' (소문자) + endpoint → 정규화 후 AIC-PKPD."""
        result = verify_a0_analysis_intent(
            self._df(), {"analysis_intent": "aic-pkpd", "endpoint_data_type": "CONTINUOUS_PD"}
        )
        assert result["a0_state"] == "AIC-PKPD"

    def test_out_of_scope_endpoint_not_silent_pass(self):
        """AIC-ER + scope 밖 endpoint → AIC-ER로 silent pass 금지, AIC-MISSING/Q11."""
        result = verify_a0_analysis_intent(
            self._df(), {"analysis_intent": "AIC-ER", "endpoint_data_type": "TTE_EVENT"}
        )
        assert result["a0_state"] == "AIC-MISSING"
        assert result["pass"] is False
        assert result["route_to_q"] == "Q11"

    def test_pkpd_missing_endpoint_not_silent_pass(self):
        """AIC-PKPD인데 endpoint(필수) 부재 → AIC-PKPD로 silent pass 금지, Q11."""
        result = verify_a0_analysis_intent(self._df(), {"analysis_intent": "AIC-PKPD"})
        assert result["a0_state"] == "AIC-MISSING"
        assert result["route_to_q"] == "Q11"

    def test_blank_intent_is_missing_not_present(self):
        """공백뿐인 intent는 '선언됨'이 아니라 부재 → AIC-MISSING."""
        result = verify_a0_analysis_intent(self._df(), {"analysis_intent": "   "})
        assert result["a0_state"] == "AIC-MISSING"


class TestC0204Adversarial:
    """c0204 adversarial traps: inputs that would silently misclassify a4_state."""

    def _dose_df(self):
        return pd.DataFrame({
            "subject_id": [1, 1],
            "EVID": [1, 0],
            "AMT": [100.0, None],
            "time_value": [0.0, 1.0],
            "dv_value": [None, 5.2],
        })

    def _obs_only_df(self):
        return pd.DataFrame({
            "subject_id": [1, 1],
            "EVID": [0, 0],
            "AMT": [None, None],
            "time_value": [1.0, 2.0],
            "dv_value": [5.2, 3.1],
        })

    def test_df_readonly_not_modified(self):
        """kind=verify → df 변경 금지(SRP)."""
        df = self._dose_df()
        original_cols = list(df.columns)
        original_shape = df.shape
        verify_amt(df, {})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_meta_a4_state_is_written(self):
        """meta['a4_state'] side-effect 기록 확인."""
        meta = {"dose_regimen": "combination"}
        verify_amt(self._dose_df(), meta)
        assert "a4_state" in meta
        assert meta["a4_state"] in [
            "COMPLETE", "WEIGHT-BASED", "BSA-BASED", "PLANNED-FALLBACK", "ADDL-II",
            "ADDL-ACTUAL-CONFLICT", "TITRATION-ADAPTIVE", "LOADING-MAINTENANCE",
            "INFUSION-STOP-RESTART", "PARTIAL-RECOVERY", "COMBINATION",
            "MISSING-NO-POLICY", "UNRECOVERABLE",
        ]

    def test_conflict_priority_not_swallowed(self):
        """충돌 + regimen 혼재 시 regimen이 충돌을 silent하게 가리면 안 됨 → ADDL-ACTUAL-CONFLICT 우선."""
        meta = {"has_addl_actual_conflict": True, "dose_regimen": "weight-based"}
        result = verify_amt(self._dose_df(), meta)
        assert result["a4_state"] == "ADDL-ACTUAL-CONFLICT"
        assert result["route_to_q"] == "Q14"

    def test_no_doses_not_silent_complete(self):
        """obs만 있고 dose 행 0 → COMPLETE로 silent 통과 금지, MISSING-NO-POLICY/Q08."""
        result = verify_amt(self._obs_only_df(), {})
        assert result["a4_state"] == "MISSING-NO-POLICY"
        assert result["pass"] is False
        assert result["route_to_q"] == "Q08"

    def test_titration_no_policy_routes_q08_not_pass(self):
        """가변용량 정책 부재가 silent pass되면 안 됨 → route Q08."""
        result = verify_amt(self._dose_df(), {"dose_regimen": "titration"})
        assert result["a4_state"] == "TITRATION-ADAPTIVE"
        assert result["pass"] is False
        assert result["route_to_q"] == "Q08"

    def test_infusion_does_not_invent_q04(self):
        """INFUSION-STOP-RESTART는 can_route_to_q 밖 Q04를 날조하지 않는다 → route_to_q=None."""
        result = verify_amt(self._dose_df(), {"dose_regimen": "infusion-stop-restart"})
        assert result["a4_state"] == "INFUSION-STOP-RESTART"
        assert result["route_to_q"] is None

    def test_unrecoverable_does_not_invent_invalid(self):
        """UNRECOVERABLE은 can_route_to_q 밖 INVALID/Q를 날조하지 않는다 → route_to_q=None."""
        result = verify_amt(self._dose_df(), {"dose_regimen": "unrecoverable"})
        assert result["a4_state"] == "UNRECOVERABLE"
        assert result["route_to_q"] is None

    def test_regimen_whitespace_case_normalized(self):
        """' Loading-Maintenance ' (공백·대소문자·구분자) → 정규화 후 LOADING-MAINTENANCE."""
        result = verify_amt(self._dose_df(), {"dose_regimen": " Loading-Maintenance ", "dose_policy_present": True})
        assert result["a4_state"] == "LOADING-MAINTENANCE"
        assert result["route_to_q"] is None


class TestC0017Adversarial:
    """c0017 adversarial traps: inputs that would silently produce wrong DV."""

    def test_obs_dv_equals_measurement(self):
        """유효 obs(EVID=0,MDV=0)의 DV는 입력 측정값과 같아야 한다(0으로 덮어쓰지 않음)."""
        measured = 7.34
        df = pd.DataFrame({"EVID": [0], "MDV": [0], "dv_value": [measured]})
        result = assign_dv(df)
        assert result["success"] is True
        assert result["df"]["DV"].iloc[0] == measured

    def test_mdv1_row_dv_zero(self):
        """MDV=1 행은 dv_value가 있어도 DV=0(무시 규격)."""
        df = pd.DataFrame({"EVID": [1], "MDV": [1], "dv_value": [999.0]})
        result = assign_dv(df)
        assert result["success"] is True
        assert result["df"]["DV"].iloc[0] == 0

    def test_obs_missing_value_fails(self):
        """유효 obs인데 측정값 결측 → DV NaN을 silent 통과시키지 않고 fail."""
        df = pd.DataFrame({"EVID": [0, 0], "MDV": [0, 0], "dv_value": [np.nan, 5.0]})
        result = assign_dv(df)
        assert result["success"] is False

    def test_input_df_not_mutated(self):
        """transform은 df.copy()를 사용해야 한다 — 원본 df 변경 금지."""
        df = pd.DataFrame({"EVID": [0], "MDV": [0], "dv_value": [1.0]})
        original_cols = list(df.columns)
        assign_dv(df)
        assert list(df.columns) == original_cols
        assert "DV" not in df.columns


class TestC0018Adversarial:
    """c0018 adversarial traps: inputs that would silently produce wrong ID."""

    def test_same_subject_same_id(self):
        """동일 subject_id 행들은 같은 ID로 매핑되어야 한다(상대 invariant)."""
        df = pd.DataFrame({"subject_id": ["A", "B", "A", "B", "A"]})
        result = assign_id(df)
        assert result["success"] is True
        ids = result["df"]["ID"]
        assert ids.iloc[0] == ids.iloc[2] == ids.iloc[4]  # A
        assert ids.iloc[1] == ids.iloc[3]  # B

    def test_distinct_subjects_distinct_ids(self):
        """서로 다른 subject_id 수만큼 고유 ID가 생성되어야 한다."""
        df = pd.DataFrame({"subject_id": ["A", "B", "C", "A"]})
        result = assign_id(df)
        assert result["success"] is True
        assert result["df"]["ID"].nunique() == df["subject_id"].nunique()

    def test_id_is_int_not_float(self):
        """ID는 정수형이어야 한다(leading-zero 문자열 포함, float이면 postcond clause 3 위반)."""
        df = pd.DataFrame({"subject_id": ["007", "007", "012"]})
        result = assign_id(df)
        assert result["success"] is True
        for val in result["df"]["ID"]:
            assert isinstance(val, (int, np.integer))

    def test_missing_subject_id_fails(self):
        """subject_id 결측을 ID=0 등으로 silent 채우지 않고 fail."""
        df = pd.DataFrame({"subject_id": ["A", np.nan, "B"]})
        result = assign_id(df)
        assert result["success"] is False

    def test_input_df_not_mutated(self):
        """transform은 df.copy()를 사용해야 한다 — 원본 df 변경 금지."""
        df = pd.DataFrame({"subject_id": ["A", "B"]})
        original_cols = list(df.columns)
        assign_id(df)
        assert list(df.columns) == original_cols
        assert "ID" not in df.columns


class TestC0201Adversarial:
    """c0201 adversarial traps: inputs that would silently misclassify a1_state."""

    def _df(self):
        return pd.DataFrame({
            "subject_id": [1, 2],
            "study_id": ["STUDY_001", "STUDY_001"],
        })

    def test_df_readonly_not_modified(self):
        """kind=detect → df 변경 금지(SRP)."""
        df = self._df()
        original_cols = list(df.columns)
        original_shape = df.shape
        detect_sheet_inventory(df, {})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_meta_a1_state_is_written(self):
        """meta['a1_state'] side-effect 기록 확인."""
        meta = {"study_integration": "multi-site", "harmonization_policy_present": True}
        detect_sheet_inventory(self._df(), meta)
        assert "a1_state" in meta
        assert meta["a1_state"] in [
            "SINGLE", "MULTI-HOMO", "MULTI-HETERO", "MULTI-SITE", "INTERIM",
        ]

    def test_descriptor_whitespace_case_normalized(self):
        """' Multi-Site ' (공백·대소문자·구분자) → 정규화 후 MULTI-SITE."""
        result = detect_sheet_inventory(self._df(), {"study_integration": " Multi-Site ", "harmonization_policy_present": True})
        assert result["a1_state"] == "MULTI-SITE"
        assert result["route_to_q"] is None

    def test_multi_no_policy_routes_q05_not_pass(self):
        """MULTI-* + harmonization 정책 부재가 silent pass되면 안 됨 → route Q05."""
        result = detect_sheet_inventory(self._df(), {"study_integration": "multi-homo"})
        assert result["a1_state"] == "MULTI-HOMO"
        assert result["pass"] is False
        assert result["route_to_q"] == "Q05"

    def test_single_does_not_invent_q05(self):
        """SINGLE은 can_route_to_q 밖 Q를 날조하지 않는다 → route_to_q=None."""
        result = detect_sheet_inventory(self._df(), {"study_integration": "single"})
        assert result["a1_state"] == "SINGLE"
        assert result["route_to_q"] is None

    def test_interim_not_routed(self):
        """INTERIM은 Q05 trigger 대상이 아니다 → route_to_q=None."""
        result = detect_sheet_inventory(self._df(), {"study_integration": "interim"})
        assert result["a1_state"] == "INTERIM"
        assert result["route_to_q"] is None

    def test_declared_multi_wins_over_single_looking_df(self):
        """df study_id가 1개로 보여도 선언이 multi면 SINGLE로 silent 격하 금지."""
        result = detect_sheet_inventory(self._df(), {"study_integration": "multi-hetero", "harmonization_policy_present": True})
        assert result["a1_state"] == "MULTI-HETERO"


class TestC0202Adversarial:
    """c0202 adversarial traps: inputs that would silently misclassify a2_state.

    can_route_to_q=[] → 순수 분류기. Q 라우팅 trap 없음(route_to_q 항상 None).
    """

    def _df(self):
        return pd.DataFrame({
            "subject_id": [1, 1, 2],
            "time_value": [0.0, 1.0, 0.0],
            "dv_value": [5.2, 3.1, 4.8],
        })

    def _df_xover(self):
        return pd.DataFrame({
            "subject_id": [1, 1, 2],
            "period": [1, 2, 1],
            "sequence": ["AB", "BA", "AB"],
            "time_value": [0.0, 0.0, 0.0],
            "dv_value": [5.2, 4.8, 5.0],
        })

    def _df_repeated_dose(self):
        # SAD-MAD처럼 다회 투여로 보이지만 period/sequence 없음 → fallback이 구분 못 함
        return pd.DataFrame({
            "subject_id": [1, 1, 1, 1],
            "time_value": [0.0, 24.0, 48.0, 72.0],
            "dv_value": [5.2, 4.9, 5.1, 5.0],
        })

    def test_df_readonly_not_modified(self):
        """kind=detect → df 변경 금지(SRP)."""
        df = self._df()
        original_cols = list(df.columns)
        original_shape = df.shape
        classify_regimen_descriptor(df, {"study_design": "parallel"})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_meta_a2_state_is_written(self):
        """meta['a2_state'] side-effect 기록 확인 + 10-state 범위."""
        meta = {"study_design": "ddi"}
        classify_regimen_descriptor(self._df(), meta)
        assert "a2_state" in meta
        assert meta["a2_state"] in [
            "PARALLEL", "SAD-MAD", "CROSSOVER", "BE", "DDI",
            "FOOD-EFFECT", "SPECIAL-POP", "PEDIATRIC", "TDM-RWD", "PRECLINICAL",
        ]

    def test_descriptor_whitespace_case_normalized(self):
        """' Food-Effect ' (공백·대소문자) → FOOD-EFFECT."""
        result = classify_regimen_descriptor(self._df(), {"study_design": " Food-Effect "})
        assert result["a2_state"] == "FOOD-EFFECT"
        assert result["route_to_q"] is None

    def test_pure_classifier_never_routes_q(self):
        """can_route_to_q=[] → 어떤 state도 Q를 날조하지 않는다(route_to_q None, pass True)."""
        for desc in ["parallel", "sad-mad", "crossover", "be", "ddi",
                     "food-effect", "special-pop", "pediatric", "tdm-rwd", "preclinical"]:
            result = classify_regimen_descriptor(self._df(), {"study_design": desc})
            assert result["route_to_q"] is None
            assert result["pass"] is True

    def test_unknown_descriptor_deterministic_fallback(self):
        """미지의 선언이 out-of-vocab state를 만들거나 crash하면 안 됨 → 유효 10-state로 fallback."""
        result = classify_regimen_descriptor(self._df(), {"study_design": "totally-unknown-xyz"})
        assert result["a2_state"] in [
            "PARALLEL", "SAD-MAD", "CROSSOVER", "BE", "DDI",
            "FOOD-EFFECT", "SPECIAL-POP", "PEDIATRIC", "TDM-RWD", "PRECLINICAL",
        ]
        assert result["a2_state"] == "PARALLEL"  # 평이한 df → 기본값
        assert result["route_to_q"] is None

    def test_fallback_limit_sad_mad_to_parallel(self):
        """문서화된 한계(GAP-9): 선언 부재 + period/seq 없는 다회투여 df는 SAD-MAD를 구분 못 하고
        PARALLEL 기본값으로 떨어진다. 버그가 아니라 fallback이 8개 design을 구분하지 못함을 고정."""
        result = classify_regimen_descriptor(self._df_repeated_dose(), {})
        assert result["a2_state"] == "PARALLEL"
        assert result["route_to_q"] is None

    def test_declaration_wins_over_df_signal(self):
        """선언 BE가 period/sequence df(CROSSOVER 신호) 때문에 silent 혼동되면 안 됨 → BE."""
        result = classify_regimen_descriptor(self._df_xover(), {"study_design": "be"})
        assert result["a2_state"] == "BE"
        assert result["route_to_q"] is None


class TestC0203Adversarial:
    """c0203 adversarial traps: inputs that would silently misclassify a3_state."""

    def _df(self):
        return pd.DataFrame({
            "subject_id": [1, 1],
            "time_value": [0.0, 1.0],
        })

    def _df_text(self):
        return pd.DataFrame({
            "subject_id": [1, 1],
            "time_value": ["predose", "1.0"],
        })

    def _df_null(self):
        return pd.DataFrame({
            "subject_id": [1, 1],
            "time_value": [None, None],
        })

    def test_df_readonly_not_modified(self):
        """kind=detect → df 변경 금지(SRP)."""
        df = self._df()
        original_cols = list(df.columns)
        original_shape = df.shape
        detect_time_format(df, {})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_meta_a3_state_is_written(self):
        """meta['a3_state'] side-effect 기록 확인."""
        meta = {"time_policy": "elapsed"}
        detect_time_format(self._df(), meta)
        assert "a3_state" in meta
        assert meta["a3_state"] in [
            "ACTUAL", "NOMINAL-ONLY", "ACTUAL-PREFERRED", "NOMINAL-PREFERRED",
            "ELAPSED", "INTERVAL", "AMBIGUOUS", "UNRECOVERABLE",
        ]

    def test_policy_whitespace_case_normalized(self):
        """' Actual-Preferred ' (공백·대소문자·구분자) → 정규화 후 ACTUAL-PREFERRED."""
        result = detect_time_format(self._df(), {"time_policy": " Actual-Preferred "})
        assert result["a3_state"] == "ACTUAL-PREFERRED"
        assert result["route_to_q"] is None

    def test_ambiguous_routes_q02(self):
        """AMBIGUOUS는 can_route_to_q의 Q02로 라우팅 → route Q02."""
        result = detect_time_format(self._df(), {"time_policy": "ambiguous"})
        assert result["a3_state"] == "AMBIGUOUS"
        assert result["pass"] is False
        assert result["route_to_q"] == "Q02"

    def test_unrecoverable_routes_q12_not_invalid(self):
        """UNRECOVERABLE은 INVALID/None로 silent 처리하지 않고 q_codes Q12로 라우팅."""
        result = detect_time_format(self._df(), {"time_policy": "unrecoverable"})
        assert result["a3_state"] == "UNRECOVERABLE"
        assert result["pass"] is False
        assert result["route_to_q"] == "Q12"

    def test_clean_state_not_routed(self):
        """ACTUAL은 Q를 날조하지 않는다 → route_to_q=None."""
        result = detect_time_format(self._df(), {"time_policy": "actual"})
        assert result["a3_state"] == "ACTUAL"
        assert result["route_to_q"] is None

    def test_unparseable_not_silent_actual(self):
        """텍스트 토큰 혼재 시간을 ACTUAL로 silent 통과 금지 → AMBIGUOUS."""
        result = detect_time_format(self._df_text(), {})
        assert result["a3_state"] == "AMBIGUOUS"

    def test_all_null_not_silent_actual(self):
        """time_value 전부 결측을 ACTUAL로 silent 통과 금지 → UNRECOVERABLE."""
        result = detect_time_format(self._df_null(), {})
        assert result["a3_state"] == "UNRECOVERABLE"


class TestC0205Adversarial:
    """c0205 adversarial traps: inputs that would silently misclassify a5_state."""

    def _df(self):
        return pd.DataFrame({
            "subject_id": [1, 1],
            "dv_value": [5.2, 3.1],
        })

    def _df_text(self):
        return pd.DataFrame({
            "subject_id": [1, 1],
            "dv_value": ["<LLOQ", "3.1"],
        })

    def _df_null(self):
        return pd.DataFrame({
            "subject_id": [1, 1],
            "dv_value": [None, None],
        })

    def test_df_readonly_not_modified(self):
        """kind=detect → df 변경 금지(SRP)."""
        df = self._df()
        original_cols = list(df.columns)
        original_shape = df.shape
        detect_blq_token(df, {})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_meta_a5_state_is_written(self):
        """meta['a5_state'] side-effect 기록 확인."""
        meta = {"obs_blq_state": "blq-flagged"}
        detect_blq_token(self._df(), meta)
        assert "a5_state" in meta
        assert meta["a5_state"] in [
            "CLEAN", "BLQ-FLAGGED", "BLQ-TEXT", "BLQ-ZERO", "MULTI-ANALYTE",
            "LLOQ-CHANGED", "MISSING-MDV1", "BIOANALYTICAL-FINAL-FLAG-MISSING",
            "ABOVE-ULOQ", "ABOVE-ULOQ-NO-POLICY", "REPLICATE-SAME-TIME",
            "REPLICATE-NO-POLICY", "BLQ-NO-POLICY", "LLOQ-MISSING", "ABSENT",
        ]

    def test_descriptor_whitespace_case_normalized(self):
        """' Above-ULOQ-No-Policy ' (공백·대소문자·구분자) → ABOVE-ULOQ-NO-POLICY, Q01."""
        result = detect_blq_token(self._df(), {"obs_blq_state": " Above-ULOQ-No-Policy "})
        assert result["a5_state"] == "ABOVE-ULOQ-NO-POLICY"
        assert result["route_to_q"] == "Q01"

    def test_blq_no_policy_routes_q01(self):
        """BLQ-NO-POLICY는 can_route_to_q의 Q01로 라우팅 → route Q01."""
        result = detect_blq_token(self._df(), {"obs_blq_state": "blq-no-policy"})
        assert result["a5_state"] == "BLQ-NO-POLICY"
        assert result["pass"] is False
        assert result["route_to_q"] == "Q01"

    def test_final_flag_missing_routes_q15d_not_q01(self):
        """BIOANALYTICAL-FINAL-FLAG-MISSING은 Q01이 아니라 Q15D로 라우팅."""
        result = detect_blq_token(self._df(), {"obs_blq_state": "bioanalytical-final-flag-missing"})
        assert result["a5_state"] == "BIOANALYTICAL-FINAL-FLAG-MISSING"
        assert result["route_to_q"] == "Q15D"

    def test_absent_does_not_invent_q(self):
        """ABSENT는 can_route_to_q 밖 Q/INVALID를 날조하지 않는다 → route_to_q=None (GAP-8)."""
        result = detect_blq_token(self._df(), {"obs_blq_state": "absent"})
        assert result["a5_state"] == "ABSENT"
        assert result["route_to_q"] is None

    def test_clean_state_not_routed(self):
        """CLEAN은 Q를 날조하지 않는다 → route_to_q=None."""
        result = detect_blq_token(self._df(), {"obs_blq_state": "clean"})
        assert result["a5_state"] == "CLEAN"
        assert result["route_to_q"] is None

    def test_blq_text_not_silent_clean(self):
        """DV의 '<LLOQ' 텍스트를 CLEAN으로 silent 통과 금지 → BLQ-TEXT."""
        result = detect_blq_token(self._df_text(), {})
        assert result["a5_state"] == "BLQ-TEXT"

    def test_all_null_dv_not_silent_clean(self):
        """DV 전부 결측을 CLEAN으로 silent 통과 금지 → ABSENT."""
        result = detect_blq_token(self._df_null(), {})
        assert result["a5_state"] == "ABSENT"


class TestC0206Adversarial:
    """c0206 adversarial traps: a6_state silent misclassification + Q03/Q04 routing 경계."""

    def _df(self):
        # 서로 다른 시점 → SEPARABLE (df fallback)
        return pd.DataFrame({
            "subject_id": [1, 1],
            "time_value": [0.0, 1.0],
            "event_type": ["dose", "obs"],
        })

    def _df_same_time(self):
        # 동일 (ID,TIME) dose+obs → SAME-TIME-RESOLVABLE (df fallback)
        return pd.DataFrame({
            "subject_id": [1, 1],
            "time_value": [0.0, 0.0],
            "event_type": ["dose", "obs"],
        })

    def test_df_readonly_not_modified(self):
        """kind=detect → df 변경 금지(SRP)."""
        df = self._df()
        original_cols = list(df.columns)
        original_shape = df.shape
        classify_row_ordering(df, {"event_row_state": "separable"})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_meta_a6_state_is_written(self):
        """meta['a6_state'] side-effect 기록 확인."""
        meta = {"event_row_state": "same-time-resolvable"}
        classify_row_ordering(self._df(), meta)
        assert "a6_state" in meta
        assert meta["a6_state"] in [
            "SEPARABLE", "SAME-TIME-RESOLVABLE", "COVARIATE-CHANGE",
            "RESET-NEEDED", "URINE-INTERVAL", "AMBIGUOUS",
        ]

    def test_a0_state_not_written_readonly(self):
        """c0206은 a0_state를 write하지 않는다(read-only; 라우팅 조건으로만 read)."""
        meta_no_a0 = {"event_row_state": "separable"}
        classify_row_ordering(self._df(), meta_no_a0)
        assert "a0_state" not in meta_no_a0
        meta_with_a0 = {"event_row_state": "separable", "a0_state": "AIC-PK"}
        classify_row_ordering(self._df(), meta_with_a0)
        assert meta_with_a0["a0_state"] == "AIC-PK"

    def test_descriptor_whitespace_case_normalized(self):
        """' Same-Time-Resolvable ' (공백·대소문자·구분자) → SAME-TIME-RESOLVABLE."""
        result = classify_row_ordering(self._df(), {"event_row_state": " Same-Time-Resolvable "})
        assert result["a6_state"] == "SAME-TIME-RESOLVABLE"

    def test_ambiguous_routes_q04(self):
        """AMBIGUOUS는 can_route_to_q의 Q04로 라우팅 → route Q04."""
        result = classify_row_ordering(self._df(), {"event_row_state": "ambiguous"})
        assert result["a6_state"] == "AMBIGUOUS"
        assert result["pass"] is False
        assert result["route_to_q"] == "Q04"

    def test_poppk_occasion_missing_routes_q03(self):
        """a0_state=AIC-POPPK + occasion_partition_rule 부재 + non-ambiguous → Q03."""
        result = classify_row_ordering(self._df(), {"event_row_state": "separable", "a0_state": "AIC-POPPK"})
        assert result["a6_state"] == "SEPARABLE"
        assert result["pass"] is False
        assert result["route_to_q"] == "Q03"

    def test_q04_precedence_over_q03(self):
        """AMBIGUOUS(Q04) + popPK+occasion부재(Q03) 동시 → Q04 우선."""
        meta = {"event_row_state": "ambiguous", "a0_state": "AIC-POPPK"}
        result = classify_row_ordering(self._df(), meta)
        assert result["a6_state"] == "AMBIGUOUS"
        assert result["route_to_q"] == "Q04"

    def test_q03_not_fired_when_occasion_rule_present(self):
        """occasion_partition_rule 존재 시 popPK라도 Q03 미발화 → route None."""
        meta = {"event_row_state": "separable", "a0_state": "AIC-POPPK", "occasion_partition_rule": "period"}
        result = classify_row_ordering(self._df(), meta)
        assert result["route_to_q"] is None

    def test_q03_not_fired_when_not_poppk(self):
        """a0_state≠AIC-POPPK이면 occasion 부재라도 Q03 미발화 → route None."""
        meta = {"event_row_state": "separable", "a0_state": "AIC-PK"}
        result = classify_row_ordering(self._df(), meta)
        assert result["route_to_q"] is None

    def test_a0_state_absent_no_q03_fabrication(self):
        """a0_state 부재 경로(chain 전제 미충족)에서 Q03 날조 금지 → route None (GAP-10)."""
        result = classify_row_ordering(self._df(), {"event_row_state": "separable"})
        assert result["route_to_q"] is None

    def test_same_time_not_silent_separable(self):
        """동일 (ID,TIME) dose+obs를 SEPARABLE로 silent 통과 금지 → SAME-TIME-RESOLVABLE."""
        result = classify_row_ordering(self._df_same_time(), {})
        assert result["a6_state"] == "SAME-TIME-RESOLVABLE"

    def test_separable_not_routed(self):
        """SEPARABLE은 Q를 날조하지 않는다 → route_to_q=None."""
        result = classify_row_ordering(self._df(), {"event_row_state": "separable"})
        assert result["a6_state"] == "SEPARABLE"
        assert result["route_to_q"] is None


class TestC0207Adversarial:
    """c0207 adversarial traps: a7_state silent misclassification + Q07/Q13 routing 경계."""

    def _df_clean_cov(self):
        # 깨끗한 기저 공변량 → df fallback BASELINE-CLEAN
        return pd.DataFrame({
            "ID": [1, 2],
            "TIME": [0.0, 0.0],
            "DV": [5.2, 3.0],
            "WT": [70.5, 55.0],
            "AGE": [45, 38],
        })

    def _df_missing_cov(self):
        # 결측 공변량 → df fallback BASELINE-IMPUTABLE
        return pd.DataFrame({
            "ID": [1, 2],
            "TIME": [0.0, 0.0],
            "DV": [5.2, 3.0],
            "WT": [70.5, np.nan],
        })

    def _df_no_cov(self):
        # cov 컬럼 없음 → df fallback NONE-REQUIRED
        return pd.DataFrame({
            "ID": [1, 2],
            "TIME": [0.0, 0.0],
            "DV": [5.2, 3.0],
        })

    def test_df_readonly_not_modified(self):
        """kind=detect → df 변경 금지(SRP)."""
        df = self._df_clean_cov()
        original_cols = list(df.columns)
        original_shape = df.shape
        classify_covariate_layout(df, {"covariate_state": "baseline-clean"})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_meta_a7_state_is_written(self):
        """meta['a7_state'] side-effect 기록 확인."""
        meta = {"covariate_state": "baseline-clean"}
        classify_covariate_layout(self._df_clean_cov(), meta)
        assert "a7_state" in meta
        assert meta["a7_state"] in [
            "NONE-REQUIRED", "BASELINE-CLEAN", "BASELINE-IMPUTABLE", "TIME-VARYING",
            "EXTERNAL-JOIN", "PEDIATRIC-MATURATION", "KEY-MISSING", "POLICY-MISSING",
        ]

    def test_descriptor_whitespace_case_normalized(self):
        """' Policy_Missing ' (공백·대소문자·구분자) → POLICY-MISSING."""
        result = classify_covariate_layout(self._df_no_cov(), {"covariate_state": " Policy_Missing "})
        assert result["a7_state"] == "POLICY-MISSING"
        assert result["route_to_q"] == "Q07"

    def test_policy_missing_routes_q07(self):
        """POLICY-MISSING는 can_route_to_q의 Q07로 라우팅 → route Q07."""
        result = classify_covariate_layout(self._df_no_cov(), {"covariate_state": "policy-missing"})
        assert result["a7_state"] == "POLICY-MISSING"
        assert result["pass"] is False
        assert result["route_to_q"] == "Q07"

    def test_key_missing_routes_q13(self):
        """KEY-MISSING는 can_route_to_q의 Q13으로 라우팅 → route Q13."""
        result = classify_covariate_layout(self._df_no_cov(), {"covariate_state": "key-missing"})
        assert result["a7_state"] == "KEY-MISSING"
        assert result["pass"] is False
        assert result["route_to_q"] == "Q13"

    def test_declared_policy_missing_wins_over_imputable_df(self):
        """df 결측→fallback IMPUTABLE(pass)이지만 선언 policy-missing → POLICY-MISSING+Q07 (silent-pass 금지)."""
        result = classify_covariate_layout(self._df_missing_cov(), {"covariate_state": "policy-missing"})
        assert result["a7_state"] == "POLICY-MISSING"
        assert result["route_to_q"] == "Q07"

    def test_declared_external_join_wins_over_none_required_df(self):
        """df에 cov 없음→fallback NONE-REQUIRED이지만 선언 external-join → EXTERNAL-JOIN (격하 금지)."""
        result = classify_covariate_layout(self._df_no_cov(), {"covariate_state": "external-join"})
        assert result["a7_state"] == "EXTERNAL-JOIN"

    def test_clean_cov_not_routed(self):
        """BASELINE-CLEAN은 Q를 날조하지 않는다 → route_to_q=None."""
        result = classify_covariate_layout(self._df_clean_cov(), {"covariate_state": "baseline-clean"})
        assert result["a7_state"] == "BASELINE-CLEAN"
        assert result["route_to_q"] is None

    def test_no_q_fabrication_from_df_alone(self):
        """선언 부재 시 df만으로 Q07/Q13 날조 금지 → fallback pass-state, route None."""
        for df in (self._df_no_cov(), self._df_clean_cov(), self._df_missing_cov()):
            result = classify_covariate_layout(df, {})
            assert result["route_to_q"] is None
            assert result["pass"] is True

    def test_fallback_limit_time_varying_to_baseline(self):
        """★ 문서화된 한계(GAP-11): 선언 부재 시 시변 공변량 df도 fallback은 BASELINE-* 로만 떨어진다.

        df fallback은 8개 중 3개(NONE-REQUIRED/BASELINE-CLEAN/BASELINE-IMPUTABLE)만 도달한다.
        TIME-VARYING은 covariate_state 선언이 있어야 도달(c0202 GAP-9 fallback 한계 동형).
        """
        # WT가 시점별로 변하지만 선언 없으면 TIME-VARYING이 아니라 BASELINE-CLEAN으로 분류
        df_tv = pd.DataFrame({
            "ID": [1, 1, 1],
            "TIME": [0.0, 24.0, 48.0],
            "DV": [5.2, 4.1, 3.5],
            "WT": [70.0, 69.0, 68.0],
        })
        result = classify_covariate_layout(df_tv, {})
        assert result["a7_state"] == "BASELINE-CLEAN"  # NOT TIME-VARYING (선언 의존)
        # 선언이 있으면 TIME-VARYING으로 올바르게 분류
        result_declared = classify_covariate_layout(df_tv, {"covariate_state": "time-varying"})
        assert result_declared["a7_state"] == "TIME-VARYING"

    def test_a7_state_not_pre_read(self):
        """c0207은 a7_state를 write한다(자기 축 emitter). 기존 a7_state 값에 의존하지 않고 재계산."""
        meta = {"covariate_state": "key-missing", "a7_state": "BASELINE-CLEAN"}
        result = classify_covariate_layout(self._df_no_cov(), meta)
        assert result["a7_state"] == "KEY-MISSING"
        assert meta["a7_state"] == "KEY-MISSING"


class TestC0209Adversarial:
    """c0209 adversarial traps: a9_state silent misclassification + Q06/Q15D routing 경계."""

    def _df_clean(self):
        return pd.DataFrame({
            "subject_id": [1, 1, 2],
            "time_value": [0.5, 1.0, 0.5],
            "dv_value": [5.2, 4.8, 6.0],
        })

    def _df_full_dup(self):
        # 완전중복 행(전체 일치) → DUPLICATE-EXACT
        return pd.DataFrame({
            "subject_id": [1, 1, 1],
            "time_value": [0.5, 0.5, 1.0],
            "dv_value": [5.2, 5.2, 4.8],
        })

    def _df_replicate(self):
        # 동일 (ID,TIME) 다른 DV → 정당 replicate(A5 소관), DUPLICATE-EXACT 아님
        return pd.DataFrame({
            "subject_id": [1, 1, 1],
            "time_value": [0.5, 0.5, 1.0],
            "dv_value": [5.2, 5.9, 4.8],
        })

    def _df_unsorted(self):
        # id별 time 역순 → UNSORTED
        return pd.DataFrame({
            "subject_id": [1, 1, 1],
            "time_value": [2.0, 1.0, 0.5],
            "dv_value": [3.1, 4.8, 5.2],
        })

    def test_df_readonly_not_modified(self):
        """kind=verify → df 변경 금지(SRP)."""
        df = self._df_full_dup()
        original_cols = list(df.columns)
        original_shape = df.shape
        verify_cross_column_invariant(df, {})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_meta_a9_state_is_written(self):
        """meta['a9_state'] side-effect 기록 확인."""
        meta = {"defect_state": "unit-conversion"}
        verify_cross_column_invariant(self._df_clean(), meta)
        assert "a9_state" in meta
        assert meta["a9_state"] in [
            "CLEAN", "DUPLICATE-EXACT", "UNSORTED", "COLUMN-SYNONYM", "UNIT-CONVERSION",
            "ENCODING-FIX", "PRE-DOSE-SAMPLE", "PLANNED-VS-ACTUAL", "PROTOCOL-DEVIATION",
            "REANALYSIS-FINAL-DEFINED", "REANALYSIS-FINAL-MISSING",
            "PROTOCOL-DEVIATION-NO-POLICY", "IRRECONCILABLE",
        ]

    def test_descriptor_whitespace_case_normalized(self):
        """' Protocol-Deviation-No-Policy ' (공백·대소문자·구분자) → PROTOCOL-DEVIATION-NO-POLICY, Q06."""
        result = verify_cross_column_invariant(self._df_clean(), {"defect_state": " Protocol-Deviation-No-Policy "})
        assert result["a9_state"] == "PROTOCOL-DEVIATION-NO-POLICY"
        assert result["route_to_q"] == "Q06"

    def test_protocol_deviation_no_policy_routes_q06(self):
        """PROTOCOL-DEVIATION-NO-POLICY는 can_route_to_q의 Q06으로 라우팅 → route Q06."""
        result = verify_cross_column_invariant(self._df_clean(), {"defect_state": "protocol-deviation-no-policy"})
        assert result["a9_state"] == "PROTOCOL-DEVIATION-NO-POLICY"
        assert result["pass"] is False
        assert result["route_to_q"] == "Q06"

    def test_reanalysis_final_missing_routes_q15d(self):
        """REANALYSIS-FINAL-MISSING은 Q06이 아니라 Q15D로 라우팅."""
        result = verify_cross_column_invariant(self._df_clean(), {"defect_state": "reanalysis-final-missing"})
        assert result["a9_state"] == "REANALYSIS-FINAL-MISSING"
        assert result["route_to_q"] == "Q15D"

    def test_irreconcilable_does_not_invent_invalid(self):
        """IRRECONCILABLE은 can_route_to_q 밖 INVALID/Q를 날조하지 않는다 → route_to_q=None (GAP-12)."""
        result = verify_cross_column_invariant(self._df_clean(), {"defect_state": "irreconcilable"})
        assert result["a9_state"] == "IRRECONCILABLE"
        assert result["route_to_q"] is None

    def test_full_dup_is_duplicate_exact(self):
        """완전중복 행은 DUPLICATE-EXACT (df fallback)."""
        result = verify_cross_column_invariant(self._df_full_dup(), {})
        assert result["a9_state"] == "DUPLICATE-EXACT"

    def test_replicate_not_silent_duplicate_loss(self):
        """P3: 동일 (ID,TIME) 다른 DV(정당 replicate)를 DUPLICATE-EXACT로 silent 제거 금지 → CLEAN."""
        result = verify_cross_column_invariant(self._df_replicate(), {})
        assert result["a9_state"] == "CLEAN"
        assert result["route_to_q"] is None

    def test_unsorted_not_silent_clean(self):
        """id별 time 역순을 CLEAN으로 silent 통과 금지 → UNSORTED."""
        result = verify_cross_column_invariant(self._df_unsorted(), {})
        assert result["a9_state"] == "UNSORTED"

    def test_no_q_fabrication_from_df_alone(self):
        """선언 부재 시 df만으로 Q06/Q15D 날조 금지 → fallback pass-state, route None."""
        for df in (self._df_clean(), self._df_full_dup(), self._df_unsorted(), self._df_replicate()):
            result = verify_cross_column_invariant(df, {})
            assert result["route_to_q"] is None
            assert result["pass"] is True

    def test_declared_no_policy_wins_over_clean_df(self):
        """df가 깨끗해도 선언 protocol-deviation-no-policy면 CLEAN으로 silent 격하 금지 → Q06."""
        result = verify_cross_column_invariant(self._df_clean(), {"defect_state": "protocol-deviation-no-policy"})
        assert result["a9_state"] == "PROTOCOL-DEVIATION-NO-POLICY"
        assert result["route_to_q"] == "Q06"

    def test_declared_deviation_with_policy_not_routed(self):
        """PROTOCOL-DEVIATION(처리 정책 有)이 -NO-POLICY로 silent 격하되면 안 됨 → route None."""
        result = verify_cross_column_invariant(self._df_clean(), {"defect_state": "protocol-deviation"})
        assert result["a9_state"] == "PROTOCOL-DEVIATION"
        assert result["route_to_q"] is None


class TestC0210Adversarial:
    """c0210 adversarial traps: a10_state silent misclassification.

    can_route_to_q=[] → 순수 분류기(c0202 동형). Q 라우팅 trap 없음(route_to_q 항상 None).
    NON-TABULAR→UNSUPPORTED / CORRUPTED→INVALID은 scope-밖 terminal(하류 ROUTE c) — GAP-13.
    """

    def _df(self):
        return pd.DataFrame({
            "subject_id": [1, 1, 2],
            "time_value": [0.0, 1.0, 0.0],
            "dv_value": [5.2, 3.1, 4.8],
        })

    def test_df_readonly_not_modified(self):
        """kind=detect → df 변경 금지(SRP)."""
        df = self._df()
        original_cols = list(df.columns)
        original_shape = df.shape
        detect_source_format(df, {"file_format": "cro-vendor"})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_meta_a10_state_is_written(self):
        """meta['a10_state'] side-effect 기록 확인 + 8-state 범위."""
        meta = {"file_format": "sdtm-adam"}
        detect_source_format(self._df(), meta)
        assert "a10_state" in meta
        assert meta["a10_state"] in [
            "SDTM-ADaM", "EDC-STRUCTURED", "CRO-VENDOR", "FLAT-TABULAR",
            "LEGACY-NM", "SEMI-STRUCTURED", "NON-TABULAR", "CORRUPTED",
        ]

    def test_descriptor_whitespace_case_normalized(self):
        """' Cro-Vendor ' (공백·대소문자) → CRO-VENDOR."""
        result = detect_source_format(self._df(), {"file_format": " Cro-Vendor "})
        assert result["a10_state"] == "CRO-VENDOR"
        assert result["route_to_q"] is None

    def test_pure_classifier_never_routes_q(self):
        """can_route_to_q=[] → 어떤 state도 Q를 날조하지 않는다(route_to_q None, pass True).

        NON-TABULAR/CORRUPTED는 →UNSUPPORTED/INVALID terminal이지만 Q-code가 아니므로
        route_to_q=None·pass=True (scope-out; 하류 ROUTE c — GAP-13)."""
        for desc in ["sdtm-adam", "edc-structured", "cro-vendor", "flat-tabular",
                     "legacy-nm", "semi-structured", "non-tabular", "corrupted"]:
            result = detect_source_format(self._df(), {"file_format": desc})
            assert result["route_to_q"] is None
            assert result["pass"] is True

    def test_unknown_descriptor_deterministic_fallback(self):
        """미지의 선언이 out-of-vocab state를 만들거나 crash하면 안 됨 → 유효 8-state로 fallback."""
        result = detect_source_format(self._df(), {"file_format": "totally-unknown-xyz"})
        assert result["a10_state"] in [
            "SDTM-ADaM", "EDC-STRUCTURED", "CRO-VENDOR", "FLAT-TABULAR",
            "LEGACY-NM", "SEMI-STRUCTURED", "NON-TABULAR", "CORRUPTED",
        ]
        assert result["a10_state"] == "FLAT-TABULAR"  # 파싱된 df → 기본값
        assert result["route_to_q"] is None

    def test_fallback_limit_corrupted_unreachable_via_df(self):
        """★ 문서화된 한계(GAP-13): 선언 부재 시 파싱된 df는 CORRUPTED/NON-TABULAR에 도달할 수 없다
        (그런 파일은 애초에 df를 못 만든다 = 위치 불일치). df fallback은 8개 중 FLAT-TABULAR 1개만
        도달함을 고정. 버그가 아니라 실패 state가 선언 의존임을 못박는다."""
        result = detect_source_format(self._df(), {})
        assert result["a10_state"] == "FLAT-TABULAR"
        assert result["a10_state"] not in ("CORRUPTED", "NON-TABULAR")
        assert result["route_to_q"] is None

    def test_declaration_wins_over_df(self):
        """선언 SDTM-ADaM이 평범한 df 때문에 FLAT-TABULAR로 silent 격하되면 안 됨 → SDTM-ADaM."""
        result = detect_source_format(self._df(), {"file_format": "sdtm-adam"})
        assert result["a10_state"] == "SDTM-ADaM"
        assert result["route_to_q"] is None


class TestC0019Adversarial:
    """c0019 adversarial traps: TIME 표준화 silent-error.

    설계(사용자 확정): spec snippet 1:1(to_numeric(time_value)). a3_state는 라우팅만
    (AMBIGUOUS→Q02, UNRECOVERABLE→Q12). 6개 유도가능 state는 동일 derivation —
    spec에 없는 per-state 산문 derivation(nominal_time/offset/midpoint) 금지.
    입력계약: time_value 생산자=상류 mess c 미구현 — provenance_gaps GAP-18(↔GAP-7).
    """

    _DERIVABLE = ["ACTUAL", "ACTUAL-PREFERRED", "NOMINAL-ONLY",
                  "NOMINAL-PREFERRED", "ELAPSED", "INTERVAL"]

    def test_time_equals_numeric_time_value(self):
        """ACTUAL: TIME은 time_value의 numeric 변환과 같아야 한다."""
        df = pd.DataFrame({"time_value": [0.0, 1.5, 3.0]})
        result = assign_time(df, {"a3_state": "ACTUAL"})
        assert result["success"] is True
        assert list(result["df"]["TIME"]) == [0.0, 1.5, 3.0]

    def test_all_six_states_identical_derivation(self):
        """6개 유도가능 state는 동일 derivation(=numeric(time_value)) — a3_state로 값이 갈리지 않는다."""
        tv = [0.0, 2.0, 5.0]
        outs = []
        for st in self._DERIVABLE:
            result = assign_time(pd.DataFrame({"time_value": tv}), {"a3_state": st})
            assert result["success"] is True
            outs.append(list(result["df"]["TIME"]))
        assert all(o == [0.0, 2.0, 5.0] for o in outs)

    def test_nominal_does_not_use_nominal_time_column(self):
        """NOMINAL state라도 spec에 없는 nominal_time derivation을 쓰지 않는다 — TIME은 time_value 기반."""
        df = pd.DataFrame({"time_value": [10.0, 11.0, 13.0], "nominal_time": [0.0, 1.0, 3.0]})
        result = assign_time(df, {"a3_state": "NOMINAL-ONLY"})
        assert result["success"] is True
        assert list(result["df"]["TIME"]) == [10.0, 11.0, 13.0]  # nominal_time [0,1,3] 무시

    def test_ambiguous_routes_q02(self):
        """AMBIGUOUS → fail, Q02 (derivation 안 함)."""
        df = pd.DataFrame({"time_value": [0.0, 1.0]})
        result = assign_time(df, {"a3_state": "AMBIGUOUS"})
        assert result["success"] is False
        assert result["route_to_q"] == "Q02"

    def test_unrecoverable_routes_q12(self):
        """UNRECOVERABLE → fail, Q12."""
        df = pd.DataFrame({"time_value": [0.0, 1.0]})
        result = assign_time(df, {"a3_state": "UNRECOVERABLE"})
        assert result["success"] is False
        assert result["route_to_q"] == "Q12"

    def test_nan_time_not_silent(self):
        """time_value 결측 → TIME NaN을 silent 통과시키지 않고 fail."""
        df = pd.DataFrame({"time_value": [None, 3.0]})
        result = assign_time(df, {"a3_state": "ACTUAL"})
        assert result["success"] is False

    def test_text_token_not_silent(self):
        """파싱 불가 문자 토큰 → fail(silent NaN 금지)."""
        df = pd.DataFrame({"time_value": ["noon", "1.5"]})
        result = assign_time(df, {"a3_state": "ACTUAL"})
        assert result["success"] is False

    def test_negative_time_not_silent(self):
        """음수 시간은 numeric·notna여서 postcond는 통과하나 도메인 위반 → fail."""
        df = pd.DataFrame({"time_value": [-1.0, 2.0]})
        result = assign_time(df, {"a3_state": "ACTUAL"})
        assert result["success"] is False

    def test_missing_time_value_column_fails(self):
        """time_value 컬럼 부재(상류 mess c 미산출, GAP-18) → silent 통과 금지, fail."""
        df = pd.DataFrame({"foo": [1, 2]})
        result = assign_time(df, {"a3_state": "ACTUAL"})
        assert result["success"] is False

    def test_missing_a3_state_fails(self):
        """meta에 a3_state 부재(c0203 미선행) → fail."""
        df = pd.DataFrame({"time_value": [0.0, 1.0]})
        result = assign_time(df, {})
        assert result["success"] is False

    def test_input_df_not_mutated(self):
        """transform은 df.copy()를 사용해야 한다 — 원본 df에 TIME 추가 금지."""
        df = pd.DataFrame({"time_value": [0.0, 1.0]})
        original_cols = list(df.columns)
        assign_time(df, {"a3_state": "ACTUAL"})
        assert list(df.columns) == original_cols
        assert "TIME" not in df.columns


class TestC0020Adversarial:
    """c0020 adversarial traps: BLQ_FLAG 부여 silent-error.

    설계(plan): blq_policy 분기(M3/M4 컬럼 생성 vs M1/M5 미생성). BLQ_FLAG는 bool이 아닌
    int(.astype(int)). 핵심 silent-error: BLQ_FLAG=1이 dose행(EVID≠0)에 붙으면 fail+Q01.
    입력계약: blq_detected(←c0306 미구현)/blq_policy(←외부) — provenance_gaps GAP-15(DECISION-D3).
    """

    def test_blq_flag_is_int_not_bool(self):
        """M3: BLQ_FLAG는 bool이 아닌 int여야 한다(spec .astype(int))."""
        df = pd.DataFrame({"EVID": [0, 0], "blq_detected": [True, False]})
        result = assign_blq_flag(df, {"a5_state": "BLQ-FLAGGED", "blq_policy": "M3"})
        assert result["success"] is True
        assert pd.api.types.is_integer_dtype(result["df"]["BLQ_FLAG"])
        assert not pd.api.types.is_bool_dtype(result["df"]["BLQ_FLAG"])

    def test_blq_on_dose_not_silent(self):
        """BLQ_FLAG=1이 dose행(EVID=1)에 붙는 경우 silent 통과 금지 → fail Q01."""
        df = pd.DataFrame({"EVID": [0, 1], "blq_detected": [False, True]})
        result = assign_blq_flag(df, {"a5_state": "BLQ-FLAGGED", "blq_policy": "M3"})
        assert result["success"] is False
        assert result["route_to_q"] == "Q01"

    def test_m3_m4_identical(self):
        """M3와 M4는 동일 derivation(둘 다 likelihood) — BLQ_FLAG 동일."""
        df = pd.DataFrame({"EVID": [0, 0, 0], "blq_detected": [False, True, False]})
        r3 = assign_blq_flag(df, {"a5_state": "BLQ-FLAGGED", "blq_policy": "M3"})
        r4 = assign_blq_flag(df, {"a5_state": "BLQ-FLAGGED", "blq_policy": "M4"})
        assert r3["success"] is True and r4["success"] is True
        assert list(r3["df"]["BLQ_FLAG"]) == list(r4["df"]["BLQ_FLAG"]) == [0, 1, 0]

    def test_m1_m5_no_column(self):
        """M1(제외)/M5(대체)는 BLQ_FLAG 컬럼 미생성, success."""
        df = pd.DataFrame({"EVID": [0, 0], "blq_detected": [False, True]})
        for policy in ("M1", "M5"):
            result = assign_blq_flag(df, {"a5_state": "BLQ-FLAGGED", "blq_policy": policy})
            assert result["success"] is True
            assert "BLQ_FLAG" not in result["df"].columns

    def test_non_blq_all_zero(self):
        """M3, 전부 non-BLQ → BLQ_FLAG 전부 0, success."""
        df = pd.DataFrame({"EVID": [0, 0, 0], "blq_detected": [False, False, False]})
        result = assign_blq_flag(df, {"a5_state": "BLQ-FLAGGED", "blq_policy": "M3"})
        assert result["success"] is True
        assert list(result["df"]["BLQ_FLAG"]) == [0, 0, 0]

    def test_missing_a5_state_fails(self):
        """meta에 a5_state 부재(c0205 미선행) → fail Q01."""
        df = pd.DataFrame({"EVID": [0, 0], "blq_detected": [False, True]})
        result = assign_blq_flag(df, {"blq_policy": "M3"})
        assert result["success"] is False
        assert result["route_to_q"] == "Q01"

    def test_input_df_not_mutated(self):
        """transform은 df.copy()를 사용 — 원본 df에 BLQ_FLAG 추가 금지."""
        df = pd.DataFrame({"EVID": [0, 0], "blq_detected": [False, True]})
        original_cols = list(df.columns)
        assign_blq_flag(df, {"a5_state": "BLQ-FLAGGED", "blq_policy": "M3"})
        assert list(df.columns) == original_cols
        assert "BLQ_FLAG" not in df.columns


class TestC0021Adversarial:
    """c0021 adversarial traps: LLOQ 부여 silent-error.

    설계(plan): 분기 변수='BLQ_FLAG' in df.columns. BLQ_FLAG 존재 시 to_numeric(coerce)로 LLOQ
    생성 후 Guard1(NaN: 비수치/결측을 >0 비교 *전에* 차단) → Guard2(≤0)로 검사. dose행(EVID≠0,
    non-BLQ)은 미제약. 입력계약: lloq_value(←c0306 미구현)/BLQ_FLAG(←c0020 형제) —
    provenance_gaps GAP-15(DECISION-D3).
    """

    def test_no_blq_flag_no_lloq(self):
        """BLQ_FLAG 부재 → LLOQ 미생성, success (M1/M5 하류)."""
        df = pd.DataFrame({"EVID": [0, 0], "lloq_value": [0.1, 0.1]})
        result = assign_lloq(df, {"a5_state": "BLQ-FLAGGED"})
        assert result["success"] is True
        assert "LLOQ" not in result["df"].columns

    def test_obs_lloq_must_be_positive(self):
        """obs LLOQ=0은 ≤0이므로 Guard2 → fail Q01."""
        df = pd.DataFrame({"EVID": [0, 0], "BLQ_FLAG": [0, 1], "lloq_value": [0.0, 0.1]})
        result = assign_lloq(df, {"a5_state": "BLQ-FLAGGED"})
        assert result["success"] is False
        assert result["route_to_q"] == "Q01"

    def test_negative_lloq_not_silent(self):
        """음수 LLOQ → Guard2, silent 통과 금지 → fail Q01."""
        df = pd.DataFrame({"EVID": [0, 0], "BLQ_FLAG": [0, 1], "lloq_value": [-0.1, 0.1]})
        result = assign_lloq(df, {"a5_state": "BLQ-FLAGGED"})
        assert result["success"] is False
        assert result["route_to_q"] == "Q01"

    def test_nonnumeric_lloq_caught_before_compare(self):
        """비수치 obs LLOQ는 to_numeric→NaN→Guard1로 *>0 비교 전에* 잡힌다(crash·silent 모두 금지)."""
        df = pd.DataFrame({"EVID": [0, 0], "BLQ_FLAG": [0, 1], "lloq_value": ["abc", "0.1"]})
        result = assign_lloq(df, {"a5_state": "BLQ-FLAGGED"})  # 예외 없이 반환되어야 함
        assert result["success"] is False
        assert result["route_to_q"] == "Q01"
        assert pd.isna(result["df"]["LLOQ"].iloc[0])  # coerce로 NaN이 된 뒤 Guard1에서 차단(≤0 경로 아님)

    def test_blq_row_lloq_must_be_positive(self):
        """BLQ행(BLQ_FLAG=1)의 LLOQ도 >0 필수 — obs는 정상이나 BLQ행이 0이면 BLQ절로 fail Q01."""
        df = pd.DataFrame({"EVID": [0, 1], "BLQ_FLAG": [0, 1], "lloq_value": [0.1, 0.0]})
        result = assign_lloq(df, {"a5_state": "BLQ-FLAGGED"})
        assert result["success"] is False
        assert result["route_to_q"] == "Q01"

    def test_dose_row_lloq_unconstrained(self):
        """dose행(EVID≠0, non-BLQ)의 LLOQ는 NaN이어도 무방 — obs/BLQ만 유효하면 success(postcond scope)."""
        df = pd.DataFrame({"EVID": [0, 1], "BLQ_FLAG": [1, 0], "lloq_value": [0.1, None]})
        result = assign_lloq(df, {"a5_state": "BLQ-FLAGGED"})
        assert result["success"] is True
        assert result["df"]["LLOQ"].iloc[0] == 0.1
        assert pd.isna(result["df"]["LLOQ"].iloc[1])  # dose행은 NaN 허용

    def test_input_df_not_mutated(self):
        """transform은 df.copy()를 사용 — 원본 df에 LLOQ 추가 금지."""
        df = pd.DataFrame({"EVID": [0, 0], "BLQ_FLAG": [0, 1], "lloq_value": [0.1, 0.1]})
        original_cols = list(df.columns)
        assign_lloq(df, {"a5_state": "BLQ-FLAGGED"})
        assert list(df.columns) == original_cols
        assert "LLOQ" not in df.columns


class TestC0022Adversarial:
    """c0022 adversarial traps: 기저 공변량 코딩 silent-error (★ IMPUTE 금지 핵심).

    설계(사용자 ★★★ 확정): spec snippet fillna(median())은 미준수 — vocab §A IMPUTE 제외 전역 규칙.
    결측 공변량은 median 대입 없이 NaN 보존(FLAG) + Q07. 범주형 SEX→int(M/F 매핑), 연속형→
    to_numeric. axis gate: KEY-MISSING→Q13, POLICY-MISSING→Q07. 핵심 trap: 결측을 median/mean으로
    fabricate하지 않는지(임의 imputation 발생 시 fail). 입력계약: baseline_covariates 리스트 생산자
    부재 — provenance_gaps GAP-3, snippet↔vocab 불일치 GAP-19.
    """

    def test_clean_covariates_coded(self):
        """결측 없는 WT(실수)+SEX(M/F→0/1) → 코딩, success."""
        df = pd.DataFrame({"WT": [70.5, 55.0], "SEX": ["M", "F"]})
        meta = {"a7_state": "BASELINE-CLEAN", "baseline_covariates": ["WT", "SEX"]}
        result = assign_baseline_covariate(df, meta)
        assert result["success"] is True
        assert list(result["df"]["WT"]) == [70.5, 55.0]
        assert list(result["df"]["SEX"]) == [0, 1]

    def test_sex_is_int_not_object(self):
        """SEX 코딩 결과는 object/bool이 아닌 int dtype."""
        df = pd.DataFrame({"SEX": ["M", "F", "M"]})
        meta = {"a7_state": "BASELINE-CLEAN", "baseline_covariates": ["SEX"]}
        result = assign_baseline_covariate(df, meta)
        assert result["success"] is True
        assert pd.api.types.is_integer_dtype(result["df"]["SEX"])
        assert list(result["df"]["SEX"]) == [0, 1, 0]

    def test_missing_wt_not_median_filled(self):
        """★ 결측 WT를 median으로 silent 채우지 않는다 — NaN 보존 + Q07 (IMPUTE 금지 핵심 trap).

        WT=[70,80,NaN]; median=75.0(관측에 없는 값). 잘못된 fillna(median)이면 NaN이 75.0이 된다.
        """
        df = pd.DataFrame({"WT": [70.0, 80.0, np.nan]})
        meta = {"a7_state": "BASELINE-IMPUTABLE", "baseline_covariates": ["WT"]}
        result = assign_baseline_covariate(df, meta)
        assert result["success"] is False
        assert result["route_to_q"] == "Q07"
        assert pd.isna(result["df"]["WT"].iloc[2])           # median(75.0)으로 fabricate 안 됨
        assert list(result["df"]["WT"].iloc[:2]) == [70.0, 80.0]  # 관측값은 보존(변형 금지)

    def test_unmapped_sex_not_fabricated(self):
        """매핑 불가 SEX('U') → NaN(임의 정수 코딩 금지) → fail Q07."""
        df = pd.DataFrame({"SEX": ["M", "U"]})
        meta = {"a7_state": "BASELINE-CLEAN", "baseline_covariates": ["SEX"]}
        result = assign_baseline_covariate(df, meta)
        assert result["success"] is False
        assert result["route_to_q"] == "Q07"
        assert pd.isna(result["df"]["SEX"].iloc[1])  # 'U'를 임의 정수로 코딩하지 않음

    def test_policy_missing_routes_q07(self):
        """a7_state=POLICY-MISSING → fail Q07 (axis gate)."""
        df = pd.DataFrame({"WT": [70.5, 55.0]})
        result = assign_baseline_covariate(df, {"a7_state": "POLICY-MISSING", "baseline_covariates": ["WT"]})
        assert result["success"] is False
        assert result["route_to_q"] == "Q07"

    def test_key_missing_routes_q13(self):
        """a7_state=KEY-MISSING → fail Q13 (axis gate; external linkage key)."""
        df = pd.DataFrame({"WT": [70.5, 55.0]})
        result = assign_baseline_covariate(df, {"a7_state": "KEY-MISSING", "baseline_covariates": ["WT"]})
        assert result["success"] is False
        assert result["route_to_q"] == "Q13"

    def test_gap3_fallback_codes_detected_covariates(self):
        """GAP-3 방어: baseline_covariates 미선언이라도 df covariate 컬럼을 탐지·코딩(silent no-op 금지)."""
        df = pd.DataFrame({"WT": [70.5, 55.0], "SEX": ["M", "F"]})
        result = assign_baseline_covariate(df, {"a7_state": "BASELINE-CLEAN"})  # 리스트 미주입
        assert result["success"] is True
        assert pd.api.types.is_integer_dtype(result["df"]["SEX"])  # 탐지되어 코딩됨(빈 순회 아님)
        assert list(result["df"]["SEX"]) == [0, 1]

    def test_input_df_not_mutated(self):
        """transform은 df.copy()를 사용 — 원본 df의 SEX를 0/1로 변형 금지."""
        df = pd.DataFrame({"WT": [70.5, 55.0], "SEX": ["M", "F"]})
        original_sex = list(df["SEX"])
        assign_baseline_covariate(df, {"a7_state": "BASELINE-CLEAN", "baseline_covariates": ["WT", "SEX"]})
        assert list(df["SEX"]) == original_sex  # 원본 SEX 여전히 'M'/'F'


class TestC0023Adversarial:
    """c0023 adversarial traps: 시변 공변량 LOCF silent-error.

    설계(plan): LOCF(groupby('ID').ffill()) = vocab §A V10 PROPAGATE(정당; 자의적 IMPUTE 아님).
    핵심 silent-error: (1) cross-ID bleed 금지 — groupby 없는 ffill은 타 subject 값으로 오염,
    (2) leading 결측은 직전 관측 부재이므로 bfill/mean 날조 없이 Q07. structural gate: 'ID' 부재→Q07.
    입력계약: tv_covariates 리스트 생산자 부재 — provenance_gaps GAP-3; groupby 키 GAP-17.
    """

    def test_locf_within_id_no_cross_subject_bleed(self):
        """★ ffill은 ID 내에서만 — subject2 leading 결측이 subject1 값으로 오염되면 안 된다.

        ID=[1,1,2,2], WT=[70,NaN,NaN,55]. groupby('ID').ffill(): ID1→[70,70], ID2→[NaN,55].
        ID2 첫 행은 직전 관측 없어 NaN 유지(70으로 채우면 cross-ID 오염). residual NaN → Q07.
        """
        df = pd.DataFrame({"ID": [1, 1, 2, 2], "WT": [70.0, np.nan, np.nan, 55.0]})
        meta = {"a7_state": "TIME-VARYING", "tv_covariates": ["WT"]}
        result = assign_time_varying_covariate(df, meta)
        assert result["success"] is False
        assert result["route_to_q"] == "Q07"
        assert pd.isna(result["df"]["WT"].iloc[2])   # ID2 첫 행: ID1의 70으로 오염 안 됨
        assert result["df"]["WT"].iloc[1] == 70.0    # ID1은 정상 carry-forward

    def test_ffill_carries_observed_not_fabricated(self):
        """중간 결측은 직전 *관측값*으로 채워진다(평균 날조 아님): [70,NaN,65]→[70,70,65]."""
        df = pd.DataFrame({"ID": [1, 1, 1], "WT": [70.0, np.nan, 65.0]})
        meta = {"a7_state": "TIME-VARYING", "tv_covariates": ["WT"]}
        result = assign_time_varying_covariate(df, meta)
        assert result["success"] is True
        assert list(result["df"]["WT"]) == [70.0, 70.0, 65.0]
        assert result["df"]["WT"].iloc[1] != 67.5   # mean(70,65)=67.5로 날조 안 됨

    def test_no_mean_or_median_fill(self):
        """trailing 결측은 마지막 관측(LOCF)으로 채워진다 — 통계 아님: [70,80,NaN]→[70,80,80]."""
        df = pd.DataFrame({"ID": [1, 1, 1], "WT": [70.0, 80.0, np.nan]})
        meta = {"a7_state": "TIME-VARYING", "tv_covariates": ["WT"]}
        result = assign_time_varying_covariate(df, meta)
        assert result["success"] is True
        assert result["df"]["WT"].iloc[2] == 80.0   # 마지막 관측 carry-forward
        assert result["df"]["WT"].iloc[2] != 75.0   # mean/median(70,80)=75로 날조 안 됨

    def test_leading_missing_routes_q07(self):
        """leading 결측(직전 관측 부재) → ffill 미충족 → Q07 (bfill 금지)."""
        df = pd.DataFrame({"ID": [1, 1], "WT": [np.nan, 65.0]})
        meta = {"a7_state": "TIME-VARYING", "tv_covariates": ["WT"]}
        result = assign_time_varying_covariate(df, meta)
        assert result["success"] is False
        assert result["route_to_q"] == "Q07"
        assert pd.isna(result["df"]["WT"].iloc[0])   # 직전 관측 없어 NaN 유지

    def test_policy_missing_routes_q07(self):
        """a7_state=POLICY-MISSING → fail Q07 (axis gate)."""
        df = pd.DataFrame({"ID": [1, 1], "WT": [70.0, 72.0]})
        result = assign_time_varying_covariate(df, {"a7_state": "POLICY-MISSING", "tv_covariates": ["WT"]})
        assert result["success"] is False
        assert result["route_to_q"] == "Q07"

    def test_missing_id_column_routes_q07(self):
        """'ID' 컬럼 부재(groupby 키 없음) → fail Q07 (structural gate, c0021 EVID 동형)."""
        df = pd.DataFrame({"TIME": [0, 24], "WT": [70.0, np.nan]})
        result = assign_time_varying_covariate(df, {"a7_state": "TIME-VARYING", "tv_covariates": ["WT"]})
        assert result["success"] is False
        assert result["route_to_q"] == "Q07"

    def test_input_df_not_mutated(self):
        """transform은 df.copy()를 사용 — 원본 df는 ffill되지 않는다."""
        df = pd.DataFrame({"ID": [1, 1], "WT": [70.0, np.nan]})
        assign_time_varying_covariate(df, {"a7_state": "TIME-VARYING", "tv_covariates": ["WT"]})
        assert pd.isna(df["WT"].iloc[1])   # 원본 결측 그대로(copy 사용)


class TestC0140Adversarial:
    """c0140 adversarial traps: 기저 공변량 부착(L-2→L-3) silent-error (★ GAP-17/19 핵심).

    설계(사용자 ★★★ 확정): baseline(time==0) 값을 subject별 전 행에 within-subject PROPAGATE(§A V10,
    c0023 동류). 결측 baseline은 median 대입 없이 NaN 보존 + Q07(GAP-19). GAP-17: TIME 부재→time_value
    fallback, groupby 키 subject_id→ID. 사용자 지정 3 trap 필수: ① no-baseline→median 날조 없이 Q07,
    ② 부분결측 subject→자기 baseline PROPAGATE로 success(IMPUTE 아님 양성), ③ cross-subject bleed 금지.
    추가: baseline-row 식별(time==0)을 postcond와 독립 검증(spurious pass 방지). 입력계약: GAP-3.
    """

    def test_no_baseline_subject_not_median_filled(self):
        """① ★GAP-19 핵심: baseline 전무 subject(3)를 median(타subj)으로 채우지 않는다 — NaN 보존 + Q07.

        WT=[70,80,NaN]; median([70,80])=75.0(관측에 없는 값). 잘못된 median-fill이면 subj3가 75.0이 된다.
        """
        df = pd.DataFrame({"subject_id": [1, 2, 3], "time_value": [0, 0, 0], "WT": [70.0, 80.0, np.nan]})
        meta = {"a7_state": "BASELINE-IMPUTABLE", "baseline_covariates": ["WT"]}
        result = assign_baseline_covariate_l3(df, meta)
        assert result["success"] is False
        assert result["route_to_q"] == "Q07"
        assert pd.isna(result["df"]["WT"].iloc[2])              # subj3: median(75.0) fabricate 안 됨
        assert list(result["df"]["WT"].iloc[:2]) == [70.0, 80.0]  # 관측 baseline 보존

    def test_partial_missing_within_subject_propagated(self):
        """② ★신규 양성: baseline 보유 subject의 비-baseline 결측 행이 자기 baseline 값으로 PROPAGATE.

        subj1 baseline 70, subj2 baseline 50; 각 비-baseline 결측은 자기 baseline으로 채워져 success.
        통계 fill(예: 전체 mean 60)이 아니라 within-subject PROPAGATE임을 양성 검증(IMPUTE 아님).
        """
        df = pd.DataFrame({
            "subject_id": [1, 1, 2, 2],
            "time_value": [0, 24, 0, 24],
            "WT": [70.0, np.nan, 50.0, np.nan],
        })
        meta = {"a7_state": "BASELINE-IMPUTABLE", "baseline_covariates": ["WT"]}
        result = assign_baseline_covariate_l3(df, meta)
        assert result["success"] is True
        assert list(result["df"]["WT"]) == [70.0, 70.0, 50.0, 50.0]
        assert result["df"]["WT"].iloc[1] == 70.0   # subj1 결측행 = 자기 baseline(통계 60 아님)
        assert result["df"]["WT"].iloc[3] == 50.0   # subj2 결측행 = 자기 baseline

    def test_no_cross_subject_bleed(self):
        """③ ★ baseline 전파는 subject별 — subj1 baseline(70)이 subj2(55) 행으로 새지 않는다(interleaved).

        행 순서 [1,2,1,2]에서 단순 ffill(groupby 없음)이면 55→다음행 오염 가능. map per subject_id는 격리.
        """
        df = pd.DataFrame({
            "subject_id": [1, 2, 1, 2],
            "time_value": [0, 0, 24, 24],
            "WT": [70.0, 55.0, np.nan, np.nan],
        })
        meta = {"a7_state": "BASELINE-CLEAN", "baseline_covariates": ["WT"]}
        result = assign_baseline_covariate_l3(df, meta)
        assert result["success"] is True
        assert list(result["df"]["WT"]) == [70.0, 55.0, 70.0, 55.0]  # subj1=70, subj2=55, 오염 없음

    def test_baseline_identified_by_time_not_row_order(self):
        """★독립검증: baseline은 time==0로 식별(첫 행 아님) — 비정렬 [t24=99, t0=70] → 전파값=70.

        spurious pass 방지: time 식별을 안 하고 첫 행을 baseline으로 쓰면 99가 전파된다(잘못).
        """
        df = pd.DataFrame({"subject_id": [1, 1], "time_value": [24, 0], "WT": [99.0, 70.0]})
        meta = {"a7_state": "BASELINE-CLEAN", "baseline_covariates": ["WT"]}
        result = assign_baseline_covariate_l3(df, meta)
        assert result["success"] is True
        assert list(result["df"]["WT"]) == [70.0, 70.0]      # t0=70 전파
        assert (result["df"]["WT"] != 99.0).all()            # 첫 행(t24=99) 아님

    def test_unmapped_sex_not_fabricated(self):
        """매핑 불가 SEX('U') baseline → NaN(임의 정수 코딩 금지) → fail Q07."""
        df = pd.DataFrame({"subject_id": [1, 2], "time_value": [0, 0], "SEX": ["M", "U"]})
        meta = {"a7_state": "BASELINE-CLEAN", "baseline_covariates": ["SEX"]}
        result = assign_baseline_covariate_l3(df, meta)
        assert result["success"] is False
        assert result["route_to_q"] == "Q07"
        assert pd.isna(result["df"]["SEX"].iloc[1])   # 'U'를 임의 정수로 코딩하지 않음

    def test_policy_missing_routes_q07(self):
        """a7_state=POLICY-MISSING → fail Q07 (axis gate)."""
        df = pd.DataFrame({"subject_id": [1, 2], "time_value": [0, 0], "WT": [70.0, 55.0]})
        result = assign_baseline_covariate_l3(df, {"a7_state": "POLICY-MISSING", "baseline_covariates": ["WT"]})
        assert result["success"] is False
        assert result["route_to_q"] == "Q07"

    def test_time_value_fallback_no_keyerror(self):
        """★GAP-17: TIME 컬럼 부재 → df['time_value']==0 fallback (KeyError 아님), 정상 success."""
        df = pd.DataFrame({"subject_id": [1, 1], "time_value": [0, 24], "WT": [70.0, np.nan]})
        meta = {"a7_state": "BASELINE-CLEAN", "baseline_covariates": ["WT"]}
        result = assign_baseline_covariate_l3(df, meta)   # TIME 없음 → time_value fallback
        assert result["success"] is True
        assert list(result["df"]["WT"]) == [70.0, 70.0]

    def test_groupby_key_fallback_subject_id_then_id(self):
        """★GAP-17: subject_id 부재·ID 존재 → ID로 groupby(verbatim postcond는 subject_id 하드코딩이라 미assert)."""
        df = pd.DataFrame({"ID": [1, 1], "time_value": [0, 24], "WT": [70.0, np.nan]})
        meta = {"a7_state": "BASELINE-CLEAN", "baseline_covariates": ["WT"]}
        result = assign_baseline_covariate_l3(df, meta)   # subject_id 없음 → ID 기준 전파
        assert result["success"] is True
        assert list(result["df"]["WT"]) == [70.0, 70.0]

    def test_gap3_fallback_attaches_detected_covariates(self):
        """GAP-3 방어: baseline_covariates 미선언이라도 df covariate 컬럼 탐지·부착(silent no-op 금지)."""
        df = pd.DataFrame({"subject_id": [1, 2], "time_value": [0, 0], "WT": [70.5, 55.0], "SEX": ["M", "F"]})
        result = assign_baseline_covariate_l3(df, {"a7_state": "BASELINE-CLEAN"})  # 리스트 미주입
        assert result["success"] is True
        assert pd.api.types.is_integer_dtype(result["df"]["SEX"])  # 탐지되어 코딩됨(빈 순회 아님)
        assert list(result["df"]["SEX"]) == [0, 1]

    def test_input_df_not_mutated(self):
        """transform은 df.copy()를 사용 — 원본 df의 SEX를 0/1로 변형 금지."""
        df = pd.DataFrame({"subject_id": [1, 2], "time_value": [0, 0], "SEX": ["M", "F"]})
        original_sex = list(df["SEX"])
        assign_baseline_covariate_l3(df, {"a7_state": "BASELINE-CLEAN", "baseline_covariates": ["SEX"]})
        assert list(df["SEX"]) == original_sex  # 원본 SEX 여전히 'M'/'F'


class TestC0141Adversarial:
    """c0141 adversarial traps: 시변 공변량 부착(L-2→L-3) LOCF silent-error.

    설계(c0023 동형, key='subject_id'): LOCF(groupby('subject_id').ffill()) = vocab §A V10 PROPAGATE
    (정당; 자의적 IMPUTE 아님). 핵심 silent-error: (1) cross-subject bleed 금지 — groupby 없는 ffill은
    타 subject 값으로 오염, (2) leading 결측은 직전 관측 부재이므로 bfill/mean 날조 없이 Q07. structural
    gate: 'subject_id' 부재→Q07(c0023 'ID' 대비, GAP-17). 입력계약: tv_covariates 생산자 부재(GAP-3).
    """

    def test_locf_within_subject_no_cross_bleed(self):
        """★ ffill은 subject_id 내에서만 — subject2 leading 결측이 subject1 값으로 오염되면 안 된다.

        subject_id=[1,1,2,2], WT=[70,NaN,NaN,55]. groupby ffill: id1→[70,70], id2→[NaN,55].
        id2 첫 행은 직전 관측 없어 NaN 유지(70으로 채우면 cross-subject 오염). residual NaN → Q07.
        """
        df = pd.DataFrame({"subject_id": [1, 1, 2, 2], "WT": [70.0, np.nan, np.nan, 55.0]})
        meta = {"a7_state": "TIME-VARYING", "tv_covariates": ["WT"]}
        result = assign_time_varying_covariate_l3(df, meta)
        assert result["success"] is False
        assert result["route_to_q"] == "Q07"
        assert pd.isna(result["df"]["WT"].iloc[2])   # id2 첫 행: id1의 70으로 오염 안 됨
        assert result["df"]["WT"].iloc[1] == 70.0    # id1은 정상 carry-forward

    def test_ffill_carries_observed_not_fabricated(self):
        """중간 결측은 직전 *관측값*으로 채워진다(평균 날조 아님): [70,NaN,65]→[70,70,65]."""
        df = pd.DataFrame({"subject_id": [1, 1, 1], "WT": [70.0, np.nan, 65.0]})
        meta = {"a7_state": "TIME-VARYING", "tv_covariates": ["WT"]}
        result = assign_time_varying_covariate_l3(df, meta)
        assert result["success"] is True
        assert list(result["df"]["WT"]) == [70.0, 70.0, 65.0]
        assert result["df"]["WT"].iloc[1] != 67.5   # mean(70,65)=67.5로 날조 안 됨

    def test_no_mean_or_median_fill(self):
        """trailing 결측은 마지막 관측(LOCF)으로 채워진다 — 통계 아님: [70,80,NaN]→[70,80,80]."""
        df = pd.DataFrame({"subject_id": [1, 1, 1], "WT": [70.0, 80.0, np.nan]})
        meta = {"a7_state": "TIME-VARYING", "tv_covariates": ["WT"]}
        result = assign_time_varying_covariate_l3(df, meta)
        assert result["success"] is True
        assert result["df"]["WT"].iloc[2] == 80.0   # 마지막 관측 carry-forward
        assert result["df"]["WT"].iloc[2] != 75.0   # mean/median(70,80)=75로 날조 안 됨

    def test_leading_missing_routes_q07(self):
        """leading 결측(직전 관측 부재) → ffill 미충족 → Q07 (bfill 금지)."""
        df = pd.DataFrame({"subject_id": [1, 1], "WT": [np.nan, 65.0]})
        meta = {"a7_state": "TIME-VARYING", "tv_covariates": ["WT"]}
        result = assign_time_varying_covariate_l3(df, meta)
        assert result["success"] is False
        assert result["route_to_q"] == "Q07"
        assert pd.isna(result["df"]["WT"].iloc[0])   # 직전 관측 없어 NaN 유지

    def test_policy_missing_routes_q07(self):
        """a7_state=POLICY-MISSING → fail Q07 (axis gate)."""
        df = pd.DataFrame({"subject_id": [1, 1], "WT": [70.0, 72.0]})
        result = assign_time_varying_covariate_l3(df, {"a7_state": "POLICY-MISSING", "tv_covariates": ["WT"]})
        assert result["success"] is False
        assert result["route_to_q"] == "Q07"

    def test_missing_subject_id_column_routes_q07(self):
        """'subject_id' 컬럼 부재(groupby 키 없음) → fail Q07 (structural gate; c0023 'ID' 대비, GAP-17)."""
        df = pd.DataFrame({"ID": [1, 1], "WT": [70.0, np.nan]})
        result = assign_time_varying_covariate_l3(df, {"a7_state": "TIME-VARYING", "tv_covariates": ["WT"]})
        assert result["success"] is False
        assert result["route_to_q"] == "Q07"

    def test_input_df_not_mutated(self):
        """transform은 df.copy()를 사용 — 원본 df는 ffill되지 않는다."""
        df = pd.DataFrame({"subject_id": [1, 1], "WT": [70.0, np.nan]})
        assign_time_varying_covariate_l3(df, {"a7_state": "TIME-VARYING", "tv_covariates": ["WT"]})
        assert pd.isna(df["WT"].iloc[1])   # 원본 결측 그대로(copy 사용)


class TestC0121Adversarial:
    """c0121 adversarial traps: 공변량 wide→long PIVOT silent-error (★ 사용자 ①②③ + 무결성).

    설계(사용자 ★★★ 확정): 출력 shape = REFINED wide→long(postcond > snippet, GAP-21). 핵심 silent-error:
    ① plain melt로 잘못 구현돼 base명('WT') 대신 'cov_value'가 생기면 fail(postcond 위반 검출),
    ② cov_layout 부재 시 pivot 미수행을 success=True로 조용히 통과(no-op) 금지 — fail+route_to_q=None,
    ③ multi-cov(WT_V*,AGE_V*)가 한 컬럼에 섞이면 fail(별도 WT,AGE 컬럼 유지). 무결성: ID×visit 행 수
    정확·비결측 값 손실/중복 0. ragged wide 결측은 NaN 보존(IMPUTE 금지). scope-out 라우팅은 None(Q 날조
    금지, can_route_to_q=[]). 분기키 cov_layout는 c0380/c0381(미구현)이 생산(GAP-16) — 본 테스트는 직접 주입.
    """

    def test_value_column_named_by_base_not_cov_value(self):
        """① plain-melt 회귀 방지: 값 컬럼은 base명('WT')이지 'cov_value'가 아니다."""
        df = pd.DataFrame({"ID": [1, 2], "WT_V1": [70, 55], "WT_V2": [68, 54]})
        result = pivot_covariate_layout(df, {"cov_layout": "wide", "covariate_columns": ["WT"]})
        assert result["success"] is True
        out = result["df"]
        assert "WT" in out.columns
        assert "cov_value" not in out.columns
        assert "visit" in out.columns

    def test_cov_layout_missing_not_silent_noop(self):
        """② cov_layout 부재 → silent no-op 금지: success=False, route_to_q=None(pivot 미수행을 위장 통과 안 함)."""
        df = pd.DataFrame({"ID": [1, 2], "WT_V1": [70, 55], "WT_V2": [68, 54]})
        result = pivot_covariate_layout(df, {"covariate_columns": ["WT"]})   # cov_layout 없음
        assert result["success"] is False
        assert result["route_to_q"] is None
        assert "WT_V1" in result["df"].columns      # 변환 안 됨(wide 그대로)
        assert "visit" not in result["df"].columns  # success=True로 위장한 no-op 아님

    def test_multi_covariate_not_mixed(self):
        """③ multi-cov는 한 컬럼에 섞이지 않는다 — WT,AGE 별도 scalar 컬럼."""
        df = pd.DataFrame({"ID": [1, 2], "WT_V1": [70, 55], "WT_V2": [68, 54],
                           "AGE_V1": [30, 40], "AGE_V2": [31, 41]})
        result = pivot_covariate_layout(df, {"cov_layout": "wide", "covariate_columns": ["WT", "AGE"]})
        assert result["success"] is True
        out = result["df"]
        assert "WT" in out.columns and "AGE" in out.columns
        assert "cov_value" not in out.columns
        assert list(out["WT"]) == [70, 68, 55, 54]      # 정렬(ID,visit) 후
        assert list(out["AGE"]) == [30, 31, 40, 41]

    def test_pivot_no_row_loss_or_dup(self):
        """무결성: long 행 수 = subjects×visits, 비결측 값 손실/중복 0."""
        df = pd.DataFrame({"ID": [1, 2, 3], "WT_V1": [70, 55, 60], "WT_V2": [68, 54, 59]})
        result = pivot_covariate_layout(df, {"cov_layout": "wide", "covariate_columns": ["WT"]})
        assert result["success"] is True
        out = result["df"]
        assert len(out) == 3 * 2                          # 3 subjects × 2 visits(손실/중복 없음)
        assert out["WT"].notna().sum() == 6
        assert sorted(out["WT"].tolist()) == sorted([70, 68, 55, 54, 60, 59])

    def test_ragged_wide_na_preserved_not_imputed(self):
        """ragged wide(subject2 V2 결측) → 결측 NaN 보존(평균/median 날조 없음), 행 drop 없음."""
        df = pd.DataFrame({"ID": [1, 2], "WT_V1": [70.0, 55.0], "WT_V2": [68.0, np.nan]})
        result = pivot_covariate_layout(df, {"cov_layout": "wide", "covariate_columns": ["WT"]})
        assert result["success"] is True
        out = result["df"]
        assert len(out) == 4                              # (2,V2) 행 drop 안 됨
        s2_v2 = out[(out["ID"] == 2) & (out["visit"] == "V2")]["WT"]
        assert pd.isna(s2_v2.iloc[0])                     # 통계 fill 아님 — NaN 보존
        assert out["WT"].notna().sum() == 3               # 비결측 3개(원본 동일)

    def test_unrecognized_layout_no_fabricated_q(self):
        """미인식 layout → route_to_q=None(can_route_to_q=[] 밖 Q 날조 금지)."""
        df = pd.DataFrame({"ID": [1, 2], "WT_V1": [70, 55], "WT_V2": [68, 54]})
        result = pivot_covariate_layout(df, {"cov_layout": "weird", "covariate_columns": ["WT"]})
        assert result["success"] is False
        assert result["route_to_q"] is None

    def test_input_df_not_mutated(self):
        """transform은 df.copy()를 사용 — 원본 wide df는 변형되지 않는다."""
        df = pd.DataFrame({"ID": [1, 2], "WT_V1": [70, 55], "WT_V2": [68, 54]})
        original_cols = list(df.columns)
        pivot_covariate_layout(df, {"cov_layout": "wide", "covariate_columns": ["WT"]})
        assert list(df.columns) == original_cols          # 원본 wide 컬럼 그대로
        assert "visit" not in df.columns                  # long 변형이 원본에 누출 안 됨

    def test_long_passthrough_unchanged(self):
        """cov_layout='long' → 이미 long, 반환 df가 입력값과 동일(불변)."""
        df = pd.DataFrame({"ID": [1, 1], "visit": ["V1", "V2"], "WT": [70, 68]})
        result = pivot_covariate_layout(df, {"cov_layout": "long", "covariate_columns": ["WT"]})
        assert result["success"] is True
        out = result["df"]
        assert list(out["WT"]) == [70, 68]
        assert list(out["visit"]) == ["V1", "V2"]


# ===== Phase 5 · Slice 2 — TIME family adversarial =====

class TestC0213Adversarial:
    """c0213 adversarial traps: anchor 일관성 silent over/under-verify 차단."""

    def test_df_readonly_not_modified(self):
        """kind=verify → df 변경 금지(SRP)."""
        df = pd.DataFrame({"time_value": [0.0, 1.0, 2.0]})
        original_cols = list(df.columns)
        original_shape = df.shape
        verify_time_anchor(df, {"time_anchor": ["Day 1", "Day 2"]})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_meta_consistent_is_written(self):
        """meta['time_anchor_consistent'] side-effect 기록(bool)."""
        meta = {"time_anchor": ["Day 1", "Day 2"]}
        verify_time_anchor(pd.DataFrame({"time_value": [0.0]}), meta)
        assert isinstance(meta.get("time_anchor_consistent"), bool)

    def test_mixed_anchor_not_silent_pass(self):
        """혼재 anchor(day/visit/date)를 'anchor 존재→일관'으로 silent pass 금지 → False, Q02."""
        df = pd.DataFrame({"time_value": [0.0, 1.0, 2.0]})
        meta = {"time_anchor": ["Day 1", "Visit 2", "2024-01-15"]}
        result = verify_time_anchor(df, meta)
        assert result["time_anchor_consistent"] is False
        assert result["pass"] is False
        assert result["route_to_q"] == "Q02"

    def test_declared_inconsistent_respected(self):
        """외부 선언 time_anchor_consistent=False는 토큰이 일관적으로 보여도 존중 → Q02."""
        df = pd.DataFrame({"time_value": [0.0, 1.0]})
        meta = {"time_anchor": ["Day 1", "Day 2"], "time_anchor_consistent": False}
        result = verify_time_anchor(df, meta)
        assert result["time_anchor_consistent"] is False
        assert result["route_to_q"] == "Q02"

    def test_no_anchor_no_fabricated_inconsistency(self):
        """앵커 토큰 부재(time_value만) → 비일관 날조 금지: 기본 consistent=True, route None."""
        df = pd.DataFrame({"time_value": [0.0, 1.0, 2.0]})
        result = verify_time_anchor(df, {})
        assert result["time_anchor_consistent"] is True
        assert result["route_to_q"] is None

    def test_df_column_anchor_mixed_detected(self):
        """meta 선언 없이 df 'time_anchor' 컬럼에서 혼재 감지(fallback 경로) → False, Q02."""
        df = pd.DataFrame({
            "time_value": [0.0, 1.0],
            "time_anchor": ["Day 1", "Visit 1"],
        })
        result = verify_time_anchor(df, {})
        assert result["time_anchor_consistent"] is False
        assert result["route_to_q"] == "Q02"


class TestC0251Adversarial:
    """c0251 adversarial traps: A3 fail-state 라우팅 silent 오라우팅 차단."""

    def test_ambiguous_routes_q02(self):
        """AMBIGUOUS → Q02 (Q12/INVALID로 오라우팅 금지)."""
        result = route_time_format(pd.DataFrame({"time_value": [0.0]}), {"a3_state": "AMBIGUOUS"})
        assert result["routing_decision"] == "Q02"
        assert result["q_code"] == "Q02"
        assert result["terminal"] == "QUARANTINE"

    def test_unrecoverable_routes_q12_not_invalid(self):
        """★ snippet 산문('UNRECOVERABLE→INVALID') 무시: UNRECOVERABLE → Q12 (can_route_to_q·strands SSOT, GAP-7)."""
        result = route_time_format(pd.DataFrame({"time_value": [0.0]}), {"a3_state": "UNRECOVERABLE"})
        assert result["routing_decision"] == "Q12"
        assert result["routing_decision"] != "INVALID"
        assert result["q_code"] == "Q12"
        assert result["terminal"] == "QUARANTINE"

    def test_routing_decision_in_postcond_set(self):
        """postcond: routing_decision ∈ {Q02,Q12,INVALID} (두 fail state 모두)."""
        for state in ("AMBIGUOUS", "UNRECOVERABLE"):
            result = route_time_format(pd.DataFrame({"time_value": [0.0]}), {"a3_state": state})
            assert result["routing_decision"] in ["Q02", "Q12", "INVALID"]

    def test_q_route_terminal_is_quarantine_not_auto(self):
        """Q-route는 terminal=QUARANTINE — silent AUTO/None 종착 금지."""
        result = route_time_format(pd.DataFrame({"time_value": [0.0]}), {"a3_state": "AMBIGUOUS"})
        assert result["terminal"] == "QUARANTINE"
        assert result["terminal"] not in (None, "AUTO")


class TestC0250Adversarial:
    """c0250 adversarial traps: A0 fail-state 라우팅 silent 오라우팅 차단 (단일 fail-state → Q11)."""

    def test_aic_missing_routes_q11(self):
        """AIC-MISSING → Q11 (QUARANTINE)."""
        result = route_column_schema(pd.DataFrame({"ID": [1]}), {"a0_state": "AIC-MISSING"})
        assert result["routing_decision"] == "Q11"
        assert result["q_code"] == "Q11"
        assert result["terminal"] == "QUARANTINE"

    def test_pass_state_not_routed(self):
        """★ unconditional-Q11(snippet 'routing=Q11') 차단: pass-state는 Q11 금지 → INVALID."""
        for state in ("AIC-PK", "AIC-POPPK", "AIC-PKPD"):
            result = route_column_schema(pd.DataFrame({"ID": [1]}), {"a0_state": state})
            assert result["routing_decision"] == "INVALID", state
            assert result["q_code"] is None, state

    def test_missing_state_routes_invalid_not_q11(self):
        """meta에 a0_state 부재 시 silent Q11 금지 → INVALID."""
        result = route_column_schema(pd.DataFrame({"ID": [1]}), {})
        assert result["routing_decision"] == "INVALID"
        assert result["q_code"] is None


class TestC0252Adversarial:
    """c0252 adversarial traps: A4 fail-state 라우팅 silent 오라우팅 차단 (Q04/Q08/Q14/INVALID)."""

    def test_missing_no_policy_routes_q08(self):
        """MISSING-NO-POLICY → Q08 (Q14/INVALID로 오라우팅 금지)."""
        result = route_amt(pd.DataFrame({"AMT": [100]}), {"a4_state": "MISSING-NO-POLICY"})
        assert result["routing_decision"] == "Q08"
        assert result["q_code"] == "Q08"
        assert result["terminal"] == "QUARANTINE"

    def test_addl_actual_conflict_routes_q14_not_q08(self):
        """ADDL-ACTUAL-CONFLICT → Q14 (Q08로 분기 혼동 오라우팅 금지)."""
        result = route_amt(pd.DataFrame({"AMT": [100]}), {"a4_state": "ADDL-ACTUAL-CONFLICT"})
        assert result["routing_decision"] == "Q14"
        assert result["q_code"] == "Q14"

    def test_unrecoverable_routes_invalid_not_q(self):
        """UNRECOVERABLE → INVALID (Q08/Q14로 silent 승격 금지; SSOT 174 strand)."""
        result = route_amt(pd.DataFrame({"AMT": [100]}), {"a4_state": "UNRECOVERABLE"})
        assert result["routing_decision"] == "INVALID"
        assert result["q_code"] is None

    def test_infusion_stop_restart_routes_q04_not_invalid(self):
        """★ GAP-31 RESOLVED (결정 A): INFUSION-STOP-RESTART → Q04 (SSOT 168 strand; cite universe_sm
        §3 A4 '無 Q04'). INVALID default fallthrough로 silent 회귀 금지."""
        result = route_amt(pd.DataFrame({"AMT": [100]}), {"a4_state": "INFUSION-STOP-RESTART"})
        assert result["routing_decision"] == "Q04"
        assert result["routing_decision"] != "INVALID"
        assert result["q_code"] == "Q04"
        assert result["terminal"] == "QUARANTINE"

    def test_routing_decision_in_postcond_set(self):
        """postcond: routing_decision ∈ {Q04,Q08,Q14,INVALID} (precond 4-state)."""
        for state in ("MISSING-NO-POLICY", "ADDL-ACTUAL-CONFLICT", "INFUSION-STOP-RESTART", "UNRECOVERABLE"):
            result = route_amt(pd.DataFrame({"AMT": [100]}), {"a4_state": state})
            assert result["routing_decision"] in ["Q04", "Q08", "Q14", "INVALID"], state


class TestC0254Adversarial:
    """c0254 adversarial traps: A7 fail-state 라우팅 silent 오라우팅 차단 (Q07/Q13)."""

    def test_policy_missing_routes_q07(self):
        """POLICY-MISSING → Q07 (Q13으로 오라우팅 금지)."""
        result = route_covariate_layout(pd.DataFrame({"WT": [70]}), {"a7_state": "POLICY-MISSING"})
        assert result["routing_decision"] == "Q07"
        assert result["q_code"] == "Q07"
        assert result["terminal"] == "QUARANTINE"

    def test_key_missing_routes_q13_not_q07(self):
        """KEY-MISSING → Q13 (Q07로 분기 혼동 오라우팅 금지)."""
        result = route_covariate_layout(pd.DataFrame({"WT": [70]}), {"a7_state": "KEY-MISSING"})
        assert result["routing_decision"] == "Q13"
        assert result["q_code"] == "Q13"

    def test_pass_state_routes_invalid_not_q07(self):
        """★ naive 'else Q07' 차단: pass-state는 Q07로 silent 라우팅 금지 → INVALID."""
        for state in ("NONE-REQUIRED", "BASELINE-CLEAN", "TIME-VARYING"):
            result = route_covariate_layout(pd.DataFrame({"WT": [70]}), {"a7_state": state})
            assert result["routing_decision"] == "INVALID", state
            assert result["q_code"] is None, state


class TestC0255Adversarial:
    """c0255 adversarial traps: A8 fail-state 라우팅 silent 오라우팅 차단 (단일 fail-state → Q09)."""

    def test_cmt_policy_missing_routes_q09(self):
        """CMT-POLICY-MISSING → Q09 (QUARANTINE)."""
        result = route_analyte_column(pd.DataFrame({"DV": [0.5]}), {"a8_state": "CMT-POLICY-MISSING"})
        assert result["routing_decision"] == "Q09"
        assert result["q_code"] == "Q09"
        assert result["terminal"] == "QUARANTINE"

    def test_pass_state_not_routed(self):
        """★ unconditional-Q09 차단: pass-state는 Q09 금지 → INVALID."""
        for state in ("SINGLE-DRUG", "MULTI-CMT-DEFINED", "METABOLITE-DEFINED"):
            result = route_analyte_column(pd.DataFrame({"DV": [0.5]}), {"a8_state": state})
            assert result["routing_decision"] == "INVALID", state
            assert result["q_code"] is None, state


class TestC0256Adversarial:
    """c0256 adversarial traps: A9 fail-state 라우팅 silent 오라우팅 차단 (Q06/Q15D/INVALID)."""

    def test_protocol_deviation_no_policy_routes_q06(self):
        """PROTOCOL-DEVIATION-NO-POLICY → Q06 (Q15D/INVALID로 오라우팅 금지)."""
        result = route_cross_column_invariant(pd.DataFrame({"EVID": [1]}), {"a9_state": "PROTOCOL-DEVIATION-NO-POLICY"})
        assert result["routing_decision"] == "Q06"
        assert result["q_code"] == "Q06"
        assert result["terminal"] == "QUARANTINE"

    def test_reanalysis_final_missing_routes_q15d_not_q06(self):
        """REANALYSIS-FINAL-MISSING → Q15D (Q06로 분기 혼동 오라우팅 금지)."""
        result = route_cross_column_invariant(pd.DataFrame({"EVID": [0]}), {"a9_state": "REANALYSIS-FINAL-MISSING"})
        assert result["routing_decision"] == "Q15D"
        assert result["q_code"] == "Q15D"

    def test_irreconcilable_routes_invalid_not_q(self):
        """IRRECONCILABLE → INVALID (Q06/Q15D로 silent 승격 금지; SSOT 30 strand)."""
        result = route_cross_column_invariant(pd.DataFrame({"EVID": [1]}), {"a9_state": "IRRECONCILABLE"})
        assert result["routing_decision"] == "INVALID"
        assert result["q_code"] is None

    def test_routing_decision_in_postcond_set(self):
        """postcond: routing_decision ∈ {Q06,Q15D,INVALID} (precond 3-state 전부)."""
        for state in ("PROTOCOL-DEVIATION-NO-POLICY", "REANALYSIS-FINAL-MISSING", "IRRECONCILABLE"):
            result = route_cross_column_invariant(pd.DataFrame({"EVID": [1]}), {"a9_state": state})
            assert result["routing_decision"] in ["Q06", "Q15D", "INVALID"], state


class TestC0257Adversarial:
    """c0257 adversarial traps: A6 fail-state 라우팅 silent 오라우팅 차단 (Q03/Q04)."""

    def test_ambiguous_routes_q04(self):
        """AMBIGUOUS → Q04 (Q03으로 오라우팅 금지)."""
        result = route_row_ordering(pd.DataFrame({"ID": [1]}), {"a6_state": "AMBIGUOUS"})
        assert result["routing_decision"] == "Q04"
        assert result["q_code"] == "Q04"
        assert result["terminal"] == "QUARANTINE"

    def test_q03_states_route_q03_not_q04(self):
        """★ snippet 'routing=Q04' 무시: 4개 비-AMBIGUOUS fail-state → Q03 (Q04로 silent 라우팅 금지;
        postcond·can_route_to_q·strands SSOT, c0251 선례)."""
        for state in ("COVARIATE-CHANGE", "RESET-NEEDED", "SAME-TIME-RESOLVABLE", "SEPARABLE"):
            result = route_row_ordering(pd.DataFrame({"ID": [1]}), {"a6_state": state})
            assert result["routing_decision"] == "Q03", state
            assert result["routing_decision"] != "Q04", state
            assert result["q_code"] == "Q03", state

    def test_pass_state_routes_invalid(self):
        """★ over-broad 차단: pass a6-state(URINE-INTERVAL)는 Q03/Q04 어느 쪽으로도 silent 라우팅 금지 → INVALID."""
        result = route_row_ordering(pd.DataFrame({"ID": [1]}), {"a6_state": "URINE-INTERVAL"})
        assert result["routing_decision"] == "INVALID"
        assert result["q_code"] is None


class TestC0310Adversarial:
    """c0310 adversarial traps: 시간 형식 silent 오감지 차단."""

    def test_df_readonly_not_modified(self):
        """kind=detect → df 변경 금지(SRP)."""
        df = pd.DataFrame({"time_value": ["0:00", "1:30"]})
        original_cols = list(df.columns)
        original_shape = df.shape
        detect_time_format_mess(df, {})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_meta_format_written_in_postcond_set(self):
        """meta['time_format_detected'] 기록 + postcond 범위 ∈ 5형식."""
        meta = {}
        detect_time_format_mess(pd.DataFrame({"time_value": ["0:00"]}), meta)
        assert meta.get("time_format_detected") in ["clock", "elapsed", "decimal", "datetime", "mixed"]

    def test_mixed_not_silent_single(self):
        """혼재(clock+datetime)를 첫값 기준 'clock'으로 silent 단정 금지 → 'mixed'."""
        df = pd.DataFrame({"time_value": ["0:00", "2024-01-15"]})
        result = detect_time_format_mess(df, {})
        assert result["time_format_detected"] == "mixed"

    def test_datetime_not_misread_as_decimal(self):
        """ISO datetime을 decimal로 silent 오분류 금지 → 'datetime'."""
        df = pd.DataFrame({"time_value": ["2024-01-15", "2024-01-16"]})
        result = detect_time_format_mess(df, {})
        assert result["time_format_detected"] == "datetime"

    def test_declared_overrides_data(self):
        """선언 meta['time_format']='elapsed'는 data 추정보다 우선."""
        df = pd.DataFrame({"time_value": ["0:00", "1:30"]})
        result = detect_time_format_mess(df, {"time_format": "elapsed"})
        assert result["time_format_detected"] == "elapsed"


class TestC0314Adversarial:
    """c0314 adversarial traps: 시간 기준점 유형 silent 오감지·None 차단."""

    def test_df_readonly_not_modified(self):
        """kind=detect → df 변경 금지(SRP)."""
        df = pd.DataFrame({"time_value": [0.0, 1.0], "time_anchor": ["Day 1", "Day 2"]})
        original_cols = list(df.columns)
        original_shape = df.shape
        detect_time_anchor(df, {})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_anchor_type_never_none(self):
        """postcond: time_anchor_type is not None — 앵커 부재여도 None 금지('none' 정직 표기)."""
        result = detect_time_anchor(pd.DataFrame({"time_value": [0.0, 1.0]}), {})
        assert result["time_anchor_type"] is not None
        assert result["time_anchor_type"] == "none"

    def test_mixed_anchor_detected(self):
        """혼재 anchor(day+date)를 단일유형으로 silent 단정 금지 → 'mixed'."""
        df = pd.DataFrame({"time_value": [0.0, 1.0], "time_anchor": ["Day 1", "2024-01-15"]})
        result = detect_time_anchor(df, {})
        assert result["time_anchor_type"] == "mixed"

    def test_meta_anchor_tokens_priority(self):
        """meta['time_anchor'] 선언 토큰 우선 사용(df 컬럼 없이도 분류)."""
        result = detect_time_anchor(pd.DataFrame({"time_value": [0.0]}), {"time_anchor": ["Visit 1", "Visit 2"]})
        assert result["time_anchor_type"] == "period-relative"


class TestC0311Adversarial:
    """c0311 adversarial traps: 시간 형식 변환 silent no-op·부분 NaN 차단."""

    def test_input_df_not_mutated(self):
        """transform은 df.copy() — 원본 time_value(문자열) 불변."""
        df = pd.DataFrame({"time_value": ["0:00", "1:30"]})
        convert_time_format(df, {"time_format_detected": "clock"})
        assert list(df["time_value"]) == ["0:00", "1:30"]

    def test_silent_noop_caught(self):
        """clock 문자열 미변환(no-op) 금지 → 실제 numeric, postcond 충족."""
        df = pd.DataFrame({"time_value": ["1:30", "2:00"]})
        result = convert_time_format(df, {"time_format_detected": "clock"})
        df_out = result["df"]
        assert df_out["time_value"].apply(lambda x: isinstance(x, (int, float))).all()
        assert list(df_out["time_value"]) == [1.5, 2.0]

    def test_unparseable_clock_routes_q02_not_partial_nan(self):
        """파싱 불가 토큰이 섞이면 부분 NaN을 silent 통과시키지 않고 fail/Q02."""
        df = pd.DataFrame({"time_value": ["1:30", "garbage"]})
        result = convert_time_format(df, {"time_format_detected": "clock"})
        assert result["success"] is False
        assert result["route_to_q"] == "Q02"

    def test_mixed_format_routes_q02(self):
        """mixed 형식은 결정적 변환 불가 → Q02(can_route_to_q), silent 통과 금지."""
        df = pd.DataFrame({"time_value": ["0:00", "1.5"]})
        result = convert_time_format(df, {"time_format_detected": "mixed"})
        assert result["success"] is False
        assert result["route_to_q"] == "Q02"

    def test_datetime_to_elapsed_hours(self):
        """datetime 형식 → 첫 시각 기준 elapsed hours numeric."""
        df = pd.DataFrame({"time_value": ["2024-01-01 00:00", "2024-01-01 02:00"]})
        result = convert_time_format(df, {"time_format_detected": "datetime"})
        assert result["success"] is True
        df_out = result["df"]
        assert df_out["time_value"].apply(lambda x: isinstance(x, (int, float))).all()
        assert list(df_out["time_value"]) == [0.0, 2.0]


class TestC0315Adversarial:
    """c0315 adversarial traps: 시간 기준점 파싱 vacuous no-op·부분 NaN 차단."""

    def test_input_df_not_mutated(self):
        """transform은 df.copy() — 원본에 time_anchor_parsed 누출 금지."""
        df = pd.DataFrame({"time_value": [0, 1], "time_anchor": ["Day 1", "Day 2"]})
        convert_time_anchor(df, {})
        assert "time_anchor_parsed" not in df.columns

    def test_vacuous_noop_caught(self):
        """time_anchor 존재 시 parsed 컬럼 미생성(부재로 postcond vacuous 우회) 금지 → 생성·정확."""
        df = pd.DataFrame({"time_value": [0, 1], "time_anchor": ["Day 1", "Day 2"]})
        result = convert_time_anchor(df, {})
        df_out = result["df"]
        assert "time_anchor_parsed" in df_out.columns
        assert list(df_out["time_anchor_parsed"]) == [0.0, 24.0]

    def test_unparseable_anchor_routes_q02(self):
        """비교 불가 토큰(절대날짜 등)이 섞여 부분 NaN이면 silent 통과 금지 → fail/Q02."""
        df = pd.DataFrame({"time_value": [0, 1], "time_anchor": ["Day 1", "2024-01-15"]})
        result = convert_time_anchor(df, {})
        assert result["success"] is False
        assert result["route_to_q"] == "Q02"


class TestC0312Adversarial:
    """c0312 adversarial traps: 시간대 불일치 silent 오감지·날조 차단."""

    def test_df_readonly_not_modified(self):
        """kind=detect → df 변경 금지(SRP)."""
        df = pd.DataFrame({"time_value": ["08:00 KST", "09:00 JST"]})
        original_cols = list(df.columns)
        original_shape = df.shape
        detect_timezone(df, {})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_mixed_tz_not_silent_single(self):
        """혼합 tz(KST+UTC)를 단일로 silent 단정 금지 → has_mixed_tz True, n_distinct_tz=2."""
        df = pd.DataFrame({"time_value": ["08:00 KST", "00:00 UTC"]})
        result = detect_timezone(df, {})
        assert result["tz_issues"]["has_mixed_tz"] is True
        assert result["tz_issues"]["n_distinct_tz"] == 2

    def test_no_tz_token_not_invented(self):
        """tz 토큰 부재(numeric time_value) → tz 날조 금지(has_mixed_tz False, tokens 빈)."""
        df = pd.DataFrame({"time_value": [0.0, 1.5, 3.0]})
        result = detect_timezone(df, {})
        assert result["tz_issues"]["has_mixed_tz"] is False
        assert result["tz_issues"]["tz_tokens"] == []

    def test_unknown_token_not_counted_as_tz(self):
        """known set 밖 토큰('XYZ')은 시간대로 오집계 금지(false positive 차단)."""
        df = pd.DataFrame({"time_value": ["08:00 XYZ", "09:00 XYZ"]})
        result = detect_timezone(df, {})
        assert result["tz_issues"]["tz_tokens"] == []
        assert result["tz_issues"]["has_mixed_tz"] is False

    def test_postcond_tz_issues_is_dict(self):
        """postcond: isinstance(meta.get('tz_issues'), dict) — 항상 dict 기록."""
        meta = {}
        detect_timezone(pd.DataFrame({"time_value": ["08:00 KST"]}), meta)
        assert isinstance(meta.get("tz_issues"), dict)


class TestC0313Adversarial:
    """c0313 adversarial traps: 시간대 정규화 vacuous/silent no-op·부분변환 차단 (GAP-27)."""

    def test_input_df_not_mutated(self):
        """transform은 df.copy() — 원본 time_value(tz 토큰) 불변."""
        df = pd.DataFrame({"time_value": ["09:00 KST", "00:00 UTC"]})
        normalize_timezone(df, {"tz_issues": {"has_mixed_tz": True}, "tz_target": "UTC"})
        assert list(df["time_value"]) == ["09:00 KST", "00:00 UTC"]

    def test_silent_noop_caught(self):
        """혼합 tz 미변환(flag만 set하는 no-op 포함) 금지 → 실제 단일 tz 통일 + 값 정확."""
        df = pd.DataFrame({"time_value": ["09:00 KST", "00:00 UTC"]})
        result = normalize_timezone(df, {"tz_issues": {"has_mixed_tz": True}, "tz_target": "UTC"})
        df_out = result["df"]
        assert {str(v).split()[-1] for v in df_out["time_value"]} == {"UTC"}
        assert list(df_out["time_value"]) == ["00:00 UTC", "00:00 UTC"]

    def test_vacuous_postcond_not_bypassed_when_detection_missing(self):
        """★ GAP-27: tz_issues(c0312 산출) 부재 시 default-True postcond를 우회한 silent 통과 금지
        → success=False, route_to_q=None(Q 날조 금지), flag 미설정."""
        df = pd.DataFrame({"time_value": ["09:00 KST", "00:00 UTC"]})
        meta = {}
        result = normalize_timezone(df, meta)
        assert result["success"] is False
        assert result["route_to_q"] is None
        assert meta.get("tz_normalized") is not True

    def test_unparseable_time_with_tz_not_partial(self):
        """tz 토큰 有 + 시각 파싱 불가가 섞이면 부분 변환을 silent 통과시키지 않고 fail."""
        df = pd.DataFrame({"time_value": ["09:00 KST", "morning KST"]})
        result = normalize_timezone(df, {"tz_issues": {"has_mixed_tz": False}, "tz_target": "UTC"})
        assert result["success"] is False

    def test_no_token_idempotent_but_flagged(self):
        """tz 토큰 부재(정규화 대상 없음) → 값 보존하되 flag 명시 set(정당 idempotent, 부재≠silent)."""
        df = pd.DataFrame({"time_value": [0.0, 1.5]})
        meta = {"tz_issues": {"has_mixed_tz": False, "tz_tokens": [], "n_distinct_tz": 0}}
        result = normalize_timezone(df, meta)
        assert result["success"] is True
        assert list(result["df"]["time_value"]) == [0.0, 1.5]
        assert meta.get("tz_normalized") is True


class TestC0380Adversarial:
    """c0380 adversarial traps: 공변량 레이아웃 silent 오판·날조 차단."""

    def test_df_readonly_not_modified(self):
        """kind=detect → df 변경 금지(SRP)."""
        df = pd.DataFrame({"ID": [1, 2], "WT_V1": [70, 55], "WT_V2": [68, 54]})
        original_cols = list(df.columns)
        original_shape = df.shape
        detect_covariate_layout(df, {})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_wide_not_silent_none(self):
        """비-covariate 접미사(DOSE_AMT) 혼재 속 covariate wide(AGE_V1,AGE_V2)를 'none' silent 오판 금지."""
        df = pd.DataFrame({"ID": [1], "AGE_V1": [45], "AGE_V2": [46], "DOSE_AMT": [100]})
        result = detect_covariate_layout(df, {})
        assert result["cov_layout"] == "wide"

    def test_long_not_misread_as_wide(self):
        """plain covariate 단일 컬럼(WT) → 'long'(visit 반복 부재인데 'wide' 날조 금지)."""
        df = pd.DataFrame({"ID": [1, 2], "WT": [70, 55]})
        result = detect_covariate_layout(df, {})
        assert result["cov_layout"] == "long"

    def test_no_covariate_not_invented(self):
        """covariate 컬럼 전무([ID,TIME,DV]) → 'none'(wide/long 날조 금지)."""
        df = pd.DataFrame({"ID": [1, 2], "TIME": [0, 24], "DV": [10.0, 5.0]})
        result = detect_covariate_layout(df, {})
        assert result["cov_layout"] == "none"

    def test_noncov_suffix_not_counted_wide(self):
        """non-covariate 접미사 컬럼(DV_1,DV_2)을 wide로 오집계 금지(false positive 차단) → 'none'."""
        df = pd.DataFrame({"ID": [1], "DV_1": [10.0], "DV_2": [5.0]})
        result = detect_covariate_layout(df, {})
        assert result["cov_layout"] == "none"

    def test_postcond_cov_layout_in_set(self):
        """postcond: meta.get('cov_layout') in ['wide','long','none'] — 항상 유효값 기록."""
        meta = {}
        detect_covariate_layout(pd.DataFrame({"WT_V1": [70], "WT_V2": [68]}), meta)
        assert meta.get("cov_layout") in ["wide", "long", "none"]


class TestC0381Adversarial:
    """c0381 adversarial traps: 공변량 레이아웃 분류 vacuous/silent no-op 차단 (GAP-27)."""

    def test_df_readonly_not_modified(self):
        """kind=detect(분류) → df 변경 금지(SRP). meta만 기록."""
        df = pd.DataFrame({"ID": [1, 2], "WT": [70, 55]})
        original_cols = list(df.columns)
        original_shape = df.shape
        classify_covariate_layout_mess(df, {"cov_layout": "wide"})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_vacuous_flag_not_set_when_detection_missing(self):
        """★ GAP-27 ③: cov_layout(c0380 산출) 부재 시 default-False postcond를 우회한 silent 통과 금지
        → success=False, route_to_q=None(Q 날조 금지), flag 미설정."""
        df = pd.DataFrame({"ID": [1]})
        meta = {}
        result = classify_covariate_layout_mess(df, meta)
        assert result["success"] is False
        assert result["route_to_q"] is None
        assert meta.get("cov_layout_classified") is not True

    def test_invalid_cov_layout_not_classified(self):
        """무효 cov_layout('sideways') → vacuous 분류 금지: success=False, flag 미설정."""
        df = pd.DataFrame({"ID": [1]})
        meta = {"cov_layout": "sideways"}
        result = classify_covariate_layout_mess(df, meta)
        assert result["success"] is False
        assert meta.get("cov_layout_classified") is not True

    def test_valid_layout_flag_explicitly_set(self):
        """cov_layout='wide' → flag를 default(False)가 아닌 명시 True로 설정."""
        meta = {"cov_layout": "wide"}
        result = classify_covariate_layout_mess(pd.DataFrame({"ID": [1]}), meta)
        assert result["cov_layout_classified"] is True
        assert meta.get("cov_layout_classified") is True

    def test_none_layout_idempotent_but_flagged(self):
        """cov_layout='none'(공변량 불요) → 정당한 분류, flag 명시 set(부재≠silent no-op)."""
        meta = {"cov_layout": "none"}
        result = classify_covariate_layout_mess(pd.DataFrame({"ID": [1]}), meta)
        assert result["success"] is True
        assert meta.get("cov_layout_classified") is True


class TestC0392Adversarial:
    """c0392 adversarial traps: 위약 감지 silent 오판·날조 차단 (AMT=0 vs 누락 구분)."""

    def test_df_readonly_not_modified(self):
        """kind=detect → df 변경 금지(SRP). meta만 기록."""
        df = pd.DataFrame({"subject_id": [1, 2], "dose_amount": [100, 0]})
        original_cols = list(df.columns)
        original_shape = df.shape
        detect_placebo_subject(df, {})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_amt_zero_detected_not_silent_false(self):
        """AMT=0(피험자 2) 존재 → has_placebo=True (False 하드코딩 vacuous 통과 차단)."""
        df = pd.DataFrame({"subject_id": [1, 2, 3], "dose_amount": [100, 0, 100]})
        result = detect_placebo_subject(df, {})
        assert result["has_placebo"] is True

    def test_missing_dose_not_mistaken_for_placebo(self):
        """dose 누락(NaN)만 있고 실제 AMT=0 없음 → has_placebo=False (누락≠위약, M105 구분)."""
        df = pd.DataFrame({"subject_id": [1, 2], "dose_amount": [100, None]})
        result = detect_placebo_subject(df, {})
        assert result["has_placebo"] is False

    def test_no_dose_column_not_invented(self):
        """dose_amount 컬럼 전무 → has_placebo=False(위약 날조 금지, graceful)."""
        df = pd.DataFrame({"subject_id": [1, 2], "TIME": [0, 24]})
        result = detect_placebo_subject(df, {})
        assert result["has_placebo"] is False

    def test_string_zero_dose_detected(self):
        """raw 문자열 dose '0'도 AMT=0으로 감지(to_numeric coerce) → has_placebo=True."""
        df = pd.DataFrame({"subject_id": [1, 2], "dose_amount": ["100", "0"]})
        result = detect_placebo_subject(df, {})
        assert result["has_placebo"] is True

    def test_postcond_has_placebo_is_bool(self):
        """postcond: isinstance(meta.get('has_placebo'), bool) — numpy.bool_ 누출 금지(파이썬 bool)."""
        meta = {}
        detect_placebo_subject(pd.DataFrame({"subject_id": [1], "dose_amount": [0]}), meta)
        assert isinstance(meta.get("has_placebo"), bool)


class TestC0393Adversarial:
    """c0393 adversarial traps: 위약 분류 vacuous/silent no-op 차단 (GAP-27)."""

    def test_df_readonly_not_modified(self):
        """kind=detect(분류) → df 변경 금지(SRP). meta만 기록."""
        df = pd.DataFrame({"subject_id": [1, 2], "dose_amount": [100, 0]})
        original_cols = list(df.columns)
        original_shape = df.shape
        classify_placebo_subject(df, {"has_placebo": True})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_subjects_not_set_when_detection_missing(self):
        """★ GAP-27 ③: detection(c0392) 산출 has_placebo 부재 시 silent 통과 금지
        → success=False, route_to_q=None(Q 날조 금지), placebo_subjects 미설정."""
        df = pd.DataFrame({"subject_id": [1, 2], "dose_amount": [100, 0]})
        meta = {}
        result = classify_placebo_subject(df, meta)
        assert result["success"] is False
        assert result["route_to_q"] is None
        assert meta.get("placebo_subjects") is None

    def test_non_bool_has_placebo_not_classified(self):
        """무효 has_placebo(bool 아님) → vacuous 분류 금지: success=False, placebo_subjects 미설정."""
        df = pd.DataFrame({"subject_id": [1], "dose_amount": [0]})
        meta = {"has_placebo": "yes"}
        result = classify_placebo_subject(df, meta)
        assert result["success"] is False
        assert meta.get("placebo_subjects") is None

    def test_real_placebo_subjects_not_silent_empty(self):
        """has_placebo=True + 실제 AMT=0 피험자[3,7] → placebo_subjects=[3,7](silent [] no-op 차단)."""
        df = pd.DataFrame({"subject_id": [3, 5, 7], "dose_amount": [0, 100, 0]})
        meta = {"has_placebo": True}
        result = classify_placebo_subject(df, meta)
        assert result["placebo_subjects"] == [3, 7]
        assert meta.get("placebo_subjects") == [3, 7]

    def test_no_placebo_empty_list_legit(self):
        """has_placebo=False(위약 없음) → placebo_subjects=[] 정당한 빈 분류, success(부재≠silent no-op)."""
        df = pd.DataFrame({"subject_id": [1, 2], "dose_amount": [100, 100]})
        meta = {"has_placebo": False}
        result = classify_placebo_subject(df, meta)
        assert result["success"] is True
        assert meta.get("placebo_subjects") == []

    def test_postcond_placebo_subjects_is_list(self):
        """postcond: isinstance(meta.get('placebo_subjects'), list) — 분류 산출은 항상 list."""
        meta = {"has_placebo": True}
        classify_placebo_subject(pd.DataFrame({"subject_id": [2], "dose_amount": [0]}), meta)
        assert isinstance(meta.get("placebo_subjects"), list)


class TestC0305Adversarial:
    """c0305 adversarial traps: BLQ 토큰 변종 silent-miss·날조 차단 (vacuous postcond 보강)."""

    def test_df_readonly_not_modified(self):
        """kind=detect → df 변경 금지(SRP). meta만 기록."""
        df = pd.DataFrame({"dv_value": ["5.2", "<0.1", "BLQ"]})
        original_cols = list(df.columns)
        original_shape = df.shape
        detect_blq_token_mess(df, {})
        assert list(df.columns) == original_cols
        assert df.shape == original_shape

    def test_real_variants_not_silent_empty(self):
        """실재 BLQ 변종([<0.1,BLQ,ND]) → blq_variants_found 비어있지 않음(silent [] vacuous 차단)."""
        df = pd.DataFrame({"dv_value": ["5.2", "<0.1", "BLQ", "ND", "3.1"]})
        result = detect_blq_token_mess(df, {})
        assert result["blq_variants_found"]  # non-empty
        assert set(result["blq_variants_found"]) == {"<0.1", "BLQ", "ND"}

    def test_no_blq_empty_list_legit(self):
        """순수 numeric → blq_variants_found=[] 정당한 빈 감지(날조 금지)."""
        df = pd.DataFrame({"dv_value": ["5.2", "3.1", "1.0"]})
        result = detect_blq_token_mess(df, {})
        assert result["blq_variants_found"] == []

    def test_korean_token_detected(self):
        """한글 '이하'(LLOQ 이하 표기)도 BLQ 변종으로 감지(어휘 누락 차단)."""
        df = pd.DataFrame({"dv_value": ["5.2", "정량한계 이하"]})
        result = detect_blq_token_mess(df, {})
        assert "정량한계 이하" in result["blq_variants_found"]

    def test_postcond_blq_variants_is_list(self):
        """postcond: isinstance(meta.get('blq_variants_found'), list) — 부재여도 list."""
        meta = {}
        detect_blq_token_mess(pd.DataFrame({"dv_value": ["5.2"]}), meta)
        assert isinstance(meta.get("blq_variants_found"), list)


class TestC0306Adversarial:
    """c0306 adversarial traps: BLQ 정규화 silent no-op + cross-layer 산출 컬럼 누락 차단 (GAP-15)."""

    def test_input_df_not_mutated(self):
        """transform은 df.copy() — 원본 dv_value(토큰 문자열) 불변."""
        df = pd.DataFrame({"dv_value": ["5.2", "<0.1", "BLQ"]})
        normalize_blq_token(df, {})
        assert list(df["dv_value"]) == ["5.2", "<0.1", "BLQ"]

    def test_silent_noop_caught(self):
        """토큰 미제거(no-op) 금지 → postcond(토큰 잔존 0) 충족 (verbatim postcond)."""
        df = pd.DataFrame({"dv_value": ["5.2", "<0.1", "BLQ", "ND"]})
        result = normalize_blq_token(df, {})
        df_out = result["df"]
        assert not df_out["dv_value"].astype(str).str.contains(r"<|BLQ|ND|LOD|이하", case=False, na=False).any()

    def test_blq_detected_column_produced(self):
        """cross-layer 계약(GAP-15): blq_detected가 BLQ 행을 정확히 표식(c0020 ASSIGN BLQ_FLAG 입력)."""
        df = pd.DataFrame({"dv_value": ["5.2", "<0.1", "BLQ 0.05", "3.1"]})
        result = normalize_blq_token(df, {})
        df_out = result["df"]
        assert "blq_detected" in df_out.columns
        assert list(df_out["blq_detected"]) == [False, True, True, False]

    def test_lloq_value_extracted(self):
        """cross-layer 계약(GAP-15): lloq_value가 토큰서 numeric 추출(c0021 ASSIGN LLOQ 입력). <0.1→0.1."""
        df = pd.DataFrame({"dv_value": ["<0.1", "<0.05"]})
        result = normalize_blq_token(df, {})
        df_out = result["df"]
        assert "lloq_value" in df_out.columns
        assert df_out["lloq_value"].tolist() == [0.1, 0.05]

    def test_no_blq_vacuous_pass_no_token_invented(self):
        """순수 numeric → 토큰 날조 금지, blq_detected 전부 False, dv 불변."""
        df = pd.DataFrame({"dv_value": [5.2, 3.1, 1.0]})
        result = normalize_blq_token(df, {})
        df_out = result["df"]
        assert list(df_out["blq_detected"]) == [False, False, False]
        assert list(df_out["dv_value"]) == [5.2, 3.1, 1.0]


class TestC0253Adversarial:
    """c0253 adversarial traps: A5 fail-state 라우팅 silent 오라우팅 차단 (Q01/Q15D/INVALID)."""

    def test_blq_no_policy_routes_q01(self):
        """BLQ-NO-POLICY → Q01 (Q15D/INVALID로 오라우팅 금지)."""
        result = route_blq_token(pd.DataFrame({"dv_value": [0.1]}), {"a5_state": "BLQ-NO-POLICY"})
        assert result["routing_decision"] == "Q01"
        assert result["q_code"] == "Q01"
        assert result["terminal"] == "QUARANTINE"

    def test_all_four_q01_states(self):
        """★ 불완전 매핑 차단: Q01 4-state 전부 Q01(BLQ-NO-POLICY만 매핑하고 나머지 누락 금지)."""
        for st in ("BLQ-NO-POLICY", "LLOQ-MISSING", "ABOVE-ULOQ-NO-POLICY", "REPLICATE-NO-POLICY"):
            result = route_blq_token(pd.DataFrame({"dv_value": [0.1]}), {"a5_state": st})
            assert result["routing_decision"] == "Q01", st

    def test_bioanalytical_routes_q15d_not_q01(self):
        """BIOANALYTICAL-FINAL-FLAG-MISSING → Q15D (Q01로 silent 합치기 금지; SSOT 89 strand)."""
        result = route_blq_token(pd.DataFrame({"dv_value": [0.1]}), {"a5_state": "BIOANALYTICAL-FINAL-FLAG-MISSING"})
        assert result["routing_decision"] == "Q15D"
        assert result["q_code"] == "Q15D"
        assert result["terminal"] == "QUARANTINE"

    def test_absent_routes_invalid_not_q01(self):
        """ABSENT → INVALID(q_code=None) (Q01로 silent 승격 금지; SSOT 111 strand, GAP-8)."""
        result = route_blq_token(pd.DataFrame({"dv_value": [0.1]}), {"a5_state": "ABSENT"})
        assert result["routing_decision"] == "INVALID"
        assert result["q_code"] is None
        assert result["terminal"] == "INVALID"

    def test_routing_decision_in_postcond_set(self):
        """postcond: routing_decision ∈ {Q01,Q15D,INVALID} (전 precond fail state)."""
        for st in ("BLQ-NO-POLICY", "LLOQ-MISSING", "ABOVE-ULOQ-NO-POLICY", "REPLICATE-NO-POLICY",
                   "BIOANALYTICAL-FINAL-FLAG-MISSING", "ABSENT"):
            result = route_blq_token(pd.DataFrame({"dv_value": [0.1]}), {"a5_state": st})
            assert result["routing_decision"] in ["Q01", "Q15D", "INVALID"]


# ===== slice 9 — Batch B adversarial =====

class TestC0211Adversarial:
    """c0211 adversarial traps: 토큰 silent-miss · np.bool_ · 거짓양성 차단."""

    def test_above_uloq_token_not_silently_missed(self):
        """'>100' 토큰 → 반드시 True (uloq meta 없이 숫자비교만 하는 naive 감지기 차단)."""
        df = pd.DataFrame({"dv_value": ["5.2", ">100", "4.8"]})
        meta = {}
        result = detect_above_uloq(df, meta)
        assert result["has_above_uloq"] is True
        assert result["route_to_q"] == "Q01"

    def test_flag_is_python_bool_not_numpy(self):
        """meta/result flag는 Python bool — numpy.bool_은 isinstance(.,bool)=False라 postcond 위반."""
        df = pd.DataFrame({"dv_value": [5.2, 150.0, 4.8]})
        meta = {"uloq": 100}
        result = detect_above_uloq(df, meta)
        assert result["has_above_uloq"] is True
        assert isinstance(meta["has_above_uloq"], bool)
        assert not isinstance(meta["has_above_uloq"], np.bool_)

    def test_no_uloq_no_fabrication(self):
        """clean 숫자 DV + uloq meta 부재 → False (없는 초과를 날조하지 않음)."""
        df = pd.DataFrame({"dv_value": [5.2, 3.1, 4.8]})
        meta = {}
        result = detect_above_uloq(df, meta)
        assert result["has_above_uloq"] is False
        assert result["pass"] is True

    def test_policy_present_repairs_no_q(self):
        """초과 감지 + uloq_policy 존재 → ABOVE-ULOQ(REPAIR), route None (Q01로 silent 승격 금지)."""
        df = pd.DataFrame({"dv_value": [5.2, 150.0, 4.8]})
        meta = {"uloq": 100, "uloq_policy": "M3"}
        result = detect_above_uloq(df, meta)
        assert result["has_above_uloq"] is True
        assert result["route_to_q"] is None
        assert result["pass"] is True


class TestC0212Adversarial:
    """c0212 adversarial traps: exact-dup 오탐 · NaN 제외 · np.bool_ 차단."""

    def test_exact_duplicate_not_replicate(self):
        """전체 행 일치(DUPLICATE-EXACT) → replicate 아님(False) — naive groupby(len>=2) 오탐 차단."""
        df = pd.DataFrame({"subject_id": [1, 1, 2], "time_value": [0, 0, 0], "dv_value": [5.2, 5.2, 4.8]})
        meta = {}
        result = detect_replicate_obs(df, meta)
        assert result["has_replicates"] is False
        assert result["route_to_q"] is None

    def test_distinct_dv_same_time_is_replicate(self):
        """같은 (ID,TIME) 서로 다른 DV ≥2 → 정당 replicate(True) → Q01."""
        df = pd.DataFrame({"subject_id": [1, 1], "time_value": [1, 1], "dv_value": [5.4, 5.6]})
        meta = {}
        result = detect_replicate_obs(df, meta)
        assert result["has_replicates"] is True
        assert result["route_to_q"] == "Q01"

    def test_nan_dv_not_counted(self):
        """같은 (ID,TIME)이라도 유효 DV가 1개뿐(나머지 NaN)이면 replicate 아님(False)."""
        df = pd.DataFrame({"subject_id": [1, 1], "time_value": [1, 1], "dv_value": [5.4, np.nan]})
        meta = {}
        result = detect_replicate_obs(df, meta)
        assert result["has_replicates"] is False
        assert isinstance(meta["has_replicates"], bool)
        assert not isinstance(meta["has_replicates"], np.bool_)

    def test_missing_subject_id_no_crash(self):
        """★ subject_id 컬럼 부재(runtime neutral df) → KeyError 없이 False (silent-error 0; precond 미충족 robust)."""
        df = pd.DataFrame({"time_value": [0, 1, 0], "dv_value": [0.1, 0.2, 0.3]})
        meta = {}
        result = detect_replicate_obs(df, meta)
        assert result["has_replicates"] is False
        assert result["route_to_q"] is None


class TestC0215Adversarial:
    """c0215 adversarial traps: replicate 오탐(직교) · np.bool_ 차단."""

    def test_exact_dup_detected(self):
        """전체 행 일치 → has_exact_duplicates=True (hardcoded-False 차단)."""
        df = pd.DataFrame({"subject_id": [1, 1, 2], "time_value": [0, 0, 1], "dv_value": [5.2, 5.2, 3.1]})
        meta = {}
        result = detect_duplicate_row(df, meta)
        assert result["has_exact_duplicates"] is True

    def test_replicate_not_flagged_as_exact_dup(self):
        """같은 (ID,TIME) 다른 DV(A5 replicate) → exact dup 아님(False) — c0212와 직교."""
        df = pd.DataFrame({"subject_id": [1, 1, 2], "time_value": [0, 0, 1], "dv_value": [5.2, 5.4, 3.1]})
        meta = {}
        result = detect_duplicate_row(df, meta)
        assert result["has_exact_duplicates"] is False
        assert isinstance(meta["has_exact_duplicates"], bool)
        assert not isinstance(meta["has_exact_duplicates"], np.bool_)


class TestC0216Adversarial:
    """c0216 adversarial traps: 비-ASCII 검출 · 숫자 거짓양성 · np.bool_ 차단."""

    def test_non_ascii_value_detected(self):
        """비-ASCII 값(cp949 '환자') → has_encoding_issues=True (hardcoded-False 차단)."""
        df = pd.DataFrame({"subject_id": [1, 2], "note": ["clean", "환자"]})
        meta = {}
        result = detect_encoding(df, meta)
        assert result["has_encoding_issues"] is True

    def test_numeric_only_no_false_positive(self):
        """숫자 전용 df → str 캐스팅 후 ASCII뿐 → False (숫자를 인코딩 결함으로 오탐 차단)."""
        df = pd.DataFrame({"subject_id": [1, 2], "dv_value": [5.2, 3.1]})
        meta = {}
        result = detect_encoding(df, meta)
        assert result["has_encoding_issues"] is False
        assert isinstance(meta["has_encoding_issues"], bool)
        assert not isinstance(meta["has_encoding_issues"], np.bool_)


class TestC0214Adversarial:
    """c0214 adversarial traps: 부분 누락 silent-pass · df-default · declared override."""

    def test_partial_unit_missing_routes_q10(self):
        """units dict 존재하나 numeric 컬럼 일부 단위 누락 → incomplete=False → Q10
        (naive 'units 키 존재 → complete' 차단)."""
        df = pd.DataFrame({"dv_value": [5.2, 3.1], "wt": [70, 80]})
        meta = {"units": {"dv_value": "mg/L"}}
        result = verify_unit_declaration(df, meta)
        assert result["unit_declaration_complete"] is False
        assert result["route_to_q"] == "Q10"

    def test_df_default_fail_empty_meta(self):
        """★ GAP-32: numeric 컬럼 존재 + empty meta(units 미선언) → incomplete=False → Q10
        (c0213 scope-out-pass와 정반대 df-default=fail; SSOT 'unit 사전 불완전→Q10'에 충실)."""
        df = pd.DataFrame({"dv_value": [5.2, 3.1], "wt": [70, 80]})
        meta = {}
        result = verify_unit_declaration(df, meta)
        assert result["unit_declaration_complete"] is False
        assert result["route_to_q"] == "Q10"

    def test_declared_override_wins(self):
        """선언된 meta['unit_declaration_complete']=True가 units 미선언보다 우선(declared > 점검)."""
        df = pd.DataFrame({"dv_value": [5.2, 3.1]})
        meta = {"unit_declaration_complete": True}
        result = verify_unit_declaration(df, meta)
        assert result["unit_declaration_complete"] is True
        assert result["route_to_q"] is None

    def test_no_numeric_cols_vacuous_pass(self):
        """numeric 컬럼 부재(문자열 전용) → 점검 대상 없음 → complete=True (없는 누락 날조 금지)."""
        df = pd.DataFrame({"note": ["a", "b"]})
        meta = {}
        result = verify_unit_declaration(df, meta)
        assert result["unit_declaration_complete"] is True
        assert result["pass"] is True
