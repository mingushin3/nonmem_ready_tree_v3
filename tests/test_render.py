"""tests/test_render.py — Phase 8 렌더 구조 invariant (브라우저 불요, DoD #6 green 게이트 유지).

render/build_html.py가 spec/decision_tree.json(+c_units/q_codes/strands/anchors)을 단일 self-contained
interactive HTML(render/index.html)로 deterministic하게 렌더하는지 구조적으로 검증한다.
(dagre 라이브 ms는 별도 headless/사용자 Chrome 측정 — GAP-25; 여기서는 node-count·join·고립·시각구분·inline만.)
"""

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "render"))
import build_html as B  # noqa: E402

INDEX = ROOT / "render" / "index.html"


@pytest.fixture(scope="module")
def html():
    B.main()  # 항상 새로 빌드(테스트가 산출물을 신선하게 유지)
    return INDEX.read_text(encoding="utf-8")


# ───────────────────────── canonical node/edge 수 (decision_tree.json stats 정합)
def test_canonical_node_counts():
    assert len(B.C_IDS) == 57
    assert len(B.Q_IDS) == 19
    assert len(B.AXIS_IDS) == 11
    assert len(B.BRANCH_IDS) == 8
    assert len(B.PROC_IDS) == 5
    assert len(B.C_IDS) + len(B.Q_IDS) + len(B.AXIS_IDS) + len(B.BRANCH_IDS) + len(B.PROC_IDS) == 100
    s = B.STATS
    assert s["nodes_total"] == 100
    assert s["conditional_edges"] == len(B.COND) == 52
    assert s["terminal_edges"] == len(B.TERMR) == 3
    assert s["attach_edges"] == len(B.ATTACH) == 76


def test_edge_endpoints_reference_real_nodes():
    # 모든 edge의 source/target은 선언된 node id여야 한다(cytoscape 예약키 'source'/'target' 충돌 회귀 방지).
    node_ids = {e["data"]["id"] for e in B.ELES if "source" not in e["data"]}
    for e in B.ELES:
        d = e["data"]
        if "source" in d:
            assert d["source"] in node_ids, "edge %s: source %r 미존재 노드" % (d.get("id"), d["source"])
            assert d["target"] in node_ids, "edge %s: target %r 미존재 노드" % (d.get("id"), d["target"])


def test_edge_composition_in_eles():
    ek = {}
    for e in B.ELES:
        d = e["data"]
        if "source" in d:
            ek[d["ekind"]] = ek.get(d["ekind"], 0) + 1
    assert ek.get("attach", 0) >= 76          # 76 canonical (+ 합성 c0001 boundary link)
    assert ek.get("conditional", 0) == 52     # D-S4 Q-route (정확히 canonical)
    assert ek.get("terminal_routing", 0) == 3  # 결정 B (정확히 canonical)
    assert ek.get("backbone", 0) >= 9          # spine + N7→AUTO/REPAIR + Q→QUARANTINE + A0 link
    assert ek.get("deferred", 0) >= 2          # GAP-13 c0210→UNSUPPORTED/INVALID


# ───────────────────────── join 완전성 (c_units / q_codes)
def test_all_c_units_joined():
    assert set(B.CUNITS) == set(B.C_IDS)
    for cid, c in B.CUNITS.items():
        assert c["c_name_ko"], cid
        assert c["python_snippet"], cid
        assert c["srp_intent"], cid
        assert isinstance(c["precondition_checklist_ko"], list)


def test_all_q_joined_with_panel_fields():
    assert set(B.QINFO) == set(B.Q_IDS)
    for qid, q in B.QINFO.items():
        assert q["human_decision_point"], qid       # (C')
        assert q["recover_to_c_id"], qid            # (D')
        assert isinstance(q["clarification_to_sponsor"], list)  # (B')


def test_q_partition_counts():
    qp = B.QPART
    assert len(qp["exercised"]) == 13
    assert len(qp["static_no_strand"]) == 2
    assert len(qp["unreached"]) == 4
    assert set(qp["unreached"]) == {"Q15A", "Q15B", "Q15C", "Q15X"}


