# Controlled Vocabulary — c-단위체 srp_intent 작명 규칙

> **Version:** 0.1  
> **Scope:** modality = SMALL_MOLECULE; endpoint_data_type ∈ {PK_CONCENTRATION, EXPOSURE_METRIC, CONTINUOUS_PD}  
> **Canonical ref:** universe_sm.md v1.1, anchors.json v1.1, layers.md v0.1, L0_nonmem_ready.md v0.1  
> **Purpose:** Phase 2a–2d에서 정의하는 모든 c-단위체의 `srp_intent` 필드를 구성하는 통제 어휘(controlled vocabulary)를 정의한다.  
> **Non-scope:** 개별 c-단위체 정의, srp_intent 인스턴스 열거는 본 문서 범위 밖.

---

## 0. srp_intent 구성 규칙

### 0.1 형식

```
srp_intent ::= "{VERB} {NOUN}"
             | "{VERB} {NOUN} BY {MODIFIER}"
```

- **전부 대문자 + underscore.** 한글·자유 서술 ZERO.
- `c_name_ko`는 별개 필드(사람 가독 한글 라벨, 자유 형식).

### 0.2 예시

| srp_intent | c_name_ko (별개) |
|---|---|
| `ASSIGN EVID` | EVID 부여 |
| `DETECT BLQ_TOKEN` | BLQ 토큰 패턴 감지 |
| `NORMALIZE NA_TOKEN` | 결측 토큰 정규화 |
| `VERIFY ROW_ORDERING BY WITHIN_ID` | subject 내 시간순 검증 |
| `PIVOT ANALYTE_COLUMN` | 분석물질 wide→long 변환 |
| `JOIN DOSE_SHEET BY ACROSS_SHEET` | 투약 시트 결합 |
| `CONVERT ENCODING` | 인코딩 변환 |
| `ROUTE CROSS_COLUMN_INVARIANT` | invariant 위반 시 Q-code 라우팅 |

### 0.3 규칙

1. 하나의 c-단위체 = 하나의 srp_intent (SRP, Lock 2).
2. VERB·NOUN·MODIFIER는 본 문서에 정의된 것만 사용. 신규 필요 시 STOP+보고.
3. 동일 srp_intent의 c가 복수 존재 가능(layer_pair가 다르거나, BY modifier가 다르면 구분).
4. NOUN 카테고리를 혼합하는 srp_intent는 허용하되, VERB의 SRP 경계를 벗어나지 않아야 한다.

---

## A. VERBS (13, closed set — 추가 금지)

### 설계 결정

- **★ IMPUTE 제외:** 임의 결측 보충은 silent error 원천. 결측은 DETECT(감지) → FILTER(FLAG) → 정책 문서 기반 처리(ASSIGN/NORMALIZE). 자의적 IMPUTE 금지.
- **★ FILTER = 조건부 FLAG:** row를 삭제(drop/exclude)하지 않는다. FLAG 컬럼을 부여하여 NONMEM의 IGNORE/ACCEPT이 최종 결정하도록 위임한다.

### VERB 정의

#### V01. ASSIGN

| 항목 | 내용 |
|------|------|
| **정의** | 대상 column/field에 특정 값을 부여한다. |
| **SRP 경계** | 값 결정 로직 + 기입. 값의 발견·감지는 DETECT, 기준 판정은 VERIFY 소관. |
| **kind 친화** | transform |
| **layer 친화** | L-1↔L-2 (NONMEM column 부여), L-2↔L-3 (covariate attach 등) |
| **cost** | 2 |
| **전형 pairing** | ASSIGN EVID, ASSIGN MDV, ASSIGN CMT, ASSIGN RATE, ASSIGN ADDL, ASSIGN II, ASSIGN ROW_ORDERING, ASSIGN BASELINE_COVARIATE |

#### V02. VERIFY

