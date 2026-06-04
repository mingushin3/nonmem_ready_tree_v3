# Layer Stack: L-5 → L0 — Backward Decomposition Formal Specification

> **Version:** 0.1  
> **Scope:** modality = SMALL_MOLECULE; endpoint_data_type ∈ {PK_CONCENTRATION, EXPOSURE_METRIC, CONTINUOUS_PD}  
> **Canonical ref:** universe_sm.md v1.1, anchors.json v1.1, L0_nonmem_ready.md v0.1  
> **Purpose:** Raw data(L-5)에서 NONMEM-ready(L0)까지 5개 중간 layer의 entry precondition / exit postcondition을 formal predicate로 정의한다. 각 predicate는 binary(true/false)로 판정 가능해야 한다.  
> **Non-scope:** 개별 c-단위체 정의, sc 열거, 구현 코드는 본 문서 범위 밖.

---

## 0. Layer Stack Overview

### 0.1 전체 구조

```
Universe B (Mess Normalization)              Universe A (Axis Routing)
commutative, order-independent               branchy, conditional, N0–N7
                                       ★
L-5  ──────→  L-4  ──────→  L-3  ══════→  L-2  ──────→  L-1  ──────→  L0
Raw           Token-        Boundary       Tidy          Pre-          NONMEM-
Mess          Normalized    (bisection)    Long-Format   NONMEM        Ready
              (Phase 2d)    (Phase 2c)     (Phase 2b)    (Phase 2a)
```

### 0.2 이등분 원칙 (★ D-S3)

L-3을 **Universe A/B 경계**로 확정한다.

| 영역 | Layer 범위 | Universe | 특성 | Ref |
|------|-----------|----------|------|-----|
| 하류 | L-5 → L-4 → L-3 | B (Syntactic Mess) | 표기 정규화, 거의 commutative, 분기 거의 없음 | universe_sm §0.1, §6 |
| 상류 | L-3 → L-2 → L-1 → L0 | A (Scenario/Routing) | N0–N7 routing, 분기 다수, conditional logic | universe_sm §0.1, §2–§5 |

**분기/conditional의 거의 전부는 Universe A(상류)에 산다.** Universe B(하류)는 병렬·순서무관 정규화 파이프라인에 가깝다 (universe_sm §0.1).

### 0.3 Layer 한 줄 정의

| Layer | 정의 | Phase 2 sub-session |
|-------|------|---------------------|
| **L-5** | Raw mess. universe_sm §6 모든 dimension이 활성 가능한 상태. | — (입력) |
| **L-4** | Token-normalized. §6 26개 dimension 전부 해소. 구조는 미변형. | 2d (L-4↔L-5) |
| **L-3** | ★경계★ 모든 mess 해소 + A0–A10 axis가 deterministic하게 evaluate됨. | 2c (L-3↔L-4) |
| **L-2** | Tidy long-format. one event/row, one variable/column. NONMEM 컬럼 의식 없음. | 2b (L-2↔L-3) |
| **L-1** | NONMEM 특수컬럼 부여 완료. 표준 long-format event table. dose/obs 의미 명확. | 2a (L-1↔L-2) |
| **L0** | NONMEM-ready dataset. L0_nonmem_ready.md 전체 predicate 충족. | — (출력) |

---

## 1. L-5 — Raw Mess

### 1.1 Entry Precondition

L-5는 파이프라인의 최하류 진입점이다. 진입 조건은 **최소한** — 처리를 시작할 수 있는 파일임을 보장한다.

| ID | Predicate | Ref |
|----|-----------|-----|
| **L5-PRE-01** | `파일이 binary 수준에서 읽기 가능하다 (non-zero bytes, OS 수준 접근 가능)` | universe_sm §3 A10: CORRUPTED 제외 |
| **L5-PRE-02** | `파일이 tabular-origin이다 (표 형태로 해석 가능한 원본: CSV, Excel, TSV, SDTM 등). 순수 산문(PDF prose), 이미지, binary-only는 제외.` | universe_sm §3 A10: NON-TABULAR 제외 |

### 1.2 Exit Postcondition

L-5.exit_post ≡ L-4.entry_pre. 아래 §2.1의 L4-P01–P26 전체.

### 1.3 Violations & Routing

| 위반 조건 | Routing | Terminal | Ref |
|-----------|---------|----------|-----|
| L5-PRE-01 위반 (A10 = CORRUPTED) | — | INVALID | universe_sm §3 A10 |
| L5-PRE-02 위반 (A10 = NON-TABULAR) | — | UNSUPPORTED | universe_sm §3 A10 |

---

## 2. L-4 — Token-Normalized

### 2.1 Entry Precondition (= L-5.exit_post)

