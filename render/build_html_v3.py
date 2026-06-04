"""render/build_html_v3.py — index_v3.html: v2 '쉬운 설명 뷰'를 100% 계승 + ★Phase A 정본 흐름 렌더.

★ 표현층 전용. 엔진/spec/SSOT 무수정(report-only). v1(index.html)·v2(index_v2.html)는 그대로 보존하고,
  본 파일은 별도 산출물 render/index_v3.html만 쓴다. 데이터층은 build_html(=B)을 통해, 쉬운 말 UI(EASY 122·
  진단 마법사·용어집·작업카드 122·passChip/failChip·색 규정)는 build_html_v2(=V2)를 import해 그대로 재사용한다.

v3가 새로 그리는 것(Phase A, commit 81483fd "GAP-13 정본 배선" → spec/decision_tree.json):
  (a) backbone_routing 52 edge(spine 9는 v1 합성 bb_*와 중복 → 제외): gate_branch 14 + axis_branch 27 + axis_onward 11.
      N0→N7 spine·N7→{AUTO,REPAIR} 완성종착은 v1이 이미 그림 → v3는 그 위에 분기/복귀 edge를 얹는다.
  (b) AUTO/REPAIR를 '🏁 nonmem-ready(L0)' compound 그룹으로 묶음(정본 id/label AUTO·REPAIR 유지).
  (c) 노드 클릭 → 출발→🏁 실제 선로(실선) 하이라이트. v1 flowNeighborhood(upstream∪downstream BFS)를
      재사용하되, declared_cond·spec_attach(미실현/미배선)는 자동 경로 union에서 제외(정직성).
  (d) spec_only 65 노드 클릭 가능 + '정의됨·미구현(spec_only)' 배지(runnable=false 시각 구분).
      declared_conditional 35는 보라 점선('선언만 됨·미실현')으로 realized와 분리 표시.

색·의미는 v2 유지: 앰버 실선=자동 진행, 청록 점선=질문(Q) 갈림길. v3 추가 색: 보라(#9C6ADE)=선언·미실현.
검증: tests/test_render_v3.py (구조·결정론·v2/v1 byte-불변 가드·node --check) + 수동 headless 1회(결과는 issues 기록).
"""
import copy
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)   # import build_html, build_html_v2 (siblings)
sys.path.insert(0, _ROOT)   # (src.adapter는 V2가 import)

import build_html as B       # noqa: E402  데이터층(main 가드 → import 시 index.html 미작성)
import build_html_v2 as V2   # noqa: E402  v2층(main 가드 → import 시 index_v2.html 미작성)

# ── Phase A 정본 데이터(read-only) ───────────────────────────────────────────
SPEC_ONLY = B.DT["spec_only"]              # {note, nodes(65), attach_edges(65), declared_conditional(35)}
BACKBONE_ROUTING = B.DT["backbone_routing"]  # 61 edge: spine 9 / gate_branch 14 / axis_branch 27 / axis_onward 11

# backbone_routing type → v3 ekind (spine은 v1 합성 bb_* edge와 중복 → 제외)
_BR_EKIND = {"gate_branch": "route_gate", "axis_branch": "route_axis", "axis_onward": "axis_onward"}


