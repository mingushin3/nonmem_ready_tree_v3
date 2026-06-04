"""render/build_html_v2.py — index_v2.html: 대학 1학년도 이해하는 '쉬운 설명 뷰' + 파일 진단 마법사.

★ 표현층 전용. 엔진/spec/SSOT 무수정(report-only). 정본 index.html(build_html.py)은 그대로 보존하고,
  본 파일은 별도 산출물 render/index_v2.html만 쓴다. 데이터층(ELES/CUNITS/QINFO/…/LIBS/js)은
  build_html.py를 import해 재사용하고, (1) 색을 진한 앰버(기본 자동경로)+청록(질문 갈림길)로 바꾸고,
  (2) 패널 문구를 쉬운 말 + 코드 배지 + hover 용어집으로 재작성하고, (3) src/adapter 정본을 1:1 미러한
  '내 파일 진단' 마법사를 붙인다.

★ 진단 마법사의 판정 상수(_FILE_PROPERTY/_DATA_DEPENDENT/_CANON_ORDER/_QA_TOKENS)는 src.adapter에서
  직접 import → 빌드 시점에 정본과 동일함이 보장된다(drift 불가). 판정 로직(faithful_tidy 게이트 +
  precondition-gated c-sequence)은 navigator.choose_detect_sequence / xlsx_ingester._classify_shape 를
  그대로 옮긴 것이며, tests/test_render_v2.py가 wizard 판정 == src.adapter.ingest() 임을 검증한다.

색: --hl-single #FFD700→진한 앰버(#E8820C, 실선) · --hl-cond #FFF8B0→청록(#15B4C7, 점선).
    의미(실선=자동 진행 / 점선=질문 Q로 갈리는 갈림길)는 유지하고 색만 교체 → Lock7/index.html 무영향.
"""
import json
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)   # import build_html (sibling)
sys.path.insert(0, _ROOT)   # import src.adapter (repo root)

import build_html as B  # noqa: E402  데이터층 재사용(main 가드 → import 시 index.html 미작성)

# ── 정본 어댑터 상수(live import → drift 불가) ────────────────────────────────
from src.adapter.navigator import _FILE_PROPERTY, _DATA_DEPENDENT, _CANON_ORDER  # noqa: E402
from src.adapter import xlsx_ingester as XI  # noqa: E402  (_QA_TOKENS, _classify_shape priority)
from src.adapter.column_canonicalizer import _SUBJ as _SUBJ_RE  # noqa: E402  (has_subject 판정)


# ═════════════════════════════════════════════════════════════════════════════
# 1. 진단 마법사 — src/adapter 1:1 미러 (WIZARD 상수 + 판정 로직)
# ═════════════════════════════════════════════════════════════════════════════
#
# navigator._precondition_ok(df-present, tidy 케이스)의 컬럼 요구를 데이터로 표현.
#   none           : len(df)>0 (faithful 밴드에선 항상 충족)
#   time           : time_value/TIME 존재 (tidy 시트는 시간 헤더 보장 → canonicalize가 time_value 매핑)
#   dv             : dv_value/DV 존재 (tidy 시트는 농도 헤더 보장)
#   subject+time+dv: 셋 다 (subject 열 유무 = has_subject)
PRECOND = {
    "c0201": "none", "c0210": "none", "c0214": "none", "c0215": "none",
    "c0216": "none", "c0314": "none",
    "c0203": "time", "c0310": "time", "c0312": "time",
    "c0205": "dv", "c0211": "dv", "c0305": "dv",
    "c0212": "subject+time+dv",
}

# honest-stop recipe WU 매핑(recipe_emitter._wu1_qa/_wu1_param_summary/_wu3_pivot/_wu4_join 의 name)
WIZARD_WU = {"qa": "QA-strip", "param": "param-summary-reserve",
             "subject_wide": "pivot-wide-to-long", "dose_bw": "dose-bw-join"}

WIZARD = {
    "file_property_c": list(_FILE_PROPERTY),       # ('c0201','c0210')
    "data_dependent_c": list(_DATA_DEPENDENT),
    "canon_order": list(_CANON_ORDER),
    "qa_tokens": list(XI._QA_TOKENS),
    "shape_priority": ["qa-contaminated", "param-summary", "subject-wide", "tidy-long", "unknown"],
    "precond": dict(PRECOND),
    "wu_map": dict(WIZARD_WU),
    # 사람가독 패턴 설명(브라우저 표시용; 판정에 쓰지 않음)
    "patterns": {
        "tidy": "헤더에 '시간'(time/시간/nominal) 열과 '농도'(conc/DV/농도/observation) 열이 둘 다",
        "subject_wide": "헤더에 개체(subject/animal/개체/동물/ID)류 열이 2개 이상",
        "param_summary": "셀에 'Parameter'와 'Unit'(단위)이 함께 (값은 Mean)",
        "qa": "첫 열에 Standard/DBLK/BLK/QC/Calibration/Blank 등 검량·QA 행",
    },
}


def wizard_verdict_from_answers(a: dict) -> dict:
    """예/아니오 답 → 판정. navigator.choose_detect_sequence 미러(faithful 밴드 컬럼 완비 가정).

    faithful = tidy 시트 존재(ingest: "tidy-long" in shapes). qa/param/subject_wide 는 honest-stop
    '이유'에만 쓰이고 faithful 자체는 막지 않는다(ingest 와 동일 — tidy 시트가 있으면 faithful).
    """
    faithful = bool(a.get("tidy"))
    chosen = set(_FILE_PROPERTY)
    if faithful:
        for c in _DATA_DEPENDENT:
            req = PRECOND[c]
            ok = (req == "none"
                  or req == "time"            # tidy ⇒ 시간 헤더 보장
                  or req == "dv"              # tidy ⇒ 농도 헤더 보장
                  or (req == "subject+time+dv" and bool(a.get("has_subject"))))
            if ok:
                chosen.add(c)
    c_sequence = [c for c in _CANON_ORDER if c in chosen]
    return {
        "faithful_tidy": faithful,
        "entry_node": "N0",
        "c_sequence": c_sequence,
        "honest_stop": (not faithful),
        "stop_at": ("navigable-band-complete" if faithful else "structure-recognition"),
        "gap": (None if faithful else "GAP-37"),
    }


def _answers_from_structure(structure: dict) -> dict:
    """read_workbook_structure 산출 → 마법사 답 벡터(정본 분류기로 도출 — 새 판정 로직 0)."""
    shapes = [s["shape_class"] for s in structure["per_sheet"].values()]
    has_tidy = "tidy-long" in shapes
    has_subject = False
    if has_tidy:
        for s in structure["per_sheet"].values():
            if s["shape_class"] == "tidy-long":
                has_subject = any(_SUBJ_RE.search(h or "") for h in s.get("header_row", []))
                break
    merged = any(s.get("n_merged", 0) for s in structure["per_sheet"].values())
    return {
        "qa": "qa-contaminated" in shapes,
        "param": "param-summary" in shapes,
        "subject_wide": "subject-wide" in shapes,
        "tidy": has_tidy,
        "has_subject": has_subject,
        "multi_or_merged": (structure.get("n_sheets", 1) > 1) or bool(merged),
        "non_ascii": bool(structure.get("non_ascii_present")),
    }


def wizard_verdict_from_structure(structure: dict) -> dict:
    """구조 → 답 → 판정(=ingest 동치 검증용)."""
    return wizard_verdict_from_answers(_answers_from_structure(structure))


# ═════════════════════════════════════════════════════════════════════════════
# 2. 용어집(GLOSSARY) — 코드 집합은 SSOT 파생, 쉬운 말만 큐레이트
# ═════════════════════════════════════════════════════════════════════════════

_PLAIN_AXIS = {
    "A0": "분석 목적 — 무엇을 분석하나(PK·집단PK·PK/PD 등)와 endpoint 종류가 적혀 있나?",
    "A1": "연구 통합 — 한 연구인가, 여러 연구를 합치나(합치면 환자번호 통일 필요)?",
    "A2": "연구 설계 — 평행군·교차·생동성·전임상 등 어떤 구조인가?",
    "A3": "시간 — 사건이 '언제' 일어났는지 정할 수 있나(실제/예정/경과)?",
    "A4": "투약 완전성 — 모든 용량이 적혀 있고 충돌은 없나?",
    "A5": "관측/BLQ — 관측값이 있고, BLQ·LLOQ·ULOQ·반복 처리가 정해져 있나?",
    "A6": "행 분류 — 투약 행과 관측 행을 분명히 나눌 수 있나?",
    "A7": "공변량 — 필요한 공변량이 있고 붙일(연결) 수 있나?",
    "A8": "약물/구획 — 약·대사체가 몇 개이고 구획 번호가 정해졌나?",
    "A9": "결함 복구 — 중복·정렬·인코딩 같은 구조 결함을 고칠 수 있나?",
    "A10": "원본 형식 — 파일이 어떤 형식이고 안정적으로 읽을 수 있나?",
}

_PLAIN_NODE = {
    "N0": "출발 관문 — 분석 목적이 분명하고 endpoint 종류가 적혀 있나?",
    "N1": "개체(사람/동물) 번호를 만들 수 있나?",
    "N2": "사건을 시간순으로 줄세울 수 있나?",
    "N3": "투약 기록을 완성할 수 있나?",
    "N4": "관측 기록을 완성할 수 있나? (관측이 없다고 바로 실패는 아님)",
    "N5": "BLQ·결측·MDV를 처리할 수 있나? (ULOQ 초과 포함)",
    "N6": "공변량을 붙일 수 있나?",
    "N7": "남은 애매함이 기준 이하인가? → 자동/정리/격리 판정",
}

_PLAIN_TERMINAL = {
    "AUTO": "그대로 자동으로 NONMEM-ready 완성",
    "REPAIR": "정해진 정책을 적용해 고치면 ready",
    "QUARANTINE": "데이터는 있으나 결정이 필요 → 사람(스폰서) 답변 대기",
    "UNSUPPORTED": "지금 도구가 다루지 못하는 형식(범위 밖)",
    "INVALID": "핵심 정보가 없어 되살릴 수 없음 → 사용 불가",
}

_PLAIN_KIND = {
    "transform": "변환 — 데이터를 실제로 고치는 작업",
    "detect": "감지 — 문제/패턴이 있는지 찾아냄(고치진 않음)",
    "verify": "검사 — 조건이 맞는지 확인하고 통과/실패 판정",
    "route": "분기 — 막히면 어느 질문/종착으로 보낼지 결정",
}

_PLAIN_LAYER = {
    "L-4->L-5": "가장 바닥 정리 — 글자·인코딩·셀·토큰 정규화(L-5→L-4)",
    "L-3->L-4": "축(A0~A10) 평가 경계 — 잡음 정리 후 갈림길 판단(L-4→L-3)",
    "L-2->L-3": "깔끔한 long 표 만들기 — 시트 합치기·wide→long(L-3→L-2)",
    "L-1->L-2": "NONMEM 핵심 열 부여 — ID/TIME/DV/EVID 등(L-2→L-1)",
}

_PLAIN_Q = {
    "Q01": "BLQ/LLOQ(검출한계) 처리 방법이 안 정해짐 → 방법(M1/M3 등)·LLOQ 값을 정해달라는 질문",
    "Q02": "시간을 실제/예정/경과 중 무엇으로 쓸지, 기준점이 어딘지 안 정해짐",
    "Q03": "집단 PK에서 '회차(occasion)'를 어떻게 나눌지 안 정해짐",
    "Q04": "행이 투약인지 관측인지, 투약-채혈 연결이 애매함",
    "Q05": "여러 연구를 합칠 때 환자번호 충돌 규칙이 없음",
    "Q06": "프로토콜 위반을 어떻게 처리할지 규칙이 없음",
    "Q07": "결측 공변량을 어떻게 채울지 방법이 없음",
    "Q08": "투약 기록 출처 충돌 또는 복원 정책이 없음",
    "Q09": "약물·대사체에 구획(CMT) 번호를 어떻게 줄지 규칙이 없음",
    "Q10": "단위 사전(분자량 MW 포함)이 불완전함",
    "Q11": "분석 목적·endpoint 종류가 충분히 안 적힘",
    "Q12": "시간 기준을 되살릴 수 없음(추가 자료 필요, 또는 사용 불가 수용)",
    "Q13": "외부 공변량 표의 연결키(merge key)가 모호함",
    "Q14": "반복 투약(ADDL/II)과 실제 투약이 충돌, 우선순위 규칙이 없음",
    "Q15A": "데이터 패키지가 불완전(필수 산출물 누락)",
    "Q15B": "정체불명 legacy 표시열의 의미가 문서화 안 됨",
    "Q15C": "실세계 투약 이력 불확실(환자 진술 기반) 미해결",
    "Q15D": "재분석 결과 중 최종본 판정 문서가 없음",
    "Q15X": "어디에도 안 맞는 정체불명 결함(강한 페널티)",
}

# 축별 상태(101개) — 쉬운 말. 코드 집합은 anchors.json(=B.AXIS_STATES) SSOT, 본 dict는 쉬운 말만.
_PLAIN_STATE = {
    # A0 분석 의도
    "A0::AIC-MISSING": "분석 목적이 안 적힘 → 무엇을 분석하는지 먼저 밝혀야 함(Q11)",
    "A0::AIC-PK": "기본 약동학(PK) 분석",
    "A0::AIC-POPPK": "집단 PK(popPK) — '회차(occasion)' 구분 필요",
    "A0::AIC-PKPD": "약물 농도와 효과를 잇는 PK/PD 분석",
    "A0::AIC-ER": "노출(exposure)–반응 분석 — 노출 지표 미리 계산 필요",
    "A0::AIC-DDI": "약물 상호작용(DDI) 분석",
    "A0::AIC-PEDS": "소아 분석 — 용량 재구성 정책 필요",
    "A0::AIC-SPECIAL": "특수집단(신장/간장애 등) 분석",
    "A0::AIC-CUSTOM": "표준에 없는 맞춤 목적 — 정책 문서 필요",
    # A1 연구 통합
    "A1::SINGLE": "연구 하나 — 통합 작업 불필요",
    "A1::MULTI-HOMO": "같은 설계의 여러 연구 — 합치는 규칙 필요(없으면 Q05)",
    "A1::MULTI-HETERO": "설계가 다른 여러 연구 — 합치는 규칙 필요(없으면 Q05)",
    "A1::MULTI-SITE": "같은 연구의 여러 기관 — 환자번호 통일 필요(없으면 Q05)",
    "A1::INTERIM": "중간분석 시점 데이터 — 누적(pooling) 규칙 필요",
    # A2 연구 설계
    "A2::PARALLEL": "평행군 설계(군마다 다른 처치)",
    "A2::SAD-MAD": "단회/반복 용량 증량 시험",
    "A2::CROSSOVER": "교차 설계(한 사람이 여러 처치, 휴약기)",
    "A2::BE": "생물학적 동등성 시험(대조약 vs 시험약)",
    "A2::DDI": "약물 상호작용 시험",
    "A2::FOOD-EFFECT": "음식 영향 시험(공복 vs 식후)",
    "A2::SPECIAL-POP": "특수집단 시험",
    "A2::PEDIATRIC": "소아 시험(체중/체표면적 기반 용량)",
    "A2::TDM-RWD": "치료약물모니터링/실세계데이터(환자 진술 기반 가능)",
    "A2::PRECLINICAL": "전임상(동물) 시험",
    # A3 시간
    "A3::ACTUAL": "실제 측정된 시각(벽시계 시간)",
    "A3::NOMINAL-ONLY": "예정된 시각만 있음(실제 기록 없음)",
    "A3::ACTUAL-PREFERRED": "둘 다 있고 실제 시각을 사용",
    "A3::NOMINAL-PREFERRED": "둘 다 있고 예정 시각을 사용",
    "A3::ELAPSED": "투약 이후 경과시간(상대 시간)",
    "A3::INTERVAL": "구간으로 기록된 시간(예: 2~4시간)",
    "A3::AMBIGUOUS": "시간 해석이 여러 가지로 갈려 애매함 → 사람이 정해야 함(Q02)",
    "A3::UNRECOVERABLE": "시간 정보가 아예 없어 되살릴 수 없음 → 진행 불가(Q12/INVALID)",
    # A4 투약 완전성
    "A4::COMPLETE": "모든 투약이 완비됨 → 자동 진행",
    "A4::WEIGHT-BASED": "체중당 용량(mg/kg) — 재구성 정책 필요",
    "A4::BSA-BASED": "체표면적당 용량(mg/m²) — 정책 필요",
    "A4::PLANNED-FALLBACK": "실제가 없으면 예정 용량 사용",
    "A4::ADDL-II": "등간격 반복 투약(ADDL/II로 압축)",
    "A4::ADDL-ACTUAL-CONFLICT": "반복 투약 정보와 실제 투약이 어긋남 → 우선순위 결정 필요(Q14)",
    "A4::TITRATION-ADAPTIVE": "용량 조절(적정) — 정책 없으면 질문(Q08)",
    "A4::LOADING-MAINTENANCE": "부하+유지 용량 — 정책 없으면 질문(Q08)",
    "A4::INFUSION-STOP-RESTART": "정맥주입 중단/재개·속도변경 — 정책 없으면 질문(Q04)",
    "A4::PARTIAL-RECOVERY": "일부 투약만 있음 → 나머지 추정·표시",
    "A4::COMBINATION": "여러 약 병용 — 경로/구획 정책 필요",
    "A4::MISSING-NO-POLICY": "투약 기록 없고 복원 규칙도 없음 → 질문(Q08)",
    "A4::UNRECOVERABLE": "필수 투약 정보가 없어 되살릴 수 없음 → 진행 불가",
    # A5 관측/BLQ
    "A5::CLEAN": "관측값 깨끗함(BLQ 없음) → 자동 진행",
    "A5::BLQ-FLAGGED": "BLQ가 플래그로 표시 + 정책 있음 → 정리 가능",
    "A5::BLQ-TEXT": "BLQ가 글자로(<0.1, 'BLQ') → 해석·정규화",
    "A5::BLQ-ZERO": "BLQ가 0으로 표시 → 진짜 0과 구분 필요",
    "A5::MULTI-ANALYTE": "여러 분석물질(모약물·대사체) — 구획 정책 필요",
    "A5::LLOQ-CHANGED": "정량하한(LLOQ)이 중간에 바뀜 → 표시·정리",
    "A5::MISSING-MDV1": "관측 결측 → MDV=1로 표시(자동)",
    "A5::BIOANALYTICAL-FINAL-FLAG-MISSING": "여러 분석 결과 중 최종본 표시 없음 → 질문(Q15D)",
    "A5::ABOVE-ULOQ": "정량상한(ULOQ) 초과 + 정책 있음 → 정리 가능",
    "A5::ABOVE-ULOQ-NO-POLICY": "ULOQ 초과인데 처리 정책 없음 → 질문(Q01)",
    "A5::REPLICATE-SAME-TIME": "같은 시점 반복 측정 + 정책 있음 → 정리(평균/대표/모두)",
    "A5::REPLICATE-NO-POLICY": "반복 측정인데 처리 정책 없음 → 질문(Q01)",
    "A5::BLQ-NO-POLICY": "BLQ 있는데 처리 방법(M1/M3…) 없음 → 질문(Q01)",
    "A5::LLOQ-MISSING": "BLQ 있는데 LLOQ 값이 없음 → 질문(Q01)",
    "A5::ABSENT": "관측값이 아예 없음 → 진행 불가(INVALID)",
    # A6 행 분류
    "A6::SEPARABLE": "투약 행과 관측 행이 시각으로 구분됨 → 자동",
    "A6::SAME-TIME-RESOLVABLE": "같은 시각이지만 투약→관측 순서가 정해짐 → 정리 가능",
    "A6::COVARIATE-CHANGE": "공변량 변경 행(EVID=2) 있음 → 표시",
    "A6::RESET-NEEDED": "구획 초기화 행 필요(휴약 등) → 표시",
    "A6::URINE-INTERVAL": "소변 수집 구간(0~4h 등) → 구간 표시",
    "A6::AMBIGUOUS": "행이 투약인지 관측인지 애매함 → 질문(Q04)",
    # A7 공변량
    "A7::NONE-REQUIRED": "공변량 불필요 → 자동",
    "A7::BASELINE-CLEAN": "기저 공변량 완비 → 자동(첫 값 사용)",
    "A7::BASELINE-IMPUTABLE": "기저 공변량 결측 + 보충 정책 있음 → 정리",
    "A7::TIME-VARYING": "시간에 따라 변하는 공변량 → 시점 맞춰 정리",
    "A7::EXTERNAL-JOIN": "별도 표의 공변량 + 연결키 있음 → 합치기",
    "A7::PEDIATRIC-MATURATION": "소아 성숙(나이) 함수 적용 → 정리",
    "A7::KEY-MISSING": "외부 공변량 표의 연결키가 모호 → 질문(Q13)",
    "A7::POLICY-MISSING": "공변량 결측 처리 방법이 없음 → 질문(Q07)",
    # A8 약물/구획
    "A8::SINGLE-DRUG": "약 하나, 구획 하나 → 자동",
    "A8::MULTI-CMT-DEFINED": "여러 약/대사체 + 구획 규칙 있음 → 정리",
    "A8::DDI-VICTIM-ONLY": "상호작용에서 영향 받는 약만 → 정리",
    "A8::DDI-VICTIM-PERPETRATOR": "영향 받고+주는 약 둘 다 → 구획 분리",
    "A8::METABOLITE-DEFINED": "모약물+대사체 별도 구획 → 정리",
    "A8::CMT-POLICY-MISSING": "구획 번호 배정 규칙이 없음 → 질문(Q09)",
    # A9 결함 복구
    "A9::CLEAN": "구조/인코딩 결함 없음 → 자동",
    "A9::DUPLICATE-EXACT": "완전 중복 행 → 중복 제거",
    "A9::UNSORTED": "정렬 안 됨(ID·시간순 아님) → 정렬",
    "A9::COLUMN-SYNONYM": "같은 뜻 열이 여러 개 → 표준 하나 선택",
    "A9::UNIT-CONVERSION": "단위 불일치(mg vs µg) → 표준화",
    "A9::ENCODING-FIX": "문자 인코딩 문제(cp949 등) → UTF-8 변환",
    "A9::PRE-DOSE-SAMPLE": "투약 전 채취(시간<0/'PRE') → 정리",
    "A9::PLANNED-VS-ACTUAL": "예정값·실제값 둘 다 + 선택 정책 → 정리",
    "A9::PROTOCOL-DEVIATION": "프로토콜 위반 기록 있음 → 표시(정책 없으면 Q06)",
    "A9::REANALYSIS-FINAL-DEFINED": "재분석 + 최종본 표시됨 → 정리",
    "A9::REANALYSIS-FINAL-MISSING": "재분석인데 최종본 표시 없음 → 질문(Q15D)",
    "A9::PROTOCOL-DEVIATION-NO-POLICY": "위반 있는데 처리 규칙이 없음 → 질문(Q06)",
    "A9::IRRECONCILABLE": "데이터 무결성 깨짐(해결 불가) → 진행 불가",
    # A10 원본 형식
    "A10::SDTM-ADaM": "CDISC 표준(SDTM/ADaM) 형식 → 자동 파싱",
    "A10::EDC-STRUCTURED": "임상 EDC 추출본 → 평탄화·표준화",
    "A10::CRO-VENDOR": "CRO 제공 형식(벤더별) → 규격대로 파싱",
    "A10::FLAT-TABULAR": "단순 평면 표(깔끔한 CSV/Excel) → 약간 정리",
    "A10::LEGACY-NM": "기존 NONMEM 데이터셋(이미 포맷됨) → 검증",
    "A10::SEMI-STRUCTURED": "여러 시트/표를 합쳐야 함(투약+관측 시트) → 합치기",
    "A10::NON-TABULAR": "표가 아님(텍스트/PDF/이미지) → 미지원",
    "A10::CORRUPTED": "파일 손상(읽기 불가) → 진행 불가",
}