| 항목 | 내용 |
|------|------|
| **정의** | 주어진 조건(predicate)이 데이터에서 충족되는지 검증하고 pass/fail을 판정한다. |
| **SRP 경계** | 검증만. 실패 시 수정은 별도 transform c 또는 Q-code routing이 담당. |
| **kind 친화** | verify |
| **layer 친화** | 모든 layer pair (경계마다 exit_post 검증) |
| **cost** | 1 |
| **전형 pairing** | VERIFY ROW_ORDERING BY WITHIN_ID, VERIFY CROSS_COLUMN_INVARIANT, VERIFY ROW_LEVEL_INVARIANT |

#### V03. CONVERT

| 항목 | 내용 |
|------|------|
| **정의** | 값의 타입이나 형식을 다른 타입/형식으로 변환한다. |
| **SRP 경계** | 형식 변환만. 값의 의미 해석·범주 분류는 CLASSIFY/DETECT 소관. |
| **kind 친화** | transform |
| **layer 친화** | L-4↔L-5 (encoding, dtype, date serial 등) |
| **cost** | 2 |
| **전형 pairing** | CONVERT ENCODING, CONVERT ID_DTYPE, CONVERT EXCEL_DATE_SERIAL, CONVERT TIME_FORMAT, CONVERT UNIT_CANONICAL |

#### V04. NORMALIZE

| 항목 | 내용 |
|------|------|
| **정의** | 동일 의미의 다양한 표현을 단일 canonical form으로 통일한다. |
| **SRP 경계** | 정규화만. 어떤 변종이 존재하는지 감지하는 것은 DETECT, canonical form이 올바른지 확인하는 것은 VERIFY 소관. |
| **kind 친화** | transform |
| **layer 친화** | L-4↔L-5 (NA token, timezone, leading zero 등) |
| **cost** | 2 |
| **전형 pairing** | NORMALIZE NA_TOKEN, NORMALIZE TIMEZONE, NORMALIZE ID_LEADING_ZERO, NORMALIZE NON_ASCII_DECIMAL, NORMALIZE LINE_ENDING |

#### V05. JOIN

| 항목 | 내용 |
|------|------|
| **정의** | 두 개 이상의 table/sheet를 공통 key 기반으로 결합한다. |
| **SRP 경계** | 결합만. key 식별·유효성 검증은 VERIFY/DETECT 소관. key 부재 시 Q13 routing은 ROUTE 소관. |
| **kind 친화** | transform |
| **layer 친화** | L-2↔L-3 (multi-sheet join, covariate attach) |
| **cost** | 4–5 |
| **전형 pairing** | JOIN DOSE_SHEET BY ACROSS_SHEET, JOIN COVARIATE_SHEET BY ACROSS_SHEET, JOIN BASELINE_COVARIATE |

#### V06. SPLIT

| 항목 | 내용 |
|------|------|
| **정의** | 하나의 컬럼 또는 셀을 여러 구성요소로 분리한다. |
| **SRP 경계** | 분리만. 분리 기준·패턴 식별은 DETECT 소관. |
| **kind 친화** | transform |
| **layer 친화** | L-4↔L-5 (freetext 분리, multi-level header 해체 등) |
| **cost** | 4–5 |
| **전형 pairing** | SPLIT FREETEXT_COMMENT, SPLIT MULTI_LEVEL_HEADER |

#### V07. PIVOT

| 항목 | 내용 |
|------|------|
| **정의** | wide format ↔ long format 간 변환을 수행한다. |
| **SRP 경계** | pivot 변환만. pivot 필요 여부 결정은 DETECT/CLASSIFY 소관. |
| **kind 친화** | transform |
| **layer 친화** | L-2↔L-3 (analyte wide→long, covariate layout 변환) |
| **cost** | 4–5 |
| **전형 pairing** | PIVOT ANALYTE_COLUMN, PIVOT COVARIATE_LAYOUT |

#### V08. FILTER

| 항목 | 내용 |
|------|------|
| **정의** | 조건에 따라 행을 FLAG한다. **★ 행 삭제(drop/exclude)가 아님.** |
| **SRP 경계** | flag 부여만. flag 기준 결정은 DETECT/VERIFY 소관. 실제 row exclusion은 NONMEM의 IGNORE/ACCEPT이 최종 결정. |
| **kind 친화** | transform |
| **layer 친화** | 모든 layer pair |
| **cost** | 2 |
| **전형 pairing** | FILTER DUPLICATE_ROW, FILTER PLACEBO_SUBJECT, FILTER TRAILING_BLANK |

