"""render/build_slice4.py — Phase 5 slice 4 부분 tree 렌더 빌더 (COVARIATE_LAYOUT family).

★ GAP-25 결정: Phase 8 렌더 정본 = inline(spike_interaction.html 방식). slice1의 CDN 답습 금지.
build_slice3.py와 동일하게 spike_interaction.html의 inline 라이브러리 3블록(cytoscape 3.30.2 +
dagre 0.8.5 + cytoscape-dagre 2.5.0)을 추출해 오프라인 단일 HTML(render/slice4_covariate.html)을
생성한다. decision_tree.json 부재(Phase 7 미완)이므로 c_units.json 사실 기반으로 직접 구성.

정본 idiom 재사용: N()/E() 헬퍼, kind별 STYLE, dagre LR layout, buildBackbone()/applyHighlight()/
onNodeTap(), upstream∪downstream 하이라이트(Lock 7), localStorage graceful fallback.

표시(★ slice 4 = COVARIATE_LAYOUT mess + 기구현 자산 활성화): COVARIATE_LAYOUT 쌍(c0380 DETECT →
c0381 CLASSIFY)을 강조(주황)하고, 그 산출 cov_layout이 backbone(A7 axis c0207)을 지나 기구현
c0121(PIVOT, L-2->L-3, 초록=활성화)을 실제로 구동하는 **활성화 chain**을 함께 그린다. c0380→c0121
점선(주황) = GAP-16 실효 detection(분기키 cov_layout 생산자는 c0207이 아니라 c0380). COVARIATE_LAYOUT
쌍은 can_route_to_q=[] → Q-terminal 노드/패널 없음(D-S4 무기여). c0381 postcond는 vacuous-flag(GAP-27)
— 패널에 명시 표기.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPIKE = (ROOT / "render" / "spike_interaction.html").read_text(encoding="utf-8")


def extract_inline_libs(spike: str) -> str:
    """spike의 inline cytoscape/dagre/cytoscape-dagre <script> 3블록을 추출(GAP-25 정본)."""
    start = spike.index("<script>/*! inlined: cytoscape 3.30.2")
    cd = spike.index("/*! inlined: cytoscape-dagre")
    end = spike.index("</script>", cd) + len("</script>")
    return spike[start:end]


LIBS = extract_inline_libs(SPIKE)

PAGE_HEAD = """<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>pmx-dt · Phase 5 slice 4 — COVARIATE_LAYOUT family 부분 tree</title>
<!-- Lock 6: Cytoscape.js + dagre, 단일 HTML, ★ inline(offline) — GAP-25 정본(slice1 CDN 답습 금지). -->
<style>
  :root{ --hl:#FFD700; --hl-cond:#FFF8B0; --slice:#ff8f3f; --act:#2e7d32; }
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;color:#16314f}
  header{padding:8px 14px;border-bottom:1px solid #dde;background:#f7f9ff}
  header h1{font-size:15px;margin:0 0 3px}
  header .sub{font-size:12px;color:#5b6b82}
  #libok{font-size:12px;font-weight:700;color:#2e7d32;margin-top:4px}
  #wrap{display:flex;height:calc(100vh - 132px);min-height:420px}
  #cy{flex:1;background:#fbfcff;border-right:1px solid #e5e9f2}
  #panel{width:390px;overflow:auto;padding:10px 12px;font-size:13px;background:#fff}
  #panel .ph{color:#8a97aa;font-size:12px;margin-top:8px}
  .sect{border:1px solid #e5e9f2;border-radius:8px;margin:8px 0;overflow:hidden}
  .sect h3{margin:0;padding:6px 9px;background:#eef3ff;font-size:12px;border-bottom:1px solid #e5e9f2}
  .sect .body{padding:8px 9px}
  .kv{margin:3px 0;font-size:12.5px}
  .k{color:#7385a0}
  .mono{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:11.5px;background:#f1f4fb;padding:1px 4px;border-radius:4px}
  pre.pc{white-space:pre-wrap;word-break:break-word;background:#0f1b2d;color:#d6e4ff;padding:8px;border-radius:6px;font-size:11px;margin:4px 0}
  .pill{display:inline-block;padding:1px 7px;border-radius:10px;font-size:11px;background:#eef;margin:1px 2px}
  .pill.pass{background:#e6f4ea;color:#1e7a37}
  .pill.q{background:#fdecea;color:#b71c1c}
  .pill.slice{background:#fff0e3;color:#b35a16}
  .pill.act{background:#e6f4ea;color:#1e7a37}
  .warn{color:#8a5a00;font-size:12px;margin:3px 0}
  #legend{padding:6px 14px;border-top:1px solid #dde;background:#f7f9ff;font-size:11.5px;display:flex;flex-wrap:wrap;gap:12px;align-items:center}
  .lg{display:inline-flex;align-items:center;gap:5px}
  .sw{display:inline-block;width:14px;height:14px;border:1.5px solid #3f78d6;background:#cfe0ff}
</style>
</head>
<body>
<header>
  <h1>Phase 5 · slice 4 — COVARIATE_LAYOUT family 부분 decision tree</h1>
  <div class="sub"><b>c0380 DETECT → c0381 CLASSIFY</b>(주황=이번 슬라이스) 산출 <span class="mono">cov_layout</span>이 A7 axis(c0207) 경유 기구현 <b>c0121 PIVOT</b>(초록=활성화)을 구동 — 점선=GAP-16 실효 detection. COVARIATE_LAYOUT은 Q-code 없음(can_route_to_q=[]). 라이브러리=inline(offline, GAP-25).</div>
  <div id="libok">로드 확인 중…</div>
</header>
<div id="wrap">
  <div id="cy"></div>
  <div id="panel"><div class="ph">노드를 클릭하면 c-단위체 정보(4섹션)가 표시됩니다.</div></div>
</div>
<div id="legend">
  <span class="lg"><span class="sw" style="border-radius:50%;background:#bcd9ff;border-style:dashed"></span>detect(점선원)</span>
  <span class="lg"><span class="sw" style="border-radius:50%;background:#7fb2ff"></span>transform(원)</span>
  <span class="lg"><span class="sw" style="background:#cde8d4;border-color:#4c9a68;border-radius:7px"></span>backbone 진입(merge)</span>
  <span class="lg"><span class="sw" style="background:var(--slice);border-color:#b35a16"></span>이번 슬라이스(c0380/c0381)</span>
  <span class="lg"><span class="sw" style="border-radius:50%;background:#a5d6a7;border-color:var(--act)"></span>활성화(c0121)</span>
  <span class="lg"><span class="sw" style="background:var(--hl)"></span>단일 경로 5px</span>
</div>
"""

APP_SCRIPT = r"""<script>
"use strict";
function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}

var dagreOK=false;
try{ if(window.cytoscapeDagre){ cytoscape.use(window.cytoscapeDagre); dagreOK=true; } }catch(e){ dagreOK=false; }
document.getElementById("libok").textContent =
  (typeof cytoscape!=="undefined")
    ? ("✅ inline cytoscape 3.30.2 " + (dagreOK ? "+ dagre 0.8.5 등록됨 (offline)" : "(dagre 미등록 — breadthfirst fallback)"))
    : "⚠ cytoscape 로드 실패";

/* localStorage (graceful fallback) */
var LS_KEY="pmx_dt_slice4_state";
var state={selected:null};
try{ var raw=localStorage.getItem(LS_KEY); if(raw){ state=Object.assign(state, JSON.parse(raw)||{}); } }
catch(e){ try{ localStorage.removeItem(LS_KEY); }catch(_){ } }
function saveState(){ try{ localStorage.setItem(LS_KEY, JSON.stringify(state)); }catch(e){ } }

/* ---- 데이터 (verbatim from spec/c_units.json) ---- */
var CUNITS={
  c0380:{c_id:"c0380",c_name_ko:"공변량 레이아웃 감지",srp_intent:"DETECT COVARIATE_LAYOUT",kind:"detect",cost:1,requires_detection_by:null,layer:"L-4->L-5",slice:true,
    postcond:"meta.get('cov_layout') in ['wide', 'long', 'none']",can_route_to_q:[],
    vv:{target_columns:["covariate columns"],criterion_predicate_ko:"공변량 레이아웃 타입이 식별됨",pass_route_to:"c0381",fail_route_to:null},
    note:"분기키 cov_layout(∈{wide,long,none}) 생산자. c0121 PIVOT의 실효 detection(GAP-16) — c0207은 a7_state만 emit.",ref:"universe_sm §6 COVARIATE_LAYOUT"},
  c0381:{c_id:"c0381",c_name_ko:"공변량 레이아웃 분류",srp_intent:"CLASSIFY COVARIATE_LAYOUT",kind:"detect",cost:3,requires_detection_by:"c0380",layer:"L-4->L-5",slice:true,
    postcond:"meta.get('cov_layout_classified', False)",can_route_to_q:[],vv:null,
    note:"★ postcond는 단순 flag(default=False). cov_layout(c0380 산출) 없이 flag=True면 vacuous classification(GAP-27). spec frozen — 구현이 detection 산출에 gate(부재/무효→success=False·route_to_q=None·flag 미설정).",ref:"universe_sm §6 COVARIATE_LAYOUT"},
  c0207:{c_id:"c0207",c_name_ko:"A7 공변량 부착 평가",srp_intent:"CLASSIFY COVARIATE_LAYOUT",kind:"detect",cost:3,requires_detection_by:null,layer:"L-3->L-4",
    postcond:"meta.get('a7_state') in ['NONE-REQUIRED','BASELINE-CLEAN','BASELINE-IMPUTABLE','TIME-VARYING','EXTERNAL-JOIN','PEDIATRIC-MATURATION','KEY-MISSING','POLICY-MISSING']",can_route_to_q:["Q07","Q13"],
    vv:{target_columns:["covariate columns"],criterion_predicate_ko:"공변량 부착 전략이 8개 state 중 하나로 결정됨",pass_route_to:"c0208",fail_route_to:"Q07"},
    note:"A7 axis 평가 — a7_state 생산(≠cov_layout). c0121의 명목 requires_detection_by이나 분기키 cov_layout은 미생산(GAP-16).",ref:"universe_sm §2 N6, §3 A7"},
  c0121:{c_id:"c0121",c_name_ko:"공변량 레이아웃 변환",srp_intent:"PIVOT COVARIATE_LAYOUT",kind:"transform",cost:4,requires_detection_by:"c0207",layer:"L-2->L-3",activated:true,
    postcond:"all(df[col].apply(lambda x: not isinstance(x, (list, dict))).all() for col in meta.get('covariate_columns', []))",can_route_to_q:[],vv:null,
    note:"★ 활성화(slice 4): 분기키 cov_layout은 c0380이 생산(c0207 아님). cov_layout='wide'면 wide→long pivot, 부재면 success=False(silent no-op 금지). 기구현 휴면 자산이 c0380 배선으로 구동됨.",ref:"universe_sm §6 COVARIATE_LAYOUT, §3 A7"}
};

/* ---- elements: COVARIATE_LAYOUT mess 쌍 → backbone(A7) → c0121 활성화 chain ---- */
function N(id,kind,label,slice,activated){return {data:{id:id,kind:kind,label:label,slice:!!slice,activated:!!activated}};}
function E(id,s,t){return {data:{id:id,source:s,target:t}};}
function ED(id,s,t,label){return {data:{id:id,source:s,target:t,dataflow:true,label:label}};}
var ELES=[
  N("c0380","detect","c0380\nDETECT COVARIATE_LAYOUT",true),
  N("c0381","detect","c0381\nCLASSIFY COVARIATE_LAYOUT",true),
  N("backbone","merge","backbone\n(N0–N7 / axis 평가 진입)"),
  N("c0207","detect","c0207\nA7 CLASSIFY COVARIATE_LAYOUT"),
  N("c0121","transform","c0121\nPIVOT COVARIATE_LAYOUT",false,true),
  /* detect → classify (D-S1: c0381 reqdet=c0380 cut-vertex) */
  E("e_380_381","c0380","c0381"),
  /* mess 정규화 → backbone(axis) 수렴 (D-S3: mess가 backbone 앞단) */
  E("e_381_bb","c0381","backbone"),
  /* backbone → A7 axis → c0121 PIVOT (활성화 chain; c0121 reqdet=c0207 D-S1) */
  E("e_bb_207","backbone","c0207"),
  E("e_207_121","c0207","c0121"),
  /* ★ GAP-16 실효 detection: cov_layout 데이터플로우(c0380 → c0121 분기키) */
  ED("e_380_121","c0380","c0121","cov_layout")
];

var STYLE=[
  {selector:"node",style:{"label":"data(label)","text-wrap":"wrap","text-valign":"center","text-halign":"center",
    "font-size":9,"text-max-width":120,"width":96,"height":44,"background-color":"#cfe0ff",
    "border-width":1,"border-color":"#5b8def","color":"#16314f","overlay-opacity":0,"overlay-color":"#FFD700","overlay-padding":10}},
  {selector:'node[kind="transform"]',style:{"shape":"ellipse","background-color":"#7fb2ff","border-color":"#3f78d6"}},
  {selector:'node[kind="detect"]',style:{"shape":"ellipse","background-color":"#bcd9ff","border-style":"dashed","border-width":2,"border-color":"#3f78d6"}},
  {selector:'node[kind="merge"]',style:{"shape":"round-rectangle","background-color":"#cde8d4","border-color":"#4c9a68","width":150,"height":48}},
  {selector:'node[?slice]',style:{"background-color":"#ff8f3f","border-color":"#b35a16","border-width":3,"color":"#3a1c06"}},
  {selector:'node[?activated]',style:{"background-color":"#a5d6a7","border-color":"#2e7d32","border-width":4,"color":"#10340f"}},
  {selector:"edge",style:{"width":2,"line-color":"#9e9e9e","target-arrow-color":"#9e9e9e","target-arrow-shape":"triangle","curve-style":"bezier","arrow-scale":0.9}},
  {selector:'edge[?dataflow]',style:{"line-style":"dashed","line-color":"#ff8f3f","target-arrow-color":"#ff8f3f","width":2.5,
    "label":"data(label)","font-size":8,"color":"#b35a16","text-background-color":"#fff","text-background-opacity":0.85,"text-background-padding":2,
    "curve-style":"unbundled-bezier","control-point-distances":[-46],"control-point-weights":[0.5]}},
  {selector:".dim",style:{"opacity":0.22}},
  {selector:"node.hl",style:{"border-width":3,"border-color":"#FFD700"}},
  {selector:"edge.hlSingle",style:{"line-color":"#FFD700","target-arrow-color":"#FFD700","width":5,"line-style":"solid","z-index":900,"opacity":1}},
  {selector:"node.current",style:{"border-width":4,"border-color":"#111","z-index":9999,"opacity":1}}
];

function layoutOpts(){ return {name:(dagreOK?"dagre":"breadthfirst"),rankDir:"LR",directed:true,fit:true,padding:30,animate:false,nodeSep:44,rankSep:104,spacingFactor:1.0}; }

var PLACEHOLDER='<div class="ph">노드를 클릭하면 c-단위체 정보(4섹션)가 표시됩니다.</div>';
var cy;

/* ★ buildBackbone — 정본 idiom 재사용 */
function buildBackbone(){
  cy=cytoscape({container:document.getElementById("cy"),elements:ELES,style:STYLE,layout:layoutOpts(),
    wheelSensitivity:0.2,minZoom:0.2,maxZoom:2.6});
  cy.ready(function(){ cy.fit(undefined,30); });
  cy.on("tap","node",function(evt){ onNodeTap(evt.target); });
  cy.on("tap",function(evt){ if(evt.target===cy){ clearSel(); } });
}

/* ★ applyHighlight — upstream backtrace ∪ downstream BFS (Lock 7) */
function clearHighlight(){ cy.elements().removeClass("dim hl hlSingle current"); cy.nodes().style("overlay-opacity",0); }
function applyHighlight(node){
  clearHighlight();
  var hl=node.successors().union(node.predecessors()).union(node);
  cy.elements().addClass("dim"); hl.removeClass("dim");
  hl.nodes().addClass("hl");
  hl.edges().forEach(function(e){ e.addClass("hlSingle"); });
  node.removeClass("hl dim").addClass("current");
}
function clearSel(){ state.selected=null; saveState(); if(cy) clearHighlight(); document.getElementById("panel").innerHTML=PLACEHOLDER; }

/* ★ onNodeTap — dispatch + panel */
function onNodeTap(node){
  var id=node.id();
  state.selected=id; saveState();
  applyHighlight(node);
  document.getElementById("panel").innerHTML = (id==="backbone") ? renderBackbonePanel() : renderCPanel(id);
}

function routeRow(arr){ return (arr&&arr.length) ? arr.map(function(q){return '<span class="pill q">'+esc(q)+'</span>';}).join("") : '<span class="pill">없음</span>'; }

function renderCPanel(id){
  var c=CUNITS[id]; if(!c) return '<div class="sect"><div class="body"><b>'+esc(id)+'</b></div></div>';
  var tag=(c.slice?' <span class="pill slice">slice 4</span>':'')+(c.activated?' <span class="pill act">활성화</span>':'');
  var h='<div class="sect"><h3>(A) Identity'+tag+'</h3><div class="body">';
  h+='<div class="kv"><span class="k">c_name_ko</span> · <b>'+esc(c.c_name_ko)+'</b></div>';
  h+='<div class="kv"><span class="k">srp_intent</span> · <span class="mono">'+esc(c.srp_intent)+'</span></div>';
  h+='<div class="kv"><span class="k">kind</span> '+esc(c.kind)+' · <span class="k">cost</span> '+c.cost+' · <span class="k">layer</span> '+esc(c.layer)+'</div>';
  h+='<div class="kv"><span class="k">requires_detection_by</span> <b>'+esc(c.requires_detection_by||"null")+'</b> · <span class="k">c_id</span> '+esc(c.c_id)+'</div>';
  h+='<div class="kv"><span class="k">can_route_to_q</span> '+routeRow(c.can_route_to_q)+'</div>';
  if(c.note){ h+='<div class="warn">'+esc(c.note)+'</div>'; }
  h+='</div></div>';
  h+='<div class="sect"><h3>(B) postcondition_predicate</h3><div class="body"><pre class="pc">'+esc(c.postcond)+'</pre></div></div>';
  if(c.kind==="transform"){
    h+='<div class="sect"><h3>(C) routing</h3><div class="body"><div class="kv">fail → '+routeRow(c.can_route_to_q)+'</div></div></div>';
  }else{
    h+='<div class="sect"><h3>(C) verify_visualization</h3><div class="body">'+renderVV(c.vv)+'</div></div>';
  }
  h+='<div class="sect"><h3>(D) ref</h3><div class="body"><span class="mono">'+esc(c.ref)+'</span></div></div>';
  return h;
}
function renderVV(vv){
  if(!vv) return '<i>(verify_visualization 없음)</i>';
  var h='<div class="kv"><span class="k">target_columns</span> '+(vv.target_columns||[]).map(function(x){return '<span class="pill">'+esc(x)+'</span>';}).join("")+'</div>';
  h+='<div class="kv"><span class="k">criterion</span> '+esc(vv.criterion_predicate_ko)+'</div>';
  h+='<div class="kv"><span class="k">pass →</span> <span class="pill pass">'+esc(vv.pass_route_to||"next")+'</span></div>';
  h+='<div class="kv"><span class="k">fail →</span> '+(vv.fail_route_to?'<span class="pill q">'+esc(vv.fail_route_to)+'</span>':'<span class="pill">없음</span>')+'</div>';
  return h;
}
function renderBackbonePanel(){
  var h='<div class="sect"><h3>backbone 진입 (merge)</h3><div class="body">';
  h+='<div class="kv">N1 역할: L-4→L-5 mess normalization 완료 후 <b>N0–N7 backbone / A0–A10 axis 평가</b> 진입점.</div>';
  h+='<div class="kv">N2 수렴: COVARIATE_LAYOUT mess 쌍(c0380/c0381)이 이 노드 앞에서 종료(D-S3: mess가 backbone 앞단). 이후 A7 axis(c0207) → c0121 PIVOT(L-2→L-3).</div>';
  h+='<div class="kv">N3 기여 strand: COVARIATE_LAYOUT 감지 <b>534</b>(c0380/c0381 freq), 그중 wide pivot(c0121) <b>6</b>. can_route_to_q=[] → 고립 Q-terminal 무기여(D-S4).</div>';
  h+='</div></div>';
  return h;
}

buildBackbone();
/* localStorage 복원: 이전 선택 노드 재하이라이트 */
if(state.selected && cy.getElementById(state.selected).length){ onNodeTap(cy.getElementById(state.selected)); }
</script>
</body>
</html>
"""

HTML = PAGE_HEAD + "\n" + LIBS + "\n" + APP_SCRIPT
OUT = ROOT / "render" / "slice4_covariate.html"
OUT.write_text(HTML, encoding="utf-8")
print("wrote", OUT, "(" + str(round(len(HTML) / 1024)) + " KB, inline libs " + str(round(len(LIBS) / 1024)) + " KB)")
