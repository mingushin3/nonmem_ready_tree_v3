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
  .legend-v3 .lg.goal{background:#e8f5e9;border:1px solid #bcdfc0;border-radius:5px;padding:2px 7px;font-weight:700;color:#1b5e20}

  /* ════ index v3 — 블루프린트/엔지니어링 chrome (표현층 전용; 정본 색 의미 불변) ════
     · 캔버스 그래프 색(앰버 실선=자동 / 청록 점선=Q·축 / 보라=선언미실현 / 종착 6색 / 🏁 녹 / spec_only 보라점선)은
       이 블록에서 절대 바꾸지 않는다. chrome(상단바·패널·배경·타이포)의 분위기만 '청사진 제도지'로 통일. */
  :root{
    --bg:#e8eef4;          /* 쿨 페이퍼 (was #f6f8fa) */
    --line:#cdd8e2;         /* 연한 청회 룰 (was #d7dde3) */
    --accent:#1c6fb0;       /* 제도 cyan-blue (was #2f6fde) — tab active·링크 일괄 계승 */
    --bp-ink:#27435c;       /* 제도 잉크 */
    --bp-mono:"SFMono-Regular",Menlo,"JetBrains Mono",Consolas,monospace;
    --bp-elev:0 1px 2px rgba(20,42,66,.07), 0 1px 1px rgba(20,42,66,.05);
  }
  body{
    font-family:"Pretendard","Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",system-ui,-apple-system,"Segoe UI",sans-serif;
  }
  /* 청사진 그리드 backdrop — #cy는 frozen에서 background 無 → 캔버스 투명 사이로 비침. 순수 CSS·perf 0.
     (정직 트레이드오프: 컨테이너 고정 backdrop이라 줌/팬에 따라가지 않음 — 제도지 느낌·성능 우선) */
  #cy{
    background-color:#f3f7fb;
    background-image:
      linear-gradient(rgba(28,111,176,.055) 1px, transparent 1px),
      linear-gradient(90deg, rgba(28,111,176,.055) 1px, transparent 1px),
      linear-gradient(rgba(28,111,176,.11) 1px, transparent 1px),
      linear-gradient(90deg, rgba(28,111,176,.11) 1px, transparent 1px);
    background-size:24px 24px, 24px 24px, 120px 120px, 120px 120px;
    background-position:-1px -1px, -1px -1px, -1px -1px, -1px -1px;
  }
  /* 제도 헤더 */
  #topbar{background:linear-gradient(180deg,#e9f0f6,#dde7ef);border-bottom:1px solid #b7c5d2;box-shadow:var(--bp-elev)}
  #topbar h1{font-family:var(--bp-mono);font-size:15px;letter-spacing:.01em;color:var(--bp-ink)}
  #topbar .sub{color:#5b7387;letter-spacing:.01em}
  #breadcrumb{background:#f0f5fa;color:#46607a}
  #boundary{background:#f0f5fa}
  /* 기술 라벨은 mono — DOM 한정(캔버스 한글 라벨은 가독 CJK stack 유지) */
  #perfBadge{font-family:var(--bp-mono);box-shadow:var(--bp-elev)}
  .mono{font-family:var(--bp-mono)}
  /* 절제된 깊이감 — DOM 요소에만 soft elevation (캔버스 노드는 cytoscape core가 shadow 미지원) */
  .btn,.tab{border-radius:7px}
  .btn{box-shadow:var(--bp-elev);transition:box-shadow .12s ease, transform .12s ease}
  .btn:hover{box-shadow:0 3px 7px rgba(20,42,66,.14);transform:translateY(-1px)}
  #panel{box-shadow:-2px 0 10px rgba(20,42,66,.08)}
  .sect{box-shadow:var(--bp-elev);border-radius:7px;overflow:hidden;margin-bottom:9px}
  .sect>h3{background:#e7eef5;letter-spacing:.01em}
  #minimap{box-shadow:var(--bp-elev);border:1px solid #c3d0db !important}
  #zoombar .btn{box-shadow:var(--bp-elev)}
  /* 모달(진단 마법사·용어집·작업카드 122) 깊이감 — 런타임 삽입 박스 id */
  #wizBox,#glossBox,#cardBox{box-shadow:0 14px 40px rgba(20,42,66,.22) !important;border-radius:12px}
  /* spec_only 토글 버튼(런타임 DOM 삽입) — .btn 계승 + 펼침 상태 tint */
  #v3SpecToggle{font-weight:600}
  #v3SpecToggle.on{background:#eef7ff;border-color:#9fc5e8;color:#1c6fb0}

  /* (B) 마법사 진단 breadcrumb를 layer 띠로 그룹핑 — 최하층 검사(c0314 등)가 🏁 직전처럼 안 보이게 */
  .breadcrumb.v3banded{line-height:1.5}
  .breadcrumb.v3banded .pnode.start{display:inline-block;margin-bottom:4px}
  .bcband{margin:5px 0;padding:5px 8px 6px;border-left:3px solid #9fc5e8;background:#eef4fb;border-radius:0 6px 6px 0}
  .bcband.lowest{border-left-color:#e0a23c;background:#fbf4e8}   /* 최하층 강조 */
  .bcband-lab{font-size:10px;font-weight:700;color:#2f6fb0;font-family:var(--bp-mono);margin-bottom:4px;letter-spacing:.01em}
  .bcband.lowest .bcband-lab{color:#b3651a}
  .bcband-chips{display:flex;flex-wrap:wrap;gap:5px;align-items:center}
  .bcband-note{margin-top:6px;font-size:10px;color:#6b7785;line-height:1.5}
"""

# 색: 앰버 #E8820C(자동 실선) · 청록 #15B4C7(질문 점선) · 보라 #9C6ADE(선언·미실현).
# ★ recolor()를 거치지 않으므로 최종 색을 직접 기입(의도된 표현층 색).
_V3_OVERRIDE = r'''<script>
/* ===== index v3 override: 정본 흐름(backbone_routing·spec_only) 위에 v2를 그대로 계승 ===== */
(function(){
  /* ---- 0. 레이아웃 재튜닝(★ 세로 길쭉 해소): 전역 layoutOpts 재대입.
       B의 layoutOpts(build_html.py:587)를 이름으로 호출하는 모든 곳(runInitialLayout·expandAxis·collapseAxis·reset)이
       이 정의를 자동 계승. rankDir 'LR' 유지(이미 가로) — rank 내 세로 간격(nodeSep)을 줄이고 rank 간 가로 간격(rankSep)을
       늘려 wide-and-short. tight-tree = 백본-스파인 우세 DAG에 가장 compact(fallback: network-simplex). */
  try{
    if(typeof layoutOpts!=="undefined"){
      layoutOpts = function(extra){
        return Object.assign({
          name:(typeof dagreOK!=="undefined" && dagreOK)?"dagre":"breadthfirst",
          rankDir:"LR", directed:true, fit:true, padding:28, animate:false,
          nodeSep:20, rankSep:78, edgeSep:12, ranker:"tight-tree", spacingFactor:0.9
        }, extra||{});
      };
    }
  }catch(e){ console.warn("[pmx-dt v3] layoutOpts override 실패:", e); }

  /* ---- 2a. 신규 ekind/node 스타일을 STYLE에 덧대고 재적용 (cy는 이미 생성됨) ---- */
  var V3_STYLE=[
    {selector:'edge[ekind="route_gate"]',style:{"line-style":"dashed","line-dash-pattern":[10,5],"line-color":"#15B4C7","target-arrow-color":"#15B4C7","width":3.0,"opacity":0.85}},
    {selector:'edge[ekind="route_axis"]',style:{"line-style":"dashed","line-dash-pattern":[10,5],"line-color":"#15B4C7","target-arrow-color":"#15B4C7","width":3.0,"opacity":0.85}},
    {selector:'edge[ekind="axis_onward"]',style:{"line-style":"solid","line-color":"#E8820C","target-arrow-color":"#E8820C","width":3.2,"opacity":0.9}},
    {selector:'edge[ekind="spec_attach"]',style:{"line-style":"dotted","line-color":"#cbb8e0","target-arrow-color":"#cbb8e0","width":1.4,"opacity":0.5,"arrow-scale":0.7}},
    {selector:'edge[ekind="declared_cond"]',style:{"line-style":"dashed","line-dash-pattern":[6,6],"line-color":"#9C6ADE","target-arrow-color":"#9C6ADE","width":2.4,"opacity":0.7}},
    {selector:'node[?spec_only]',style:{"border-style":"dashed","border-color":"#9C6ADE","border-width":2,"opacity":0.7}},
    {selector:'node[?dead]',style:{"opacity":0.45,"border-color":"#b0a0c8"}},
    {selector:'node[?group]',style:{"shape":"round-rectangle","background-color":"#e8f5e9","background-opacity":0.5,"border-color":"#2e7d32","border-width":3,"border-style":"solid","text-valign":"top","text-halign":"center","font-size":13,"font-weight":"bold","color":"#1b5e20","padding":"18px","text-margin-y":-2}},
    /* 🏁 종착(AUTO/REPAIR)에 옅은 녹 외곽선 — 자동경로의 목표임을 시각 강조(정본 채움색 불변) */
    {selector:'node[kind="terminal_auto"]',style:{"border-width":3}},
    {selector:'node[kind="terminal_repair"]',style:{"border-width":3}}
  ];
  try{ if(typeof cy!=="undefined" && typeof STYLE!=="undefined"){ cy.style().fromJson(STYLE.concat(V3_STYLE)).update(); } }
  catch(e){ console.warn("[pmx-dt v3] style 적용 실패:", e); }

  /* ---- 2b. spec_only 65 기본 collapse + 토글(★ 세로 길쭉 해소의 본체) ----
     display:none 토글(reversible·ELES 불변 → 167노드 구조 테스트 green; dagre가 display:none 노드를 레이아웃서 제외 →
     stage:L-4->L-5의 47-노드 기둥 소멸). hide 대상 = spec_only 노드 ∪ spec_attach 엣지 ∪ declared_cond 엣지
     (declared_cond는 실↔실도 있어 엣지셋 명시 토글=멱등). 선호는 v3 전용 LS 키(frozen pmx_dt_state 비건드림).
     최초(키 null)=hidden(기본 접힘). 펼치면 spec_only 클릭 가능 자동 복원(renderCPanel spec_only 배지 래퍼 그대로). */
  var V3_LS="pmx_dt_v3_specHidden";
  function v3IsSpecHidden(){ try{ var v=localStorage.getItem(V3_LS); return v===null ? true : v==="1"; }catch(e){ return true; } }
  function v3SetSpecHidden(h){ try{ localStorage.setItem(V3_LS, h?"1":"0"); }catch(e){} }
  function v3SpecSet(){
    return cy.nodes('[?spec_only]').union(cy.edges('[ekind="spec_attach"]')).union(cy.edges('[ekind="declared_cond"]'));
  }
  function applySpecOnlyVisibility(hidden){
    try{ v3SpecSet().style("display", hidden?"none":"element"); }
    catch(e){ console.warn("[pmx-dt v3] spec 가시성 적용 실패:", e); }
  }
  function updateSpecToggleLabel(){
    var b=document.getElementById("v3SpecToggle"); if(!b) return;
    var hidden=v3IsSpecHidden();
    b.textContent = hidden ? "⊕ 미구현 65 보기" : "⊖ 미구현 65 숨기기";
    b.title = hidden ? "정의됨·미구현(spec_only) 65 노드를 펼쳐 봅니다(클릭 가능)"
                     : "spec_only 65 노드를 다시 숨겨 화면을 정돈합니다";
    if(hidden){ b.classList.remove("on"); } else { b.classList.add("on"); }
  }
  function insertSpecToggle(){
    var anchor=document.getElementById("perfBadge");
    if(!anchor || document.getElementById("v3SpecToggle")) return;   // 멱등 가드
    anchor.insertAdjacentHTML("beforebegin",'<button class="btn" id="v3SpecToggle" type="button"></button>');
    var b=document.getElementById("v3SpecToggle");
    b.addEventListener("click", function(){
      var nowHidden = !v3IsSpecHidden();
      v3SetSpecHidden(nowHidden);
      applySpecOnlyVisibility(nowHidden);
      relayoutV3();
      updateSpecToggleLabel();
    });
    updateSpecToggleLabel();
  }
  /* 단일 재레이아웃: runInitialLayout이 구 파라미터로 이미 1회 돌았으므로 v3가 1회 재실행(collapsed·tight-tree·animate:false). */
  function relayoutV3(){
    if(typeof cy==="undefined") return;
    try{
      var t0v3=(window.performance&&performance.now)?performance.now():0;
      var L=cy.layout(layoutOpts());
      L.one("layoutstop", function(){
        try{ cy.fit(undefined,28); }catch(_){}
        if(typeof drawMinimap==="function"){ try{ drawMinimap(); }catch(_){} }   // 미니맵 동기화
        var dt=Math.round(((window.performance&&performance.now)?performance.now():0)-t0v3);
        if(window.__PERF__){                                                      // perf 배지 정직 갱신(t_total 미덮어씀)
          window.__PERF__.visibleNodes=cy.nodes(":visible").length;
          window.__PERF__.t_v3relayout=dt;
          if(typeof setPerfBadge==="function"){ try{ setPerfBadge(); }catch(_){} }
        }
        /* 초기 t_total(전체 빌드+레이아웃 실측)에 v3 재레이아웃 추가분을 정직하게 덧붙임(날조 0) */
        try{ var b=document.getElementById("perfBadge"); if(b){ b.textContent=b.textContent+" · v3 +"+dt+" ms"; } }catch(_){}
      });
      L.run();
    }catch(e){ console.warn("[pmx-dt v3] relayout 실패:", e); }
  }

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
      function v3lg(label, sw, cls){ return '<span class="lg '+(cls||"")+'"><span class="sw" style="'+sw+'"></span>'+label+'</span>'; }
      lg.insertAdjacentHTML("beforeend",
        '<div class="legend-v3"><span class="v3h">v3 정본 흐름</span>'
        + v3lg("자동 정본 경로 → 🏁 (앰버 실선)", "background:#E8820C")
        + v3lg("질문(Q)·축 갈림길 (청록 점선)", "background:#15B4C7;border-style:dashed")
        + v3lg("선언만 됨·미실현 (보라 점선)", "background:#9C6ADE;border-style:dashed")
        + v3lg("정의됨·미구현 노드 (spec_only 65)", "background:#fff;border:2px dashed #9C6ADE")
        + v3lg("🏁 nonmem-ready(L0) 그룹 (AUTO·REPAIR)", "background:#e8f5e9;border:2px solid #2e7d32", "goal")
        + '</div>');
    }
  }catch(e){}

  /* ---- 2f. (B) 마법사 진단 breadcrumb를 layer 띠로 그룹핑 ----
     c0314(DETECT TIME_ANCHOR, layer L-4→L-5)처럼 '최하층' 검사가 정규형 정렬상 마지막에 와서 🏁 직전처럼
     보이는 오해를 없앤다. pathBreadcrumb은 wizard IIFE 내부(private)라 재대입 불가 → 렌더된 .breadcrumb를
     DOM 후처리로 재구성. ★ 칩(.cchip)은 새로 만들지 않고 그대로 '이동'(appendChild) → V2가 붙인 onclick 보존
     (V2는 innerHTML 직후 동기로 onclick 부착; 본 observer는 그 뒤 microtask에 돎). */
  function v3LayerOf(cid){
    var c=(window.CUNITS&&CUNITS[cid])||(window.CUNITS_EXTRA&&CUNITS_EXTRA[cid])||null;
    return (c&&c.layer_pair)?c.layer_pair:"";
  }
  var V3_LAYER_LABEL={
    "L-4->L-5":"L-4↔L-5 · 표기 정규화 (최하층 — 토큰 청소)",
    "L-3->L-4":"L-3↔L-4 · 축(A0–A10) 평가 보조",
    "L-2->L-3":"L-2↔L-3 · 구조 변형",
    "L-1->L-2":"L-1↔L-2 · tidy 구성",
    "L0->L-1":"L0↔L-1 · NONMEM 열 생성"
  };
  function v3LayerKey(lp){ var ns=(String(lp).match(/-?\d+/g)||[]).map(Number); return ns.length?Math.min.apply(null,ns):0; }
  function v3RebandBreadcrumb(bc){
    if(!bc || bc.getAttribute("data-v3band")) return;
    var chips=[].slice.call(bc.querySelectorAll(".cchip"));
    if(!chips.length){ bc.setAttribute("data-v3band","1"); return; }
    var start=bc.querySelector(".pnode.start"), goal=bc.querySelector(".pnode.goal");
    var order=[], groups={};
    chips.forEach(function(ch){
      var lp=v3LayerOf(ch.getAttribute("data-node"))||"기타";
      if(!groups[lp]){ groups[lp]=[]; order.push(lp); }
      groups[lp].push(ch);
    });
    order.sort(function(a,b){ return v3LayerKey(a)-v3LayerKey(b); });   // 최하층(더 음수) 먼저 = 데이터 흐름 L-5→…→L0
    var lowest=order.length?order[0]:null;
    bc.setAttribute("data-v3band","1"); bc.classList.add("v3banded");
    bc.innerHTML="";                                                    // 칩 참조는 위에서 보유 → 이동(onclick 보존)
    if(start) bc.appendChild(start);
    order.forEach(function(lp){
      var band=document.createElement("div"); band.className="bcband"+(lp===lowest?" lowest":"");
      var lab=document.createElement("div"); lab.className="bcband-lab"; lab.textContent=(V3_LAYER_LABEL[lp]||lp);
      band.appendChild(lab);
      var row=document.createElement("div"); row.className="bcband-chips";
      groups[lp].forEach(function(ch){ row.appendChild(ch); });        // 원본 칩 이동
      band.appendChild(row); bc.appendChild(band);
    });
    if(goal) bc.appendChild(goal);
    var note=document.createElement("div"); note.className="bcband-note";
    note.textContent="※ 위는 실행 순서가 아니라 layer별 진단 체크리스트예요(같은 띠 안은 순서 무관). 🏁는 최종 목표. 예: TIME_ANCHOR 검사(c0314)는 최하층(L-4↔L-5)이라 맨 위 띠에 있어요.";
    bc.appendChild(note);
  }
  function v3RebandAll(){
    try{ [].forEach.call(document.querySelectorAll(".breadcrumb:not([data-v3band])"), v3RebandBreadcrumb); }
    catch(e){ console.warn("[pmx-dt v3] breadcrumb 띠 재구성 실패:", e); }
  }
  try{
    if(window.MutationObserver){
      var v3mo=new MutationObserver(function(){ v3RebandAll(); });
      v3mo.observe(document.body, {childList:true, subtree:true});
    }
    v3RebandAll();   // 이미 떠 있는 breadcrumb 즉시 처리
  }catch(e){ console.warn("[pmx-dt v3] breadcrumb observer 실패:", e); }

  /* ---- 2e. 초기 적용(★): 토글 삽입 + 기본 접힘(spec_only 65 숨김) + 단일 재레이아웃 ---- */
  try{
    insertSpecToggle();
    applySpecOnlyVisibility(v3IsSpecHidden());   // 최초 = hidden(기본 접힘)
    relayoutV3();
  }catch(e){ console.warn("[pmx-dt v3] 초기 collapse/relayout 실패:", e); }

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
