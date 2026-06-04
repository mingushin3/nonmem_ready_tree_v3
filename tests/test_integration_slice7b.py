"""Phase 5 · slice 7b — 프런티어 특성화 + GAP-29 정규화 회귀가드 (measure-not-fix).

slice 7a는 backbone 23c를 배선해 완주(no SliceBoundary) strand 173개를 처음 만들었다. 7b 발주
전제는 "구현됐는데 미배선인 상류 c를 더 배선해 173→~467로 올린다"였다. **본 모듈은 그 전제가
falsifiable하게 반증됨을 고정한다:**

  - 구현 파일(src/c_units/*.py) = REGISTRY 배선 = **46**. 미배선-구현 c = **0** → wiring 천장 = 173.
  - 467 완주는 상류 column-path **27c**(L-1→L-2 + L-2→L-3 + L-3→L-4)를 *신규 구현*해야 도달한다
    (배선 아님 — spec/c_units.json엔 entry만, src엔 파일 부재). 전체 73 blocking c 구현 시 5000.
  - 따라서 7b는 (D1) GAP-29 시그니처 정규화 + (D2) 프런티어 정밀 측정으로 한정한다(신규 c 0).
    27c 구현 백로그 = issues/column_path_implementation_backlog.md, DECISION-D2 column-path 확장.

★ ①(외부 meta 미주입)·②(D-S4 conditional edge)는 27c 구현으로 해소되지 않는 **별개 결손**이다.
   27c는 완주 *경로*만 연다 — 본 모듈이 ①/② 수치가 7b에서 7a와 **불변**임을 규모 재확인한다.

신규 코드는 본 하네스뿐이며 c-unit 본문·dispatch 로직은 무변경(D1은 8c 시그니처에 meta=None 추가).
"""

import glob
import json
import os
import re
from pathlib import Path

import pandas as pd

from src.orchestrator import REGISTRY, dispatch, run_strand

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STRANDS = json.loads((PROJECT_ROOT / "spec" / "strands.json").read_text(encoding="utf-8"))
CUNITS = {c["c_id"]: c for c in
          json.loads((PROJECT_ROOT / "spec" / "c_units.json").read_text(encoding="utf-8"))}

# 구현된 c = src/c_units/cXXXX_*.py 파일이 존재하는 c_id.
IMPL = {re.match(r"(c\d+)", os.path.basename(f)).group(1)
        for f in glob.glob(str(PROJECT_ROOT / "src" / "c_units" / "c*.py"))}
REG = set(REGISTRY.keys())

# 완주 strand = best-path 모든 c가 배선됨.
COMPLETING = [s for s in STRANDS if all(c in REGISTRY for c in s["c_sequence"])]

# blocking c = strand에 등장하나 미배선. upstream(column-path) vs mess(L-4->L-5) 분해.
BLOCKERS = sorted({c for s in STRANDS for c in s["c_sequence"] if c not in REGISTRY})
UPSTREAM27 = sorted(c for c in BLOCKERS
                    if CUNITS[c]["layer_pair"] in ("L-1->L-2", "L-2->L-3", "L-3->L-4"))
MESS46 = sorted(c for c in BLOCKERS if CUNITS[c]["layer_pair"] == "L-4->L-5")

# D1 정규화 대상 8c — orchestrator가 fn(df,meta)로 호출하는 호출규약과 정합되어야 함.
GAP29_C = ["c0001", "c0010", "c0011", "c0012", "c0014", "c0016", "c0017", "c0018"]

# terminal 키를 반환하는 ROUTE c (slice 2/6 = c0251/c0253; slice 8 Batch A = +6 axis-fail ROUTE).
ROUTE_C = {"c0251", "c0253", "c0250", "c0252", "c0254", "c0255", "c0256", "c0257"}


def _complete_if(extra):
    """REGISTRY ∪ extra가 배선된 상태에서 완주 strand 수."""
    full = REG | set(extra)
    return sum(1 for s in STRANDS if all(c in full for c in s["c_sequence"]))


def _neutral_df():
    """7a와 동일한 고정 neutral 입력(축-state 미주입) — ①/② 특성화 동치 비교용."""
    return pd.DataFrame({
        "ID": [1, 1, 2], "TIME": [0, 1, 0], "DV": [0.0, 1.0, 2.0],
        "time_value": [0, 1, 0], "dv_value": [0.1, 0.2, 0.3], "dose": [100.0, None, 200.0],
    })


# ===== 전제 반증: wiring 천장 도달 =====

def test_wiring_ceiling_reached():
    """★ falsifiable: 구현 c 집합 == REGISTRY 배선 집합 → 미배선-구현 c = 0(slice 9: 57==57).
    slice 7b=46 → slice 8(Batch A 6 ROUTE)=52 → slice 9(Batch B 5 DETECT/VERIFY)=57. unwired-implemented = 0."""
    assert IMPL == REG, IMPL ^ REG
    assert len(REG) == 57
    assert [c for c in IMPL if c not in REG] == []


def test_completing_now_439_post_batch_b():
    """완주 strand: slice 8(Batch A 6 ROUTE)=353 → slice 9(Batch B 5 DETECT/VERIFY)=439(+86).
    Batch B는 L-3->L-4 축 평가자를 배선해 완주 path를 열고 L-3->L-4 층을 전부 완성한다(백로그 누적곡선)."""
    assert len(COMPLETING) == 439


# ===== 프런티어: 27 upstream → 467, 73 → 5000 =====