# ═════════════════════════════════════════════════════════════════════════════
# 1. v3 신규 그래프 요소 (B.E/B.N 동형 {data:{...}})
# ═════════════════════════════════════════════════════════════════════════════
def v3_extra_elements():
    """backbone_routing 52 edge + 🏁 그룹 + spec_only 65 node·65 attach·35 declared_conditional."""
    existing = {e["data"]["id"] for e in B.ELES if "source" not in e["data"]}
    els = []

    def N(_id, kind, label, **extra):
        d = {"id": _id, "kind": kind, "label": label}
        d.update(extra)
        els.append({"data": d})

    def E(_id, s, t, ekind, **extra):
        d = {"id": _id, "source": s, "target": t, "ekind": ekind}
        d.update(extra)
        els.append({"data": d})

    # (b) 🏁 완성종착 그룹 부모(AUTO/REPAIR는 _eles_v3에서 parent 재지정 — id 충돌 회피)
    N("L0_group", "group_complete", "🏁 nonmem-ready(L0)", group=True)

    # (a) backbone_routing — spine 9 제외, 나머지 52 edge. 전체 index로 br_<i> 안정.
    for i, e in enumerate(BACKBONE_ROUTING):
        if e["type"] == "spine":
            continue
        E("br_%d" % i, e["from"], e["to"], _BR_EKIND[e["type"]],
          brtype=e["type"], role=e.get("role", ""), reason=e.get("reason", ""),
          state=e.get("state", ""), basis=e.get("basis", ""), ref=e.get("ref", ""),
          # gate/axis 분기 = 질문 갈림길(청록 점선·hlCond) / axis_onward = clean 복귀(앰버 실선·hlSingle)
          conditional=(e["type"] in ("gate_branch", "axis_branch")))

    # (d) spec_only 65 노드 — id 충돌 가드(현재 교집합 0; Phase A 보장)
    collide = {n["id"] for n in SPEC_ONLY["nodes"]} & existing
    if collide:
        raise SystemExit("[build_html_v3] spec_only id가 기존 그래프 노드와 충돌: %s" % sorted(collide))
    for n in SPEC_ONLY["nodes"]:
        dead = (n.get("in_strand") is False)   # c0042/c0043/c0333
        N(n["id"], n["kind"], "%s\n%s" % (n["id"], n.get("srp_intent", "")),
          spec_only=True, runnable=False, in_strand=bool(n.get("in_strand")), dead=dead,
          layer=n.get("layer_pair", ""), cost=n.get("cost", 0),
          requires_detection_by=n.get("requires_detection_by"))

    # spec_only attach 65 — 'L-4->L-5'는 노드 id가 아니라 합성 stage 'stage:L-4->L-5'로 remap
    for i, e in enumerate(SPEC_ONLY["attach_edges"]):
        tgt = ("stage:%s" % e["to"]) if e["to"] == "L-4->L-5" else e["to"]
        E("so_at_%d" % i, e["from"], tgt, "spec_attach", via=e.get("via", ""), spec_only=True)

    # declared_conditional 35 — 선언만 됨·미실현(보라 점선; realized와 분리)
    for i, e in enumerate(SPEC_ONLY["declared_conditional"]):
        E("decl_%d" % i, e["from"], e["to"], "declared_cond",
          declared=True, realized=False, csource=e.get("source", ""),
          from_kind=e.get("from_kind", ""), qstatus=e.get("q_status", ""))

    return els


def _eles_v3():
    """B.ELES deepcopy(공유 객체 비변형) + AUTO/REPAIR를 🏁 그룹 child로 재지정 + v3 신규 요소."""
    eles = copy.deepcopy(B.ELES)
    for e in eles:
        d = e["data"]
        if "source" not in d and d["id"] in ("AUTO", "REPAIR"):
            d["parent"] = "L0_group"   # 정본 id/label 유지, parent만 추가
    return eles + v3_extra_elements()


# ═════════════════════════════════════════════════════════════════════════════
# 2. v3 추가 스타일 + JS override
# ═════════════════════════════════════════════════════════════════════════════
_V3_CSS = """
  /* ── index v3 추가 스타일(정본 흐름: spec_only 배지) ── */
  .spec-only-badge{display:block;margin:0 0 8px;padding:6px 10px;border:1px dashed #9C6ADE;
    border-radius:6px;background:#f5f0fb;color:#6a3fb0;font-size:12px;font-weight:700;line-height:1.4}
  .legend-v3{margin-top:6px;border-top:1px dashed #cdd6e0;padding-top:6px}
  .legend-v3 .v3h{font-weight:700;font-size:11px;color:#5b6b7d;margin-bottom:3px}
"""

