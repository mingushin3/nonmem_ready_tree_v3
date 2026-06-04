# Tier 0 Adapter — Recipe-Emit (경로 iii 보강, read-only·report-only)

> **추적성 스탬프:** engine/SSOT baseline **2004d27** (frozen, ZERO-diff) · adapter front-end **c83c520** ·
> recipe-emit 확장 = **working-tree(미커밋)**. 본 문서 = doc-only, 미커밋 대상.
> **목적:** honest-stop 진단을 **"WU1 인벤토리 + 파일별 실행 recipe + 모델러결정 체크리스트"** 로 심화
> (검토 §5 경로 iii). recipe는 **강제 변환이 아니라 기술(description)·안내** — 트리 라우팅·실행·strand
> 재도출(M2) 일절 없음. 엔진/SSOT 무수정. = 이 팀의 WU1 인벤토리 deliverable 자동판.
> **방법:** `python -m src.adapter '<xlsx>' --recipe` (openpyxl read-only). 감지된 구조만 단정, 나머지는 verify.
> **★ probe 등급 계승:** n=3 · 단일 CRO 템플릿 · 단일 분자(Tacrolimus) · 단일 endpoint(PK). 일반화 아님.
> baseline 회귀: `pytest tests/` → **1004 passed / 4 skipped / 1 xfailed** (기존 992 + recipe-emit 12).

---

## §0. 3파일 요약 — feature-driven recipe

| 파일 | WU1 QA-strip(시트) | WU1 1.Data | WU3 PIVOT | WU4 BW JOIN | 체크리스트 | 비결정 |
|---|---|---|---|---|---|---|
| Mouse | Report_Summary, 2.Result | skip+reserve | pivot-after-qa-strip | **워크북 내** `BW` 시트 | BLQ · BW계층 | **파생 재적합**(1.Data 재산출) |
| Rat | 결과 처리본, 2.Result, 2.Result(2) | skip+reserve | pivot-after-qa-strip | **외부**(워크북 BW 부재 → PDF) | BLQ · BW계층 | — |
| Dog | 2.Result | skip+reserve | pivot-after-qa-strip | **워크북 내** `Body weights` 시트 | BLQ · BW계층 · **Advagraf/RLD 제외** | — |

**공통 골격:** 3파일 모두 동일 CRO 템플릿 → **WU1(QA-strip + 1.Data skip+reserve) → WU3(PIVOT) →
WU4(dose/BW JOIN)** 의 기계적 front-half + 모델러 결정(BLQ·BW계층)으로 수렴. 이는 이 repo의 완성·
전수검증 데이터셋이 실제로 밟은 WU1→WU3→WU4 순서와 동형(검토 §4).

**종별 차이는 감지된 구조에서 자연 발생(종 하드코딩 없음):**
- **Mouse** = BW가 워크북 내(`BW` 시트) + `1.Data`에 재산출 마커 존재 → 비결정 분류.
- **Rat** = BW-유사 시트 미검출 → 외부(교차문서, 예: PDF Table 1) JOIN로 정직 표기.
- **Dog** = comparator 마커(Advagraf/RLD) 4건 감지 → 다중-arm 제외 체크리스트 점화.

---

## §1. 파일별 recipe (실측)

### 1. Mouse PK — `ND-P2026043_..._BW포함.xlsx`
- **WU1 QA-strip** `remove` ← 시트 `['Report_Summary', '2. Result']`
  제거대상: Standard samples / DBLK / BLK (P) / QC(LQC/MQC/HQC) / Calibration curve rows / Abbreviation·정의 행.
  note: QA 제거는 PIVOT 선행(검량선·DBLK·QC가 관측 오염 차단).
- **WU1 param-summary-reserve** `skip-and-reserve` ← 시트 `['1. Data']`  ★ **drop 아님** — NCA 대조용 보존(검토 §2).
- **WU3 pivot-wide-to-long** `pivot-after-qa-strip` ← `['Report_Summary', '2. Result']`
  verify ▸ 샘플블록 wide 여부는 QA행에 가려 자동확정 못 함(QA-strip 후 layout 확인) ▸ **conc 출처 = 샘플블록
  (예: 2.Result)이며 param-summary(1.Data) 아님 확인** ▸ 수평 반복배치(Blood 1차/2차) 점검(자동감지 아님)
  ▸ wide 변종(sparse/다중배치/다중-arm) 모델러 확인 ▸ Mean/SD 집계열 제외.
- **WU4 dose-bw-join** `join` ← `bw_source={in_workbook:True, sheets:['BW']}`; 투여시점 BW로 AMT(verify).
- **체크리스트(flag만):** `blq-zero-policy` · `bw-hierarchy`.
- **비결정(non-decision):** `derived-parameter-refit @ 1. Data`
  evidence=`["1. Data r3c6: 'G2 (재산출)'", "1. Data r3c7: 'G3 (재산출)'"]`
  사유: 동일 농도-시간 데이터의 단말 NCA λz 재적합(초기지표 동일·단말만 상이) — 신규 arm/replicate 아님.
  ref: 검토의견 §3. **→ `decision_required` = 0** (이전 probe의 arm-vs-replicate 2옵션 오분류 제거).

### 2. Rat PK — `2차 RAT PK_Tacrolimus 1M_Batch No.56.78(원본).xlsx`
- **WU1 QA-strip** ← `['결과 처리본', '2. Result', '2. Result (2)']` (제거대상 동일).
- **WU1 param-summary-reserve** ← `['1. Data']` (skip+reserve).
- **WU3 pivot-wide-to-long** `pivot-after-qa-strip` ← `['결과 처리본', '2. Result', '2. Result (2)']` (verify 동일).
- **WU4 dose-bw-join** `join` ← `bw_source={in_workbook:False, sheets:[]}`
  note: BW 워크북 내 부재 → **외부 출처 필요(예: PDF Table 1), 교차문서 JOIN(난도↑)**.
  verify ▸ BW 출처를 외부 보고서에서 확보 — **PDF 존재 단정 아님, 확인 필요** ▸ 투여시점 BW 확인.
