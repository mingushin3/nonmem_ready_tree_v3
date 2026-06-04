"""Phase 5 · slice 1 — coverage (C1–C2) for the MERGED_CELL family. C3 N/A (no Q).

DoD C1 (승인본): "모든 c가 ≥1 strand OR Phase7 conditional-edge incoming ≥1". 본 family는
strand 경로로 충족. C2: 모든 edge traverse — family detect→fix edge + 출구 edge.
"""

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STRANDS = json.loads((PROJECT_ROOT / "spec" / "strands.json").read_text(encoding="utf-8"))

MERGED = [s for s in STRANDS if "c0341" in s["c_sequence"]]


def _edges(seq):
    return set(zip(seq, seq[1:]))


def test_c1_each_family_c_in_at_least_one_strand():
    """C1: c0340, c0341 각각 ≥1 strand에 등장(승인 DoD C1)."""
    assert sum("c0340" in s["c_sequence"] for s in STRANDS) >= 1
    assert sum("c0341" in s["c_sequence"] for s in STRANDS) >= 1


def test_c2_detect_to_fix_edge_traversed():
    """C2: c0340→c0341 edge가 traverse된다(실제로 549 strand 전부)."""
    count = sum(("c0340", "c0341") in _edges(s["c_sequence"]) for s in MERGED)
    assert count >= 1
    assert count == 549


def test_c2_fix_to_backbone_exit_edge():
    """C2: c0341→backbone 출구 edge가 ≥1 strand에 존재(family가 dead-end 아님)."""
    found = any(
        s["c_sequence"].index("c0341") + 1 < len(s["c_sequence"]) for s in MERGED
    )
    assert found


@pytest.mark.skip(reason="C3 N/A: MERGED_CELL family triggers no Q-code (can_route_to_q=[]).")
def test_c3_q_trigger_not_applicable():
    """C3(Q-trigger): MERGED_CELL family는 Q 없음 → 해당 없음(명시 skip)."""


# ===== Phase 5 · Slice 2 — TIME family coverage (C1–C3) =====
# ★ slice 1에서 N/A로 skip되던 C3가 TIME family(Q02/Q12 보유)에서 실제 발화한다.

TIME_NEW = ["c0213", "c0251", "c0310", "c0311", "c0314", "c0315"]
TIME_Q = [s for s in STRANDS if s.get("q_code") in ("Q02", "Q12")]


def test_c1_each_time_c_in_at_least_one_strand():
    """C1: 6개 신규 TIME c 각각 ≥1 strand에 등장."""
    for c in TIME_NEW:
        assert sum(c in s["c_sequence"] for s in STRANDS) >= 1, c


def test_c2_time_edges_traversed():
    """C2: detect→fix(c0310→c0311, c0314→c0315) + 축→ROUTE(c0203→c0251) edge가 traverse된다."""
    for a, b in [("c0310", "c0311"), ("c0314", "c0315"), ("c0203", "c0251")]:
        assert sum((a, b) in _edges(s["c_sequence"]) for s in STRANDS) >= 1, f"{a}->{b}"


def test_c3_q02_q12_triggered():
    """★ C3 활성화(slice 1 skip 대체): Q02·Q12가 strand에서 실제 trigger된다(falsifiable 388/397)."""
    q02 = sum(s.get("q_code") == "Q02" for s in STRANDS)
    q12 = sum(s.get("q_code") == "Q12" for s in STRANDS)
    assert q02 == 388, q02
    assert q12 == 397, q12


def test_c3_q_terminals_have_incoming_route_edge():
    """★ C3/D-S4: Q02·Q12 terminal은 c0251 ROUTE incoming edge ≥1 (고립 Q-terminal 0)."""
    assert TIME_Q
    for s in TIME_Q:
        assert s["c_sequence"][-1] == "c0251", s["sc_id"]


# ===== Phase 5 · Slice 3 — TIMEZONE family coverage (C1–C2; C3 N/A) =====
# ★ c0312/c0313 모두 can_route_to_q=[] → C3(Q-trigger) 해당 없음(slice 1 MERGED_CELL과 동형 skip).