# 색: 앰버 #E8820C(자동 실선) · 청록 #15B4C7(질문 점선) · 보라 #9C6ADE(선언·미실현).
# ★ recolor()를 거치지 않으므로 최종 색을 직접 기입(의도된 표현층 색).
_V3_OVERRIDE = r'''<script>
/* ===== index v3 override: 정본 흐름(backbone_routing·spec_only) 위에 v2를 그대로 계승 ===== */
(function(){
  /* ---- 2a. 신규 ekind/node 스타일을 STYLE에 덧대고 재적용 (cy는 이미 생성됨) ---- */
  var V3_STYLE=[
    {selector:'edge[ekind="route_gate"]',style:{"line-style":"dashed","line-dash-pattern":[10,5],"line-color":"#15B4C7","target-arrow-color":"#15B4C7","width":3.0,"opacity":0.85}},
    {selector:'edge[ekind="route_axis"]',style:{"line-style":"dashed","line-dash-pattern":[10,5],"line-color":"#15B4C7","target-arrow-color":"#15B4C7","width":3.0,"opacity":0.85}},
    {selector:'edge[ekind="axis_onward"]',style:{"line-style":"solid","line-color":"#E8820C","target-arrow-color":"#E8820C","width":3.2,"opacity":0.9}},
    {selector:'edge[ekind="spec_attach"]',style:{"line-style":"dotted","line-color":"#cbb8e0","target-arrow-color":"#cbb8e0","width":1.4,"opacity":0.5,"arrow-scale":0.7}},
    {selector:'edge[ekind="declared_cond"]',style:{"line-style":"dashed","line-dash-pattern":[6,6],"line-color":"#9C6ADE","target-arrow-color":"#9C6ADE","width":2.4,"opacity":0.7}},
    {selector:'node[?spec_only]',style:{"border-style":"dashed","border-color":"#9C6ADE","border-width":2,"opacity":0.7}},
    {selector:'node[?dead]',style:{"opacity":0.45,"border-color":"#b0a0c8"}},
    {selector:'node[?group]',style:{"shape":"round-rectangle","background-color":"#e8f5e9","background-opacity":0.42,"border-color":"#2e7d32","border-width":2,"border-style":"solid","text-valign":"top","text-halign":"center","font-size":11,"font-weight":"bold","color":"#1b5e20","padding":"16px"}}
  ];
  try{ if(typeof cy!=="undefined" && typeof STYLE!=="undefined"){ cy.style().fromJson(STYLE.concat(V3_STYLE)).update(); } }
  catch(e){ console.warn("[pmx-dt v3] style 적용 실패:", e); }

  /* ---- 2c. 자동 경로 추적: declared_cond·spec_attach(미실현/미배선)는 union 제외 → 실선 정본 선로만 ---- */
  /* (v1 flowNeighborhood 동형 + filter 확장. highlight()가 전역 이름으로 호출 → 재대입 반영) */
  flowNeighborhood = function(node){
    var seen=node;
    ["down","up"].forEach(function(dir){
      var frontier=node, guard=0;
      while(frontier.nonempty() && guard++<300){
        var og=(dir==="down")?frontier.outgoers():frontier.incomers();
        var edges=og.edges('[ekind != "recover"][ekind != "declared_cond"][ekind != "spec_attach"]');
        var nodes=(dir==="down")?edges.targets():edges.sources();
        var fresh=nodes.difference(seen);
        seen=seen.union(edges).union(nodes);
        frontier=fresh;
      }
    });
    return seen;
  };

  /* ---- 노드 클릭 시 AUTO/REPAIR가 켜지면 🏁 그룹 라벨도 함께 강조 ---- */
  var _bHighlight = highlight;
  highlight = function(node){
    _bHighlight(node);
    try{
      var lit = cy.getElementById("AUTO").hasClass("hl") || cy.getElementById("REPAIR").hasClass("hl");
      if(lit){ var g=cy.getElementById("L0_group"); if(g && g.length){ g.removeClass("dim").addClass("hl"); } }
    }catch(e){}
  };

  /* ---- 2d. 패널: spec_only 배지 + 🏁 그룹 안내 (v2 renderCPanel은 CUNITS_EXTRA fallback로 65 c 이미 처리) ---- */
  var _v2RenderC = window.renderCPanel;
  window.renderCPanel = function(id){
    var n = (typeof cy!=="undefined") ? cy.getElementById(id) : null;
    if(n && n.length && n.data("kind")==="group_complete"){
      return '<div class="sect"><h3>🏁 nonmem-ready (L0) · 완성 종착</h3><div class="body">'
        +'<p class="easyexp">데이터가 여기까지 오면 NONMEM 분석에 <b>바로 쓸 수 있는 상태</b>예요. '
        +'정본 어휘로는 두 종착이 이 그룹에 들어갑니다 — '
        +'<b>AUTO</b>(손 안 대고 자동 완성) · <b>REPAIR</b>(조금 고쳐서 완성).</p>'
        +'<div class="kv">자동 완성 · <span class="pill pass">AUTO</span> &nbsp;·&nbsp; 고쳐서 완성 · <span class="pill pass">REPAIR</span></div>'
        +'</div></div>';
    }
    var html = _v2RenderC(id);
    if(n && n.length && n.data("spec_only")){
      var dead = n.data("dead");
      var badge = '<div class="spec-only-badge">정의됨 · 미구현 (spec_only) — 정본엔 정의됐지만 아직 런타임에 배선되지 않은 작업이에요'
        + (dead ? ' · ⚠ dead(어떤 시나리오 strand에도 안 쓰임)' : '') + '</div>';
      html = badge + html;
    }
    return html;
  };

  /* ---- 패널 제목도 정직하게 ---- */
  if(typeof titleFor!=="undefined"){
    var _v2TitleFor = titleFor;
    titleFor = function(node){
      var k=node.data("kind"), lbl=(node.data("label")||"").split("\n")[0];
      if(k==="group_complete") return "완성 종착 · " + lbl;
      if(node.data("spec_only")) return "정의됨·미구현 c · " + lbl;
      return _v2TitleFor(node);
    };
  }

  /* ---- 2 범례: v2 범례 보존 + v3 정본 흐름 항목 추가 ---- */
  try{
    var lg=document.getElementById("legend");
    if(lg){
      function v3lg(label, sw){ return '<span class="lg"><span class="sw" style="'+sw+'"></span>'+label+'</span>'; }
      lg.insertAdjacentHTML("beforeend",
        '<div class="legend-v3"><span class="v3h">v3 정본 흐름</span>'
        + v3lg("자동 정본 경로 → 🏁 (앰버 실선)", "background:#E8820C")
        + v3lg("질문(Q)·축 갈림길 (청록 점선)", "background:#15B4C7;border-style:dashed")
        + v3lg("선언만 됨·미실현 (보라 점선)", "background:#9C6ADE;border-style:dashed")
        + v3lg("정의됨·미구현 노드 (spec_only 65)", "background:#fff;border:2px dashed #9C6ADE")
        + v3lg("🏁 nonmem-ready(L0) 그룹 (AUTO·REPAIR)", "background:#e8f5e9;border:2px solid #2e7d32")
        + '</div>');
    }
  }catch(e){}

  /* ---- 현재 선택 노드가 있으면 v3 강조로 한번 다시 그림(그룹 라벨 반영) ---- */
  try{
    if(typeof state!=="undefined" && state && state.selected){
      var sn=cy.getElementById(state.selected);
      if(sn && sn.length){ try{ onNodeTap(sn); }catch(e){} }
    }
  }catch(e){}
})();
</script>
'''


