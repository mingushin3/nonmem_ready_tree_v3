# L0: NONMEM-Ready Dataset — Formal Specification

> **Version:** 0.1  
> **Scope:** modality = SMALL_MOLECULE; endpoint_data_type ∈ {PK_CONCENTRATION, EXPOSURE_METRIC, CONTINUOUS_PD}  
> **Canonical ref:** universe_sm.md v1.1 + anchors.json v1.1  
> **Purpose:** 임의 tabular dataset의 "NONMEM-ready" 여부를 binary(true/false)로 판정할 수 있는 formal predicate 집합.  
> **Non-scope:** $CONTROL stream, model structure, BLQ handling methodology 선택, covariate imputation methodology 선택은 본 spec 범위 밖. 여기서는 *data file 자체*의 구조·값 적합성만 판정한다.

---

## A. Column Schema

모든 predicate는 "이 column이 존재하고, 모든 row에서 아래 조건을 충족하는가?"로 binary 판정한다.

NONMEM은 `"."` 을 결측으로 읽는다(내부적으로 0 처리). 아래에서 `missing`은 `"."` 또는 field 부재를 의미한다.

### A.1 Core Required Columns

아래 10개 column은 **모든** NONMEM-ready dataset에 존재해야 한다.

#### ID — Subject Identifier

| 항목 | 정의 |
|------|------|
| **Type** | integer |
| **Domain** | ℤ⁺ (양의 정수). Dataset 내에서 한 subject = 하나의 ID 값. |
| **Missing** | 불허. 모든 row에 ID 값 존재. |
| **Format** | 순수 숫자. 최종 출력에 leading zero·문자열 접두사 없음. |
| **Predicate** | `∀ row: ID ∈ ℤ⁺ ∧ ID ≠ missing` |
| **Ref** | universe_sm §2 N1 "Subject-level ID를 안정적으로 구성할 수 있는가?" |

#### TIME — Event Time

| 항목 | 정의 |
|------|------|
| **Type** | numeric (실수) |
| **Domain** | ℝ. 일반적으로 ≥0이나, pre-dose sample 등 분석 정책(A3 TIME_ANCHOR)에 따라 음수 허용. 단위는 dataset 내 일관(시간 또는 분). |
| **Missing** | 불허. 모든 row에 TIME 값 존재. |
| **Format** | decimal (period 소수점). 정수·소수 모두 가. |
| **Predicate** | `∀ row: TIME ∈ ℝ ∧ TIME ≠ missing` |
| **Ref** | universe_sm §2 N2 "시간순 event sequence 구성 가능?", §3 A3 TIME_DERIVATION |

#### DV — Dependent Variable

| 항목 | 정의 |
|------|------|
| **Type** | numeric (실수) 또는 `"."` (NONMEM missing) |
| **Domain** | EVID=0 ∧ MDV=0 일 때: 유효한 측정값. endpoint_data_type=PK_CONCENTRATION이면 DV≥0(농도는 비음수). CONTINUOUS_PD이면 ℝ(변화량 가능). MDV=1 일 때: 값 무제약(NONMEM이 무시하므로 0, ".", 임의 placeholder 가). |
| **Missing** | column은 반드시 존재. EVID=0 ∧ MDV=0인 row에서 DV missing 불허. |
| **Format** | numeric 또는 `"."`. |
| **Predicate** | `∀ row: (EVID=0 ∧ MDV=0) ⟹ DV ∈ ℝ ∧ DV ≠ missing` |
| **Ref** | universe_sm §2 N4 "Observation records 완성 가능?", §3 A5 OBSERVATION_COMPLETENESS |

#### MDV — Missing Dependent Variable Flag

| 항목 | 정의 |
|------|------|
| **Type** | integer |
| **Domain** | {0, 1}. 0 = DV를 estimation에 사용. 1 = DV를 무시(dose record, BLQ flag, 결측 등). |
| **Missing** | 불허. 모든 row에 MDV 값 존재. |
| **Format** | `0` 또는 `1`. |
| **Predicate** | `∀ row: MDV ∈ {0, 1}` |
| **Ref** | universe_sm §2 N5 "BLQ/missing/MDV 처리 가능?" |

#### EVID — Event ID

| 항목 | 정의 |
|------|------|
| **Type** | integer |
| **Domain** | {0, 1, 2, 3, 4} (NONMEM 표준). |

| EVID | 의미 | AMT | DV 사용 |
|------|------|-----|---------|
| 0 | observation | 0 또는 `.` | MDV에 따름 |
| 1 | dose | >0 | 아니오 |
| 2 | other-type event (compartment reset) | 0 또는 `.` | 아니오 |
| 3 | reset + dose | >0 | 아니오 |
| 4 | reset + turn-off + dose | >0 | 아니오 |

