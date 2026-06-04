"""render/build_html.py — Phase 8: spec/decision_tree.json → 단일 self-contained interactive HTML.

★ 첫 "실 tree" 렌더 = 최종 deliverable. 정본 시드 = render/spike_interaction.html (Lock 6/7 검증 패턴).
처음부터 만들지 않고 spike의 STYLE/highlight/onNodeTap/panel/perf/localStorage를 그대로 adapt —
데이터 주입점만 canonical spec(full tree)으로 교체한다(build_slice6.py idiom 연장).

라이브러리 = inline(GAP-25 정본): spike의 cytoscape 3.30.2 + dagre 0.8.5 + cytoscape-dagre 2.5.0 3블록 추출.
입력(READ-ONLY): spec/decision_tree.json(렌더 골격) · spec/c_units.json(4섹션 join) ·
                 spec/q_codes.json(Q A'~D' join) · spec/strands.json(영향 strand 수 실측) · anchors.json(node/axis label).
출력: render/index.html (deterministic — 재실행 시 동일).

설계 결정(plan 승인 반영):
 - 노드 100 = 8 branch(N0–N7) + 11 axis(A0–A10, collapse-by-default·101 state) + 5 process-terminal + 19 Q + 57 c.
 - 엣지: 76 attach(canonical) + 52 conditional_routing c→Q(canonical) + 3 terminal_routing c→INVALID(canonical)
         + 합성 backbone(spine N0→…→N7·N7→AUTO/REPAIR·Q→QUARANTINE) — 전부 canonical 순서/strands 실측 grounding.
 - bundle: DEFER(bundles=[] 충실 렌더; GAP-27B 가시 deferred 마커). collapse는 axis-state로 작동.
 - deferred 시각: unreached Q15A/B/C/X(고립 placeholder, 의도된 고립) + spec_decisions GAP-13/27B/c0040.
 - GAP-25: 실 backbone 레이아웃 자가측정(window.__PERF__ + 배지), node-count 100/190 이미 PASS.
"""

import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).resolve().parent.parent
SPEC = ROOT / "spec"
SPIKE = (ROOT / "render" / "spike_interaction.html").read_text(encoding="utf-8")


# ───────────────────────────────────────────────────────────── inline libs (GAP-25 정본)
def extract_inline_libs(spike: str) -> str:
    """spike의 inline cytoscape/dagre/cytoscape-dagre <script> 3블록 추출(slice6 idiom 동일)."""
    start = spike.index("<script>/*! inlined: cytoscape 3.30.2")
    cd = spike.index("/*! inlined: cytoscape-dagre")
    end = spike.index("</script>", cd) + len("</script>")
    return spike[start:end]


LIBS = extract_inline_libs(SPIKE)


def load(name: str, root: pathlib.Path = SPEC):
    return json.loads((root / name).read_text(encoding="utf-8"))


DT = load("decision_tree.json")
CU = {c["c_id"]: c for c in load("c_units.json")}
QC = {q["q_id"]: q for q in load("q_codes.json")}
STRANDS = load("strands.json")
ANCHORS = load("anchors.json", ROOT)

NODES = DT["nodes"]
ATTACH = DT["edges"]
COND = DT["conditional_routing"]
TERMR = DT["terminal_routing"]
DEFERRED = DT["deferred"]
STATS = DT["stats"]
QPART = STATS["q_partition"]

NODE_BY_ID = {n["id"]: n for n in NODES}
C_IDS = [n["id"] for n in NODES if n["type"] in ("transform", "detect", "verify", "route")]
Q_IDS = [n["id"] for n in NODES if n.get("terminal_class") == "q_code"]
PROC_IDS = [n["id"] for n in NODES if n.get("terminal_class") == "process"]
AXIS_IDS = [n["id"] for n in NODES if n["type"] == "conditional"]
BRANCH_IDS = [n["id"] for n in NODES if n["type"] == "branch"]


# ───────────────────────────────────────────────────────────── c → attached backbone nodes
def c_attach_targets():
    m = {cid: set() for cid in C_IDS}
    for e in ATTACH:
        if e["from"] in m:
            m[e["from"]].add(e["to"])
    return m


C2NODES = c_attach_targets()


# ───────────────────────────────────────────────────────────── 영향 strand 수 (실측, build-time 집계)
def strand_influence():
    """각 노드를 '지나는' strand 수 = 그 노드(혹은 부착 c)가 c_sequence/terminal/q_code에 등장한 strand 수."""
    inf = {n["id"]: 0 for n in NODES}
    cset = set(C_IDS)
    for s in STRANDS:
        touched = set()
        for c in s["c_sequence"]:
            if c in cset:
                touched.add(c)
                for nd in C2NODES.get(c, ()):  # 부착 backbone 노드(axis/branch/layer-stage)
                    if nd in inf:
                        touched.add(nd)
        if s["terminal"] in inf:
            touched.add(s["terminal"])
        if s["q_code"] in inf:
            touched.add(s["q_code"])
        for nd in touched:
            inf[nd] += 1
    return inf


INFLUENCE = strand_influence()


# ───────────────────────────────────────────────────────────── mess family 분류 (Family view)
def family_of(cid):
    """skeleton_hook 'mess:XXX' → family XXX; 그 외 axis/backbone."""
    c = CU.get(cid, {})
    hook = (c.get("skeleton_hook") or "")
    if hook.startswith("mess:"):
        return hook.split("mess:", 1)[1].split()[0]
    # axis 부착 c → 해당 axis family
    ax = sorted(a for a in C2NODES.get(cid, ()) if a in AXIS_IDS)
    if ax:
        return "axis:" + ax[0]
    nd = sorted(n for n in C2NODES.get(cid, ()) if n in BRANCH_IDS)
    if nd:
        return "backbone:" + nd[0]
    return "기타"


FAMILY = {cid: family_of(cid) for cid in C_IDS}
FAMILIES = {}
for cid, fam in FAMILY.items():
    FAMILIES.setdefault(fam, []).append(cid)


# ───────────────────────────────────────────────────────────── 노드 kind + label (cytoscape data)
def axis_label(n):
    return "%s · %d state" % (n["id"], n["state_count"])


def branch_label(n):
    q = (n.get("label") or "").split("(")[0].strip()
    return "%s\n%s" % (n["id"], q[:34])


PROC_KIND = {
    "AUTO": "terminal_auto", "REPAIR": "terminal_repair", "QUARANTINE": "terminal_quar",
    "UNSUPPORTED": "terminal_unsup", "INVALID": "terminal_invalid",
}
PROC_LABEL = {
    "AUTO": "AUTO\nNONMEM-ready", "REPAIR": "REPAIR\n정책 적용 후 ready",
    "QUARANTINE": "QUARANTINE\nQ 대기", "UNSUPPORTED": "UNSUPPORTED\n미지원",
    "INVALID": "INVALID\n복원 불가",
}


