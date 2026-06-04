"""Phase 5 · slice 9 — Batch B (L-3->L-4 axis DETECT/VERIFY) 통합 검증 + 프런티어 갱신.

slice 8(Batch A 6 ROUTE)이 완주 173→353을 만든 뒤, Batch B는 L-3->L-4 축 평가자 DETECT/VERIFY
5개(c0211/c0212/c0214/c0215/c0216, req_det None)를 신규 구현+배선해 완주 353→439(+86)로 올리고
L-3->L-4 층을 전부 완성한다(남은 상류 = L-2->L-3 12 + L-1->L-2 4 = Batch C/D/E).

★ 구조 차이(vs Batch A): Batch B c는 detect/verify(중간 c)라 terminal 키를 반환하지 않는다 →
  완주 path만 +86 열 뿐, 신규 완주 strand는 전부 기배선 terminal-producer(c0210 축 또는 c0253/
  c0254/c0255/c0256 ROUTE)로 종착한다(Batch B c로 종착하는 strand 0).

★ ① realization(measure-not-fix, GAP-30): empty meta로 신규 86 = ok 0 + mis 0 + starve 40
  (전부 INVALID; c0253 a5=CLEAN→INVALID, c0254/c0255/c0256 axis default=pass→INVALID) + axis-None 46
  (c0210 종착, terminal 미실현 = ② D-S4). Batch A(88 실현)와 달리 Batch B는 runtime Q 실현 0 —
  c0211/c0212 sub-detector의 has_above_uloq/has_replicates는 a5_state(c0205)에 안 먹이고, 실주체
  c0253은 a5=CLEAN→INVALID. 외부 meta 주입은 ① 소관.
★ df-default(GAP-30 axis별 누적): c0211 has_above_uloq=False·c0212 has_replicates=False·
  c0215/c0216=False(no route) / c0214 unit_declaration_complete=False→Q10(df-default=fail) 그러나
  Q10 ROUTE c 부재라 runtime 미실현(② D-S4, GAP-32: c0213 scope-out-pass와 정반대 df-default).
★ ② axis-only 종착: Batch B가 c0210 종착 strand 46을 추가 → axis-only-terminal 68→114(전부 runtime
  terminal None, Phase 7 D-S4 conditional edge 소관).

신규 코드: 본 하네스 + 5 DETECT/VERIFY c-unit(test/fixture/impl/adversarial) + orchestrator 5 REGISTRY 배선.
dispatch/run_strand 로직 무변경.
"""

import json
from collections import Counter
from pathlib import Path

import pandas as pd

from src.orchestrator import REGISTRY, REQUIRES_DETECTION, run_strand
from src.c_units.c0211_detect_above_uloq import detect_above_uloq
from src.c_units.c0212_detect_replicate_obs import detect_replicate_obs
from src.c_units.c0214_verify_unit_declaration import verify_unit_declaration
from src.c_units.c0215_detect_duplicate_row import detect_duplicate_row
from src.c_units.c0216_detect_encoding import detect_encoding

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STRANDS = json.loads((PROJECT_ROOT / "spec" / "strands.json").read_text(encoding="utf-8"))
CUNITS = {c["c_id"]: c for c in
          json.loads((PROJECT_ROOT / "spec" / "c_units.json").read_text(encoding="utf-8"))}

BATCH_B = {"c0211", "c0212", "c0214", "c0215", "c0216"}
AXIS = [f"c02{n:02d}" for n in range(0, 11)]       # A0–A10 평가자 c0200..c0210
ROUTE_C = {"c0251", "c0253", "c0250", "c0252", "c0254", "c0255", "c0256", "c0257"}

REG = set(REGISTRY.keys())
COMPLETING = [s for s in STRANDS if all(c in REG for c in s["c_sequence"])]
# 신규 완주 = Batch B 배선으로 비로소 완주(이전엔 strand 내 Batch B c에서 SliceBoundary).
_BASE_IDS = {s["sc_id"] for s in STRANDS if all(c in (REG - BATCH_B) for c in s["c_sequence"])}
NEW_BATCH_B = [s for s in COMPLETING if s["sc_id"] not in _BASE_IDS]


def _complete_with(wired):
    return sum(1 for s in STRANDS if all(c in wired for c in s["c_sequence"]))


def _neutral_df():
    """7a/7b/8과 동일한 고정 neutral 입력(축-state 미주입)."""
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

def test_batch_b_completing_439():
    """★ falsifiable: Batch B 5 DETECT/VERIFY 구현+배선 후 완주 = 439, 신규 = 86(백로그 예측 일치)."""
    assert len(COMPLETING) == 439
    assert len(NEW_BATCH_B) == 86


