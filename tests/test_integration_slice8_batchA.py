"""Phase 5 · slice 8 — Batch A (L-3->L-4 axis-fail ROUTE c) 통합 검증 + 프런티어 갱신.

slice 7a/7b는 backbone 46c를 배선해 완주 173을 만들고, column-path 완주는 '배선'이 아니라 '신규 구현'
과제임을 falsifiable하게 고정했다(GAP-30). slice 8은 column_path_implementation_backlog.md의 Batch A
= L-3->L-4 axis-fail ROUTE c 6개(c0250/c0252/c0254/c0255/c0256/c0257)를 신규 구현+배선해 완주
173 → 312(A1) → 353(A2)로 올린 첫 column-path 슬라이스다. 본 모듈은 신규 완주 180 strand에 Phase 5
cross-cutting 불변식(actual==best · skeleton D-S3 · D-S1 · C1/C3/C5)을 규모 검증하고, ①/②를 재측정한다.

★ 발견(cite-verify, GAP-30 영향 노트 갱신 근거): empty meta에서도 c0200→AIC-MISSING·c0204→
  MISSING-NO-POLICY(df-default가 fail-state)라 c0250(74×Q11)·c0252(14×Q08)가 외부 meta 없이 실현한다
  (realized 88/353). '① realization=0'은 c0251/c0253(df-default=pass)의 backbone-only 특성이었고 A0/A4
  ROUTE 배선으로 부분 falsify된다. ① 자체 미해소: 64 mis-realize(meta 부재로 잘못된 q) + 28 INVALID-starve
  = ① 결손 규모(measure-not-fix). 올바른 descriptor 주입 시 정상 실현(test_route_realizes_expected_q_with_meta).
★ GAP-31: c0252 INFUSION-STOP-RESTART는 strands SSOT상 Q04이나 Q04∉postcond → postcond-faithful INVALID
  (SSOT↔postcond divergence는 Phase 7 D-S4 이월; GAP-28 동형).

신규 코드: 본 하네스 + 6 ROUTE c-unit(test/fixture/impl/adversarial) + orchestrator 6 REGISTRY 배선.
dispatch/run_strand 로직 무변경.
"""

import json
from collections import Counter
from pathlib import Path

import pandas as pd

from src.orchestrator import REGISTRY, REQUIRES_DETECTION, run_strand

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STRANDS = json.loads((PROJECT_ROOT / "spec" / "strands.json").read_text(encoding="utf-8"))
CUNITS = {c["c_id"]: c for c in
          json.loads((PROJECT_ROOT / "spec" / "c_units.json").read_text(encoding="utf-8"))}

BATCH_A = {"c0250", "c0252", "c0254", "c0255", "c0256", "c0257"}
A1 = {"c0250", "c0252"}
AXIS = [f"c02{n:02d}" for n in range(0, 11)]      # A0–A10 평가자 c0200..c0210
ROUTE_C = {"c0251", "c0253"} | BATCH_A             # terminal 키를 반환하는 ROUTE c 전체

# ★ slice 8 = Batch A milestone 기록. 이후 slice 9(Batch B) 등이 REGISTRY를 확장해도 본 milestone
#   수치(완주 353 · NEW_BATCH_A 180 · ① 88/64/28)는 고정이어야 하므로, 의도적으로 Batch B 이후 c를
#   제외한 'slice 8 시점 REGISTRY 스냅샷'에서 완주를 유도한다(왜 REGISTRY 전체를 안 쓰는가 = milestone freeze).
#   살아있는 프런티어 추적은 slice 7a/7b(bump)·slice 9(live)가 담당. (tracker=bump, milestone=freeze 구분.)
_LATER_SLICES = {"c0211", "c0212", "c0214", "c0215", "c0216"}  # slice 9 Batch B — milestone 보존 위해 제외
REG = set(REGISTRY.keys()) - _LATER_SLICES
COMPLETING = [s for s in STRANDS if all(c in REG for c in s["c_sequence"])]
# 신규 완주 = Batch A ROUTE c로 종착(6 c는 slice 8에서 처음 배선됨 → 이전엔 SliceBoundary로 미완주).
NEW_BATCH_A = [s for s in COMPLETING if s["c_sequence"][-1] in BATCH_A]