#### V09. DETECT

| 항목 | 내용 |
|------|------|
| **정의** | 특정 결함이나 패턴의 존재를 감지한다. |
| **SRP 경계** | 감지만. 감지된 결함의 수정은 별도 transform c가 담당. **★ D-S1: 모든 fix-c(transform)의 필수 선행 조건.** |
| **kind 친화** | detect |
| **layer 친화** | L-3↔L-4 (axis 평가), L-4↔L-5 (mess 감지) |
| **cost** | 1 |
| **전형 pairing** | DETECT BLQ_TOKEN, DETECT NA_TOKEN, DETECT MERGED_CELL, DETECT ENCODING, DETECT TIME_FORMAT, DETECT ABOVE_ULOQ, DETECT REPLICATE_OBS |

#### V10. PROPAGATE

| 항목 | 내용 |
|------|------|
| **정의** | 값을 인접 행/셀로 전파한다 (forward-fill, carry-forward 등). |
| **SRP 경계** | 전파만. 전파 대상·방향 결정은 DETECT 소관. |
| **kind 친화** | transform |
| **layer 친화** | L-4↔L-5 (merged cell forward-fill 등) |
| **cost** | 3 |
| **전형 pairing** | PROPAGATE MERGED_CELL, PROPAGATE BASELINE_COVARIATE BY WITHIN_ID |

#### V11. CLASSIFY

| 항목 | 내용 |
|------|------|
| **정의** | 데이터를 미리 정의된 범주(axis state, analyte type, covariate type 등)로 분류한다. |
| **SRP 경계** | 분류만. 분류 기준은 universe_sm에 정의. 분류 결과에 따른 변환은 별도 transform c 소관. |
| **kind 친화** | detect 또는 transform (분류가 감지 역할을 겸하는 경우) |
| **layer 친화** | L-3↔L-4 (axis 평가 = A0–A10 state 분류) |
| **cost** | 3 |
| **전형 pairing** | CLASSIFY ANALYTE_COLUMN, CLASSIFY COVARIATE_LAYOUT, CLASSIFY METABOLITE |

#### V12. EXTRACT

| 항목 | 내용 |
|------|------|
| **정의** | 비구조화 데이터(자연어, 혼합 셀 등)에서 구조화된 값을 추출한다. |
| **SRP 경계** | 추출만. 추출 대상 식별은 DETECT 소관. 추출 결과의 정규화는 NORMALIZE 소관. |
| **kind 친화** | transform |
| **layer 친화** | L-4↔L-5 (natural language dose/time, freetext 등) |
| **cost** | 5–7 |
| **전형 pairing** | EXTRACT NATURAL_LANGUAGE_DOSE, EXTRACT NATURAL_LANGUAGE_TIME |

#### V13. ROUTE

| 항목 | 내용 |
|------|------|
| **정의** | 현재 상태를 terminal(AUTO/REPAIR) 또는 Q-code(QUARANTINE)로 라우팅한다. |
| **SRP 경계** | 라우팅 결정만. 상태 평가는 DETECT/VERIFY/CLASSIFY 소관. |
| **kind 친화** | route |
| **layer 친화** | L-3↔L-4 (N0–N7 골격 분기점) |
| **cost** | 0 |
| **전형 pairing** | ROUTE CROSS_COLUMN_INVARIANT, ROUTE COLUMN_SCHEMA |

---

## B. NOUNS (6 categories, 57 total)

### 카테고리 요약

| Category | Count | Universe | Layer 친화 | Source |
|----------|-------|----------|-----------|--------|
| NONMEM_COLUMN | 10 | A | L-1↔L-2 | L0_nonmem_ready.md §A.1 |
| MESS_CONCEPT | 26 | B (21) + A (3) + flag (2) | L-4↔L-5, L-3↔L-4 | universe_sm §6, §3 A5, §4 Q15B/Q15C |
| DOMAIN_ENTITY | 9 | A | L-2↔L-3, L-3↔L-4 | universe_sm §2–§3 |
| FILE_PROPERTY | 6 | B | L-4↔L-5 | universe_sm §6 파일군 |
| UNIT_PROPERTY | 4 | B | L-4↔L-5 | universe_sm §6, §4 Q10 |
| SCHEMA_PROPERTY | 4 | A | L-1↔L-2 | L0_nonmem_ready.md §B, §C |

