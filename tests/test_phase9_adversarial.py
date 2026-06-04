"""Phase 9 — 적대적 검증: 교차-SSOT 불변식 durable guard ("숨은 GAP 0" 회귀방지).

PROMPTS Phase 9(mode: skeptical) + DoD/Lock + 발주 적대점검을, 자기검증 대신 pytest로 고정한다
(Hallucination 차단 #6 / DoD #2). test = "참 증명", issues/phase9_adversarial_review.md = "무엇을
증명했는지 설명"(역할 분리). 각 test는 wired scope(orchestrator REGISTRY=57) 내 무모순을 검증하고,
미배선 tail은 "현재 경계의 정직한 미구현"으로 documented됨을 확인한다(은폐 0).

검증 대상(번호=review doc §C 항목):
  P9-1  D-S1: dangling requires_detection_by 0 (transform 전부 detection 보유).
  P9-2  D-S4(wired): 배선 c.can_route_to_q → conditional edge 누락 0.
  P9-3  exercised Q 고립 0 (incoming conditional ≥1).
  P9-4  SSOT recover 무결성: q.recover_to_c_id 전부 c_units 존재.
  P9-5  SSOT strand 무결성: strand c_seq c_id·q_code 전부 존재 + terminal/q_code coupling.
  P9-6  vocab/anchors(G1): can_route_to_q ⊆ q_codes ⊆ anchors.q_codes.
  P9-7  scope_out 0 (deferred.scope_out_edges 빈 + stats 0) — GAP-28 Decision C.
  P9-8  unreached Q documented + router 전부 미배선(정직한 경계, D-S4 위반 아님).
  P9-9  anchors root 위치 로드(GAP-23 경로 drift를 현실로 고정).
  P9-10 banner 수치 build-time 독립 재계산 == index.html 임베디드(렌더 정직성).
  P9-11 C1(DoD#3): 모든 c(122) ≥1 strand 등장(dead c 0).
  P9-12 recover 렌더 정직성: 미배선 recover 타깃은 알려진 omit 집합(잘못된 라우팅 주장 0).

★ 2nd cycle(2026-06-03, 1st 미검사 공격면 — recipe-emit·Direction C 델타 적대검사, DoD#5 critical 0 ×2):
  P9-13 (d) decision_tree stats 전부 raw SSOT 1차원리 재계산과 bit-exact(P9-10 심화 — stored stat 신뢰 제거).
  P9-16 (b) bundles=[] 정당화: 완전배선 정규화-transform run 0 + 미배선 정규화 후보 ≥1(GAP-39 정확화).
  P9-17 (b) closure_proof INV(119/122·C_dead 3) ↔ live SSOT 정합(Direction C 시제정정 number-drift 0).
  P9-18 (a) recipe_emitter engine/SSOT import 0 + engine 식별자 참조 0 (M2 무의존 구조 가드).
  P9-19 (a) emit_recipe purity: structure 무변이 + raw conc 미누출 + status='described, not executed'.
  P9-20 (a+e) 깨진 입력에 guard 발화(non-vacuous): fake c_id·제거 conditional edge·합성 scope-out.
  (P9-14 terminal reconcile·P9-15 recover 14는 거장 결정으로 durable test 아님 — review doc 표·_matrix [doc] 행.)

본 모듈은 `python3 tests/test_phase9_adversarial.py`로 직접 실행 시 수치 매트릭스를 출력한다
(review doc 증거 appendix용). pytest 하에서는 각 불변식을 단언한다.
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
QCODES = {q["q_id"]: q for q in
          json.loads((PROJECT_ROOT / "spec" / "q_codes.json").read_text(encoding="utf-8"))}
STRANDS = json.loads((PROJECT_ROOT / "spec" / "strands.json").read_text(encoding="utf-8"))

from src.orchestrator import REGISTRY  # noqa: E402  — wired 57 (배선 SSOT)

REG = set(REGISTRY)
COST = {cid: c["cost"] for cid, c in CUNITS.items()}
QSET = set(QCODES)
ANCHOR_QS = set(ANCHORS["q_codes"])
COND = [(e["from"], e["to"]) for e in TREE["conditional_routing"]]
CONDSET = set(COND)
COND_TARGETS = {to for _, to in COND}
QPART = TREE["stats"]["q_partition"]
DEFERRED = TREE["deferred"]
STRAND_CS = {c for s in STRANDS for c in s["c_sequence"]}
INDEX_HTML = PROJECT_ROOT / "render" / "index.html"

# closure_proof.md INV-3 / strands_stats.md §6: 문서화된 C_dead(C_used 119 / C_all 122).
# 셋 다 미배선 fail-branch ROUTE c — best-strand(pass-only)는 미통과, 배선 시 D-S4 conditional edge로 편입.
DOCUMENTED_CDEAD = ["c0042", "c0043", "c0333"]

# ── 2nd cycle (P9-13..P9-20) 추가 SSOT 파생 상수 ──
ROUTE_C = {c for c in REG if CUNITS[c].get("kind") == "route"}   # wired ROUTE c (pure/terminal 정산)
PROC_FAIL_TERMINALS = ("INVALID", "UNSUPPORTED")
_PC_LITERAL = re.compile(r"'([A-Z0-9-]+)'")                      # postcond 리터럴 토큰(결정론적 파싱)
CLOSURE_PROOF = (PROJECT_ROOT / "spec" / "closure_proof.md").read_text(encoding="utf-8")
RECIPE_SRC = (PROJECT_ROOT / "src" / "adapter" / "recipe_emitter.py").read_text(encoding="utf-8")


# ───────────────────── 불변식 계산 helper (단언과 매트릭스가 공유) ─────────────────────

def dangling_detection():
    """transform 중 requires_detection_by 누락, 또는 존재하지 않는 c 지목."""
    null_tf = [cid for cid, c in CUNITS.items()
               if c["kind"] == "transform" and not c.get("requires_detection_by")]
    dangling = [(cid, c["requires_detection_by"]) for cid, c in CUNITS.items()
                if c.get("requires_detection_by") and c["requires_detection_by"] not in CUNITS]
    return null_tf, dangling


def missing_ds4():
    """배선 c × can_route_to_q 중 conditional edge 부재 쌍."""
    return [(cid, q) for cid in REG
            for q in (CUNITS[cid].get("can_route_to_q") or [])
            if (cid, q) not in CONDSET]


def isolated_exercised_q():
    return [q for q in QPART["exercised"] if q not in COND_TARGETS]


def bad_recover():
    return [(qid, q.get("recover_to_c_id")) for qid, q in QCODES.items()
            if q.get("recover_to_c_id") not in CUNITS]


def bad_strand_refs():
    bad_c = sorted(STRAND_CS - set(CUNITS))
    bad_q = sorted({s["q_code"] for s in STRANDS
                    if s.get("q_code") is not None and s["q_code"] not in QSET})
    coupling = sum(1 for s in STRANDS
                   if (s["terminal"] == "QUARANTINE") != (s.get("q_code") is not None))
    return bad_c, bad_q, coupling


def vocab_anchor_violations():
    used_q = {q for c in CUNITS.values() for q in (c.get("can_route_to_q") or [])}
    not_in_qset = sorted(used_q - QSET)
    qset_not_anchor = sorted(QSET - ANCHOR_QS)
    return not_in_qset, qset_not_anchor


def scope_out_state():
    return (DEFERRED["scope_out_edges"],
            TREE["stats"]["scope_out_edges"],
            TREE["stats"]["scope_out_strands"])


def unreached_audit():
    """unreached Q 각: deferred 문서화 + 배선 router 0 + conditional target 부재."""
    documented = {d["q"] for d in DEFERRED["unreached_q"]}
    rows = []
    for q in QPART["unreached"]:
        wired_routers = [cid for cid in REG if q in (CUNITS[cid].get("can_route_to_q") or [])]
        rows.append({
            "q": q,
            "documented": q in documented,
            "wired_routers": wired_routers,
            "in_cond_targets": q in COND_TARGETS,
        })
    return rows


def anchors_location():
    return (PROJECT_ROOT / "anchors.json").is_file(), (PROJECT_ROOT / "spec" / "anchors.json").is_file()


def banner_recompute():
    """build_html.boundary_stats를 독립 재현해 index.html 임베디드 DT_BANNER와 비교."""
    from collections import Counter
    term = Counter(s["terminal"] for s in STRANDS)
    computed = {
        "total_strands": len(STRANDS),
        "wired_c": len(REG),
        "auto": term.get("AUTO", 0),
        "repair": term.get("REPAIR", 0),
        "complete": term.get("AUTO", 0) + term.get("REPAIR", 0),
        "quarantine": term.get("QUARANTINE", 0),
        "invalid": term.get("INVALID", 0),
        "unsupported": term.get("UNSUPPORTED", 0),
        "realized_pure": TREE["stats"]["pure_realized_strands"],
        "unwired_c": len(STRAND_CS - REG),
        "static_q": len(QPART["static_no_strand"]),
        "deferred_total": len(DEFERRED["unreached_q"]) + len(DEFERRED["spec_decisions"]),
    }
    html = INDEX_HTML.read_text(encoding="utf-8")
    m = re.search(r"var DT_BANNER=(\{[^}]*\})", html)
    embedded = json.loads(m.group(1)) if m else None
    return computed, embedded


def c1_dead_c():
    """DoD#3 C1: 모든 c가 ≥1 strand 등장. 미등장 = dead c 후보."""
    return sorted(set(CUNITS) - STRAND_CS)