# ───────────────────────── 고립 노드 0 (의도된 deferred unreached Q 제외)
def test_no_isolated_nodes_except_deferred():
    node_ids = {e["data"]["id"] for e in B.ELES if "source" not in e["data"]}
    incident = set()
    for e in B.ELES:
        if "source" in e["data"]:
            incident.add(e["data"]["source"])
            incident.add(e["data"]["target"])
    isolated = node_ids - incident
    assert isolated == set(B.QPART["unreached"]), "고립 노드는 deferred unreached Q뿐이어야 함: %s" % sorted(isolated)


def test_every_nondeferred_q_has_incoming():
    # 13 exercised + 2 static = 15 Q는 conditional incoming ≥1 (D-S4 고립 Q-terminal 0)
    cond_to = {e["to"] for e in B.COND}
    for q in B.QPART["exercised"] + B.QPART["static_no_strand"]:
        assert q in cond_to, "%s 고립(conditional incoming 0)" % q


# ───────────────────────── deferred 시각 마커
def test_deferred_markers_present(html):
    for q in ("Q15A", "Q15B", "Q15C", "Q15X"):
        assert q in html
    ids = {sd.get("id") for sd in B.DEFERRED_VIEW["spec_decisions"]}
    assert {"GAP-13", "GAP-27B"} <= ids
    # unreached Q 노드는 deferred 플래그
    for e in B.ELES:
        d = e["data"]
        if d.get("kind") == "terminal_q" and d["id"] in B.QPART["unreached"]:
            assert d.get("deferred") is True, d["id"]


# ───────────────────────── inline 라이브러리(GAP-25 정본) · 외부 의존 0
def test_inline_libs_no_external(html):
    assert "inlined: cytoscape 3.30.2" in html
    assert "inlined: dagre 0.8.5" in html
    assert "inlined: cytoscape-dagre" in html
    # CDN/외부 fetch 0 — inline만(라이선스 주석의 http URL은 fetch 아님이라 무관).
    assert "<script src=" not in html and "<link " not in html
    assert 'src="http' not in html and 'href="http' not in html
    for cdn in ("cdnjs", "unpkg", "jsdelivr", "googleapis"):
        assert cdn not in html, cdn
    assert "<img" not in html  # 외부 image 0 (Lock 6: SVG inline만)


def test_single_self_contained_file(html):
    assert html.lstrip().startswith("<!DOCTYPE html>")
    assert html.rstrip().endswith("</html>")
    assert len(html.encode("utf-8")) > 700 * 1024  # inline 라이브러리 포함 → >700KB


# ───────────────────────── Lock 6/7 시각 규약
def test_lock7_highlight_colors(html):
    assert "#FFD700" in html      # 단일 경로 5px
    assert "#FFF8B0" in html      # conditional 3px
    assert "pmx_dt_state" in html  # localStorage key ([7-3])


def test_node_shapes_present(html):
    for shape in ("hexagon", "diamond", "star", "ellipse", "octagon", "round-rectangle"):
        assert shape in html, shape
    assert 'kind="terminal_q"' in html and "#ef5350" in html  # Q-code 빨강사각


def test_conditional_vs_terminal_routing_visually_distinct(html):
    # conditional(Q) edge와 terminal_routing(INVALID) edge가 별도 ekind/스타일로 구분
    assert 'ekind="conditional"' in html
    assert 'ekind="terminal_routing"' in html


def test_perf_self_measurement_present(html):
    assert "window.__PERF__" in html
    assert "perfBadge" in html
    assert "10000" in html  # DoD#6 게이트 ms


# ───────────────────────── determinism (재실행 동일)
def test_build_deterministic():
    B.main()
    a = INDEX.read_bytes()
    B.main()
    b = INDEX.read_bytes()
    assert a == b


# ═════════════════════════ Phase 8b — UAT 반영(시각 명료성·끊김 표기·recover edge) ═════════════════════════
def _recover_edges():
    return [e["data"] for e in B.ELES if e["data"].get("ekind") == "recover"]


