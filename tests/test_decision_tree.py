"""Phase 7 — spec/decision_tree.json 골격(step 1~2.6) 정적 검증.

run_strand 무변경: decision_tree.json만 로드해 SSOT(anchors/c_units/q_codes/strands)와 정합 검증한다.
- 골격 정합(G1): backbone 식별자 == anchors 전수, 임의/초과 식별자 0.
- c node == orchestrator REGISTRY(wired 57).
- D-S4(step 2.5): 모든 배선 c.can_route_to_q → conditional edge 존재 + 고립 Q-terminal 0(exercised 한정).
- 결정 A(GAP-31/5 RESOLVED): c0252/c0204 INFUSION-STOP-RESTART→Q04 conditional edge 주입(pure 3139).
- 결정 B(GAP-8/12 RESOLVED): terminal_routing(c0252/c0253/c0256→INVALID 315) — Q-edge와 분리, INVALID 도달성.
- 결정 C(GAP-28 RESOLVED): c0253.can_route_to_q +Q15D → c0253→Q15D conditional edge 편입(89 pure, 누적 3228).
- 압축 불변성(① 비의존): 5000 strand total_cost==Σc.cost(cost) + pure(last-c∈ROUTE·q∈can_route_to_q) edge 재현(terminal).
- scope 규율: 결정 C 후 scope-out 0 edge(deferred.scope_out_edges 빈 배열).
- GAP-25: 실 axis-state 노드수 재측정(≪5000).
- 결정론: build_decision_tree.tree == on-disk(재생성 동일, 생성 근거 falsifiable).
"""
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

TREE = json.loads((PROJECT_ROOT / "spec" / "decision_tree.json").read_text(encoding="utf-8"))
ANCHORS = json.loads((PROJECT_ROOT / "anchors.json").read_text(encoding="utf-8"))
CUNITS = {c["c_id"]: c for c in
          json.loads((PROJECT_ROOT / "spec" / "c_units.json").read_text(encoding="utf-8"))}
STRANDS = json.loads((PROJECT_ROOT / "spec" / "strands.json").read_text(encoding="utf-8"))
COST = {cid: c["cost"] for cid, c in CUNITS.items()}

from src.orchestrator import REGISTRY  # noqa: E402  — wired 57 (SSOT 배선)

NODES = {n["id"]: n for n in TREE["nodes"]}
CR = TREE["conditional_routing"]
EDGESET = {(e["from"], e["to"]) for e in CR}
C_NODES = sorted(n["id"] for n in TREE["nodes"] if n.get("kind"))
ROUTE_C = {cid for cid in REGISTRY if CUNITS[cid].get("kind") == "route"}
PART = TREE["stats"]["q_partition"]


# ───────────────── 골격 정합 (step 1) ─────────────────
def test_c_nodes_equal_registry():
    """c node 집합 == orchestrator REGISTRY(wired 57). generator WIRED↔배선 drift falsifiable."""
    assert set(C_NODES) == set(REGISTRY.keys())
    assert len(C_NODES) == 57


def test_backbone_process_and_axis_nodes():
    """N0–N7(branch) + A0–A10(conditional) 전수, anchors 그대로."""
    for nid in ANCHORS["nodes"]:
        assert NODES[nid]["type"] == "branch", nid
    for aid in ANCHORS["axes"]:
        assert NODES[aid]["type"] == "conditional", aid
        assert NODES[aid]["states"] == ANCHORS["axes"][aid], aid


def test_axis_states_total_101():
    """A0–A10 axis-state 합 == 101(anchors). GAP-25 실 cell 수 근거."""
    total = sum(len(NODES[a]["states"]) for a in ANCHORS["axes"])
    assert total == 101
    assert TREE["stats"]["axis_states_total"] == 101


def test_terminals_present_exact():
    """5 process + 19 Q terminal, id == anchors(초과/누락 0)."""
    proc = {n["id"] for n in TREE["nodes"] if n.get("terminal_class") == "process"}
    qter = {n["id"] for n in TREE["nodes"] if n.get("terminal_class") == "q_code"}
    assert proc == set(ANCHORS["terminals"])
    assert qter == set(ANCHORS["q_codes"])
    assert len(proc) == 5 and len(qter) == 19


def test_no_foreign_identifiers():
    """★ G1: 모든 node id ∈ anchors(N/A/terminal/Q) ∪ wired c. 임의 식별자 0(hallucination 차단)."""
    allowed = (set(ANCHORS["nodes"]) | set(ANCHORS["axes"]) | set(ANCHORS["terminals"])
               | set(ANCHORS["q_codes"]) | set(REGISTRY.keys()))
    foreign = [n["id"] for n in TREE["nodes"] if n["id"] not in allowed]
    assert foreign == [], foreign