# 통제 어휘(srp_intent의 VERB/NOUN/MODIFIER) — spec/vocabulary.md 기반 쉬운 말.
_PLAIN_VOCAB = {
    # VERB (13)
    "ASSIGN": "값을 채워 넣기", "VERIFY": "검사하기", "CONVERT": "형식 바꾸기",
    "NORMALIZE": "여러 표기를 하나로 통일", "JOIN": "표 합치기(공통 키로)",
    "SPLIT": "한 열/칸을 여러 개로 나누기", "PIVOT": "wide↔long 모양 바꾸기",
    "FILTER": "조건에 맞는 행에 표시(삭제 아님)", "DETECT": "문제/패턴 찾아내기",
    "PROPAGATE": "값을 옆 행으로 채워 퍼뜨리기", "CLASSIFY": "정해진 범주로 분류",
    "EXTRACT": "글 속에서 값 뽑아내기", "ROUTE": "막히면 어디로 보낼지 결정",
    # MODIFIER (7) + BY
    "BY": "범위 한정:", "WITHIN_ID": "개체(ID) 안에서만", "WITHIN_OCCASION": "회차 안에서만",
    "WITHIN_ANALYTE": "분석물질 안에서만", "ACROSS_SHEET": "시트 경계를 넘어",
    "ACROSS_FILE": "파일 경계를 넘어", "PER_SUBJECT": "개체별로 반복", "PER_VISIT": "방문별로 반복",
    # NOUN — NONMEM_COLUMN (10) + BLQ/LLOQ 부수 열
    "ID": "개체 번호 열", "TIME": "시간 열", "DV": "관측값 열", "MDV": "관측결측 표시 열",
    "EVID": "이벤트 종류 열", "AMT": "투여량 열", "CMT": "구획 번호 열", "RATE": "주입 속도 열",
    "ADDL": "추가 투여 횟수 열", "II": "투여 간격 열",
    "BLQ_FLAG": "BLQ 표시 열(정량하한 미만 여부)", "LLOQ": "정량하한 값 열(LLOQ)",
    # NOUN — MESS_CONCEPT (26)
    "NA_TOKEN": "결측 토큰(NA/빈칸/999 등)", "BLQ_TOKEN": "BLQ 토큰(<LLOQ/ND 등)",
    "TIME_FORMAT": "시간 표기 형식", "TIME_ANCHOR": "시간 기준점", "TIMEZONE": "시간대",
    "ID_DTYPE": "ID 자료형(문자/숫자 혼재)", "ID_LEADING_ZERO": "ID 앞자리 0",
    "MERGED_CELL": "병합 셀", "MULTI_LEVEL_HEADER": "다단 헤더", "TRAILING_BLANK": "꼬리 빈 행",
    "DUPLICATE_ROW": "완전 중복 행", "NATURAL_LANGUAGE_DOSE": "자연어 용량('100mg')",
    "NATURAL_LANGUAGE_TIME": "자연어 시간('30분 후')", "FREETEXT_COMMENT": "자유 텍스트 코멘트",
    "EXCEL_FORMULA": "엑셀 수식 잔존", "EXCEL_DATE_SERIAL": "엑셀 날짜 일련번호",
    "NON_ASCII_DECIMAL": "비표준 소수점/천단위", "LINEBREAK_IN_CELL": "셀 안 줄바꿈",
    "SCIENTIFIC_NOTATION": "과학적 표기(1E+3)", "COVARIATE_LAYOUT": "공변량 배치(wide/long)",
    "PRE_DOSE_CODING": "투약 전 시점 코딩", "PLACEBO_SUBJECT": "위약군 피험자",
    "ABOVE_ULOQ": "ULOQ 초과 관측", "REPLICATE_OBS": "정당한 반복 관측",
    "LEGACY_FLAG_PRESENT": "정체불명 legacy 표시열", "RWD_ADHERENCE_UNRESOLVED": "실세계 투약 불확실",
    # NOUN — DOMAIN_ENTITY (9)
    "DOSE_SHEET": "투약 시트", "COVARIATE_SHEET": "공변량 시트", "ANALYTE_COLUMN": "분석물질(농도) 열",
    "BASELINE_COVARIATE": "기저 공변량", "TIME_VARYING_COVARIATE": "시변 공변량",
    "METABOLITE": "대사체", "PARENT_DRUG": "모약물", "OCCASION": "투여 회차",
    "REGIMEN_DESCRIPTOR": "투여 요법 설명",
    # NOUN — FILE_PROPERTY (6)
    "ENCODING": "문자 인코딩", "FILE_FORMAT": "파일 형식", "SHEET_INVENTORY": "시트 목록",
    "BOM": "BOM(바이트순서표시)", "LINE_ENDING": "줄바꿈 문자", "DELIMITER": "구분자",
    # NOUN — UNIT_PROPERTY (4)
    "UNIT_DECLARATION": "단위 표기", "UNIT_CONSISTENCY": "단위 일관성",
    "UNIT_CANONICAL": "단위 표준형", "MOLAR_MASS": "분자량(MW)",
    # NOUN — SCHEMA_PROPERTY (4)
    "COLUMN_SCHEMA": "열 구조(필수 열 존재·타입)", "ROW_ORDERING": "행 정렬 규칙",
    "ROW_LEVEL_INVARIANT": "행 수준 불변조건", "CROSS_COLUMN_INVARIANT": "열 간 불변조건",
}


def build_glossary():
    state = {}
    for ax, sts in B.AXIS_STATES.items():
        for s in sts:
            state[ax + "::" + s] = _PLAIN_STATE.get(ax + "::" + s)
    return {
        "axis": {ax: _PLAIN_AXIS.get(ax) for ax in B.AXIS_IDS},
        "state": state,
        "node": {n: _PLAIN_NODE.get(n) for n in B.BRANCH_IDS},
        "qcode": {q: _PLAIN_Q.get(q) for q in B.Q_IDS},
        "kind": dict(_PLAIN_KIND),
        "layer": dict(_PLAIN_LAYER),
        "terminal": {t: _PLAIN_TERMINAL.get(t) for t in B.PROC_IDS},
        "vocab": dict(_PLAIN_VOCAB),
    }


GLOSSARY = build_glossary()


# ═════════════════════════════════════════════════════════════════════════════
# 2.5 쉬운 LLM 지시문 + R 골격(EASY) — 파일럿 6개
#     정본 spec/c_units.json을 직접 읽어(무수정) 대학 1학년용 카드를 결정적으로 생성한다.
#     카드 = 🎯목표/🧩쉬운설명/📥입력📤출력/(detect)보기별 행선지/🤖복사용 LLM 요청문/📜R 골격.
#     ★ goal/explain/input/output 만 사람이 큐레이트(_EASY_SEED). 나머지(보기 행선지·요청문·R)는
#       정본 필드(srp_intent·llm_prompt·verify_visualization·before_after·r_snippet)에서 파생 →
#       hallucination/Lock4 무위반. renderCPanel은 EASY[id]가 있으면 쉬운 카드, 없으면 기존 표시.
# ═════════════════════════════════════════════════════════════════════════════

def _load_raw_cunits() -> dict:
    d = json.loads((B.ROOT / "spec" / "c_units.json").read_text(encoding="utf-8"))
    if isinstance(d, dict):
        d = d.get("c_units", list(d.values()))
    return {e["c_id"]: e for e in d}


_RAW = _load_raw_cunits()

EASY_PILOT = ["c0210", "c0201", "c0203", "c0011", "c0120", "c0110"]