# ═════════════════════════════════════════════════════════════════════════════
# 3. 조립 + 기록
# ═════════════════════════════════════════════════════════════════════════════
def page_head_v3():
    ph = V2.page_head_v2()                       # 이미 recolor + v2 CSS + 툴바 버튼 포함
    ph = ph.replace("(index v2)", "(index v3 · 정본 흐름)")   # title + h1 마커 동시 교체 → 'index v3'
    ph = ph.replace("</style>", _V3_CSS + "\n</style>")
    return ph


def app_js_v3():
    return V2.app_js_v2() + "\n" + _V3_OVERRIDE   # B.APP_JS(recolor)+_V2_OVERRIDE+_V3_OVERRIDE


def build_html() -> str:
    V2.assert_glossary_complete()                # v2 가드 재사용
    eles_v3 = _eles_v3()
    data_script = (
        "<script>\n"
        "var ELES=" + B.js(eles_v3) + ";\n"                  # ★ 확장 ELES_V3(B.ELES + v3 신규)
        "var CUNITS=" + B.js(B.CUNITS) + ";\n"
        "var CUNITS_EXTRA=" + B.js(V2.CUNITS_EXTRA) + ";\n"  # spec_only 65 = 작업카드 fallback
        "var QINFO=" + B.js(B.QINFO) + ";\n"
        "var NODEINFO=" + B.js(B.NODEINFO) + ";\n"
        "var AXIS_STATES=" + B.js(B.AXIS_STATES) + ";\n"
        "var FAMILIES=" + B.js(B.FAMILIES) + ";\n"
        "var DEFERRED_VIEW=" + B.js(B.DEFERRED_VIEW) + ";\n"
        "var DT_STATS=" + B.js(B.STATS) + ";\n"
        "var DT_BANNER=" + B.js(B.BANNER) + ";\n"
        "var WIZARD=" + B.js(V2.WIZARD) + ";\n"
        "var GLOSSARY=" + B.js(V2.GLOSSARY) + ";\n"
        "var EASY=" + B.js(V2.EASY) + ";\n"
        "var BACKBONE_ROUTING=" + B.js(BACKBONE_ROUTING) + ";\n"   # v3 정본(디버그·검증용)
        "var SPEC_ONLY=" + B.js(SPEC_ONLY) + ";\n"
        "</script>\n"
    )
    return page_head_v3() + "\n" + B.LIBS + "\n" + data_script + app_js_v3() + B.PAGE_TAIL


