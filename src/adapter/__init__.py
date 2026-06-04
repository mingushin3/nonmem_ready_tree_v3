"""src.adapter — Tier 0 auto-ingest adapter (READ-ONLY front-end, 엔진/SSOT 무수정).

실물 xlsx → 출발점 자동 detect + 이유 부착 → 57-wired 백본을 충실한 범위까지 navigate →
첫 미지원 구조에서 **이유 달고 정직 정지**(silent 추측 금지). 패치/strand 재도출 불요(M4).

ingest(xlsx_path) -> report. 아무 SSOT(spec/anchors/decision_tree/universe_sm)도, 엔진
(orchestrator/run_strand/dispatch)도 수정하지 않는다. 신규 모듈만.
"""
from .xlsx_ingester import read_workbook_structure, build_engine_df, is_lock_file
from .structure_inspector import inspect
from .column_canonicalizer import canonicalize
from .descriptor_builder import build_meta
from .navigator import navigate
from .reason_binder import bind_wired
from .gap_annotator import annotate_unwired, surface_ambiguous_wide, classify_non_decisions
from .recipe_emitter import emit_recipe

import pandas as pd

_AXES = ("A0", "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10")

__all__ = ["ingest", "read_workbook_structure", "build_engine_df", "inspect"]


def _inventory_df(structure: dict) -> pd.DataFrame:
    """honest-stop용 file-inventory df(실제 시트 메타 1행/시트). c0201/c0210의 len(df)>0 충족.

    내용은 file-property(시트명·dims·shape) — conc/dv/time 데이터 아님(날조 0). 분류는
    descriptor(n_studies/file_format)가 구동하고 df는 precond만 만족시킨다.
    """
    rows = [{"sheet_name": n, "n_rows": s["n_rows"], "n_cols": s["n_cols"],
             "shape_class": s["shape_class"]} for n, s in structure["per_sheet"].items()]
    return pd.DataFrame(rows)


def _build_reasons(findings) -> list:
    reasons = []
    for f in findings:
        if f.wired and f.target_c_id:
            b = bind_wired(f.target_c_id)
            reasons.append({"feature": f.feature, "what": f.what,
                            "structural_evidence": f.structural_evidence, "wired": True,
                            "c_id": b["c_id"], "criterion_ko": b["criterion_ko"], "ref": b["ref"]})
        else:
            reasons.append({"feature": f.feature, "what": f.what,
                            "structural_evidence": f.structural_evidence, "wired": False,
                            "gap": "GAP-37"})
    return reasons


def _build_mess_profile(findings) -> dict:
    return {f.mess_dim: True for f in findings if f.wired and f.mess_dim}


def _build_fingerprint(meta: dict, faithful_tidy: bool) -> dict:
    resolved = {ax: meta[f"a{i}_state"] for i, ax in enumerate(_AXES)
                if meta.get(f"a{i}_state") is not None}
    undetermined = [ax for ax in _AXES if ax not in resolved]
    if faithful_tidy:
        label = ("PARTIAL fingerprint — 구조 파생 축만 해소(A1/A3/A5/A10); "
                 "정책 의존 축(A0/A2/A4/A6/A7/A8/A9)은 분석자 선언 필요. over-read 금지.")
    else:
        label = ("PARTIAL file-property fingerprint (A1/A10 한정); "
                 "conc 의존 축 전부 undetermined — honest-stop. 날조 0. over-read 금지.")
    return {"resolved": resolved, "undetermined": undetermined, "label": label}


def _sheets_summary(structure: dict) -> list:
    return [{"name": n, "n_rows": s["n_rows"], "n_cols": s["n_cols"],
             "n_merged": s["n_merged"], "shape_class": s["shape_class"]}
            for n, s in structure["per_sheet"].items()]


def _serializable_record(rec: dict) -> dict:
    """run_strand record에서 df(대용량·비직렬)를 shape로 치환. meta는 엔진 산출 그대로 보존."""
    out = dict(rec)
    df = out.pop("df", None)
    out["df_shape"] = None if df is None else list(df.shape)
    return out


def ingest(xlsx_path: str) -> dict:
    """실물 xlsx → Tier 0 report(detect·이유·진입·dispatch·정지점)."""
    structure = read_workbook_structure(xlsx_path)
    df_raw, build = build_engine_df(xlsx_path, structure)
    findings = inspect(structure, df_raw, build.get("raw_columns"))
    reasons = _build_reasons(findings)
    unwired_notes = annotate_unwired(findings)
    decision_required = surface_ambiguous_wide(structure)
    meta = build_meta(findings, structure)

    if build["faithful"] and df_raw is not None:
        df, canon = canonicalize(df_raw, structure)
        dispatched = navigate(df, meta, faithful_tidy=True)
        faithful_tidy = True
        rec = dispatched["run_strand_record"]
        stop = {
            "at": rec["boundary_at"] or "navigable-band-complete",
            "structural_evidence": f"chosen_sheet={build['chosen_sheet']!r}, canonical={canon['mapped']}",
            "reason": ("navigable DETECT 밴드 완주 — 정책 의존 축은 분석자 선언 대기"
                       if rec["boundary_at"] is None else f"slice boundary at {rec['boundary_at']}"),
            "gap": None,
        }
    else:
        inv = _inventory_df(structure)
        dispatched = navigate(inv, meta, faithful_tidy=False)
        faithful_tidy = False
        unwired_feats = [f.feature for f in findings if not f.wired]
        stop = {
            "at": "structure-recognition",
            "structural_evidence": f"sheet_shapes={build['sheet_shapes']}",
            "reason": ("어느 시트도 tidy-long으로 충실 환원 불가 → conc 의존 detector 미dispatch "
                       f"(미배선 구조: {unwired_feats})"),
            "gap": "GAP-37",
        }

    fingerprint = _build_fingerprint(dispatched["run_strand_record"]["meta"], faithful_tidy)
    return {
        "source": structure["path"],
        "sheets": _sheets_summary(structure),
        "mess_profile": _build_mess_profile(findings),
        "axis_fingerprint": fingerprint,
        "entry_node": "N0",
        "reasons": reasons,
        "unwired_notes": unwired_notes,
        "decision_required": decision_required,
        "non_decisions": classify_non_decisions(structure),
        "dispatched": {"c_sequence": dispatched["c_sequence"],
                       "run_strand_record": _serializable_record(dispatched["run_strand_record"])},
        "stop": stop,
        "recipe": emit_recipe(structure, findings),
    }