# 사람 큐레이트(쉬운 말). 코드/행선지/계약은 정본 파생이라 여기 없음.
_EASY_SEED = {
    "c0210": {
        "goal": "내 파일이 8가지 형식 중 무엇인지 알아내고, 컴퓨터가 ‘표로 읽을 수 있는지’ 판정한다.",
        "explain": "정리를 시작하려면 먼저 파일이 표(행·열)로 열리는지부터 확인해야 해요. CDISC 표준인지, "
                   "CRO가 준 엑셀인지, 아니면 스캔한 PDF처럼 아예 표가 아닌지에 따라 다음 작업이 완전히 "
                   "달라집니다. 표가 아니거나(NON-TABULAR) 깨졌으면(CORRUPTED) 여기서 정직하게 멈춥니다.",
        "input": "파일 그 자체 — 확장자, 시트 구조, 첫 줄(헤더) 모양",
        "output": "형식 이름 하나 (meta$a10_state) — 예: 'CRO-VENDOR'",
    },
    "c0201": {
        "goal": "이 데이터가 연구 하나인지, 여러 연구를 합친 것인지 판정한다.",
        "explain": "여러 연구를 합쳐 분석할 때는 환자 번호가 겹치지 않게 통일해야 해요. 그래서 먼저 ‘연구가 "
                   "몇 개인가’부터 봅니다. 합칠 때 번호 충돌을 풀 규칙이 없으면 사람에게 물어봐야 합니다(Q05).",
        "input": "시트·파일 목록과 연구 식별자(study id)",
        "output": "통합 수준 하나 (meta$a1_state) — SINGLE 또는 MULTI-*",
    },
    "c0203": {
        "goal": "사건이 ‘언제’ 일어났는지, 시간을 어떻게 쓸지 정한다(실제/예정/경과 등).",
        "explain": "약을 언제 먹고 언제 채혈했는지는 PK 분석의 핵심이에요. 실제 시각이 있는지, 예정 시각만 "
                   "있는지, 투약 후 경과시간인지에 따라 TIME 열을 만드는 방법이 달라집니다. 해석이 갈리면 "
                   "사람이 정하고(Q02), 시간이 아예 없으면 되살릴 수 없습니다(INVALID).",
        "input": "시간 관련 열(날짜·시각·nominal time)과 기준점(anchor) 정보",
        "output": "시간 정책 하나 (meta$a3_state) — 예: 'ACTUAL-PREFERRED'",
    },
    "c0011": {
        "goal": "각 행이 ‘측정값 없음(MDV=1)’인지 ‘유효 관측(MDV=0)’인지 표시하는 열을 만든다.",
        "explain": "NONMEM은 어떤 행이 실제 측정이고 어떤 행이 투약·결측인지 MDV 열로 구분해요. 투약·리셋 "
                   "행(EVID 1~4)은 측정이 아니니 MDV=1, 관측 행(EVID=0)은 값이 있으면 MDV=0, 비어 있으면 "
                   "MDV=1로 채웁니다. 값을 새로 ‘지어내지’ 않습니다.",
        "input": "EVID 열, 농도값(dv_value) 열",
        "output": "MDV 열(0 또는 1) 추가",
    },
    "c0120": {
        "goal": "옆으로 펼쳐진(wide) 농도 표를 NONMEM이 원하는 ‘세로로 긴(long)’ 표로 바꾼다.",
        "explain": "농도가 ‘Time, DRUG_A, DRUG_B …’처럼 분석물질마다 열로 펼쳐져 있으면 NONMEM이 못 읽어요. "
                   "한 행에 (시간, 분석물질, 농도) 하나씩 들어가도록 녹여야 합니다. 진단 마법사가 ‘표를 "
                   "정리하라(WU3 pivot)’고 할 때 하는 작업이에요.",
        "input": "wide 농도 표 — 분석물질(또는 개체)이 열로 펼쳐짐",
        "output": "long 표 — analyte_label·dv_value 열로 녹임(행 수 = 원본 × 분석물질 수)",
    },
    "c0110": {
        "goal": "따로 있는 투약 시트를 농도 표(main)에 공통 키로 붙인다.",
        "explain": "투약 기록과 농도 측정이 서로 다른 시트에 있을 때가 많아요. 같은 환자·방문을 가리키는 "
                   "공통 키(subject_id, visit)로 두 표를 합쳐야 한 줄에 ‘언제 얼마 투약하고 얼마 측정됐는지’가 "
                   "모입니다. 마법사의 WU4 dose-join이 이 작업입니다.",
        "input": "농도 표(main) + 투약 시트 + 공통 키(c0100에서 식별)",
        "output": "투약 정보(dose_amount, admin_route)가 붙은 통합 표",
    },
    # ── Batch 0 (대표: verify-축 · route · detect-token · transform-normalize) ──
    "c0200": {
        "goal": "이 데이터로 ‘무엇을 분석할지’(분석 목적)가 분명히 적혀 있는지 확인한다.",
        "explain": "PK(약동학=약이 몸에서 변하는 과정) 정리는 ‘약 농도를 분석할지, 노출-반응을 볼지’ 목적이 "
                   "정해져야 시작해요. 목적·endpoint(분석 대상으로 삼는 측정값) 종류가 안 적혀 있으면(AIC-MISSING) "
                   "사람이 정해 줘야 합니다(질문 Q11).",
        "input": "데이터 설명(메타데이터=데이터에 대한 정보)과 분석 계획서",
        "output": "분석 의도 상태 하나 (meta$a0_state) — 예: 'AIC-PK'",
    },
    "c0204": {
        "goal": "투약(약을 준 기록) 정보가 빠짐없이, 충돌 없이 적혀 있는지 판정한다.",
        "explain": "약을 언제 얼마나 줬는지가 완전해야 PK를 계산해요. 체중당 용량인지, 반복 투여를 압축(ADDL=추가 "
                   "투여 횟수·II=투여 간격)했는지, 정맥주입을 중간에 멈췄다 다시 켰는지에 따라 처리가 달라집니다. "
                   "투약 기록·복원 규칙이 없으면 질문(Q08), 반복 투여가 실제와 충돌하면 Q14, 주입 중단/재개 정책이 "
                   "없으면 Q04, 핵심 정보가 없으면 되살리기 불가(INVALID).",
        "input": "투약 관련 열과 투여 요법(regimen=투약 방법) 정보",
        "output": "투약 완전성 상태 하나 (meta$a4_state) — 예: 'COMPLETE'",
    },
    "c0250": {
        "goal": "분석 목적이 비어 있을 때(AIC-MISSING) 사람에게 묻는 질문 Q11로 보낸다.",
        "explain": "갈림길을 정하는 작업이에요(데이터를 고치지 않음). A0(분석 목적) 평가가 ‘목적 없음’으로 나오면 "
                   "사람이 목적을 정해 줘야 하므로 질문 Q11로 ‘라우팅(routing=어디로 보낼지 결정)’합니다.",
        "input": "A0 평가 결과(meta$a0_state)",
        "output": "보낼 곳 결정 — AIC-MISSING이면 질문 Q11",
    },
    "c0042": {
        "goal": "데이터셋 전체 규칙(불변 조건) 위반을 원인별로 알맞은 질문(Q)으로 보낸다.",
        "explain": "검사(c0041)에서 찾은 위반을 원인에 따라 나눠 보내요(고치지 않음). 투약량(AMT) 문제→Q08, "
                   "구획 번호(CMT=약이 들어가는 칸 번호) 문제→Q09, 정량 하한(BLQ=측정 한계 미만) 문제→Q01, "
                   "행이 투약인지 관측인지 모호→Q04.",
        "input": "c0041이 찾은 데이터셋 위반 목록",
        "output": "보낼 질문(Q) 결정 (Q01/Q04/Q08/Q09) 또는 되살리기 불가(INVALID)",
    },
    "c0300": {
        "goal": "‘값 없음’을 뜻하는 여러 표기(토큰=표기, 예: NA·빈칸·999·점)가 어디에 있는지 찾아낸다.",
        "explain": "같은 ‘값 없음’도 NA, N/A, 999, ‘.’, 빈칸처럼 제각각 적혀 있어요. 먼저 어떤 표기가 어느 열에 "
                   "있는지 ‘목록’만 만듭니다(고치는 건 다음 단계 c0301 정규화=여러 표기를 하나로 통일).",
        "input": "원본 표(데이터프레임)",
        "output": "발견된 결측 표기 목록 (meta['na_variants_found'])",
    },
    "c0301": {
        "goal": "c0300이 찾은 여러 ‘값 없음’ 표기를 하나의 표준 빈값(NaN)으로 통일한다.",
        "explain": "NA·N/A·999·‘.’ 처럼 흩어진 ‘값 없음’ 표기를 전부 한 가지 표준값(NaN=비어 있음)으로 바꿔, "
                   "컴퓨터가 일관되게 ‘결측’으로 다루게 합니다(정규화). 다른 표기가 0개 남아야 하고, 진짜 값을 새로 "
                   "지어내지 않습니다.",
        "input": "c0300이 만든 결측 표기 목록",
        "output": "모든 ‘값 없음’ 표기 → NaN(표준 빈값)으로 통일",
    },
    # ── DETECT 나머지 (감지/분류; 대부분 '찾기만 하고 고치진 않음') ──────────────
    "c0130": {
        "goal": "농도 열이 어떤 종류의 측정물질인지 분류한다(단일 약·모약물+대사체·약물상호작용 등).",
        "explain": "한 약만 잰 건지, 모약물과 그 대사체(몸에서 약이 변해 생긴 물질)를 같이 잰 건지, 약물상호작용"
                   "(DDI) 짝인지에 따라 뒤에서 구획 번호(CMT=약이 들어가는 칸 번호) 배정이 달라져서 먼저 분류해요.",
        "input": "분석물질(농도) 관련 열들, A8 축 상태",
        "output": "분석물질 유형 (meta['analyte_type']) — single/multi/metabolite/ddi",
    },
    "c0131": {
        "goal": "대사체가 있으면 모약물과 대사체의 관계를 분류하고 구획 번호 매핑을 정한다.",
        "explain": "대사체(몸에서 약이 변해 생긴 물질)가 있으면 어느 열이 모약물이고 어느 게 대사체인지 짝지어야 "
                   "구획 번호(CMT)를 제대로 줄 수 있어요.",
        "input": "분석물질 열 이름, 화합물 정보",
        "output": "모약물↔대사체 관계 지도 (meta['parent_metabolite_map'])",
    },
    "c0150": {
        "goal": "각 행이 투약인지·관측인지·공변량 변경인지·리셋인지 분류한다.",
        "explain": "한 줄 한 줄이 ‘약을 준 기록(투약)’인지 ‘피를 뽑아 잰 기록(관측)’인지 등을 구분해야 NONMEM이 "
                   "사건을 이해해요. 구분이 안 되면 사람에게 묻는 질문(Q04).",
        "input": "원본 사건 정보가 든 표",
        "output": "+event_type 열 (dose=투약/obs=관측/cov_change=공변량변경/reset=리셋)",
    },
    "c0202": {
        "goal": "이 연구가 어떤 설계인지 분류한다(평행군·교차·생동성·전임상 등).",
        "explain": "연구 설계에 따라 데이터 구조가 달라요. 평행군(군마다 다른 처치), 교차(한 사람이 여러 처치), "
                   "생동성(대조약 비교), 전임상(동물) 등 10가지 중 하나로 정합니다.",
        "input": "연구 계획서 정보, 투약 패턴",
        "output": "연구 설계 상태 하나 (meta$a2_state) — 예: 'SAD-MAD'",
    },
    "c0205": {
        "goal": "관측값 상태와 정량 한계(BLQ) 처리 상황을 15가지 중 하나로 판정한다.",
        "explain": "농도가 깨끗한지, 정량 하한 미만(BLQ=너무 낮아 정확히 못 잼)이 있는지, 정량 상한 초과(ULOQ)·"
                   "반복 측정이 있는지 봅니다. BLQ인데 처리 방법(M1/M3 등)이 없으면 질문(Q01), 관측값이 아예 없으면 "
                   "되살리기 불가(INVALID).",
        "input": "관측(농도) 열, BLQ 표시",
        "output": "관측/BLQ 상태 하나 (meta$a5_state) — 예: 'BLQ-TEXT'",
    },
    "c0206": {
        "goal": "투약 행과 관측 행을 분명히 나눌 수 있는지 판정한다.",
        "explain": "같은 시각에 투약과 관측이 겹칠 때 순서를 정할 수 있는지, 공변량 변경·리셋 행이 있는지 봅니다. "
                   "투약인지 관측인지 모호하면 질문(Q04).",
        "input": "사건 행들(시간/투약/관측 구조)",
        "output": "행 분류 상태 하나 (meta$a6_state) — 예: 'SAME-TIME-RESOLVABLE'",
    },
    "c0207": {
        "goal": "필요한 공변량(나이·체중 등 설명 변수)이 있고 데이터에 붙일 수 있는지 판정한다.",
        "explain": "공변량(분석에 쓰는 부가 정보: 체중·나이·신장기능 등)이 필요 없는지, 기저값이 깨끗한지, 시간에 "
                   "따라 변하는지, 외부 표에서 붙여야 하는지 봅니다. 연결 키(공통 열)가 없으면 Q13, 결측 채우는 방법이 "
                   "없으면 Q07.",
        "input": "공변량 가용성, 분석 요구사항",
        "output": "공변량 부착 상태 하나 (meta$a7_state) — 예: 'BASELINE-CLEAN'",
    },
    "c0208": {
        "goal": "약/대사체가 몇 개이고 구획 번호(CMT)를 어떻게 줄지 판정한다.",
        "explain": "약이 하나인지, 여러 약/대사체인지, 약물상호작용 짝인지에 따라 ‘구획 번호(CMT=약이 들어가는 칸 "
                   "번호)’를 어떻게 매길지 정해요. 배정 규칙이 없으면 질문(Q09).",
        "input": "분석물질 열, 약물/투여경로 정보",
        "output": "다약물/구획 상태 하나 (meta$a8_state) — 예: 'SINGLE-DRUG'",
    },
    "c0211": {
        "goal": "정량 상한(ULOQ=너무 높아 정확히 못 잼)을 넘는 관측값이 있는지 찾아낸다.",
        "explain": "농도가 측정기 상한을 넘으면(>ULOQ) 그대로 쓰면 안 돼요. 그런 값이 있는지 찾습니다. 처리 정책이 "
                   "없으면 질문(Q01).",
        "input": "관측값, ULOQ 기준값",
        "output": "ULOQ 초과 여부 (meta['has_above_uloq'])와 해당 행 표시",
    },
    "c0212": {
        "goal": "같은 개체·같은 시각에 정당한 반복 측정(값이 2개 이상)이 있는지 찾아낸다.",
        "explain": "같은 (개체,시간)에서 농도를 두 번 이상 잰 ‘정당한 반복’을 찾습니다(모든 칸이 똑같은 ‘완전 중복’과는 "
                   "다름). 처리 정책이 없으면 질문(Q01).",
        "input": "개체·시간·농도가 있는 관측 행",
        "output": "반복 측정 여부 (meta['has_replicates'])와 반복 묶음 표시",
    },
    "c0215": {
        "goal": "완전히 똑같은 행(완전 중복)이 있는지 찾아낸다(A9 평가 보조).",
        "explain": "모든 칸이 똑같은 행이 있는지 봅니다. 같은 시각 다른 값인 ‘반복 측정’과는 다릅니다.",
        "input": "전체 표",
        "output": "완전 중복 존재 여부 (meta['has_exact_duplicates'])",
    },
    "c0216": {
        "goal": "글자 깨짐 같은 인코딩(글자 저장 방식) 문제가 남아 있는지 찾아낸다.",
        "explain": "한글이 깨지는 인코딩(글자를 컴퓨터에 저장하는 방식, 예: cp949) 문제가 바닥 정리 뒤에도 남았는지 "
                   "확인합니다(A9 평가 보조).",
        "input": "문자 열, 인코딩 정보",
        "output": "인코딩 문제 여부 (meta['has_encoding_issues'])",
    },
    "c0305": {
        "goal": "정량 하한 미만 표기(BLQ; <LLOQ·ND·<0.1 등)가 있는지 찾아낸다.",
        "explain": "‘<0.1’, ‘BLQ’, ‘ND(검출 안 됨)’ 같은 표기가 농도 칸에 있는지 찾고, 숫자로 된 정량 하한(LLOQ) 값도 "
                   "보존하는지 확인합니다(고치는 건 c0306).",
        "input": "관측(농도) 열",
        "output": "발견된 BLQ 표기 목록과 LLOQ 값 (meta['blq_variants_found'])",
    },
    "c0310": {
        "goal": "시간 값이 어떤 형식인지 찾아낸다(시:분, 경과시간, 소수, 날짜시각 등).",
        "explain": "‘1:30’ 같은 시계 표기인지, ‘1.5’ 같은 경과시간인지, 날짜+시각인지에 따라 나중에 숫자로 바꾸는 "
                   "방법이 달라져서 먼저 형식만 알아냅니다.",
        "input": "시간 열",
        "output": "감지된 시간 형식 (meta['time_format_detected'])",
    },
    "c0312": {
        "goal": "시간대(타임존)가 섞였는지 찾아낸다(서머타임·12시간 vs 24시간 등).",
        "explain": "측정 시각이 서로 다른 시간대(KST·JST 등)나 12/24시간 표기로 섞이면 시간 계산이 틀려요. 그런 "
                   "불일치가 있는지 찾습니다.",
        "input": "시간 열",
        "output": "시간대 문제 (meta['tz_issues'])",
    },
    "c0314": {
        "goal": "시간 기준점(anchor=시간을 재는 출발점) 표기가 섞였는지 찾아낸다(Day 1·Visit 1·날짜 혼재).",
        "explain": "‘Day 1’, ‘Visit 1’, ‘2024-01-15’처럼 기준점(언제를 0으로 볼지)이 섞이면 시간을 못 맞춰요. 그런 "
                   "혼재를 찾습니다.",
        "input": "시간 기준점 열",
        "output": "기준점 유형 (meta['time_anchor_type'])",
    },
    "c0320": {
        "goal": "개체 번호(ID) 값의 자료형(문자/숫자)이 섞였는지 찾아낸다.",
        "explain": "ID가 어떤 행은 숫자 1, 어떤 행은 글자 ‘002’처럼 섞이면 같은 개체를 다르게 볼 수 있어요. 그런 "
                   "혼재를 찾습니다.",
        "input": "ID 열",
        "output": "ID 자료형 혼재 여부 (meta['id_dtype_mixed'])",
    },
    "c0322": {
        "goal": "개체 번호(ID)에 앞자리 0(‘001’ 등)이 있는지 찾아낸다.",
        "explain": "‘001’처럼 앞에 0이 붙은 ID는 숫자로 바꾸면 0이 사라져 1과 헷갈릴 수 있어요. 그런 ID가 있는지 찾습니다.",
        "input": "ID 열",
        "output": "앞자리 0 존재 여부 (meta['has_leading_zero'])",
    },
    "c0330": {
        "goal": "각 열의 단위(mg/mL 등) 표기가 빠졌거나 섞였는지 찾아낸다.",
        "explain": "농도·체중 같은 값은 단위가 분명해야 해요. 단위가 안 적혔거나, 몰농도(molar=분자 개수 기준)와 "
                   "질량(mass=무게 기준)이 섞였는지 찾습니다.",
        "input": "열 정보(헤더 등)",
        "output": "열별 단위 상태 (meta['unit_status'])",
    },
    "c0332": {
        "goal": "몰농도↔질량 변환에 필요한 분자량(MW) 사전이 있는지 확인한다.",
        "explain": "몰농도(분자 개수 기준)와 질량(무게 기준)을 서로 바꾸려면 분자량(MW)이 필요해요. MW가 없으면 변환 "
                   "불가라 질문(Q10).",
        "input": "단위 정보",
        "output": "분자량 사전 가용 여부 (meta['mw_available'])",
    },
    "c0340": {
        "goal": "엑셀 병합 셀(여러 칸을 하나로 합쳐 아래가 빈칸처럼 보이는 것)이 있는지 찾아낸다.",
        "explain": "엑셀에서 셀을 병합하면 첫 칸만 값이 있고 아래는 빈칸이 돼요. 그대로 읽으면 값이 비어 보여서, "
                   "병합이 있는지 먼저 찾습니다(채우는 건 c0341).",
        "input": "표(데이터프레임)",
        "output": "병합 셀 존재 여부 (meta['has_merged_cells'])",
    },
    "c0342": {
        "goal": "머리글(헤더=표 맨 위 제목줄)이 두 줄 이상인 다단 헤더인지 찾아낸다.",
        "explain": "제목줄이 두 층(예: 위는 ‘PK/공변량’, 아래는 ‘ID/TIME/DV’)이면 컴퓨터가 헷갈려요. 그런 다단 "
                   "헤더를 찾습니다(한 줄로 펴기=c0343).",
        "input": "원본 파일의 머리글 행들",
        "output": "다단 헤더 여부 (meta['has_multi_header'])",
    },
    "c0344": {
        "goal": "표 끝에 붙은 빈 행(꼬리 빈 행)이 몇 개인지 찾아낸다.",
        "explain": "데이터 아래에 빈 행이 따라붙는 경우가 많아요. 잘못 세면 행 수가 틀리니, 끝의 빈 행 개수를 셉니다"
                   "(제거는 c0345).",
        "input": "표",
        "output": "꼬리 빈 행 개수 (meta['n_trailing_blank'])",
    },
    "c0346": {
        "goal": "완전히 똑같은 행(완전 중복)이 몇 개인지 찾아낸다.",
        "explain": "모든 칸이 동일한 행이 몇 번 나오는지 셉니다. 같은 시각 다른 값인 ‘반복 측정’과는 다릅니다"
                   "(표시는 c0347).",
        "input": "표",
        "output": "완전 중복 개수 (meta['n_exact_duplicates'])",
    },
    "c0350": {
        "goal": "사람 말로 적힌 투여량(‘100 mg’, ‘two tablets’)이 있는지 찾아낸다.",
        "explain": "투여량이 숫자가 아니라 ‘100 mg’, ‘알약 2개’처럼 말로 적히면 계산을 못 해요. 그런 표현이 있는지 "
                   "찾습니다(숫자로 뽑는 건 c0351).",
        "input": "투여량 열",
        "output": "자연어 투여량 존재 여부 (meta['has_nl_dose'])",
    },
    "c0352": {
        "goal": "사람 말로 적힌 시간(‘predose’, ‘after 30 min’)이 있는지 찾아낸다.",
        "explain": "시간이 ‘투약 전’, ‘30분 후’처럼 말로 적히면 숫자로 못 써요. 그런 표현을 찾습니다(숫자로 뽑는 건 "
                   "c0353).",
        "input": "시간 열",
        "output": "자연어 시간 존재 여부 (meta['has_nl_time'])",
    },
    "c0354": {
        "goal": "자유롭게 쓴 메모(코멘트) 열이 있는지 찾아낸다.",
        "explain": "‘특이사항’ 같은 긴 자유 텍스트 열은 분석값과 섞이면 안 돼요. 그런 메모 열을 찾습니다(분리는 c0355).",
        "input": "표",
        "output": "자유 텍스트 열 목록 (meta['freetext_cols'])",
    },
    "c0360": {
        "goal": "파일의 인코딩(글자 저장 방식: UTF-8·CP949 등)을 알아낸다.",
        "explain": "한글 파일은 저장 방식(인코딩)이 여러 가지라, 맞는 방식으로 안 읽으면 글자가 깨져요. 어떤 "
                   "인코딩인지 먼저 알아냅니다(UTF-8로 바꾸기=c0361).",
        "input": "원본 파일 바이트",
        "output": "감지된 인코딩 (meta['detected_encoding'])",
    },
    "c0362": {
        "goal": "파일 맨 앞의 보이지 않는 표식(BOM=Byte Order Mark)이 있는지 찾아낸다.",
        "explain": "어떤 파일은 맨 앞에 눈에 안 보이는 표식(BOM)이 붙어 첫 열 이름이 깨져 읽혀요. 그게 있는지 "
                   "찾습니다(제거는 c0363).",
        "input": "파일 첫 바이트",
        "output": "BOM 존재 여부 (meta['has_bom'])",
    },
    "c0364": {
        "goal": "줄바꿈 문자 종류(LF/CRLF/CR)가 섞였는지 찾아낸다.",
        "explain": "운영체제마다 줄바꿈 표시(LF·CRLF)가 달라 섞이면 줄이 깨질 수 있어요. 어떤 줄바꿈인지·섞였는지 "
                   "찾습니다(통일은 c0365).",
        "input": "원본 파일",
        "output": "줄바꿈 종류 (meta['line_ending'])",
    },
    "c0366": {
        "goal": "칸을 나누는 구분자(쉼표·탭·세미콜론)가 무엇인지 찾아낸다.",
        "explain": "CSV는 값을 쉼표·탭 등으로 나누는데, 무엇으로 나눴는지 알아야 표로 읽혀요. 그 구분자를 찾습니다"
                   "(쉼표로 통일=c0367).",
        "input": "원본 파일",
        "output": "구분자 (meta['delimiter'])",
    },
    "c0368": {
        "goal": "파일 안의 시트(엑셀 탭) 목록을 찾아 정리한다.",
        "explain": "엑셀에 여러 시트(탭)가 있으면 어디에 투약·농도·인적사항이 들어 있는지 먼저 목록을 만들어야 해요.",
        "input": "파일(엑셀·여러 시트)",
        "output": "시트 목록 (meta['sheet_inventory'])",
    },
    "c0370": {
        "goal": "엑셀 수식 글자(‘=SUM(...)’ 등)가 값 대신 남아 있는지 찾아낸다.",
        "explain": "엑셀에서 수식이 값으로 안 바뀌고 ‘=SUM(...)’ 글자로 남으면 숫자로 못 읽어요. 그런 수식이 있는지 "
                   "찾습니다(처리는 c0371).",
        "input": "표",
        "output": "수식 잔존 여부 (meta['has_formulas'])",
    },
    "c0372": {
        "goal": "엑셀 날짜가 숫자(일련번호, 예: 43831)로 남아 있는지 찾아낸다.",
        "explain": "엑셀은 날짜를 속으로 숫자로 저장해서, 가끔 ‘43831’ 같은 숫자로 보여요. 그런 날짜 숫자를 찾습니다"
                   "(날짜로 변환=c0373).",
        "input": "날짜/시간 열",
        "output": "날짜 일련번호 존재 여부 (meta['has_date_serial'])",
    },
    "c0374": {
        "goal": "소수점이 쉼표(‘1,5’)거나 천 단위 쉼표(‘1,000’)인지 찾아낸다.",
        "explain": "나라마다 소수점을 ‘.’ 대신 ‘,’로 쓰기도 해서(‘1,5’=1.5), 그대로 읽으면 숫자가 틀려요. 그런 표기를 "
                   "찾습니다(통일은 c0375).",
        "input": "숫자 열(텍스트로 저장된)",
        "output": "비표준 소수점 여부 (meta['has_non_ascii_decimal'])",
    },
    "c0376": {
        "goal": "과학적 표기(‘1E+3’=1000 같은 표기)가 있는지 찾아낸다.",
        "explain": "큰/작은 수를 ‘1E+3’처럼 적은 게 글자로 남으면 숫자로 못 읽을 수 있어요. 그런 표기를 찾습니다"
                   "(숫자로 풀기=c0377).",
        "input": "숫자 열",
        "output": "과학적 표기 여부 (meta['has_sci_notation'])",
    },
    "c0378": {
        "goal": "한 셀(칸) 안에 줄바꿈이 들어 있는지 찾아낸다.",
        "explain": "한 칸 안에 줄바꿈(엔터)이 있으면 그 줄이 두 줄로 잘못 읽힐 수 있어요. 그런 칸을 찾습니다(처리는 c0379).",
        "input": "표",
        "output": "셀 내 줄바꿈 여부 (meta['has_cell_linebreak'])",
    },
    "c0380": {
        "goal": "공변량(체중 등 부가 정보)이 가로로 펼쳐졌는지(wide) 세로로 길게(long) 있는지 찾아낸다.",
        "explain": "체중이 ‘WT_방문1, WT_방문2’처럼 옆으로 펼쳐졌는지(wide=가로), 한 줄에 하나씩(long=세로) 인지 "
                   "확인만 합니다(모양 바꾸기=피벗은 나중 단계).",
        "input": "공변량 열",
        "output": "공변량 배치 (meta['cov_layout']) — wide/long/none",
    },
    "c0381": {
        "goal": "공변량 배치를 분류해 태그를 붙인다(피벗은 나중 단계로 미룸).",
        "explain": "c0380이 찾은 배치(wide=가로/long=세로)를 분류해 표시만 합니다. 실제 가로→세로 변환(피벗=PIVOT)은 "
                   "뒤 단계(L-2↔L-3)에서 해요.",
        "input": "meta['cov_layout']",
        "output": "배치 분류 태그(피벗은 2b 단계로 미룸)",
    },
    "c0390": {
        "goal": "투약 전 시점 표기(음수 시간·‘PRE’·t=0)가 어떻게 돼 있는지 찾아낸다.",
        "explain": "약 먹기 ‘전’ 채혈을 음수 시간(-0.5), ‘PRE’, 0 등으로 제각각 적어요. 어떤 방식인지 찾습니다"
                   "(통일은 c0391).",
        "input": "시간/투약 열",
        "output": "투약 전 코딩 패턴 (meta['predose_pattern'])",
    },
    "c0392": {
        "goal": "위약(가짜약)군 피험자가 있는지 찾아낸다(투여량 0 vs 투약 누락 구분).",
        "explain": "위약군은 일부러 약을 0으로 준 거라, ‘투여량 0(의도)’과 ‘투약 기록 빠짐(결함)’을 구분해야 해요. "
                   "위약군이 있는지 찾습니다(분류는 c0393).",
        "input": "투약 열, 피험자 정보",
        "output": "위약군 존재 여부 (meta['has_placebo'])",
    },
    "c0393": {
        "goal": "위약군을 가려내고 ‘투여량 0(의도된 위약)’ vs ‘투약 누락(결함)’으로 분류한다.",
        "explain": "투여량이 0인 게 일부러(위약)인지 실수로 빠진 건지 분류해, 진짜 위약군 피험자 목록을 만듭니다.",
        "input": "meta['has_placebo']",
        "output": "위약군 피험자 목록 (meta['placebo_subjects'])",
    },
    "c0394": {
        "goal": "뜻이 문서에 없는 정체불명 표시 열(예: OLD_DATA·FLAG)이 있는지 찾아낸다.",
        "explain": "예전에 누가 붙인 ‘OLD_DATA’, ‘EXCLUDE’ 같은 열이 설명 없이 있으면 함부로 못 써요. 그런 열 이름·값을 "
                   "찾아 보고합니다(임의 해석 금지).",
        "input": "모든 열",
        "output": "정체불명 표시 열 존재 여부·목록 (meta['legacy_flag_columns'])",
    },
    "c0396": {
        "goal": "실세계/TDM 데이터에서 투약 이력이 환자 진술에만 의존하는지 찾아낸다.",
        "explain": "실제 진료 데이터(RWD)나 치료약물모니터링(TDM)은 ‘환자가 말한’ 투약에만 의존할 때가 있어 "
                   "불확실해요. 그런지 확인합니다(불확실하면 Q15C).",
        "input": "투약 열, meta['study_design']",
        "output": "투약 이력 불확실 여부 (meta['rwd_adherence_unresolved'])",
    },
    # ── TRANSFORM 나머지 (실제로 데이터를 고침) ──────────────────────────────────
    "c0010": {
        "goal": "각 행의 사건 종류를 NONMEM의 EVID 코드(숫자)로 매긴다.",
        "explain": "‘투약/관측/리셋’ 같은 사건 라벨을 NONMEM이 아는 숫자(EVID: 투약=1, 관측=0, 리셋=2, 리셋+투약=3, "
                   "항정상태 투약=4)로 바꿔요. 못 매기는 행은 사람에게 묻는 질문(Q04)으로 표시.",
        "input": "event_type(사건 라벨: dose/obs/reset 등) 열",
        "output": "+EVID 열 (0~4 정수)",
    },
    "c0012": {
        "goal": "투여량(AMT) 열을 NONMEM 규격으로 표준화한다.",
        "explain": "투약 행(EVID 1·3·4)은 투여량 AMT>0이어야 하고, 투약이 아닌 행(EVID 0·2)은 AMT=0이에요. 투약인데 "
                   "AMT가 비었으면 질문(Q08).",
        "input": "EVID 열, 원본 투여량(dose_amount)",
        "output": "+AMT 열 (투약>0, 비투약=0)",
    },
    "c0013": {
        "goal": "구획 번호(CMT=약이 들어가는 칸 번호)를 A8 정책대로 매긴다.",
        "explain": "약 하나면 투약 칸=1·관측 칸=2처럼 간단하지만, 여러 약/대사체면 분석물질·경로별로 칸 번호를 "
                   "나눠요. 규칙이 없으면 질문(Q09).",
        "input": "EVID·analyte_label(분석물질명)·투여경로, A8 축 상태",
        "output": "+CMT 열 (양의 정수)",
    },
    "c0014": {
        "goal": "주입 속도(RATE) 열을 매긴다(한번에 주사 vs 천천히 주입 구분).",
        "explain": "한번에 주사(bolus)면 RATE=0, 일정 속도로 천천히 주입하면 RATE>0(투여량÷시간), 모델이 속도를 "
                   "추정하면 -1, 시간 추정이면 -2예요.",
        "input": "EVID·원본 주입속도/주입시간",
        "output": "+RATE 열 (0, >0, -1, -2)",
    },
    "c0015": {
        "goal": "규칙적 반복 투여를 ADDL(추가 투여 횟수)로 압축한다.",
        "explain": "같은 사람에게 같은 용량을 일정 간격으로 여러 번 주면, 첫 행에 ‘추가로 몇 번 더(ADDL)’를 적어 "
                   "줄 수를 줄여요. 반복 정보가 실제 투약과 충돌하면 질문(Q14).",
        "input": "EVID·AMT·TIME·개체ID, A4 축 상태",
        "output": "+ADDL 열 (0 이상 정수)",
    },
    "c0016": {
        "goal": "반복 투여 간격(II)을 매긴다.",
        "explain": "ADDL(추가 투여 횟수)이 있는 행에 ‘몇 시간마다 줬는지(II=투여 간격)’를 적어요. ADDL=0이면 II=0. "
                   "단위는 TIME과 같게.",
        "input": "ADDL 열·TIME 열",
        "output": "+II 열 (0 이상; ADDL>0이면 II>0)",
    },
    "c0017": {
        "goal": "관측값(DV=종속 변수=잰 농도 등) 열을 NONMEM 규격으로 표준화한다.",
        "explain": "실제 관측 행(EVID=0·MDV=0)은 DV에 잰 값을, 관측이 아닌 행은 DV=0 또는 ‘.’을 넣어요. PK 농도는 "
                   "음수가 없어야 합니다.",
        "input": "EVID·MDV·원본 관측값(dv_value)",
        "output": "+DV 열 (숫자 또는 '.')",
    },
    "c0018": {
        "goal": "개체 번호(ID)를 NONMEM 규격(양의 정수)으로 바꾼다.",
        "explain": "‘PT-001’ 같은 글자 ID를 1, 2처럼 양의 정수로 다시 매겨요. 원본↔정수 대응표를 남겨 나중에 되짚을 "
                   "수 있게 합니다.",
        "input": "원본 개체 식별자(subject_id, 문자/숫자 섞여도 됨)",
        "output": "+ID 열 (앞자리 0 없는 양의 정수)",
    },
    "c0019": {
        "goal": "시간 값을 NONMEM의 TIME(단위 통일된 숫자)으로 바꾼다.",
        "explain": "A3(시간 정책)에 따라 실제/예정/경과 시간을 골라, ‘1:30’ 같은 표기를 1.5처럼 일관된 숫자(시간 또는 "
                   "분 단위)로 바꿔요.",
        "input": "원본 시간값(time_value), A3 축 상태",
        "output": "+TIME 열 (단위 통일된 실수)",
    },
    "c0020": {
        "goal": "정량 하한 미만(BLQ) 표시 열을 A5 정책대로 만든다.",
        "explain": "BLQ(너무 낮아 정확히 못 잰 값) 처리 방법이 M3/M4(우도법)면 BLQ 행에 BLQ_FLAG=1을 달고, M1(제외)이면 "
                   "열을 안 만들어요. 정책이 없으면 질문(Q01).",
        "input": "EVID·blq_detected, A5 축 상태·BLQ 정책",
        "output": "+BLQ_FLAG 열 (조건부, 0/1)",
    },
    "c0021": {
        "goal": "정량 하한값(LLOQ) 열을 A5 정책대로 매긴다.",
        "explain": "BLQ_FLAG 열이 있으면 정량 하한(LLOQ=정확히 잴 수 있는 가장 낮은 값) 열도 있어야 해요. 시점마다 "
                   "LLOQ가 바뀌면 시점별로 적용. LLOQ가 없으면 질문(Q01).",
        "input": "EVID·BLQ_FLAG·원본 LLOQ, A5 축 상태",
        "output": "+LLOQ 열 (관측 행에 양의 실수)",
    },
    "c0022": {
        "goal": "기저 공변량(시작 시점 체중·나이·성별 등)을 NONMEM 숫자 코딩으로 바꾼다.",
        "explain": "연속값(체중)은 그대로, 범주값(성별 M/F)은 정수(0/1 등)로 바꿔요. 결측은 A7 정책대로 채우되"
                   "(결측이 남으면 안 됨), 함부로 지어내지 않습니다.",
        "input": "기저 공변량 열들(범주 문자 포함 가능), A7 축 상태",
        "output": "공변량 열 → 전부 숫자(연속=실수, 범주=정수)",
    },
    "c0023": {
        "goal": "시간에 따라 변하는 공변량(체중·신장기능 등)을 시점별 숫자로 코딩한다.",
        "explain": "시점마다 달라지는 값(예: 체중 변화)을 해당 행에 맞춰 넣어요. 빈 시점은 직전 값 유지(LOCF=마지막 "
                   "값 이어쓰기) 또는 A7 정책으로 채우되, 결측이 남으면 안 됩니다.",
        "input": "시변 공변량 열들, A7 축 상태·시점 매핑",
        "output": "시변 공변량 열 → 행마다 숫자",
    },
    "c0031": {
        "goal": "행을 NONMEM 규격으로 정렬한다(개체→시간→투약 먼저).",
        "explain": "1순위 개체 번호(ID) 오름차순, 2순위 같은 개체 안에서 시간(TIME) 오름차순, 3순위 같은 시각이면 "
                   "투약 행을 관측 행보다 앞에 둬요.",
        "input": "ID·TIME·EVID 열(정렬 안 됨)",
        "output": "같은 열들, 행 순서만 정렬",
    },
    "c0111": {
        "goal": "따로 있는 공변량 시트(체중·나이 등)를 농도 표에 공통 키로 붙인다.",
        "explain": "인적사항(체중·나이·성별)이 다른 시트에 있으면, 같은 개체를 가리키는 공통 키로 합쳐(조인=JOIN, "
                   "공통 열로 두 표 합치기) 한 표에 모아요(기준은 농도 표).",
        "input": "공변량 시트 + 공통 키(c0101에서 식별)",
        "output": "농도 표에 WT·AGE·SEX 등 공변량 열 추가",
    },
    "c0121": {
        "goal": "가로로 펼쳐진 공변량을 세로로 긴(long) 형태로 바꾼다.",
        "explain": "체중이 ‘WT_방문1, WT_방문2’처럼 옆으로 펼쳐졌으면(wide=가로), 한 줄에 하나씩(long=세로)으로 "
                   "녹여요(피벗=PIVOT, 가로↔세로 모양 바꾸기). 이미 long이면 그대로 둡니다.",
        "input": "wide 형태 공변량 열(예: WT_V1, WT_V2), A7 축 상태",
        "output": "long 형태 공변량(시점마다 한 줄에 한 값)",
    },
    "c0140": {
        "goal": "기저 공변량을 각 개체의 시작 시점에서 뽑아 그 개체 모든 행에 채워 넣는다.",
        "explain": "체중·나이 같은 기저값을 개체의 첫 시점에서 가져와 그 사람 모든 줄에 똑같이 붙여요. 기저값이 "
                   "깨끗하면 그대로, 비었으면 A7 채움 정책 적용.",
        "input": "공변량 원본 열들, A7 축 상태",
        "output": "개체별 기저 공변량이 모든 행에 채워짐",
    },
    "c0141": {
        "goal": "시간에 따라 변하는 공변량을 시점에 맞춰 각 행에 붙인다.",
        "explain": "A7이 ‘시변(시간에 따라 변함)’이면, 시점별 체중·크레아티닌 등을 해당 시각 행에 맞춰 넣어요"
                   "(외부 시트가 이미 합쳐져(조인=JOIN) 있으면 시점 매핑).",
        "input": "시변 공변량 열·TIME 열, A7 상태",
        "output": "시점별 공변량이 각 행에 부착",
    },
    "c0161": {
        "goal": "단위가 섞인 열을 하나의 표준 단위로 변환한다.",
        "explain": "같은 열에 mg/L과 µg/mL이 섞이면 값이 틀려요. 변환 계수를 적용해 한 표준 단위로 통일합니다. "
                   "몰농도↔질량 변환에 분자량(MW)이 필요하면 질문(Q10).",
        "input": "단위가 섞인 숫자 열들, 단위 지도",
        "output": "열마다 단일 표준 단위로 통일된 숫자",
    },
    "c0306": {
        "goal": "c0305가 찾은 BLQ 표기를 표준 표시로 바꾸고 정량 하한값(LLOQ)을 보존한다.",
        "explain": "‘<0.1’ 같은 표기를 표준 빈값으로 바꾸되, 그 숫자(0.1)는 정량 하한(LLOQ)으로 따로 보존하고 "
                   "‘BLQ였음’ 표시도 남겨요(값을 함부로 0으로 단정하지 않음).",
        "input": "c0305가 찾은 BLQ 표기 목록",
        "output": "BLQ 표기 → 표준 표시 + LLOQ 숫자 열 보존",
    },
    "c0311": {
        "goal": "찾아낸 시간 형식을 숫자(경과 시간) 또는 표준 날짜시각으로 끝까지 바꾼다.",
        "explain": "‘1:30’ 같은 표기를 1.5(시간)처럼 계산 가능한 숫자로, 또는 표준 날짜시각(ISO)으로 파싱(컴퓨터가 "
                   "읽을 수 있게 해석)해요.",
        "input": "meta['time_format_detected']",
        "output": "time_value → 숫자/표준 날짜시각으로 파싱 완료",
    },
    "c0313": {
        "goal": "여러 시간대를 하나의 기준으로 통일한다.",
        "explain": "KST·JST처럼 섞인 시간대를 한 기준으로 맞추고, 서머타임·12/24시간 모호함을 없애요.",
        "input": "meta['tz_issues']",
        "output": "시간값 → 단일 시간대로 통일",
    },
    "c0315": {
        "goal": "시간 기준점 표기(Day 1 등)를 비교 가능한 숫자로 바꾼다.",
        "explain": "‘Day 1’, ‘Day 2’ 같은 기준점을 0시간, 24시간처럼 비교 가능한 숫자로 파싱(해석)해요.",
        "input": "meta['time_anchor_type']",
        "output": "기준점 → 비교 가능한 숫자",
    },
    "c0321": {
        "goal": "개체 번호(ID) 자료형을 하나로 통일한다.",
        "explain": "숫자 1과 글자 ‘002’처럼 섞인 ID를 같은 형식(전부 문자 또는 전부 숫자)으로 맞춰, 같은 개체가 "
                   "갈라지지 않게 해요.",
        "input": "meta['id_dtype_mixed']",
        "output": "subject_id → 균일한 자료형",
    },
    "c0323": {
        "goal": "ID의 앞자리 0을 정책대로 처리한다(보존 또는 제거).",
        "explain": "‘001’의 앞 0을 살릴지 뺄지 정책에 따라 일관되게 처리해요(여기선 보통 보존).",
        "input": "meta['has_leading_zero']",
        "output": "subject_id → 앞자리 0 정책대로 처리됨",
    },
    "c0331": {
        "goal": "단위 표기를 표준형으로 바꾼다(㎍→µg 등).",
        "explain": "‘㎍/㎖’ 같은 특수문자 단위를 표준 표기(µg/mL)로 바꿔 컴퓨터가 일관되게 읽게 해요.",
        "input": "meta['unit_status']",
        "output": "단위 표준화·태깅",
    },
    "c0341": {
        "goal": "엑셀 병합 셀로 생긴 빈칸을 위 값으로 채운다(아래로 흘려보냄).",
        "explain": "병합 셀은 첫 칸만 값이 있고 아래가 비어요. 위 값을 아래로 채워(forward-fill=아래로 채우기) 모든 "
                   "행에 제대로 값이 들어가게 합니다. 병합 잔존 0개.",
        "input": "meta['has_merged_cells']",
        "output": "병합으로 빈 칸이 위 값으로 채워짐",
    },
    "c0343": {
        "goal": "두 줄짜리 머리글(다단 헤더)을 한 줄로 편다.",
        "explain": "위·아래 두 층 제목줄을 합쳐 한 줄 이름(예: ‘PK_ID’)으로 만들어 컴퓨터가 열을 제대로 알아보게 해요.",
        "input": "meta['has_multi_header']",
        "output": "단일 행 평탄 헤더",
    },
    "c0345": {
        "goal": "표 끝에 붙은 빈 행을 제거한다.",
        "explain": "데이터 뒤에 따라붙은 빈 행을 지워 행 수가 정확해지게 해요.",
        "input": "meta['n_trailing_blank']",
        "output": "꼬리 빈 행 제거됨",
    },
    "c0347": {
        "goal": "완전히 똑같은 행을 ‘표시(flag)’한다(삭제는 안 함).",
        "explain": "완전 중복 행에 표시만 달아요(함부로 지우지 않음 — 진짜 반복일 수도 있어 사람이 확인하도록).",
        "input": "meta['n_exact_duplicates']",
        "output": "+duplicate_flag 열(중복 표시)",
    },
    "c0351": {
        "goal": "말로 적힌 투여량(‘100 mg’)에서 숫자와 단위를 뽑아낸다.",
        "explain": "‘100 mg’을 (숫자 100, 단위 ‘mg’)로 분리해 계산 가능하게 해요. 애매하면 질문(Q08).",
        "input": "meta['has_nl_dose']",
        "output": "투여량 → (숫자, 단위)",
    },
    "c0353": {
        "goal": "말로 적힌 시간(‘after 30 min’)을 숫자 시간으로 뽑아낸다.",
        "explain": "‘투약 전’→-0.5, ‘30분 후’→0.5처럼 말로 된 시간을 숫자(시간 단위)로 바꿔요.",
        "input": "meta['has_nl_time']",
        "output": "시간 → 숫자(시간)",
    },
    "c0355": {
        "goal": "자유 텍스트 메모 열을 데이터 열과 분리한다.",
        "explain": "긴 메모(코멘트) 열을 분석값 열과 떼어 내, 숫자 분석을 방해하지 않게 해요(메모는 따로 보존).",
        "input": "meta['freetext_cols']",
        "output": "메모 열이 분리됨",
    },
    "c0361": {
        "goal": "파일 인코딩(글자 저장 방식)을 UTF-8로 바꾼다.",
        "explain": "cp949 등으로 저장돼 깨지는 한글을, 표준 방식(UTF-8)으로 바꿔 안 깨지게 해요.",
        "input": "meta['detected_encoding']",
        "output": "인코딩 = UTF-8",
    },
    "c0363": {
        "goal": "파일 맨 앞의 보이지 않는 표식(BOM)을 제거한다.",
        "explain": "맨 앞 숨은 표식(BOM) 때문에 첫 열 이름이 깨지면, 그 표식을 떼어 내요.",
        "input": "meta['has_bom']",
        "output": "BOM 제거됨",
    },
    "c0365": {
        "goal": "줄바꿈 문자를 하나로 통일한다(LF 또는 CRLF).",
        "explain": "섞인 줄바꿈 표시를 한 가지로 맞춰 줄이 깨지지 않게 해요.",
        "input": "meta['line_ending']",
        "output": "일관된 줄바꿈",
    },
    "c0367": {
        "goal": "칸 구분자를 쉼표로 표준화한다.",
        "explain": "탭·세미콜론 등으로 나뉜 값을 표준 쉼표(comma) 구분으로 바꿔요.",
        "input": "meta['delimiter']",
        "output": "구분자 = 쉼표",
    },
    "c0371": {
        "goal": "남아 있는 엑셀 수식 글자를 값으로 평가하거나 제거한다.",
        "explain": "‘=SUM(...)’ 글자를 실제 계산값으로 바꾸거나 지워, 숫자로 읽히게 해요.",
        "input": "meta['has_formulas']",
        "output": "수식 글자 → 값/제거",
    },
    "c0373": {
        "goal": "엑셀 날짜 숫자(일련번호)를 진짜 날짜로 바꾼다.",
        "explain": "‘43831’ 같은 엑셀 내부 날짜 숫자를 ‘2020-01-01’ 같은 날짜로 변환해요.",
        "input": "meta['has_date_serial']",
        "output": "일련번호 → 날짜",
    },
    "c0375": {
        "goal": "소수점을 ‘.’으로 통일하고 천 단위 구분자를 없앤다.",
        "explain": "‘1,5’(=1.5)의 쉼표 소수점을 ‘.’으로 바꾸고, ‘1,000’의 천 단위 쉼표를 없애 숫자로 제대로 읽히게 해요.",
        "input": "meta['has_non_ascii_decimal']",
        "output": "소수점=‘.’, 천 단위 구분자 제거",
    },
    "c0377": {
        "goal": "과학적 표기(‘1E+3’)를 보통 숫자(1000)로 푼다.",
        "explain": "‘1E+3’ 같은 표기가 글자로 남으면 보통 숫자(1000)로 풀어 계산되게 해요.",
        "input": "meta['has_sci_notation']",
        "output": "과학적 표기 → 보통 숫자",
    },
    "c0379": {
        "goal": "한 칸 안의 줄바꿈을 없애거나 안전하게 바꾼다.",
        "explain": "칸 안 줄바꿈(엔터) 때문에 줄이 잘못 갈라지지 않게, 그 줄바꿈을 제거하거나 공백 등으로 바꿔요.",
        "input": "meta['has_cell_linebreak']",
        "output": "칸 내 줄바꿈 제거/치환",
    },
    "c0391": {
        "goal": "투약 전 시점 표기를 정책대로 하나로 통일한다.",
        "explain": "‘PRE’, 음수 시간 등 제각각인 투약 전 표기를 일관된 값(예: -0.5)으로 맞춰요.",
        "input": "meta['predose_pattern']",
        "output": "투약 전 코딩 표준화",
    },
    # ── VERIFY (검사; 데이터 안 바꾸고 통과/실패만 판정) ─────────────────────────
    "c0001": {
        "goal": "깔끔한 long 표(L-2)가 NONMEM 열을 만들 준비가 됐는지 검사한다.",
        "explain": "사건 종류·개체·시간·투여량·농도 같은 ‘뜻이 있는 열’이 다 있고 결측 없이 매핑되는지 확인해요. "
                   "통과해야 다음(NONMEM 열 부여)으로 갑니다.",
        "input": "L-2 tidy long 표(한 줄=한 측정)",
        "output": "통과/실패 판정만(데이터 안 바꿈)",
    },
    "c0030": {
        "goal": "행이 NONMEM 순서(개체→시간 오름차순)대로 정렬됐는지 검사한다.",
        "explain": "개체 번호가 커지는 순서, 같은 개체 안에서 시간이 커지는 순서인지 확인해요. 어긋나면 정렬 작업"
                   "(c0031)을 부르고, 시간이 모호하면 질문(Q02/Q04).",
        "input": "ID·TIME·EVID 열",
        "output": "통과/실패 판정만",
    },
    "c0040": {
        "goal": "각 행이 지켜야 할 규칙(행 수준 불변 조건)을 모두 만족하는지 검사한다.",
        "explain": "예: 개체 번호는 양의 정수, 투약 행은 투여량>0, 관측 행은 값 존재, ADDL↔II 짝 맞음 등 행별 규칙"
                   "(I-R01~I-R15)을 다 지키는지 봐요.",
        "input": "NONMEM 핵심 열 전부(ID·TIME·DV·MDV·EVID·AMT·CMT 등)",
        "output": "통과/실패 + 위반 행 목록",
    },
    "c0041": {
        "goal": "데이터셋 전체가 지켜야 할 규칙(데이터셋 수준 불변 조건)을 검사한다.",
        "explain": "예: 유효 관측이 최소 1개 있는지, 머리글이 있는지, 투약 기록이 있는지, 단위가 일관된지"
                   "(I-D01~I-D07) 등 전체 규칙을 봐요.",
        "input": "NONMEM 데이터셋 전체",
        "output": "통과/실패 + 위반 목록",
    },
    "c0100": {
        "goal": "여러 시트 중 투약 시트를 찾고, 합칠 공통 키가 있는지 검사한다.",
        "explain": "투약 정보가 별도 시트에 있을 때, 그 시트가 있는지와 농도 표와 합칠 공통 열(개체·방문·날짜)이 "
                   "있는지 확인해요. 키가 없으면 질문(Q08/Q15A).",
        "input": "시트별 표 목록과 시트 정보",
        "output": "투약 시트 존재 + 공통 키 유효 판정",
    },
    "c0101": {
        "goal": "여러 시트 중 공변량 시트를 찾고, 합칠 공통 키가 있는지 검사한다.",
        "explain": "인적사항(체중·나이·성별)이 별도 시트에 있을 때, 그 시트와 합칠 공통 키가 있는지 확인해요. "
                   "키가 없으면 질문(Q13/Q07).",
        "input": "시트별 표 목록과 시트 정보",
        "output": "공변량 시트 존재 + 공통 키 유효 판정",
    },
    "c0102": {
        "goal": "여러 분석물질이 가로로 펼쳐졌는지 검사하고 피벗(가로→세로) 전략을 정한다.",
        "explain": "약이 여러 개면 농도가 ‘DRUG_A, DRUG_B’처럼 옆으로 펼쳐졌는지 보고, 세로로 녹일(피벗=PIVOT) 대상 "
                   "열을 정해요. 못 하면 질문(Q09).",
        "input": "가로형일 수 있는 분석물질 열, A8 축 상태",
        "output": "피벗 전략 결정(데이터 안 바꿈)",
    },
    "c0160": {
        "goal": "한 열 안에서 단위가 일관적인지 검사한다.",
        "explain": "같은 농도 열에 mg/L과 µg/mL이 섞이거나 몰농도/질량이 섞이지 않았는지 확인해요. 필요했던 단위 "
                   "변환이 끝났는지도 봅니다. 불일치면 질문(Q10).",
        "input": "단위 정보가 있는 숫자 열",
        "output": "단위 일관성 통과/실패",
    },
    "c0209": {
        "goal": "구조 결함(중복·정렬·단위·인코딩 등)을 고칠 수 있는지 13가지 중 하나로 판정한다.",
        "explain": "깨끗한지, 완전 중복·정렬 안 됨·열 이름 동의어·단위 불일치·인코딩(글자 저장 방식) 문제 등 어떤 "
                   "결함인지 정해요. "
                   "프로토콜 위반 처리 규칙이 없으면 질문(Q06), 무결성이 깨져 못 고치면 되살리기 불가(INVALID).",
        "input": "전체 표, 데이터 품질 지표",
        "output": "결함 수리 상태 하나 (meta$a9_state) — 예: 'DUPLICATE-EXACT'",
    },
    "c0213": {
        "goal": "시간 기준점(언제를 0으로 볼지)이 일관되고 해석 가능한지 검사한다.",
        "explain": "‘Day 1’과 ‘Visit 1’, 날짜가 섞이지 않았는지 확인해요. 모호하면 질문(Q02).",
        "input": "시간 기준점 표기/정보",
        "output": "기준점 일관성 통과/실패",
    },
    "c0214": {
        "goal": "모든 숫자 열에 단위가 빠짐없이 선언됐는지 검사한다.",
        "explain": "농도·체중 등 모든 수치 열에 단위가 적혀 있는지, 몰↔질량 변환에 분자량(MW)이 필요한지 봐요. "
                   "단위 사전이 불완전하면 질문(Q10).",
        "input": "열별 단위 선언 정보",
        "output": "단위 선언 완전성 통과/실패",
    },
    "c0369": {
        "goal": "모든 시트가 빠짐없이 작업 공간에 불러와졌는지 검사한다.",
        "explain": "엑셀의 모든 시트(탭)가 다 로드됐는지 확인해요(누락되면 데이터가 통째로 빠질 수 있어서). "
                   "누락이면 질문(Q15A).",
        "input": "meta['sheet_inventory']",
        "output": "모든 시트 로드 확인",
    },
    # ── ROUTE (갈림길; 데이터 안 고치고 '어느 질문 Q로 보낼지'만 결정) ───────────
    "c0043": {
        "goal": "열 구조 검사 실패(c0001)를 알맞은 질문(Q)으로 보낸다.",
        "explain": "분석 목적이 안 정해졌으면 Q11, 정체불명 결함이면 Q15X, 핵심 열이 아예 없으면 되살리기 불가"
                   "(INVALID)로 보내요(고치지 않음).",
        "input": "c0001이 찾은 스키마(열 구조) 위반",
        "output": "보낼 질문(Q) 결정 (Q11/Q15X) 또는 INVALID",
    },
    "c0170": {
        "goal": "단위 관련 실패를 단위 사전 질문(Q10)으로 보낸다.",
        "explain": "분자량(MW)이 없어 몰↔질량 변환을 못 하는 등 단위 실패면 Q10으로 보내요.",
        "input": "c0160/c0161의 단위 위반",
        "output": "보낼 곳 결정 — Q10",
    },
    "c0251": {
        "goal": "시간(A3) 평가 실패를 알맞은 질문(Q)으로 보낸다.",
        "explain": "시간 해석이 모호(AMBIGUOUS)하면 Q02, 시간이 아예 되살릴 수 없으면 INVALID로 보내요.",
        "input": "A3 평가 결과(a3_state)",
        "output": "보낼 곳 결정 — Q02/Q12 또는 INVALID",
    },
    "c0252": {
        "goal": "투약 완전성(A4) 평가 실패를 알맞은 질문(Q)으로 보낸다.",
        "explain": "투약 기록·복원 규칙 없음→Q08, 반복 투여가 실제와 충돌→Q14, 주입 중단/재개 정책 없음→Q04, "
                   "핵심 정보 없음→INVALID.",
        "input": "A4 평가 결과(a4_state)",
        "output": "보낼 곳 결정 — Q04/Q08/Q14 또는 INVALID",
    },
    "c0253": {
        "goal": "관측/BLQ(A5) 평가 실패를 알맞은 질문(Q)으로 보낸다.",
        "explain": "BLQ(정량 하한 미만)·반복 처리 정책 없음→Q01, 여러 분석 결과 중 최종본 표시 없음→Q15D, "
                   "관측값 없음→INVALID.",
        "input": "A5 평가 결과(a5_state)",
        "output": "보낼 곳 결정 — Q01/Q15D 또는 INVALID",
    },
    "c0254": {
        "goal": "공변량(A7) 평가 실패를 알맞은 질문(Q)으로 보낸다.",
        "explain": "외부 공변량 표의 연결 키(공통 열)가 없으면 Q13, 결측 채우는 방법이 없으면 Q07로 보내요.",
        "input": "A7 평가 결과(a7_state)",
        "output": "보낼 곳 결정 — Q07/Q13",
    },
    "c0255": {
        "goal": "다약물/구획(A8) 평가 실패를 구획 질문(Q09)으로 보낸다.",
        "explain": "구획 번호(CMT) 배정 규칙이 없으면(CMT-POLICY-MISSING) Q09로 보내요.",
        "input": "A8 평가 결과(a8_state)",
        "output": "보낼 곳 결정 — Q09",
    },
    "c0256": {
        "goal": "결함 수리(A9) 평가 실패를 알맞은 질문(Q)으로 보낸다.",
        "explain": "프로토콜 위반 처리 규칙 없음→Q06, 재분석 최종본 표시 없음→Q15D, 무결성이 깨져 못 고침→INVALID.",
        "input": "A9 평가 결과(a9_state)",
        "output": "보낼 곳 결정 — Q06/Q15D 또는 INVALID",
    },
    "c0257": {
        "goal": "행 분류(A6) 평가 실패를 알맞은 질문(Q)으로 보낸다.",
        "explain": "행이 투약인지 관측인지 모호(AMBIGUOUS)하면 Q04로 보내요(회차 정의 모호는 Q03).",
        "input": "A6 평가 결과(a6_state)",
        "output": "보낼 곳 결정 — Q03/Q04",
    },
    "c0333": {
        "goal": "단위 선언 불완전(또는 분자량 없음)을 단위 사전 질문(Q10)으로 보낸다.",
        "explain": "단위가 빠졌거나 몰↔질량 변환에 필요한 분자량(MW)이 없으면 Q10으로 보내요.",
        "input": "단위 점검 결과",
        "output": "보낼 곳 결정 — Q10",
    },
    "c0499": {
        "goal": "어떤 처리로도 안 잡히는 정체불명 결함을 catch-all 질문(Q15X)으로 보낸다.",
        "explain": "감지·정규화 어디에도 안 걸리는 미분류 결함은 마지막으로 Q15X(모르는 결함 모음)로 보내요. "
                   "강한 페널티(점수 크게 깎임)가 붙습니다.",
        "input": "처리 안 된 결함 표시",
        "output": "보낼 곳 결정 — Q15X(catch-all, 페널티)",
    },
}