def recover_omitted_targets():
    """recover_to_c_id 중 미배선 타깃(렌더가 정직히 omit해야 하는 집합)."""
    return sorted({q["recover_to_c_id"] for q in QCODES.values()
                   if q.get("recover_to_c_id") not in REG and q.get("recover_to_c_id") in CUNITS})


# ───────────── 2nd cycle helpers (P9-13..P9-20; 1st 12 미검사 공격면 a–e) ─────────────
# ★ P9-14(terminal reconcile)·P9-15(recover 14)는 durable test 아님(거장 결정: test 위생) —
#   P9-13(stats 1차원리 재계산)이 terminal_strands 315를 이미 bit-exact 포섭하고, recover 14는
#   정당한 미래 배선(Q10→c0330)에 brittle하므로 review doc 표로만 기록. _matrix는 [doc] 행으로 노출.

def recompute_tree_stats():
    """(P9-13, surface d) build_decision_tree.py stats를 raw SSOT(strands+c_units+REGISTRY)에서 1차원리 재현.
    P9-10은 stored stat(realized_pure/static_q)을 신뢰; 여기선 독립 재계산해 bit-exact 대조한다."""
    q_inc = {q: [] for q in ANCHORS["q_codes"]}
    for cid in REG:
        for q in CUNITS[cid].get("can_route_to_q") or []:
            if q in q_inc:
                q_inc[q].append(cid)
    exer = {q for q, cs in q_inc.items() if any(CUNITS[c].get("kind") == "route" for c in cs)}
    static = {q for q, cs in q_inc.items() if cs and q not in exer}
    unreach = {q for q, cs in q_inc.items() if not cs}
    pure = 0
    scope_q, scope_t = {}, {}
    for x in STRANDS:
        lc = (x["c_sequence"] or [None])[-1]
        if lc not in ROUTE_C:
            continue
        crq = CUNITS[lc].get("can_route_to_q") or []
        q, term = x.get("q_code"), x.get("terminal")
        if q and q in crq:
            pure += 1
        elif q:
            scope_q[(lc, q)] = scope_q.get((lc, q), 0) + 1
        elif term and term != "QUARANTINE":
            scope_t[(lc, term)] = scope_t.get((lc, term), 0) + 1
    cond = 0
    for cid in REG:
        seen = set()
        for q in CUNITS[cid].get("can_route_to_q") or []:
            if q not in seen:
                seen.add(q)
                cond += 1
        frt = (CUNITS[cid].get("verify_visualization") or {}).get("fail_route_to")
        if frt and frt in ANCHORS["q_codes"] and frt not in seen:
            cond += 1
    term_edges = term_strands = declared_unex = 0
    for cid in REG:
        if CUNITS[cid].get("kind") != "route":
            continue
        for t in sorted(set(_PC_LITERAL.findall(CUNITS[cid].get("postcondition_predicate") or ""))
                        & set(PROC_FAIL_TERMINALS)):
            n = scope_t.get((cid, t), 0)
            if n > 0:
                term_edges += 1
                term_strands += n
            else:
                declared_unex += 1
    return {"pure_realized_strands": pure, "conditional_edges": cond, "terminal_edges": term_edges,
            "terminal_strands": term_strands, "terminal_declared_unexercised": declared_unex,
            "scope_out_edges": len(scope_q), "scope_out_strands": sum(scope_q.values()),
            "c_nodes": len(REG), "q_exercised": sorted(exer), "q_static": sorted(static),
            "q_unreached": sorted(unreach)}