universe_sm §6의 **26개 mess dimension 전부**가 해소된 상태. 각 predicate는 해당 dimension의 raw 변종이 canonical form으로 정규화되었음을 뜻한다.

#### 2.1.1 결측 (Missing Value)

| ID | Predicate | Ref |
|----|-----------|-----|
| **L4-P01** | `모든 결측 토큰이 단일 canonical marker로 통일되었다. "NA", "N/A", "na", " NA ", blank, "999", ".", "NULL" 등 변종 잔존 0개.` | universe_sm §6 NA_TOKEN |

#### 2.1.2 BLQ

| ID | Predicate | Ref |
|----|-----------|-----|
| **L4-P02** | `모든 BLQ 토큰이 canonical marker로 치환되었다. numeric LLOQ 값이 보존되었다. "<LLOQ", "<0.1", "BLQ", "<LOD" 등 raw text 잔존 0개.` | universe_sm §6 BLQ_TOKEN |

#### 2.1.3 시간 (Time)

| ID | Predicate | Ref |
|----|-----------|-----|
| **L4-P03** | `모든 시간 값이 numeric type(elapsed hours/minutes) 또는 ISO datetime으로 파싱 완료되었다. clock/mixed/AM-PM raw string 잔존 0개.` | universe_sm §6 TIME_FORMAT |
| **L4-P04** | `Timezone offset이 단일 기준 시간대로 통일되었다. DST/12h-24h 모호성 0개.` | universe_sm §6 TIMEZONE |
| **L4-P05** | `Time anchor 토큰이 파싱 완료되었다 ("Day 1", "Visit 1", date string → comparable 수치형). 단, anchor 정책의 의미 해석(A3 axis evaluation)은 L-3에서 수행.` | universe_sm §6 TIME_ANCHOR |

#### 2.1.4 ID

| ID | Predicate | Ref |
|----|-----------|-----|
| **L4-P06** | `모든 ID 값이 균일 dtype(전부 integer 또는 전부 string)으로 통일되었다. string/int 혼재 0개. leading-zero 처리 완료("'001" → "001" 또는 1, 정책에 따라).` | universe_sm §6 ID_DTYPE |

#### 2.1.5 단위 (Unit)

| ID | Predicate | Ref |
|----|-----------|-----|
| **L4-P07** | `각 column의 단위가 식별·표기 표준화되었다. molar/mass 구분이 태깅되었다. MW 사전 부재로 변환 불가 시 Q10 routing 대상으로 플래그.` | universe_sm §6 UNIT_DECLARATION |

#### 2.1.6 셀 구조 (Cell Structure)

| ID | Predicate | Ref |
|----|-----------|-----|
| **L4-P08** | `병합 셀이 forward-fill로 해소되었다. 병합 잔존 0개.` | universe_sm §6 MERGED_CELL |
| **L4-P09** | `Multi-level header가 단일 행 header로 평탄화되었다.` | universe_sm §6 MULTI_LEVEL_HEADER |
| **L4-P10** | `Trailing blank row가 제거되었다. 마지막 data row 이후 빈 행 0개.` | universe_sm §6 TRAILING_BLANK |
| **L4-P11** | `완전중복 행(exact duplicate)이 식별·플래그되었다. (A5 REPLICATE-SAME-TIME과 구분: 동일 (ID,TIME)에 서로 다른 DV = replicate, 전체 행 일치 = duplicate.)` | universe_sm §6 DUPLICATE_ROW, §3 A5 P3 note |

#### 2.1.7 자연어 (Natural Language)

| ID | Predicate | Ref |
|----|-----------|-----|
| **L4-P12** | `자연어 dose 표현("100 mg", "two tablets")이 구조화 추출되었다: (numeric_amount, unit).` | universe_sm §6 NATURAL_LANGUAGE_DOSE |
| **L4-P13** | `자연어 time 표현("after 30 min", "predose")이 구조화 numeric time으로 추출되었다.` | universe_sm §6 NATURAL_LANGUAGE_TIME |
| **L4-P14** | `자유 코멘트 컬럼(freetext)이 data 컬럼과 격리되었다.` | universe_sm §6 FREETEXT_COMMENT |

#### 2.1.8 파일 (File Property)

| ID | Predicate | Ref |
|----|-----------|-----|
| **L4-P15** | `Character encoding = UTF-8. BOM 없음.` | universe_sm §6 ENCODING |
| **L4-P16** | `Line ending이 일관되게 정규화되었다 (LF 또는 CRLF). CR-only 없음.` | universe_sm §6 LINE_ENDING |
| **L4-P17** | `Delimiter가 comma로 표준화되었다.` | universe_sm §6 DELIMITER |
| **L4-P18** | `모든 sheet가 목록화(catalogued)되고 workspace에 로드되었다. 단, 도메인 수준 JOIN은 미수행 — sheet별 DataFrame이 개별 존재.` | universe_sm §6 SHEET_INVENTORY |