_AXIS_RE = re.compile(r"a(\d+)_state")
_ARROW_RE = re.compile(r"([A-Z][A-Z0-9\-]+)\s*→\s*(UNSUPPORTED|INVALID|Q\d+[A-Z]?)")


def _axis_of(raw: dict):
    """output_schema_delta의 '+meta[\'aN_state\']'에서 축 ID(A0..A10)를 추출(정본 파생)."""
    m = _AXIS_RE.search(raw.get("output_schema_delta", "") or "")
    return ("A" + m.group(1)) if m else None


def _easy_states(raw: dict, axis):
    """축(axis) 평가 c의 보기별 행선지(detect∪verify — c0200/c0204 등 verify-축 포함).
    종료 매핑은 정본 llm_prompt의 'STATE→TERMINAL' 화살표에서만 취득(날조 0)."""
    if not axis:
        return None
    tmap = dict(_ARROW_RE.findall(raw.get("llm_prompt", "") or ""))
    out = []
    for s in B.AXIS_STATES.get(axis, []):
        to = tmap.get(s)
        route = "go" if to is None else ("ask" if to.startswith("Q") else "stop")
        out.append({"code": s, "plain": GLOSSARY["state"].get(axis + "::" + s) or "",
                    "route": route, "to": to})
    return out


