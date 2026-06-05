"""render/index_v3.html(정본 흐름 뷰) 검증 — 엔진/SSOT 무수정(신규 파일).

핵심:
  (구조) backbone_routing 52 edge(route_gate 14/route_axis 27/axis_onward 11) + 🏁 그룹 +
         spec_only 65 노드(runnable=false) + declared_conditional 35(미실현) 가 그래프에 정확히 렌더.
  (계승) v2 100% 상속 — EASY 122·wizard==ingest·glossary·passChip/failChip·색(앰버/청록).
  (정직) v2/v1(index.html·index_v2.html·build_html*.py) byte-불변. node --check 통과.
※ headless Chrome 콘솔-에러-0·perf는 수동 1회 실측(결과 issues 기록); 본 스위트는 환경-비의존만 커밋.
"""
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "render"))

import build_html_v3 as V3  # noqa: E402  (import 시 B·V2 데이터층 빌드 — index_*.html 미작성)
import build_html_v2 as V2  # noqa: E402
import build_html as B      # noqa: E402

from src.adapter.navigator import _FILE_PROPERTY, _DATA_DEPENDENT, _CANON_ORDER  # noqa: E402
from src.adapter import xlsx_ingester as XI  # noqa: E402

HTML = V3.build_html()
ELES = V3._eles_v3()
NODES = [e["data"] for e in ELES if "source" not in e["data"]]
EDGES = [e["data"] for e in ELES if "source" in e["data"]]
NODE_IDS = {n["id"] for n in NODES}
EK = Counter(e.get("ekind") for e in EDGES)


# ===== (1) 결정성 ============================================================
def test_v3_build_deterministic():
    assert V3.build_html() == V3.build_html()


# ===== (2) 노드/엣지 카운트 ===================================================
def test_v3_graph_node_count():
    # 167 = v1 101(100 canonical + 합성 stage 1) + spec_only 65 + 🏁 group 1
    assert len(NODES) == 167, len(NODES)
    # budget metric(canonical-only)은 별개 불변: 165 = 100 + 65
    assert B.STATS["render_budget_v3"]["collapsed_with_spec_only"] == 165


def test_v3_new_edge_counts():
    assert EK["route_gate"] == 14
    assert EK["route_axis"] == 27
    assert EK["axis_onward"] == 11
    assert EK["route_gate"] + EK["route_axis"] + EK["axis_onward"] == 52
    assert EK["spec_attach"] == 65
    assert EK["declared_cond"] == 35


def test_v3_edge_endpoints_reference_real_nodes():
    # 'L-4->L-5' remap 회귀 가드: 모든 edge 양끝이 실 노드 id
    for e in EDGES:
        assert e["source"] in NODE_IDS, ("dangling source", e["id"], e["source"])
        assert e["target"] in NODE_IDS, ("dangling target", e["id"], e["target"])


def test_v3_no_duplicate_spine():
    # backbone_routing의 spine 9 edge는 v1 합성 bb_*와 중복 → v3 추가분에 재출현 금지
    extra = V3.v3_extra_elements()
    assert not any(d["data"].get("brtype") == "spine" for d in extra if "source" in d["data"])
    # 기존 'backbone' ekind 개수 불변(v1 25)
    assert EK["backbone"] == Counter(
        e["data"].get("ekind") for e in B.ELES if "source" in e["data"])["backbone"]


# ===== (3) 🏁 완성종착 그룹 ===================================================
def test_v3_group_parent_and_children():
    g = next((n for n in NODES if n["id"] == "L0_group"), None)
    assert g is not None and g.get("group") is True
    assert "🏁 nonmem-ready(L0)" in g["label"]
    auto = next(n for n in NODES if n["id"] == "AUTO")
    repair = next(n for n in NODES if n["id"] == "REPAIR")
    assert auto.get("parent") == "L0_group" and repair.get("parent") == "L0_group"
    # 정본 id/label/kind 보존(parent만 추가)
    b_auto = next(e["data"] for e in B.ELES if e["data"].get("id") == "AUTO")
    assert auto["label"] == b_auto["label"] and auto["kind"] == b_auto["kind"]


def test_v3_completion_path_present():
    pairs = {(e["source"], e["target"]) for e in EDGES}
    assert ("N7", "AUTO") in pairs and ("N7", "REPAIR") in pairs  # v1 합성 spine 유지


def test_v3_no_axis_sink():
    onward_sources = {e["source"] for e in EDGES if e.get("ekind") == "axis_onward"}
    for ax in B.AXIS_IDS:
        assert ax in onward_sources, ("axis sink (no axis_onward)", ax)