#### 2.1.9 Excel Artifact

| ID | Predicate | Ref |
|----|-----------|-----|
| **L4-P19** | `Formula 텍스트 잔존("=SUM(...)")이 평가 또는 제거되었다.` | universe_sm §6 EXCEL_FORMULA |
| **L4-P20** | `Excel date serial number(e.g., 43000)가 date 값으로 변환되었다.` | universe_sm §6 EXCEL_DATE_SERIAL |
| **L4-P21** | `소수점 = period. comma-as-decimal("1,5") 없음. 천단위 구분자("1,000") 해소.` | universe_sm §6 NON_ASCII_DECIMAL |
| **L4-P22** | `Scientific notation artifact("1E+3", "1*10^3")가 plain numeric으로 평가되었다.` | universe_sm §6 SCIENTIFIC_NOTATION |
| **L4-P23** | `셀 내 linebreak가 제거 또는 escape되었다.` | universe_sm §6 LINEBREAK_IN_CELL |

#### 2.1.10 레이아웃 (Layout)

| ID | Predicate | Ref |
|----|-----------|-----|
| **L4-P24** | `Covariate layout 타입(wide/long)이 식별되었다. 단, pivot 변형은 미수행 — 식별만 완료.` | universe_sm §6 COVARIATE_LAYOUT |

#### 2.1.11 도메인 (Domain)

| ID | Predicate | Ref |
|----|-----------|-----|
| **L4-P25** | `Pre-dose coding이 표준화되었다 (음수시간, "PRE" flag, t=0 중 정책에 따라 통일).` | universe_sm §6 PRE_DOSE_CODING |
| **L4-P26** | `Placebo subject가 식별되었다. AMT=0 vs dose 누락이 구분되었다.` | universe_sm §6 PLACEBO_SUBJECT |

### 2.2 Exit Postcondition

L-4.exit_post ≡ L-3.entry_pre. 아래 §3.1의 전체(L4-P01–P26 + L3-AX-01–AX-11).

### 2.3 Violations & Routing

| 위반 조건 | Routing | Ref |
|-----------|---------|-----|
| L4-P01–P26 중 하나라도 미충족 (= mess dimension 미해소) | 해당 dimension의 처리 c 재시도 또는 → Q15X (catch-all) | universe_sm §6, §4 Q15X |
| L4-P07 위반 중 MW 사전 부재 | → Q10 | universe_sm §4 Q10, P5 |

---

## 3. L-3 — Boundary (★ Universe A/B 이등분점)

### 3.1 Entry Precondition (= L-4.exit_post)

L-3 진입은 두 조건을 모두 충족해야 한다:

**(A) 모든 mess 해소:** L4-P01–P26 전부 true.

**(B) A0–A10 11개 axis 각각이 anchors.json의 유효 state 중 하나로 할당됨:**