def _complete_with(wired):
    """임의 배선 집합 wired에서 완주 strand 수."""
    return sum(1 for s in STRANDS if all(c in wired for c in s["c_sequence"]))


def _neutral_df():
    """7a/7b와 동일한 고정 neutral 입력(축-state 미주입)."""
    return pd.DataFrame({
        "ID": [1, 1, 2], "TIME": [0, 1, 0], "DV": [0.0, 1.0, 2.0],
        "time_value": [0, 1, 0], "dv_value": [0.1, 0.2, 0.3], "dose": [100.0, None, 200.0],
    })


_RUNS = None


def _run_all():
    """완주 strand 전체를 neutral df로 1회 실행하고 (strand, record) 캐시."""
    global _RUNS
    if _RUNS is None:
        _RUNS = [(s, run_strand(s["c_sequence"], _neutral_df(), {})) for s in COMPLETING]
    return _RUNS


# ===== 완주 규모 (백로그 누적곡선) =====

def test_batch_a_completing_353():
    """★ falsifiable: Batch A 6 ROUTE 구현+배선 후 완주 = 353, 신규 = 180 (백로그 예측 일치)."""
    assert len(COMPLETING) == 353
    assert len(NEW_BATCH_A) == 180


def test_a1_a2_cumulative_curve():
    """★ 백로그 §2 누적곡선 falsifiable 재현: base 173 → A1(+c0250,c0252)=312(+139) → A2(+4)=353(+41).
    base = 현 REGISTRY − Batch A 6 = slice 7a/7b 배선 46."""
    base = REG - BATCH_A
    assert len(base) == 46
    assert _complete_with(base) == 173
    assert _complete_with(base | A1) == 312
    assert _complete_with(base | BATCH_A) == 353


# ===== actual == best (구조적), 예외 0 =====

def test_actual_equals_best_new_180():
    """★ Phase 5 핵심: 신규 완주 180 전부 best c_sequence를 SliceBoundary 없이 완주(ROUTE c가 last-c라
    실현 prefix == best). cost = Σc.cost 동치(C5)."""
    for s in NEW_BATCH_A:
        rec = run_strand(s["c_sequence"], _neutral_df(), {})
        assert rec["boundary_at"] is None, s["sc_id"]
        assert rec["actual_c_sequence"] == s["c_sequence"], s["sc_id"]
        assert rec["total_cost"] == s["total_cost"], s["sc_id"]


def test_new_strands_end_in_batch_a_route_c():
    """신규 완주 180은 전부 Batch A ROUTE c로 종착(173 base와 분리)."""
    assert len(NEW_BATCH_A) == 180
    assert all(s["c_sequence"][-1] in BATCH_A for s in NEW_BATCH_A)


def test_no_runtime_exceptions():
    """axis verify/detect + ROUTE c가 neutral df에 robust(예외 0) — _run_all이 catch 없이 완주."""
    assert len(_run_all()) == 353


# ===== skeleton D-S3 / axis N0-N7 / D-S1 (신규 180) =====

def test_skeleton_axis_n0_n7_ascending_new():
    """D-S3 골격: 신규 strand의 axis(c0200..c0210) subseq는 c_id 오름차순(N0–N7 무모순)."""
    for s in NEW_BATCH_A:
        sub = [c for c in s["c_sequence"] if c in AXIS]
        assert sub == sorted(sub), s["sc_id"]


def test_skeleton_mess_precedes_backbone_new():
    """D-S3: 신규 strand에서 mess(L-4->L-5) c는 backbone(비 L-4->L-5)보다 앞에 온다(있을 때)."""
    for s in NEW_BATCH_A:
        seq = s["c_sequence"]
        mess_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] == "L-4->L-5"]
        bb_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] != "L-4->L-5"]
        if mess_idx and bb_idx:
            assert max(mess_idx) < min(bb_idx), s["sc_id"]