def test_cumulative_curve_353_to_439():
    """★ 백로그 §2 누적곡선: base(REG−B)=353 → +B=439(+86). Batch B = L-3->L-4 축 DETECT/VERIFY 5c."""
    assert len(BATCH_B) == 5
    assert _complete_with(REG - BATCH_B) == 353
    assert _complete_with(REG) == 439


def test_new_strands_end_in_prewired_terminal_producers():
    """★ Batch B c는 중간 detect/verify → 신규 완주 strand가 Batch B c로 종착하는 경우 0.
    전부 기배선 c0210(축) 또는 ROUTE c(c0253/c0254/c0255/c0256)로 종착."""
    assert all(s["c_sequence"][-1] not in BATCH_B for s in NEW_BATCH_B)
    assert dict(Counter(s["c_sequence"][-1] for s in NEW_BATCH_B)) == {
        "c0210": 46, "c0253": 29, "c0255": 6, "c0254": 4, "c0256": 1}


def test_each_batch_b_c_appears_and_sole_unlocks():
    """★ C1 규모(falsifiable 고정): 각 Batch B c의 전체 등장 strand 수 + NB 내 sole-unlock(단 1개 B c) 수.
    sole 합 74 + ≥2 B c 필요 12 = 86(conjunctive 꼬리)."""
    appears = {c: sum(1 for s in STRANDS if c in s["c_sequence"]) for c in BATCH_B}
    assert appears == {"c0211": 355, "c0212": 352, "c0214": 109, "c0215": 113, "c0216": 102}
    sole = Counter()
    for s in NEW_BATCH_B:
        bset = [c for c in s["c_sequence"] if c in BATCH_B]
        if len(bset) == 1:
            sole[bset[0]] += 1
    assert dict(sole) == {"c0211": 29, "c0212": 28, "c0214": 5, "c0215": 5, "c0216": 7}
    assert sum(sole.values()) == 74


# ===== actual == best (구조적), 예외 0 =====

def test_actual_equals_best_new_86():
    """★ Phase 5 핵심: 신규 완주 86 전부 best c_sequence를 SliceBoundary 없이 완주. cost = Σc.cost(C5)."""
    for s in NEW_BATCH_B:
        rec = run_strand(s["c_sequence"], _neutral_df(), {})
        assert rec["boundary_at"] is None, s["sc_id"]
        assert rec["actual_c_sequence"] == s["c_sequence"], s["sc_id"]
        assert rec["total_cost"] == s["total_cost"], s["sc_id"]


def test_no_runtime_exceptions():
    """완주 439가 neutral df에 robust(예외 0). ★ c0212는 subject_id 부재(neutral df) graceful → False."""
    assert len(_run_all()) == 439


# ===== C1 / C5 =====

def test_c1_each_batch_b_c_in_completing():
    """C1(DoD): Batch B 5c 각각이 ≥1 완주 strand에 등장(dead c 0; 중간 c라 last-c 아님)."""
    used = {c for s in COMPLETING for c in s["c_sequence"]}
    for c in sorted(BATCH_B):
        assert c in used, c


def test_batch_b_req_det_none():
    """req_det None cite-verify — detect/verify라 D-S1 게이트 비대상."""
    for c in sorted(BATCH_B):
        assert REQUIRES_DETECTION.get(c) is None, c


def test_c5_batch_b_cost_one():
    """C5: DETECT/VERIFY cost=1(c_units.json). 5c 전부 1."""
    for c in sorted(BATCH_B):
        assert CUNITS[c]["cost"] == 1, c


# ===== skeleton D-S3 / axis 오름차순 / D-S1 (신규 86) =====

def test_skeleton_axis_ascending_new():
    """D-S3 골격: 신규 strand의 axis(c0200..c0210) subseq는 c_id 오름차순(N0–N7 무모순)."""
    for s in NEW_BATCH_B:
        sub = [c for c in s["c_sequence"] if c in AXIS]
        assert sub == sorted(sub), s["sc_id"]


def test_skeleton_mess_precedes_backbone_new():
    """D-S3: 신규 strand에서 mess(L-4->L-5) c는 backbone(비 L-4->L-5)보다 앞에 온다(있을 때)."""
    for s in NEW_BATCH_B:
        seq = s["c_sequence"]
        mess_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] == "L-4->L-5"]
        bb_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] != "L-4->L-5"]
        if mess_idx and bb_idx:
            assert max(mess_idx) < min(bb_idx), s["sc_id"]


