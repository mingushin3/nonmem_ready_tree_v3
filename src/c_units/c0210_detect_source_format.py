"""DETECT FILE_FORMAT — A10 소스 형식 파싱 가능성 평가

srp_intent: DETECT FILE_FORMAT
c_name_ko: A10 소스 형식 파싱 가능성 평가
kind: detect  (A10 axis classifier; df read-only)

postcondition_predicate:
    meta.get('a10_state') in ['SDTM-ADaM','EDC-STRUCTURED','CRO-VENDOR','FLAT-TABULAR','LEGACY-NM','SEMI-STRUCTURED','NON-TABULAR','CORRUPTED']

★ 위치 AUDIT (timing 불일치 — issues/provenance_gaps.md GAP-13):
  FILE_FORMAT(xlsx/csv·인코딩·시트·corrupted/non-tabular)은 의미상 df가 생기기 *전* 파이프라인
  맨 앞 게이트이고 trigger_condition도 "파일 로드 직후"다. 그러나 axis 번호는 A10(마지막),
  layer_pair=L-3->L-4, pass_route_to chain은 c0209(A9)→c0210→next로 axis sweep 끝에 c0210을
  둔다. 즉 *axis 순서 vs 의미상 시점* 불일치(c0209 GAP-12 NOUN↔구현 표면 불일치와 동류).
  falsifiable 귀결: precond(len(df)>0 or file_exists) 하에 A10이 끝에서 평가되면, 파싱된 df가
  존재한다는 것 자체가 파일이 성공적으로 열렸다는 뜻 → NON-TABULAR/CORRUPTED는 df 검사로
  구조적 도달 불가(그런 파일은 애초에 df를 못 만든다). 두 실패 state는 선언에만 의존한다.

Routing scope (can_route_to_q=[]): 순수 분류기 — route_to_q 항상 None, pass 항상 True.
  q_codes.json에 A10/FILE_FORMAT 참조 0건 → can_route_to_q=[]와 정합(c0202 A2 동형).
  단 universe_sm §3 A10은 NON-TABULAR→UNSUPPORTED, CORRUPTED→INVALID 종착을 명시한다.
  UNSUPPORTED/INVALID는 §2 terminal(Q-code 아님; anchors.json 'terminals'에 존재) →
  **scope-밖 라우팅**: 8 state 전수 분류는 하되 route_to_q=None, terminal은 하류 ROUTE c 책임
  (D-S1/D-S4). c0204 GAP-5 / c0205 GAP-8 / c0209 GAP-12 선례(분류 범위 ≠ 라우팅 범위).
  contract상 NON-TABULAR/CORRUPTED도 pass=True가 되지만, 이는 c0205 ABSENT 처리와 동일하다.

선언 1차 → df fallback 한계(정직 기록, GAP-13; c0202 GAP-9 / c0207 GAP-11 / c0209 GAP-12 동형):
  meta['file_format'](1차) → meta['source_format'](2차) 선언 descriptor(외부 경계 입력)가 1차.
  부재 시 df fallback은 8개 중 **1개(FLAT-TABULAR)만** 도달한다 — 파싱된 df는 정의상 tabular·
  비-corrupted이므로 vendor/format 특화 state(SDTM/EDC/CRO/LEGACY/SEMI)와 실패 state
  (NON-TABULAR/CORRUPTED)는 선언 없이 구분/날조하지 못한다(위치 불일치 때문에 c0202의 2/10보다
  좁다). df만으로 state 날조 금지.

입력계약 (issues/provenance_gaps.md GAP-13):
  meta['file_format']/['source_format'] = 생산 c 없는 sponsor/file inventory 외부 경계 입력
    (study_design/covariate_state/defect_state 동형, orchestrator Phase 5 주입).
  meta['file_exists'] = precond 사용, 경계/orchestrator 입력(생산 c 없음).
  df = 파일 로드 단계가 생산 = A10이 "감지"하려는 그 대상 자체(위치 불일치의 핵심, 순환).
  ★ 시그니처 메모: spec python_snippet은 detect_source_format(file_path, meta)이나, 형제 c
    (c0202/c0207/c0209) 및 conftest 하네스는 전부 (df, meta) 규약 → (df, meta)로 구현,
    file 신호는 meta 경유. c0210은 meta['a10_state']만 write한다(df read-only).
"""

import pandas as pd

VALID_A10_STATES = frozenset([
    "SDTM-ADaM",
    "EDC-STRUCTURED",
    "CRO-VENDOR",
    "FLAT-TABULAR",
    "LEGACY-NM",
    "SEMI-STRUCTURED",
    "NON-TABULAR",
    "CORRUPTED",
])

# declared file-format descriptor -> a10_state (canonical + 명백한 alias)
_FILE_FORMAT_TO_STATE = {
    "sdtm-adam": "SDTM-ADaM",
    "sdtm": "SDTM-ADaM",
    "adam": "SDTM-ADaM",
    "edc-structured": "EDC-STRUCTURED",
    "edc": "EDC-STRUCTURED",
    "cro-vendor": "CRO-VENDOR",
    "cro": "CRO-VENDOR",
    "vendor": "CRO-VENDOR",
    "flat-tabular": "FLAT-TABULAR",
    "flat": "FLAT-TABULAR",
    "tabular": "FLAT-TABULAR",
    "csv": "FLAT-TABULAR",
    "legacy-nm": "LEGACY-NM",
    "legacy": "LEGACY-NM",
    "nonmem": "LEGACY-NM",
    "semi-structured": "SEMI-STRUCTURED",
    "semi": "SEMI-STRUCTURED",
    "multisheet": "SEMI-STRUCTURED",
    "pdf-table": "SEMI-STRUCTURED",
    "crf-export": "SEMI-STRUCTURED",
    "vendor-custom": "SEMI-STRUCTURED",
    "non-tabular": "NON-TABULAR",
    "nontabular": "NON-TABULAR",
    "pdf": "NON-TABULAR",
    "docx": "NON-TABULAR",
    "corrupted": "CORRUPTED",
    "corrupt": "CORRUPTED",
    "unreadable": "CORRUPTED",
}


def _norm_descriptor(val) -> str | None:
    if not isinstance(val, str):
        return None
    norm = val.strip().lower().replace("_", "-").replace(" ", "-")
    return norm or None


def _classify_a10(df: pd.DataFrame, meta: dict) -> str:
    # 1차: 선언 descriptor (외부 경계 입력) — file_format → source_format
    desc = _norm_descriptor(meta.get("file_format")) or _norm_descriptor(meta.get("source_format"))
    if desc in _FILE_FORMAT_TO_STATE:
        return _FILE_FORMAT_TO_STATE[desc]

    # df fallback (선언 부재): 파싱된 df = tabular·비-corrupted → FLAT-TABULAR 기본값(1-of-8 한계).
    # vendor/format 특화 state·실패 state(NON-TABULAR/CORRUPTED)는 선언 없이 날조 금지 (GAP-13).
    return "FLAT-TABULAR"


def _route_a10(a10_state: str):
    # can_route_to_q=[] : 순수 분류기, never routes. NON-TABULAR→UNSUPPORTED /
    # CORRUPTED→INVALID terminal은 하류 ROUTE c 책임 (scope-out, GAP-13).
    return None


def detect_source_format(df: pd.DataFrame, meta: dict) -> dict:
    state = _classify_a10(df, meta)
    meta["a10_state"] = state
    route = _route_a10(state)
    return {"a10_state": state, "pass": route is None, "route_to_q": route}
