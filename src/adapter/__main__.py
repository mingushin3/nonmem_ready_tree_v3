"""python -m src.adapter <xlsx_path> — Tier 0 adapter를 실물 파일에 실행(read-only 보고)."""
import json
import sys

from . import ingest


def _summarize(report: dict) -> str:
    fp = report["axis_fingerprint"]
    disp = report["dispatched"]
    lines = [
        f"source: {report['source']}",
        f"sheets: {[(s['name'], s['shape_class']) for s in report['sheets']]}",
        f"mess_profile(wired): {report['mess_profile']}",
        f"axis_fingerprint.resolved: {fp['resolved']}",
        f"axis_fingerprint.undetermined: {fp['undetermined']}",
        f"label: {fp['label']}",
        f"entry_node: {report['entry_node']}",
        f"dispatched.c_sequence: {disp['c_sequence']}",
        f"stop.at: {report['stop']['at']}  reason: {report['stop']['reason']}",
        f"reasons: {len(report['reasons'])}  decision_required: {len(report['decision_required'])}"
        f"  non_decisions: {len(report['non_decisions'])}",
        f"recipe.work_units: {[w['wu'] + ':' + w['name'] for w in report['recipe']['work_units']]}",
        f"recipe.checklist: {[it['id'] for it in report['recipe']['checklist']]}",
    ]
    return "\n".join(lines)


def _recipe_view(report: dict) -> str:
    """파일별 실행 recipe + 모델러 체크리스트 사람가독 printout(WU1 인벤토리 deliverable)."""
    rec = report["recipe"]
    lines = [
        f"# Tier 0 recipe — {rec['source']}",
        f"# {rec['commit_baseline']}",
        f"# status: {rec['status']} — {rec['note']}",
        f"# target: {rec['target']}",
        "",
        "## work units (실행 순서 — 기술일 뿐, adapter 미실행):",
    ]
    if not rec["work_units"]:
        lines.append("  (감지된 미지원 구조 없음 — WU recipe 불요)")
    for w in rec["work_units"]:
        lines.append(f"  [{w['wu']}] {w['name']}  action={w['action']}  ({w['status']})")
        if w.get("sheets"):
            lines.append(f"        sheets: {w['sheets']}")
        if w.get("targets"):
            lines.append(f"        remove: {w['targets']}")
        if "bw_source" in w:
            lines.append(f"        bw_source: {w['bw_source']}")
        lines.append(f"        note: {w['note']}")
        for v in w.get("verify", []):
            lines.append(f"        verify ▸ {v}")
    lines.append("")
    lines.append("## 모델러 결정 체크리스트 (flag만 — 네가 정하라):")
    if not rec["checklist"]:
        lines.append("  (해당 결정 신호 없음)")
    for it in rec["checklist"]:
        ev = f"  evidence={it['evidence']}" if it.get("evidence") else ""
        lines.append(f"  [ ] {it['id']}: {it['flag']}{ev}")
    nd = report.get("non_decisions", [])
    if nd:
        lines.append("")
        lines.append("## 비결정(non-decision) — 결정 라우팅 안 함:")
        for n in nd:
            lines.append(f"  · {n['kind']} @ {n['sheet']}: {n['rationale']}")
            lines.append(f"    evidence={n['evidence']}  ref={n['ref']}")
    return "\n".join(lines)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if not argv:
        print("usage: python -m src.adapter <xlsx_path> [--json | --recipe]", file=sys.stderr)
        return 2
    report = ingest(argv[0])
    if "--json" in argv:
        print(json.dumps(report, ensure_ascii=False, indent=2, default=str))
    elif "--recipe" in argv:
        print(_recipe_view(report))
    else:
        print(_summarize(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