def test_recover_edges_separate_ekind():
    # recover는 별도 ekind — conditional/terminal_routing 카운트와 섞이지 않음(구조 invariant 회귀)
    ek = {}
    for e in B.ELES:
        d = e["data"]
        if "source" in d:
            ek[d["ekind"]] = ek.get(d["ekind"], 0) + 1
    assert ek["conditional"] == 52
    assert ek["terminal_routing"] == 3
    assert ek["recover"] == 14
    assert len(_recover_edges()) == 14


def test_recover_only_reachable_q_to_wired_c():
    reachable = set(B.QPART["exercised"]) | set(B.QPART["static_no_strand"])
    cset = set(B.C_IDS)
    unreached = set(B.QPART["unreached"])
    seen_q = set()
    for d in _recover_edges():
        assert d["source"] in reachable and d["source"] not in unreached, d["source"]
        assert d["target"] in cset and d["target"] in B.CUNITS, d["target"]
        seen_q.add(d["source"])
    # 기대 = recover_to_c_id가 wired인 도달가능 Q (q_codes SSOT에서 도출 — 하드코딩 아님)
    expected = {q for q in reachable if B.QC.get(q, {}).get("recover_to_c_id") in cset}
    assert seen_q == expected


def test_recover_unwired_target_and_unreached_skipped():
    srcs = {d["source"] for d in _recover_edges()}
    assert "Q10" not in srcs           # Q10→c0330 미배선 → edge 생략
    assert "c0330" not in set(B.C_IDS)  # 전제
    for q in B.QPART["unreached"]:      # unreached Q는 전부 제외(고립 불변)
        assert q not in srcs


def test_recover_isolation_invariant_preserved():
    # recover edge 추가 후에도 고립 노드 == unreached Q (기존 invariant 무변경)
    node_ids = {e["data"]["id"] for e in B.ELES if "source" not in e["data"]}
    incident = set()
    for e in B.ELES:
        if "source" in e["data"]:
            incident.add(e["data"]["source"])
            incident.add(e["data"]["target"])
    assert (node_ids - incident) == set(B.QPART["unreached"])


def test_boundary_banner_numbers(html):
    # ★ 정직성: 전 수치 render 입력서 build-time 계산(strands.json/decision_tree.json) — 날조 0
    b = B.BANNER
    assert b["total_strands"] == 5000 and b["wired_c"] == 57
    assert b["complete"] == b["auto"] + b["repair"] == 235
    assert (b["quarantine"], b["invalid"], b["unsupported"]) == (3380, 862, 523)
    assert b["realized_pure"] == 3228
    assert b["unwired_c"] == 62 and b["static_q"] == 2 and b["deferred_total"] == 7
    # 주입 수치가 html에 존재 + oracle↔wired 두 축 구분 문구
    assert '"total_strands":5000' in html and '"complete":235' in html
    assert '"quarantine":3380' in html and '"unwired_c":62' in html
    assert 'id="boundary"' in html and "oracle 최적경로" in html and "현재 경계" in html


def test_termination_legend_present(html):
    for label in ("완주 AUTO/REPAIR", "QUARANTINE", "Q-code", "미실현 terminal",
                  "INVALID", "UNSUPPORTED", "미배선", "recover"):
        assert label in html, label


def test_termination_status_colors(html):
    # 완주 녹 / QUARANTINE 주황 / INVALID slate / UNSUP 회보라 / 미실현 회색
    for hexc in ("#43a047", "#a5d6a7", "#ffa726", "#546e7a", "#9e8aa8", "#b0bec5"):
        assert hexc in html, hexc
    assert "#ef5350" in html   # Q-code 빨강 보존(spec)


def test_conditional_gold_visibility(html):
    # 문제 A: resting conditional 골드 + 굵기 상향
    assert "#c9920e" in html
    assert '"width":3.6' in html
    assert 'ekind="conditional"' in html


def test_recover_edge_style_and_lock7_separation(html):
    assert 'ekind="recover"' in html
    assert "#1976d2" in html          # recover 파랑(자동 라우팅 분리)
    assert "사람" in html and "복귀" in html
    # Lock7 auto-flow union에서 recover 제외(human-loop) + Lock7 hue 불변
    assert 'ekind != "recover"' in html and "flowNeighborhood" in html and "hlRecover" in html
    assert "#FFD700" in html and "#FFF8B0" in html