TZ_NEW = ["c0312", "c0313"]
TZ = [s for s in STRANDS if "c0313" in s["c_sequence"]]


def test_c1_each_timezone_c_in_at_least_one_strand():
    """C1: c0312, c0313 각각 ≥1 strand에 등장(실제 532)."""
    for c in TZ_NEW:
        assert sum(c in s["c_sequence"] for s in STRANDS) >= 1, c


def test_c2_timezone_detect_to_fix_edge_traversed():
    """C2: c0312→c0313 edge가 traverse된다(실제로 532 strand 전부)."""
    count = sum(("c0312", "c0313") in _edges(s["c_sequence"]) for s in TZ)
    assert count >= 1
    assert count == 532


def test_c2_timezone_fix_to_backbone_exit_edge():
    """C2: c0313→backbone 출구 edge가 ≥1 strand에 존재(family가 dead-end 아님)."""
    found = any(
        s["c_sequence"].index("c0313") + 1 < len(s["c_sequence"]) for s in TZ
    )
    assert found


@pytest.mark.skip(reason="C3 N/A: TIMEZONE family triggers no Q-code (c0312/c0313 can_route_to_q=[]).")
def test_c3_timezone_not_applicable():
    """C3(Q-trigger): TIMEZONE family는 Q 없음 → 해당 없음(명시 skip)."""


# ===== Phase 5 · Slice 4 — COVARIATE_LAYOUT family coverage (C1–C2) =====
# ★ c0380/c0381 모두 can_route_to_q=[] → C3(Q-trigger) 해당 없음(slice 1/3과 동형 skip).
# 활성화 chain(c0380→…→c0121) edge는 strand-인접 아님 → orchestrator 동적 검증 소관(test_strands).

COV_NEW = ["c0380", "c0381"]
COV = [s for s in STRANDS if "c0380" in s["c_sequence"]]


def test_c1_each_covariate_c_in_at_least_one_strand():
    """C1: c0380, c0381 각각 ≥1 strand에 등장(실제 534). 활성화 대상 c0121도 ≥1(실제 6)."""
    for c in COV_NEW:
        assert sum(c in s["c_sequence"] for s in STRANDS) >= 1, c
    assert sum("c0121" in s["c_sequence"] for s in STRANDS) >= 1


def test_c2_covariate_detect_to_fix_edge_traversed():
    """C2: c0380→c0381 edge가 traverse된다(실제로 534 strand 전부)."""
    count = sum(("c0380", "c0381") in _edges(s["c_sequence"]) for s in COV)
    assert count >= 1
    assert count == 534


def test_c2_covariate_fix_to_backbone_exit_edge():
    """C2: c0381→backbone 출구 edge가 ≥1 strand에 존재(family가 dead-end 아님)."""
    found = any(
        s["c_sequence"].index("c0381") + 1 < len(s["c_sequence"]) for s in COV
    )
    assert found


@pytest.mark.skip(reason="C3 N/A: COVARIATE_LAYOUT family triggers no Q-code (c0380/c0381 can_route_to_q=[]).")
def test_c3_covariate_not_applicable():
    """C3(Q-trigger): COVARIATE_LAYOUT family는 Q 없음 → 해당 없음(명시 skip)."""


# ===== Phase 5 · Slice 5 — PLACEBO_SUBJECT family coverage (C1–C2) =====
# ★ c0392/c0393 모두 can_route_to_q=[] → C3(Q-trigger) 해당 없음(slice 1/3/4와 동형 skip).
# 자기완결: 하류 transform 부재(mess_catalog M103–105) — 활성화 chain 없음(slice 4와 차이).

PBO_NEW = ["c0392", "c0393"]
PBO = [s for s in STRANDS if "c0392" in s["c_sequence"]]


def test_c1_each_placebo_c_in_at_least_one_strand():
    """C1: c0392, c0393 각각 ≥1 strand에 등장(실제 543)."""
    for c in PBO_NEW:
        assert sum(c in s["c_sequence"] for s in STRANDS) >= 1, c


