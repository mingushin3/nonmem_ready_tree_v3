# Tier 0 Adapter — Real-File Probe (read-only, report-only)

> **추적성 스탬프:** engine/SSOT baseline **2004d27** (frozen, ZERO-diff) · 이 probe 출력 = adapter
> front-end **c83c520** 상태. (문서↔코드 falsifiable 귀속, 검토 §1 권고.) recipe-emit 보강은 별도
> 산출물 `issues/tier0_recipe_emit.md`(working-tree, 미커밋)로 분리 — 본 probe는 재작성하지 않음.

> **목적:** Tier 0 auto-ingest adapter(신규 `src/adapter/`, 엔진/SSOT 무수정)를 실물 전임상
> 소분자 raw xlsx 3종에 투입 — 출발점 자동 detect + 이유 부착 + 57-wired 백본 navigate +
> **첫 미지원 구조에서 정직 정지**(silent 추측 0). 실물 navigate 사거리·패치 우선순위 실측.
> **방법:** `src.adapter.ingest(xlsx)` 직접 실행(openpyxl read-only). 본 문서 = doc-only, 미커밋 대상.
> **★ 무수정:** spec/·src/orchestrator.py·src/c_units/·anchors·decision_tree·universe_sm 전부 불변.
> adapter는 `run_strand`/`dispatch`를 **무수정 호출**하는 front-end(ripple M4).
> **★ probe 등급:** n=3 · 단일 CRO 템플릿 · 단일 분자(Tacrolimus) · 단일 endpoint(PK). 일반화 아님.
> baseline: HEAD 2004d27 · pytest **974 green 불변**(+18 adapter test = 992 passed/4 skipped/1 xfailed).

---

## §0. 요약 — 3파일 공통 결과

| 파일 | 시트 | dispatched | resolved fingerprint | stop |
|---|---|---|---|---|
| 1. Mouse PK | 5 | `['c0201', 'c0210']` | {'A1': 'SINGLE', 'A10': 'SEMI-STRUCTURED'} | structure-recognition |
| 2. Rat PK | 6 | `['c0201', 'c0210']` | {'A1': 'SINGLE', 'A10': 'SEMI-STRUCTURED'} | structure-recognition |
| 3. Dog PK | 5 | `['c0201', 'c0210']` | {'A1': 'SINGLE', 'A10': 'SEMI-STRUCTURED'} | structure-recognition |

**공통 판정:** 3파일 모두 **honest-stop at `structure-recognition`** — 어느 시트도 tidy-long으로
충실 환원되지 않아(파생 param-summary·QA-혼재·subject-wide) conc 의존 detector를 dispatch하지 않음.
Fork 1대로 **file-property 축 `[c0201(A1), c0210(A10)]`만** dispatch(conc/dv/time 무관, cite-verify).
conc 의존 축(A0/A2~A9) 전부 `undetermined` — 부분 fingerprint로 명시 라벨(over-read 차단, 날조 0).
→ pilot_validation_preclinical §3 drop-point(step 2~4 QA제거·PIVOT·JOIN)를 **실측 재확인**.

---

## §1. 파일별 상세

### 1. Mouse PK

`ND-P2026043_Results_Tacrolimus_mPK_Blood_4th_fR_RE, BW포함.xlsx`

**시트 inventory + shape 분류:**

| sheet | rows | cols | merged | shape_class |
|---|---|---|---|---|
| Report_Summary | 30 | 12 | 18 | qa-contaminated |
| 1. Data | 70 | 15 | 4 | param-summary |
| 2. Result | 102 | 35 | 19 | qa-contaminated |
| 1(1). LCMS | 47 | 19 | 73 | unknown |
| BW | 30 | 28 | 12 | unknown |

**dispatched:** `['c0201', 'c0210']` · run_strand: boundary_at=None terminal=None total_cost=2 · entry_node=N0