def stats_drift():
    """재계산 ↔ decision_tree.json stats 불일치 (키, computed, stored) list (빈 list = bit-exact)."""
    c, s = recompute_tree_stats(), TREE["stats"]
    drift = [(k, c[k], s[k]) for k in
             ("pure_realized_strands", "conditional_edges", "terminal_edges",
              "terminal_strands", "scope_out_edges", "scope_out_strands", "c_nodes") if c[k] != s[k]]
    if c["terminal_declared_unexercised"] != len(s["terminal_declared_unexercised"]):
        drift.append(("terminal_declared_unexercised", c["terminal_declared_unexercised"],
                      len(s["terminal_declared_unexercised"])))
    qp = s["q_partition"]
    for sk, ck in (("exercised", "q_exercised"), ("static_no_strand", "q_static"), ("unreached", "q_unreached")):
        if c[ck] != qp[sk]:
            drift.append(("q_partition." + sk, c[ck], qp[sk]))
    return drift


def bundle_candidate_partition():
    """(P9-16, surface b/GAP-39) measurement doc §5 probe 재현 →
    (전체 후보, 완전배선 정규화-transform run, 미배선 정규화 포함 후보). 다발 압축은 57-wired tree 대상."""
    from collections import Counter
    thresh = (len(STRANDS) + 9) // 10               # ceil(b/10) = 500
    cnt = Counter()
    for s in STRANDS:
        seq, seen = s["c_sequence"], set()
        for i in range(len(seq)):
            for j in range(i + 3, len(seq) + 1):    # 길이 ≥ 3 contiguous
                seen.add(tuple(seq[i:j]))
        for sub in seen:
            cnt[sub] += 1
    cand = [k for k, v in cnt.items() if v >= thresh]

    def norm(c):
        return CUNITS.get(c, {}).get("layer_pair") == "L-4->L-5"

    def norm_transform(c):  # commutative normalization transform = 압축 대상(Lock 5/D-S2)
        return norm(c) and CUNITS.get(c, {}).get("kind") == "transform"

    wired_runs = [k for k in cand if all(c in REG for c in k) and all(norm_transform(c) for c in k)]
    unwired_norm_cand = [k for k in cand if any((c not in REG) and norm(c) for c in k)]
    return cand, wired_runs, unwired_norm_cand