### B.1 NONMEM_COLUMN (10)

NONMEM-ready dataset의 core required column. L0_nonmem_ready.md §A.1과 1:1 대응.

| NOUN | 정의 | L0 predicate | Ref |
|------|------|-------------|-----|
| **ID** | 피험자 식별자 컬럼 (양의 정수) | §A.1 ID | universe_sm §2 N1 |
| **TIME** | 이벤트 시간 컬럼 (실수, 단위 일관) | §A.1 TIME | universe_sm §2 N2 |
| **DV** | 종속 변수 컬럼 (관측값) | §A.1 DV | universe_sm §2 N4 |
| **MDV** | 결측 종속 변수 flag 컬럼 ({0,1}) | §A.1 MDV | universe_sm §2 N5 |
| **EVID** | 이벤트 ID 컬럼 ({0,1,2,3,4}) | §A.1 EVID | universe_sm §2 N3/N4 |
| **AMT** | 투여량 컬럼 | §A.1 AMT | universe_sm §2 N3 |
| **CMT** | 구획 번호 컬럼 | §A.1 CMT | universe_sm §3 A8 |
| **RATE** | 주입 속도 컬럼 | §A.1 RATE | universe_sm §3 A4 |
| **ADDL** | 추가 투여 횟수 컬럼 | §A.1 ADDL | universe_sm §3 A4 |
| **II** | 투여 간격 컬럼 | §A.1 II | universe_sm §3 A4 |

### B.2 MESS_CONCEPT (26)

syntactic mess dimension 또는 observation 특수 패턴. 대부분 Universe B(§6), 일부 Universe A(§3 A5), Q15B/Q15C flag 2개(Phase 3 사용자 지시 추가).

#### 결측/BLQ (2)

| NOUN | 정의 | Universe | Ref |
|------|------|----------|-----|
| **NA_TOKEN** | 결측값 토큰 ("NA", "N/A", blank, "999", ".", "NULL", "-" 등) | B | universe_sm §6 NA_TOKEN |
| **BLQ_TOKEN** | BLQ 토큰 ("<LLOQ", "<0.1", "BLQ", "ND", "이하" 등) | B | universe_sm §6 BLQ_TOKEN |

#### 시간 (3)

| NOUN | 정의 | Universe | Ref |
|------|------|----------|-----|
| **TIME_FORMAT** | 시간 값의 표기 형식 (clock, elapsed, decimal, datetime, mixed) | B | universe_sm §6 TIME_FORMAT |
| **TIME_ANCHOR** | 시간 기준점 표현 ("Day 1", "Visit 1", date 혼재 등) | B | universe_sm §6 TIME_ANCHOR |
| **TIMEZONE** | 시간대 (DST crossing, 24h vs 12h+AM/PM) | B | universe_sm §6 TIMEZONE |

#### ID (2)

| NOUN | 정의 | Universe | Ref |
|------|------|----------|-----|
| **ID_DTYPE** | ID 값의 데이터 타입 (string/int 혼재, 형식 불일치) | B | universe_sm §6 ID_DTYPE |
| **ID_LEADING_ZERO** | ID 앞자리 0 처리 ("'001" → "001" 또는 1) | B | universe_sm §6 ID_DTYPE (하위) |

#### 셀 구조 (4)

| NOUN | 정의 | Universe | Ref |
|------|------|----------|-----|
| **MERGED_CELL** | 병합 셀 잔존 (forward-fill 필요) | B | universe_sm §6 MERGED_CELL |
| **MULTI_LEVEL_HEADER** | 다단 헤더 (1–2행 병합 헤더) | B | universe_sm §6 MULTI_LEVEL_HEADER |
| **TRAILING_BLANK** | 꼬리 빈 행 | B | universe_sm §6 TRAILING_BLANK |
| **DUPLICATE_ROW** | 완전 중복 행 (≠ A5 REPLICATE-SAME-TIME) | B | universe_sm §6 DUPLICATE_ROW |