| ID | Axis | Predicate | 유효 States (anchors.json) | Ref |
|----|------|-----------|---------------------------|-----|
| **L3-AX-01** | A0 Analysis Intent | `A0 ∈ {AIC-MISSING, AIC-PK, AIC-POPPK, AIC-PKPD, AIC-ER, AIC-DDI, AIC-PEDS, AIC-SPECIAL, AIC-CUSTOM}` | 9개 | universe_sm §3 A0 |
| **L3-AX-02** | A1 Study Integration | `A1 ∈ {SINGLE, MULTI-HOMO, MULTI-HETERO, MULTI-SITE, INTERIM}` | 5개 | universe_sm §3 A1 |
| **L3-AX-03** | A2 Study Design | `A2 ∈ {PARALLEL, SAD-MAD, CROSSOVER, BE, DDI, FOOD-EFFECT, SPECIAL-POP, PEDIATRIC, TDM-RWD, PRECLINICAL}` | 10개 | universe_sm §3 A2 |
| **L3-AX-04** | A3 Time Derivation | `A3 ∈ {ACTUAL, NOMINAL-ONLY, ACTUAL-PREFERRED, NOMINAL-PREFERRED, ELAPSED, INTERVAL, AMBIGUOUS, UNRECOVERABLE}` | 8개 | universe_sm §3 A3 |
| **L3-AX-05** | A4 Dose Completeness | `A4 ∈ {COMPLETE, WEIGHT-BASED, BSA-BASED, PLANNED-FALLBACK, ADDL-II, ADDL-ACTUAL-CONFLICT, TITRATION-ADAPTIVE, LOADING-MAINTENANCE, INFUSION-STOP-RESTART, PARTIAL-RECOVERY, COMBINATION, MISSING-NO-POLICY, UNRECOVERABLE}` | 13개 | universe_sm §3 A4 |
| **L3-AX-06** | A5 Observation/BLQ | `A5 ∈ {CLEAN, BLQ-FLAGGED, BLQ-TEXT, BLQ-ZERO, MULTI-ANALYTE, LLOQ-CHANGED, MISSING-MDV1, BIOANALYTICAL-FINAL-FLAG-MISSING, ABOVE-ULOQ, ABOVE-ULOQ-NO-POLICY, REPLICATE-SAME-TIME, REPLICATE-NO-POLICY, BLQ-NO-POLICY, LLOQ-MISSING, ABSENT}` | 15개 | universe_sm §3 A5 + P1, P3 |
| **L3-AX-07** | A6 Event Row Classification | `A6 ∈ {SEPARABLE, SAME-TIME-RESOLVABLE, COVARIATE-CHANGE, RESET-NEEDED, URINE-INTERVAL, AMBIGUOUS}` | 6개 | universe_sm §3 A6 |
| **L3-AX-08** | A7 Covariate Attachment | `A7 ∈ {NONE-REQUIRED, BASELINE-CLEAN, BASELINE-IMPUTABLE, TIME-VARYING, EXTERNAL-JOIN, PEDIATRIC-MATURATION, KEY-MISSING, POLICY-MISSING}` | 8개 | universe_sm §3 A7 |
| **L3-AX-09** | A8 Multi-Drug/CMT | `A8 ∈ {SINGLE-DRUG, MULTI-CMT-DEFINED, DDI-VICTIM-ONLY, DDI-VICTIM-PERPETRATOR, METABOLITE-DEFINED, CMT-POLICY-MISSING}` | 6개 | universe_sm §3 A8 + P2 |
| **L3-AX-10** | A9 Data Defect Repairability | `A9 ∈ {CLEAN, DUPLICATE-EXACT, UNSORTED, COLUMN-SYNONYM, UNIT-CONVERSION, ENCODING-FIX, PRE-DOSE-SAMPLE, PLANNED-VS-ACTUAL, PROTOCOL-DEVIATION, REANALYSIS-FINAL-DEFINED, REANALYSIS-FINAL-MISSING, PROTOCOL-DEVIATION-NO-POLICY, IRRECONCILABLE}` | 13개 | universe_sm §3 A9 |
| **L3-AX-11** | A10 Source Format | `A10 ∈ {SDTM-ADaM, EDC-STRUCTURED, CRO-VENDOR, FLAT-TABULAR, LEGACY-NM, SEMI-STRUCTURED, NON-TABULAR, CORRUPTED}` | 8개 | universe_sm §3 A10 |

### 3.2 Exit Postcondition

L-3.exit_post ≡ L-2.entry_pre. 아래 §4.1의 전체.

### 3.3 Violations & Routing

L-3에서 축 상태가 결정된 후, 특정 상태는 즉시 Q-code 또는 terminal로 routing된다. 이 routing은 universe_sm §2 N0–N7 골격을 따른다.

| Axis | 위반 State | Routing | Terminal | N-node | Ref |
|------|-----------|---------|----------|--------|-----|
| A0 | AIC-MISSING | Q11 | QUARANTINE | N0 | universe_sm §2 N0, §3 A0 |
| A1 | MULTI-* (harmonization policy 부재 시) | Q05 | QUARANTINE | — | universe_sm §3 A1 |
| A3 | AMBIGUOUS | Q02 | QUARANTINE | N2 | universe_sm §2 N2, §3 A3 |
| A3 | UNRECOVERABLE | — | INVALID | N2 | universe_sm §2 N2, §3 A3 |
| A4 | MISSING-NO-POLICY | Q08 | QUARANTINE | N3 | universe_sm §2 N3, §3 A4 |
| A4 | ADDL-ACTUAL-CONFLICT | Q14 | QUARANTINE | N3 | universe_sm §3 A4 |
| A4 | UNRECOVERABLE | — | INVALID | N3 | universe_sm §2 N3, §3 A4 |
| A5 | BLQ-NO-POLICY | Q01 | QUARANTINE | N5 | universe_sm §2 N5, §3 A5 |
| A5 | LLOQ-MISSING | Q01 | QUARANTINE | N5 | universe_sm §2 N5, §3 A5 |
| A5 | ABOVE-ULOQ-NO-POLICY | Q01 (subtype: uloq) | QUARANTINE | N5 | universe_sm §3 A5 P1 |
| A5 | REPLICATE-NO-POLICY | Q01 (subtype: replicate) | QUARANTINE | N5 | universe_sm §3 A5 P3 |
| A5 | BIOANALYTICAL-FINAL-FLAG-MISSING | Q15D | QUARANTINE | N4 | universe_sm §3 A5 |
| A5 | ABSENT | — | INVALID | N4 | universe_sm §2 N4, §3 A5 |
| A6 | AMBIGUOUS | Q04 | QUARANTINE | N2 | universe_sm §2 N2, §3 A6 |
| A7 | KEY-MISSING | Q13 | QUARANTINE | N6 | universe_sm §2 N6, §3 A7 |
| A7 | POLICY-MISSING | Q07 | QUARANTINE | N6 | universe_sm §2 N6, §3 A7 |
| A8 | CMT-POLICY-MISSING | Q09 | QUARANTINE | N4 | universe_sm §2 N4, §3 A8 |
| A9 | PROTOCOL-DEVIATION-NO-POLICY | Q06 | QUARANTINE | — | universe_sm §3 A9 |
| A9 | REANALYSIS-FINAL-MISSING | Q15D | QUARANTINE | — | universe_sm §3 A9 |
| A9 | IRRECONCILABLE | — | INVALID | — | universe_sm §3 A9 |

