"""recipe_emitter — Tier 0 진단을 'WU1 인벤토리 + 실행 recipe + 모델러 체크리스트'로 심화(report-only).

★ 강제 변환이 아니라 *기술(description)·안내* 다. df를 건드리지 않고, 트리에 라우팅하지 않으며,
  strand를 재도출(M2)하지 않는다. 이미 산출된 structure(시트 메타 + top-sample)와 findings(Finding
  리스트)만 읽어 "이 파일을 NONMEM-ready로 만들려면 이 순서로 이걸 하라 + 이 결정은 네가 정하라"를
  문자열로 emit한다. 엔진/SSOT 무수정(엔진 import 무, run_strand 무호출).

honesty 규칙: 감지된 Finding.feature를 넘어서는 모든 주장은 step["verify"](= "확인하라")에 둔다 —
  단정(assert) 금지. adapter가 실제로 본 구조 사실(시트 shape·BW-유사 시트명·마커 셀)만 단정한다.
  conc 출처·wide 변종·수평 반복배치·외부 PDF BW·투여시점 BW는 전부 verify(확인 안내)로만 남긴다. 날조 0.
"""
import re
from pathlib import Path

# 추적성 스탬프 — 런타임 git 호출 안 함(순수·read-only). engine/SSOT는 2004d27에서 frozen(ZERO-diff),
# adapter front-end는 c83c520에 커밋, 본 recipe-emit 확장은 작업트리(미커밋).
BASELINE_STAMP = ("engine/SSOT baseline 2004d27 (frozen, ZERO-diff) · "
                  "adapter front-end c83c520 · recipe-emit: working-tree (uncommitted)")

_STATUS = "described, not executed"

# BW-유사 시트 / comparator 마커(structure_inspector와 의도적 동형 — 각 모듈 자체 상수 house style)
_BW_SHEET = re.compile(r"(\bbw\b|body\s*weight|체중|weights?)", re.I)
_COMPARATOR = re.compile(r"(\brld\b|advagraf|reference\s*listed|대조약|비교약)", re.I)

# WU1 QA-strip 제거 대상(xlsx_ingester._QA_TOKENS의 사람가독 라벨 + 검토 §2 'Abbriviation 정의행')
_QA_REMOVAL_TARGETS = ["Standard samples", "DBLK", "BLK (P)", "QC (LQC/MQC/HQC)",
                       "Calibration curve rows", "Abbreviation/정의 행"]


def _features(findings) -> set:
    return {f.feature for f in findings}


def _sheets_by_shape(structure: dict, shape: str) -> list:
    return [n for n, s in structure["per_sheet"].items() if s["shape_class"] == shape]


def _bw_sheets(structure: dict) -> list:
    return [n for n in structure["sheet_names"] if _BW_SHEET.search(n)]


def _conc_present(structure: dict, feats: set) -> bool:
    """raw conc를 담은 구조(QA에 가려졌거나 wide)가 존재하는가 — dose/BW 작업 필요 신호."""
    return bool(_sheets_by_shape(structure, "qa-contaminated")
                or _sheets_by_shape(structure, "param-summary")
                or "subject-wide-conc" in feats)


def _scan(structure: dict, regex):
    """top-sample 전체에서 regex 매치 (sheet, r, c, val) 산출(structure_inspector._cells 동형)."""
    for name, s in structure["per_sheet"].items():
        for r, row in enumerate(s["sample"]):
            for c, val in enumerate(row):
                if val and regex.search(val):
                    yield name, r, c, val


def _comparator_evidence(structure: dict) -> list:
    """comparator(RLD/Advagraf) 마커를 파일명 + 샘플셀에서 탐지. evidence 리스트(없으면 [])."""
    ev = []
    fname = Path(structure["path"]).name
    if _COMPARATOR.search(fname):
        ev.append(f"filename: {fname!r}")
    for name, r, c, val in _scan(structure, _COMPARATOR):
        ev.append(f"sheet {name!r} r{r + 1}c{c + 1}: {val!r}")
        if len(ev) >= 4:
            break
    return ev


# ---- work-unit builders (감지된 trigger_feature가 있을 때만 호출) -----------

def _wu1_qa(structure: dict) -> dict:
    return {
        "wu": "WU1", "name": "QA-strip", "trigger_feature": "intra-sheet-qa-block",
        "applies": True, "status": _STATUS, "action": "remove",
        "targets": list(_QA_REMOVAL_TARGETS),
        "sheets": _sheets_by_shape(structure, "qa-contaminated"),
        "verify": ["제거 후 남는 행이 실샘플(개체×시점)인지 확인",
                   "Abbreviation/정의 행이 헤더로 오인되지 않게 확인"],
        "note": "QA 행 제거는 PIVOT보다 반드시 선행 — 검량선·DBLK·QC가 관측으로 오염되는 것 차단.",
    }


def _wu1_param_summary(structure: dict) -> dict:
    return {
        "wu": "WU1", "name": "param-summary-reserve", "trigger_feature": "param-summary",
        "applies": True, "status": _STATUS, "action": "skip-and-reserve",
        "sheets": _sheets_by_shape(structure, "param-summary"),
        "verify": ["이 시트가 파생 NCA 요약(raw conc 아님)임을 확인",
                   "보존본을 NCA 대조검증 용도로 따로 둘 것"],
        "note": "★ drop 아님 — SKIP+RESERVE. CRO가 만든 파생 산출물이라 raw conc 빌딩에선 건너뛰되 "
                "NCA 대조용으로 보존(검토 §2).",
    }