def build_elements():
    els = []

    def N(_id, kind, label, **extra):
        d = {"id": _id, "kind": kind, "label": label}
        d.update(extra)
        els.append({"data": d})

    def E(_id, s, t, ekind, **extra):
        d = {"id": _id, "source": s, "target": t, "ekind": ekind}
        d.update(extra)
        els.append({"data": d})

    # --- branch N0–N7 ---
    for n in NODES:
        if n["type"] == "branch":
            N(n["id"], "branch", branch_label(n))
    # --- axis A0–A10 (collapse-by-default; states는 expand 시 child로 추가) ---
    for n in NODES:
        if n["type"] == "conditional":
            N(n["id"], "axis", axis_label(n), axis=True, state_count=n["state_count"])
    # --- process terminals ---
    for tid in PROC_IDS:
        N(tid, PROC_KIND[tid], PROC_LABEL.get(tid, tid))
    # --- Q terminals (q_status 시각) ---
    qstatus = {}
    for q in QPART["exercised"]:
        qstatus[q] = "exercised"
    for q in QPART["static_no_strand"]:
        qstatus[q] = "static"
    for q in QPART["unreached"]:
        qstatus[q] = "unreached"
    for n in NODES:
        if n.get("terminal_class") == "q_code":
            st = qstatus.get(n["id"], "exercised")
            lab = (n.get("label") or n["id"]).split("/")[0][:24]
            N(n["id"], "terminal_q", "%s\n%s" % (n["id"], lab),
              qstatus=st, deferred=(st == "unreached"))
    # --- c-nodes (transform/detect/verify/route) ---
    for n in NODES:
        if n["type"] in ("transform", "detect", "verify", "route"):
            cid = n["id"]
            N(cid, n["kind"], "%s\n%s" % (cid, n["srp_intent"]),
              fam=FAMILY.get(cid, "기타"), layer=n.get("layer_pair", ""), cost=n.get("cost", 0))

    # ===== EDGES =====
    # 합성 backbone spine (canonical 순서; D-S3 골격) — render 가독성용, 비날조(process_nodes 순서)
    bb = DT["backbone"]["process_nodes"]
    for i in range(len(bb) - 1):
        E("bb_%s_%s" % (bb[i], bb[i + 1]), bb[i], bb[i + 1], "backbone")
    E("bb_N7_AUTO", "N7", "AUTO", "backbone")
    E("bb_N7_REPAIR", "N7", "REPAIR", "backbone")

    # attach (canonical c→backbone; layer_stage 타겟은 합성 stage 노드)
    stage_seen = set()
    for e in ATTACH:
        tgt = e["to"]
        if e.get("via") == "layer_stage":
            sid = "stage:" + tgt
            if sid not in stage_seen:
                stage_seen.add(sid)
                els.append({"data": {"id": sid, "kind": "stage", "label": "%s\n정규화 stage" % tgt, "stage": True}})
            E("at_%s_%s" % (e["from"], sid), e["from"], sid, "attach", via="layer_stage")
        else:
            E("at_%s_%s" % (e["from"], tgt), e["from"], tgt, "attach", via=e.get("via", ""))

    # conditional_routing c→Q (canonical, D-S4) — dashed, highlightable.
    # ★ 'source'는 cytoscape edge 예약키(source node)이므로 라우팅 출처는 csource로 둔다(충돌 회피).
    for i, e in enumerate(COND):
        E("cond_%d" % i, e["from"], e["to"], "conditional", conditional=True,
          qstatus=e.get("q_status", ""), strand_count=e.get("strand_count", 0),
          csource=e.get("source", ""), from_kind=e.get("from_kind", ""), gap=e.get("gap", []))
    # Q → QUARANTINE (strands 실측: 모든 Q strand → QUARANTINE) — backbone semantic
    for q in Q_IDS:
        if q not in QPART["unreached"]:
            E("q_quar_%s" % q, q, "QUARANTINE", "backbone", note="Q routing → QUARANTINE")

    # terminal_routing c→INVALID (canonical, 결정 B) — conditional과 시각 구분
    for i, e in enumerate(TERMR):
        E("termr_%d" % i, e["from"], e["to"], "terminal_routing",
          terminal_routing=True, terminal_class=e.get("terminal_class", "process"),
          strand_count=e.get("strand_count", 0))

    # deferred: GAP-13 c0210 → UNSUPPORTED/INVALID (미결 spec 결정 — ghost dashed)
    for sd in DEFERRED.get("spec_decisions", []):
        if sd.get("id") == "GAP-13" and sd.get("c") in NODE_BY_ID:
            E("def_c0210_unsup", sd["c"], "UNSUPPORTED", "deferred", deferred=True, gap="GAP-13")
            E("def_c0210_inv", sd["c"], "INVALID", "deferred", deferred=True, gap="GAP-13")

    # ── 합성 connectivity 보정(렌더 가독성; 라우팅 주장 아님) ──
    # decision_tree.json은 c→backbone attach + Q/terminal routing만 encode → 일부 backbone 노드 미부착.
    # 의도된 고립(deferred unreached Q15A/B/C/X)은 제외. 그 외 고립 노드는 label/layer 근거로 spine에 연결.
    #   · 고립 axis(A0=분석의도) → N0(분석의도 gate)에 hang(다른 axis가 c경유로 spine 연결되는 것과 동형).
    #   · 고립 c(c0001=L-1→L-2 컬럼스키마 boundary verify) → N1(첫 구성 gate)에 attach.
    node_ids = {e["data"]["id"] for e in els if "source" not in e["data"]}
    incident = set()
    for e in els:
        if "source" in e["data"]:
            incident.add(e["data"]["source"])
            incident.add(e["data"]["target"])
    deferred_q = set(QPART["unreached"])
    for nid in sorted(node_ids - incident - deferred_q):
        if nid in AXIS_IDS:
            E("synlink_N0_%s" % nid, "N0", nid, "backbone", synth=True, note="render skeleton link (axis at its gate)")
        elif nid in C_IDS:
            E("synlink_%s_N1" % nid, nid, "N1", "attach", via="skeleton_synth", synth=True, note="render skeleton link (L-boundary verify)")
        else:
            print("[build_html][WARN] 미연결 노드(연결 규칙 없음): %s" % nid)

    # ── recover edge (Q→c, human-in-the-loop): q_codes recover_to_c_id의 시각화. ★ 자동 라우팅 아님 ──
    #   · 도달가능 Q(exercised∪static)만 + 타깃이 wired c(∈C_IDS, =CUNITS key)일 때만 그린다.
    #   · unreached Q(Q15A/B/C/X)는 reachable_q에 없어 자동 제외 → 고립 불변 보존(test_no_isolated_nodes_except_deferred).
    #   · 미배선 타깃(Q10→c0330)은 edge 생략(패널 D'에서 명시). ★ 별도 ekind="recover"(conditional/terminal 카운트 불혼입).
    #   · 연결 보정 loop 뒤에 추가(loop의 incident 계산·synlink 거동 무변경 → 결정론/회귀 안전).
    cset = set(C_IDS)
    for q in sorted(QPART["exercised"] + QPART["static_no_strand"]):
        tgt = QC.get(q, {}).get("recover_to_c_id") or NODE_BY_ID.get(q, {}).get("recover_to_c_id", "")
        if tgt in cset:
            E("recover_%s_%s" % (q, tgt), q, tgt, "recover", recover=True, label="↩", recover_to=tgt)
    return els


ELES = build_elements()


# ───────────────────────────────────────────────────────────── axis states (expand 시 child)
AXIS_STATES = {n["id"]: n["states"] for n in NODES if n["type"] == "conditional"}


# ───────────────────────────────────────────────────────────── CUNITS (57 wired → 4섹션 join)
def build_cunits():
    out = {}
    missing = []
    for cid in C_IDS:
        c = CU.get(cid)
        if not c:
            missing.append(cid)
            continue
        ba = c.get("before_after_toy_example") or {}
        out[cid] = {
            "c_id": cid, "c_name_ko": c.get("c_name_ko", ""), "srp_intent": c.get("srp_intent", ""),
            "kind": c.get("kind", ""), "cost": c.get("cost", 0),
            "requires_detection_by": c.get("requires_detection_by"),
            "layer_pair": c.get("layer_pair", ""), "ref": c.get("ref", ""),
            "llm_prompt": c.get("llm_prompt", ""),
            "precondition_checklist_ko": c.get("precondition_checklist_ko", []),
            "r_snippet": c.get("r_snippet", ""), "python_snippet": c.get("python_snippet", ""),
            "verify_visualization": c.get("verify_visualization"),
            "can_route_to_q": c.get("can_route_to_q", []),
            "before": ba.get("before", ""), "after": ba.get("after", ""),
            "fam": FAMILY.get(cid, "기타"), "influence": INFLUENCE.get(cid, 0),
        }
    if missing:
        raise SystemExit("[build_html] c_units.json에 없는 wired c: %s" % missing)
    return out


CUNITS = build_cunits()


# ───────────────────────────────────────────────────────────── QINFO (19 Q → A'~D' join)
def build_qinfo():
    out = {}
    for q in Q_IDS:
        n = NODE_BY_ID[q]
        meta = QC.get(q, {})
        reach = [{"from": e["from"], "from_kind": e.get("from_kind", ""), "source": e.get("source", ""),
                  "strand_count": e.get("strand_count", 0), "realizing_route_c": e.get("realizing_route_c", [])}
                 for e in COND if e["to"] == q]
        out[q] = {
            "q_id": q, "name": meta.get("name", n.get("label", "")),
            "trigger_condition": meta.get("trigger_condition", n.get("trigger", "")),
            "clarification_to_sponsor": meta.get("clarification_to_sponsor", []),
            "human_decision_point": meta.get("human_decision_point", ""),
            "recover_to_c_id": meta.get("recover_to_c_id", n.get("recover_to_c_id", "")),
            "routing_cost": meta.get("routing_cost", n.get("routing_cost", 0)),
            "human_effort_score": meta.get("human_effort_score", "—"),
            "ref": meta.get("ref", n.get("ref", "")),
            "q_status": n.get("q_status", "exercised"),
            "incoming_wired_c": n.get("incoming_wired_c", []),
            "reach": reach, "influence": INFLUENCE.get(q, 0),
        }
    return out


QINFO = build_qinfo()


# ───────────────────────────────────────────────────────────── NODEINFO (branch/axis/terminal → 3섹션)
def axis_routes(axis_id):
    """이 axis에 부착된 c가 라우팅하는 Q 목록(분기 정보)."""
    cs = [cid for cid in C_IDS if axis_id in C2NODES.get(cid, ())]
    qs = sorted({e["to"] for e in COND if e["from"] in cs})
    return cs, qs