def test_upstream27_yields_467():
    """★ falsifiable: 남은 상류 column-path blocking c를 마저 구현+배선하면 완주 = 정확히 467.
    slice 9(Batch B 5 DET/VER) 후 남은 upstream blocker = 16(=27 − 6 ROUTE − 5 DET/VER). _complete_if는
    REG∪남은16 = 전체 27 상류 배선 = 467로 불변(프런티어가 21→16으로 이동, 목표값 467 고정)."""
    assert len(UPSTREAM27) == 16
    assert _complete_if(UPSTREAM27) == 467


def test_all73_blockers_yield_5000():
    """★ falsifiable: 남은 blocking c 전부 구현+배선 시 완주 = 5000(전수). slice 9 후 남은 blocker =
    62(=73 − 6 ROUTE − 5 DET/VER) = 16 upstream + 46 mess. _complete_if(REG∪남은62)=전체 73 배선=5000 불변."""
    assert len(BLOCKERS) == 62
    assert len(MESS46) == 46
    assert _complete_if(BLOCKERS) == 5000


def test_all_blockers_unimplemented():
    """★ 핵심 반증: 73 blocking c는 전부 미구현(src 파일 부재) — '배선'이 아니라 '신규 구현' 대상."""
    assert all(c not in IMPL for c in BLOCKERS), [c for c in BLOCKERS if c in IMPL]


def test_upstream_layer_decomposition():
    """백로그 정합: 남은 upstream c의 layer_pair 분해. slice 9(Batch B: L-3→L-4 DET/VER 5 완료) 후
    L-3→L-4는 전부 완성(11 = 6 ROUTE + 5 DET/VER) → 남은 = L-1→L-2 4 + L-2→L-3 12."""
    from collections import Counter
    lp = Counter(CUNITS[c]["layer_pair"] for c in UPSTREAM27)
    assert lp == {"L-1->L-2": 4, "L-2->L-3": 12}, dict(lp)


# ===== GAP-29 정규화 회귀가드 =====

def test_gap29_dispatch_callable_no_typeerror():
    """★ GAP-29 RESOLVED 가드: 8c가 orchestrator dispatch(fn(df,meta)) 호출규약으로 호출돼도
    TypeError 0(정규화 전엔 (df)-only라 TypeError). reqdet은 meta에 _ran 주입해 D-S1 충족."""
    df = pd.DataFrame({
        "subject_id": [1, 1, 2], "event_type": ["dose", "obs", "obs"],
        "time_value": [0, 1, 0], "dv_value": [None, 1.0, 2.0],
    })
    for c in GAP29_C:
        rd = CUNITS[c].get("requires_detection_by")
        meta = {f"{rd}_ran": True} if rd else {}
        try:
            dispatch(c, df.copy(), meta)
        except TypeError as e:  # 호출규약 위반만 실패로 본다
            raise AssertionError(f"{c} dispatch raised TypeError (정규화 미적용): {e}")
        except Exception:
            pass  # 로직상 success=False/route 등은 본 가드의 관심사 아님


def test_gap29_backward_compatible_single_arg():
    """후방호환: 8c를 기존 단위테스트처럼 fn(df) 단일인자로 호출해도 정상(meta=None 기본값)."""
    from src.c_units.c0001_verify_column_schema import verify_column_schema
    from src.c_units.c0010_assign_evid import assign_evid
    from src.c_units.c0018_assign_id import assign_id
    df = pd.DataFrame({
        "subject_id": [1, 2], "event_type": ["obs", "obs"],
        "time_value": [0, 1], "dv_value": [1.0, 2.0],
    })
    assert verify_column_schema(df)["pass"] in (True, False)   # df-only 호출 TypeError 없음
    assert assign_evid(df)["success"] in (True, False)
    assert assign_id(df)["success"] in (True, False)


# ===== ①/② 불변: 7b는 ①/②를 바꾸지 않음(27c가 안 건드림) =====

def test_terminal_realization_partial_post_batch_a():
    """★ GAP-30 영향 노트: Batch A로 '① 실현 0' 부분 falsify — 88(c0250 74×Q11 + c0252 14×Q08)이 meta
    미주입에도 실현(c0200/c0204 df-default=fail). slice 9(Batch B)는 실현 0 추가(신규 86 = starve 40 +
    axis-None 46) → 완주 439 중 여전히 88. ① 미해소: 나머지 ROUTE 종착 strand는 meta 부재로 mis/starve
    (measure-not-fix). 상세 분해는 slice 8/9 하네스."""
    runs = [(s, run_strand(s["c_sequence"], _neutral_df(), {})) for s in COMPLETING]
    realized = [s["sc_id"] for s, rec in runs if s["q_code"] and rec["q_code"] == s["q_code"]]
    assert len(realized) == 88, len(realized)


def test_d_s4_axis_terminal_grows_to_114_post_batch_b():
    """★ ②(Phase 7 D-S4 소관): axis evaluator 종착 strand는 전부 terminal 미실현. Batch A 시점 68에서
    slice 9(Batch B)가 c0210 종착 +46을 추가 → axis-only 종착 68→114(미실현 class 불변, count 증가).
    그중 Q05 via c0201 4개 불변. ★ 27c 중 Batch B(축 DET/VER)는 ②를 건드린다(이전 'still unchanged'
    전제 갱신 — 완주 path뿐 아니라 axis-only 종착도 늘린다); Phase 7 conditional-edge가 흡수할 결손."""
    runs = [(s, run_strand(s["c_sequence"], _neutral_df(), {})) for s in COMPLETING]
    axis_last = [(s, rec) for s, rec in runs if s["c_sequence"][-1] not in ROUTE_C]
    assert len(axis_last) == 114
    assert all(rec["terminal"] is None for s, rec in axis_last)
    q05 = [s for s, _ in axis_last if s["q_code"]]
    assert len(q05) == 4
    assert all(s["q_code"] == "Q05" and s["c_sequence"][-1] == "c0201" for s in q05)