def _wu3_pivot(structure: dict, feats: set) -> dict:
    wide_asserted = "subject-wide-conc" in feats   # 구조에서 wide layout 직접 확인됨
    verify = [
        "conc 출처 = 샘플블록(예: '2. Result')이며 param-summary('1. Data')가 아님을 확인",
        "수평 반복배치(예: Blood 1차/2차 좌우 병치) 점검 — 자동감지 아님, 있으면 별도 배치로 분리",
        "wide 변종 분류(sparse / 다중배치 / 다중-arm) — 자동감지 아님, 모델러 확인",
    ]
    if "mean-sd-aggregate" in feats:
        verify.append("Mean/SD 집계열 제외 — 어느 열인지 확인(개별 관측만 유지)")
    if not wide_asserted:
        verify.insert(0, "샘플블록의 wide 여부는 QA행에 가려 자동확정 못 함 — QA-strip 후 layout 확인")
    return {
        "wu": "WU3", "name": "pivot-wide-to-long",
        "trigger_feature": "subject-wide-conc" if wide_asserted else "intra-sheet-qa-block",
        "applies": True, "status": _STATUS,
        "action": "pivot" if wide_asserted else "pivot-after-qa-strip",
        "sheets": (_sheets_by_shape(structure, "subject-wide") if wide_asserted
                   else _sheets_by_shape(structure, "qa-contaminated")),
        "wide_layout_detected": wide_asserted,
        "verify": verify,
        "note": "wide(시간=행, 개체/군=열) → tidy-long. adapter는 pivot을 실행하지 않음(기술만).",
    }


def _wu4_join(structure: dict) -> dict:
    bw = _bw_sheets(structure)
    if bw:
        return {
            "wu": "WU4", "name": "dose-bw-join", "trigger_feature": "dose-bw-sheet-join",
            "applies": True, "status": _STATUS, "action": "join",
            "bw_source": {"in_workbook": True, "sheets": bw},
            "verify": ["AMT용 BW가 '투여시점' 값인지 확인(임의 시점 아님)"],
            "note": "BW를 명시 시트에서 event table로 JOIN; 투여시점 BW로 AMT(=dose×BW) 유도.",
        }
    return {
        "wu": "WU4", "name": "dose-bw-join", "trigger_feature": "dose-bw-sheet-join",
        "applies": True, "status": _STATUS, "action": "join",
        "bw_source": {"in_workbook": False, "sheets": []},
        "verify": ["BW 출처를 외부 보고서에서 확보(예: PDF Table 1) — PDF 존재 단정 아님, 확인 필요",
                   "AMT용 BW가 투여시점 값인지 확인"],
        "note": "BW가 워크북 내 부재 → 외부 출처 필요(예: PDF Table 1). 교차문서 JOIN(자동화 난도↑).",
    }


def _build_checklist(structure: dict, feats: set) -> list:
    """모델러 결정 — flag만(decided=False). adapter는 절대 자동결정하지 않는다(검토 §5)."""
    items = []
    if "blq-token" in feats or "inline-blq" in feats:
        items.append({"id": "blq-zero-policy", "decided": False,
                      "flag": "BLQ/ZERO 통일 정책(M1 / M3 / 제외) — 모델러 결정"})
    if _bw_sheets(structure) or _conc_present(structure, feats):
        items.append({"id": "bw-hierarchy", "decided": False,
                      "flag": "BW 계층(기준 vs 시간가변) — 모델러 결정"})
    comp_ev = _comparator_evidence(structure)
    if comp_ev:
        items.append({"id": "comparator-arm-exclusion", "decided": False,
                      "detected_marker": True, "evidence": comp_ev,
                      "flag": "Advagraf(RLD) 비교-arm 제외 / comedication 필터 — 모델러 결정(다중-arm)"})
    return items


def emit_recipe(structure: dict, findings) -> dict:
    """structure + findings → 파일별 실행 recipe + 모델러 체크리스트(report-only, 기술만).

    감지된 Finding.feature가 있을 때만 해당 WU step을 emit한다(없는 구조를 날조하지 않음).
    """
    feats = _features(findings)
    work_units = []
    if "intra-sheet-qa-block" in feats:
        work_units.append(_wu1_qa(structure))
    if "param-summary" in feats:
        work_units.append(_wu1_param_summary(structure))
    if "subject-wide-conc" in feats or "intra-sheet-qa-block" in feats:
        work_units.append(_wu3_pivot(structure, feats))
    if _bw_sheets(structure) or _conc_present(structure, feats):
        work_units.append(_wu4_join(structure))
    return {
        "source": structure["path"],
        "status": _STATUS,
        "commit_baseline": BASELINE_STAMP,
        "target": "NONMEM-ready tidy-long (subject·time·dv·amt …)",
        "note": "recipe = 기술(description)·안내일 뿐 — adapter는 변환/실행/트리 라우팅을 하지 않는다"
                "(M2 무의존). 각 step은 '이렇게 하라', 각 verify는 '이걸 확인하라', checklist는 '네가 정하라'.",
        "work_units": work_units,
        "checklist": _build_checklist(structure, feats),
    }