def _r_skeleton(raw: dict) -> str:
    """r_snippet 노출. detect의 미정의 helper 호출(예: detect_source_format)은 TODO 주석으로 전개."""
    r = raw.get("r_snippet", "") or ""
    if raw.get("kind") == "detect" and "<-" in r and "::" not in r and "(" in r:
        return ("# TODO: 아래 판별 로직(함수)을 직접 구현하세요 "
                "— ④의 🤖 요청문을 LLM에 주면 이 함수를 만들어 줍니다.\n" + r)
    return r


def _llm_request(raw: dict, seed: dict, states) -> str:
    """복사용 LLM 요청문 — 목표·입력·동작·보기·예시·출력계약·형식을 묶어 실행가능 R 산출을 유도."""
    action = " · ".join(_PLAIN_VOCAB.get(t, t) for t in str(raw.get("srp_intent", "")).split())
    ba = raw.get("before_after_toy_example") or {}
    lines = [
        "[목표] " + seed["goal"],
        "[내 데이터] " + seed["input"],
        "[해야 할 일] " + action + ".",
    ]
    if states:
        opts = "; ".join("%s = %s" % (s["code"], (s["plain"].split("→")[0].strip() or s["code"]))
                         for s in states)
        lines.append("[분류 보기] 아래 중 정확히 하나로 판정하고, 판별 규칙을 코드에 담아줘 — " + opts)
    cq = raw.get("can_route_to_q") or []
    if cq and not states:
        lines.append("[막히면 보낼 질문(Q)] 조건이 안 맞으면 " + ", ".join(cq)
                     + " 중 해당하는 질문으로 라우팅(routing=어디로 보낼지 결정)하도록 코드에 표시.")
    if ba.get("before"):
        lines.append("[예시] 입력 « %s » → 출력 « %s »"
                     % (str(ba.get("before", "")).replace("\n", " / "),
                        str(ba.get("after", "")).replace("\n", " / ")))
    lines.append("[결과(출력 계약)] " + seed["output"]
                 + ("; 표로 읽을 수 없으면 왜 안 되는지 사유 문자열도 함께 반환." if states else "."))
    lines.append("[형식] 위를 수행하는 ‘실행 가능한 R 스크립트’를 dplyr/tidyr로 작성해줘. "
                 "각 줄에 한국어 주석을 달고, 없는 값을 새로 지어내지 마(IMPUTE 금지). "
                 "도우미 함수가 필요하면 정의까지 포함해줘.")
    return "\n".join(lines)


