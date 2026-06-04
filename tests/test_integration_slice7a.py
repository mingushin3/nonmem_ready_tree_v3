"""Phase 5 · slice 7a — FIRST end-to-end integration harness (backbone 가동).

slice 1–6은 family-segment만 동적 실행했다(미구현 하류 c에서 SliceBoundary로 정지). slice 7a가
backbone(axis A0–A10 = c0200–c0210 + L-1→L-2 NONMEM 컬럼 c0001/c0010–c0019 + covariate
c0022/c0023/c0140/c0141)을 REGISTRY에 배선하면서, strands.json best-path **전체**가 wired-set
안에 드는 strand(=완주 strand)가 처음으로 생긴다. 본 모듈은 그 완주 strand에 대해 Phase 5
cross-cutting 불변식을 처음으로 **규모(scale)** 검증하고, meta 미주입 단계에서 깨지는 불변식을
falsifiable하게 고정(characterization)한다 — 이것이 7b 착수 전 알아야 할 핵심 정보다.

측정 기준: 고정 neutral df + meta 미주입. 라이브 측정(2026-06-01, slice 7a):
  - 완주(no SliceBoundary) strand = 173  (best-path 모든 c가 REGISTRY에 존재).
  - actual_c_sequence == best c_sequence (구조적) : 173/173. 실현 c는 항상 last-c라 prefix 동일.
  - run 예외 0. (axis verify/detect c가 최소 df에 robust.)
  - skeleton D-S3(mess L-4->L-5 ≺ backbone) : 위반 0.  axis A0–A10 오름차순(N0–N7) : 위반 0.
  - D-S1 detection ≺ fix : 위반 0.

★ 깨지는 불변식(보고용 — 신규 GAP 아님, 기존 ledger 연결):
  (1) terminal 실현 GAP(① 외부 meta 주입): meta 미주입 시 기대-QUARANTINE strand 중 기대 q를
      실현하는 것 **0개**. ROUTE c(c0251/c0253)가 축-state 부재 → default INVALID로 라우팅한다.
      → GAP-4/6/7/9/10/11/12/14(외부 meta 주입 규약, 통합 시 1회 설계). WITH-meta 대표 실행
      (test_route_realizes_expected_q_with_meta)은 동일 strand가 정상 Q를 실현함을 증명.
  (2) D-S4 runtime-isolated Q-terminal(② Phase 7 D-S4): 완주 q-strand 중 **4개(Q05)**가 ROUTE c가
      아니라 axis detect c0201(route_to_q=Q05, terminal 키 미반환)로 종착 → orchestrator가 실현 못 함.
      INVALID/UNSUPPORTED(axis-only 68 strand, terminal=None)와 동일 class.
      → GAP-5/8/12/13(conditional-edge 재구성). 경험적으로 규모 확인.

신규 코드는 본 테스트 하네스뿐이며 c-unit·dispatch 로직은 무변경(순수 배선).
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

AXIS = [f"c02{n:02d}" for n in range(0, 11)]      # A0–A10 평가자 c0200..c0210
# terminal 키를 반환하는 ROUTE c (slice 2/6 = c0251/c0253; slice 8 Batch A = +6 axis-fail ROUTE).
ROUTE_C = {"c0251", "c0253", "c0250", "c0252", "c0254", "c0255", "c0256", "c0257"}
NEW_BACKBONE = [                                    # slice 7a가 배선한 23c
    "c0200", "c0201", "c0202", "c0204", "c0206", "c0208", "c0209", "c0210",
    "c0001", "c0010", "c0011", "c0012", "c0013", "c0014", "c0015", "c0016",
    "c0017", "c0018", "c0019", "c0022", "c0023", "c0140", "c0141",
]
# ★ GAP-29(RESOLVED slice 7b: 8c에 meta=None 정규화): 정규화 후에도 8c는 완주 strand 미포함(27c 상류
#   미구현)이라 미exercise — 아래 NOMETA∉exercised 불변식은 그대로 유효.
NOMETA = ["c0001", "c0010", "c0011", "c0012", "c0014", "c0016", "c0017", "c0018"]

# 완주 strand = best-path 모든 c가 배선됨(SliceBoundary 없이 끝까지 dispatch 가능).
COMPLETING = [s for s in STRANDS if all(c in REGISTRY for c in s["c_sequence"])]


def _neutral_df():
    """고정 neutral 입력(축-state 미주입). 결과 결정성을 위해 매 strand 사본 사용."""
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


# ===== 완주 규모 =====

def test_completing_count():
    """완주(no SliceBoundary) strand 수. slice 7a=173 → slice 8(Batch A 6 ROUTE)=353 →
    slice 9(Batch B 5 DETECT/VERIFY)=439 (falsifiable, 백로그 누적곡선 일치)."""
    assert len(COMPLETING) == 439


def test_completing_split_by_last_c():
    """완주 439의 종착 구조: ROUTE c 종착 325 + axis 종착 114(c0210 110 + c0201 4).
    slice 9(Batch B)가 route 종착 +40(c0253 +29·c0254 +4·c0255 +6·c0256 +1) + axis 종착 +46(c0210)."""
    route_last = [s for s in COMPLETING if s["c_sequence"][-1] in ROUTE_C]
    axis_last = [s for s in COMPLETING if s["c_sequence"][-1] not in ROUTE_C]
    assert len(route_last) == 325
    assert len(axis_last) == 114
    assert sum(s["c_sequence"][-1] == "c0251" for s in route_last) == 73
    assert sum(s["c_sequence"][-1] == "c0253" for s in route_last) == 61
    # ROUTE c 종착 분포 (Batch A + slice 9 Batch B 누적)
    route_by_last = {"c0250": 74, "c0252": 65, "c0254": 15, "c0255": 21, "c0256": 3, "c0257": 13}
    for c, n in route_by_last.items():
        assert sum(s["c_sequence"][-1] == c for s in route_last) == n, c


# ===== 핵심: actual == best (구조적), 예외 0 =====

def test_actual_equals_best_structural():
    """★ Phase 5 핵심 불변식(규모 검증): 완주 strand 전부 best c_sequence를 그대로 실행하고
    SliceBoundary 없이 종료한다. 실현 terminal 여부와 무관하게 sequence 동치(slice 9: 439/439)."""
    runs = _run_all()
    assert len(runs) == 439
    for s, rec in runs:
        assert rec["boundary_at"] is None, s["sc_id"]
        assert rec["actual_c_sequence"] == s["c_sequence"], s["sc_id"]


def test_no_runtime_exceptions_on_neutral_df():
    """axis verify/detect c가 최소 df에 robust(예외 0) — _run_all이 catch 없이 완주함으로 증명."""
    assert len(_run_all()) == len(COMPLETING)


# ===== skeleton D-S3 + axis N0–N7 =====

def test_skeleton_d_s3_mess_precedes_backbone():
    """D-S3: 완주 strand에서 mess(L-4->L-5) c는 backbone(비 L-4->L-5)보다 앞에 온다(있을 때)."""
    for s in COMPLETING:
        seq = s["c_sequence"]
        mess_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] == "L-4->L-5"]
        backbone_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] != "L-4->L-5"]
        if mess_idx and backbone_idx:
            assert max(mess_idx) < min(backbone_idx), s["sc_id"]


def test_skeleton_axis_n0_n7_ascending():
    """D-S3 골격: 완주 strand의 axis(A0–A10=c0200..c0210) subseq는 c_id 오름차순(N0–N7 순서 무모순)."""
    for s in COMPLETING:
        sub = [c for c in s["c_sequence"] if c in AXIS]
        assert sub == sorted(sub), s["sc_id"]


# ===== D-S1 =====

def test_d_s1_detection_precedes_fix_scale():
    """D-S1: 완주 strand 전체에서 requires_detection_by가 strand에 있으면 항상 그 c 앞에 온다."""
    for s in COMPLETING:
        seq = s["c_sequence"]
        for i, c in enumerate(seq):
            rd = REQUIRES_DETECTION.get(c)
            if rd is not None and rd in seq:
                assert seq.index(rd) < i, (s["sc_id"], c, rd)


# ===== C1 coverage =====

def test_c1_new_backbone_c_in_at_least_one_strand():
    """C1(승인 DoD): slice 7a 배선 23c 각각이 ≥1 strand에 등장."""
    for c in NEW_BACKBONE:
        assert sum(c in s["c_sequence"] for s in STRANDS) >= 1, c


def test_c1_axis_covered_by_completing_strands():
    """C1 규모: axis A0–A10 평가자는 완주 strand로 실제 exercise된다(컬럼 transform은 7b 상류 하류라 미exercise)."""
    exercised = {c for s in COMPLETING for c in s["c_sequence"]}
    for c in AXIS:
        assert c in exercised, c
    # NO-META 8c + 컬럼 transform은 완주 strand에 미포함(7b 소관) — 의도된 미exercise를 명시 고정.
    assert all(c not in exercised for c in NOMETA), "NO-META c가 완주 strand에 등장하면 GAP-29 호출 위험"


# ===== ★ 깨지는 불변식 (1): terminal 실현 GAP — 외부 meta 주입(①) =====

def test_terminal_realization_partial_without_meta():
    """★ slice 8 갱신(발견 2 / GAP-30 영향 노트): slice 7a/7b에서 'meta 미주입 → 기대-q 실현 0'이었으나
    Batch A로 falsify — 완주 439 중 88(c0250 74×Q11 + c0252 14×Q08)이 meta 미주입에도 실현한다
    (slice 9 Batch B는 실현 0 추가 — 신규 86 = starve 40 + axis-None 46).
    c0200/c0204가 '선언 부재'를 fail-state(AIC-MISSING / MISSING-NO-POLICY)로 해석하므로 df-default가
    fail인 A0/A4의 ROUTE c는 외부 meta 없이 실현한다(realization=0은 c0251/c0253처럼 df-default가 pass인
    backbone-only 특성이었음). ① 자체는 미해소 — 나머지 ROUTE 종착 strand는 mis-realize/INVALID-starve로
    ① 결손 규모를 측정한다(slice 8 하네스 test_realization_breakdown 참조). meta 주입은 여전히 ① 소관."""
    runs = _run_all()
    realized = [s for s, rec in runs if s["q_code"] and rec["q_code"] == s["q_code"]]
    assert len(realized) == 88, len(realized)
    by_lastc = Counter(s["c_sequence"][-1] for s in realized)
    assert dict(by_lastc) == {"c0250": 74, "c0252": 14}, dict(by_lastc)


def test_route_realizes_expected_q_with_meta():
    """★ 대조군(① 해소 증명): 동일 완주 strand라도 올바른 축-state meta를 주입하면 wired axis prefix를
    통과해 ROUTE c가 기대 Q를 실현한다 — 실현 경로 자체는 정상, 결손은 meta 주입뿐임을 falsifiable 분리."""
    q02 = next(s for s in COMPLETING if s["q_code"] == "Q02")
    rec = run_strand(q02["c_sequence"], _neutral_df(), {"time_policy": "ambiguous"})
    assert rec["terminal"] == "QUARANTINE" and rec["q_code"] == "Q02", q02["sc_id"]

    q01 = next(s for s in COMPLETING if s["q_code"] == "Q01")
    rec = run_strand(q01["c_sequence"], _neutral_df(), {"obs_blq_state": "blq-no-policy"})
    assert rec["terminal"] == "QUARANTINE" and rec["q_code"] == "Q01", q01["sc_id"]


# ===== ★ 깨지는 불변식 (2): D-S4 runtime-isolated Q-terminal — Phase 7 D-S4(②) =====

def test_d_s4_route_terminated_q_strands_not_isolated():
    """D-S4 부분 통과: ROUTE c(c0251/c0253)로 종착하는 완주 q-strand는 고립 아님(실현 가능)."""
    route_q = [s for s in COMPLETING if s["q_code"] and s["c_sequence"][-1] in ROUTE_C]
    assert route_q
    for s in route_q:
        assert s["c_sequence"][-1] in ROUTE_C, s["sc_id"]


def test_d_s4_q05_runtime_isolated_break():
    """★ falsifiable BREAK: 완주 q-strand 중 4개(전부 Q05)가 ROUTE c가 아니라 axis detect c0201로 종착한다.
    c0201은 route_to_q=Q05만 반환(terminal 키 없음) → orchestrator 미실현 = runtime-isolated Q-terminal.
    INVALID/UNSUPPORTED(axis-only 68 strand)와 동일 class — Phase 7 D-S4 conditional-edge 재구성
    (② GAP-5/8/12/13)이 흡수. 신규 GAP 아님."""
    non_route_q = [s for s in COMPLETING if s["q_code"] and s["c_sequence"][-1] not in ROUTE_C]
    assert len(non_route_q) == 4
    assert all(s["q_code"] == "Q05" for s in non_route_q)
    assert all(s["c_sequence"][-1] == "c0201" for s in non_route_q)


def test_axis_only_terminal_unrealized_break():
    """★ falsifiable BREAK: axis evaluator로 종착하는 114 strand는 전부 terminal=None을 실현한다
    (axis verify/detect는 route_to_q만 반환, run_strand는 ROUTE c의 terminal 키만 실현). 기대 terminal은
    c0210 종착 110=INVALID/UNSUPPORTED, c0201 종착 4=QUARANTINE(Q05) — 모두 미실현(② class, GAP-5/8/12/13).
    slice 9(Batch B)가 c0210 종착 +46(64→110) → axis-only 종착 68→114(Phase 7 D-S4 소관, 미실현 불변)."""
    runs = _run_all()
    axis_last = [(s, rec) for s, rec in runs if s["c_sequence"][-1] not in ROUTE_C]
    assert len(axis_last) == 114
    for s, rec in axis_last:
        assert rec["terminal"] is None, s["sc_id"]          # 공통: 기대 terminal 미실현
    c0210_last = [s for s, _ in axis_last if s["c_sequence"][-1] == "c0210"]
    assert len(c0210_last) == 110
    assert all(s["terminal"] in ("INVALID", "UNSUPPORTED") for s in c0210_last)
    c0201_last = [s for s, _ in axis_last if s["c_sequence"][-1] == "c0201"]
    assert len(c0201_last) == 4
    assert all(s["terminal"] == "QUARANTINE" and s["q_code"] == "Q05" for s in c0201_last)