def test_d_s1_detection_precedes_route_new():
    """D-S1: 신규 strand에서 ROUTE c의 requires_detection_by(axis)가 strand에 있으면 항상 앞에 온다."""
    for s in NEW_BATCH_A:
        seq = s["c_sequence"]
        for i, c in enumerate(seq):
            rd = REQUIRES_DETECTION.get(c)
            if rd is not None and rd in seq:
                assert seq.index(rd) < i, (s["sc_id"], c, rd)


def test_d_s1_route_runtime_gate_holds():
    """D-S1 런타임: ROUTE c는 대응 axis detect가 meta['{req}_ran']을 남긴 뒤에만 dispatch된다.
    _run_all이 RuntimeError(D-S1 위반) 없이 353 완주함으로 cut-vertex 게이트 통과를 증명."""
    runs = _run_all()
    assert len(runs) == 353
    assert all(rec["boundary_at"] is None for _, rec in runs)


# ===== C1 / C3 / C5 =====

def test_c1_batch_a_each_in_completing():
    """C1(DoD): Batch A 6c 각각이 ≥1 완주 strand의 last-c로 등장(dead c 0)."""
    last_cs = Counter(s["c_sequence"][-1] for s in COMPLETING)
    for c in sorted(BATCH_A):
        assert last_cs[c] >= 1, c
    # 종착 분해(falsifiable 고정)
    assert {c: last_cs[c] for c in sorted(BATCH_A)} == {
        "c0250": 74, "c0252": 65, "c0254": 11, "c0255": 15, "c0256": 2, "c0257": 13}


def test_c3_new_q_codes_triggered():
    """C3(DoD): Batch A ROUTE c가 신규 발화시키는 Q-code = {Q04,Q07,Q08,Q09,Q11,Q13,Q14,Q15D}(8종).
    strands.json 기준 신규 완주 strand의 기대 q(Q03은 본 Batch에서 미완주 — 백로그 후속)."""
    new_q = {s["q_code"] for s in NEW_BATCH_A if s["q_code"]}
    assert new_q == {"Q04", "Q07", "Q08", "Q09", "Q11", "Q13", "Q14", "Q15D"}, sorted(new_q)


def test_c5_route_cost_zero():
    """C5: ROUTE c는 cost=0(c_units.json) → strand total_cost = Σ(non-route c cost). 6c 전부 cost 0."""
    for c in sorted(BATCH_A):
        assert CUNITS[c]["cost"] == 0, c


def test_no_isolated_q_terminal_among_new():
    """D-S4 부분 통과: 신규 완주 q-strand는 전부 ROUTE c(c025X)로 종착 = 고립 Q-terminal 0(실현 가능)."""
    new_q = [s for s in NEW_BATCH_A if s["q_code"]]
    assert new_q
    assert all(s["c_sequence"][-1] in BATCH_A for s in new_q)


# ===== ① realization 규모 (measure-not-fix; GAP-30 영향 노트) =====

def test_realization_88_correct_without_meta():
    """★ ①(발견/GAP-30): empty meta로 완주 353 중 88이 기대-q 실현(c0250 74×Q11 + c0252 14×Q08).
    c0200/c0204의 df-default가 fail-state라 A0/A4 ROUTE가 meta 없이 실현 — realization=0은 backbone-only
    (c0251/c0253) 특성이었음(slice 7a/7b는 0)."""
    runs = _run_all()
    realized = [s for s, rec in runs if s["q_code"] and rec["q_code"] == s["q_code"]]
    assert len(realized) == 88
    assert dict(Counter(s["c_sequence"][-1] for s in realized)) == {"c0250": 74, "c0252": 14}