**Routing이 아닌 pass-through state:** 위 표에 없는 axis state(e.g., A0=AIC-PK, A4=COMPLETE, A5=CLEAN, A9=CLEAN 등)는 처리 가능(AUTO 또는 REPAIR)하며 L-2로 진행한다.

### 3.4 Bisection Note

L-3 아래(L-5→L-4→L-3)에서 수행되는 모든 작업은 **Universe B**: 토큰/파일/셀 수준 정규화로, 대부분 commutative(순서 무관)하다. L-3 위(L-3→L-2→L-1→L0)에서 수행되는 모든 작업은 **Universe A**: N0–N7 골격을 따르는 routing/분기 로직이다. 이 경계에서 axis state가 확정되므로, 상류의 모든 conditional 분기가 deterministic하게 결정된다.

---

## 4. L-2 — Tidy Long-Format

### 4.1 Entry Precondition (= L-3.exit_post)

L-3 전체(mess 해소 + axis 평가) 위에 **구조 변형**이 적용된 상태.

| ID | Predicate | Ref |
|----|-----------|-----|
| **L2-PRE-01** | `L4-P01–P26 모두 충족 (mess 전부 해소).` | universe_sm §6 (전체) |
| **L2-PRE-02** | `L3-AX-01–AX-11 모두 충족 (모든 axis state 결정됨).` | universe_sm §3 A0–A10 |
| **L2-PRE-03** | `One event per row: 각 행이 단일 event(단일 시점의 단일 dose 또는 단일 observation)를 나타낸다.` | tidy data 원칙 |
| **L2-PRE-04** | `One variable per column: 각 column이 단일 변수를 나타낸다. Multi-level header, 병합 셀, wide-format analyte 잔존 0개.` | tidy data 원칙, universe_sm §6 MULTI_LEVEL_HEADER (해소됨) |
| **L2-PRE-05** | `Multi-sheet source인 경우(A10 ∈ {SEMI-STRUCTURED 등}): 모든 sheet가 도메인 key 기반으로 단일 테이블에 JOIN 완료.` | universe_sm §3 A10, §6 SHEET_INVENTORY |
| **L2-PRE-06** | `Multi-analyte인 경우(A5 = MULTI-ANALYTE 또는 A8 ≠ SINGLE-DRUG): analyte column이 long format으로 PIVOT 완료. 각 행 = 단일 analyte의 단일 측정.` | universe_sm §3 A5, A8 |
| **L2-PRE-07** | `Covariate가 A7 policy에 따라 attach 완료. NONE-REQUIRED이면 해당 없음. BASELINE-CLEAN이면 baseline 값 merge. BASELINE-IMPUTABLE이면 imputation policy 적용. TIME-VARYING이면 시간대응 값 attach. EXTERNAL-JOIN이면 외부 table join 완료.` | universe_sm §2 N6, §3 A7 |
| **L2-PRE-08** | `Dose row와 observation row가 의미적으로 구별 가능하다: event_type 또는 동등한 semantic label이 존재하여 각 행이 dose/obs/covariate-change/reset 중 어디에 해당하는지 결정됨.` | universe_sm §2 N3, N4 |
| **L2-PRE-09** | `각 행에 subject identifier, time value, event type이 존재한다.` | universe_sm §2 N1, N2 |
| **L2-PRE-10** | `단위가 각 변수 column 내에서 일관되다. A9 UNIT-CONVERSION이 필요했다면 변환 적용 완료.` | universe_sm §3 A9, §6 UNIT_DECLARATION |

### 4.2 Exit Postcondition

L-2.exit_post ≡ L-1.entry_pre. 아래 §5.1의 전체.

### 4.3 Violations & Routing