SM PK 실무에서 대다수 row는 EVID ∈ {0, 1}. EVID=4는 steady-state 처리, EVID=2는 covariate-change record, EVID=3는 washout 후 재투약에 쓰인다.

| 항목 | 정의 |
|------|------|
| **Missing** | 불허. 모든 row에 EVID 값 존재. |
| **Format** | 정수 `0`–`4`. |
| **Predicate** | `∀ row: EVID ∈ {0, 1, 2, 3, 4}` |
| **Ref** | universe_sm §2 N3 "Dose records 완성 가능?", §2 N4 "Observation records 완성 가능?" |

#### AMT — Dose Amount

| 항목 | 정의 |
|------|------|
| **Type** | numeric (실수 ≥0) 또는 `"."` |
| **Domain** | dose event (EVID ∈ {1, 3, 4}): AMT > 0. non-dose event (EVID ∈ {0, 2}): AMT = 0 또는 `"."`. |
| **Missing** | dose event에서 불허. non-dose event에서 0 또는 `.` |
| **Format** | numeric. 단위는 dataset 내 일관(mg, µg 등). |
| **Predicate** | `∀ row: EVID ∈ {1,3,4} ⟹ AMT > 0` ∧ `EVID ∈ {0,2} ⟹ AMT = 0 ∨ AMT = "."` |
| **Ref** | universe_sm §2 N3, §3 A4 DOSE_COMPLETENESS |

#### CMT — Compartment Number

| 항목 | 정의 |
|------|------|
| **Type** | integer |
| **Domain** | ℤ⁺ (1 이상). 분석 모델의 compartment 번호 매핑. |
| **Missing** | dose event (EVID ∈ {1, 3, 4})에서 불허 — 투여 compartment 명시 필수. observation (EVID = 0)에서도 정의되어야 함 — 관측 compartment 명시. EVID = 2에서는 context-dependent(reset 대상 compartment). |
| **Format** | 양의 정수. |
| **Predicate** | `∀ row: EVID ∈ {0, 1, 3, 4} ⟹ CMT ∈ ℤ⁺` |
| **Ref** | universe_sm §3 A8 "Multi-Drug / CMT Assignment" |

#### RATE — Infusion Rate