def test_runtime_terminal_table_empty_meta():
    """★ ① 결손 규모(measure-not-fix): empty meta에서 신규 ROUTE c별 런타임 (terminal,q) 분포를 고정.
    c0250→Q11×74(전부 실현) / c0252→Q08×65(14 실현 + 51 mis-realize: a4 단일 default MISSING-NO-POLICY) /
    c0254·c0255·c0256→INVALID(a7/a8/a9 default=pass → 28 starve) / c0257→Q03×13(a6 default=SEPARABLE→Q03,
    기대 Q04와 불일치 mis-realize). 합 mis 64 + starve 28 + ok 88 = 180. 외부 meta 주입은 ① 소관."""
    runs = {s["sc_id"]: rec for s, rec in _run_all()}
    dist = Counter((s["c_sequence"][-1], runs[s["sc_id"]]["terminal"], runs[s["sc_id"]]["q_code"])
                   for s in NEW_BATCH_A)
    assert dict(dist) == {
        ("c0250", "QUARANTINE", "Q11"): 74,
        ("c0252", "QUARANTINE", "Q08"): 65,
        ("c0254", "INVALID", None): 11,
        ("c0255", "INVALID", None): 15,
        ("c0256", "INVALID", None): 2,
        ("c0257", "QUARANTINE", "Q03"): 13,
    }, dict(dist)


def test_realization_deficit_scale():
    """★ ① 결손 규모: 신규 180 = ok 88 + mis-realize 64(QUARANTINE이나 q 불일치) + INVALID-starve 28.
    이 64+28이 외부 meta 주입(① GAP-4/6/7/9/10/11/12/14)으로 닫히는 결손의 규모."""
    runs = {s["sc_id"]: rec for s, rec in _run_all()}
    ok = mis = starve = 0
    for s in NEW_BATCH_A:
        rec = runs[s["sc_id"]]
        if s["q_code"] and rec["q_code"] == s["q_code"]:
            ok += 1
        elif rec["terminal"] == "INVALID":
            starve += 1
        else:
            mis += 1
    assert (ok, mis, starve) == (88, 64, 28), (ok, mis, starve)


def test_route_realizes_expected_q_with_meta():
    """★ ① 대조군(measure-not-fix 증명): 올바른 축-state descriptor 주입 시 starve/mis-realize였던 신규
    ROUTE strand가 기대 Q를 실현한다 — 결손은 외부 meta 주입뿐임을 falsifiable 분리(7a 동형)."""
    def first(lastc, q):
        return next(s for s in NEW_BATCH_A if s["c_sequence"][-1] == lastc and s["q_code"] == q)
    # c0252: meta 없이는 Q08 mis-realize(기대 Q14) → has_addl_actual_conflict 주입 시 Q14 실현
    q14 = first("c0252", "Q14")
    rec = run_strand(q14["c_sequence"], _neutral_df(), {"has_addl_actual_conflict": True})
    assert rec["terminal"] == "QUARANTINE" and rec["q_code"] == "Q14", q14["sc_id"]
    # c0254: meta 없이는 INVALID starve → covariate_state 주입 시 Q07/Q13 실현
    q07 = first("c0254", "Q07")
    rec = run_strand(q07["c_sequence"], _neutral_df(), {"covariate_state": "policy-missing"})
    assert rec["terminal"] == "QUARANTINE" and rec["q_code"] == "Q07", q07["sc_id"]
    q13 = first("c0254", "Q13")
    rec = run_strand(q13["c_sequence"], _neutral_df(), {"covariate_state": "key-missing"})
    assert rec["terminal"] == "QUARANTINE" and rec["q_code"] == "Q13", q13["sc_id"]


# ===== ② D-S4 axis-terminal 불변 (Batch A는 axis 종착 strand를 안 건드림) =====

def test_d_s4_axis_terminal_unchanged():
    """★ ② 불변: axis evaluator 종착 strand(ROUTE c 아님)는 여전히 68개·terminal 미실현, 그중 Q05 via
    c0201 4개. Batch A는 ROUTE 종착 strand만 추가 → axis-only 종착 집합 불변(Phase 7 D-S4 소관)."""
    runs = _run_all()
    axis_last = [(s, rec) for s, rec in runs if s["c_sequence"][-1] not in ROUTE_C]
    assert len(axis_last) == 68
    assert all(rec["terminal"] is None for _, rec in axis_last)
    q05 = [s for s, _ in axis_last if s["q_code"]]
    assert len(q05) == 4
    assert all(s["q_code"] == "Q05" and s["c_sequence"][-1] == "c0201" for s in q05)