#### 자연어 (3)

| NOUN | 정의 | Universe | Ref |
|------|------|----------|-----|
| **NATURAL_LANGUAGE_DOSE** | 자연어 dose 표현 ("100 mg", "two tablets") | B | universe_sm §6 NATURAL_LANGUAGE_DOSE |
| **NATURAL_LANGUAGE_TIME** | 자연어 시간 표현 ("after 30 min", "predose") | B | universe_sm §6 NATURAL_LANGUAGE_TIME |
| **FREETEXT_COMMENT** | 자유 텍스트 코멘트 컬럼 | B | universe_sm §6 FREETEXT_COMMENT |

#### Excel artifact (5)

| NOUN | 정의 | Universe | Ref |
|------|------|----------|-----|
| **EXCEL_FORMULA** | Excel 수식 텍스트 잔존 ("=SUM(...)") | B | universe_sm §6 EXCEL_FORMULA |
| **EXCEL_DATE_SERIAL** | Excel 날짜 일련번호 (43000 등) | B | universe_sm §6 EXCEL_DATE_SERIAL |
| **NON_ASCII_DECIMAL** | 비표준 소수점·천단위 구분자 ("1,5" / "1,000") | B | universe_sm §6 NON_ASCII_DECIMAL |
| **LINEBREAK_IN_CELL** | 셀 내 줄바꿈 | B | universe_sm §6 LINEBREAK_IN_CELL |
| **SCIENTIFIC_NOTATION** | 과학적 표기법 artifact ("1E+3", "1*10^3") | B | universe_sm §6 SCIENTIFIC_NOTATION |

#### 레이아웃 (1)

| NOUN | 정의 | Universe | Ref |
|------|------|----------|-----|
| **COVARIATE_LAYOUT** | 공변량 레이아웃 (wide vs long) | B | universe_sm §6 COVARIATE_LAYOUT |

#### 도메인 코딩 (2)

| NOUN | 정의 | Universe | Ref |
|------|------|----------|-----|
| **PRE_DOSE_CODING** | 투약 전 시점 코딩 (음수시간, "PRE" flag, t=0) | B | universe_sm §6 PRE_DOSE_CODING |
| **PLACEBO_SUBJECT** | 위약군 피험자 (AMT=0 vs dose 누락 구분) | B | universe_sm §6 PLACEBO_SUBJECT |

#### Observation 특수 패턴 (2) — Universe A 유래

| NOUN | 정의 | Universe | Ref |
|------|------|----------|-----|
| **ABOVE_ULOQ** | ULOQ 초과 관측값 (>ULOQ, 우측 censoring/희석 초과) | A | universe_sm §3 A5 P1 |
| **REPLICATE_OBS** | 동일 (ID,TIME)에서 유효 농도 ≥2 (정당 replicate) | A | universe_sm §3 A5 P3 |

### B.3 DOMAIN_ENTITY (9)

도메인 수준의 데이터 개체. Universe A(Scenario/Routing)에 속하며 구조 변형(L-2↔L-3)과 axis 평가(L-3↔L-4)에서 사용.

| NOUN | 정의 | Ref |
|------|------|-----|
| **DOSE_SHEET** | 투약 기록이 담긴 시트/파일 | universe_sm §2 N3, §6 SHEET_INVENTORY |
| **COVARIATE_SHEET** | 공변량이 담긴 시트/파일 | universe_sm §2 N6, §6 SHEET_INVENTORY |
| **ANALYTE_COLUMN** | 분석물질(약물 농도) 컬럼 | universe_sm §3 A5, A8 |
| **BASELINE_COVARIATE** | 기저 시점 공변량 (baseline WT, AGE 등) | universe_sm §3 A7 BASELINE-CLEAN/IMPUTABLE |
| **TIME_VARYING_COVARIATE** | 시변 공변량 (시간에 따라 변동하는 WT, CRCL 등) | universe_sm §3 A7 TIME-VARYING |
| **METABOLITE** | 대사체 (active metabolite, 측정 대상) | universe_sm §3 A8 METABOLITE-DEFINED |
| **PARENT_DRUG** | 모약물 (prodrug 또는 원래 투여 약물) | universe_sm §3 A8 |
| **OCCASION** | 투여 기간/방문 주기 (occasion 정의) | universe_sm §4 Q03 |
| **REGIMEN_DESCRIPTOR** | 투여 요법 기술자 (loading/maintenance, titration 등) | universe_sm §3 A4 |