def closure_proof_consistency():
    """(P9-17, surface b) closure_proof.md INV 수치 ↔ live SSOT 재계산 정합 + doc 수치 명시."""
    c_all, c_used = len(CUNITS), len(STRAND_CS)
    c_dead = sorted(set(CUNITS) - STRAND_CS)
    doc_ok = ("119" in CLOSURE_PROOF and "122" in CLOSURE_PROOF
              and all(cid in CLOSURE_PROOF for cid in DOCUMENTED_CDEAD))
    return c_all, c_used, c_dead, doc_ok


def recipe_engine_coupling():
    """(P9-18, surface a) recipe_emitter.py AST import 분석 → engine/SSOT/상대 import 0 (M2 무의존).

    ★ 구조적 가드: engine 모듈을 import하지 않으면 run_strand/REGISTRY/navigate 등 어떤 engine
    함수도 호출 불가(NameError). 따라서 import 0 = 변환·트리 라우팅·strand 재도출 불가의 충분조건이다.
    (소스 substring 검사는 부적합 — docstring의 'run_strand 무호출' 같은 *주석*에 false-positive.)"""
    import ast
    mods = set()
    for node in ast.walk(ast.parse(RECIPE_SRC)):
        if isinstance(node, ast.Import):
            mods |= {a.name.split(".")[0] for a in node.names}
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:          # 상대 import(. / .. = adapter/engine 패키지 결합)
                mods.add("." * node.level + (node.module or ""))
            elif node.module:
                mods.add(node.module.split(".")[0])
    engine_modules = {"src", "orchestrator", "c_units", "decision_tree", "strands", "postcondition_checks"}
    coupling = sorted(m for m in mods if m.startswith(".") or m in engine_modules)
    return sorted(mods), coupling


def recipe_purity():
    """(P9-19, surface a) emit_recipe: structure 무변이 + raw conc 미누출 + 모든 status='described, not executed'."""
    import copy
    from src.adapter.recipe_emitter import emit_recipe

    class _F:
        def __init__(self, feature):
            self.feature = feature

    structure = {
        "path": "/tmp/p9_synthetic.xlsx", "sheet_names": ["2. Result"],
        "per_sheet": {"2. Result": {
            "n_rows": 4, "n_cols": 2, "shape_class": "qa-contaminated",
            "sample": [["Sample", "Conc"], ["Standard sample", "0"],
                       ["Subject-1", "5.2345671"], ["Subject-2", "6.7890123"]]}},
    }
    findings = [_F("intra-sheet-qa-block")]
    before = copy.deepcopy(structure)
    rec = emit_recipe(structure, findings)
    mutated = structure != before
    blob = json.dumps(rec, ensure_ascii=False, default=str)
    leaked = [v for v in ("5.2345671", "6.7890123") if v in blob]   # raw conc 수치 누출 검사
    statuses = [rec["status"]] + [w["status"] for w in rec["work_units"]]
    return mutated, leaked, statuses