# ===== (4) spec_only 정직 표시 ===============================================
def test_v3_spec_only_nodes_runnable_false():
    so = [n for n in NODES if n.get("spec_only")]
    assert len(so) == 65
    assert all(n.get("runnable") is False for n in so)
    assert {n["id"] for n in so} == set(V2.CUNITS_EXTRA)  # 65 == 작업카드 fallback


def test_v3_spec_only_dead_flagged():
    dead = {n["id"] for n in NODES if n.get("dead")}
    assert dead == {"c0042", "c0043", "c0333"}, dead


def test_v3_spec_only_badge_in_html():
    assert "spec-only-badge" in HTML
    assert "정의됨 · 미구현 (spec_only)" in HTML
    assert "window.renderCPanel = function" in HTML  # v2 위 래퍼


def test_v3_declared_conditional_distinct_style():
    assert 'ekind="declared_cond"' in HTML or "declared_cond" in HTML
    assert "#9C6ADE" in HTML  # 보라 = 선언·미실현
    # 자동 경로 추적에서 미실현/미배선 제외(정직성)
    assert 'ekind != "declared_cond"' in HTML
    assert 'ekind != "spec_attach"' in HTML


# ===== (5) v2 계승(회귀) =====================================================
def test_v3_easy_122_reachable():
    universe = set(B.CUNITS) | set(V2.CUNITS_EXTRA)
    assert set(V2.EASY) <= universe
    assert len(V2.EASY) == 122
    assert "renderEasyCPanel" in HTML and "var EASY=" in HTML


def test_v3_wizard_constants_match_adapter():
    assert V2.WIZARD["file_property_c"] == list(_FILE_PROPERTY)
    assert V2.WIZARD["data_dependent_c"] == list(_DATA_DEPENDENT)
    assert V2.WIZARD["canon_order"] == list(_CANON_ORDER)
    assert set(V2.WIZARD["qa_tokens"]) == set(XI._QA_TOKENS)


def test_v3_reuses_v2_wizard_identity():
    # v3는 wizard 로직을 복제하지 않고 V2를 그대로 사용 → ingest 동치(test_simulation_realdata)가 상속됨
    assert V3.V2 is V2
    assert V3.V2.WIZARD is V2.WIZARD