# ───────────────── D-S4 conditional edge (step 2.5) ─────────────────
def test_every_wired_can_route_to_q_has_edge():
    """★ 사용자 검증 항목: 모든 배선 c의 can_route_to_q가 conditional edge로 존재."""
    missing = [(cid, q) for cid in REGISTRY
               for q in (CUNITS[cid].get("can_route_to_q") or []) if (cid, q) not in EDGESET]
    assert missing == [], missing


def test_conditional_edge_targets_in_anchors():
    """G1: 모든 conditional edge target ∈ anchors.q_codes."""
    bad = [e for e in CR if e["to"] not in ANCHORS["q_codes"]]
    assert bad == [], bad


def test_no_isolated_exercised_q_terminal():
    """★ D-S4: exercised Q(13) 전부 incoming conditional edge ≥1(고립 Q-terminal 0)."""
    incoming = {q: sum(1 for e in CR if e["to"] == q) for q in ANCHORS["q_codes"]}
    iso = [q for q in PART["exercised"] if incoming[q] == 0]
    assert iso == [], iso
    assert len(PART["exercised"]) == 13


def test_static_q_edge_without_route_realizer():
    """STATIC Q(Q05/Q10): incoming edge는 있으나 realizing route c 없음 → 검증 strand 없음(falsifiable)."""
    assert sorted(PART["static_no_strand"]) == ["Q05", "Q10"]
    for q in PART["static_no_strand"]:
        edges = [e for e in CR if e["to"] == q]
        assert edges, q                                   # 정적 edge는 주입됨
        assert all(e["realizing_route_c"] == [] for e in edges), q  # 그러나 route 실현자 없음


def test_unreached_q_zero_incoming_but_documented():
    """UNREACHED Q(Q15A/B/C/X): wired incoming 0 + deferred.unreached_q에 명문 기록(silent drop 아님)."""
    assert sorted(PART["unreached"]) == ["Q15A", "Q15B", "Q15C", "Q15X"]
    for q in PART["unreached"]:
        assert [e for e in CR if e["to"] == q] == []      # incoming 0
    documented = {d["q"] for d in TREE["deferred"]["unreached_q"]}
    assert documented == set(PART["unreached"])


# ───────────────── scope 규율 (spec-결정 edge 제외) ─────────────────
TERMSET = {(e["from"], e["to"]) for e in TREE["terminal_routing"]}


def test_scope_out_edges_not_injected():
    """★ scope 규율: 결정 C(GAP-28 RESOLVE)로 c0253→Q15D가 can_route_to_q 편입 → conditional 주입(scope-out 0).
    결정 A로 c0252→Q04 conditional 주입, 결정 B로 INVALID 3개는 terminal_routing(conditional_routing 아님)으로 이동."""
    # 결정 C(GAP-28): c0253→Q15D는 이제 conditional edge로 주입됨(더는 scope-out 아님)
    assert ("c0253", "Q15D") in EDGESET
    assert ("c0253", "Q15D") not in TERMSET
    # 결정 A: c0252→Q04는 conditional_routing에 주입됨
    assert ("c0252", "Q04") in EDGESET
    # 결정 B: INVALID 3개는 conditional_routing이 아니라 terminal_routing에만
    for inv in [("c0252", "INVALID"), ("c0253", "INVALID"), ("c0256", "INVALID")]:
        assert inv not in EDGESET, inv
        assert inv in TERMSET, inv


def test_scope_out_documented_in_deferred():
    """결정 C(GAP-28 RESOLVE) 후 scope-out 0 → deferred.scope_out_edges는 빈 배열(잔존 이월 없음)."""
    so = TREE["deferred"]["scope_out_edges"]
    pairs = {(e["from"], e["to"]) for e in so}
    assert pairs == set()
    assert sum(e["strand_count"] for e in so) == 0        # GAP-28 해소(89 pure 편입); 결정 A 168·결정 B 174+111+30 기해소
    assert all(e["gap"] == "GAP-28" for e in so)          # vacuous(빈 배열) — 잔존 시 GAP cite 보존 규약