def negative_guard_probes():
    """(P9-20, surface a+e) 1st+2nd 불변식이 vacuous하지 않음 — 깨진 입력에 guard 발화(실데이터 무변경, 복사본만)."""
    import copy
    sc = copy.deepcopy(STRANDS[:3])
    sc[0]["c_sequence"] = list(sc[0]["c_sequence"]) + ["c9999_FAKE"]
    inj = {c for s in sc for c in s["c_sequence"]}
    fake_caught = "c9999_FAKE" in (inj - set(CUNITS))                       # bad-strand-ref guard
    sample = next(((cid, q) for cid in sorted(REG)
                   for q in (CUNITS[cid].get("can_route_to_q") or [])), None)
    edge_caught = sample is not None and sample in CONDSET and sample not in (CONDSET - {sample})  # missing-edge guard
    rc = next(iter(sorted(ROUTE_C)))
    crq = set(CUNITS[rc].get("can_route_to_q") or [])
    bad_q = next((q for q in sorted(QSET) if q not in crq), None)
    synth = {"c_sequence": [rc], "q_code": bad_q, "terminal": "QUARANTINE"}
    scopeout_caught = (synth["c_sequence"][-1] in ROUTE_C                   # scope-out classifier
                       and synth["q_code"] is not None and synth["q_code"] not in crq)
    return fake_caught, edge_caught, scopeout_caught


# ───────────────────────────────── pytest 단언 ─────────────────────────────────

def test_p9_1_no_dangling_detection():
    """P9-1 D-S1: transform 전부 requires_detection_by 보유 + dangling 0."""
    null_tf, dangling = dangling_detection()
    assert null_tf == [], f"transform without detection: {null_tf}"
    assert dangling == [], f"dangling requires_detection_by: {dangling}"


def test_p9_2_ds4_wired_no_missing_edge():
    """P9-2 D-S4(wired): 배선 c.can_route_to_q → conditional edge 누락 0."""
    assert missing_ds4() == [], f"missing conditional edges: {missing_ds4()}"


def test_p9_3_no_isolated_exercised_q():
    """P9-3: exercised Q(13) 전부 incoming conditional edge ≥1."""
    assert isolated_exercised_q() == [], f"isolated exercised Q: {isolated_exercised_q()}"


def test_p9_4_recover_targets_exist():
    """P9-4 SSOT: 모든 q.recover_to_c_id 가 c_units 에 존재."""
    assert bad_recover() == [], f"dangling recover_to_c_id: {bad_recover()}"


def test_p9_5_strand_refs_valid():
    """P9-5 SSOT: strand c_seq·q_code 전부 존재 + QUARANTINE⟺q_code coupling."""
    bad_c, bad_q, coupling = bad_strand_refs()
    assert bad_c == [], f"strand references unknown c: {bad_c}"
    assert bad_q == [], f"strand references unknown q: {bad_q}"
    assert coupling == 0, f"terminal/q_code coupling violations: {coupling}"


def test_p9_6_vocab_anchor_subset():
    """P9-6 G1: can_route_to_q ⊆ q_codes ⊆ anchors.q_codes (hallucination 차단)."""
    not_in_qset, qset_not_anchor = vocab_anchor_violations()
    assert not_in_qset == [], f"can_route_to_q not in q_codes: {not_in_qset}"
    assert qset_not_anchor == [], f"q_codes not in anchors: {qset_not_anchor}"


def test_p9_7_scope_out_zero():
    """P9-7: scope_out 0 (GAP-28 Decision C RESOLVE)."""
    edges, stat_edges, stat_strands = scope_out_state()
    assert edges == [], f"deferred.scope_out_edges not empty: {edges}"
    assert stat_edges == 0 and stat_strands == 0, (stat_edges, stat_strands)


