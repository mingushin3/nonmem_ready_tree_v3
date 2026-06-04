"""render/build_slice6.py — Phase 5 slice 6 부분 tree 렌더 빌더 (BLQ_TOKEN family).

★ GAP-25 결정: Phase 8 렌더 정본 = inline(spike_interaction.html 방식). slice1의 CDN 답습 금지.
build_slice5.py와 동일 idiom으로 spike의 inline 라이브러리 3블록(cytoscape 3.30.2 + dagre 0.8.5 +
cytoscape-dagre 2.5.0)을 추출해 오프라인 단일 HTML(render/slice6_blq.html)을 생성한다.
decision_tree.json 부재(Phase 7 미완)이므로 c_units.json/q_codes.json 사실 기반으로 직접 구성.

정본 idiom 재사용: N()/E() 헬퍼, kind별 STYLE, dagre LR layout, buildBackbone()/applyHighlight()/
onNodeTap(), upstream∪downstream 하이라이트(Lock 7), localStorage graceful fallback.
slice 2(Q-terminal+conditional edge)의 D-S4 렌더 + slice 4/5(mess→backbone 수렴)를 합친다.

표시(★ slice 6 = BLQ_TOKEN; detect+transform 복귀 + has_Q):
 - mess 쌍 c0305 DETECT → c0306 NORMALIZE(주황=이번 슬라이스), backbone(N0–N7 / A5 axis)으로 수렴.
 - A5 axis c0205 DETECT → c0253 ROUTE(주황, conditional 육각) → Q01/Q15D(빨강) / INVALID(회색) conditional edge.
 - ★ 멘탈모델 교정(GAP-28): Q01 strand 라우팅 실주체 = c0253(ROUTE, 645 last-c), c0306 아님.
   c0306.can_route_to_q=[Q01]은 Phase 7 D-S4 *선언*(slice 2 'c0019가 아니라 c0251'=GAP-26 동형).
 - ★ GAP-15 종결: c0306 산출(blq_detected/lloq_value)이 기구현 c0020 ASSIGN BLQ_FLAG → c0021 ASSIGN LLOQ를
   cross-layer 활성화(teal 점선 producer edge). c0205 pass→assignment, fail→c0253(Q).
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
<title>pmx-dt · Phase 5 slice 6 — BLQ_TOKEN family 부분 tree</title>
<!-- Lock 6: Cytoscape.js + dagre, 단일 HTML, ★ inline(offline) — GAP-25 정본(slice1 CDN 답습 금지). -->
<style>
  :root{ --hl:#FFD700; --hl-cond:#FFF8B0; --slice:#ff8f3f; --prod:#1a9e8f; }
  *{box-sizing:border-box}
  body{margin:0;font-family:-apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Malgun Gothic",sans-serif;color:#16314f}
  header{padding:8px 14px;border-bottom:1px solid #dde;background:#f7f9ff}
  header h1{font-size:15px;margin:0 0 3px}
  header .sub{font-size:12px;color:#5b6b82}
  #libok{font-size:12px;font-weight:700;color:#2e7d32;margin-top:4px}
  #wrap{display:flex;height:calc(100vh - 150px);min-height:420px}
  #cy{flex:1;background:#fbfcff;border-right:1px solid #e5e9f2}
  #panel{width:400px;overflow:auto;padding:10px 12px;font-size:13px;background:#fff}
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
  .pill.act{background:#d7f0ec;color:#0f6f62}
  ul.cl{margin:4px 0;padding-left:18px} ul.cl li{margin:2px 0;font-size:12px}
  .warn{color:#8a5a00;font-size:12px;margin:3px 0}
  #legend{padding:6px 14px;border-top:1px solid #dde;background:#f7f9ff;font-size:11.5px;display:flex;flex-wrap:wrap;gap:11px;align-items:center}
  .lg{display:inline-flex;align-items:center;gap:5px}
  .sw{display:inline-block;width:14px;height:14px;border:1.5px solid #3f78d6;background:#cfe0ff}
</style>
</head>
<body>
<header>
  <h1>Phase 5 · slice 6 — BLQ_TOKEN family 부분 decision tree</h1>
  <div class="sub"><b>c0305 DETECT → c0306 NORMALIZE</b>(주황=이번 슬라이스)가 backbone(A5 axis)으로 수렴 — detect+transform 복귀. A5 축 <b>c0205 → c0253 ROUTE</b>가 <b>Q01</b>(BLQ/LLOQ policy)·Q15D·INVALID로 conditional 라우팅. ★ <b>Q01 실주체는 c0253(ROUTE)이지 c0306이 아니다</b> — c0306.can_route_to_q=[Q01]은 Phase 7 D-S4 선언(GAP-28). ★ GAP-15 종결: c0306 산출(blq_detected/lloq_value)이 기구현 <b>c0020/c0021</b>을 cross-layer 활성화(teal 점선). 라이브러리=inline(offline, GAP-25).</div>
  <div id="libok">로드 확인 중…</div>
</header>
<div id="wrap">
  <div id="cy"></div>
  <div id="panel"><div class="ph">노드를 클릭하면 c-단위체/Q-code 정보가 표시됩니다.</div></div>
</div>
<div id="legend">
  <span class="lg"><span class="sw" style="border-radius:50%;background:#bcd9ff;border-style:dashed"></span>detect(점선원)</span>
  <span class="lg"><span class="sw" style="border-radius:50%;background:#7fb2ff"></span>transform(원)</span>
  <span class="lg"><span class="sw" style="background:#ffcf80;border-color:#e09b3d"></span>conditional ROUTE(육각)</span>
  <span class="lg"><span class="sw" style="background:#ef5350;border-color:#b71c1c"></span>Q-terminal(빨강)</span>
  <span class="lg"><span class="sw" style="background:var(--slice);border-color:#b35a16"></span>이번 슬라이스(c0305/c0306/c0253)</span>
  <span class="lg"><span class="sw" style="background:#d7f0ec;border-color:var(--prod)"></span>기구현 활성화(c0020/c0021, GAP-15)</span>
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
var LS_KEY="pmx_dt_slice6_state";
var state={selected:null};
try{ var raw=localStorage.getItem(LS_KEY); if(raw){ state=Object.assign(state, JSON.parse(raw)||{}); } }
catch(e){ try{ localStorage.removeItem(LS_KEY); }catch(_){ } }
function saveState(){ try{ localStorage.setItem(LS_KEY, JSON.stringify(state)); }catch(e){ } }

/* ---- 데이터 (verbatim from spec/c_units.json + q_codes.json) ---- */
var CUNITS={
  c0305:{c_id:"c0305",c_name_ko:"BLQ 토큰 감지",srp_intent:"DETECT BLQ_TOKEN",kind:"detect",cost:1,requires_detection_by:null,layer:"L-4->L-5",slice:true,
    postcond:"isinstance(meta.get('blq_variants_found'), list)",can_route_to_q:[],
    vv:{target_columns:["dv_value"],criterion_predicate_ko:"BLQ 토큰 변종의 존재와 LLOQ 수치가 파악됨",pass_route_to:"c0306",fail_route_to:null},
    note:"mess 층(L-4→L-5) BLQ 토큰 변종(<LLOQ,<0.1,BLQ,ND,<LOD,이하) 감지. 함수 detect_blq_token_mess — c0205(A5 축)와 구분. can_route_to_q=[] → 라우팅은 A5 축 소관. postcond는 list-타입만(빈 [] 통과) → trap이 실재 토큰 감지를 behavioral 강제.",ref:"universe_sm §6 BLQ_TOKEN"},
  c0306:{c_id:"c0306",c_name_ko:"BLQ 토큰 정규화",srp_intent:"NORMALIZE BLQ_TOKEN",kind:"transform",cost:2,requires_detection_by:"c0305",layer:"L-4->L-5",slice:true,
    postcond:"not df['dv_value'].astype(str).str.contains(r'<|BLQ|ND|LOD|이하', case=False, na=False).any()",can_route_to_q:["Q01"],vv:null,
    note:"★ postcond NON-vacuous — 토큰 잔존 시 곧장 fail이라 silent no-op 0 자동 강제. 산출 blq_detected/lloq_value를 하류 c0020/c0021가 cross-layer 소비(GAP-15). ★ can_route_to_q=[Q01]은 Phase 7 D-S4 *선언*이며 runtime 라우팅 아님 — Q01 strand 실주체는 c0253(ROUTE). GAP-28(slice 2 GAP-26 동형).",ref:"universe_sm §6 BLQ_TOKEN"},
  c0205:{c_id:"c0205",c_name_ko:"A5 관측/BLQ 평가",srp_intent:"DETECT BLQ_TOKEN",kind:"detect",cost:1,requires_detection_by:null,layer:"L-3->L-4",
    postcond:"meta.get('a5_state') in ['CLEAN','BLQ-FLAGGED','BLQ-TEXT','BLQ-ZERO','MULTI-ANALYTE','LLOQ-CHANGED','MISSING-MDV1','BIOANALYTICAL-FINAL-FLAG-MISSING','ABOVE-ULOQ','ABOVE-ULOQ-NO-POLICY','REPLICATE-SAME-TIME','REPLICATE-NO-POLICY','BLQ-NO-POLICY','LLOQ-MISSING','ABSENT']",can_route_to_q:["Q01","Q15D"],
    vv:{target_columns:["dv_value","blq indicators"],criterion_predicate_ko:"관측/BLQ 상태가 15개 state 중 하나로 결정됨",pass_route_to:"c0206",fail_route_to:"Q01"},
    note:"A5 axis 평가(기구현, 이번 슬라이스 배선). a5_state fail({BLQ-NO-POLICY,LLOQ-MISSING,ABOVE-ULOQ-NO-POLICY,REPLICATE-NO-POLICY}→Q01; BIOANALYTICAL-FINAL-FLAG-MISSING→Q15D)이면 c0253 ROUTE 도달. pass면 하류 BLQ_FLAG/LLOQ assign 진행.",ref:"universe_sm §2 N4/N5, §3 A5 + P1/P3"},
  c0253:{c_id:"c0253",c_name_ko:"A5 실패 라우팅",srp_intent:"ROUTE BLQ_TOKEN",kind:"route",cost:0,requires_detection_by:"c0205",layer:"L-3->L-4",slice:true,
    postcond:"routing_decision in ['Q01', 'Q15D', 'INVALID']",can_route_to_q:["Q01"],vv:null,
    note:"★ Q01 strand 라우팅 실주체(645 last-c: Q01 445/Q15D 89/INVALID 111). 매핑 c0205._route_a5 동형. can_route_to_q=[Q01]은 실제 라우팅 {Q01,Q15D,INVALID}의 부분집합 — Q15D/INVALID는 Phase 7 D-S4에서 c0205.can_route_to_q + GAP-8(ABSENT→INVALID)로 재구성(GAP-28).",ref:"universe_sm §2 N4/N5, §3 A5"},
  c0020:{c_id:"c0020",c_name_ko:"BLQ_FLAG 부여",srp_intent:"ASSIGN BLQ_FLAG",kind:"transform",cost:2,requires_detection_by:"c0205",layer:"L-1->L-2",activated:true,
    postcond:"('BLQ_FLAG' not in df.columns) or (df['BLQ_FLAG'].isin([0,1]).all() and (df.loc[df['BLQ_FLAG']==1, 'EVID']==0).all())",can_route_to_q:["Q01"],vv:null,
    note:"기구현 자산 — 이번 슬라이스 활성화(GAP-15). 입력 blq_detected ← c0306(cross-layer producer). blq_policy ∈ {M3,M4}이면 BLQ_FLAG=blq_detected(likelihood); M1/M5는 컬럼 미생성. blq_policy는 외부(sponsor) 입력 = 통합 시 주입(잔여 by-design).",ref:"universe_sm §2 N5, §3 A5, L0 §A.2 BLQ_FLAG"},
  c0021:{c_id:"c0021",c_name_ko:"LLOQ 부여",srp_intent:"ASSIGN LLOQ",kind:"transform",cost:2,requires_detection_by:"c0205",layer:"L-1->L-2",activated:true,
    postcond:"('LLOQ' not in df.columns) or ((df.loc[df['EVID']==0, 'LLOQ'] > 0).all() and (df.loc[df.get('BLQ_FLAG', pd.Series())==1, 'LLOQ'] > 0).all() if 'BLQ_FLAG' in df.columns else True)",can_route_to_q:["Q01"],vv:null,
    note:"기구현 자산 — 활성화(GAP-15). 입력 lloq_value ← c0306, BLQ_FLAG ← c0020(형제 chain). Guard1: obs행(EVID==0) LLOQ 비결측 필수 → 활성화 fixture는 전 obs행 BLQ-with-number.",ref:"universe_sm §3 A5 LLOQ-MISSING→Q01, L0 §A.2 LLOQ"}
};
var QCODES={
  Q01:{q_id:"Q01",name:"BLQ/LLOQ handling policy not specified",trigger_condition:"A5 ∈ {BLQ-NO-POLICY, LLOQ-MISSING, ABOVE-ULOQ-NO-POLICY, REPLICATE-NO-POLICY}",
    human_decision_point:"sponsor가 BLQ/LLOQ/ULOQ handling policy를 결정하고 LLOQ 값을 제공해야 한다",
    clarification_to_sponsor:["BLQ handling method(M1/M3/M4/M5/M6/M7) 지정","LLOQ 수치 제공 (analyte별)","ULOQ 초과 시 처리 방법 지정: 희석 factor 적용 또는 right-censor flag (subtype=uloq)","동일 (ID,TIME) 반복 측정 처리: 평균/우선/둘다 유지 (subtype=replicate)"],
    recover_to_c_id:"c0205",routing_cost:20,human_effort_score:3,ref:"universe_sm §4 Q01, §3 A5 + P1/P3"},
  Q15D:{q_id:"Q15D",name:"Assay reanalysis/final-result adjudication missing",trigger_condition:"A5 = BIOANALYTICAL-FINAL-FLAG-MISSING OR A9 = REANALYSIS-FINAL-MISSING",
    human_decision_point:"재분석 결과 중 최종 결과를 결정하는 adjudication 문서를 제공해야 한다",
    clarification_to_sponsor:["final adjudication document 제공","FINAL column 표기(다수 assay 결과 중 최종 선택)","reanalysis reconciliation 완료 확인"],
    recover_to_c_id:"c0209",routing_cost:100,human_effort_score:6,ref:"universe_sm §4 Q15D, §3 A5/A9"}
};

/* ---- elements (BLQ mess→backbone→A5 axis→ROUTE→Q; + GAP-15 cross-layer producer) ---- */
function N(id,kind,label,extra){ var d={id:id,kind:kind,label:label}; if(extra){ for(var k in extra){ d[k]=extra[k]; } } return {data:d}; }
function E(id,s,t,flags){ var d={id:id,source:s,target:t}; if(flags){ for(var k in flags){ d[k]=flags[k]; } } return {data:d}; }
var ELES=[
  N("c0305","detect","c0305\nDETECT BLQ_TOKEN",{slice:true}),
  N("c0306","transform","c0306\nNORMALIZE BLQ_TOKEN",{slice:true}),
  N("backbone","merge","backbone\n(N0–N7 / A5 axis 평가)"),
  N("c0205","detect","c0205\nDETECT BLQ_TOKEN (A5)"),
  N("c0253","conditional","c0253\nROUTE BLQ_TOKEN",{slice:true}),
  N("c0020","transform","c0020\nASSIGN BLQ_FLAG",{activated:true}),
  N("c0021","transform","c0021\nASSIGN LLOQ",{activated:true}),
  N("Q01","terminal_q","Q01\nBLQ/LLOQ policy 미지정"),
  N("Q15D","terminal_q","Q15D\n재분석 final 미정"),
  N("INVALID","terminal_invalid","INVALID\n(ABSENT 등)"),
  /* solid strand path: mess 쌍 → backbone(axis) → A5 → route */
  E("e_305_306","c0305","c0306"),
  E("e_306_bb","c0306","backbone"),
  E("e_bb_205","backbone","c0205"),
  E("e_205_253","c0205","c0253"),
  E("e_205_020","c0205","c0020"),
  E("e_020_021","c0020","c0021"),
  /* c0253 ROUTE → Q01/Q15D/INVALID (★ 슬라이스 핵심; strands 645 last-c=c0253, conditional D-S4) */
  E("e_253_q01","c0253","Q01",{conditional:true}),
  E("e_253_q15d","c0253","Q15D",{conditional:true}),
  E("e_253_invalid","c0253","INVALID",{conditional:true}),
  /* ★ GAP-15 cross-layer producer: c0306 산출(blq_detected/lloq_value) → c0020 ASSIGN BLQ_FLAG */
  E("e_306_020","c0306","c0020",{producer:true,elabel:"blq_detected/lloq_value"})
];

var STYLE=[
  {selector:"node",style:{"label":"data(label)","text-wrap":"wrap","text-valign":"center","text-halign":"center",
    "font-size":9,"text-max-width":118,"width":92,"height":44,"background-color":"#cfe0ff",
    "border-width":1,"border-color":"#5b8def","color":"#16314f","overlay-opacity":0,"overlay-color":"#FFD700","overlay-padding":10}},
  {selector:'node[kind="transform"]',style:{"shape":"ellipse","background-color":"#7fb2ff","border-color":"#3f78d6"}},
  {selector:'node[kind="detect"]',style:{"shape":"ellipse","background-color":"#bcd9ff","border-style":"dashed","border-width":2,"border-color":"#3f78d6"}},
  {selector:'node[kind="merge"]',style:{"shape":"round-rectangle","background-color":"#cde8d4","border-color":"#4c9a68","width":150,"height":48}},
  {selector:'node[kind="conditional"]',style:{"shape":"hexagon","background-color":"#ffcf80","border-color":"#e09b3d","width":98,"height":48}},
  {selector:'node[kind="terminal_q"]',style:{"shape":"rectangle","background-color":"#ef5350","border-color":"#b71c1c","color":"#fff"}},
  {selector:'node[kind="terminal_invalid"]',style:{"shape":"rectangle","background-color":"#9e9e9e","border-color":"#616161","color":"#fff"}},
  {selector:'node[?activated]',style:{"background-color":"#d7f0ec","border-color":"#1a9e8f","border-width":3}},
  {selector:'node[?slice]',style:{"background-color":"#ff8f3f","border-color":"#b35a16","border-width":3,"color":"#3a1c06"}},
  {selector:"edge",style:{"width":2,"line-color":"#9e9e9e","target-arrow-color":"#9e9e9e","target-arrow-shape":"triangle","curve-style":"bezier","arrow-scale":0.9}},
  {selector:"edge[?conditional]",style:{"line-style":"dashed","line-color":"#bcaaa4","target-arrow-color":"#bcaaa4"}},
  {selector:"edge[?producer]",style:{"line-style":"dashed","line-color":"#1a9e8f","target-arrow-color":"#1a9e8f","width":2.5,
    "label":"data(elabel)","font-size":8,"color":"#0f6f62","text-rotation":"autorotate","text-background-color":"#fff","text-background-opacity":0.85,"text-background-padding":2}},
  {selector:".dim",style:{"opacity":0.22}},
  {selector:"node.hl",style:{"border-width":3,"border-color":"#FFD700"}},
  {selector:"edge.hlSingle",style:{"line-color":"#FFD700","target-arrow-color":"#FFD700","width":5,"line-style":"solid","z-index":900,"opacity":1}},
  {selector:"edge.hlCond",style:{"line-color":"#FFF8B0","target-arrow-color":"#FFF8B0","width":3,"line-style":"dashed","z-index":900,"opacity":1}},
  {selector:"node.current",style:{"border-width":4,"border-color":"#111","z-index":9999,"opacity":1}}
];

function layoutOpts(){ return {name:(dagreOK?"dagre":"breadthfirst"),rankDir:"LR",directed:true,fit:true,padding:30,animate:false,nodeSep:42,rankSep:96,spacingFactor:1.0}; }

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

/* ★ applyHighlight — upstream backtrace ∪ downstream BFS (Lock 7); conditional/producer=옅은 노랑 */
function clearHighlight(){ cy.elements().removeClass("dim hl hlSingle hlCond current"); cy.nodes().style("overlay-opacity",0); }
function applyHighlight(node){
  clearHighlight();
  var hl=node.successors().union(node.predecessors()).union(node);
  cy.elements().addClass("dim"); hl.removeClass("dim");
  hl.nodes().addClass("hl");
  hl.edges().forEach(function(e){ e.addClass((e.data("conditional")||e.data("producer"))?"hlCond":"hlSingle"); });
  node.removeClass("hl dim").addClass("current");
}
function clearSel(){ state.selected=null; saveState(); if(cy) clearHighlight(); document.getElementById("panel").innerHTML=PLACEHOLDER; }

/* ★ onNodeTap — dispatch + panel */
function onNodeTap(node){
  var id=node.id(), kind=node.data("kind");
  state.selected=id; saveState();
  applyHighlight(node);
  var html;
  if(kind==="terminal_q"){ html=renderQPanel(id); }
  else if(kind==="terminal_invalid"){ html=renderInvalidPanel(); }
  else if(id==="backbone"){ html=renderBackbonePanel(); }
  else { html=renderCPanel(id); }
  document.getElementById("panel").innerHTML=html;
}

function routeRow(arr){ return (arr&&arr.length) ? arr.map(function(q){return '<span class="pill q">'+esc(q)+'</span>';}).join("") : '<span class="pill">없음</span>'; }

function renderCPanel(id){
  var c=CUNITS[id]; if(!c) return '<div class="sect"><div class="body"><b>'+esc(id)+'</b></div></div>';
  var tag=(c.slice?' <span class="pill slice">slice 6</span>':(c.activated?' <span class="pill act">기구현 활성화(GAP-15)</span>':''));
  var h='<div class="sect"><h3>(A) Identity'+tag+'</h3><div class="body">';
  h+='<div class="kv"><span class="k">c_name_ko</span> · <b>'+esc(c.c_name_ko)+'</b></div>';
  h+='<div class="kv"><span class="k">srp_intent</span> · <span class="mono">'+esc(c.srp_intent)+'</span></div>';
  h+='<div class="kv"><span class="k">kind</span> '+esc(c.kind)+' · <span class="k">cost</span> '+c.cost+' · <span class="k">layer</span> '+esc(c.layer)+'</div>';
  h+='<div class="kv"><span class="k">requires_detection_by</span> <b>'+esc(c.requires_detection_by||"null")+'</b> · <span class="k">c_id</span> '+esc(c.c_id)+'</div>';
  h+='<div class="kv"><span class="k">can_route_to_q</span> '+routeRow(c.can_route_to_q)+'</div>';
  if(c.note){ h+='<div class="warn">★ '+esc(c.note)+'</div>'; }
  h+='</div></div>';
  h+='<div class="sect"><h3>(B) postcondition_predicate</h3><div class="body"><pre class="pc">'+esc(c.postcond)+'</pre></div></div>';
  h+='<div class="sect"><h3>(C) verify_visualization</h3><div class="body">'+renderVV(c.vv)+'</div></div>';
  h+='<div class="sect"><h3>(D) ref</h3><div class="body"><span class="mono">'+esc(c.ref)+'</span></div></div>';
  return h;
}
function renderVV(vv){
  if(!vv) return '<i>(verify_visualization 없음 — transform/route)</i>';
  var h='<div class="kv"><span class="k">target_columns</span> '+(vv.target_columns||[]).map(function(x){return '<span class="pill">'+esc(x)+'</span>';}).join("")+'</div>';
  h+='<div class="kv"><span class="k">criterion</span> '+esc(vv.criterion_predicate_ko)+'</div>';
  h+='<div class="kv"><span class="k">pass →</span> <span class="pill pass">'+esc(vv.pass_route_to||"next")+'</span></div>';
  h+='<div class="kv"><span class="k">fail →</span> '+(vv.fail_route_to?'<span class="pill q">'+esc(vv.fail_route_to)+'</span>':'<span class="pill">없음</span>')+'</div>';
  return h;
}
function renderQPanel(id){
  var q=QCODES[id]; if(!q) return '<div class="sect"><div class="body"><b>'+esc(id)+'</b></div></div>';
  var h='<div class="sect"><h3>(A′) 도달 사유 <span class="pill q">'+esc(q.q_id)+'</span></h3><div class="body">';
  h+='<div class="kv"><b>'+esc(q.name)+'</b></div>';
  h+='<div class="kv"><span class="k">trigger</span> <span class="mono">'+esc(q.trigger_condition)+'</span></div>';
  h+='<div class="kv"><span class="k">conditional edge</span> c0253(ROUTE) → '+esc(q.q_id)+' (D-S4; best-strand last-c)</div>';
  h+='<div class="kv"><span class="k">routing_cost</span> '+q.routing_cost+' · <span class="k">human_effort</span> '+q.human_effort_score+'/10</div>';
  h+='</div></div>';
  h+='<div class="sect"><h3>(B′) clarification_to_sponsor</h3><div class="body"><ul class="cl">'+
     (q.clarification_to_sponsor||[]).map(function(x){return '<li>'+esc(x)+'</li>';}).join("")+'</ul></div></div>';
  h+='<div class="sect"><h3>(C′) human_decision_point</h3><div class="body">'+esc(q.human_decision_point)+'</div></div>';
  h+='<div class="sect"><h3>(D′) recover_to_c_id</h3><div class="body"><span class="mono">'+esc(q.recover_to_c_id)+'</span> 로 복귀</div></div>';
  return h;
}
function renderInvalidPanel(){
  var h='<div class="sect"><h3>INVALID terminal</h3><div class="body">';
  h+='<div class="kv">c0253(ROUTE)이 a5_state=ABSENT(관측 부재)일 때 도달하는 비-Q terminal(q_code=None).</div>';
  h+='<div class="kv">strands.json: c0253 last-c 645 중 <b>111</b>이 (INVALID, None). can_route_to_q=[Q01]의 scope 밖 —</div>';
  h+='<div class="warn">Phase 7 D-S4에서 conditional edge로 INVALID terminal 연결(GAP-8: c0205 ABSENT→INVALID scope-out). 고립 terminal 아님.</div>';
  h+='</div></div>';
  return h;
}
function renderBackbonePanel(){
  var h='<div class="sect"><h3>backbone 진입 (merge)</h3><div class="body">';
  h+='<div class="kv">N1 역할: L-4→L-5 mess normalization 완료 후 <b>N0–N7 backbone / A5 axis(관측/BLQ) 평가</b> 진입점.</div>';
  h+='<div class="kv">N2 수렴: BLQ mess 쌍(c0305/c0306)이 이 노드 앞에서 종료(D-S3: mess가 backbone 앞단). 이후 A5 축(c0205)이 a5_state를 결정.</div>';
  h+='<div class="kv">N3 기여 strand: BLQ_TOKEN 감지 <b>500</b>(c0305/c0306 freq). Q01 라우팅 <b>445</b>(c0253 last-c).</div>';
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
OUT = ROOT / "render" / "slice6_blq.html"
OUT.write_text(HTML, encoding="utf-8")
print("wrote", OUT, "(" + str(round(len(HTML) / 1024)) + " KB, inline libs " + str(round(len(LIBS) / 1024)) + " KB)")
