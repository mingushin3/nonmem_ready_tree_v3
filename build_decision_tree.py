"""Phase 7 — spec/decision_tree.json 최초 조립 (step 1~2.5 골격). DETERMINISTIC SSOT 파생.

PROMPTS Phase 7 step 1(골격 채택)→2(c 부착)→2.5(D-S4 conditional-edge)→2.6(결정 B terminal_routing)를 수행한다.
57 wired c의 can_route_to_q에서 conditional edge(Q) + postcond routing_decision에서 terminal edge(INVALID)를
SSOT(strands.json 측정)로 정적 주입. Phase 7 승인 결정 A(c0252/c0204 INFUSION→Q04 spec-change)·B(terminal_routing) 반영.
run_strand 무변경(① 비의존). suffix-tree 다발 압축(step 2 하류·step 5)은 범위 밖.

SSOT 입력(read-only):
  - anchors.json        : N0–N7(8) · A0–A10(11축 101 state) · terminals(5) · q_codes(19). 식별자 정본.
  - spec/c_units.json   : 122 c 정의. 본 골격은 src/orchestrator.py REGISTRY의 wired 57만 node로.
  - spec/q_codes.json   : Q trigger_condition · recover_to_c_id · routing_cost(경로비용 비가산, 메타).
  - spec/strands.json   : 5000 best-strand. 각 conditional edge의 strand_count·scope-out 정산용(생성 근거 falsifiable).

생성 근거(falsifiable, cite-verify 완료):
  - cost=Σc.cost (run_strand; Q.routing_cost 비가산). 5000 strand 전부 total_cost==Σc.cost 선검증 통과.
  - Q partition(두 lens 일치): EXERCISED 13(wired ROUTE c can_route_to_q) / STATIC 2(Q05 c0201·Q10 c0214, nonroute) /
    UNREACHED 4(Q15A/B/C/X, wired c edge 0). PURE 3228 strand(결정 A c0252→Q04 168 + 결정 C c0253→Q15D 89 편입).
  - 결정 A(GAP-31/5 RESOLVED): c0252/c0204에 INFUSION-STOP-RESTART→Q04 정합 → conditional edge +2.
  - 결정 B(GAP-8/12 RESOLVED): terminal_routing 3 edge(c0252/c0253/c0256→INVALID, 315 strand)=postcond INVALID ∩ 측정.
  - 잔존 SCOPE-OUT 0: c0253→Q15D(89)는 결정 C(GAP-28 RESOLVE)로 can_route_to_q 편입 → pure. c0251→INVALID(선언·0 strand)=terminal_declared_unexercised.

산출: spec/decision_tree.json. 검증: tests/test_decision_tree.py.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ANCHORS = json.loads((ROOT / "anchors.json").read_text(encoding="utf-8"))
CUNITS = json.loads((ROOT / "spec" / "c_units.json").read_text(encoding="utf-8"))
QCODES = json.loads((ROOT / "spec" / "q_codes.json").read_text(encoding="utf-8"))
STRANDS = json.loads((ROOT / "spec" / "strands.json").read_text(encoding="utf-8"))

BYID = {c["c_id"]: c for c in CUNITS}
QBYID = {q["q_id"]: q for q in QCODES}
COST = {c["c_id"]: c["cost"] for c in CUNITS}

# ── wired REGISTRY (src/orchestrator.py 와 동기. test_decision_tree.py가 REGISTRY==WIRED 강제) ──
WIRED = [
    # slice 1 MERGED_CELL / slice 2-3 TIME·TIMEZONE / slice 4 COVARIATE / slice 5 PLACEBO / slice 6 BLQ
    "c0340", "c0341", "c0203", "c0213", "c0251", "c0310", "c0311", "c0314", "c0315",
    "c0312", "c0313", "c0380", "c0381", "c0207", "c0121", "c0392", "c0393",
    "c0305", "c0306", "c0205", "c0253", "c0020", "c0021",
    # slice 7a backbone: axis A0–A10 + L-1→L-2 NONMEM 컬럼 + covariate
    "c0200", "c0201", "c0202", "c0204", "c0206", "c0208", "c0209", "c0210",
    "c0001", "c0010", "c0011", "c0012", "c0013", "c0014", "c0015", "c0016", "c0017", "c0018", "c0019",
    "c0022", "c0023", "c0140", "c0141",
    # slice 8 Batch A ROUTE / slice 9 Batch B DETECT·VERIFY
    "c0250", "c0252", "c0254", "c0255", "c0256", "c0257",
    "c0211", "c0212", "c0214", "c0215", "c0216",
]
WIRED_SET = set(WIRED)
ROUTE_C = {c for c in WIRED if BYID[c].get("kind") == "route"}

# ── 결정 B(terminal_routing): ROUTE c가 postcond routing_decision에 선언 가능한 비-Q process terminal ──
PROC_FAIL_TERMINALS = ("INVALID", "UNSUPPORTED")
_PC_LITERAL = re.compile(r"'([A-Z0-9-]+)'")        # postcond 리터럴 토큰(결정론적 파싱)


def _postcond_targets(cid):
    return set(_PC_LITERAL.findall(BYID[cid].get("postcondition_predicate", "") or ""))

# ── Q partition (wired c can_route_to_q 기준; route 우선) ──
Q_INCOMING = {q: [] for q in ANCHORS["q_codes"]}          # q -> [wired c that declare it]
for cid in WIRED:
    for q in BYID[cid].get("can_route_to_q", []) or []:
        if q in Q_INCOMING:
            Q_INCOMING[q].append(cid)
Q_EXERCISED = {q for q, cs in Q_INCOMING.items() if any(BYID[c].get("kind") == "route" for c in cs)}
Q_STATIC = {q for q, cs in Q_INCOMING.items() if cs and q not in Q_EXERCISED}
Q_UNREACHED = {q for q, cs in Q_INCOMING.items() if not cs}


def q_status(q):
    if q in Q_EXERCISED:
        return "exercised"
    if q in Q_STATIC:
        return "static-no-strand"
    return "unreached"


# ── strands 기반 정산: (last-c, q_code) pure 실현 count + scope-out edge ──
PURE_COUNT = {}     # (cid, q) -> n  (q in cid.can_route_to_q, cid wired route)
SCOPEOUT = {}       # (cid, target) -> n  (q NOT in can_route_to_q OR non-Q terminal; deferred)
for x in STRANDS:
    lc = (x["c_sequence"] or [None])[-1]
    if lc not in ROUTE_C:
        continue
    crq = BYID[lc].get("can_route_to_q", []) or []
    q, term = x.get("q_code"), x.get("terminal")
    if q and q in crq:
        PURE_COUNT[(lc, q)] = PURE_COUNT.get((lc, q), 0) + 1
    elif q:
        SCOPEOUT[(lc, q, "QUARANTINE")] = SCOPEOUT.get((lc, q, "QUARANTINE"), 0) + 1
    elif term and term != "QUARANTINE":
        SCOPEOUT[(lc, term, term)] = SCOPEOUT.get((lc, term, term), 0) + 1

# SCOPEOUT을 Q-scope(deferred.scope_out_edges)와 terminal-scope(결정 B terminal_routing)로 분리
SCOPE_Q = {(cid, t): n for (cid, t, kind), n in SCOPEOUT.items() if kind == "QUARANTINE"}
SCOPE_TERM = {(cid, t): n for (cid, t, kind), n in SCOPEOUT.items() if kind != "QUARANTINE"}

# ═══════════════ step 1: backbone 채택 (anchors 그대로) ═══════════════
nodes = []
for nid, desc in ANCHORS["nodes"].items():               # N0–N7 process gate
    nodes.append({"id": nid, "type": "branch", "role": "process_gate",
                  "label": desc, "ref": f"anchors.nodes.{nid}"})
for aid, states in ANCHORS["axes"].items():              # A0–A10 axis (state cell)
    nodes.append({"id": aid, "type": "conditional", "role": "axis",
                  "states": states, "state_count": len(states), "ref": f"anchors.axes.{aid}"})
for t in ANCHORS["terminals"]:                           # 5 process terminal
    nodes.append({"id": t, "type": "terminal", "terminal_class": "process",
                  "ref": f"anchors.terminals.{t}"})
for qid, qmeta in ANCHORS["q_codes"].items():            # 19 Q terminal
    qd = QBYID.get(qid, {})
    nodes.append({"id": qid, "type": "terminal", "terminal_class": "q_code",
                  "label": qmeta.get("name"), "trigger": qd.get("trigger_condition"),
                  "recover_to_c_id": qd.get("recover_to_c_id"),
                  "routing_cost": qd.get("routing_cost"), "routing_cost_added_to_path": False,
                  "q_status": q_status(qid), "incoming_wired_c": Q_INCOMING[qid],
                  "ref": f"anchors.q_codes.{qid}"})

# ═══════════════ step 2: c 부착 (skeleton_hook) ═══════════════
ANCHOR_TOK = re.compile(r"\bA(?:10|[0-9])\b|\bN[0-7]\b")
MESS_TOK = re.compile(r"mess:[A-Z_]+")
edges = []                                               # 구조 attach edge
for cid in WIRED:
    c = BYID[cid]
    hook = c.get("skeleton_hook", "") or ""
    nodes.append({"id": cid, "type": c.get("kind"), "kind": c.get("kind"),
                  "layer_pair": c.get("layer_pair"), "cost": COST[cid],
                  "srp_intent": c.get("srp_intent"), "skeleton_hook": hook,
                  "requires_detection_by": c.get("requires_detection_by"),
                  "ref": f"c_units.{cid}"})
    anchors_hit = sorted(set(ANCHOR_TOK.findall(hook)))
    for a in anchors_hit:
        edges.append({"from": cid, "to": a, "type": "attach", "via": "skeleton_hook"})
    if not anchors_hit and c.get("layer_pair") == "L-4->L-5":
        mess = MESS_TOK.findall(hook)
        edges.append({"from": cid, "to": "L-4->L-5", "type": "attach", "via": "layer_stage",
                      "note": "mess 전처리 stage(D-S3); 다발 부착은 step2 압축(범위 밖)",
                      "mess": mess[0] if mess else None})

# ═══════════════ step 2.5: D-S4 conditional-edge 재구성 (순수 주입) ═══════════════
conditional_routing = []
GAP_BY_C = {  # 순수-edge GAP 출처 cite (해당 c가 가진 can_route_to_q 선언의 설계근거)
    # 결정 B로 GAP-8(c0253→INVALID)·GAP-12(c0256→INVALID) RESOLVED → c0205/c0209 cite에서 제거. 결정 C로 GAP-28(c0253→Q15D) RESOLVE(can_route_to_q 편입; provenance cite는 GAP-10/26 선례처럼 유지).
    "c0205": ["GAP-28"], "c0206": ["GAP-10"],
    "c0251": ["GAP-26"], "c0253": ["GAP-28"], "c0306": ["GAP-28"],
    "c0019": ["GAP-26"], "c0311": ["GAP-26"], "c0315": ["GAP-26"], "c0203": ["GAP-26"],
}
for cid in WIRED:
    c = BYID[cid]
    kind = c.get("kind")
    seen = set()
    for q in c.get("can_route_to_q", []) or []:
        if q in seen:
            continue
        seen.add(q)
        realizers = [rc for rc in Q_INCOMING[q] if BYID[rc].get("kind") == "route"]
        conditional_routing.append({
            "from": cid, "to": q, "type": "conditional", "source": "can_route_to_q",
            "from_kind": kind, "q_status": q_status(q),
            "realizing_route_c": realizers,
            "strand_count": PURE_COUNT.get((cid, q), 0),
            "gap": GAP_BY_C.get(cid, []),
        })
    # verify_visualization.fail_route_to (Q만; terminal/복합은 deferred)
    vv = c.get("verify_visualization") or {}
    frt = vv.get("fail_route_to")
    if frt and frt in ANCHORS["q_codes"] and frt not in seen:
        conditional_routing.append({
            "from": cid, "to": frt, "type": "conditional", "source": "fail_route_to",
            "from_kind": kind, "q_status": q_status(frt),
            "realizing_route_c": [rc for rc in Q_INCOMING[frt] if BYID[rc].get("kind") == "route"],
            "strand_count": PURE_COUNT.get((cid, frt), 0), "gap": GAP_BY_C.get(cid, []),
        })

# ═══════════════ step 2.6: 결정 B — terminal_routing (process-terminal edge, Q-edge와 분리) ═══════════════
# 각 wired ROUTE c의 postcond routing_decision에서 process-fail-terminal(INVALID/UNSUPPORTED)을 도출(SSOT),
# strands 측정(SCOPE_TERM)으로 strand_count. 측정 0(선언만; 예: c0251→INVALID)은 terminal_declared_unexercised에
# falsifiable 기록(silent drop 금지). conditional_routing(Q-only, source=can_route_to_q)과 분리해 의미 보존.
terminal_routing = []
terminal_declared_unexercised = []
for cid in WIRED:
    if BYID[cid].get("kind") != "route":
        continue
    for term in sorted(_postcond_targets(cid) & set(PROC_FAIL_TERMINALS)):
        n = SCOPE_TERM.get((cid, term), 0)
        if n > 0:
            terminal_routing.append({
                "from": cid, "to": term, "type": "terminal", "terminal_class": "process",
                "source": "postcond_routing_decision", "strand_count": n, "gap": [],
            })
        else:
            terminal_declared_unexercised.append({"from": cid, "to": term, "strand_count": 0})

# ═══════════════ deferred: spec 결정 / scope-out / unreached ═══════════════
deferred = {
    "spec_decisions": [
        # GAP-5(c0204)·GAP-31(c0252): Phase 7 결정 A로 RESOLVED — c0252/c0204 can_route_to_q+postcond에
        #   INFUSION-STOP-RESTART→Q04 정합(cite universe_sm §3 A4 '無 Q04', q_codes Q04.trigger). provenance_gaps 참조.
        {"id": "GAP-13", "c": "c0210", "missing_edge": "A10(NON-TABULAR→UNSUPPORTED / CORRUPTED→INVALID)",
         "reason": "fail_route_to=UNSUPPORTED/INVALID(terminal, Q 아님) + A10 실행 위치(front vs chain 끝) 결정 필요."},
        {"id": "GAP-27B", "c": "c0313", "missing_edge": "FORMAT↔TIMEZONE 정렬 상호작용 노드화",
         "reason": "정규화 순서 상호작용의 tree 표현은 step2 bundle/설계 결정 대기."},
        {"id": "c0040-placeholder", "c": "c0040", "missing_edge": "(미배선)",
         "reason": "REGISTRY 미배선 c. node 부재 → 부착·라우팅 보류."},
    ],
    "scope_out_edges": [  # 결정 C(GAP-28)로 c0253→Q15D can_route_to_q 편입 → scope-out 0(빈 배열). 결정 A c0252→Q04·결정 B INVALID 3개 terminal_routing.
        {"from": cid, "to": q, "terminal": "QUARANTINE", "strand_count": n,
         "gap": {("c0253", "Q15D"): "GAP-28"}.get((cid, q), "?")}
        for (cid, q), n in sorted(SCOPE_Q.items())
    ],
    "unreached_q": [
        {"q": q, "trigger": QBYID.get(q, {}).get("trigger_condition"),
         "recover_to_c_id": QBYID.get(q, {}).get("recover_to_c_id"),
         "status": "isolated-deferred (wired c edge 0; source c 미배선)",
         "note": "정적 placeholder. 검증 strand 없음. source c 배선 시 edge 생성(후속)."}
        for q in sorted(Q_UNREACHED)
    ],
}

# ═══════════════ stats (GAP-25 실 노드수 재측정 포함) ═══════════════
n_axis_states = sum(len(s) for s in ANCHORS["axes"].values())
collapsed_display = len(ANCHORS["nodes"]) + len(ANCHORS["axes"]) + len(ANCHORS["terminals"]) \
    + len(ANCHORS["q_codes"]) + len(WIRED)              # axis collapsed(11), c 가시(bundle=[] 이므로 57)
expanded_worst = len(ANCHORS["nodes"]) + n_axis_states + len(ANCHORS["terminals"]) \
    + len(ANCHORS["q_codes"]) + len(WIRED)              # axis 펼침(101 state)
stats = {
    "nodes_total": len(nodes), "backbone_process_nodes": len(ANCHORS["nodes"]),
    "axis_nodes": len(ANCHORS["axes"]), "axis_states_total": n_axis_states,
    "process_terminals": len(ANCHORS["terminals"]), "q_terminals": len(ANCHORS["q_codes"]),
    "c_nodes": len(WIRED), "attach_edges": len(edges), "conditional_edges": len(conditional_routing),
    "terminal_edges": len(terminal_routing),
    "terminal_strands": sum(e["strand_count"] for e in terminal_routing),
    "terminal_declared_unexercised": terminal_declared_unexercised,
    "bundles": 0,
    "q_partition": {"exercised": sorted(Q_EXERCISED), "static_no_strand": sorted(Q_STATIC),
                    "unreached": sorted(Q_UNREACHED)},
    "pure_realized_strands": sum(PURE_COUNT.values()),
    "scope_out_edges": len(SCOPE_Q), "scope_out_strands": sum(SCOPE_Q.values()),
    "gap25_remeasure": {  # 실 axis-state 기준. ms 타이밍은 Phase 8 라이브.
        "collapsed_display_nodes": collapsed_display, "expanded_worst_nodes": expanded_worst,
        "replaces_synthetic": "spike 248/236", "gate_10s": "PASS(노드 ~190 ≪ 5000; dagre sub-second)"},
}

tree = {
    "schema_version": "0.2-phase7-step1-2.6-decisionABC",
    "generated_by": "build_decision_tree.py (DETERMINISTIC; 재실행 시 동일)",
    "scope": "step 1~2.6 골격 + Phase 7 결정 A(c0252/c0204 INFUSION-STOP-RESTART→Q04 spec-change)·결정 B(terminal_routing INVALID). bundles·재배선(①) 제외.",
    "provenance": {
        "backbone": "anchors.json (universe_sm §2–§5 N0–N7·A0–A10·terminals·q_codes)",
        "c_nodes": "spec/c_units.json ∩ src/orchestrator.py REGISTRY (wired 57)",
        "conditional_routing": "c.can_route_to_q + verify_visualization.fail_route_to (D-S4, PROMPTS step 2.5)",
        "terminal_routing": "wired ROUTE c.postcond routing_decision의 process-terminal(INVALID) ∩ strands 측정 (결정 B)",
        "q_meta": "spec/q_codes.json (trigger/recover/routing_cost)",
        "strand_counts": "spec/strands.json 5000 (last-c·q_code 실측; cost=Σc.cost)",
    },
    "backbone": {"process_nodes": list(ANCHORS["nodes"].keys()), "axes": ANCHORS["axes"],
                 "terminals_process": ANCHORS["terminals"], "terminals_q": list(ANCHORS["q_codes"].keys())},
    "nodes": nodes,
    "edges": edges,
    "conditional_routing": conditional_routing,
    "terminal_routing": terminal_routing,
    "bundles": [],
    "deferred": deferred,
    "stats": stats,
}

if __name__ == "__main__":
    out = ROOT / "spec" / "decision_tree.json"
    out.write_text(json.dumps(tree, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"WROTE {out}")
    print(f"  nodes={stats['nodes_total']} (backbone {len(ANCHORS['nodes'])}N + {len(ANCHORS['axes'])}axis"
          f"[{n_axis_states} states] + {len(ANCHORS['terminals'])}+{len(ANCHORS['q_codes'])} terminal + {len(WIRED)}c)")
    print(f"  conditional_edges={stats['conditional_edges']} | terminal_edges={stats['terminal_edges']} | attach_edges={stats['attach_edges']} | bundles=0")
    print(f"  Q exercised={len(Q_EXERCISED)} static={len(Q_STATIC)} unreached={len(Q_UNREACHED)}")
    print(f"  pure_realized_strands={stats['pure_realized_strands']} | scope_out edges={len(SCOPE_Q)}"
          f" strands={sum(SCOPE_Q.values())} | terminal_routing={stats['terminal_edges']}({stats['terminal_strands']})")
    print(f"  GAP-25 collapsed_display={collapsed_display} expanded_worst={expanded_worst} (≪5000, gate PASS)")