def easy_card(raw: dict) -> dict:
    seed = _EASY_SEED[raw["c_id"]]
    axis = _axis_of(raw)
    states = _easy_states(raw, axis)
    vv = raw.get("verify_visualization") or {}
    return {
        "goal": seed["goal"], "explain": seed["explain"],
        "input": seed["input"], "output": seed["output"],
        "axis": axis, "states": states,
        "pass_to": vv.get("pass_route_to"), "fail_to": vv.get("fail_route_to"),
        "llm_request": _llm_request(raw, seed, states),
        "r_skeleton": _r_skeleton(raw),
    }


EASY = {cid: easy_card(_RAW[cid]) for cid in _EASY_SEED}


def _cunits_extra() -> dict:
    """B.CUNITS(트리-배선 57개)에 없는 c의 패널 렌더용 필드(정본 c_units.json 파생).
    → 전체 122 c의 쉬운 카드를 그래프 배선과 무관하게 열람 가능(report-only, spec 무수정)."""
    have = set(B.CUNITS)
    out = {}
    for cid, raw in _RAW.items():
        if cid in have:
            continue
        ba = raw.get("before_after_toy_example") or {}
        out[cid] = {
            "c_id": cid, "c_name_ko": raw.get("c_name_ko"), "srp_intent": raw.get("srp_intent"),
            "kind": raw.get("kind"), "cost": raw.get("cost"), "layer_pair": raw.get("layer_pair"),
            "requires_detection_by": raw.get("requires_detection_by"), "ref": raw.get("ref"),
            "llm_prompt": raw.get("llm_prompt"),
            "precondition_checklist_ko": raw.get("precondition_checklist_ko") or [],
            "r_snippet": raw.get("r_snippet"), "python_snippet": raw.get("python_snippet"),
            "verify_visualization": raw.get("verify_visualization"),
            "can_route_to_q": raw.get("can_route_to_q") or [],
            "before": ba.get("before"), "after": ba.get("after"), "fam": raw.get("fam"),
        }
    return out


CUNITS_EXTRA = _cunits_extra()


def assert_glossary_complete():
    """ELES/CUNITS/QINFO/AXIS_STATES에 등장하는 모든 코드가 쉬운 말을 갖는지 검사(누락 시 빌드 실패)."""
    g = GLOSSARY
    missing = []

    def need(cat, key):
        if key not in g[cat] or not g[cat][key]:
            missing.append((cat, key))

    for cid, c in B.CUNITS.items():
        need("kind", c["kind"])
        if c["layer_pair"]:
            need("layer", c["layer_pair"])
        for tok in str(c["srp_intent"]).split():
            need("vocab", tok)
    for q in B.Q_IDS:
        need("qcode", q)
    for ax in B.AXIS_IDS:
        need("axis", ax)
        for s in B.AXIS_STATES.get(ax, []):
            need("state", ax + "::" + s)
    for n in B.BRANCH_IDS:
        need("node", n)
    for t in B.PROC_IDS:
        need("terminal", t)

    miss = sorted(set(missing))
    if miss:
        raise SystemExit("[build_html_v2] 용어집 미완 — 다음 항목에 쉬운 말이 없습니다:\n  "
                         + "\n  ".join("%s: %s" % (k, v) for k, v in miss))
    return True


# ═════════════════════════════════════════════════════════════════════════════
# 3. 색 교체 + PAGE_HEAD(쉬운 말·진단 버튼·추가 CSS)
# ═════════════════════════════════════════════════════════════════════════════
AMBER = "#E8820C"       # 기본 자동경로(실선) — 진한 앰버(원래 #FFD700)
TEAL = "#15B4C7"        # 질문 갈림길(점선, 하이라이트) — 청록(원래 #FFF8B0)
TEAL_DEEP = "#0E8A99"   # 질문 갈림길(점선, resting) — 딥 틸(원래 #c9920e)


def recolor(s: str) -> str:
    return s.replace("#FFD700", AMBER).replace("#FFF8B0", TEAL).replace("#c9920e", TEAL_DEEP)


_EXTRA_CSS = """
  /* ── index v2 추가 스타일(쉬운 말 배지·툴팁·진단 마법사) ── */
  .codechip{display:inline-block;font-family:Consolas,monospace;font-size:10px;color:#5a6b7a;background:#eef2f7;
            border:1px solid #d7dde3;border-radius:4px;padding:0 4px;margin-left:3px;cursor:help;vertical-align:middle}
  .muted{color:#8a97aa}
  .big{font-size:14px;font-weight:700;margin:1px 0 6px;color:#16314f}
  [data-tip]{position:relative}
  [data-tip]:hover::after{content:attr(data-tip);position:absolute;left:0;top:128%;z-index:10000;
     background:#1c2733;color:#fff;font-size:11px;font-weight:400;line-height:1.45;padding:6px 9px;border-radius:6px;
     width:max-content;max-width:300px;white-space:normal;box-shadow:0 3px 12px rgba(0,0,0,.28);pointer-events:none}
  .colornote{font-size:11px;color:#46535f;background:#f3f8fb;border:1px solid #d7e6ee;border-radius:6px;
     padding:6px 9px;margin-bottom:9px;line-height:1.55}
  .colornote b.amb{color:#E8820C} .colornote b.tl{color:#0E8A99}
  /* 진단 마법사 모달 */
  #wizMask,#glossMask{display:none;position:fixed;inset:0;background:rgba(20,30,40,.42);z-index:2000}
  #wizMask.on,#glossMask.on{display:flex;align-items:center;justify-content:center}
  #wizBox,#glossBox{background:#fff;border-radius:12px;max-width:700px;width:92%;max-height:88vh;overflow:auto;
     box-shadow:0 14px 44px rgba(0,0,0,.32)}
  #wizBox h2,#glossBox h2{font-size:15px;margin:0;padding:12px 16px;border-bottom:1px solid var(--line);
     display:flex;justify-content:space-between;align-items:center;background:#fafbfc;position:sticky;top:0}
  #wizBody,#glossBody{padding:13px 16px}
  .wq{margin:9px 0;padding:9px 11px;border:1px solid var(--line);border-radius:8px;background:#fafbfc}
  .wq .q{font-size:13px;font-weight:600;margin-bottom:6px;line-height:1.5}
  .wq label{font-size:12px;margin-right:16px;cursor:pointer}
  .wizact{display:flex;gap:8px;margin-top:13px;flex-wrap:wrap}
  #wizResult{margin-top:14px}
  .rescard{border:1px solid var(--line);border-radius:8px;padding:11px 13px;margin:9px 0;font-size:13px;line-height:1.65}
  .rescard.ok{background:#edf7ee;border-color:#bcdfc0}
  .rescard.stop{background:#fff4ec;border-color:#f0c9a8}
  .rescard h4{margin:0 0 6px;font-size:13.5px}
  .cchip{display:inline-block;font-family:Consolas,monospace;font-size:11px;background:#eaf1fb;border:1px solid #bcd2f0;
         border-radius:5px;padding:1px 6px;margin:2px;cursor:pointer;color:#1b4f8a}
  .cchip:hover{background:#d7e6fb}
  .gloss-sec{margin:10px 0}
  .gloss-sec h3{font-size:12.5px;margin:0 0 5px;color:#3a4651;border-bottom:1px solid var(--line);padding-bottom:3px}
  .gloss-row{font-size:12px;margin:3px 0;line-height:1.5}
  .gloss-row .gc{font-family:Consolas,monospace;font-size:11px;color:#1b4f8a;background:#eaf1fb;border-radius:4px;padding:0 5px;margin-right:6px}
  /* 쉬운 카드(EASY) + 궤도복귀/경로 breadcrumb */
  .easygoal{font-size:13.5px;font-weight:700;color:#16314f;background:#fff7ec;border:1px solid #f0d6ad;border-radius:6px;padding:7px 9px;margin-bottom:6px;line-height:1.5}
  .easyexp{font-size:12.5px;color:#3a4651;line-height:1.7;margin-bottom:7px}
  .straw{font-size:12px;line-height:1.7;padding:3px 0;border-bottom:1px dashed #eef2f7}
  .termstop{display:inline-block;font-size:11px;color:#455a64;background:#eceff1;border:1px solid #b0bec5;border-radius:5px;padding:0 6px;cursor:help}
  .llmreq{white-space:pre-wrap;background:#f7faff;border:1px solid #cfe0f5;border-radius:7px;padding:10px 11px;font-size:12px;line-height:1.65;color:#1f3550;font-family:Consolas,monospace;margin-top:6px}
  .copybtn{font-size:11px;padding:2px 8px;margin-bottom:2px}
  .rescard.onramp{background:#eef6ff;border-color:#bcd6f0}
  .rescard .step{margin-top:9px;padding:8px 10px;background:#fff;border:1px solid var(--line);border-radius:7px;font-size:12.5px;line-height:1.65}
  .rescard .manual{font-size:11px;color:#b3541e;background:#fff1e6;border:1px solid #f0c9a8;border-radius:5px;padding:1px 6px;margin-left:4px}
  .breadcrumb{margin:7px 0;padding:7px 9px;background:#fffaf2;border:1px solid #f0dcc0;border-radius:7px;font-size:12px;line-height:2.1}
  .breadcrumb.dotted{background:#f4f8fc;border-style:dashed;border-color:#bcd2f0}
  .pnode{display:inline-block;font-weight:700;font-size:11px;border-radius:5px;padding:1px 7px}
  .pnode.start{background:#ffe1a8;color:#7a4b00}
  .pnode.goal{background:#43a047;color:#fff}
  .parrow{color:#E8820C;font-weight:700}
  .parrow.d{color:#7d9bbb}
  /* attach 가이드(마법사 상단) */
  .attachguide{border:1px solid #cfe0f5;border-radius:8px;background:#f6faff;margin-bottom:11px;padding:1px 4px}
  .attachguide>summary{cursor:pointer;font-size:12.5px;font-weight:700;color:#16314f;padding:8px}
  .agbody{font-size:12px;line-height:1.7;color:#33404d;padding:2px 10px 9px}
  .agsteps{margin:7px 0 0;padding-left:18px}
  .agsteps li{margin:5px 0}
  .agmanual{color:#b3541e;background:#fff1e6;border:1px solid #f0c9a8;border-radius:5px;padding:1px 5px;font-size:11px}
  .agflow{margin:6px 0 2px;display:flex;flex-wrap:wrap;align-items:center;gap:3px}
  .agn{display:inline-block;font-size:11px;background:#fff;border:1px solid #d7e6ee;border-radius:5px;padding:1px 6px;cursor:help}
  .agar{color:#E8820C;font-weight:700;margin:0 1px}
  /* 전체 작업 카드(122) 목록 모달 */
  #cardMask{display:none;position:fixed;inset:0;background:rgba(20,30,40,.42);z-index:2000}
  #cardMask.on{display:flex;align-items:center;justify-content:center}
  #cardBox{background:#fff;border-radius:12px;width:94%;max-width:1040px;height:86vh;display:flex;flex-direction:column;
     box-shadow:0 14px 44px rgba(0,0,0,.32);overflow:hidden}
  #cardBox>h2{font-size:15px;margin:0;padding:12px 16px;border-bottom:1px solid var(--line);display:flex;
     justify-content:space-between;align-items:center;background:#fafbfc}
  #cardWrap{display:flex;flex:1;min-height:0}
  #cardList{width:330px;border-right:1px solid var(--line);overflow:auto;padding:8px}
  #cardSearch{width:100%;box-sizing:border-box;padding:6px 8px;font-size:12px;border:1px solid var(--line);border-radius:6px;margin-bottom:6px}
  #cardRows .clgrp h4{font-size:11.5px;color:#3a4651;margin:9px 2px 3px;border-bottom:1px solid var(--line);padding-bottom:2px}
  .clrow{font-size:12px;padding:4px 6px;border-radius:5px;cursor:pointer;line-height:1.45}
  .clrow:hover{background:#eef6ff}
  .clrow.sel{background:#dcebff}
  .clcode{font-family:Consolas,monospace;font-size:11px;color:#1b4f8a;background:#eaf1fb;border-radius:4px;padding:0 4px}
  .clkind{font-size:10px;color:#8a97aa}
  #cardDetail{flex:1;overflow:auto;padding:12px 14px}
"""


def page_head_v2() -> str:
    ph = recolor(B.PAGE_HEAD)
    ph = ph.replace("<title>pmx-dt · NONMEM-ready decision tree (Phase 8 · 전체 tree)</title>",
                    "<title>pmx-dt · 쉬운 설명 뷰 (index v2)</title>")
    ph = ph.replace("<h1>pmx-dt · decision tree</h1>",
                    '<h1>pmx-dt · 쉬운 설명 뷰 <span style="font-weight:400;color:#8a97aa;font-size:11px">(index v2)</span></h1>')
    ph = ph.replace("NONMEM-ready data wrangling · 전체 tree (Phase 8)",
                    "raw 데이터 → NONMEM-ready 정리 지도 · 클릭하면 쉬운 말로 설명")
    # 토프바에 진단/용어집 버튼 추가(선택 해제 버튼 앞)
    ph = ph.replace(
        '<button class="btn" id="clearSel" type="button">선택 해제</button>',
        '<button class="btn" id="wizardBtn" type="button" style="background:#e8f4ff;border-color:#9cc6f0;font-weight:700">🔍 내 파일 진단</button>\n'
        '  <button class="btn" id="glossBtn" type="button" style="background:#f1f0fb;border-color:#cfc8ee">📖 용어집</button>\n'
        '  <button class="btn" id="cardBtn" type="button" style="background:#eafaf1;border-color:#a8dcc0;font-weight:700">📋 작업 카드 122</button>\n'
        '  <button class="btn" id="clearSel" type="button">선택 해제</button>')
    # 안내 기본 문구(쉬운 말)
    ph = ph.replace("노드를 클릭하면 경로(N0→현재)가 표시됩니다.",
                    "점(작업)을 클릭하면 그 일이 무엇인지 + 끝까지 가는 길이 색으로 표시됩니다. 처음이면 “🔍 내 파일 진단”부터.")
    ph = ph.replace("</style>", _EXTRA_CSS + "\n</style>")
    return ph


