"""render/build_slice2.py — Phase 5 slice 2 부분 tree 렌더 빌더.

★ GAP-25 결정: Phase 8 렌더 정본 = inline(spike_interaction.html 방식). slice1의 CDN 답습 금지.
이 빌더는 spike_interaction.html의 inline 라이브러리 블록(cytoscape 3.30.2 + dagre 0.8.5 +
cytoscape-dagre 2.5.0, <script>×3)을 추출해 slice-2 TIME 부분 tree 앱과 결합, 오프라인 단일
HTML(render/slice2_time.html)을 생성한다. decision_tree.json 부재(Phase 7 미완)이므로
c_units.json/strands.json 사실에 기반해 TIME backbone을 직접 구성한다.

정본 idiom 재사용: N()/E() element 헬퍼, kind별 STYLE(transform=원/detect·verify=점선원/
conditional=육각/terminal_q=빨강사각), dagre LR layout, buildBackbone()/applyHighlight()/
onNodeTap(), upstream∪downstream 하이라이트(Lock 7), localStorage graceful fallback.

표시: TIME 생산 chain(c0310/c0311 FORMAT, c0314/c0315 ANCHOR) → 축(c0213 VERIFY, c0203 A3
detect) → c0251 ROUTE → Q02(AMBIGUOUS)/Q12(UNRECOVERABLE) conditional edge. c0251·c0213·
c0311·c0315의 can_route_to_q=Q02/Q12를 conditional edge(점선)로 명시 → 고립 Q-terminal 0 가시화.
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
<title>pmx-dt · Phase 5 slice 2 — TIME family 부분 tree</title>
<!-- Lock 6: Cytoscape.js + dagre, 단일 HTML, ★ inline(offline) — GAP-25 정본(slice1 CDN 답습 금지). -->
<style>
  :root{ --hl:#FFD700; --hl-cond:#FFF8B0; }
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
  #legend{padding:6px 14px;border-top:1px solid #dde;background:#f7f9ff;font-size:11.5px;display:flex;flex-wrap:wrap;gap:12px;align-items:center}
  .lg{display:inline-flex;align-items:center;gap:5px}
  .sw{display:inline-block;width:14px;height:14px;border:1.5px solid #3f78d6;background:#cfe0ff}
</style>
</head>
<body>
<header>
  <h1>Phase 5 · slice 2 — TIME family 부분 decision tree</h1>
  <div class="sub">time_value 생산 chain(c0310/c0311·c0314/c0315) → 축(c0213·c0203) → <b>c0251 ROUTE</b> → Q02/Q12. ★ 노드 클릭: upstream∪downstream 하이라이트 + 4섹션. 라이브러리=inline(offline, GAP-25).</div>
  <div id="libok">로드 확인 중…</div>
</header>
<div id="wrap">
  <div id="cy"></div>
  <div id="panel"><div class="ph">노드를 클릭하면 c-단위체/​Q-code 정보가 표시됩니다.</div></div>
</div>
<div id="legend">
  <span class="lg"><span class="sw" style="border-radius:50%;background:#7fb2ff"></span>transform(원)</span>
  <span class="lg"><span class="sw" style="border-radius:50%;background:#bcd9ff;border-style:dashed"></span>detect·verify(점선원)</span>
  <span class="lg"><span class="sw" style="background:#ffcf80;clip-path:polygon(25% 0,75% 0,100% 50%,75% 100%,25% 100%,0 50%)"></span>route·conditional(육각)</span>
  <span class="lg"><span class="sw" style="background:#ef5350;border-color:#b71c1c"></span>Q-code terminal(빨강사각)</span>
  <span class="lg"><span class="sw" style="background:var(--hl)"></span>단일 경로 5px</span>
  <span class="lg"><span class="sw" style="background:var(--hl-cond);border-style:dashed"></span>conditional 3px</span>
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
var LS_KEY="pmx_dt_slice2_state";
var state={selected:null};
try{ var raw=localStorage.getItem(LS_KEY); if(raw){ state=Object.assign(state, JSON.parse(raw)||{}); } }
catch(e){ try{ localStorage.removeItem(LS_KEY); }catch(_){ } }
function saveState(){ try{ localStorage.setItem(LS_KEY, JSON.stringify(state)); }catch(e){ } }

/* ---- 데이터 (verbatim from spec/c_units.json + q_codes.json) ---- */
var CUNITS={
  c0310:{c_id:"c0310",c_name_ko:"시간 형식 감지",srp_intent:"DETECT TIME_FORMAT",kind:"detect",cost:1,requires_detection_by:null,layer:"L-4->L-5",
    postcond:"meta.get('time_format_detected') in ['clock','elapsed','decimal','datetime','mixed']",can_route_to_q:[],
    vv:{target_columns:["time_value"],criterion_predicate_ko:"시간 형식 유형이 식별됨",pass_route_to:"c0311",fail_route_to:null},ref:"universe_sm §6 TIME_FORMAT"},
  c0311:{c_id:"c0311",c_name_ko:"시간 형식 변환",srp_intent:"CONVERT TIME_FORMAT",kind:"transform",cost:2,requires_detection_by:"c0310",layer:"L-4->L-5",
    postcond:"df['time_value'].apply(lambda x: isinstance(x, (int, float))).all()",can_route_to_q:["Q02"],vv:null,ref:"universe_sm §6 TIME_FORMAT"},
  c0314:{c_id:"c0314",c_name_ko:"시간 기준점 감지",srp_intent:"DETECT TIME_ANCHOR",kind:"detect",cost:1,requires_detection_by:null,layer:"L-4->L-5",
    postcond:"meta.get('time_anchor_type') is not None",can_route_to_q:[],
    vv:{target_columns:["time anchor tokens"],criterion_predicate_ko:"시간 기준점 유형이 파악됨",pass_route_to:"c0315",fail_route_to:null},ref:"universe_sm §6 TIME_ANCHOR"},
  c0315:{c_id:"c0315",c_name_ko:"시간 기준점 파싱",srp_intent:"CONVERT TIME_ANCHOR",kind:"transform",cost:2,requires_detection_by:"c0314",layer:"L-4->L-5",
    postcond:"df.get('time_anchor_parsed', pd.Series()).notna().all() if 'time_anchor_parsed' in df.columns else True",can_route_to_q:["Q02"],vv:null,ref:"universe_sm §6 TIME_ANCHOR"},
  c0213:{c_id:"c0213",c_name_ko:"시간 기준점 검증",srp_intent:"VERIFY TIME_ANCHOR",kind:"verify",cost:1,requires_detection_by:null,layer:"L-3->L-4",
    postcond:"meta.get('time_anchor_consistent', True)",can_route_to_q:["Q02"],
    vv:{target_columns:["time anchor tokens"],criterion_predicate_ko:"시간 기준점이 일관적이고 해석 가능하다",pass_route_to:"c0203",fail_route_to:"Q02"},ref:"universe_sm §6 TIME_ANCHOR, §3 A3"},
  c0203:{c_id:"c0203",c_name_ko:"A3 시간 유도 정책 평가",srp_intent:"DETECT TIME_FORMAT",kind:"detect",cost:1,requires_detection_by:null,layer:"L-3->L-4",
    postcond:"meta.get('a3_state') in ['ACTUAL','NOMINAL-ONLY','ACTUAL-PREFERRED','NOMINAL-PREFERRED','ELAPSED','INTERVAL','AMBIGUOUS','UNRECOVERABLE']",can_route_to_q:["Q02","Q12"],
    vv:{target_columns:["time_value"],criterion_predicate_ko:"시간 유도 정책이 8개 state 중 하나로 결정됨",pass_route_to:"c0204",fail_route_to:"Q02"},ref:"universe_sm §6 TIME_FORMAT, §3 A3"},
  c0251:{c_id:"c0251",c_name_ko:"A3 실패 라우팅",srp_intent:"ROUTE TIME_FORMAT",kind:"route",cost:0,requires_detection_by:"c0203",layer:"L-3->L-4",
    postcond:"routing_decision in ['Q02', 'Q12', 'INVALID']",can_route_to_q:["Q02","Q12"],vv:null,
    note:"AMBIGUOUS→Q02, UNRECOVERABLE→Q12 (SSOT strands.json 785개 last-c + GAP-7; snippet 산문 'INVALID' 무시).",ref:"universe_sm §2 N2, §3 A3"}
};
var QCODES={
  Q02:{q_id:"Q02",name:"Time policy not specified / ELAPSED anchor 모호",trigger_condition:"A3 = AMBIGUOUS",
    human_decision_point:"시간 정책(actual/nominal/elapsed)과 time anchor point를 명확히 결정해야 한다",
    clarification_to_sponsor:["actual vs nominal time 정책 결정","ELAPSED 기준점(첫 투약 vs 직전) 명확화","시간 변환 규칙 제공"],
    recover_to_c_id:"c0203",routing_cost:20,human_effort_score:4,ref:"universe_sm §4 Q02, §3 A3"},
  Q12:{q_id:"Q12",name:"Time anchor irrecoverable",trigger_condition:"A3 = UNRECOVERABLE",
    human_decision_point:"시간 anchor 복원 데이터를 제공하거나 INVALID 판정을 수용해야 한다",
    clarification_to_sponsor:["누락 시간 데이터 제공(CRF/EDC)","외부 adjudication 통한 복원","INVALID 판정 수용 여부"],
    recover_to_c_id:"c0203",routing_cost:200,human_effort_score:8,ref:"universe_sm §4 Q12, §3 A3"}
};

/* ---- elements (TIME backbone; conditional=can_route_to_q fail-branch, D-S4) ---- */
function N(id,kind,label){return {data:{id:id,kind:kind,label:label}};}
function E(id,s,t,cond){return {data:{id:id,source:s,target:t,conditional:!!cond}};}
var ELES=[
  N("c0310","detect","c0310\nDETECT TIME_FORMAT"),
  N("c0311","transform","c0311\nCONVERT TIME_FORMAT"),
  N("c0314","detect","c0314\nDETECT TIME_ANCHOR"),
  N("c0315","transform","c0315\nCONVERT TIME_ANCHOR"),
  N("c0213","verify","c0213\nVERIFY TIME_ANCHOR"),
  N("c0203","detect","c0203\nDETECT TIME_FORMAT (A3)"),
  N("c0251","conditional","c0251\nROUTE TIME_FORMAT"),
  N("Q02","terminal_q","Q02\nTime policy 모호"),
  N("Q12","terminal_q","Q12\nAnchor 복원불가"),
  /* solid strand path (mess → axis → route) */
  E("e_310_311","c0310","c0311"),
  E("e_314_315","c0314","c0315"),
  E("e_311_213","c0311","c0213"),
  E("e_315_213","c0315","c0213"),
  E("e_213_203","c0213","c0203"),
  E("e_203_251","c0203","c0251"),
  /* c0251 ROUTE → Q (★ 슬라이스 핵심; strands 785개 last-c=c0251) */
  E("e_251_q02","c0251","Q02",true),
  E("e_251_q12","c0251","Q12",true),
  /* D-S4 conditional fail-branch (can_route_to_q; best-strand 0 — Phase 7 재구성 조기가시화) */
  E("e_213_q02","c0213","Q02",true),
  E("e_311_q02","c0311","Q02",true),
  E("e_315_q02","c0315","Q02",true)
];

var STYLE=[
  {selector:"node",style:{"label":"data(label)","text-wrap":"wrap","text-valign":"center","text-halign":"center",
    "font-size":9,"text-max-width":104,"width":86,"height":42,"background-color":"#cfe0ff",
    "border-width":1,"border-color":"#5b8def","color":"#16314f","overlay-opacity":0,"overlay-color":"#FFD700","overlay-padding":10}},
  {selector:'node[kind="transform"]',style:{"shape":"ellipse","background-color":"#7fb2ff","border-color":"#3f78d6"}},
  {selector:'node[kind="detect"]',style:{"shape":"ellipse","background-color":"#bcd9ff","border-style":"dashed","border-width":2,"border-color":"#3f78d6"}},
  {selector:'node[kind="verify"]',style:{"shape":"ellipse","background-color":"#bcd9ff","border-style":"dashed","border-width":2,"border-color":"#3f78d6"}},
  {selector:'node[kind="conditional"]',style:{"shape":"hexagon","background-color":"#ffcf80","border-color":"#e09b3d","width":96,"height":48}},
  {selector:'node[kind="terminal_q"]',style:{"shape":"rectangle","background-color":"#ef5350","border-color":"#b71c1c","color":"#fff"}},
  {selector:"edge",style:{"width":2,"line-color":"#9e9e9e","target-arrow-color":"#9e9e9e","target-arrow-shape":"triangle","curve-style":"bezier","arrow-scale":0.9}},
  {selector:"edge[?conditional]",style:{"line-style":"dashed","line-color":"#bcaaa4","target-arrow-color":"#bcaaa4"}},
  {selector:".dim",style:{"opacity":0.22}},
  {selector:"node.hl",style:{"border-width":3,"border-color":"#FFD700"}},
  {selector:"edge.hlSingle",style:{"line-color":"#FFD700","target-arrow-color":"#FFD700","width":5,"line-style":"solid","z-index":900,"opacity":1}},
  {selector:"edge.hlCond",style:{"line-color":"#FFF8B0","target-arrow-color":"#FFF8B0","width":3,"line-style":"dashed","z-index":900,"opacity":1}},
  {selector:"node.current",style:{"border-width":4,"border-color":"#111","z-index":9999,"opacity":1}}
];

function layoutOpts(){ return {name:(dagreOK?"dagre":"breadthfirst"),rankDir:"LR",directed:true,fit:true,padding:30,animate:false,nodeSep:46,rankSep:88,spacingFactor:1.0}; }

var PLACEHOLDER='<div class="ph">노드를 클릭하면 c-단위체/Q-code 정보가 표시됩니다.</div>';
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
function clearHighlight(){ cy.elements().removeClass("dim hl hlSingle hlCond current"); cy.nodes().style("overlay-opacity",0); }
function applyHighlight(node){
  clearHighlight();
  var hl=node.successors().union(node.predecessors()).union(node);
  cy.elements().addClass("dim"); hl.removeClass("dim");
  hl.nodes().addClass("hl");
  hl.edges().forEach(function(e){ e.addClass(e.data("conditional")?"hlCond":"hlSingle"); });
  node.removeClass("hl dim").addClass("current");
}
function clearSel(){ state.selected=null; saveState(); if(cy) clearHighlight(); document.getElementById("panel").innerHTML=PLACEHOLDER; }

/* ★ onNodeTap — dispatch + panel */
function onNodeTap(node){
  var id=node.id(), kind=node.data("kind");
  state.selected=id; saveState();
  applyHighlight(node);
  document.getElementById("panel").innerHTML = (kind==="terminal_q") ? renderQPanel(id) : renderCPanel(id);
}

function routeRow(arr){ return (arr&&arr.length) ? arr.map(function(q){return '<span class="pill q">'+esc(q)+'</span>';}).join("") : '<span class="pill">없음</span>'; }

function renderCPanel(id){
  var c=CUNITS[id]; if(!c) return '<div class="sect"><div class="body"><b>'+esc(id)+'</b></div></div>';
  var h='<div class="sect"><h3>(A) Identity</h3><div class="body">';
  h+='<div class="kv"><span class="k">c_name_ko</span> · <b>'+esc(c.c_name_ko)+'</b></div>';
  h+='<div class="kv"><span class="k">srp_intent</span> · <span class="mono">'+esc(c.srp_intent)+'</span></div>';
  h+='<div class="kv"><span class="k">kind</span> '+esc(c.kind)+' · <span class="k">cost</span> '+c.cost+' · <span class="k">layer</span> '+esc(c.layer)+'</div>';
  h+='<div class="kv"><span class="k">requires_detection_by</span> <b>'+esc(c.requires_detection_by||"null")+'</b> · <span class="k">c_id</span> '+esc(c.c_id)+'</div>';
  h+='<div class="kv"><span class="k">can_route_to_q</span> '+routeRow(c.can_route_to_q)+'</div>';
  if(c.note){ h+='<div class="kv" style="color:#8a5a00">★ '+esc(c.note)+'</div>'; }
  h+='</div></div>';
  h+='<div class="sect"><h3>(B) postcondition_predicate</h3><div class="body"><pre class="pc">'+esc(c.postcond)+'</pre></div></div>';
  if(c.kind==="transform"||c.kind==="route"){
    h+='<div class="sect"><h3>(C) routing</h3><div class="body"><div class="kv">'+
       (c.kind==="route"?'AMBIGUOUS → <span class="pill q">Q02</span> · UNRECOVERABLE → <span class="pill q">Q12</span>':'fail → '+routeRow(c.can_route_to_q))+'</div></div></div>';
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
function renderQPanel(id){
  var q=QCODES[id]; if(!q) return '<div class="sect"><div class="body"><b>'+esc(id)+'</b></div></div>';
  var h='<div class="sect"><h3>(A′) 도달 사유 (conditional routing)</h3><div class="body">';
  h+='<div class="kv"><span class="k">'+esc(q.q_id)+'</span> · <b>'+esc(q.name)+'</b></div>';
  h+='<div class="kv"><span class="k">trigger</span> <span class="mono">'+esc(q.trigger_condition)+'</span> · incoming = <b>c0251</b> (ROUTE)</div></div></div>';
  h+='<div class="sect"><h3>(B′) clarification_to_sponsor</h3><div class="body"><ul style="margin:0;padding-left:18px">'+
     q.clarification_to_sponsor.map(function(t){return '<li>'+esc(t)+'</li>';}).join("")+'</ul></div></div>';
  h+='<div class="sect"><h3>(C′) human_decision_point</h3><div class="body">'+esc(q.human_decision_point)+'</div></div>';
  h+='<div class="sect"><h3>(D′) recover / cost</h3><div class="body"><div class="kv"><span class="k">recover_to_c_id</span> <b>'+esc(q.recover_to_c_id)+'</b></div>'+
     '<div class="kv"><span class="k">routing_cost</span> '+q.routing_cost+' · <span class="k">human_effort</span> '+q.human_effort_score+'/10</div>'+
     '<div class="kv"><span class="k">ref</span> <span class="mono">'+esc(q.ref)+'</span></div></div></div>';
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
OUT = ROOT / "render" / "slice2_time.html"
OUT.write_text(HTML, encoding="utf-8")
print("wrote", OUT, "(" + str(round(len(HTML) / 1024)) + " KB, inline libs " + str(round(len(LIBS) / 1024)) + " KB)")