**axis_fingerprint.resolved:** {'A1': 'SINGLE', 'A10': 'SEMI-STRUCTURED'}  
**undetermined:** ['A0', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9']  
**label:** PARTIAL file-property fingerprint (A1/A10 한정); conc 의존 축 전부 undetermined — honest-stop. 날조 0. over-read 금지.

**mess_profile (wired §6 dims):** {'BLQ_TOKEN': True, 'ENCODING': True, 'UNIT_DECLARATION': True}

**detect 내용 — wired 사유 (M5 단일출처: criterion_predicate_ko + ref):**

| feature | wired c | criterion_predicate_ko | ref | 구조 증거 |
|---|---|---|---|---|
| blq-token | c0305 | BLQ 토큰 변종의 존재와 LLOQ 수치가 파악됨 | universe_sm §6 BLQ_TOKEN | sheet '2. Result' r5c2: 'BQL' |
| encoding | c0216 | 인코딩 관련 결함 존재 여부가 결정됨 | universe_sm §3 A9 ENCODING-FIX, §6 ENCODING | non_ascii_present=True (cp949-suspected) |
| unit-column | c0214 | 모든 numeric 컬럼에 단위가 선언되어 있다 | universe_sm §6 UNIT_DECLARATION, §4 Q10, P5 | sheet '1. Data' |
| file-format | c0210 | 소스 형식이 8개 state 중 하나로 결정됨 | universe_sm §3 A10 | n_sheets=5, merged_total=126 |
| study-integration | c0201 | 연구 통합 수준이 SINGLE/MULTI-* 중 하나로 결정됨 | universe_sm §3 A1 | n_sheets=5, 단일 파일 |

**미지원 구조 — unwired 주석 (감지했으나 미배선, [[GAP-37]]):**

| feature | what | 구조 증거 |
|---|---|---|
| intra-sheet-qa-block | intra-sheet QA블록(Standard/DBLK/BLK/QC/Calibration)이 실샘플과 동일시트 혼재 | sheets: ['Report_Summary', '2. Result'] |
| param-summary | 파생 NCA 파라미터 요약 시트(Parameters×Unit×Mean) — raw conc 아님 | sheets: ['1. Data'] |
| mean-sd-aggregate | Mean/SD 집계열 (개별 관측 아님) | sheet '1. Data' |
| reanalysis-duplicate | 재산출/재분석 중복 그룹 (예: 'G2 (재산출)') | sheet '1. Data' r3c6: 'G2 (재산출)' |
| dose-bw-sheet-join | 체중(BW)/용량이 별도 시트 — event table로 JOIN 필요(c0110/c0111 미배선) | BW-like sheets: ['BW'] |

**decision_required — 모호-wide 2옵션 (D-G2, 자동 선택 금지):**

- sheet `1. Data` evidence=['G2 (재산출)', 'G3 (재산출)']
  - A: 동일 그룹의 재산출/재측정(replicate·reanalysis) → reconcile/dedupe 후 단일 시계열
  - B: 별개 arm/그룹(예: RLD vs 시험) → 분리 유지 + subject-wide→long PIVOT 개별 처리
  - why: 재측정 vs 별개군이 구조만으로 불확정 — 자동 선택 시 silent 오류(D-G2). 사용자 결정 필요.

> **★ SUPERSEDED (검토 §3 교정, recipe-emit 보강):** 위 2옵션(arm-vs-replicate, B의 "RLD vs 시험")은
> 도메인 오분류다 — `1.Data` 재산출은 **단말 NCA 재적합(파생 재적합)** = **비결정(non-decision)** 이다
> (초기지표 동일·단말만 상이, raw conc엔 무의미). recipe-emit는 param-summary 재산출을 `decision_required`
> 2옵션이 아니라 `non_decisions[derived-parameter-refit]`로 분류한다 → Mouse `decision_required` **1→0**,
> `non_decisions` **0→1**. "RLD vs 시험"은 Dog 구조이며 Dog comparator-arm 체크리스트로 위치.
> 상세 = `issues/tier0_recipe_emit.md` §2. (본 probe는 c83c520 출력 그대로 보존 — 정직 provenance.)

**stop:** at=`structure-recognition` · gap=GAP-37  
reason: 어느 시트도 tidy-long으로 충실 환원 불가 → conc 의존 detector 미dispatch (미배선 구조: ['intra-sheet-qa-block', 'param-summary', 'mean-sd-aggregate', 'reanalysis-duplicate', 'dose-bw-sheet-join'])


### 2. Rat PK

`2차 RAT PK_Tacrolimus 1M_Batch No.56.78(원본).xlsx`

**시트 inventory + shape 분류:**

| sheet | rows | cols | merged | shape_class |
|---|---|---|---|---|
| 결과 처리본 | 177 | 22 | 24 | qa-contaminated |
| Report_Summary | 35 | 12 | 17 | unknown |
| 1. Data | 149 | 18 | 46 | param-summary |
| 2. Result | 177 | 22 | 24 | qa-contaminated |
| 1(1). LCMS | 44 | 20 | 142 | unknown |
| 2. Result (2) | 177 | 22 | 32 | qa-contaminated |

**dispatched:** `['c0201', 'c0210']` · run_strand: boundary_at=None terminal=None total_cost=2 · entry_node=N0

**axis_fingerprint.resolved:** {'A1': 'SINGLE', 'A10': 'SEMI-STRUCTURED'}  
**undetermined:** ['A0', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9']  
**label:** PARTIAL file-property fingerprint (A1/A10 한정); conc 의존 축 전부 undetermined — honest-stop. 날조 0. over-read 금지.

**mess_profile (wired §6 dims):** {'BLQ_TOKEN': True, 'ENCODING': True, 'UNIT_DECLARATION': True}

**detect 내용 — wired 사유 (M5 단일출처: criterion_predicate_ko + ref):**

| feature | wired c | criterion_predicate_ko | ref | 구조 증거 |
|---|---|---|---|---|
| blq-token | c0305 | BLQ 토큰 변종의 존재와 LLOQ 수치가 파악됨 | universe_sm §6 BLQ_TOKEN | sheet '결과 처리본' r5c2: 'BQL' |
| encoding | c0216 | 인코딩 관련 결함 존재 여부가 결정됨 | universe_sm §3 A9 ENCODING-FIX, §6 ENCODING | non_ascii_present=True (cp949-suspected) |
| unit-column | c0214 | 모든 numeric 컬럼에 단위가 선언되어 있다 | universe_sm §6 UNIT_DECLARATION, §4 Q10, P5 | sheet '1. Data' |
| file-format | c0210 | 소스 형식이 8개 state 중 하나로 결정됨 | universe_sm §3 A10 | n_sheets=6, merged_total=285 |
| study-integration | c0201 | 연구 통합 수준이 SINGLE/MULTI-* 중 하나로 결정됨 | universe_sm §3 A1 | n_sheets=6, 단일 파일 |

**미지원 구조 — unwired 주석 (감지했으나 미배선, [[GAP-37]]):**

| feature | what | 구조 증거 |
|---|---|---|
| intra-sheet-qa-block | intra-sheet QA블록(Standard/DBLK/BLK/QC/Calibration)이 실샘플과 동일시트 혼재 | sheets: ['결과 처리본', '2. Result', '2. Result (2)'] |
| param-summary | 파생 NCA 파라미터 요약 시트(Parameters×Unit×Mean) — raw conc 아님 | sheets: ['1. Data'] |
| mean-sd-aggregate | Mean/SD 집계열 (개별 관측 아님) | sheet '1. Data' |

**decision_required:** 없음 (sampled top-region에 재산출/재분석 마커 미검출 — §3 sampling 경계 참조).

**stop:** at=`structure-recognition` · gap=GAP-37  
reason: 어느 시트도 tidy-long으로 충실 환원 불가 → conc 의존 detector 미dispatch (미배선 구조: ['intra-sheet-qa-block', 'param-summary', 'mean-sd-aggregate'])


### 3. Dog PK

`3차 BEAGLE PK_Tacrolimus 1M (RLD 비교) - 복사.xlsx`

**시트 inventory + shape 분류:**

| sheet | rows | cols | merged | shape_class |
|---|---|---|---|---|
| Report_Summary | 33 | 12 | 28 | unknown |
| 1. Data | 129 | 15 | 37 | param-summary |
| Body weights | 42 | 13 | 25 | unknown |
| 2. Result | 211 | 61 | 22 | qa-contaminated |
| 3. LCMS | 44 | 14 | 71 | unknown |

**dispatched:** `['c0201', 'c0210']` · run_strand: boundary_at=None terminal=None total_cost=2 · entry_node=N0

**axis_fingerprint.resolved:** {'A1': 'SINGLE', 'A10': 'SEMI-STRUCTURED'}  
**undetermined:** ['A0', 'A2', 'A3', 'A4', 'A5', 'A6', 'A7', 'A8', 'A9']  
**label:** PARTIAL file-property fingerprint (A1/A10 한정); conc 의존 축 전부 undetermined — honest-stop. 날조 0. over-read 금지.

**mess_profile (wired §6 dims):** {'BLQ_TOKEN': True, 'ENCODING': True, 'UNIT_DECLARATION': True}

**detect 내용 — wired 사유 (M5 단일출처: criterion_predicate_ko + ref):**

| feature | wired c | criterion_predicate_ko | ref | 구조 증거 |
|---|---|---|---|---|
| blq-token | c0305 | BLQ 토큰 변종의 존재와 LLOQ 수치가 파악됨 | universe_sm §6 BLQ_TOKEN | sheet '2. Result' r5c2: 'BQL' |
| encoding | c0216 | 인코딩 관련 결함 존재 여부가 결정됨 | universe_sm §3 A9 ENCODING-FIX, §6 ENCODING | non_ascii_present=True (cp949-suspected) |
| unit-column | c0214 | 모든 numeric 컬럼에 단위가 선언되어 있다 | universe_sm §6 UNIT_DECLARATION, §4 Q10, P5 | sheet '1. Data' |
| file-format | c0210 | 소스 형식이 8개 state 중 하나로 결정됨 | universe_sm §3 A10 | n_sheets=5, merged_total=183 |
| study-integration | c0201 | 연구 통합 수준이 SINGLE/MULTI-* 중 하나로 결정됨 | universe_sm §3 A1 | n_sheets=5, 단일 파일 |

**미지원 구조 — unwired 주석 (감지했으나 미배선, [[GAP-37]]):**

| feature | what | 구조 증거 |
|---|---|---|
| intra-sheet-qa-block | intra-sheet QA블록(Standard/DBLK/BLK/QC/Calibration)이 실샘플과 동일시트 혼재 | sheets: ['2. Result'] |
| param-summary | 파생 NCA 파라미터 요약 시트(Parameters×Unit×Mean) — raw conc 아님 | sheets: ['1. Data'] |
| mean-sd-aggregate | Mean/SD 집계열 (개별 관측 아님) | sheet '1. Data' |
| dose-bw-sheet-join | 체중(BW)/용량이 별도 시트 — event table로 JOIN 필요(c0110/c0111 미배선) | BW-like sheets: ['Body weights'] |

**decision_required:** 없음 (sampled top-region에 재산출/재분석 마커 미검출 — §3 sampling 경계 참조).

**stop:** at=`structure-recognition` · gap=GAP-37  
reason: 어느 시트도 tidy-long으로 충실 환원 불가 → conc 의존 detector 미dispatch (미배선 구조: ['intra-sheet-qa-block', 'param-summary', 'mean-sd-aggregate', 'dose-bw-sheet-join'])

---

## §2. 종합 — navigate 사거리 + 패치 우선순위 (실측)

- **navigate 사거리(현 Tier 0):** 파일 로드 → 시트 inventory/shape 분류 → file-property 축
  (A1 SINGLE · A10 SEMI-STRUCTURED) 확정 → BLQ토큰·ENCODING·UNIT 별도열 등 **wired feature 감지**
  + subject-wide·QA블록·param-summary·mean-sd·sheet-JOIN·inline-BLQ **unwired 감지(GAP-37)** →
  tidy-long 부재로 **structure-recognition에서 정직 정지.** conc 의존 축(A3 TIME·A5 BLQ·…)은 미도달.
- **drop-point 공통:** 실물은 **구조 조립 front-half(시트선택·QA제거·wide→long PIVOT·dose/BW JOIN)**
  에서 막힌다. 현 57-wired는 tidy long이 주어진 *후*(BLQ정규화·축평가·terminal)를 가이드하나,
  raw 다중시트 Excel→tidy long의 **앞단을 실현 못 함**(pilot §3 재확인, n=3 실측 일치).
- **패치 우선순위(실측 근거):** ① subject-wide→long **PIVOT** + intra-sheet **QA-strip** (모든 파일 1순위
  차단) ② dose/BW **sheet-JOIN** ③ inline-BLQ 결합셀 파싱. = ripple §4 Tier A→B→C 사다리와 동형.
- **Tier 사다리(ripple §4):** Tier 0(현재, 패치 불요) → Tier A(+QA 패치+배선) → Tier B(+PIVOT) →
  Tier C/D(+JOIN/UNIT) → Full. 각 Tier가 첫 미지원 경계를 뒤로 민다.

## §3. 경계 (정직)

- **probe 등급:** n=3 · 단일 CRO 템플릿 · 단일 분자(Tacrolimus) · 단일 endpoint(PK_CONCENTRATION).
  통계적 일반화가 아니라 **방향 신호**. (pilot §5 경계 계승.)
- **partial fingerprint:** resolved는 file-property 축(A1/A10)에 한정 — conc 의존 축은 undetermined로
  명시 라벨. 부분 결과를 전체 분류로 **over-read 금지**(Fork 1 사용자 보강).
- **sampling 경계:** inspector는 각 시트 **top 20행 × 12열**만 스캔(구조 판별 충분, 비용↓). 깊은 위치의
  재산출 마커(예: Rat `2. Result (2)`)는 미검출될 수 있음 — decision_required 공란은 '없음'이 아니라
  'sampled region 내 미검출'. 시트명 레벨 중복은 inventory에 보임.
- **무수정·무커밋:** spec/src/anchors/decision_tree/universe_sm 불변. run_strand/dispatch 무수정 호출.
  날조 0(사유 cite-verify, 정지점 구조 증거 기반). 본 문서 untracked.

## 부록 — 산출 방법

- 생성: `python -m src.adapter '<xlsx>'` 또는 `src.adapter.ingest('<xlsx>')`(read-only).
- reason 출처: `spec/c_units.json[c_id].verify_visualization.criterion_predicate_ko` + `.ref` (M5).
- 엔진 호출: `src.orchestrator.run_strand(seq, df, meta)` 무수정 — record 계약 그대로 소비.
- 회귀: `pytest tests/` → 992 passed / 4 skipped / 1 xfailed (기존 974 불변 + adapter 18).