# ═════════════════════════════════════════════════════════════════════════════
# 4. APP_JS 오버라이드 — 쉬운 말 패널 재작성 + 색 안내 + 진단 마법사 + 용어집
#    (build_html.py의 함수들을 window.* 재할당으로 교체. 데이터는 전부 전역 globals 참조.)
# ═════════════════════════════════════════════════════════════════════════════
_V2_OVERRIDE = r'''<script>
"use strict";
/* ===== index v2 override: 쉬운 말 패널 + 색 안내 + 진단 마법사 + 용어집 ===== */
(function(){
  function E(s){ return esc(s); }
  function sect(title, body){ return '<div class="sect"><h3>'+title+'</h3><div class="body">'+body+'</div></div>'; }
  function kv(k, v){ return '<div class="kv"><span class="k">'+k+'</span> · '+v+'</div>'; }
  function gloss(cat, code){ var m=(GLOSSARY[cat]||{}); return m[code]||""; }
  function plainSrp(srp){
    var voc=GLOSSARY.vocab||{};
    return String(srp||"").split(/\s+/).filter(Boolean).map(function(t){ return voc[t]||t; }).join(" · ");
  }
  function chip(code, cat){
    var tip;
    if(cat==="srp") tip=plainSrp(code);
    else if(cat==="c") tip=((CUNITS[code]||CUNITS_EXTRA[code]||{}).c_name_ko)||code;
    else tip=gloss(cat, code);
    return '<span class="codechip" data-tip="'+E(tip||code)+'">'+E(code)+'</span>';
  }
  function qChip(q){ return '<span class="pill q codechip" data-tip="'+E(gloss("qcode",q)||q)+'">'+E(q)+'</span>'; }
  function stateChip(ax, s){ return '<span class="pill codechip" data-tip="'+E(gloss("state", ax+"::"+s)||s)+'">'+E(s)+'</span>'; }
  /* onward 라우팅 해소(모든 노드): 통과=c칩/친절문구 · 막힘=질문(Q) vs ✋정당한 종료 구분 */
  function isCid(x){ return /^c\d{4}$/.test(String(x||"")); }
  function isQc(x){ return /^Q\d+[A-Z]?$/.test(String(x||"")); }
  function passChip(p){
    if(!p) return '<span class="pill pass">다음 작업으로 계속</span>';
    if(isCid(p)) return '<span class="pill pass">→</span> '+chip(p,"c");
    if(String(p)==="next axis") return '<span class="pill pass">다음 축 평가로 계속 → 🏁</span>';
    return '<span class="pill pass">'+E(p)+'</span>';
  }
  function failChip(f){
    if(!f) return '<span class="pill">없음(이 작업은 막히지 않음)</span>';
    if(isQc(f)) return qChip(f);
    return '<span class="termstop" data-tip="자동 처리 대상이 아니라 여기서 정직하게 종료합니다(결함이 아니라 정당한 종료).">✋ 정당한 종료 · '+E(f)+'</span>';
  }
  function colorNote(){
    return '<div class="colornote">길 색 안내 — <b class="amb">굵은 앰버 실선</b> = 자동으로 흘러가는 <b>기본 경로</b>(사람 손 불필요) · '
         + '<b class="tl">청록 점선</b> = 여기서 문제가 있으면 <b>‘사람이 결정해야 하는 질문(Q)’</b>으로 빠지는 갈림길.</div>';
  }
  window.__v2_colorNote = colorNote;

  /* ---- (c 패널) 변환/감지/검사/분기 — 쉬운 말 4섹션 ---- */
  window.renderCPanel = function(id){
    var c=CUNITS[id]||(window.CUNITS_EXTRA&&CUNITS_EXTRA[id]); if(!c) return window.renderNodePanel(id,"node");
    if(window.EASY && EASY[id]) return renderEasyCPanel(id, c, EASY[id]);
    var h=colorNote();
    var chk=(c.precondition_checklist_ko||[]).map(function(t,i){
      return '<li><input type="checkbox" class="ckbox" data-i="'+i+'" id="ck'+i+'"><label for="ck'+i+'">'+E(t)+'</label></li>';
    }).join("");
    h+=sect("① 시작 전 — 내 데이터가 이 작업을 받을 준비가 됐는지 확인",
            '<ul class="chklist" id="chk">'+chk+'</ul><div class="badge-ok" id="chkbadge">✓ 위치 확인됨</div>');
    var b="";
    b+=kv("이름", "<b>"+E(c.c_name_ko)+"</b>");
    b+=kv("하는 일", plainSrp(c.srp_intent)+" "+chip(c.srp_intent,"srp"));
    b+=kv("작업 종류", E(gloss("kind",c.kind))+" "+chip(c.kind,"kind"));
    b+=kv("드는 품(비용)", String(c.cost));
    b+=kv("정리 단계", E(gloss("layer",c.layer_pair))+" "+chip(c.layer_pair,"layer"));
    b+=kv("먼저 끝나야 할 작업", c.requires_detection_by
            ? (chip(c.requires_detection_by,"c")+' <span class="muted">(이 감지가 선행되어야 함)</span>')
            : '<span class="muted">없음(바로 시작 가능)</span>');
    b+=kv("영향 받는 시나리오", "<b>"+c.influence+"</b>개 경로");
    b+='<div class="snlabel">이 작업을 시키는 지시문(사람/LLM용)</div><div class="prompt">'+E(c.llm_prompt)+'</div>';
    b+=kv("원래 코드", chip(c.c_id,"c")+' · <span class="muted">근거</span> '+E(c.ref));
    h+=sect("② 이 작업이 무슨 일을 하나", b);
    if(c.kind==="transform"){
      h+=sect("③ 고치기 전 / 후 — 앰버 칸이 바뀐 부분", renderBeforeAfter(c.before,c.after));
    }else{
      h+=sect("③ 무엇을 검사하고, 통과하면 어디로 · 막히면 어디로", window.renderVV(c.verify_visualization,c.can_route_to_q));
    }
    h+=sect("④ 실제 코드 예시 (위 R · 아래 Python)",
            '<div class="snlabel">R</div><pre class="snip">'+hlComments(c.r_snippet)+'</pre>'
            +'<div class="snlabel">Python</div><pre class="snip">'+hlComments(c.python_snippet)+'</pre>');
    return h;
  };

  window.renderVV = function(vv, canQ){
    if(!vv){
      var q=(canQ||[]);
      return '<div class="muted">이 작업은 ‘검사’가 아니라 변환/분기라 검사 장면이 없습니다.</div>'
        + (q.length ? kv("막히면 갈 수 있는 질문", q.map(qChip).join(" "))
                    : kv("다음", '<span class="pill pass">정리 후 다음 작업으로 계속 → 🏁</span>'));
    }
    var h=kv("검사 대상 열", (vv.target_columns||[]).map(function(x){return '<span class="pill">'+E(x)+'</span>';}).join(" "));
    h+=kv("합격 기준", E(vv.criterion_predicate_ko));
    h+=kv("통과하면 →", passChip(vv.pass_route_to));
    h+=kv("막히면(실패) →", failChip(vv.fail_route_to));
    return h;
  };

  /* ---- (쉬운 카드) 파일럿 c — 🎯목표/🧩설명/보기 행선지/🤖요청문/R 골격 ---- */
  function renderEasyCPanel(id, c, ez){
    var h=colorNote();
    var chk=(c.precondition_checklist_ko||[]).map(function(t,i){
      return '<li><input type="checkbox" class="ckbox" data-i="'+i+'" id="ck'+i+'"><label for="ck'+i+'">'+E(t)+'</label></li>';
    }).join("");
    h+=sect("① 시작 전 — 내 데이터가 이 작업을 받을 준비가 됐는지 확인",
            '<ul class="chklist" id="chk">'+chk+'</ul><div class="badge-ok" id="chkbadge">✓ 위치 확인됨</div>');
    var b='<div class="easygoal">🎯 '+E(ez.goal)+'</div>';
    b+='<div class="easyexp">🧩 '+E(ez.explain)+'</div>';
    b+=kv("📥 들어오는 것(입력)", E(ez.input));
    b+=kv("📤 나가는 것(출력)", E(ez.output));
    b+=kv("작업 종류", E(gloss("kind",c.kind))+" "+chip(c.kind,"kind"));
    b+=kv("원래 코드", chip(c.c_id,"c")+' · <span class="muted">근거</span> '+E(c.ref));
    h+=sect("② 이 작업이 무슨 일을 하나 (쉬운 말)", b);
    if(ez.states){
      var rows=ez.states.map(function(s){
        var rt = (s.route==="go") ? '<span class="pill pass">→ 계속</span>'
               : (s.route==="ask") ? ('→ '+qChip(s.to))
               : ('<span class="termstop">✋ 정당한 종료 · '+E(s.to)+'</span>');
        return '<div class="straw">'+stateChip(ez.axis,s.code)+' <span class="muted">'+E(s.plain||"")+'</span> '+rt+'</div>';
      }).join("");
      h+=sect("③ 보기 — 내 파일이 어디에 해당하고, 그러면 어디로 가나",
              rows+'<div style="margin-top:7px">'+kv("통과하면 →", passChip(ez.pass_to))+kv("막히면 →", failChip(ez.fail_to))+'</div>');
    }else if(c.kind==="transform"){
      h+=sect("③ 고치기 전 / 후 — 앰버 칸이 바뀐 부분", renderBeforeAfter(c.before,c.after));
    }else{
      h+=sect("③ 무엇을 검사/분기하고, 통과하면 어디로 · 막히면 어디로",
              window.renderVV(c.verify_visualization, c.can_route_to_q));
    }
    h+=sect("④ 🤖 LLM에게 이대로 복사해 요청하세요 — 이 작업에 맞는 R 스크립트를 만들어 줍니다",
            '<button class="btn copybtn" data-copy="llmreq_'+E(id)+'">📋 복사</button>'
            +'<pre class="llmreq" id="llmreq_'+E(id)+'">'+E(ez.llm_request)+'</pre>');
    h+=sect("⑤ 참고 코드 골격 (위 요청문으로 받은 R을 검증·비교할 때 — 위 R · 아래 Python)",
            '<div class="snlabel">R</div><pre class="snip">'+hlComments(ez.r_skeleton)+'</pre>'
            +'<div class="snlabel">Python</div><pre class="snip">'+hlComments(c.python_snippet)+'</pre>');
    return h;
  }

  /* ---- (Q 패널) 질문(Q-code) — 쉬운 말 ---- */
  window.renderQPanel = function(id){
    var q=QINFO[id]; if(!q) return window.renderTerminalPanel(id);
    var defer=(q.q_status==="unreached");
    var h=colorNote();
    h+=sect("이 질문은? "+chip(id,"qcode")+(defer?' <span class="deferbadge">아직 연결 안 됨</span>':''),
            '<div class="big">'+E(gloss("qcode",id)||q.name)+'</div>'
            + kv("원래 이름", E(q.name))
            + kv("언제 생기나(조건)", E(q.trigger_condition)));
    var reach;
    if(defer){
      reach='<div class="muted">아직 이 질문으로 가는 작업이 연결되지 않은 자리표시입니다(후속 작업).</div>';
    }else if(q.reach && q.reach.length){
      reach=q.reach.map(function(r){
        return '<div class="reachrow">'+chip(r.from,"c")+' <span class="muted">('+E(gloss("kind",r.from_kind)||r.from_kind)+')</span> → '+E(id)+' · 시나리오 '+r.strand_count+'</div>';
      }).join("");
    }else{
      reach='<div class="kv">연결된 작업: '+(q.incoming_wired_c||[]).map(function(x){return chip(x,"c");}).join(" ")+'</div>';
    }
    h+=sect("① 어떻게 여기로 오나 — 어떤 작업에서 이 질문으로 빠지는지", reach
            + kv("이 질문이 영향 주는 시나리오", "<b>"+q.influence+"</b>개"));
    var clar=(q.clarification_to_sponsor||[]).map(function(t){return '<li>'+E(t)+'</li>';}).join("");
    h+=sect("② 스폰서/데이터 주인에게 물어볼 것", '<ul style="margin:0;padding-left:18px;font-size:13px;line-height:1.6">'+clar+'</ul>');
    h+=sect("③ 사람이 내려야 할 결정", E(q.human_decision_point)
            + kv("드는 비용/노력", "비용 "+q.routing_cost+" · 노력 "+E(q.human_effort_score)+"/10"));
    var rec=q.recover_to_c_id, recWired=(rec && CUNITS[rec]);
    var rh='답을 받은 뒤 돌아오는 지점: <b>'+E(rec||"—")+'</b>';
    if(defer){
      rh+='<div class="kv muted">이 질문은 아직 미연결이라 복귀선도 생략됩니다.</div>';
    }else if(recWired){
      rh+=' <button class="btn" id="recoverBtn" data-to="'+E(rec)+'">↩ '+E(rec)+' 로 돌아가기</button>';
      rh+='<div class="kv" style="color:#1565c0">트리에 ↩ 파랑 점선으로 표시 — <b>자동이 아니라</b> 사람이 답한 뒤 다시 들어가는 길입니다.</div>';
    }else{
      rh+='<div class="kv" style="color:#b35a16">복귀 지점 '+E(rec)+' 는 아직 구현 범위 밖이라 선은 생략(숨김 0).</div>';
    }
    h+=sect("④ 답을 받은 뒤 어디로 돌아오나 (사람 개입 후)", rh);
    return h;
  };

  /* ---- (노드 패널) 관문 N/축 A/stage/state — 쉬운 말 ---- */
  window.renderNodePanel = function(id, kind){
    var info=NODEINFO[id];
    if(kind==="state"){
      var p=id.split("::"), ax=p[0], s=p[1]||id, pl=gloss("state", id);
      return colorNote()+sect("이 칸은? "+chip(ax,"axis")+" 의 상태 · "+E(s),
        (pl?'<div class="big">'+E(pl)+'</div>':'')
        +'이 칸을 지나는 시나리오는 '+E(ax)+' 축에서 <b>'+E(s)+'</b>로 분류됩니다.');
    }
    if(kind==="stage"){
      return colorNote()+sect("정규화 stage란?",
        '글자·인코딩·셀 같은 ‘가장 바닥’을 정리하는 묶음 단계입니다. 묶인 개별 작업(c)은 따로 점으로 보입니다.')
        +sect("참고", '묶음 노드화는 후속 결정 대기(GAP-27B). 지금은 개별 c로 표시합니다.');
    }
    if(!info) return sect("노드", E(id));
    var isAxis=(kind==="axis");
    var pl=isAxis?gloss("axis",id):gloss("node",id);
    var h=colorNote();
    h+=sect("역할 "+chip(id, isAxis?"axis":"node"),
        (pl?'<div class="big">'+E(pl)+'</div>':'')+E(info.role)+(info.ref?kv("근거",E(info.ref)):''));
    var bm=E(info.bm);
    if(info.states){
      bm+='<div class="navrow">'+info.states.map(function(s){return stateChip(id,s);}).join("")+'</div>';
      bm+='<button class="btn" id="axisToggle" data-ax="'+E(id)+'">'+(state.expandedAxes.indexOf(id)>=0?"▲ 상태 접기":"▼ 상태 펼치기")+'</button>';
    }
    h+=sect(isAxis?"어떤 상태로 갈라지나":"여기서 갈라지는/합쳐지는 방식", bm);
    h+=sect("영향 받는 시나리오 수", "<b>"+info.strands+"</b>개 경로");
    return h;
  };

  window.renderTerminalPanel = function(id){
    var info=NODEINFO[id]||{role:"종착", bm:"", strands:"—"};
    var pl=gloss("terminal",id);
    return colorNote()+sect("종착점 "+chip(id,"terminal"),
        (pl?'<div class="big">'+E(pl)+'</div>':'')+E(info.role)+(info.ref?kv("근거",E(info.ref)):''))
      +sect("영향 받는 시나리오 수","<b>"+info.strands+"</b>개 경로");
  };

  /* ===== 진단 마법사(src/adapter 1:1 미러) ===== */
  var WQ=[
    {k:"tidy", q:"1) 농도(concentration) 데이터 시트가 <b>1행=헤더</b>이고, 그 헤더에 <b>시간 열</b>과 <b>농도 열</b>이 둘 다 있는 <b>깔끔한 표</b>(검량/QA 행이 안 섞임)인가요?"},
    {k:"qa", q:"2) 그 시트 <b>맨 왼쪽 첫 열</b>에 Standard · DBLK · BLK · QC · Calibration · Blank 같은 <b>검량/QA 행</b>이 실제 샘플과 섞여 있나요?"},
    {k:"param", q:"3) 그 표가 농도 원자료가 아니라 Cmax · AUC 같은 <b>‘파라미터 요약’</b>(열에 Parameters · Unit, 값은 Mean)인가요?"},
    {k:"subject_wide", q:"4) 농도가 <b>‘시간=행, 동물/사람=열’</b>(예: Time, Animal1, Animal2 …)로 옆으로 펼쳐져 있나요?"},
    {k:"has_subject", q:"5) 그 표에 <b>개체(사람/동물) 번호 열</b>(subject / animal / ID 등)이 있나요?"},
    {k:"multi_or_merged", q:"6) 엑셀에 <b>시트가 2개 이상</b>이거나 <b>병합된 셀</b>이 있나요?"},
    {k:"non_ascii", q:"7) 시트 이름이나 셀에 <b>한글/특수문자</b>가 있나요?"},
    {k:"unit_col", q:"8) 단위가 <b>별도 ‘Unit’ 열</b>로 들어 있나요?"},
    {k:"blq", q:"9) 농도 칸에 <b>‘BLQ’ · ‘&lt;LLOQ’ · ‘ND’</b> 같은 토큰이 단독으로 들어 있나요?"},
    {k:"bw_sheet", q:"10) <b>체중(BW / body weight / 체중)</b> 정보가 <b>별도 시트</b>로 있나요?"}
  ];
  function wizardVerdict(a){
    var faithful=!!a.tidy;
    var chosen={};
    WIZARD.file_property_c.forEach(function(c){ chosen[c]=1; });
    if(faithful){
      WIZARD.data_dependent_c.forEach(function(c){
        var req=WIZARD.precond[c];
        var ok=(req==="none")||(req==="time")||(req==="dv")||(req==="subject+time+dv" && !!a.has_subject);
        if(ok) chosen[c]=1;
      });
    }
    var cseq=WIZARD.canon_order.filter(function(c){ return chosen[c]; });
    var qset={};
    cseq.forEach(function(c){ ((CUNITS[c]||{}).can_route_to_q||[]).forEach(function(q){ qset[q]=1; }); });
    return {faithful:faithful, entry:"N0", c_sequence:cseq, qcodes:Object.keys(qset), honest_stop:!faithful};
  }
  /* 표가 tidy가 됐다고 가정했을 때의 경로(=궤도 복귀 후 '예상 경로'). wizardVerdict의 faithful 분기와 동일 규칙. */
  function projectedFaithfulSeq(a){
    var chosen={};
    WIZARD.file_property_c.forEach(function(c){ chosen[c]=1; });
    WIZARD.data_dependent_c.forEach(function(c){
      var req=WIZARD.precond[c];
      var ok=(req==="none")||(req==="time")||(req==="dv")||(req==="subject+time+dv" && !!a.has_subject);
      if(ok) chosen[c]=1;
    });
    return WIZARD.canon_order.filter(function(c){ return chosen[c]; });
  }
  /* 출발점 N0 → c들 → 🏁 nonmem-ready 까지의 경로를 한 줄로. dotted=true 면 '예상 경로'(점선). */
  function pathBreadcrumb(seq, dotted){
    var arrow=dotted?' <span class="parrow d">⇢</span> ':' <span class="parrow">→</span> ';
    var parts=['<span class="pnode start">N0</span>'];
    (seq||[]).forEach(function(c){ parts.push('<span class="cchip" data-node="'+E(c)+'">'+E(c)+'</span>'); });
    parts.push('<span class="pnode goal">🏁 nonmem-ready</span>');
    return '<div class="breadcrumb'+(dotted?' dotted':'')+'">'+parts.join(arrow)+'</div>';
  }
  /* 골격 attach → nonmem-ready 가이드 (정직한 5단계, 쉬운 말) */
  function attachGuide(){
    var flow=[
      ["N0","분석 목적 정해짐?"],["N1","개체(사람/동물) 번호 만들기"],["N2","사건을 시간순으로 줄세우기"],
      ["N3","투약 기록 완성"],["N4","관측 기록 완성"],["N5","BLQ(정량 하한 미만)·결측 처리"],
      ["N6","공변량(체중·나이 등 부가정보) 붙이기"],["N7","남은 모호함 점검"]
    ];
    var chips=flow.map(function(x){
      return '<span class="agn" data-tip="'+E(gloss("node",x[0])||"")+'"><b>'+x[0]+'</b> '+E(x[1])+'</span>';
    }).join('<span class="agar">→</span>');
    return '<details class="attachguide" open><summary>📍 이 진단은 어떻게 <b>🏁 nonmem-ready</b>까지 안내하나? (눌러서 펼치기/접기)</summary>'
      +'<div class="agbody">'
      +'<div>이 그림은 <b>‘엉망인 raw(원본) 데이터 → NONMEM 분석용 깔끔한 데이터(🏁 nonmem-ready)’</b>까지 가는 <b>지도</b>예요. 길은 이렇게 이어집니다:</div>'
      +'<ol class="agsteps">'
      +'<li><b>출발</b> — 내 raw 파일(보통 엉망: 여러 시트·병합 셀·BLQ 표기 등).</li>'
      +'<li><b>표 모양 정리(필요할 때만)</b> — 깔끔한 <b>tidy 표(한 줄 = 한 측정)</b>가 아니면 먼저 모양을 정리해요 '
      +'(검량/QA 행 제거 · 가로→세로 피벗(PIVOT=모양 바꾸기) · 시트 합치기(조인=JOIN)). '
      +'<span class="agmanual">⚠️ 이 정리는 아직 도구가 자동으로 못 해서, 당신이나 LLM이 먼저 합니다(GAP-37).</span></li>'
      +'<li><b>골격에 ‘붙기(attach)’</b> — tidy 표가 되면, 각 정리·검사 작업이 아래 <b>관문(N0~N7)</b> 골격의 제자리에 붙어요. '
      +'<span class="muted">(attach=지도에서 ‘이 작업이 어느 관문에서 일어나는지’ 표시)</span></li>'
      +'<li><b>관문을 차례로 통과 + 축(A0~A10) 평가</b>:<div class="agflow">'+chips
      +' <span class="agar">→</span> <span class="pnode goal">🏁 nonmem-ready</span></div></li>'
      +'<li><b>도착 또는 갈림</b> — 다 통과하면 <b>🏁 nonmem-ready</b>(L0=분석 준비 끝). 막히면 '
      +'<span class="termstop">✋ 정당한 종료</span>(예: 표가 아니거나 파일 손상) 또는 ❓ <b>질문 Q</b>(사람이 정책을 정해야 함)로 갈려요. '
      +'<b>어느 쪽이든 ‘다음에 뭘 할지’를 알려주니 막다른 길이 아닙니다.</b></li>'
      +'</ol></div></details>';
  }
  function buildWizard(){
    var mask=document.createElement("div"); mask.id="wizMask";
    var qhtml=WQ.map(function(w){
      return '<div class="wq"><div class="q">'+w.q+'</div>'
        +'<label><input type="radio" name="wq_'+w.k+'" value="y"> 예</label>'
        +'<label><input type="radio" name="wq_'+w.k+'" value="n" checked> 아니오</label></div>';
    }).join("");
    mask.innerHTML='<div id="wizBox"><h2>🔍 내 파일 진단 — 어디서 시작할까요?'
      +'<button class="btn" id="wizClose">×</button></h2><div id="wizBody">'
      +'<div class="muted" style="font-size:12px;margin-bottom:8px">파일을 올리지 않습니다. 아래 질문에 답하면, 정본 Python 어댑터(<span class="mono">src/adapter</span>)와 <b>똑같은 규칙</b>으로 시작 지점을 알려줍니다. (1번이 ‘예’이면 2~4번은 보통 ‘아니오’ — 한 시트는 한 종류)</div>'
      +attachGuide()
      +qhtml
      +'<div class="wizact"><button class="btn" id="wizGo" style="background:#2f6fde;color:#fff;border-color:#2f6fde;font-weight:700">진단하기</button>'
      +'<button class="btn" id="wizReset2">답 지우기</button></div><div id="wizResult"></div></div></div>';
    document.body.appendChild(mask);
    mask.addEventListener("click", function(e){ if(e.target===mask) closeWiz(); });
    document.getElementById("wizClose").addEventListener("click", closeWiz);
    document.getElementById("wizGo").addEventListener("click", runWiz);
    document.getElementById("wizReset2").addEventListener("click", function(){
      WQ.forEach(function(w){ var n=document.querySelector('input[name="wq_'+w.k+'"][value="n"]'); if(n) n.checked=true; });
      document.getElementById("wizResult").innerHTML="";
    });
  }
  function openWiz(){ document.getElementById("wizMask").classList.add("on"); }
  function closeWiz(){ document.getElementById("wizMask").classList.remove("on"); }
  function readAnswers(){
    var a={};
    WQ.forEach(function(w){ var el=document.querySelector('input[name="wq_'+w.k+'"]:checked'); a[w.k]=!!(el&&el.value==="y"); });
    return a;
  }
  function cSeqChips(seq){
    return seq.map(function(c){
      var nm=((CUNITS[c]||{}).c_name_ko)||"";
      return '<span class="cchip" data-node="'+E(c)+'" title="'+E(nm)+'">'+E(c)+'</span>';
    }).join("");
  }
  function runWiz(){
    var a=readAnswers();
    var v=wizardVerdict(a);
    var box=document.getElementById("wizResult");
    var html="";
    if(v.faithful){
      var qhtml=v.qcodes.length? v.qcodes.map(qChip).join(" ") : '<span class="muted">없음(축이 깨끗하면 질문 없이 통과)</span>';
      html+='<div class="rescard ok"><h4>✅ 시작 지점: <b>N0</b> → 따라가면 <b>🏁 nonmem-ready</b></h4>'
        +'당신 파일은 <b>깔끔한 tidy 표</b>라 도구가 자동 정리 밴드로 들어갑니다. 아래 길을 끝까지 따라가면 완성에 도달합니다.'
        + pathBreadcrumb(v.c_sequence, false)
        +'<div style="margin-top:8px"><b>이 파일에 적용되는 정리·검사 작업</b> (클릭하면 설명):<br>'+cSeqChips(v.c_sequence)+'</div>'
        +'<div style="margin-top:8px"><b>정리하면서 마주칠 수 있는 결정 질문(Q)</b>:<br>'+qhtml+'</div>'
        +'<div style="margin-top:8px" class="muted">파일만으로 풀리는 축: <b>A1 / A3 / A5 / A10</b>. 나머지(A0 / A2 / A4 / A6 / A7 / A8 / A9)는 '
        +'<b>분석 목적 · 정책</b>이라 <b>당신이 정해야</b> 합니다(파일만 봐선 모름 — over-read 금지).</div></div>';
    }else{
      var reasons=[], wus=[];
      if(a.qa){ reasons.push("검량/QA 블록이 실샘플과 섞여 있음"); wus.push("WU1 QA-strip(검량·QC 행 제거)"); wus.push("WU3 pivot(QA 제거 후 wide→long)"); }
      if(a.param){ reasons.push("파라미터 요약 시트(원자료 아님)"); wus.push("WU1 param-summary-reserve(건너뛰고 보존 — drop 아님)"); }
      if(a.subject_wide){ reasons.push("subject-wide(시간=행, 개체=열) 배치"); wus.push("WU3 pivot-wide-to-long"); }
      if(a.bw_sheet || a.qa || a.param || a.subject_wide){ wus.push("WU4 dose-bw-join(체중/용량 시트 결합)"); }
      if(!a.qa && !a.param && !a.subject_wide){ reasons.push("알 수 없는 구조(tidy로 못 읽음)"); }
      var uniq=wus.filter(function(x,i){ return wus.indexOf(x)===i; });
      var proj=projectedFaithfulSeq(a);
      html+='<div class="rescard onramp"><h4>🛟 궤도 복귀 경로 — 막다른 길이 아닙니다</h4>'
        +'당신 파일은 아직 도구가 자동으로 다루는 <b>깔끔한 tidy 표</b>가 아닙니다. 하지만 dead-end가 아니라, 아래 <b>2단계</b>로 궤도에 올리면 <b>🏁 nonmem-ready</b>까지 갈 수 있어요.'
        +'<div style="margin-top:8px"><b>감지된 이유</b>: '+(reasons.length?reasons.map(E).join(" / "):"—")+'</div>'
        +'<div class="step"><b>1단계 — 표 정리(on-ramp)</b> <span class="manual">⚠️ 이 정리는 아직 도구가 자동으로 못 함 — 당신/LLM이 먼저 (GAP-37)</span><br>'+(uniq.length?uniq.map(E).join("<br>"):"—")+'</div>'
        +'<div class="step"><b>2단계 — 표가 tidy가 되면 이어지는 자동 경로</b> <span class="muted">(아래는 <b>예상 경로</b> · 점선)</span>'+pathBreadcrumb(proj, true)+'</div>'
        +'<div style="margin-top:8px">지금 도구가 자동으로 진단하는 작업: '+cSeqChips(v.c_sequence)+' <span class="muted">(파일 속성만 — 1단계 정리 전이라 여기까지)</span></div>'
        +'<div style="margin-top:8px" class="muted">✅ 정확한 자동 진단은 정본 Python 어댑터로: <span class="mono">python -m src.adapter &lt;내파일.xlsx&gt; --recipe</span></div></div>';
    }
    box.innerHTML=html;
    Array.prototype.forEach.call(box.querySelectorAll(".cchip"), function(ch){
      ch.addEventListener("click", function(){
        var n=cy.getElementById(ch.getAttribute("data-node"));
        if(n && n.length){ closeWiz(); onNodeTap(n); }
      });
    });
    var ids=["N0"].concat(v.c_sequence).concat(v.qcodes||[]).concat(["AUTO"]);
    highlightSet(ids);
  }
  function highlightSet(ids){
    if(typeof clearHighlight==="function") clearHighlight();
    var col=cy.collection();
    ids.forEach(function(id){ var n=cy.getElementById(id); if(n && n.length) col=col.union(n); });
    if(!col.length) return;
    cy.elements().addClass("dim");
    col.removeClass("dim").addClass("hl");
    var inter=col.edgesWith(col);
    inter.removeClass("dim");
    inter.forEach(function(e){ e.addClass(e.data("conditional")?"hlCond":"hlSingle"); });
    var n0=cy.getElementById("N0"); if(n0 && n0.length){ n0.removeClass("hl").addClass("current"); }
    try{ cy.animate({fit:{eles:col.union(inter), padding:60}}, {duration:300}); }catch(e){ cy.fit(col.union(inter),60); }
  }

  /* ===== 용어집 모달 ===== */
  function buildGloss(){
    var mask=document.createElement("div"); mask.id="glossMask";
    function rows(catLabel, obj, order){
      var keys=order||Object.keys(obj);
      var body=keys.map(function(k){
        var v=obj[k]; if(!v) return "";
        return '<div class="gloss-row"><span class="gc">'+E(k.indexOf("::")>=0?k.split("::")[1]:k)+'</span>'+E(v)+'</div>';
      }).join("");
      return '<div class="gloss-sec"><h3>'+catLabel+'</h3>'+body+'</div>';
    }
    var statesByAxis="";
    (Object.keys(GLOSSARY.axis)).forEach(function(ax){
      var sub=Object.keys(GLOSSARY.state).filter(function(k){ return k.indexOf(ax+"::")===0; });
      if(sub.length){
        var b=sub.map(function(k){ return '<div class="gloss-row"><span class="gc">'+E(k.split("::")[1])+'</span>'+E(GLOSSARY.state[k])+'</div>'; }).join("");
        statesByAxis+='<div class="gloss-sec"><h3>축 '+E(ax)+' 의 상태 — '+E(GLOSSARY.axis[ax])+'</h3>'+b+'</div>';
      }
    });
    mask.innerHTML='<div id="glossBox"><h2>📖 용어집 — 어려운 말 쉬운 말 대응<button class="btn" id="glossClose">×</button></h2><div id="glossBody">'
      +'<div class="muted" style="font-size:12px;margin-bottom:8px">화면 곳곳의 <span class="codechip">코드</span>에 마우스를 올려도 같은 설명이 뜹니다.</div>'
      +rows("관문 N0–N7 (큰 단계)", GLOSSARY.node)
      +rows("축 A0–A10 (판단 기준)", GLOSSARY.axis)
      +rows("작업 종류", GLOSSARY.kind)
      +rows("정리 단계(layer)", GLOSSARY.layer)
      +rows("종착점", GLOSSARY.terminal)
      +rows("질문 Q-code", GLOSSARY.qcode)
      +statesByAxis
      +rows("작업 용어(srp_intent의 동사/명사)", GLOSSARY.vocab)
      +'</div></div>';
    document.body.appendChild(mask);
    mask.addEventListener("click", function(e){ if(e.target===mask) mask.classList.remove("on"); });
    document.getElementById("glossClose").addEventListener("click", function(){ mask.classList.remove("on"); });
  }

  /* ===== 범례 + 경계 배너 쉬운 말로 다시 그리기 ===== */
  function redrawLegend(){
    function lg(label, sw){ return '<span class="lg"><span class="sw" style="'+sw+'"></span>'+label+'</span>'; }
    var shapes=[
      ["동그라미 = 변환(고치기)","background:#7fb2ff;border-radius:50%"],
      ["점선 동그라미 = 감지/검사","background:#bcd9ff;border-radius:50%;border-style:dashed"],
      ["육각 = 분기 결정","background:#ffcf80"],
      ["연한 육각 = 축 질문(A0~A10)","background:#ffe1a8"],
      ["다이아 = 큰 관문(N0~N7)","background:#ffb74d"]
    ];
    var term=[
      ["완성(자동/정리)","background:#43a047"],
      ["사람 결정 대기","background:#ffa726"],
      ["질문(Q) 답변 필요","background:#ef5350"],
      ["사용 불가(INVALID)","background:#546e7a"]
    ];
    var edges=[
      ["자동 기본 경로 (앰버 실선)","background:#E8820C"],
      ["질문(Q)으로 빠지는 갈림길 (청록 점선)","background:#15B4C7;border-style:dashed"],
      ["사람 개입 후 복귀 (파랑 점선)","background:#1976d2;border-style:dashed"]
    ];
    function row(items){ return items.map(function(x){ return lg(x[0], x[1]); }).join(""); }
    var el=document.getElementById("legend");
    if(el) el.innerHTML='<span class="grp">노드 모양</span>'+row(shapes)
      +'<span class="sep"></span><span class="grp">종착</span>'+row(term)
      +'<span class="sep"></span><span class="grp">길(클릭 시)</span>'+row(edges);
    var bn=document.getElementById("boundary"), b=window.DT_BANNER||{};
    if(bn) bn.innerHTML='<b>쉽게 말해</b> — 이 그림은 엉망인 raw 데이터에서 NONMEM 분석용 <b>깔끔한 데이터</b>까지 가는 모든 갈림길을 한 장에 그린 <b>지도</b>입니다. '
      +'점(작업)을 클릭하면 그 일이 무엇인지·다음에 어디로 가는지 쉬운 말로 풀어줍니다. '
      +'· 전체 시나리오 <b>'+b.total_strands+'개</b> 중 자동 완성 <b>'+b.complete+'</b> · 사람 결정 대기(Q) <b>'+b.quarantine+'</b> · 사용 불가 <b>'+b.invalid+'</b>. '
      +'→ <b>“🔍 내 파일 진단”</b> 버튼으로 내 파일이 어디서 시작하는지 확인하세요.';
  }

  /* ===== 전체 작업 카드(122) 목록 모달 — 그래프 배선과 무관히 모든 c 열람 ===== */
  function buildCardList(){
    var mask=document.createElement("div"); mask.id="cardMask";
    var ids=Object.keys(EASY).slice().sort();
    function cinfo(id){ return CUNITS[id]||CUNITS_EXTRA[id]||{}; }
    var order=["L-1->L-2","L-2->L-3","L-3->L-4","L-4->L-5"];
    var byL={}; ids.forEach(function(id){ var L=cinfo(id).layer_pair||"기타"; (byL[L]=byL[L]||[]).push(id); });
    var groups=order.concat(Object.keys(byL).filter(function(L){return order.indexOf(L)<0;}));
    var listHtml=groups.filter(function(L){return byL[L];}).map(function(L){
      var items=byL[L].map(function(id){ var c=cinfo(id);
        return '<div class="clrow" data-cid="'+id+'" data-q="'+E((id+' '+(c.c_name_ko||'')+' '+(c.srp_intent||'')).toLowerCase())+'">'
          +'<span class="clcode">'+id+'</span> '+E(c.c_name_ko||"")
          +' <span class="clkind">'+E((gloss("kind",c.kind)||c.kind||"").split(" ")[0])+'</span></div>';
      }).join("");
      return '<div class="clgrp"><h4>'+E(gloss("layer",L)||L)+' <span class="muted">('+byL[L].length+')</span></h4>'+items+'</div>';
    }).join("");
    mask.innerHTML='<div id="cardBox"><h2>📋 작업 카드 — 전체 '+ids.length+'개 '
      +'<span class="muted" style="font-weight:400;font-size:11px">(검색·클릭 → 쉬운 설명 + 🤖 LLM 요청문)</span>'
      +'<button class="btn" id="cardClose">×</button></h2>'
      +'<div id="cardWrap"><div id="cardList">'
      +'<input id="cardSearch" placeholder="검색: 코드·이름·작업 (예: BLQ, 시간, 병합, c0011)" autocomplete="off">'
      +'<div id="cardRows">'+listHtml+'</div></div>'
      +'<div id="cardDetail"><div class="muted" style="padding:14px">← 왼쪽에서 작업(c)을 클릭하면 쉬운 카드가 여기 표시됩니다. (122개 전부 열람 가능)</div></div>'
      +'</div></div>';
    document.body.appendChild(mask);
    mask.addEventListener("click", function(e){ if(e.target===mask) mask.classList.remove("on"); });
    document.getElementById("cardClose").addEventListener("click", function(){ mask.classList.remove("on"); });
    var detail=document.getElementById("cardDetail");
    Array.prototype.forEach.call(mask.querySelectorAll(".clrow"), function(row){
      row.addEventListener("click", function(){
        Array.prototype.forEach.call(mask.querySelectorAll(".clrow.sel"), function(r){ r.classList.remove("sel"); });
        row.classList.add("sel");
        detail.innerHTML=window.renderCPanel(row.getAttribute("data-cid"));
        detail.scrollTop=0;
      });
    });
    var sb=document.getElementById("cardSearch");
    sb.addEventListener("input", function(){
      var q=sb.value.trim().toLowerCase();
      Array.prototype.forEach.call(mask.querySelectorAll(".clrow"), function(r){
        r.style.display=(!q || r.getAttribute("data-q").indexOf(q)>=0)?"":"none";
      });
      Array.prototype.forEach.call(mask.querySelectorAll(".clgrp"), function(g){
        var any=Array.prototype.some.call(g.querySelectorAll(".clrow"), function(r){ return r.style.display!=="none"; });
        g.style.display=any?"":"none";
      });
    });
  }

  /* ===== 부팅: 모달 생성 + 버튼 연결 + 범례 갱신 + 현재 패널 v2로 다시 그리기 ===== */
  buildWizard();
  buildGloss();
  buildCardList();
  redrawLegend();
  var wb=document.getElementById("wizardBtn"); if(wb) wb.addEventListener("click", openWiz);
  var gb=document.getElementById("glossBtn"); if(gb) gb.addEventListener("click", function(){ document.getElementById("glossMask").classList.add("on"); });
  var cb=document.getElementById("cardBtn"); if(cb) cb.addEventListener("click", function(){ document.getElementById("cardMask").classList.add("on"); });
  /* 🤖 요청문 복사 버튼(이벤트 위임 — 패널은 매번 새로 그려지므로) */
  document.addEventListener("click", function(e){
    var btn=(e.target && e.target.closest) ? e.target.closest(".copybtn") : null;
    if(!btn) return;
    var el=document.getElementById(btn.getAttribute("data-copy")); if(!el) return;
    var txt=el.innerText||el.textContent||"";
    function flash(){ var t=btn.getAttribute("data-lbl"); if(!t){ t=btn.textContent; btn.setAttribute("data-lbl",t); } btn.textContent="✓ 복사됨"; setTimeout(function(){ btn.textContent=t; },1200); }
    if(navigator.clipboard && navigator.clipboard.writeText){ navigator.clipboard.writeText(txt).then(flash, flash); }
    else { try{ var r=document.createRange(); r.selectNodeContents(el); var sel=window.getSelection(); sel.removeAllRanges(); sel.addRange(r); document.execCommand("copy"); }catch(_){ } flash(); }
  });
  if(state && state.selected){
    var sn=cy.getElementById(state.selected);
    if(sn && sn.length){ try{ onNodeTap(sn); }catch(e){} }
  }
})();
</script>
'''