# ───────────────── 압축 불변성 (① 비의존) ─────────────────
def test_cost_invariance_all_5000():
    """★ 압축 불변성(cost): 5000 strand 전부 total_cost == Σ COST[c]. tree는 동일 cost 모델(Q.routing_cost 비가산)."""
    bad = [x["sc_id"] for x in STRANDS if x["total_cost"] != sum(COST[c] for c in x["c_sequence"])]
    assert bad == [], bad[:10]
    assert all(NODES[q].get("routing_cost_added_to_path") is False
               for q in ANCHORS["q_codes"])               # Q.routing_cost 경로 비가산 명시


def test_terminal_invariance_pure_scope():
    """★ 압축 불변성(terminal): last-c∈wired ROUTE & q∈can_route_to_q인 strand는 tree edge가 동일 Q 재현."""
    pure = 0
    for x in STRANDS:
        lc = (x["c_sequence"] or [None])[-1]
        q = x.get("q_code")
        if lc in ROUTE_C and q and q in (CUNITS[lc].get("can_route_to_q") or []):
            assert (lc, q) in EDGESET, (lc, q)
            pure += 1
    assert pure == 3228                                   # 결정 A c0252→Q04(168) + 결정 C c0253→Q15D(89) 편입 (2971+168+89)
    assert TREE["stats"]["pure_realized_strands"] == 3228


# ───────────────── 결정 B: terminal_routing (process-terminal edge) ─────────────────
def test_terminal_routing_injected():
    """★ 결정 B: process-terminal edge(INVALID) 3개가 terminal_routing에 주입(Q-edge와 분리).
    c0252→INVALID 174 + c0253→INVALID 111 + c0256→INVALID 30 = 315. INVALID 도달성 확보(dead 아님)."""
    tr = TREE["terminal_routing"]
    pairs = {(e["from"], e["to"]) for e in tr}
    assert pairs == {("c0252", "INVALID"), ("c0253", "INVALID"), ("c0256", "INVALID")}
    assert sum(e["strand_count"] for e in tr) == 315
    assert all(e["source"] == "postcond_routing_decision" for e in tr)
    # terminal_routing target ⊆ process terminal, Q-code 아님 (Q-edge와 미혼재)
    assert all(e["terminal_class"] == "process" and e["to"] in ANCHORS["terminals"] for e in tr)
    assert all(e["to"] not in ANCHORS["q_codes"] for e in tr)
    # SSOT 정합: 각 edge의 terminal은 해당 c의 postcond routing_decision에 선언됨
    for e in tr:
        decl = set(re.findall(r"'([A-Z0-9-]+)'", CUNITS[e["from"]].get("postcondition_predicate", "")))
        assert e["to"] in decl, (e["from"], e["to"])
    # INVALID process terminal incoming ≥ 1 (더는 고립/dead 아님)
    assert sum(1 for e in tr if e["to"] == "INVALID") >= 1
    assert TREE["stats"]["terminal_edges"] == 3 and TREE["stats"]["terminal_strands"] == 315


def test_terminal_declared_unexercised_documented():
    """c0251→INVALID는 postcond 선언이나 측정 strand 0 → terminal_routing 미주입, stats에 falsifiable 기록(silent drop 금지)."""
    decl = TREE["stats"]["terminal_declared_unexercised"]
    assert {(d["from"], d["to"]) for d in decl} == {("c0251", "INVALID")}
    assert all(d["strand_count"] == 0 for d in decl)
    assert ("c0251", "INVALID") not in {(e["from"], e["to"]) for e in TREE["terminal_routing"]}


# ───────────────── GAP-25 재측정 / scope / 결정론 ─────────────────
def test_gap25_node_count_remeasure():
    """GAP-25: 실 axis-state 기준 collapsed 100 / expanded 190 노드 — synthetic 248/236 갱신, ≪5000."""
    g = TREE["stats"]["gap25_remeasure"]
    collapsed = len(ANCHORS["nodes"]) + len(ANCHORS["axes"]) + len(ANCHORS["terminals"]) \
        + len(ANCHORS["q_codes"]) + 57
    expanded = len(ANCHORS["nodes"]) + 101 + len(ANCHORS["terminals"]) + len(ANCHORS["q_codes"]) + 57
    assert g["collapsed_display_nodes"] == collapsed == 100
    assert g["expanded_worst_nodes"] == expanded == 190
    assert expanded < 5000


def test_bundles_empty_skeleton_scope():
    """이번 세션 scope: suffix-tree 다발 압축 미수행 → bundles == []."""
    assert TREE["bundles"] == []
    assert TREE["stats"]["bundles"] == 0


def test_deterministic_regeneration():
    """★ 생성 근거 falsifiable: build_decision_tree.tree(재구성) == on-disk decision_tree.json."""
    import build_decision_tree
    assert build_decision_tree.tree == TREE