def build_nodeinfo():
    out = {}
    for n in NODES:
        nid = n["id"]
        if n["type"] == "branch":
            out[nid] = {"role": n.get("label", ""), "ref": n.get("ref", ""),
                        "bm": "process gate · pass→다음 N / fail→Q·terminal(conditional)",
                        "strands": INFLUENCE.get(nid, 0)}
        elif n["type"] == "conditional":
            cs, qs = axis_routes(nid)
            out[nid] = {"role": "axis %s — %d개 state (collapse 기본; 클릭→펼침)" % (nid, n["state_count"]),
                        "ref": n.get("ref", ""), "states": n["states"], "state_count": n["state_count"],
                        "bm": "부착 c: %s → 라우팅 Q: %s" % (", ".join(cs) or "—", ", ".join(qs) or "—"),
                        "strands": INFLUENCE.get(nid, 0)}
        elif n.get("terminal_class") == "process":
            out[nid] = {"role": PROC_LABEL.get(nid, nid).replace("\n", " — "), "ref": n.get("ref", ""),
                        "bm": "종착(process terminal)", "strands": INFLUENCE.get(nid, 0)}
    return out


NODEINFO = build_nodeinfo()


# ───────────────────────────────────────────────────────────── deferred markers (시각 표시)
DEFERRED_VIEW = {
    "unreached_q": DEFERRED.get("unreached_q", []),
    "spec_decisions": DEFERRED.get("spec_decisions", []),
}


# ───────────────────────────────────────────────────────────── 경계 배너 수치 (★ 전부 render 입력서 build-time 계산 = deterministic·검증가능)
def boundary_stats():
    """문제 B 정직성: oracle(strands.json 5000 종착) ↔ 57-wired 구현범위 두 축을 명확 구분.
    orchestrator 런타임 지표(완주 439·realized 88)는 render 입력서 재계산 불가라 미포함(별도 안내)."""
    term = Counter(s["terminal"] for s in STRANDS)
    used = set()
    for s in STRANDS:
        used.update(s["c_sequence"])
    return {
        "total_strands": len(STRANDS),                       # 5000
        "wired_c": len(C_IDS),                               # 57
        "auto": term.get("AUTO", 0), "repair": term.get("REPAIR", 0),
        "complete": term.get("AUTO", 0) + term.get("REPAIR", 0),  # 235 (oracle 완주=AUTO+REPAIR)
        "quarantine": term.get("QUARANTINE", 0),             # 3380
        "invalid": term.get("INVALID", 0),                   # 862
        "unsupported": term.get("UNSUPPORTED", 0),           # 523
        "realized_pure": STATS.get("pure_realized_strands", 0),   # 3228
        "unwired_c": len(used - set(C_IDS)),                 # 62 (strands 등장·미wired)
        "static_q": len(QPART["static_no_strand"]),          # 2 (Q05/Q10 미실현)
        "deferred_total": len(DEFERRED.get("unreached_q", [])) + len(DEFERRED.get("spec_decisions", [])),  # 7 (unreached Q4 + GAP c3)
    }


BANNER = boundary_stats()


# ============================================================= HTML 조립
def js(obj):
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


