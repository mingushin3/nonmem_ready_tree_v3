"""Phase 5 · slice 1 — skeleton (D-S3/D-S4) verification for MERGED_CELL.

D-S3: §6 mess-normalization은 N0–N7 backbone의 앞단 전처리(universe_sm §2/§6, line 33:
"Mess Catalog는 그 앞단에 붙는 normalization 전처리"). 따라서 모든 MERGED_CELL strand에서
L-4->L-5 mess c들이 backbone(비 L-4->L-5) c보다 앞에 온다 — 골격 무모순.
D-S4: 이 family는 Q-code를 트리거하지 않으므로 conditional Q-edge/고립 Q-terminal 무기여.
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STRANDS = json.loads((PROJECT_ROOT / "spec" / "strands.json").read_text(encoding="utf-8"))
CUNITS = {c["c_id"]: c for c in
          json.loads((PROJECT_ROOT / "spec" / "c_units.json").read_text(encoding="utf-8"))}

MERGED = [s for s in STRANDS if "c0341" in s["c_sequence"]]


def test_mess_normalization_precedes_backbone():
    """D-S3: 모든 549 strand에서 마지막 L-4->L-5 c index < 첫 비-L-4->L-5 c index."""
    for s in MERGED:
        seq = s["c_sequence"]
        mess_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] == "L-4->L-5"]
        backbone_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] != "L-4->L-5"]
        assert mess_idx, s["sc_id"]
        if backbone_idx:
            assert max(mess_idx) < min(backbone_idx), s["sc_id"]


def test_family_in_mess_stage():
    """c0340/c0341은 L-4->L-5 (mess normalization 전처리 stage)."""
    assert CUNITS["c0340"]["layer_pair"] == "L-4->L-5"
    assert CUNITS["c0341"]["layer_pair"] == "L-4->L-5"


def test_family_introduces_no_q_edge():
    """D-S4: MERGED_CELL family는 Q-code 트리거 없음 → 고립 Q-terminal 무기여."""
    assert CUNITS["c0340"]["can_route_to_q"] == []
    assert CUNITS["c0341"]["can_route_to_q"] == []
    vv = CUNITS["c0340"].get("verify_visualization") or {}
    assert vv.get("fail_route_to") is None


# ===== Phase 5 · Slice 2 — TIME family skeleton (D-S3/D-S4) =====

TIME_MESS = ["c0310", "c0311", "c0314", "c0315"]
TIME_STRANDS = [s for s in STRANDS if any(c in s["c_sequence"] for c in TIME_MESS)]
TIME_Q = [s for s in STRANDS if s.get("q_code") in ("Q02", "Q12")]


def test_time_mess_precedes_backbone():
    """D-S3: TIME mess c(L-4->L-5)는 모든 TIME strand에서 backbone(비 L-4->L-5)보다 앞에 온다."""
    for s in TIME_STRANDS:
        seq = s["c_sequence"]
        mess_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] == "L-4->L-5"]
        backbone_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] != "L-4->L-5"]
        assert mess_idx, s["sc_id"]
        if backbone_idx:
            assert max(mess_idx) < min(backbone_idx), s["sc_id"]


def test_time_c_layer_assignment():
    """TIME mess(c0310/c0311/c0314/c0315)=L-4->L-5; 축(c0203/c0213/c0251)=L-3->L-4."""
    for c in TIME_MESS:
        assert CUNITS[c]["layer_pair"] == "L-4->L-5", c
    for c in ["c0203", "c0213", "c0251"]:
        assert CUNITS[c]["layer_pair"] == "L-3->L-4", c


def test_time_q_terminals_not_isolated():
    """★ D-S4(슬라이스1의 역): c0251.can_route_to_q=[Q02,Q12], 둘 다 ≥1 strand로 도달·c0251로 종착 → 고립 Q-terminal 0."""
    assert CUNITS["c0251"]["can_route_to_q"] == ["Q02", "Q12"]
    reached = {s["q_code"] for s in TIME_Q}
    assert {"Q02", "Q12"} <= reached
    assert all(s["c_sequence"][-1] == "c0251" for s in TIME_Q)


def test_time_convert_q_edge_targets_reachable():
    """D-S4 조기보증: c0311/c0315 can_route_to_q=[Q02] 타깃 Q02 도달가능(Phase 7 conditional-edge 고립 방지)."""
    for c in ["c0311", "c0315"]:
        assert CUNITS[c]["can_route_to_q"] == ["Q02"]
    assert any(s.get("q_code") == "Q02" for s in STRANDS)


# ===== Phase 5 · Slice 3 — TIMEZONE family skeleton (D-S3/D-S4) =====

TZ_MESS = ["c0312", "c0313"]
TZ_STRANDS = [s for s in STRANDS if "c0313" in s["c_sequence"]]


def test_timezone_mess_precedes_backbone():
    """D-S3: 모든 532 strand에서 마지막 L-4->L-5 c index < 첫 비-L-4->L-5(backbone) c index."""
    for s in TZ_STRANDS:
        seq = s["c_sequence"]
        mess_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] == "L-4->L-5"]
        backbone_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] != "L-4->L-5"]
        assert mess_idx, s["sc_id"]
        if backbone_idx:
            assert max(mess_idx) < min(backbone_idx), s["sc_id"]


def test_timezone_c_layer_assignment():
    """c0312/c0313은 L-4->L-5 (mess normalization 전처리 stage)."""
    for c in TZ_MESS:
        assert CUNITS[c]["layer_pair"] == "L-4->L-5", c


def test_timezone_family_introduces_no_q_edge():
    """D-S4: TIMEZONE family는 Q-code 트리거 없음(can_route_to_q=[]) → 고립 Q-terminal 무기여."""
    assert CUNITS["c0312"]["can_route_to_q"] == []
    assert CUNITS["c0313"]["can_route_to_q"] == []
    vv = CUNITS["c0312"].get("verify_visualization") or {}
    assert vv.get("fail_route_to") is None
    assert CUNITS["c0313"].get("verify_visualization") is None


# ===== Phase 5 · Slice 4 — COVARIATE_LAYOUT family skeleton (D-S3/D-S4) =====

COV_MESS_C = ["c0380", "c0381"]
COV_STRANDS = [s for s in STRANDS if "c0380" in s["c_sequence"]]


def test_covariate_mess_precedes_backbone():
    """D-S3: 모든 534 strand에서 마지막 L-4->L-5 c index < 첫 비-L-4->L-5(backbone) c index."""
    for s in COV_STRANDS:
        seq = s["c_sequence"]
        mess_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] == "L-4->L-5"]
        backbone_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] != "L-4->L-5"]
        assert mess_idx, s["sc_id"]
        if backbone_idx:
            assert max(mess_idx) < min(backbone_idx), s["sc_id"]


def test_covariate_c_layer_assignment():
    """c0380/c0381은 L-4->L-5(mess 전처리 stage). 활성화 대상 c0121은 L-2->L-3 backbone(전이 위반 아님)."""
    for c in COV_MESS_C:
        assert CUNITS[c]["layer_pair"] == "L-4->L-5", c
    assert CUNITS["c0121"]["layer_pair"] == "L-2->L-3"


def test_covariate_family_introduces_no_q_edge():
    """D-S4: COVARIATE_LAYOUT family는 Q-code 트리거 없음(can_route_to_q=[]) → 고립 Q-terminal 무기여."""
    assert CUNITS["c0380"]["can_route_to_q"] == []
    assert CUNITS["c0381"]["can_route_to_q"] == []
    vv = CUNITS["c0380"].get("verify_visualization") or {}
    assert vv.get("fail_route_to") is None
    assert CUNITS["c0381"].get("verify_visualization") is None


# ===== Phase 5 · Slice 5 — PLACEBO_SUBJECT family skeleton (D-S3/D-S4) =====

PBO_MESS_C = ["c0392", "c0393"]
PBO_STRANDS = [s for s in STRANDS if "c0392" in s["c_sequence"]]


def test_placebo_mess_precedes_backbone():
    """D-S3: 모든 543 strand에서 마지막 L-4->L-5 c index < 첫 비-L-4->L-5(backbone) c index."""
    for s in PBO_STRANDS:
        seq = s["c_sequence"]
        mess_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] == "L-4->L-5"]
        backbone_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] != "L-4->L-5"]
        assert mess_idx, s["sc_id"]
        if backbone_idx:
            assert max(mess_idx) < min(backbone_idx), s["sc_id"]


def test_placebo_c_layer_assignment():
    """c0392/c0393은 L-4->L-5(mess 전처리 stage). 하류 transform/활성화 대상 없음(자기완결)."""
    for c in PBO_MESS_C:
        assert CUNITS[c]["layer_pair"] == "L-4->L-5", c


def test_placebo_family_introduces_no_q_edge():
    """D-S4: PLACEBO_SUBJECT family는 Q-code 트리거 없음(can_route_to_q=[]) → 고립 Q-terminal 무기여."""
    assert CUNITS["c0392"]["can_route_to_q"] == []
    assert CUNITS["c0393"]["can_route_to_q"] == []
    vv = CUNITS["c0392"].get("verify_visualization") or {}
    assert vv.get("fail_route_to") is None
    assert vv.get("pass_route_to") == "c0393"
    assert CUNITS["c0393"].get("verify_visualization") is None


# ===== Phase 5 · Slice 6 — BLQ_TOKEN family skeleton (D-S3/D-S4) =====

BLQ_MESS_C = ["c0305", "c0306"]
BLQ_STRANDS = [s for s in STRANDS if "c0306" in s["c_sequence"]]
BLQ_Q01 = [s for s in STRANDS if s.get("q_code") == "Q01"]


def test_blq_mess_precedes_backbone():
    """D-S3: BLQ mess c(c0305/c0306, L-4->L-5)는 모든 BLQ strand에서 backbone(비 L-4->L-5)보다 앞에 온다."""
    for s in BLQ_STRANDS:
        seq = s["c_sequence"]
        mess_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] == "L-4->L-5"]
        backbone_idx = [i for i, c in enumerate(seq) if CUNITS[c]["layer_pair"] != "L-4->L-5"]
        assert mess_idx, s["sc_id"]
        if backbone_idx:
            assert max(mess_idx) < min(backbone_idx), s["sc_id"]


def test_blq_c_layer_assignment():
    """BLQ mess(c0305/c0306)=L-4->L-5; A5 축(c0205/c0253)=L-3->L-4; assign(c0020/c0021)=L-1->L-2."""
    for c in BLQ_MESS_C:
        assert CUNITS[c]["layer_pair"] == "L-4->L-5", c
    for c in ["c0205", "c0253"]:
        assert CUNITS[c]["layer_pair"] == "L-3->L-4", c
    for c in ["c0020", "c0021"]:
        assert CUNITS[c]["layer_pair"] == "L-1->L-2", c


def test_blq_q_terminals_not_isolated():
    """★ D-S4: Q01 라우터는 c0253(ROUTE), c0253.can_route_to_q=[Q01, Q15D]. Q01이 ≥1 strand로 도달·c0253로 종착
    → 고립 Q-terminal 0. (c0306.can_route_to_q=[Q01]은 D-S4 *선언*이지 strand 라우터 아님 — GAP-28.)"""
    assert CUNITS["c0253"]["can_route_to_q"] == ["Q01", "Q15D"]
    assert CUNITS["c0306"]["can_route_to_q"] == ["Q01"]  # D-S4 선언(runtime 라우터 아님)
    assert BLQ_Q01
    assert {s["q_code"] for s in BLQ_Q01} == {"Q01"}
    assert all(s["c_sequence"][-1] == "c0253" for s in BLQ_Q01)


def test_blq_route_q_targets_reachable():
    """D-S4 조기보증: c0253이 실제 도달시키는 Q01/Q15D 타깃이 strand에 존재(Phase 7 conditional-edge 고립 방지).
    c0253 실제 라우팅 {Q01,Q15D,INVALID}: Q01/Q15D는 can_route_to_q(결정 C로 Q15D 편입)·INVALID는 terminal_routing(결정 B)."""
    assert any(s.get("q_code") == "Q01" for s in STRANDS)
    assert any(s.get("q_code") == "Q15D" and s["c_sequence"][-1] == "c0253" for s in STRANDS)


# ===== slice 9 — Batch B (L-3->L-4 axis DETECT/VERIFY) =====

def test_batch_b_c_layer_assignment():
    """slice 9 Batch B 축 DETECT/VERIFY(c0211/c0212/c0214/c0215/c0216) = 전부 L-3->L-4 (D-S3 골격 정합)."""
    for c in ["c0211", "c0212", "c0214", "c0215", "c0216"]:
        assert CUNITS[c]["layer_pair"] == "L-3->L-4", c


def test_batch_b_can_route_to_q_is_d_s4_declaration():
    """★ D-S4(GAP-30/32): Batch B detect/verify의 can_route_to_q는 *선언*이지 runtime 라우터 아님.
    c0211/c0212=[Q01](runtime 라우터=c0253) · c0214=[Q10](Q10 ROUTE c 부재 → 미실현 ②) · c0215/c0216=[].
    cite-verify — terminal 키 미반환이므로 신규 고립 Q-terminal을 만들지 않는다(Phase 7 conditional-edge 소관)."""
    assert CUNITS["c0211"]["can_route_to_q"] == ["Q01"]
    assert CUNITS["c0212"]["can_route_to_q"] == ["Q01"]
    assert CUNITS["c0214"]["can_route_to_q"] == ["Q10"]
    assert CUNITS["c0215"]["can_route_to_q"] == []
    assert CUNITS["c0216"]["can_route_to_q"] == []
