"""Fixture generator for c0200 (A0 analysis-intent) and c0204 (A4 dose-completeness).

Declarative oracle: each case lists (name, meta, expected) with expected values
HAND-AUTHORED (independent of the c-unit implementation). The input df is a small
constant table (classification is meta-driven; df only satisfies len(df) > 0 and,
for c0204, supplies dose-row presence for the default path).

Run:  python generate_c0200_c0204_fixtures.py
Emits fixtures/intermediate/c0200/<case>_{input.csv,meta.json,expected.json}
and    fixtures/intermediate/c0204/<case>_{input.csv,meta.json,expected.json}
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FIX = ROOT / "fixtures" / "intermediate"

# --- constant input tables -------------------------------------------------

C0200_CSV = "subject_id,time_value,dv_value\n1,0.0,\n1,1.0,5.2\n"

C0204_DOSES_CSV = (
    "subject_id,EVID,AMT,time_value,dv_value\n"
    "1,1,100.0,0.0,\n"
    "1,0,,1.0,5.2\n"
    "1,0,,2.0,3.1\n"
)
C0204_NODOSE_CSV = (
    "subject_id,EVID,AMT,time_value,dv_value\n"
    "1,0,,1.0,5.2\n"
    "1,0,,2.0,3.1\n"
)


def _ok(state_key, state):
    return {state_key: state, "pass": True, "route_to_q": None}


def _q(state_key, state, q):
    return {state_key: state, "pass": False, "route_to_q": q}


# --- c0200: (name, meta, expected) ----------------------------------------
# a0_state postcond set: AIC-MISSING/PK/POPPK/PKPD/ER/DDI/PEDS/SPECIAL/CUSTOM
C0200 = [
    # 8 happy pass (one per non-missing state)
    ("happy_aic_pk", {"analysis_intent": "AIC-PK"}, _ok("a0_state", "AIC-PK")),
    ("happy_aic_poppk", {"analysis_intent": "AIC-POPPK"}, _ok("a0_state", "AIC-POPPK")),
    ("happy_aic_pkpd", {"analysis_intent": "AIC-PKPD", "endpoint_data_type": "CONTINUOUS_PD"}, _ok("a0_state", "AIC-PKPD")),
    ("happy_aic_er", {"analysis_intent": "AIC-ER", "endpoint_data_type": "EXPOSURE_METRIC"}, _ok("a0_state", "AIC-ER")),
    ("happy_aic_ddi", {"analysis_intent": "AIC-DDI"}, _ok("a0_state", "AIC-DDI")),
    ("happy_aic_peds", {"analysis_intent": "AIC-PEDS"}, _ok("a0_state", "AIC-PEDS")),
    ("happy_aic_special", {"analysis_intent": "AIC-SPECIAL"}, _ok("a0_state", "AIC-SPECIAL")),
    ("happy_aic_custom", {"analysis_intent": "AIC-CUSTOM", "policy_document": "protocol_v2.pdf"}, _ok("a0_state", "AIC-CUSTOM")),
    # fail happy (AIC-MISSING)
    ("happy_aic_missing", {}, _q("a0_state", "AIC-MISSING", "Q11")),
    # edge: endpoint-only fallback per before_after example
    ("edge_endpoint_fallback", {"endpoint_data_type": "PK_CONCENTRATION"}, _ok("a0_state", "AIC-PK")),
    # category / misclassification traps
    ("trap_pkpd_missing_endpoint", {"analysis_intent": "AIC-PKPD"}, _q("a0_state", "AIC-MISSING", "Q11")),
    ("trap_er_out_of_scope_endpoint", {"analysis_intent": "AIC-ER", "endpoint_data_type": "CATEGORICAL_PD"}, _q("a0_state", "AIC-MISSING", "Q11")),
    ("trap_custom_no_document", {"analysis_intent": "AIC-CUSTOM"}, _q("a0_state", "AIC-MISSING", "Q11")),
    ("trap_endpoint_without_intent", {"endpoint_data_type": "CONTINUOUS_PD"}, _ok("a0_state", "AIC-PKPD")),
    ("trap_unrecognized_intent", {"analysis_intent": "AIC-FOO"}, _q("a0_state", "AIC-MISSING", "Q11")),
    ("trap_whitespace_case", {"analysis_intent": " aic-pk "}, _ok("a0_state", "AIC-PK")),
    # MANDATORY: blank intent looks declared but is empty -> AIC-MISSING -> Q11
    ("trap_aic_missing_q11_routing", {"analysis_intent": "   "}, _q("a0_state", "AIC-MISSING", "Q11")),
]

# --- c0204: (name, meta, expected, csv) -----------------------------------
# a4_state postcond set: 13 states. route_to_q in {None, Q08, Q14} only.
D = C0204_DOSES_CSV
N = C0204_NODOSE_CSV
C0204 = [
    # 13 happy (one per a4_state)
    ("happy_complete", {}, _ok("a4_state", "COMPLETE"), D),
    ("happy_weight_based", {"dose_regimen": "weight-based"}, _ok("a4_state", "WEIGHT-BASED"), D),
    ("happy_bsa_based", {"dose_regimen": "bsa-based"}, _ok("a4_state", "BSA-BASED"), D),
    ("happy_planned_fallback", {"dose_regimen": "planned-fallback"}, _ok("a4_state", "PLANNED-FALLBACK"), D),
    ("happy_addl_ii", {"dose_regimen": "addl-ii"}, _ok("a4_state", "ADDL-II"), D),
    ("happy_addl_actual_conflict", {"has_addl_actual_conflict": True}, _q("a4_state", "ADDL-ACTUAL-CONFLICT", "Q14"), D),
    ("happy_titration_adaptive", {"dose_regimen": "titration", "dose_policy_present": True}, _ok("a4_state", "TITRATION-ADAPTIVE"), D),
    ("happy_loading_maintenance", {"dose_regimen": "loading-maintenance", "dose_policy_present": True}, _ok("a4_state", "LOADING-MAINTENANCE"), D),
    ("happy_infusion_stop_restart", {"dose_regimen": "infusion-stop-restart"}, _ok("a4_state", "INFUSION-STOP-RESTART"), D),
    ("happy_partial_recovery", {"dose_regimen": "partial-recovery"}, _ok("a4_state", "PARTIAL-RECOVERY"), D),
    ("happy_combination", {"dose_regimen": "combination"}, _ok("a4_state", "COMBINATION"), D),
    ("happy_missing_no_policy", {"dose_regimen": "missing"}, _q("a4_state", "MISSING-NO-POLICY", "Q08"), N),
    ("happy_unrecoverable", {"dose_regimen": "unrecoverable"}, _ok("a4_state", "UNRECOVERABLE"), D),
    # edge
    ("edge_minimal", {}, _ok("a4_state", "COMPLETE"), "subject_id,EVID,AMT,time_value,dv_value\n1,1,50.0,0.0,\n"),
    # traps
    ("trap_q08_routing", {"dose_regimen": "missing"}, _q("a4_state", "MISSING-NO-POLICY", "Q08"), N),
    ("trap_q14_routing", {"has_addl_actual_conflict": True}, _q("a4_state", "ADDL-ACTUAL-CONFLICT", "Q14"), D),
    ("trap_addl_ii_vs_titration", {"dose_regimen": "titration", "dose_policy_present": True}, _ok("a4_state", "TITRATION-ADAPTIVE"), D),
    ("trap_conflict_priority", {"has_addl_actual_conflict": True, "dose_regimen": "addl-ii"}, _q("a4_state", "ADDL-ACTUAL-CONFLICT", "Q14"), D),
    ("trap_titration_no_policy_q08", {"dose_regimen": "titration", "dose_policy_present": False}, _q("a4_state", "TITRATION-ADAPTIVE", "Q08"), D),
    ("trap_loading_no_policy_q08", {"dose_regimen": "loading-maintenance"}, _q("a4_state", "LOADING-MAINTENANCE", "Q08"), D),
    ("trap_infusion_no_q", {"dose_regimen": "infusion-stop-restart"}, _ok("a4_state", "INFUSION-STOP-RESTART"), D),
    ("trap_unrecoverable_no_q", {"dose_regimen": "unrecoverable"}, _ok("a4_state", "UNRECOVERABLE"), D),
    ("trap_no_doses_not_complete", {}, _q("a4_state", "MISSING-NO-POLICY", "Q08"), N),
]


def _write(cdir, name, csv, meta, expected):
    cdir.mkdir(parents=True, exist_ok=True)
    (cdir / f"{name}_input.csv").write_text(csv, encoding="utf-8")
    (cdir / f"{name}_meta.json").write_text(json.dumps(meta), encoding="utf-8")
    (cdir / f"{name}_expected.json").write_text(json.dumps(expected), encoding="utf-8")


def main():
    c0200_dir = FIX / "c0200"
    for name, meta, expected in C0200:
        _write(c0200_dir, name, C0200_CSV, meta, expected)
    c0204_dir = FIX / "c0204"
    for name, meta, expected, csv in C0204:
        _write(c0204_dir, name, csv, meta, expected)
    print(f"c0200: {len(C0200)} cases -> {c0200_dir}")
    print(f"c0204: {len(C0204)} cases -> {c0204_dir}")


if __name__ == "__main__":
    main()