def main():
    html = build_html()
    out = B.ROOT / "render" / "index_v3.html"     # ★ index_v3.html만 기록(v1/v2 무변경)
    out.write_text(html, encoding="utf-8")
    kb = len(html.encode("utf-8")) / 1024.0
    eles = _eles_v3()
    n_nodes = sum(1 for e in eles if "source" not in e["data"])
    n_edges = sum(1 for e in eles if "source" in e["data"])
    from collections import Counter
    ek = Counter(e["data"].get("ekind") for e in eles if "source" in e["data"])
    print("[build_html_v3] wrote %s" % out)
    print("[build_html_v3] size = %.1f KB" % kb)
    print("[build_html_v3] graph: %d nodes + %d edges (v1 101 + spec_only 65 + 🏁 group 1 = %d node)" % (
        n_nodes, n_edges, n_nodes))
    print("[build_html_v3] new ekind: route_gate=%d route_axis=%d axis_onward=%d spec_attach=%d declared_cond=%d" % (
        ek.get("route_gate", 0), ek.get("route_axis", 0), ek.get("axis_onward", 0),
        ek.get("spec_attach", 0), ek.get("declared_cond", 0)))
    print("[build_html_v3] budget(render_budget_v3.collapsed_with_spec_only) = %s" % (
        B.STATS.get("render_budget_v3", {}).get("collapsed_with_spec_only")))


if __name__ == "__main__":
    main()