def test_p9_8_unreached_q_documented_and_unwired():
    """P9-8: unreached Q(4) 전부 deferred 문서화 + 배선 router 0 + conditional target 부재.
    → 고립이 아니라 '미배선 source의 정직한 경계'(D-S4 위반 아님)."""
    for row in unreached_audit():
        assert row["documented"], f"{row['q']} not documented in deferred.unreached_q"
        assert row["wired_routers"] == [], f"{row['q']} has wired router(s): {row['wired_routers']}"
        assert not row["in_cond_targets"], f"{row['q']} unexpectedly has conditional incoming"


def test_p9_9_anchors_at_root_not_spec():
    """P9-9: anchors.json 은 repo ROOT 에 존재(코드가 거기서 로드), spec/ 엔 없음.
    → 'MISSING'이 아니라 CLAUDE.md 레이아웃 경로 drift(기존 GAP-23 OPEN)의 현실 고정."""
    root_exists, spec_exists = anchors_location()
    assert root_exists, "anchors.json must exist at PROJECT_ROOT"
    assert not spec_exists, "spec/anchors.json absence is the GAP-23 path-drift reality"


def test_p9_10_banner_numbers_build_time_verifiable():
    """P9-10 렌더 정직성: index.html DT_BANNER == 독립 재계산(strands.json+decision_tree.json).
    배너 수치는 하드코딩이 아니라 spec 파생(검증가능)."""
    computed, embedded = banner_recompute()
    assert embedded is not None, "DT_BANNER not found in index.html"
    assert computed == embedded, f"banner drift:\n  computed={computed}\n  embedded={embedded}"


def test_p9_11_c1_dead_c_matches_documented():
    """P9-11 DoD#3 C1: strand 미등장 dead c == 문서화된 C_dead {c0042,c0043,c0333}(UNDOCUMENTED dead 0).
    셋 다 미배선 fail-branch ROUTE c. closure_proof.md INV-3·strands_stats.md §6 기록.
    ★ closure_proof Option C는 "배선 시 tree-live" forward-looking(2026-06-03 시제 정정·GAP-36 RESOLVED);
    현 57-wired scope에선 미배선 → tree 부재(C1 OR절 미충족, ②latent). 본 test는 '미기록 dead c가 새로 생기지 않음'을 회귀방지(정직한 경계 고정)."""
    assert c1_dead_c() == DOCUMENTED_CDEAD, f"dead c set drifted from documented C_dead: {c1_dead_c()}"


def test_p9_12_recover_unwired_targets_known():
    """P9-12 렌더 정직성: 미배선 recover 타깃은 알려진 omit 집합(잘못된 라우팅 주장 0).
    렌더는 wired+reachable recover edge만 그린다(test_render.py 교차)."""
    assert recover_omitted_targets() == ["c0330", "c0368", "c0499"], recover_omitted_targets()


# ═══════════════════ 2nd cycle 단언 (P9-13,16..20; 기존 12 불변) ═══════════════════

def test_p9_13_stats_reproduce_from_ssot():
    """P9-13(d): decision_tree.json stats 전부 raw SSOT 1차원리 재계산과 bit-exact.
    P9-10 심화 — stored realized_pure/static_q 신뢰 제거하고 strands+c_units+REGISTRY에서 독립 재계산."""
    assert stats_drift() == [], f"stats drift from SSOT recompute: {stats_drift()}"


def test_p9_16_bundles_empty_justified_gap39():
    """P9-16(b/GAP-39): bundles=[]는 '완전배선 commutative-normalization-transform run 0'으로 정당화.
    measurement doc §0/§1 'transform 후보 전부 c0200–c0213·정규화층 0' prose는 5000-oracle 측정이라 부정확 —
    미배선 정규화 후보(예: c0320–c0323 freq 531)는 존재하나 57-wired tree에 부재(GAP-39 정확화)."""
    cand, wired_runs, unwired_norm_cand = bundle_candidate_partition()
    assert TREE["bundles"] == [], f"bundles not empty: {TREE['bundles']}"
    assert wired_runs == [], f"wired commutative-normalization-transform runs exist: {wired_runs}"
    assert len(unwired_norm_cand) >= 1, (
        "GAP-39: 미배선 정규화 후보 0이면 doc의 '정규화층 0'이 옳다는 뜻 — 본 cycle 발견과 모순")