| 위반 조건 | Routing | Ref |
|-----------|---------|-----|
| L2-PRE-05 위반: JOIN key 부재 | → Q13 (external covariate linkage key 모호) | universe_sm §4 Q13 |
| L2-PRE-06 위반: analyte PIVOT 실패 (CMT 정책 부재) | → Q09 (CMT assignment policy 없음) | universe_sm §4 Q09 |
| L2-PRE-07 위반: covariate attach 실패 (key 또는 policy 부재) | → Q07 또는 Q13 | universe_sm §4 Q07, Q13 |
| L2-PRE-08 위반: event type 구분 불가 (row 유형 모호) | → Q04 | universe_sm §4 Q04 |
| L2-PRE-09 위반: subject ID 구성 불가 | — (INVALID) | universe_sm §2 N1 |

---

## 5. L-1 — Pre-NONMEM

### 5.1 Entry Precondition (= L-2.exit_post)

L-2 전체(tidy long-format) 위에 **NONMEM 특수컬럼 부여 및 최종 검증**이 완료된 상태.

#### 5.1.1 NONMEM Core Column 부여

| ID | Predicate | Ref |
|----|-----------|-----|
| **L1-PRE-01** | `L2-PRE-01–PRE-10 모두 충족.` | §4 전체 |
| **L1-PRE-02** | `ID column: ∀ row: ID ∈ ℤ⁺ ∧ ID ≠ missing. 순수 정수, leading zero 없음.` | L0_nonmem_ready.md §A.1 ID, universe_sm §2 N1 |
| **L1-PRE-03** | `TIME column: ∀ row: TIME ∈ ℝ ∧ TIME ≠ missing. 단위 일관(hr 또는 min).` | L0_nonmem_ready.md §A.1 TIME, universe_sm §2 N2 |
| **L1-PRE-04** | `DV column: ∀ row: (EVID=0 ∧ MDV=0) ⟹ DV ∈ ℝ ∧ DV ≠ missing.` | L0_nonmem_ready.md §A.1 DV, universe_sm §2 N4 |
| **L1-PRE-05** | `EVID column: ∀ row: EVID ∈ {0, 1, 2, 3, 4}.` | L0_nonmem_ready.md §A.1 EVID, universe_sm §2 N3/N4 |
| **L1-PRE-06** | `MDV column: ∀ row: MDV ∈ {0, 1}. EVID ∈ {1,2,3,4} ⟹ MDV = 1.` | L0_nonmem_ready.md §A.1 MDV, I-R09 |
| **L1-PRE-07** | `AMT column: ∀ row: EVID ∈ {1,3,4} ⟹ AMT > 0. EVID ∈ {0,2} ⟹ AMT = 0 ∨ AMT = ".".` | L0_nonmem_ready.md §A.1 AMT, I-R06/I-R07 |
| **L1-PRE-08** | `CMT column: ∀ row: EVID ∈ {0,1,3,4} ⟹ CMT ∈ ℤ⁺. A8 policy 반영.` | L0_nonmem_ready.md §A.1 CMT, universe_sm §3 A8 + P2 |
| **L1-PRE-09** | `RATE column: ∀ row: RATE ∈ {0} ∪ ℝ⁺ ∪ {-1, -2}. RATE > 0 ⟹ AMT > 0. RATE ∈ {-1,-2} ⟹ EVID ∈ {1,3,4}.` | L0_nonmem_ready.md §A.1 RATE, I-R12/I-R13 |
| **L1-PRE-10** | `ADDL column: ∀ row: ADDL ∈ ℤ≥0.` | L0_nonmem_ready.md §A.1 ADDL |
| **L1-PRE-11** | `II column: ∀ row: (ADDL > 0 ⟹ II > 0) ∧ (II > 0 ⟹ ADDL > 0).` | L0_nonmem_ready.md §A.1 II, I-R10/I-R11 |

#### 5.1.2 Conditional Column 부여

| ID | Predicate | Ref |
|----|-----------|-----|
| **L1-PRE-12** | `BLQ_FLAG column (존재 시): ∀ row: BLQ_FLAG ∈ {0, 1}. BLQ_FLAG = 1 ⟹ EVID = 0.` | L0_nonmem_ready.md §A.2 BLQ_FLAG |
| **L1-PRE-13** | `LLOQ column (존재 시): ∀ row where EVID=0: LLOQ ∈ ℝ⁺. BLQ_FLAG=1 ⟹ LLOQ > 0.` | L0_nonmem_ready.md §A.2 LLOQ |

#### 5.1.3 Covariate Column 부여

| ID | Predicate | Ref |
|----|-----------|-----|
| **L1-PRE-14** | `분석 의도(A0)에서 선언한 모든 covariate가 column으로 존재. ∀ row: COV ∈ ℝ (numeric coding 완료). 결측 잔존 불허(imputation 또는 MDV=1 처리 완료).` | L0_nonmem_ready.md §A.3, universe_sm §2 N6 |

#### 5.1.4 Row Ordering 검증