- **체크리스트:** `blq-zero-policy` · `bw-hierarchy`. comparator 미점화(정직 — Rat RLD 없음).
- **비결정:** 없음 (재산출 마커가 top-sample 영역 내 미검출 — '없음'이 아니라 '미검출', §3 sampling 경계).

### 3. Dog PK — `3차 BEAGLE PK_Tacrolimus 1M (RLD 비교) - 복사.xlsx`
- **WU1 QA-strip** ← `['2. Result']` (제거대상 동일).
- **WU1 param-summary-reserve** ← `['1. Data']` (skip+reserve).
- **WU3 pivot-wide-to-long** `pivot-after-qa-strip` ← `['2. Result']` (verify 동일).
- **WU4 dose-bw-join** `join` ← `bw_source={in_workbook:True, sheets:['Body weights']}`; 투여시점 BW로 AMT(verify).
- **체크리스트(flag만):** `blq-zero-policy` · `bw-hierarchy` · **`comparator-arm-exclusion`**
  evidence=`["filename: '...RLD 비교...'", "Report_Summary r11c2: 'Advagraf'", "1. Data r1c2: '시험 목적: ...
  RLD (Advagraf)의 PK를 비교...'", "1. Data r10c3: 'AdvagrafⓇ, 1 mg(1 capsule)/head'"]`
  flag: Advagraf(RLD) 비교-arm 제외 / comedication 필터 — **모델러 결정(다중-arm)**.
- **비결정:** 없음 (재산출 마커 sampled region 내 미검출).

---

## §2. 검토 §3 도메인 교정 — Mouse 재산출 = 비결정(파생 재적합)

이전 probe(c83c520)는 Mouse `1.Data`의 `재산출` 컬럼을 **arm-vs-replicate 2옵션**(B에 Dog 전용
"RLD vs 시험" 오용)으로 surface했다. 검토 §3가 짚은 대로 이는 도메인 오분류다 — `재산출`은 동일 농도
데이터의 **단말 NCA 재적합**(초기지표 tmax/Cmax/AUC0-168 동일, 단말 t½/tlast/AUCinf만 상이)일 뿐,
신규 arm도 replicate도 아니다(raw conc엔 무의미). 본 보강은:
- `surface_ambiguous_wide`가 **param-summary 시트를 skip**(per-sheet) → arm-vs-replicate 2옵션 미생성.
- `classify_non_decisions`가 **`derived-parameter-refit` 비결정**으로 분류(1.Data SKIP하면 ambiguity 미발생).
- **실측 결과:** Mouse `decision_required` **1 → 0**, `non_decisions` **0 → 1**. honest-stop이 자동 선택을
  애초에 막았기에 silent 오류로 굳지 않았고, 도메인 라벨만 교정됨. "RLD vs 시험"은 Dog 구조이며 Dog의
  comparator-arm 체크리스트로 올바르게 위치(§1.3).
- **회귀 안전:** param-summary 아닌 wide(재산출)의 2옵션은 그대로 유지(가드 과적용 0,
  `test_two_option_preserved_for_nonparam_wide`).

---

## §3. Honesty 경계 — 단정 vs 확인(verify)

recipe는 **감지된 `Finding.feature`만 단정**하고, 그 외는 전부 `verify`(="확인하라")로 남긴다(날조 0):
- **단정 가능(감지됨):** QA-contaminated 시트 목록 · param-summary 시트 · BW-유사 시트 유무 · Mean/SD
  마커 존재 · comparator 마커(파일명+셀, evidence 동반).
- **단정 금지(→ verify):** conc 출처가 2.Result(≠1.Data)임 · wide layout(QA에 가려 자동확정 불가) ·
  wide 변종명(sparse/다중배치/다중-arm) · 수평 반복배치(Blood 1차/2차) · 투여시점 BW 기준 ·
  외부 BW가 PDF에 존재함(부재-사실만 단정, PDF는 *예시*).
- WU1/WU3가 `Report_Summary`(Mouse)처럼 요약시트까지 qa-contaminated로 포함하는 것은 over-read가
  아니라 **후보 나열** — "conc 출처=샘플블록 확인" verify가 모델러에게 진짜 conc 블록 선별을 위임한다.

---

## §4. 산출 방법 · 무수정 증명
- 생성: `python -m src.adapter '<xlsx>' --recipe` (또는 `ingest(xlsx)['recipe']`/`['non_decisions']`). read-only.
- 신규/변경 표면: `src/adapter/recipe_emitter.py`(신규) · `gap_annotator.py`(§3 가드+classify) ·
  `__init__.py`/`__main__.py`(배선) · `tests/test_adapter_tier0.py`(+12). **엔진/SSOT diff = 0줄**
  (`git diff --numstat -- src/orchestrator.py src/c_units/ spec/` = empty).
- recipe-emit는 df를 환원/pivot/JOIN하지 않는다 — honest-stop 파일은 여전히 `[c0201, c0210]`만 dispatch,
  `structure-recognition`에서 정지. recipe는 **그 위에 얹은 기술(description)일 뿐**(M2 무의존, 되돌림위험 0).
- 본 보강 후 "현 진단(honest-stop) vs recipe-emit 중 실무에 무엇이 쓸 만한가"는 사용자가 둘을 나란히
  놓고 실물로 비교해 정한다(measure-first 충족). 본 작업은 그 비교 대상을 만들어 둔 것이지 진단을 대체·강제하지 않음.