| 항목 | 정의 |
|------|------|
| **Type** | numeric |
| **Domain** | `0` = bolus (즉시 투여). `>0` = zero-order infusion rate (AMT/TIME 단위, e.g., mg/hr). `-1` = NONMEM model-estimated rate (D# 필요). `-2` = NONMEM model-estimated duration (D# 필요). |
| **Missing** | 불허. 미입력 시 0 (bolus default). |
| **Format** | numeric. |
| **Predicate** | `∀ row: RATE ∈ {0} ∪ ℝ⁺ ∪ {-1, -2}` ∧ `RATE > 0 ⟹ AMT > 0` ∧ `RATE ∈ {-1,-2} ⟹ EVID ∈ {1,3,4}` |
| **Ref** | universe_sm §3 A4 (INFUSION-STOP-RESTART state) |

#### ADDL — Additional Doses

| 항목 | 정의 |
|------|------|
| **Type** | integer |
| **Domain** | ℤ≥0. `0` = 추가 투여 없음. `n>0` = 현 dose 이후 II 간격으로 n회 추가 투여. |
| **Missing** | 불허. 미입력 시 0. |
| **Format** | 비음수 정수. |
| **Predicate** | `∀ row: ADDL ∈ ℤ≥0` |
| **Ref** | universe_sm §3 A4 (ADDL-II state) |

#### II — Inter-dose Interval

| 항목 | 정의 |
|------|------|
| **Type** | numeric |
| **Domain** | `>0` when ADDL > 0. `0` when ADDL = 0. TIME과 동일 단위. |
| **Missing** | 불허. 미입력 시 0. |
| **Format** | numeric (비음수). |
| **Predicate** | `∀ row: (ADDL > 0 ⟹ II > 0) ∧ (II > 0 ⟹ ADDL > 0)` |
| **Ref** | universe_sm §3 A4 (ADDL-II state) |

### A.2 Conditional Columns

아래 column은 분석 context에 따라 존재 여부가 결정된다. 존재할 때 아래 predicate를 충족해야 한다.

#### BLQ_FLAG — Below Limit of Quantification Flag

**존재 조건:** 연구에 BLQ observation이 있고, BLQ handling methodology가 explicit flag를 요구할 때 (e.g., M3/M4 likelihood method). M1(exclusion) 또는 M5(LLOQ/2 substitution) 적용 시에는 column 부재 허용.

| 항목 | 정의 |
|------|------|
| **Type** | integer |
| **Domain** | {0, 1}. 0 = not BLQ. 1 = BLQ. |
| **Missing** | 불허 (column 존재 시). 미입력 시 0. |
| **Format** | `0` 또는 `1`. |
| **Predicate** | `column 존재 시: ∀ row: BLQ_FLAG ∈ {0, 1}` ∧ `BLQ_FLAG = 1 ⟹ EVID = 0` |
| **Ref** | universe_sm §3 A5, §2 N5 |

#### LLOQ — Lower Limit of Quantification

**존재 조건:** BLQ handling methodology가 LLOQ 값 참조를 요구할 때 (e.g., M3 conditional likelihood). BLQ 없는 연구이거나 substitution method 적용 시에는 column 부재 허용.

| 항목 | 정의 |
|------|------|
| **Type** | numeric |
| **Domain** | ℝ⁺ (>0). analyte·assay별 값. study 중 LLOQ 변경 시(A5 LLOQ-CHANGED) 해당 시점에 맞는 값. |
| **Missing** | column 존재 시, EVID=0인 row에서 불허. |
| **Format** | numeric (양수). |
| **Predicate** | `column 존재 시: ∀ row where EVID=0: LLOQ ∈ ℝ⁺` ∧ `BLQ_FLAG=1 ⟹ LLOQ ∈ ℝ⁺` |
| **Ref** | universe_sm §3 A5 (LLOQ-MISSING → Q01), §4 Q01 |

### A.3 Covariate Columns

분석 의도(A0)에서 선언한 covariate는 dataset column으로 존재해야 한다.

| 항목 | 정의 |
|------|------|
| **Type** | numeric. 연속형은 실수, 범주형은 정수 코딩 (e.g., SEX: 0=male, 1=female). |
| **Domain** | 도메인 특이적 (WT>0, AGE≥0, CRCL≥0 등). |
| **Missing** | 분석 정책(A7)에 따라 처리 완료 상태. 결측 잔존 불허 — imputation 또는 flag 후 MDV=1 처리 완료. |
| **Format** | numeric. 문자열 범주값은 정수 코딩 필수. |
| **Predicate** | `∀ declared covariate COV: COV column 존재` ∧ `∀ row: COV ∈ ℝ ∨ COV = "."(정책상 허용 시)` |
| **Ref** | universe_sm §2 N6 "공변량 attach 가능?", §3 A7 COVARIATE_ATTACHMENT |

### A.4 Additional Columns

Core/conditional/covariate 외 추가 column(e.g., STUD, OCC, TAD, FLAG)은 허용된다. 추가 column의 존재 자체는 NONMEM-ready 판정에 영향하지 않는다. 단, 추가 column이 core column 값과 모순(e.g., TAD와 TIME 불일치)되면 dataset 자체의 일관성 위반이다.

---

## B. Cross-column Invariants

모든 invariant는 `true`/`false`로 판정 가능한 formal predicate다.

### B.1 Row-level Invariants (∀ row 적용)

| ID | Predicate | 위반 의미 | Ref |
|----|-----------|-----------|-----|
| **I-R01** | `ID ∈ ℤ⁺ ∧ ID ≠ missing` | ID 부재/비정수 | §2 N1 |
| **I-R02** | `TIME ∈ ℝ ∧ TIME ≠ missing` | TIME 부재/비숫자 | §2 N2 |
| **I-R03** | `EVID ∈ {0, 1, 2, 3, 4}` | 유효하지 않은 event type | §2 N3, N4 |
| **I-R04** | `MDV ∈ {0, 1}` | 유효하지 않은 MDV | §2 N5 |
| **I-R05** | `EVID = 0 ∧ MDV = 0 ⟹ DV ∈ ℝ ∧ DV ≠ missing` | 유효 observation인데 DV 부재 | §2 N4 |
| **I-R06** | `EVID ∈ {1, 3, 4} ⟹ AMT > 0 ∧ CMT ∈ ℤ⁺` | dose record인데 AMT 또는 CMT 부재 | §2 N3 |
| **I-R07** | `EVID ∈ {0, 2} ⟹ AMT = 0 ∨ AMT = "."` | 비투여 record인데 AMT > 0 | §2 N3, N4 |
| **I-R08** | `AMT > 0 ⟹ EVID ∈ {1, 3, 4}` | AMT 양수인데 dose event 아님 (I-R07의 대우) | §2 N3 |
| **I-R09** | `EVID ∈ {1, 2, 3, 4} ⟹ MDV = 1` | 비관측 record인데 MDV=0 | §2 N3, N4, N5 |
| **I-R10** | `ADDL > 0 ⟹ II > 0` | 반복투여인데 간격 미정 | §3 A4 |
| **I-R11** | `II > 0 ⟹ ADDL > 0` | 간격 지정인데 반복 횟수 없음 | §3 A4 |
| **I-R12** | `RATE > 0 ⟹ AMT > 0` | infusion rate 양수인데 투여량 없음 | §3 A4 |
| **I-R13** | `RATE ∈ {-1, -2} ⟹ EVID ∈ {1, 3, 4}` | model-estimated rate/duration이 dose event가 아닌 row에 존재 | §3 A4 |
| **I-R14** | `BLQ_FLAG = 1 ⟹ LLOQ ∈ ℝ⁺ ∧ LLOQ > 0` (BLQ_FLAG, LLOQ column 존재 시) | BLQ인데 LLOQ 정의 안 됨 | §3 A5, §4 Q01 |
| **I-R15** | `EVID = 0 ∧ MDV = 0 ∧ endpoint = PK_CONCENTRATION ⟹ DV ≥ 0` | PK 농도가 음수 | §3 A5 |

### B.2 Dataset-level Invariants (전체 dataset 적용)

| ID | Predicate | 위반 의미 | Ref |
|----|-----------|-----------|-----|
| **I-D01** | `∃ row: EVID = 0 ∧ MDV = 0` | dataset 전체에 유효 observation 0개 | §2 N4 (ABSENT → INVALID) |
| **I-D02** | 첫 행(row 1)은 column header이며, §A에 정의된 모든 required column name 포함 | header 부재 또는 필수 column 누락 | §6 MULTI_LEVEL_HEADER (해소됨) |
| **I-D03** | `∀ ID value v in dataset: COUNT(rows where ID=v) ≥ 1` | 고아 ID 참조 없음 (자명, ID가 row에 있으므로 항상 true — 외부 reference와의 일관성 체크 목적) | §2 N1 |
| **I-D04** | 분석 의도(A0)에서 선언한 모든 covariate가 column으로 존재하고, 모든 row에서 numeric | 선언된 covariate 부재 | §2 N6, §3 A7 |
| **I-D05** | `∀ ID: (분석 의도에 dosing 포함) ⟹ ∃ row where ID=v ∧ EVID ∈ {1,3,4}` — 또는 subject가 dose-only/placebo 정책에 의해 면제 | PK 분석인데 특정 subject에 dose 기록 없음 | §2 N3 |
| **I-D06** | TIME, AMT, II의 단위가 dataset 내 일관 (혼재 불가) | 단위 혼재 | §3 A4, §6 UNIT_DECLARATION |
| **I-D07** | 모든 numeric field가 period (`.`) 소수점 사용, comma 소수점 없음 | 소수점 표기 불일치 | §6 NON_ASCII_DECIMAL |

---

## C. Sorting

모든 sort predicate는 dataset의 행 순서에 대해 binary 판정 가능하다.

| ID | Predicate | Ref |
|----|-----------|-----|
| **S-01** | `∀ adjacent rows (i, i+1): ID[i] ≤ ID[i+1]` — ID는 ascending. 동일 ID의 row는 연속 (grouped). | §2 N1 |
| **S-02** | `∀ adjacent rows (i, i+1) where ID[i] = ID[i+1]: TIME[i] ≤ TIME[i+1]` — 동일 subject 내 TIME ascending. | §2 N2, §3 A3 |
| **S-03** | `∀ rows (i, j) where ID[i]=ID[j] ∧ TIME[i]=TIME[j] ∧ i < j: EVID[i] ≥ EVID[j] 이되, 구체적으로 dose event(EVID∈{1,3,4})가 observation(EVID=0)보다 선행` — 동시각 tiebreak: dose before obs. | §3 A6 (SAME-TIME-RESOLVABLE) |

**S-03 정밀화:** 동일 (ID, TIME)에서 EVID가 dose(1,3,4)와 observation(0) 모두 있으면, dose row가 먼저 온다. 같은 type끼리의 상대 순서는 무관.

---

## D. Encoding / Format

각 항목은 file 수준에서 binary 판정 가능하다.

| ID | Predicate | Ref |
|----|-----------|-----|
| **E-01** | file format = CSV (comma-separated values). delimiter = `,` (comma). | §6 DELIMITER |
| **E-02** | decimal separator = `.` (period). `,` 를 소수점으로 사용하지 않음. | §6 NON_ASCII_DECIMAL |
| **E-03** | numeric field 내부에 comma 없음 (천단위 구분자 금지). | §6 NON_ASCII_DECIMAL |
| **E-04** | character encoding = UTF-8. BOM (Byte Order Mark) 없음. | §6 ENCODING |
| **E-05** | 첫 행 = column header (single-row, flat). multi-level header 없음. | §6 MULTI_LEVEL_HEADER (해소됨) |
| **E-06** | line ending = LF 또는 CRLF. file 내 일관. CR-only 불허. | §6 LINE_ENDING |
| **E-07** | trailing blank row 없음. 마지막 data row 이후 빈 행 0개. | §6 TRAILING_BLANK |
| **E-08** | merged cell 없음 (CSV이므로 구조적으로 불가하나, Excel→CSV 변환 잔재 검증). | §6 MERGED_CELL |
| **E-09** | embedded formula 없음. `=` 로 시작하는 cell 없음. | §6 EXCEL_FORMULA |
| **E-10** | cell 내 linebreak 없음. 모든 field는 single-line. | §6 LINEBREAK_IN_CELL |
| **E-11** | numeric field에 scientific notation artifact 없음. `1E+3`, `1*10^3` 등은 실수로 평가 완료 상태(e.g., `1000`). NONMEM은 `1E3` 형식을 읽을 수 있으나, 본 spec은 해소 완료를 요구. | §6 SCIENTIFIC_NOTATION |

**E-11 보충:** NONMEM은 Fortran-style scientific notation(`1.23E+02`)을 정상 파싱한다. 본 항목은 "의도치 않은 Excel artifact"(문자열 `1E+3`이 text로 남는 경우)의 부재를 요구하는 것이며, 정규 scientific notation으로 의도적 기재된 값은 valid하다. 판정 기준: 해당 field를 floating-point로 파싱 시 올바른 수치가 되는가?

---

## E. Ambiguous Items

> 목표: 0개. 아래는 검토 후 해소한 후보 항목.

### 해소 완료

| 후보 | 판정 | 근거 |
|------|------|------|
| TIME이 음수일 수 있는가? | **허용.** pre-dose sample은 TIME < 0 가능. domain은 ℝ. | A3 TIME_DERIVATION: PRE-DOSE-SAMPLE은 valid coding. TIME_ANCHOR 정책이 음수 시간을 정의하면 합법. |
| Dose row의 DV 값 제약? | **무제약.** EVID ∈ {1,2,3,4}이면 MDV=1(I-R09)이므로 NONMEM이 DV를 무시. 값은 0, `.`, placeholder 모두 가능. | NONMEM documentation: MDV=1이면 DV 미참조. |
| EVID=2, 3 사용 가능? | **허용.** NONMEM standard {0,1,2,3,4} 전부 valid. SM PK에서 EVID=2(covariate-change/reset), EVID=3(washout 후 재투여)는 드물지만 합법. | NONMEM PREDPP documentation. |
| Scientific notation 허용? | **조건부 허용.** floating-point 파싱 가능한 정규 표기(e.g., `1.23E+02`)는 valid. Excel artifact로 text 잔존한 경우만 reject. | E-11 보충 참조. |
| Obs-only dataset(dose record 없음)? | **허용(제한적).** AIC-ER + EXPOSURE_METRIC 의도에서 exposure가 pre-computed covariate이면 EVID=1 row 불필요. 이 경우 I-D05 면제. | universe_sm §2 N3 "불필요(obs-only intent)" 분기. |

**잔존 ambiguity: 0개.**

---

## F. Self-check

| # | 질문 | 판정 |
|---|------|------|
| 1 | 이 문서만으로 임의 dataset의 NONMEM-ready 여부를 binary 판정 가능한가? | **Yes.** §A column 존재·type·domain, §B invariant, §C sorting, §D encoding — 각각 row/dataset/file 수준에서 true/false 평가 가능. |
| 2 | [AMBIGUOUS] 태그 잔존 0개인가? | **Yes.** §E에서 5개 후보 모두 해소. |
| 3 | 모든 invariant가 universe_sm.md section을 인용하는가? | **Yes.** I-R01~I-R15, I-D01~I-D07, S-01~S-03, E-01~E-11 모두 Ref column 기재. |
| 4 | anchors.json 식별자만 사용하는가? | **Yes.** 사용한 식별자: terminal(AUTO/REPAIR/QUARANTINE/INVALID), axis state(A3~A8 참조), Q-code(Q01 참조), endpoint_data_type(PK_CONCENTRATION/EXPOSURE_METRIC/CONTINUOUS_PD). 모두 anchors.json v1.1에 등록. |