def test_v3_js_wizard_matches_python(tmp_path):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node 미설치 — JS↔python 동치 검사 생략")
    i = HTML.index("function wizardVerdict(")
    depth, k, started = 0, i, False
    while k < len(HTML):
        ch = HTML[k]
        if ch == "{":
            depth += 1
            started = True
        elif ch == "}":
            depth -= 1
            if started and depth == 0:
                fn = HTML[i:k + 1]
                break
        k += 1
    else:
        raise AssertionError("wizardVerdict 미발견")
    import json
    cunits = {kk: {"can_route_to_q": c.get("can_route_to_q", [])} for kk, c in B.CUNITS.items()}
    harness = (
        "var WIZARD=" + json.dumps(V2.WIZARD) + ";\n"
        "var CUNITS=" + json.dumps(cunits) + ";\n" + fn + "\n"
        "var out=[];[true,false].forEach(function(t){[true,false].forEach(function(s){\n"
        "  var a={tidy:t,has_subject:s};var v=wizardVerdict(a);\n"
        "  out.push({a:a,c:v.c_sequence,f:v.faithful});});});\n"
        "console.log(JSON.stringify(out));\n"
    )
    p = tmp_path / "h.js"
    p.write_text(harness, encoding="utf-8")
    r = subprocess.run([node, str(p)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    for item in json.loads(r.stdout):
        pv = V2.wizard_verdict_from_answers(item["a"])
        assert item["c"] == pv["c_sequence"], (item["a"], item["c"], pv["c_sequence"])
        assert item["f"] == pv["faithful_tidy"], item["a"]


def test_v3_glossary_complete():
    assert V2.assert_glossary_complete() is True


def test_v3_color_semantics():
    assert "#E8820C" in HTML and "#15B4C7" in HTML            # 앰버 실선 / 청록 점선
    for legacy in ("#FFD700", "#FFF8B0", "#c9920e"):
        assert legacy not in HTML, ("legacy highlight color leaked", legacy)


# ===== (6) self-contained / inline-only ======================================
def test_v3_inline_libs_no_external():
    assert "<script src=" not in HTML
    assert "<link" not in HTML
    assert "<img" not in HTML
    for cdn in ("cdnjs", "unpkg", "jsdelivr", "googleapis"):
        assert cdn not in HTML, cdn


def test_v3_single_self_contained_file():
    assert HTML.lstrip().startswith("<!DOCTYPE")
    assert "index v3" in HTML
    assert len(HTML.encode("utf-8")) > 1_000_000  # inline libs


# ===== (7) v2/v1 byte-불변 가드(★ 핵심) =======================================
def test_v3_does_not_touch_v1_v2(tmp_path):
    targets = ["render/index.html", "render/index_v2.html",
               "render/build_html.py", "render/build_html_v2.py"]
    before = {t: (ROOT / t).read_bytes() for t in targets}
    V3.main()                                  # index_v3.html만 기록해야 함
    after = {t: (ROOT / t).read_bytes() for t in targets}
    for t in targets:
        assert before[t] == after[t], ("v3 빌드가 v1/v2 파일을 변경함", t)
    out = ROOT / "render" / "index_v3.html"
    assert out.exists() and "index v3" in out.read_text(encoding="utf-8")


# ===== (8) node --check: inline script 문법 무결 ==============================
def test_v3_inline_scripts_node_check(tmp_path):
    node = shutil.which("node")
    if node is None:
        pytest.skip("node 미설치 — JS 문법검사 생략")
    import re
    blocks = re.findall(r"<script>(.*?)</script>", HTML, re.S)
    assert len(blocks) >= 4
    for idx, b in enumerate(blocks):
        f = tmp_path / ("blk%d.js" % idx)
        f.write_text(b, encoding="utf-8")
        r = subprocess.run([node, "--check", str(f)], capture_output=True, text=True)
        assert r.returncode == 0, ("node --check 실패 block %d: %s" % (idx, r.stderr[:300]))


# ===== (9) v3 표현 재설계: 블루프린트 레이아웃·collapse (표현층 전용·환경 비의존) =====
def test_v3_spec_toggle_button_present():
    # 런타임 DOM 삽입 토글 + 함수 일습
    assert 'id="v3SpecToggle"' in HTML
    assert "insertSpecToggle" in HTML
    assert "applySpecOnlyVisibility" in HTML


def test_v3_spec_collapse_default_hidden_logic():
    # 기본 접힘: LS 키 null → hidden(true)
    assert "pmx_dt_v3_specHidden" in HTML
    assert "v3IsSpecHidden" in HTML
    # cy.remove 아닌 display 토글(reversible·ELES 불변)
    assert 'style("display"' in HTML or "style('display'" in HTML
    # hide 대상에 spec_only 노드 + spec_attach + declared_cond 엣지 포함
    assert "[?spec_only]" in HTML
    assert 'ekind="spec_attach"' in HTML
    assert 'ekind="declared_cond"' in HTML


def test_v3_separate_ls_key_not_pmx_dt_state():
    # v3 선호는 별도 키(frozen pmx_dt_state 비건드림)
    assert "pmx_dt_v3_specHidden" in HTML
    assert "pmx_dt_v3_specHidden" != "pmx_dt_state"


def test_v3_layoutopts_override_present():
    # 전역 layoutOpts 재대입 + 재튜닝 파라미터
    assert "layoutOpts = function" in HTML or "layoutOpts=function" in HTML
    assert "tight-tree" in HTML
    assert "edgeSep" in HTML
    assert 'rankDir:"LR"' in HTML  # 가로 배치 유지


def test_v3_relayout_calls_drawminimap_and_perf_honest():
    assert "relayoutV3" in HTML
    assert "drawMinimap" in HTML
    assert "layoutstop" in HTML
    # perf 정직: 초기 t_total에 v3 재레이아웃 추가분 표기(날조 0)
    assert "t_v3relayout" in HTML
    assert "v3 +" in HTML


def test_v3_blueprint_chrome_markers():
    # 블루프린트 그리드 backdrop + Pretendard 우선 폰트(외부자산 아님)
    assert "rgba(28,111,176" in HTML            # cyan 그리드 라인
    assert "Pretendard" in HTML
    assert "background-size:24px 24px" in HTML or "24px 24px" in HTML


def test_v3_canonical_hues_preserved_after_redesign():
    # 정본 색 의미 보존(앰버 실선·청록 점선·보라 미실현)
    for hue in ("#E8820C", "#15B4C7", "#9C6ADE"):
        assert hue in HTML, ("정본 hue 누락", hue)
    # 금지 하이라이트 색 재유입 0(재설계 후에도)
    for legacy in ("#FFD700", "#FFF8B0", "#c9920e"):
        assert legacy not in HTML, ("legacy color 재유입", legacy)


def test_v3_breadcrumb_layer_banding():
    # (B) 마법사 breadcrumb를 layer 띠로 재구성하는 DOM 후처리(칩 이동→onclick 보존)
    assert "v3RebandBreadcrumb" in HTML
    assert "v3LayerOf" in HTML
    assert "MutationObserver" in HTML
    assert "bcband" in HTML
    assert "data-v3band" in HTML
    # layer 라벨 맵에 최하층 L-4↔L-5 표기 정규화 포함
    assert "L-4->L-5" in HTML and "표기 정규화" in HTML