def test_c2_placebo_detect_to_fix_edge_traversed():
    """C2: c0392→c0393 edge가 traverse된다(실제로 543 strand 전부)."""
    count = sum(("c0392", "c0393") in _edges(s["c_sequence"]) for s in PBO)
    assert count >= 1
    assert count == 543


def test_c2_placebo_fix_to_backbone_exit_edge():
    """C2: c0393→backbone 출구 edge가 ≥1 strand에 존재(family가 dead-end 아님)."""
    found = any(
        s["c_sequence"].index("c0393") + 1 < len(s["c_sequence"]) for s in PBO
    )
    assert found


@pytest.mark.skip(reason="C3 N/A: PLACEBO_SUBJECT family triggers no Q-code (c0392/c0393 can_route_to_q=[]).")
def test_c3_placebo_not_applicable():
    """C3(Q-trigger): PLACEBO_SUBJECT family는 Q 없음 → 해당 없음(명시 skip)."""


# ===== Phase 5 · Slice 6 — BLQ_TOKEN family coverage (C1–C3) =====
# ★ slice 4/5에서 N/A로 skip되던 C3가 BLQ family(Q01 보유, c0253 ROUTE)에서 다시 발화한다(slice 2 동형).
#   Q01 라우터는 c0306(NORMALIZE)이 아니라 c0253(ROUTE) — c0306.can_route_to_q=[Q01]은 D-S4 선언(GAP-28).

BLQ_NEW = ["c0305", "c0306", "c0205", "c0253"]
BLQ_MESS_COV = [s for s in STRANDS if "c0306" in s["c_sequence"]]
BLQ_Q01_COV = [s for s in STRANDS if s.get("q_code") == "Q01"]


def test_c1_each_blq_c_in_at_least_one_strand():
    """C1: 신규/배선 BLQ c(c0305,c0306,c0205,c0253) + 활성화 대상 c0020/c0021 각각 ≥1 strand에 등장."""
    for c in BLQ_NEW + ["c0020", "c0021"]:
        assert sum(c in s["c_sequence"] for s in STRANDS) >= 1, c


def test_c2_blq_edges_traversed():
    """C2: detect→fix(c0305→c0306) + 축→ROUTE(c0205→c0253) edge가 traverse된다."""
    for a, b in [("c0305", "c0306"), ("c0205", "c0253")]:
        assert sum((a, b) in _edges(s["c_sequence"]) for s in STRANDS) >= 1, f"{a}->{b}"


def test_c2_blq_fix_to_backbone_exit_edge():
    """C2: c0306→backbone 출구 edge가 ≥1 strand에 존재(mess family가 dead-end 아님)."""
    found = any(
        s["c_sequence"].index("c0306") + 1 < len(s["c_sequence"]) for s in BLQ_MESS_COV
    )
    assert found


def test_c3_q01_triggered():
    """★ C3 재활성화(slice 4/5 skip 대체): Q01이 strand에서 실제 trigger된다(falsifiable 445)."""
    q01 = sum(s.get("q_code") == "Q01" for s in STRANDS)
    assert q01 == 445, q01


def test_c3_q01_terminal_has_incoming_route_edge():
    """★ C3/D-S4: Q01 terminal은 c0253 ROUTE incoming edge ≥1 (고립 Q-terminal 0; c0306 아님, GAP-28)."""
    assert BLQ_Q01_COV
    for s in BLQ_Q01_COV:
        assert s["c_sequence"][-1] == "c0253", s["sc_id"]


# ===== slice 9 — Batch B (L-3->L-4 axis DETECT/VERIFY) =====
BATCHB_NEW = ["c0211", "c0212", "c0214", "c0215", "c0216"]


def test_c1_each_batch_b_c_in_at_least_one_strand():
    """C1(DoD): Batch B 5 axis DETECT/VERIFY c 각각이 ≥1 strand에 등장(dead c 0; 중간 c라 last-c는 아님).
    can_route_to_q는 Phase 7 D-S4 *선언*이라 runtime Q 미실현 — cite-verify는 test_skeleton.py."""
    for c in BATCHB_NEW:
        assert sum(c in s["c_sequence"] for s in STRANDS) >= 1, c