| ID | Predicate | Ref |
|----|-----------|-----|
| **L1-PRE-15** | `∀ adjacent rows (i, i+1): ID[i] ≤ ID[i+1]. 동일 ID의 row는 연속(grouped).` | L0_nonmem_ready.md S-01, universe_sm §2 N1 |
| **L1-PRE-16** | `∀ adjacent rows (i, i+1) where ID[i] = ID[i+1]: TIME[i] ≤ TIME[i+1].` | L0_nonmem_ready.md S-02, universe_sm §2 N2 |
| **L1-PRE-17** | `동일 (ID, TIME)에서 dose event(EVID ∈ {1,3,4})가 observation(EVID=0)보다 선행.` | L0_nonmem_ready.md S-03, universe_sm §3 A6 SAME-TIME-RESOLVABLE |

#### 5.1.5 Cross-column Invariant 검증

| ID | Predicate | Ref |
|----|-----------|-----|
| **L1-PRE-18** | `Row-level invariants I-R01–I-R15 전부 충족.` | L0_nonmem_ready.md §B.1 |
| **L1-PRE-19** | `Dataset-level invariants I-D01–I-D07 전부 충족.` | L0_nonmem_ready.md §B.2 |

#### 5.1.6 Encoding/Format 검증

| ID | Predicate | Ref |
|----|-----------|-----|
| **L1-PRE-20** | `Encoding/format predicates E-01–E-11 전부 충족: CSV comma / period decimal / no comma in numeric / UTF-8 no BOM / single-row header / LF|CRLF / no trailing blank / no merged cell / no formula / no linebreak in cell / no scientific notation artifact.` | L0_nonmem_ready.md §D |

### 5.2 Exit Postcondition

**L-1.exit_post ≡ L0 entry predicate** = L0_nonmem_ready.md의 §A(Column Schema) + §B(Cross-column Invariants) + §C(Sorting) + §D(Encoding/Format) 전체.

따라서 L-1에서 L0로의 전환은 추가 transformation이 아니라 **검증(verification)**이다: L1-PRE-01–PRE-20이 모두 true이면 해당 dataset은 L0(NONMEM-ready)이다.

### 5.3 Violations & Routing

| 위반 조건 | Routing | Ref |
|-----------|---------|-----|
| L1-PRE-05 위반: EVID 부여 불가 (event type 모호) | → Q04 | universe_sm §4 Q04 |
| L1-PRE-08 위반: CMT 부여 불가 (CMT policy 부재) | → Q09 | universe_sm §4 Q09 |
| L1-PRE-14 위반: covariate 결측 처리 불가 (policy 부재) | → Q07 | universe_sm §4 Q07 |
| L1-PRE-15/16/17 위반: 정렬 불가 (시간 모호) | → Q02 또는 Q04 | universe_sm §4 Q02, Q04 |
| L1-PRE-18/19 위반: invariant 위반 (원인별 분기) | 원인에 따라 해당 Q-code 또는 INVALID | L0_nonmem_ready.md §B |

---

## 6. L0 — NONMEM-Ready (참조)

L0의 formal specification은 **spec/L0_nonmem_ready.md**에 정의되어 있다. 본 문서에서 재정의하지 않는다.

**L-1.exit_post ≡ L0 entry predicate** 확인:

| L0 Section | L-1 Predicate 대응 | 동일성 |
|------------|---------------------|--------|
| §A.1 Core Columns (ID, TIME, DV, MDV, EVID, AMT, CMT, RATE, ADDL, II) | L1-PRE-02–PRE-11 | ≡ |
| §A.2 Conditional Columns (BLQ_FLAG, LLOQ) | L1-PRE-12–PRE-13 | ≡ |
| §A.3 Covariate Columns | L1-PRE-14 | ≡ |
| §B.1 Row-level Invariants (I-R01–I-R15) | L1-PRE-18 | ≡ |
| §B.2 Dataset-level Invariants (I-D01–I-D07) | L1-PRE-19 | ≡ |
| §C Sorting (S-01–S-03) | L1-PRE-15–PRE-17 | ≡ |
| §D Encoding/Format (E-01–E-11) | L1-PRE-20 | ≡ |

---

## 7. 인접 Layer Transition 검증 표

각 인접 쌍에서 lower layer의 exit_post가 upper layer의 entry_pre와 동일함을 확인한다.