def app_js_v2() -> str:
    return recolor(B.APP_JS) + "\n" + _V2_OVERRIDE


# ═════════════════════════════════════════════════════════════════════════════
# 5. 조립 + 기록
# ═════════════════════════════════════════════════════════════════════════════
def build_html() -> str:
    assert_glossary_complete()
    data_script = (
        "<script>\n"
        "var ELES=" + B.js(B.ELES) + ";\n"
        "var CUNITS=" + B.js(B.CUNITS) + ";\n"
        "var CUNITS_EXTRA=" + B.js(CUNITS_EXTRA) + ";\n"
        "var QINFO=" + B.js(B.QINFO) + ";\n"
        "var NODEINFO=" + B.js(B.NODEINFO) + ";\n"
        "var AXIS_STATES=" + B.js(B.AXIS_STATES) + ";\n"
        "var FAMILIES=" + B.js(B.FAMILIES) + ";\n"
        "var DEFERRED_VIEW=" + B.js(B.DEFERRED_VIEW) + ";\n"
        "var DT_STATS=" + B.js(B.STATS) + ";\n"
        "var DT_BANNER=" + B.js(B.BANNER) + ";\n"
        "var WIZARD=" + B.js(WIZARD) + ";\n"
        "var GLOSSARY=" + B.js(GLOSSARY) + ";\n"
        "var EASY=" + B.js(EASY) + ";\n"
        "</script>\n"
    )
    return page_head_v2() + "\n" + B.LIBS + "\n" + data_script + app_js_v2() + B.PAGE_TAIL


def main():
    html = build_html()
    out = B.ROOT / "render" / "index_v2.html"
    out.write_text(html, encoding="utf-8")
    kb = len(html.encode("utf-8")) / 1024.0
    print("[build_html_v2] wrote %s" % out)
    print("[build_html_v2] size = %.1f KB" % kb)
    print("[build_html_v2] glossary: axis=%d state=%d qcode=%d kind=%d layer=%d terminal=%d vocab=%d" % (
        len(GLOSSARY["axis"]), len(GLOSSARY["state"]), len(GLOSSARY["qcode"]),
        len(GLOSSARY["kind"]), len(GLOSSARY["layer"]), len(GLOSSARY["terminal"]), len(GLOSSARY["vocab"])))
    print("[build_html_v2] wizard: file_property=%s data_dependent=%d canon=%d qa_tokens=%d" % (
        WIZARD["file_property_c"], len(WIZARD["data_dependent_c"]), len(WIZARD["canon_order"]), len(WIZARD["qa_tokens"])))


if __name__ == "__main__":
    main()