def test_d_s1_detection_precedes_dependent_new():
    """D-S1: 신규 strand에서 c.requires_detection_by가 strand에 있으면 항상 앞에 온다."""
    for s in NEW_BATCH_B:
        seq = s["c_sequence"]
        for i, c in enumerate(seq):
            rd = REQUIRES_DETECTION.get(c)
            if rd is not None and rd in seq:
                assert seq.index(rd) < i, (s["sc_id"], c, rd)


def test_d_s1_runtime_no_violation():
    """D-S1 런타임: _run_all이 RuntimeError(D-S1 위반)·SliceBoundary 없이 439 완주."""
    runs = _run_all()
    assert len(runs) == 439
    assert all(rec["boundary_at"] is None for _, rec in runs)


# ===== ① realization 규모 (measure-not-fix; GAP-30 영향 노트 / GAP-32) =====

def test_realization_zero_without_meta():
    """★ ①(measure-not-fix): empty meta로 신규 86 = ok 0 + mis 0 + starve 40 + axis-None 46.
    Batch A(88 실현)와 달리 Batch B는 runtime Q 실현 0 — c0211/c0212 sub-flag는 a5_state에 안 먹이고
    실주체 c0253은 a5=CLEAN→INVALID, c0254/c0255/c0256 axis default=pass→INVALID. 외부 meta 주입은 ① 소관."""
    runs = {s["sc_id"]: rec for s, rec in _run_all()}
    ok = mis = starve = nq = 0
    for s in NEW_BATCH_B:
        rec = runs[s["sc_id"]]
        if not s["q_code"]:
            nq += 1
        elif rec["q_code"] == s["q_code"]:
            ok += 1
        elif rec["terminal"] == "INVALID":
            starve += 1
        else:
            mis += 1
    assert (ok, mis, starve, nq) == (0, 0, 40, 46), (ok, mis, starve, nq)


def test_runtime_terminal_table_empty_meta():
    """★ ① 결손 분포 고정(measure-not-fix): 신규 86의 런타임 (last_c, terminal, q)."""
    runs = {s["sc_id"]: rec for s, rec in _run_all()}
    dist = Counter((s["c_sequence"][-1], runs[s["sc_id"]]["terminal"], runs[s["sc_id"]]["q_code"])
                   for s in NEW_BATCH_B)
    assert dict(dist) == {
        ("c0210", None, None): 46,
        ("c0253", "INVALID", None): 29,
        ("c0254", "INVALID", None): 4,
        ("c0255", "INVALID", None): 6,
        ("c0256", "INVALID", None): 1,
    }, dict(dist)


def test_df_default_flags_empty_meta():
    """★ df-default(GAP-30 axis별 누적): empty meta + neutral df에서 각 Batch B c의 플래그·route.
    c0211/c0212/c0215/c0216 = False·route None / c0214 unit_declaration_complete=False→Q10(df-default=fail,
    GAP-32; runtime 미실현 ②). 전부 Python bool(np.bool_ 저장 시 isinstance(.,bool)=False라 postcond 위반)."""
    cases = [
        (detect_above_uloq, "has_above_uloq", False, None),
        (detect_replicate_obs, "has_replicates", False, None),
        (verify_unit_declaration, "unit_declaration_complete", False, "Q10"),
        (detect_duplicate_row, "has_exact_duplicates", False, None),
        (detect_encoding, "has_encoding_issues", False, None),
    ]
    for fn, key, exp_flag, exp_route in cases:
        meta = {}
        r = fn(_neutral_df(), meta)
        assert r[key] is exp_flag, (fn.__name__, r[key])
        assert r["route_to_q"] == exp_route, (fn.__name__, r["route_to_q"])
        assert isinstance(meta[key], bool), fn.__name__


# ===== ② D-S4 axis-terminal: Batch B가 c0210 종착 strand 46 추가 (68→114) =====

def test_d_s4_axis_terminal_grows_to_114():
    """★ ②(Phase 7 D-S4 소관): axis-only 종착(ROUTE c 아님) = 68(Batch A 시점) + 46(Batch B c0210 종착)
    = 114, 전부 runtime terminal None(미실현). 신규 46은 전부 c0210 종착·기대 terminal UNSUPPORTED/INVALID."""
    runs = _run_all()
    axis_last = [(s, rec) for s, rec in runs if s["c_sequence"][-1] not in ROUTE_C]
    assert len(axis_last) == 114
    assert all(rec["terminal"] is None for _, rec in axis_last)
    new_axis = [s for s in NEW_BATCH_B if s["c_sequence"][-1] not in ROUTE_C]
    assert len(new_axis) == 46
    assert all(s["c_sequence"][-1] == "c0210" for s in new_axis)
    assert dict(Counter(s["terminal"] for s in new_axis)) == {"UNSUPPORTED": 26, "INVALID": 20}