def test_p9_17_closure_proof_matches_live():
    """P9-17(b): closure_proof INV(C_used 119/C_all 122/C_dead {c0042,c0043,c0333}) ↔ live SSOT 정합.
    Direction C 시제정정(prose만 변경)이 INV 수치를 흔들지 않았음을 회귀방지."""
    c_all, c_used, c_dead, doc_ok = closure_proof_consistency()
    assert c_all == 122 and c_used == 119, (c_all, c_used)
    assert c_dead == DOCUMENTED_CDEAD, c_dead
    assert doc_ok, "closure_proof.md must state 119/122 + C_dead {c0042,c0043,c0333}"


def test_p9_18_recipe_emitter_no_engine_coupling():
    """P9-18(a): recipe_emitter.py 가 engine/SSOT 모듈도 상대 패키지도 import하지 않음(stdlib만).
    M2 무의존(변환·트리 라우팅·strand 재도출 무)의 구조적 회귀가드 — import 0 = engine 호출 불가."""
    mods, coupling = recipe_engine_coupling()
    assert coupling == [], f"recipe_emitter couples to engine/SSOT/relative module: {coupling} (mods={mods})"


def test_p9_19_emit_recipe_pure_no_conc_leak():
    """P9-19(a): emit_recipe는 (i) 입력 structure 무변이 (ii) raw conc 수치 미누출
    (iii) 모든 work_unit status='described, not executed'. 변환 0(기술·안내만)의 falsifiable 고정."""
    mutated, leaked, statuses = recipe_purity()
    assert not mutated, "emit_recipe mutated input structure"
    assert leaked == [], f"raw conc values leaked into recipe output: {leaked}"
    assert all(s == "described, not executed" for s in statuses), statuses


def test_p9_20_guards_are_non_vacuous():
    """P9-20(a+e): 깨진 입력에 guard 발화(non-vacuous) — fake c_id·제거된 conditional edge·합성 scope-out
    전부 적발. 1st+2nd 불변식이 vacuous-pass가 아님을 적대적으로 입증(실데이터 무변경, 복사본만)."""
    fake_caught, edge_caught, scopeout_caught = negative_guard_probes()
    assert fake_caught, "bad-strand-ref guard vacuous (fake c_id not caught)"
    assert edge_caught, "missing-conditional-edge guard vacuous"
    assert scopeout_caught, "scope-out classifier vacuous"


# ─────────────────────────── 직접 실행: 수치 매트릭스 출력 ───────────────────────────