| 인접 쌍 | Lower.exit_post | Upper.entry_pre | 동일성 검증 |
|---------|-----------------|-----------------|-------------|
| **L-5 → L-4** | L-5.exit_post = "§6 26개 dimension 전부 해소" | L-4.entry_pre = L4-P01–P26 | ≡ §6 26개 dimension과 L4-P01–P26이 1:1 대응. |
| **L-4 → L-3** | L-4.exit_post = "L4-P01–P26 + A0–A10 axis 결정" | L-3.entry_pre = L4-P01–P26 + L3-AX-01–AX-11 | ≡ L3-AX-01–AX-11이 A0–A10 11개 axis를 전수 커버. |
| **L-3 → L-2** | L-3.exit_post = "L-3 전체 + 구조 변형 완료" | L-2.entry_pre = L2-PRE-01–PRE-10 | ≡ L2-PRE-01/02는 L-3 전체 포함, L2-PRE-03–10은 구조 변형 결과. |
| **L-2 → L-1** | L-2.exit_post = "L-2 전체 + NONMEM 컬럼 부여" | L-1.entry_pre = L1-PRE-01–PRE-20 | ≡ L1-PRE-01은 L-2 전체 포함, L1-PRE-02–20은 NONMEM 컬럼 + 검증. |
| **L-1 → L0** | L-1.exit_post = L0 predicates | L0.entry_pre = L0_nonmem_ready.md §A+B+C+D | ≡ §6 대응표 참조. |

### 7.1 Predicate 포함 관계 다이어그램

```
L0 predicates
  └── L-1.exit_post = L0_nonmem_ready.md §A+§B+§C+§D
      └── L-1.entry_pre = L1-PRE-01–20
          └── L-2.exit_post
              └── L-2.entry_pre = L2-PRE-01–10
                  └── L-3.exit_post
                      └── L-3.entry_pre = L4-P01–26 + L3-AX-01–11
                          └── L-4.exit_post
                              └── L-4.entry_pre = L4-P01–26
                                  └── L-5.exit_post
                                      └── L-5.entry_pre = L5-PRE-01–02
```

각 상위 layer의 entry_pre는 하위 layer의 exit_post를 **논리적으로 포함(⊇)**한다. 이는 파이프라인이 단조 증가(monotonically accumulating predicates)함을 보장한다.

---

## 8. Self-check

| # | 질문 | 판정 |
|---|------|------|
| 1 | 각 layer predicate가 binary(true/false) 판정 가능한가? | **Yes.** 모든 predicate는 "~이다" 또는 "~가 아니다"의 이항 술어로 기술됨. |
| 2 | 인접 layer exit_post ≡ entry_pre가 성립하는가? | **Yes.** §7 검증표에서 5개 인접쌍 모두 동일성 확인. |
| 3 | universe_sm §6 모든 dimension이 L-5→L-4에서 전수 커버되는가? | **Yes.** L4-P01–P26이 §6의 26개 dimension(NA_TOKEN, BLQ_TOKEN, TIME_FORMAT, TIME_ANCHOR, TIMEZONE, ID_DTYPE, UNIT_DECLARATION, MERGED_CELL, MULTI_LEVEL_HEADER, TRAILING_BLANK, DUPLICATE_ROW, NATURAL_LANGUAGE_DOSE, NATURAL_LANGUAGE_TIME, FREETEXT_COMMENT, ENCODING, LINE_ENDING, DELIMITER, SHEET_INVENTORY, EXCEL_FORMULA, EXCEL_DATE_SERIAL, NON_ASCII_DECIMAL, SCIENTIFIC_NOTATION, LINEBREAK_IN_CELL, COVARIATE_LAYOUT, PRE_DOSE_CODING, PLACEBO_SUBJECT)을 1:1 대응. |
| 4 | A0–A10 11개 axis가 L-4→L-3에서 전수 커버되는가? | **Yes.** L3-AX-01–AX-11이 A0–A10을 1:1 매핑. 모든 state는 anchors.json에서 검증. |
| 5 | [AMBIGUOUS] 태그 잔존 0개인가? | **Yes.** |
| 6 | 모든 인용이 anchors.json 식별자를 사용하는가? | **Yes.** 사용 axis state: A0–A10 전체 state set (anchors.json `axes` 일치). 사용 Q-code: Q01(+subtypes uloq, replicate), Q02, Q04, Q05, Q06, Q07, Q08, Q09, Q10, Q13, Q14, Q15D, Q15X (anchors.json `q_codes` 일치). 사용 terminal: AUTO, REPAIR, QUARANTINE, UNSUPPORTED, INVALID (anchors.json `terminals` 일치). |
| 7 | L0_nonmem_ready.md의 모든 predicate가 L-1.exit_post에 포함되는가? | **Yes.** §6 대응표에서 §A(L1-PRE-02–14), §B(L1-PRE-18–19), §C(L1-PRE-15–17), §D(L1-PRE-20)에 전수 대응. |
| 8 | c 정의 또는 sc 열거가 포함되어 있지 않은가? | **Yes.** 본 문서는 layer 경계의 predicate만 정의. 개별 c-단위체 정의 및 starting condition 열거 없음. |