### B.4 FILE_PROPERTY (6)

파일 수준 속성. Universe B에 속하며 L-4↔L-5에서 사용.

| NOUN | 정의 | Ref |
|------|------|-----|
| **ENCODING** | 파일 문자 인코딩 (UTF-8, CP949 등) | universe_sm §6 ENCODING |
| **FILE_FORMAT** | 파일 형식 (CSV, Excel/xlsx, TSV 등) | universe_sm §3 A10 |
| **SHEET_INVENTORY** | 파일 내 시트 목록 (multi-sheet 구조) | universe_sm §6 SHEET_INVENTORY |
| **BOM** | Byte Order Mark 존재 여부 | universe_sm §6 ENCODING (하위) |
| **LINE_ENDING** | 줄바꿈 문자 (LF, CRLF, CR) | universe_sm §6 LINE_ENDING |
| **DELIMITER** | 필드 구분자 (comma, tab, semicolon) | universe_sm §6 DELIMITER |

### B.5 UNIT_PROPERTY (4)

단위 관련 속성. Universe B에 속하며 L-4↔L-5에서 사용.

| NOUN | 정의 | Ref |
|------|------|-----|
| **UNIT_DECLARATION** | 각 컬럼의 단위 표기·선언 (누락 여부, 표기 방식) | universe_sm §6 UNIT_DECLARATION |
| **UNIT_CONSISTENCY** | 컬럼 내 단위 일관성 (동일 컬럼에 mg/µg 혼재 등) | universe_sm §6 UNIT_DECLARATION (확장) |
| **UNIT_CANONICAL** | 단위의 표준 형식 (㎗→dL, mcg→µg 등 유니코드 정규화 포함) | universe_sm §6 UNIT_DECLARATION (확장) |
| **MOLAR_MASS** | 분자량 (molar↔mass 변환에 필요, MW 사전) | universe_sm §4 Q10, P5 |

### B.6 SCHEMA_PROPERTY (4)

데이터셋 구조·불변 조건. Universe A에 속하며 L-1↔L-2에서 사용.

| NOUN | 정의 | Ref |
|------|------|-----|
| **COLUMN_SCHEMA** | 컬럼 구조 정의 (필수 컬럼 존재, 타입, 도메인) | L0_nonmem_ready.md §A |
| **ROW_ORDERING** | 행 정렬 규칙 (ID asc → TIME asc → EVID tiebreak) | L0_nonmem_ready.md §C (S-01~S-03) |
| **ROW_LEVEL_INVARIANT** | 행 수준 불변 조건 (I-R01~I-R15) | L0_nonmem_ready.md §B.1 |
| **CROSS_COLUMN_INVARIANT** | 교차 컬럼 불변 조건 (I-D01~I-D07 포함) | L0_nonmem_ready.md §B.2 |

---

## C. MODIFIERS (7)

MODIFIER는 `BY {MOD}` 형태로 srp_intent에 붙어 작업의 적용 범위(scope)를 한정한다.