def _matrix():
    def line(tag, ok, detail):
        print(f"  [{'PASS' if ok else 'FAIL'}] {tag:7} {detail}")

    print("=" * 78)
    print("PHASE 9 — 적대적 교차-SSOT 검증 매트릭스 (read-only, falsifiable)")
    print("=" * 78)
    print(f"  로드: c_units {len(CUNITS)} · q_codes {len(QSET)} · wired REGISTRY {len(REG)} · "
          f"strands {len(STRANDS)} · tree nodes {len(TREE['nodes'])} · cond {len(COND)}")
    print("-" * 78)

    null_tf, dangling = dangling_detection()
    line("P9-1", not null_tf and not dangling,
         f"D-S1 dangling detection: null_tf={len(null_tf)} dangling={len(dangling)}")
    line("P9-2", not missing_ds4(), f"D-S4 wired 누락 edge: {len(missing_ds4())}")
    line("P9-3", not isolated_exercised_q(), f"exercised Q 고립: {len(isolated_exercised_q())}")
    line("P9-4", not bad_recover(), f"dangling recover_to_c_id: {len(bad_recover())}")
    bad_c, bad_q, coupling = bad_strand_refs()
    line("P9-5", not bad_c and not bad_q and coupling == 0,
         f"strand bad_c={len(bad_c)} bad_q={len(bad_q)} coupling_viol={coupling}")
    niq, qna = vocab_anchor_violations()
    line("P9-6", not niq and not qna, f"can_route∉q_codes={len(niq)} q_codes∉anchors={len(qna)}")
    e, se, ss = scope_out_state()
    line("P9-7", not e and se == 0 and ss == 0, f"scope_out edges={len(e)} stat_edges={se} stat_strands={ss}")
    ua = unreached_audit()
    ok8 = all(r["documented"] and not r["wired_routers"] and not r["in_cond_targets"] for r in ua)
    line("P9-8", ok8, "unreached Q=" + ",".join(
        f"{r['q']}(doc={r['documented']},wired_router={len(r['wired_routers'])})" for r in ua))
    re_, se_ = anchors_location()
    line("P9-9", re_ and not se_, f"anchors root={re_} spec/anchors={se_} (GAP-23 drift)")
    computed, embedded = banner_recompute()
    line("P9-10", computed == embedded, f"banner build-time 재계산 == 임베디드: {computed == embedded}")
    line("P9-11", c1_dead_c() == DOCUMENTED_CDEAD,
         f"C1 dead c == 문서화 C_dead {DOCUMENTED_CDEAD}: 실측 {c1_dead_c()} (미기록 dead 0)")
    line("P9-12", recover_omitted_targets() == ["c0330", "c0368", "c0499"],
         f"미배선 recover omit 집합: {recover_omitted_targets()}")
    # ── 2nd cycle (P9-13,16..20) ──
    line("P9-13", stats_drift() == [], f"decision_tree stats 1차원리 재계산 drift={len(stats_drift())} (bit-exact=0)")
    _cand, _wr, _uc = bundle_candidate_partition()
    line("P9-16", TREE["bundles"] == [] and _wr == [] and len(_uc) >= 1,
         f"bundles={TREE['bundles']} 완전배선-norm-transform-run={len(_wr)} 미배선-norm-후보={len(_uc)} (GAP-39)")
    _ca, _cu, _cd, _dok = closure_proof_consistency()
    line("P9-17", _ca == 122 and _cu == 119 and _cd == DOCUMENTED_CDEAD and _dok,
         f"closure_proof C_used {_cu}/C_all {_ca} C_dead {_cd} doc_ok={_dok}")
    _mods, _coup = recipe_engine_coupling()
    line("P9-18", _coup == [], f"recipe_emitter imports={_mods} engine/relative coupling={_coup} (M2 무의존)")
    _mut, _lk, _st = recipe_purity()
    line("P9-19", (not _mut) and _lk == [] and all(s == "described, not executed" for s in _st),
         f"emit_recipe mutated={_mut} conc_leak={_lk} status_set={set(_st)}")
    _f, _e, _s = negative_guard_probes()
    line("P9-20", _f and _e and _s, f"non-vacuous: fake_c={_f} edge_removal={_e} scope_out={_s}")
    # ── P9-14/P9-15: 거장 결정으로 durable test 아님(review doc 표); 증거 appendix용 [doc] 정보 행 ──
    _band = sorted(QPART["exercised"] + QPART["static_no_strand"])
    _rec_drawn = sum(1 for q in _band if QCODES.get(q, {}).get("recover_to_c_id") in REG)
    print(f"  [doc ] P9-15   recover edge drawn={_rec_drawn} (=14; Q10→c0330 omit) — brittle(미래 Q10 배선)→review doc 표")
    _tr_ok = all(e["strand_count"] == sum(1 for x in STRANDS
                 if (x["c_sequence"] or [None])[-1] == e["from"] and x["terminal"] == e["to"]
                 and not x.get("q_code")) for e in TREE["terminal_routing"])
    _inv_rem = {(x["c_sequence"] or [None])[-1] for x in STRANDS
                if x["terminal"] in PROC_FAIL_TERMINALS and not x.get("q_code")
                and ((x["c_sequence"] or [None])[-1], x["terminal"])
                not in {(e["from"], e["to"]) for e in TREE["terminal_routing"]}}
    print(f"  [doc ] P9-14   terminal_routing reconcile vs strands={_tr_ok}; process-fail remainder last-c={_inv_rem or '∅'}"
          f"(GAP-13) — P9-13(315)에 포섭")
    print("-" * 78)

    # 2축 보조 통계(은폐 0 입증용 — review doc §E)
    from collections import Counter
    term = Counter(s["terminal"] for s in STRANDS)
    qcnt = Counter(s["q_code"] for s in STRANDS if s.get("q_code"))
    unreal6 = sum(qcnt[q] for q in (QPART["static_no_strand"] + QPART["unreached"]))
    print("  [축1 oracle] terminal:", dict(term), "| complete(AUTO+REPAIR)=",
          term["AUTO"] + term["REPAIR"])
    print(f"  [축2 wired ] banner.realized_pure={embedded['realized_pure']} · "
          f"unwired_c={embedded['unwired_c']} · static_q={embedded['static_q']} · "
          f"deferred={embedded['deferred_total']}")
    print(f"  [경계 정직] oracle이 미실현/미도달 Q(Q05/Q10/Q15A/B/C/X)로 보낸 strand={unreal6} "
          f"→ QUARANTINE(사람개입)으로 정직 집계, 그 Q-terminal은 wired 미실현 표시(은폐 0)")
    print("=" * 78)


if __name__ == "__main__":
    _matrix()