PAGE_HEAD = r"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>pmx-dt · NONMEM-ready decision tree (Phase 8 · 전체 tree)</title>
<!-- Lock 6: Cytoscape.js + dagre, 단일 self-contained HTML, ★ inline(offline) — GAP-25 정본. 외부 image 0. -->
<style>
  :root{ --hl-single:#FFD700; --hl-cond:#FFF8B0; --ink:#1c2733; --line:#d7dde3; --bg:#f6f8fa;
         --panel:#fff; --accent:#2f6fde; --red:#d32f2f; --green:#2e7d32; --amber:#b35a16; }
  *{box-sizing:border-box}
  html,body{height:100%;margin:0}
  body{font-family:"Malgun Gothic","Apple SD Gothic Neo","Noto Sans KR",system-ui,sans-serif;
       color:var(--ink);background:var(--bg);display:flex;flex-direction:column}
  code,pre,.mono{font-family:"Consolas","SFMono-Regular",Menlo,monospace}
  #topbar{flex:0 0 auto;display:flex;align-items:center;gap:8px;padding:7px 12px;background:#fff;
          border-bottom:1px solid var(--line);flex-wrap:wrap}
  #topbar h1{font-size:14px;margin:0 6px 0 0;font-weight:700}
  #topbar .sub{font-size:11px;color:#6b7785}
  .tab{cursor:pointer;border:1px solid var(--line);background:#fff;border-radius:6px;padding:5px 11px;font-size:12px}
  .tab.active{background:var(--accent);color:#fff;border-color:var(--accent)}
  .btn{cursor:pointer;border:1px solid var(--line);background:#fff;border-radius:6px;padding:5px 9px;font-size:12px}
  .btn:hover{background:#eef3fb}
  #perfBadge{font-size:11px;font-weight:700;padding:4px 9px;border-radius:6px;border:1px solid var(--line);background:#f3f6fa;color:#566}
  #perfBadge.pass{background:#e8f5e9;border-color:#bcdfc0;color:var(--green)}
  #perfBadge.fail{background:#fdecea;border-color:#f3b9b3;color:var(--red)}
  #famSel{font-size:12px;padding:4px 6px;border:1px solid var(--line);border-radius:6px;display:none}
  #breadcrumb{flex:0 0 auto;font-size:11px;color:#566;padding:4px 12px;border-bottom:1px solid var(--line);
              background:#fafbfc;min-height:24px;display:flex;gap:4px;align-items:center;flex-wrap:wrap}
  #breadcrumb .crumb{cursor:pointer;color:var(--accent);text-decoration:none}
  #breadcrumb .crumb:hover{text-decoration:underline}
  #boundary{flex:0 0 auto;font-size:10.5px;color:#46535f;padding:6px 12px;border-bottom:1px solid var(--line);
            background:#fbfcfe;line-height:1.55}
  #boundary b{color:var(--ink)}
  #boundary .ax{color:var(--accent);font-weight:700}
  #boundary .warn{color:var(--amber)}
  #legend{flex:0 0 auto;display:flex;gap:10px 14px;flex-wrap:wrap;align-items:center;padding:5px 12px;
          font-size:10.5px;color:#566;border-bottom:1px solid var(--line);background:#fff}
  #legend .grp{font-weight:700;color:#3a4651;margin-right:2px}
  #legend .sep{width:1px;height:13px;background:var(--line);display:inline-block}
  .lg{display:inline-flex;align-items:center;gap:4px}
  .sw{width:13px;height:13px;display:inline-block;border:1px solid #888}
  #stage{flex:1 1 auto;min-height:0;display:flex}
  #cywrap{flex:1 1 0;min-width:0;position:relative}
  #cy{position:absolute;inset:0}
  #minimap{position:absolute;right:8px;bottom:8px;width:190px;height:130px;border:1px solid var(--line);
           background:rgba(255,255,255,.92);border-radius:6px;z-index:6;cursor:pointer}
  #zoombar{position:absolute;left:8px;bottom:8px;z-index:6;display:flex;gap:4px}
  #panel{flex:0 0 0;width:0;overflow:hidden;border-left:1px solid var(--line);background:var(--panel);
         display:none;flex-direction:column;min-width:0}
  body.split #cywrap{flex:1 1 50%}
  body.split #panel{display:flex;flex:1 1 50%;width:auto}
  #panelHead{flex:0 0 auto;display:flex;align-items:center;justify-content:space-between;padding:8px 12px;
             border-bottom:1px solid var(--line);background:#fafbfc}
  #panelTitle{font-weight:700;font-size:13px}
  #panelClose{cursor:pointer;border:none;background:none;font-size:20px;line-height:1;color:#888}
  #panelBody{flex:1 1 auto;overflow:auto;padding:11px 13px}
  .sect{border:1px solid var(--line);border-radius:8px;margin-bottom:11px;overflow:hidden}
  .sect>h3{margin:0;font-size:12px;padding:6px 10px;background:#eef2f7;border-bottom:1px solid var(--line)}
  .sect>.body{padding:9px 10px}
  .kv{font-size:12px;margin:3px 0}
  .kv .k{color:#6b7785}
  .mono{font-family:"Consolas",monospace;font-size:11.5px;background:#f1f4fb;padding:1px 4px;border-radius:4px}
  .pill{display:inline-block;background:#eef2f7;border:1px solid var(--line);border-radius:5px;padding:1px 6px;font-size:11px;margin:1px}
  .pill.q{background:#fdecea;border-color:#f3b9b3;color:var(--red);font-weight:700}
  .pill.pass{background:#e8f5e9;border-color:#bcdfc0;color:var(--green)}
  .pill.def{background:#f3eaff;border-color:#d7c2f0;color:#6a3fb0}
  .prompt{background:#fffef2;border:1px dashed #d9cf86;border-radius:6px;padding:8px;font-size:12px;white-space:pre-wrap;line-height:1.45}
  pre.snip{background:#0f1722;color:#d6e2f0;border-radius:6px;padding:9px;font-size:11.5px;overflow:auto;margin:4px 0;line-height:1.45}
  pre.snip .cmt{color:#7fa7c7}
  .snlabel{font-size:11px;font-weight:700;color:#566;margin-top:6px}
  table.toy{border-collapse:collapse;font-size:11.5px;margin:4px 0}
  table.toy td,table.toy th{border:1px solid var(--line);padding:3px 8px;text-align:center}
  table.toy th{background:#f0f3f7;font-weight:600}
  td.chg{background:var(--hl-single);font-weight:700}
  .chklist{list-style:none;padding:0;margin:0;font-size:13px}
  .chklist li{margin:5px 0;display:flex;gap:7px;align-items:flex-start}
  #chkbadge,.badge-ok{display:none;margin-top:6px;color:var(--green);font-weight:700;font-size:12px}
  .badge-ok.show{display:block}
  .deferbadge{display:inline-block;background:#f3eaff;border:1px solid #d7c2f0;color:#6a3fb0;border-radius:5px;padding:1px 6px;font-size:10px;margin-left:6px}
  .navrow{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0}
  .reachrow{font-size:11.5px;margin:2px 0;padding:3px 6px;background:#f7f9fc;border-radius:5px}
  #libwarn{display:none;background:#fdecea;border:1px solid #f3b9b3;color:#a3261d;padding:6px 10px;font-size:12px}
</style>
</head>
<body>
<header id="topbar">
  <h1>pmx-dt · decision tree</h1>
  <span class="sub">NONMEM-ready data wrangling · 전체 tree (Phase 8)</span>
  <span style="flex:1"></span>
  <button class="tab active" id="tabAll" type="button">전체</button>
  <button class="tab" id="tabFam" type="button">Family</button>
  <select id="famSel" title="mess 정규화 family 선택"></select>
  <span id="perfBadge" title="GAP-25 DoD#6 성능 게이트(dagre &lt; 10s)">perf…</span>
  <button class="btn" id="clearSel" type="button">선택 해제</button>
  <button class="btn" id="resetState" type="button" title="localStorage 초기화">상태 초기화</button>
</header>
<div id="libwarn">⚠ inline 라이브러리 로드 실패 — 파일 손상 의심(인터넷 불필요·캐시 무관). 다시 내려받으세요.</div>
<div id="breadcrumb"><span style="color:#8a97aa">노드를 클릭하면 경로(N0→현재)가 표시됩니다.</span></div>
<div id="boundary"></div>
<div id="legend"></div>
<div id="stage">
  <div id="cywrap">
    <div id="cy"></div>
    <div id="zoombar"><button class="btn" id="zin" type="button">＋</button><button class="btn" id="zout" type="button">－</button><button class="btn" id="zfit" type="button">fit</button></div>
    <canvas id="minimap" width="190" height="130" title="미니맵 — 클릭하면 그 위치로 이동"></canvas>
  </div>
  <aside id="panel">
    <div id="panelHead"><span id="panelTitle">패널</span><button id="panelClose" type="button">×</button></div>
    <div id="panelBody"></div>
  </aside>
</div>
"""

PAGE_TAIL = "</body>\n</html>\n"


# ───────────────────────────────────────────────────────────── APP_JS (spike 함수 adapt; 재작성 아님)
APP_JS = r'''<script>
"use strict";
/* ===== 0. util + dagre 등록 + localStorage(graceful fallback, LS key=pmx_dt_state per [7-3]) ===== */
function esc(s){return String(s==null?"":s).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;");}
function ms(x){return Math.round(x).toLocaleString()+" ms";}
var dagreOK=false;
try{ if(window.cytoscapeDagre){ cytoscape.use(window.cytoscapeDagre); dagreOK=true; } }catch(e){ dagreOK=false; }
var libsOK=(typeof cytoscape!=="undefined")&&(typeof dagre!=="undefined")&&!!window.cytoscapeDagre&&dagreOK;
if(!libsOK){ document.getElementById("libwarn").style.display="block"; }

var LS_KEY="pmx_dt_state";
function defaultState(){return {view:"all", family:null, selected:null, expandedAxes:[], checks:{}};}
var state=defaultState();
function loadState(){
  try{ var raw=localStorage.getItem(LS_KEY); if(!raw) return;
    var s=JSON.parse(raw); if(s&&typeof s==="object"){ state=Object.assign(defaultState(),s); }
  }catch(e){ console.warn("[pmx-dt] localStorage corrupt → 초기화:",e);
    try{localStorage.removeItem(LS_KEY);}catch(_){ } state=defaultState(); }
}
function saveState(){ try{ localStorage.setItem(LS_KEY,JSON.stringify(state)); }catch(e){ } }

/* ===== 1. STYLE (kind별 shape = [7-1] 1:1) + Lock7 highlight ===== */
var STYLE=[
  {selector:"node",style:{"label":"data(label)","text-wrap":"wrap","text-valign":"center","text-halign":"center",
    "font-size":8,"text-max-width":96,"width":74,"height":38,"background-color":"#cfe0ff","border-width":1,
    "border-color":"#5b8def","color":"#16314f","overlay-opacity":0,"overlay-color":"#FFD700","overlay-padding":10}},
  {selector:'node[kind="transform"]',style:{"shape":"ellipse","background-color":"#7fb2ff","border-color":"#3f78d6"}},
  {selector:'node[kind="detect"]',style:{"shape":"ellipse","background-color":"#bcd9ff","border-style":"dashed","border-width":2,"border-color":"#3f78d6"}},
  {selector:'node[kind="verify"]',style:{"shape":"ellipse","background-color":"#bcd9ff","border-style":"dashed","border-width":2,"border-color":"#3f78d6"}},
  {selector:'node[kind="route"]',style:{"shape":"hexagon","background-color":"#ffcf80","border-color":"#d57b1f","border-width":2,"width":86,"height":44}},
  {selector:'node[kind="axis"]',style:{"shape":"hexagon","background-color":"#ffe1a8","border-color":"#e09b3d","border-width":2,"width":92,"height":50,"font-size":9,"font-weight":"bold"}},
  {selector:'node[kind="stage"]',style:{"shape":"round-rectangle","background-color":"#d1c4e9","border-color":"#7e57c2","border-width":3,"width":120,"height":46}},
  {selector:'node[kind="branch"]',style:{"shape":"diamond","background-color":"#ffb74d","border-color":"#e09b3d","width":92,"height":66}},
  {selector:'node[kind="state"]',style:{"shape":"ellipse","background-color":"#fff3df","border-color":"#e0b070","width":58,"height":26,"font-size":7}},
  /* ★ 문제 B 종착유형 색-코딩: 완주=녹 / QUARANTINE=주황(사람개입대기) / INVALID=slate(복원불가) / UNSUP=회보라(미지원). fill=상태, 하이라이트=border(#FFD700) → 채널 분리 */
  {selector:'node[kind="terminal_auto"]',style:{"shape":"star","background-color":"#43a047","border-color":"#2e7d32","border-width":2,"color":"#fff","width":78,"height":78}},
  {selector:'node[kind="terminal_repair"]',style:{"shape":"round-rectangle","background-color":"#a5d6a7","border-color":"#2e7d32","border-width":2}},
  {selector:'node[kind="terminal_quar"]',style:{"shape":"round-rectangle","background-color":"#ffa726","border-color":"#e65100","border-width":2}},
  {selector:'node[kind="terminal_unsup"]',style:{"shape":"octagon","background-color":"#9e8aa8","border-color":"#6d5f80","border-width":2,"color":"#fff"}},
  {selector:'node[kind="terminal_invalid"]',style:{"shape":"octagon","background-color":"#546e7a","border-color":"#37474f","border-width":2,"color":"#fff"}},
  {selector:'node[kind="terminal_q"]',style:{"shape":"rectangle","background-color":"#ef5350","border-color":"#b71c1c","color":"#fff"}},
  {selector:'node[qstatus="static"]',style:{"background-color":"#b0bec5","border-style":"dashed","border-color":"#78909c","color":"#37474f"}},
  {selector:'node[?deferred]',style:{"background-color":"#eceff1","border-style":"dashed","border-color":"#9e9e9e","color":"#90a4ae","opacity":0.72}},
  /* edges */
  {selector:"edge",style:{"width":2,"line-color":"#9e9e9e","target-arrow-color":"#9e9e9e","target-arrow-shape":"triangle","curve-style":"bezier","arrow-scale":0.85}},
  {selector:'edge[ekind="backbone"]',style:{"width":3,"line-color":"#7d8b9a","target-arrow-color":"#7d8b9a"}},
  {selector:'edge[ekind="attach"]',style:{"width":1.4,"line-color":"#c7d2dd","target-arrow-color":"#c7d2dd","line-style":"dotted","arrow-scale":0.7}},
  /* ★ 문제 A: conditional(c→Q 분기) 골드/앰버 dashed·굵게 — resting 색은 Lock 미규정(비-frozen). 하이라이트 #FFF8B0과 '노랑 계열' 일관 */
  {selector:'edge[ekind="conditional"]',style:{"line-style":"dashed","line-dash-pattern":[10,5],"line-color":"#c9920e","target-arrow-color":"#c9920e","width":3.6}},
  {selector:'edge[ekind="terminal_routing"]',style:{"width":3.2,"line-color":"#8d3b3b","target-arrow-color":"#8d3b3b","line-style":"solid","target-arrow-shape":"tee"}},
  /* ★ recover(Q→c, human-in-the-loop): 파랑 dashed — 자동 라우팅 아님(시각·범례서 명확 구분) */
  {selector:'edge[ekind="recover"]',style:{"line-style":"dashed","line-dash-pattern":[4,4],"line-color":"#1976d2","target-arrow-color":"#1976d2","target-arrow-shape":"vee","width":2.6,"curve-style":"bezier","label":"data(label)","font-size":7,"color":"#1565c0","text-background-color":"#fff","text-background-opacity":0.85,"text-background-padding":1}},
  {selector:'edge[ekind="deferred"]',style:{"width":1.6,"line-color":"#b39ddb","target-arrow-color":"#b39ddb","line-style":"dashed","opacity":0.6}},
  /* highlight (Lock 7) */
  {selector:".dim",style:{"opacity":0.18}},
  {selector:".famdim",style:{"opacity":0.1}},
  {selector:"node.hl",style:{"border-width":3,"border-color":"#FFD700"}},
  {selector:"edge.hlSingle",style:{"line-color":"#FFD700","target-arrow-color":"#FFD700","width":5,"line-style":"solid","z-index":900,"opacity":1}},
  {selector:"edge.hlCond",style:{"line-color":"#FFF8B0","target-arrow-color":"#FFF8B0","width":3,"line-style":"dashed","z-index":900,"opacity":1}},
  /* recover 강조(선택 노드에 incident한 human-loop만) — Lock7 노랑과 분리된 파랑, 풀 라벨 */
  {selector:"edge.hlRecover",style:{"line-color":"#1565c0","target-arrow-color":"#1565c0","width":3.6,"line-style":"dashed","label":"↩ 사람개입 후 복귀","font-size":9,"color":"#0d47a1","z-index":901,"opacity":1}},
  {selector:"node.current",style:{"border-width":4,"border-color":"#111","z-index":9999,"opacity":1}}
];
function layoutOpts(extra){
  return Object.assign({name:dagreOK?"dagre":"breadthfirst",rankDir:"LR",directed:true,fit:true,padding:28,
    animate:false,nodeSep:26,rankSep:62,spacingFactor:0.95},extra||{});
}

/* ===== 2. cytoscape 인스턴스 + ★ GAP-25 자가측정(실 backbone 레이아웃) ===== */
window.__PERF__=null;
var t0=performance.now();
var cy=cytoscape({container:document.getElementById("cy"),elements:ELES,style:STYLE,layout:{name:"preset"},
  wheelSensitivity:0.2,minZoom:0.05,maxZoom:3});
var t1b=performance.now();
function runInitialLayout(){
  var L=cy.layout(layoutOpts());
  L.one("layoutstop",function(){
    var t3=performance.now();
    requestAnimationFrame(function(){
      var t4=performance.now();
      var vis=cy.nodes(":visible").length;
      window.__PERF__={visibleNodes:vis,t_construct:Math.round(t1b-t0),t_layout:Math.round(t3-t1b),
        t_total:Math.round(t4-t0),t_expand:null,gate:10000};
      setPerfBadge();
      console.log("[pmx-dt][perf]",window.__PERF__);
    });
  });
  L.run();
}
function setPerfBadge(){
  var p=window.__PERF__, b=document.getElementById("perfBadge"); if(!p||!b) return;
  var pass=p.t_total<=p.gate; b.className=pass?"pass":"fail";
  b.textContent=(pass?"✅":"❌")+" "+p.visibleNodes+" nodes · dagre "+ms(p.t_layout)+" · total "+ms(p.t_total)+(p.t_expand!=null?" · expand "+ms(p.t_expand):"");
  b.title="GAP-25 DoD#6 게이트: dagre 레이아웃<10s · collapsed "+p.visibleNodes+" nodes ≪ 5000 ("+(pass?"PASS":"FAIL")+")";
}

/* ===== 3. highlight (Lock 7: upstream backtrace ∪ downstream BFS) ===== */
/* ★ recover(Q→c, human-in-the-loop) edge는 auto-flow union에서 제외 — Lock7 의미(자동 경로 union) 보존.
   recover는 선택 노드에 incident할 때만 파랑 강조(hlRecover), 자동 경로와 명확히 구분. */
function flowNeighborhood(node){
  var seen=node;
  ["down","up"].forEach(function(dir){
    var frontier=node, guard=0;
    while(frontier.nonempty() && guard++<300){
      var og=(dir==="down")?frontier.outgoers():frontier.incomers();
      var edges=og.edges('[ekind != "recover"]');          // human-loop 제외
      var nodes=(dir==="down")?edges.targets():edges.sources();
      var fresh=nodes.difference(seen);                    // 새로 발견한 노드
      seen=seen.union(edges).union(nodes);
      frontier=fresh;                                      // fresh 없으면 다음 회차 nonempty=false → 종료
    }
  });
  return seen;
}
function clearHighlight(){ cy.elements().removeClass("dim hl hlSingle hlCond hlRecover current"); cy.nodes().style("overlay-opacity",0); }
function highlight(node){
  clearHighlight();
  var hl=flowNeighborhood(node);
  cy.elements().addClass("dim"); hl.removeClass("dim");
  hl.nodes().addClass("hl");
  hl.edges().forEach(function(e){ e.addClass(e.data("conditional")?"hlCond":"hlSingle"); });
  node.connectedEdges('[ekind="recover"]').removeClass("dim").addClass("hlRecover"); // 선택 노드의 human-loop만 강조
  node.removeClass("hl dim").addClass("current");
  startPulse(node);
}
function startPulse(node){
  (function step(up){
    if(!node.hasClass("current")){ node.style("overlay-opacity",0); return; }
    node.animate({style:{"overlay-opacity":up?0.38:0.0}},{duration:500,complete:function(){ step(!up); }});
  })(true);
}

/* ===== 4. 노드 클릭 dispatch + split 패널 ===== */
function onNodeTap(node){
  var kind=node.data("kind"), id=node.id();
  if(kind==="axis"){ toggleAxis(id); }       // axis: state 펼침/접기
  state.selected=id; saveState();
  openSplit();
  var html;
  if(kind==="terminal_q") html=renderQPanel(id);
  else if(kind&&kind.indexOf("terminal")===0) html=renderTerminalPanel(id);
  else if(kind==="branch"||kind==="axis"||kind==="stage"||kind==="state") html=renderNodePanel(id,kind);
  else html=renderCPanel(id);               // transform/detect/verify/route
  setPanel(titleFor(node),html);
  wireChecklist(id);
  highlight(node);
  setBreadcrumb(node);
  refit();
}
function titleFor(node){
  var k=node.data("kind"), lbl=(node.data("label")||"").split("\n")[0];
  if(k==="terminal_q") return "Q-code terminal · "+lbl;
  if(k&&k.indexOf("terminal")===0) return "Terminal · "+lbl;
  if(k==="branch"||k==="axis") return "노드 · "+lbl;
  if(k==="stage") return "정규화 stage · "+lbl;
  if(k==="state") return "axis state · "+lbl;
  return "c-단위체 · "+lbl;
}

/* ---- (7-3) c 4섹션: transform/detect/verify/route ---- */
function renderCPanel(id){
  var c=CUNITS[id]; if(!c) return renderNodePanel(id,"node");
  var h="";
  h+='<div class="sect"><h3>(A) precondition_checklist_ko</h3><div class="body"><ul class="chklist" id="chk">';
  (c.precondition_checklist_ko||[]).forEach(function(t,i){
    h+='<li><input type="checkbox" class="ckbox" data-i="'+i+'" id="ck'+i+'"><label for="ck'+i+'">'+esc(t)+'</label></li>'; });
  h+='</ul><div class="badge-ok" id="chkbadge">✓ 위치 확인됨</div></div></div>';
  h+='<div class="sect"><h3>(B) Identity</h3><div class="body">';
  h+='<div class="kv"><span class="k">c_name_ko</span> · <b>'+esc(c.c_name_ko)+'</b></div>';
  h+='<div class="kv"><span class="k">srp_intent</span> · <span class="mono">'+esc(c.srp_intent)+'</span></div>';
  h+='<div class="kv"><span class="k">kind</span> '+esc(c.kind)+' · <span class="k">cost</span> '+c.cost+
     ' · <span class="k">layer</span> '+esc(c.layer_pair)+' · <span class="k">req_detect</span> '+esc(c.requires_detection_by||"null")+'</div>';
  h+='<div class="kv"><span class="k">family</span> <span class="pill">'+esc(c.fam)+'</span> · <span class="k">영향 strand</span> <b>'+c.influence+'</b></div>';
  h+='<div class="snlabel">llm_prompt</div><div class="prompt">'+esc(c.llm_prompt)+'</div>';
  h+='<div class="kv" style="margin-top:6px"><span class="k">c_id</span> <b>'+esc(c.c_id)+'</b> · <span class="k">ref</span> '+esc(c.ref)+'</div></div></div>';
  if(c.kind==="transform"){
    h+='<div class="sect"><h3>(C) before / after — 변경 셀 강조</h3><div class="body">'+renderBeforeAfter(c.before,c.after)+'</div></div>';
  }else{
    h+='<div class="sect"><h3>(C) verify_visualization</h3><div class="body">'+renderVV(c.verify_visualization,c.can_route_to_q)+'</div></div>';
  }
  h+='<div class="sect"><h3>(D) snippet (R 상 / Python 하)</h3><div class="body">';
  h+='<div class="snlabel">R</div><pre class="snip">'+hlComments(c.r_snippet)+'</pre>';
  h+='<div class="snlabel">Python</div><pre class="snip">'+hlComments(c.python_snippet)+'</pre></div></div>';
  return h;
}
function hlComments(s){
  return esc(s).split("\n").map(function(ln){ return /^\s*#/.test(ln)?'<span class="cmt">'+ln+'</span>':ln; }).join("\n");
}
function parseRow(line){ return line.split(","); }
function cellTd(cell){
  var m=/^\*\*([\s\S]*)\*\*$/.exec(cell.trim());
  return m?'<td class="chg">'+esc(m[1])+'</td>':'<td>'+esc(cell)+'</td>';
}
function csvTable(title,csv){
  if(!csv) return "";
  var rows=String(csv).split("\n").filter(function(r){return r.length;});
  if(!rows.length) return "";
  var h='<div class="snlabel">'+title+'</div><table class="toy">';
  rows.forEach(function(r,ri){
    var cells=parseRow(r);
    h+="<tr>"+cells.map(function(cell){
      if(ri===0){ var m=/^\*\*([\s\S]*)\*\*$/.exec(cell.trim()); return "<th>"+esc(m?m[1]:cell)+"</th>"; }
      return cellTd(cell);
    }).join("")+"</tr>";
  });
  return h+"</table>";
}
function renderBeforeAfter(before,after){
  if(!before&&!after) return "<i>n/a</i>";
  return csvTable("before",before)+csvTable("after (노란 셀 = 변경)",after);
}
function renderVV(vv,canQ){
  if(!vv){ var q=(canQ||[]); return '<i>(transform/route — verify_visualization 없음)</i>'+(q.length?'<div class="kv" style="margin-top:5px"><span class="k">can_route_to_q</span> '+q.map(function(x){return '<span class="pill q">'+esc(x)+'</span>';}).join("")+'</div>':""); }
  var h='<div class="kv"><span class="k">target_columns</span> '+(vv.target_columns||[]).map(function(x){return '<span class="pill">'+esc(x)+'</span>';}).join("")+'</div>';
  h+='<div class="kv"><span class="k">criterion</span> '+esc(vv.criterion_predicate_ko)+'</div>';
  h+='<div class="kv"><span class="k">pass →</span> <span class="pill pass">'+esc(vv.pass_route_to||"next")+'</span></div>';
  h+='<div class="kv"><span class="k">fail →</span> '+(vv.fail_route_to?'<span class="pill q">'+esc(vv.fail_route_to)+'</span>':'<span class="pill">없음</span>')+'</div>';
  return h;
}

/* ---- (7-4) Q-code terminal: A'~D' ---- */
function renderQPanel(id){
  var q=QINFO[id]; if(!q) return renderTerminalPanel(id);
  var defer=(q.q_status==="unreached");
  var h='<div class="sect"><h3>(A\') 도달 사유 — conditional routing'+(defer?' <span class="deferbadge">deferred(미배선)</span>':'')+'</h3><div class="body">';
  if(defer){ h+='<div class="kv" style="color:#6a3fb0">★ 고립 deferred placeholder — source c 미배선(검증 strand 0). 배선 시 conditional edge 생성(후속).</div>'; }
  else if(q.reach.length){
    q.reach.forEach(function(r){ h+='<div class="reachrow"><span class="pill q">'+esc(r.from)+'</span> <span class="k">('+esc(r.from_kind)+', '+esc(r.source)+')</span> → '+esc(id)+' · strand '+r.strand_count+(r.realizing_route_c&&r.realizing_route_c.length?' · realize '+r.realizing_route_c.join(","):"")+'</div>'; });
  } else { h+='<div class="kv">incoming wired c: '+(q.incoming_wired_c||[]).map(function(x){return '<span class="pill">'+esc(x)+'</span>';}).join("")+'</div>'; }
  h+='<div class="kv" style="margin-top:5px"><span class="k">trigger</span> '+esc(q.trigger_condition)+'</div>';
  h+='<div class="kv"><span class="k">name</span> '+esc(q.name)+' · <span class="k">q_status</span> '+esc(q.q_status)+' · <span class="k">영향 strand</span> <b>'+q.influence+'</b></div></div></div>';
  h+='<div class="sect"><h3>(B\') clarification_to_sponsor</h3><div class="body"><ul style="margin:0;padding-left:18px;font-size:13px">';
  (q.clarification_to_sponsor||[]).forEach(function(t){ h+='<li>'+esc(t)+'</li>'; });
  h+='</ul></div></div>';
  h+='<div class="sect"><h3>(C\') human_decision_point</h3><div class="body">'+esc(q.human_decision_point)+
     '<div class="kv" style="margin-top:6px"><span class="k">routing_cost</span> '+q.routing_cost+' · <span class="k">effort</span> '+esc(q.human_effort_score)+'/10 · <span class="k">ref</span> '+esc(q.ref)+'</div></div></div>';
  var rec=q.recover_to_c_id, recWired=(rec&&CUNITS[rec]);
  h+='<div class="sect"><h3>(D\') recover_to_c_id — ↩ 사람 개입 후 복귀(human-in-the-loop)</h3><div class="body">복귀 지점 <b>'+esc(rec||"—")+'</b>';
  if(defer){
    h+='<div class="kv" style="margin-top:5px;color:#6a3fb0">★ 이 Q는 unreached(source c 미배선) 고립 placeholder → recover edge 생략. 복귀 타깃 '+esc(rec)+(recWired?'는 wired이나 Q 자체 미배선이라 일괄 이월':'도 미배선')+'.</div>';
  }else if(recWired){
    h+=' <button class="btn" id="recoverBtn" data-to="'+esc(rec)+'">↩ '+esc(rec)+' 로 복귀</button>';
    h+='<div class="kv" style="margin-top:5px;color:#1565c0">tree에 ↩ 파랑 점선 edge로 표시 — <b>자동 라우팅 아님</b>(사람이 sponsor clarification 응답 후 재진입).</div>';
  }else{
    h+='<div class="kv" style="margin-top:5px;color:#b35a16">★ 복귀 지점 '+esc(rec)+' 미배선(현재 57-wired 밖) → tree edge 생략(은폐 0). 배선 시 ↩ edge 생성(후속).</div>';
  }
  h+='</div></div>';
  return h;
}

/* ---- (노드클릭) branch/axis/stage/state: 3섹션 ---- */
function renderNodePanel(id,kind){
  var info=NODEINFO[id];
  if(kind==="state"){
    var ax=id.split("::")[0];
    return '<div class="sect"><h3>N1 — 역할</h3><div class="body">axis '+esc(ax)+' 의 state <b>'+esc(id.split("::")[1]||id)+'</b></div></div>'+
           '<div class="sect"><h3>N2 — 분기·병합 정보</h3><div class="body">이 cell을 지나는 sc 경로가 '+esc(ax)+' 축에서 이 state로 분류됨</div></div>'+
           '<div class="sect"><h3>N3 — 영향 strand 수</h3><div class="body"><i>state별 집계는 후속(axis 단위 집계 표시)</i></div></div>';
  }
  if(kind==="stage"){
    return '<div class="sect"><h3>N1 — 역할</h3><div class="body">L-4→L-5 mess 정규화 stage (commutative normalization 층). 멤버 c는 collapse 기본 — 개별 c 노드로 표시됨.</div></div>'+
           '<div class="sect"><h3>N2 — 분기·병합 정보</h3><div class="body">bundle 노드화는 Phase 7 step-2 결정 대기(GAP-27B). 현 bundles=[].</div></div>'+
           '<div class="sect"><h3>N3 — 영향 strand 수</h3><div class="body"><i>멤버 c 각각의 영향 strand는 c 클릭 시 표시</i></div></div>';
  }
  if(!info) return '<div class="sect"><h3>노드</h3><div class="body">'+esc(id)+'</div></div>';
  var h='<div class="sect"><h3>N1 — 역할</h3><div class="body">'+esc(info.role)+'<div class="kv" style="margin-top:4px"><span class="k">ref</span> '+esc(info.ref||"")+'</div></div></div>';
  h+='<div class="sect"><h3>N2 — 분기·병합 정보</h3><div class="body">'+esc(info.bm);
  if(info.states){ h+='<div class="navrow">'+info.states.map(function(s){return '<span class="pill">'+esc(s)+'</span>';}).join("")+'</div>';
    h+='<button class="btn" id="axisToggle" data-ax="'+esc(id)+'">'+(state.expandedAxes.indexOf(id)>=0?"▲ state 접기":"▼ state 펼치기")+'</button>'; }
  h+='</div></div>';
  h+='<div class="sect"><h3>N3 — 영향 strand 수</h3><div class="body"><b>'+info.strands+'</b> strand</div></div>';
  return h;
}
function renderTerminalPanel(id){
  var info=NODEINFO[id]||{role:"terminal",bm:"종착",strands:"—"};
  return '<div class="sect"><h3>Terminal</h3><div class="body">'+esc(info.role)+'<div class="kv" style="margin-top:4px"><span class="k">ref</span> '+esc(info.ref||"")+'</div></div></div>'+
         '<div class="sect"><h3>영향 strand 수</h3><div class="body"><b>'+info.strands+'</b> strand</div></div>';
}

/* ===== 5. axis state collapse-by-default (7-2b 메커니즘 전용; 증분 expand) ===== */
function axisStateEles(ax){
  var sts=AXIS_STATES[ax]||[], out=[];
  sts.forEach(function(s,i){
    var sid=ax+"::"+s;
    out.push({data:{id:sid,kind:"state",label:s}});
    out.push({data:{id:"se_"+ax+"_"+i,source:ax,target:sid,ekind:"attach"}});
  });
  return out;
}
function toggleAxis(ax){
  var idx=state.expandedAxes.indexOf(ax);
  if(idx>=0){ collapseAxis(ax); } else { expandAxis(ax); }
}
function expandAxis(ax){
  if(state.expandedAxes.indexOf(ax)>=0) return;
  var tE0=performance.now();
  cy.add(axisStateEles(ax));
  state.expandedAxes.push(ax); saveState();
  cy.layout(layoutOpts()).run();
  var tE1=performance.now();
  if(window.__PERF__){ window.__PERF__.t_expand=Math.round(tE1-tE0); window.__PERF__.visibleNodes=cy.nodes(":visible").length; setPerfBadge(); }
}
function collapseAxis(ax){
  var idx=state.expandedAxes.indexOf(ax); if(idx<0) return;
  cy.remove(cy.nodes('[kind="state"]').filter(function(n){return n.id().indexOf(ax+"::")===0;}));
  state.expandedAxes.splice(idx,1); saveState();
  cy.layout(layoutOpts()).run();
}

/* ===== 6. Family view (전체 | Family — mess 정규화 family) ===== */
function buildFamSel(){
  var sel=document.getElementById("famSel"), fams=Object.keys(FAMILIES).sort();
  sel.innerHTML='<option value="">(모든 family)</option>'+fams.map(function(f){return '<option value="'+esc(f)+'">'+esc(f)+' ('+FAMILIES[f].length+')</option>';}).join("");
}
function applyFamily(){
  cy.nodes().removeClass("famdim");
  if(state.view!=="family"||!state.family){ return; }
  var keep={}; (FAMILIES[state.family]||[]).forEach(function(c){ keep[c]=1; });
  cy.nodes().forEach(function(n){
    var c=n.data("fam");
    if(n.data("kind")&&n.data("kind").indexOf("term")===0){ return; }     // terminal 유지
    if(["branch","axis","stage"].indexOf(n.data("kind"))>=0){ return; }   // backbone 유지
    if(!keep[n.id()]) n.addClass("famdim");
  });
}
function showView(v){
  state.view=v; saveState();
  document.getElementById("tabAll").classList.toggle("active",v==="all");
  document.getElementById("tabFam").classList.toggle("active",v==="family");
  document.getElementById("famSel").style.display=(v==="family")?"inline-block":"none";
  applyFamily();
}

/* ===== 7. breadcrumb (N0 → 현재) ===== */
function setBreadcrumb(node){
  var bc=document.getElementById("breadcrumb");
  var chain=[node], cur=node, guard=0;
  while(guard++<40){
    var inc=cur.incomers('node[kind="branch"], node[kind="axis"], node');
    var prev=cur.incomers("edge").sources().filter(function(n){return n.id()!==cur.id();});
    if(prev.empty()) break;
    // 우선순위: backbone 부모 > 그 외
    var pick=prev.filter('[kind="branch"]'); if(pick.empty()) pick=prev;
    cur=pick[0]; if(!cur||chain.indexOf(cur)>=0) break; chain.unshift(cur);
    if(cur.id()==="N0") break;
  }
  bc.innerHTML=chain.map(function(n,i){
    var lbl=(n.data("label")||n.id()).split("\n")[0];
    return '<a class="crumb" data-id="'+esc(n.id())+'">'+esc(lbl)+'</a>'+(i<chain.length-1?' <span style="color:#bbb">›</span>':"");
  }).join(" ");
  Array.prototype.forEach.call(bc.querySelectorAll(".crumb"),function(a){
    a.addEventListener("click",function(){ var n=cy.getElementById(a.getAttribute("data-id")); if(n&&!n.empty()) onNodeTap(n); });
  });
}

/* ===== 8. minimap (canvas, viewport 동기) ===== */
var mm=document.getElementById("minimap"), mctx=mm.getContext("2d");
function drawMinimap(){
  if(!mctx) return;
  var W=mm.width,H=mm.height; mctx.clearRect(0,0,W,H);
  var bb=cy.elements(":visible").boundingBox(); if(!bb||!isFinite(bb.w)||bb.w===0) return;
  var pad=6, sx=(W-2*pad)/bb.w, sy=(H-2*pad)/bb.h, s=Math.min(sx,sy);
  function mx(x){return pad+(x-bb.x1)*s;} function my(y){return pad+(y-bb.y1)*s;}
  mctx.fillStyle="#9ec2ff";
  cy.nodes(":visible").forEach(function(n){ var p=n.position(); mctx.fillRect(mx(p.x)-1,my(p.y)-1,2.4,2.4); });
  var ext=cy.extent();
  mctx.strokeStyle="#d32f2f"; mctx.lineWidth=1;
  mctx.strokeRect(mx(ext.x1),my(ext.y1),(ext.x2-ext.x1)*s,(ext.y2-ext.y1)*s);
  mm._bb=bb; mm._s=s; mm._pad=pad;
}
mm.addEventListener("click",function(ev){
  if(!mm._bb) return;
  var r=mm.getBoundingClientRect(), cx=ev.clientX-r.left, cy2=ev.clientY-r.top;
  var gx=mm._bb.x1+(cx-mm._pad)/mm._s, gy=mm._bb.y1+(cy2-mm._pad)/mm._s;
  cy.animate({center:{eles:cy.collection()},pan:{x:cy.width()/2-gx*cy.zoom(),y:cy.height()/2-gy*cy.zoom()}},{duration:200});
});

/* ===== 9. split / 패널 / 체크리스트 / fit ===== */
function openSplit(){ document.body.classList.add("split"); }
function setPanel(title,html){
  document.getElementById("panelTitle").textContent=title;
  document.getElementById("panelBody").innerHTML=html;
  var rb=document.getElementById("recoverBtn");
  if(rb) rb.addEventListener("click",function(){ var n=cy.getElementById(rb.getAttribute("data-to")); if(n&&!n.empty()) onNodeTap(n); });
  var at=document.getElementById("axisToggle");
  if(at) at.addEventListener("click",function(){ var ax=at.getAttribute("data-ax"); toggleAxis(ax); var n=cy.getElementById(ax); if(n&&!n.empty()) onNodeTap(n); });
}
function wireChecklist(id){
  var saved=(state.checks&&state.checks[id])||[];
  Array.prototype.forEach.call(document.querySelectorAll(".ckbox"),function(b){
    var i=+b.getAttribute("data-i"); b.checked=!!saved[i];
    b.addEventListener("change",function(){ var arr=(state.checks[id]||[]).slice(); arr[i]=b.checked; state.checks[id]=arr; saveState(); updateBadge(); });
  });
  updateBadge();
}
function updateBadge(){
  var boxes=document.querySelectorAll(".ckbox"), badge=document.getElementById("chkbadge");
  if(!badge||!boxes.length) return;
  badge.classList.toggle("show",Array.prototype.every.call(boxes,function(b){return b.checked;}));
}
function clearSelection(){ document.body.classList.remove("split"); clearHighlight(); state.selected=null; saveState(); refit(); }
function refit(){ cy.resize(); requestAnimationFrame(function(){ cy.resize(); cy.fit(undefined,28); drawMinimap(); }); }

/* ===== 10. legend (노드종류 · ★종착유형 · 엣지) + 경계 배너 ===== */
(function(){
  var shapes=[["원 transform","background:#7fb2ff;border-radius:50%"],["점선원 detect·verify","background:#bcd9ff;border-radius:50%;border-style:dashed"],
    ["육각 route","background:#ffcf80"],["육각 axis(접힘)","background:#ffe1a8"],["다이아 branch","background:#ffb74d"],["보라 stage","background:#d1c4e9"]];
  /* ★ 문제 B 종착유형 6+종 — '끊김의 의미' 즉시 이해 */
  var term=[["완주 AUTO/REPAIR(녹)","background:#43a047"],["QUARANTINE 주황·사람개입대기","background:#ffa726"],
    ["Q-code 빨강·답변필요","background:#ef5350"],["미실현 terminal 회색점선·① 대기","background:#b0bec5;border-style:dashed"],
    ["INVALID slate8각·복원불가","background:#546e7a"],["UNSUPPORTED 회보라8각·미지원(tree상 GAP-13 deferred)","background:#9e8aa8"],
    ["미배선·deferred ghost(C·D·E·unreached Q)","background:#eceff1;border-style:dashed"]];
  var edges=[["backbone","background:#7d8b9a"],["attach","background:#c7d2dd;border-style:dotted"],
    ["conditional 분기→Q(골드)","background:#c9920e;border-style:dashed"],["terminal→INVALID(적갈)","background:#8d3b3b"],
    ["↩ recover Q→c(파랑·사람개입후 재진입)","background:#1976d2;border-style:dashed"],
    ["하이라이트 단일(노랑5px)","background:#FFD700"],["분기(옅은노랑)","background:#FFF8B0;border-style:dashed"]];
  function row(items){ return items.map(function(x){return '<span class="lg"><span class="sw" style="'+x[1]+'"></span>'+x[0]+'</span>';}).join(""); }
  document.getElementById("legend").innerHTML=
    '<span class="grp">노드</span>'+row(shapes)+'<span class="sep"></span><span class="grp">종착유형</span>'+row(term)
    +'<span class="sep"></span><span class="grp">엣지</span>'+row(edges);
  /* ★ 경계 배너: oracle 5000 strand 종착 ↔ 57-wired 구현범위 두 축 명확 구분(전 수치 build-time 계산·검증가능) */
  var b=window.DT_BANNER||{}, el=document.getElementById("boundary");
  if(el) el.innerHTML=
    '이 tree는 <b>'+b.total_strands+' strand(oracle 최적경로)</b> 종착 구조를 <span class="ax">현재 구현된 '+b.wired_c+'-wired c</span> 범위로 렌더 (5000 동시표시 아님·D-S3 경로표현). · '
    +'oracle 종착(strands.json 실측): <b>완주 '+b.complete+'</b>(AUTO '+b.auto+'+REPAIR '+b.repair+') · QUARANTINE <b>'+b.quarantine+'</b>(사람개입대기) · INVALID <b>'+b.invalid+'</b>(복원불가) · UNSUPPORTED <b>'+b.unsupported+'</b>(미지원) · realized(pure) <b>'+b.realized_pure+'</b>. · '
    +'<span class="warn">현재 경계</span>: 미배선 c <b>'+b.unwired_c+'</b>(strands 등장·미구현) · 미실현 Q <b>'+b.static_q+'</b>(Q05·Q10) · deferred <b>'+b.deferred_total+'</b>(unreached Q + GAP c). · orchestrator 런타임 지표(완주·realized)는 별도 — 본 배너는 검증가능 수치만.';
})();

/* ===== 11. 이벤트 + 부팅(복원) ===== */
document.getElementById("tabAll").addEventListener("click",function(){ state.family=null; document.getElementById("famSel").value=""; showView("all"); });
document.getElementById("tabFam").addEventListener("click",function(){ showView("family"); });
document.getElementById("famSel").addEventListener("change",function(){ state.family=this.value||null; saveState(); applyFamily(); });
document.getElementById("clearSel").addEventListener("click",clearSelection);
document.getElementById("panelClose").addEventListener("click",clearSelection);
document.getElementById("resetState").addEventListener("click",function(){
  try{localStorage.removeItem(LS_KEY);}catch(e){} state=defaultState();
  cy.remove(cy.nodes('[kind="state"]')); clearSelection(); buildFamSel(); showView("all"); cy.layout(layoutOpts()).run();
});
document.getElementById("zin").addEventListener("click",function(){ cy.zoom(cy.zoom()*1.25); drawMinimap(); });
document.getElementById("zout").addEventListener("click",function(){ cy.zoom(cy.zoom()*0.8); drawMinimap(); });
document.getElementById("zfit").addEventListener("click",refit);
cy.on("tap","node",function(evt){ onNodeTap(evt.target); });
cy.on("tap",function(evt){ if(evt.target===cy){ clearSelection(); } });
cy.on("pan zoom render",function(){ drawMinimap(); });
window.addEventListener("resize",function(){ cy.resize(); drawMinimap(); });

loadState();
buildFamSel();
runInitialLayout();
cy.ready(function(){
  cy.fit(undefined,28);
  (state.expandedAxes||[]).slice().forEach(function(ax){ var i=state.expandedAxes.indexOf(ax); if(i>=0) state.expandedAxes.splice(i,1); expandAxis(ax); });
  if(state.view==="family"){ document.getElementById("famSel").value=state.family||""; }
  showView(state.view||"all");
  if(state.selected){ var n=cy.getElementById(state.selected); if(n&&!n.empty()) onNodeTap(n); }
  setTimeout(drawMinimap,60);
});
</script>
'''


def main():
    data_script = (
        "<script>\n"
        "var ELES=" + js(ELES) + ";\n"
        "var CUNITS=" + js(CUNITS) + ";\n"
        "var QINFO=" + js(QINFO) + ";\n"
        "var NODEINFO=" + js(NODEINFO) + ";\n"
        "var AXIS_STATES=" + js(AXIS_STATES) + ";\n"
        "var FAMILIES=" + js(FAMILIES) + ";\n"
        "var DEFERRED_VIEW=" + js(DEFERRED_VIEW) + ";\n"
        "var DT_STATS=" + js(STATS) + ";\n"
        "var DT_BANNER=" + js(BANNER) + ";\n"
        "</script>\n"
    )
    html = PAGE_HEAD + "\n" + LIBS + "\n" + data_script + APP_JS + PAGE_TAIL
    out = ROOT / "render" / "index.html"
    out.write_text(html, encoding="utf-8")
    kb = len(html.encode("utf-8")) / 1024.0
    n_nodes = sum(1 for e in ELES if "source" not in e["data"])
    n_edges = sum(1 for e in ELES if "source" in e["data"])
    print("[build_html] wrote %s" % out)
    print("[build_html] size = %.1f KB" % kb)
    print("[build_html] elements: %d nodes + %d edges = %d" % (n_nodes, n_edges, len(ELES)))
    print("[build_html] canonical: c=%d Q=%d axis=%d branch=%d proc=%d | attach=%d cond=%d termr=%d" % (
        len(C_IDS), len(Q_IDS), len(AXIS_IDS), len(BRANCH_IDS), len(PROC_IDS), len(ATTACH), len(COND), len(TERMR)))
    print("[build_html] families: %s" % ", ".join("%s:%d" % (k, len(v)) for k, v in sorted(FAMILIES.items())))


if __name__ == "__main__":
    main()