| MODIFIER | 정의 | 적용 범위 |
|----------|------|----------|
| **WITHIN_ID** | 동일 subject(ID) 내로 한정 | row grouping: 한 subject의 row 집합 |
| **WITHIN_OCCASION** | 동일 occasion 내로 한정 | row grouping: 한 occasion의 row 집합 |
| **WITHIN_ANALYTE** | 동일 분석물질 내로 한정 | column/row grouping: 한 analyte의 데이터 |
| **ACROSS_SHEET** | sheet 경계를 넘어 적용 | file scope: 복수 sheet 간 작업 |
| **ACROSS_FILE** | file 경계를 넘어 적용 | project scope: 복수 file 간 작업 |
| **PER_SUBJECT** | subject별로 반복 적용 | iteration: 각 subject에 대해 독립 실행 |
| **PER_VISIT** | visit별로 반복 적용 | iteration: 각 visit에 대해 독립 실행 |

---

## D. §6 Dimension ↔ NOUN 매핑표

universe_sm §6의 26개 mess dimension이 어느 NOUN 카테고리에 배치되었는지 전수 확인.

| §6 Dimension | NOUN | Category |
|---|---|---|
| NA_TOKEN | NA_TOKEN | MESS_CONCEPT |
| BLQ_TOKEN | BLQ_TOKEN | MESS_CONCEPT |
| TIME_FORMAT | TIME_FORMAT | MESS_CONCEPT |
| TIME_ANCHOR | TIME_ANCHOR | MESS_CONCEPT |
| TIMEZONE | TIMEZONE | MESS_CONCEPT |
| ID_DTYPE | ID_DTYPE + ID_LEADING_ZERO | MESS_CONCEPT (ID_LEADING_ZERO는 하위 분리) |
| UNIT_DECLARATION | UNIT_DECLARATION | UNIT_PROPERTY |
| MERGED_CELL | MERGED_CELL | MESS_CONCEPT |
| MULTI_LEVEL_HEADER | MULTI_LEVEL_HEADER | MESS_CONCEPT |
| TRAILING_BLANK | TRAILING_BLANK | MESS_CONCEPT |
| DUPLICATE_ROW | DUPLICATE_ROW | MESS_CONCEPT |
| NATURAL_LANGUAGE_DOSE | NATURAL_LANGUAGE_DOSE | MESS_CONCEPT |
| NATURAL_LANGUAGE_TIME | NATURAL_LANGUAGE_TIME | MESS_CONCEPT |
| FREETEXT_COMMENT | FREETEXT_COMMENT | MESS_CONCEPT |
| ENCODING | ENCODING | FILE_PROPERTY |
| LINE_ENDING | LINE_ENDING | FILE_PROPERTY |
| DELIMITER | DELIMITER | FILE_PROPERTY |
| SHEET_INVENTORY | SHEET_INVENTORY | FILE_PROPERTY |
| EXCEL_FORMULA | EXCEL_FORMULA | MESS_CONCEPT |
| EXCEL_DATE_SERIAL | EXCEL_DATE_SERIAL | MESS_CONCEPT |
| NON_ASCII_DECIMAL | NON_ASCII_DECIMAL | MESS_CONCEPT |
| SCIENTIFIC_NOTATION | SCIENTIFIC_NOTATION | MESS_CONCEPT |
| LINEBREAK_IN_CELL | LINEBREAK_IN_CELL | MESS_CONCEPT |
| COVARIATE_LAYOUT | COVARIATE_LAYOUT | MESS_CONCEPT |
| PRE_DOSE_CODING | PRE_DOSE_CODING | MESS_CONCEPT |
| PLACEBO_SUBJECT | PLACEBO_SUBJECT | MESS_CONCEPT |

**추가 NOUN (§6 외 유래):**

| NOUN | Source | Category | 비고 |
|------|--------|----------|------|
| ID_LEADING_ZERO | §6 ID_DTYPE 하위 | MESS_CONCEPT | leading zero 처리를 별도 c-단위체로 분리 |
| ABOVE_ULOQ | §3 A5 P1 | MESS_CONCEPT | ULOQ 초과 관측값 처리 |
| REPLICATE_OBS | §3 A5 P3 | MESS_CONCEPT | 정당 replicate 관측값 처리 |
| LEGACY_FLAG_PRESENT | §4 Q15B | MESS_CONCEPT | 미문서화 legacy marker column 존재 (Phase 3 추가) |
| RWD_ADHERENCE_UNRESOLVED | §4 Q15C | MESS_CONCEPT | TDM/RWD 투약 이력 불확실성 미해결 (Phase 3 추가) |
| FILE_FORMAT | §3 A10 | FILE_PROPERTY | 파일 형식 (CSV/Excel 등) |
| BOM | §6 ENCODING 하위 | FILE_PROPERTY | BOM 존재 여부를 별도 처리 |
| UNIT_CONSISTENCY | §6 UNIT_DECLARATION 확장 | UNIT_PROPERTY | 컬럼 내 단위 혼재 |
| UNIT_CANONICAL | §6 UNIT_DECLARATION 확장 | UNIT_PROPERTY | 단위 표준 형식 |
| MOLAR_MASS | §4 Q10, P5 | UNIT_PROPERTY | molar↔mass 변환에 필요 |
| NONMEM_COLUMN 10개 | L0_nonmem_ready.md §A.1 | NONMEM_COLUMN | — |
| DOMAIN_ENTITY 9개 | universe_sm §2–§3 | DOMAIN_ENTITY | — |
| SCHEMA_PROPERTY 4개 | L0_nonmem_ready.md §B, §C | SCHEMA_PROPERTY | — |

---

## E. Self-check

| # | 질문 | 판정 |
|---|------|------|
| 1 | VERB count = 13 (closed set)? | **Yes.** V01–V13. IMPUTE 미포함. |
| 2 | NOUN 총수 = 59? | **Yes.** NONMEM_COLUMN(10) + MESS_CONCEPT(26) + DOMAIN_ENTITY(9) + FILE_PROPERTY(6) + UNIT_PROPERTY(4) + SCHEMA_PROPERTY(4) = 59. (Phase 3에서 LEGACY_FLAG_PRESENT, RWD_ADHERENCE_UNRESOLVED 추가.) |
| 3 | universe_sm §6 26개 dimension이 전수 매핑되었는가? | **Yes.** §D 매핑표에서 26개 dimension → 21 MESS_CONCEPT + 4 FILE_PROPERTY + 1 UNIT_PROPERTY = 26. |
| 4 | NOUN 카테고리 간 중복 0개? | **Yes.** 각 NOUN은 단일 카테고리에만 속함. ID_DTYPE과 ID_LEADING_ZERO는 별개 NOUN. ENCODING(FILE_PROPERTY)과 UNIT_DECLARATION(UNIT_PROPERTY)은 카테고리가 다름. |
| 5 | 모든 NOUN이 universe_sm §3/§6 또는 L0_nonmem_ready.md에 역추적 가능한가? | **Yes.** §D 매핑표 참조. |
| 6 | srp_intent 형식이 규칙과 일치하는가? | **Yes.** §0.2 예시 전부 "{VERB} {NOUN}" 또는 "{VERB} {NOUN} BY {MOD}" 형식. |
| 7 | IMPUTE가 VERB 목록에 없는가? | **Yes.** §A 설계 결정에 명시. |
| 8 | FILTER 정의에 "row 삭제 금지" 명시되었는가? | **Yes.** V08 정의에 "★ 행 삭제(drop/exclude)가 아님" 명시. |
| 9 | anchors.json에 없는 식별자 인용 0개? | **Yes.** 모든 axis state, Q-code, terminal, endpoint_data_type 인용이 anchors.json v1.1과 일치. |
| 10 | [AMBIGUOUS] 태그 잔존 0개? | **Yes.** |

---

## F. 종료 보고

```
STATUS: PHASE_2_0_COMPLETE
산출물: spec/vocabulary.md
VERB: 13 (closed set, IMPUTE 제외 확인)
NOUN: 59 (NONMEM_COLUMN 10 / MESS_CONCEPT 26 / DOMAIN_ENTITY 9 / FILE_PROPERTY 6 / UNIT_PROPERTY 4 / SCHEMA_PROPERTY 4)
MODIFIER: 7
§6 dimension coverage: 26/26 (100%)
결정 필요사항: 없음
미해결 ambiguity: 0개
vocab 위반: 0개
다음 Phase 전 사용자 확인: Phase 2a (L-1↔L-2 NONMEM 특수컬럼) 진입 허가
```
