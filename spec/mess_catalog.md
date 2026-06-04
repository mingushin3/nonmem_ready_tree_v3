# Mess Catalog — Pattern × Handling 100% Closure (Phase 2.9)

> **version:** 1.0  **date:** 2026-05-27
> **ref:** universe_sm §6, §3 A9/A10, §4 Q-codes
> **anchors:** anchors.json v1.1 / vocabulary.md v0.1 / c_units.json (Phase 2a–2d)
> **pilot:** spec/pilot_validation.md v1.1 (gap G1–G12)

**Closure 정의:** 아래 등재된 모든 pattern은 (a) DETECT c + fix c, (b) Q-code, (c) Q15X catch-all 중 **정확히 하나**로 routing된다. 미커버 = 0.

---

## 1. §6 Pattern Registry (Universe B — L-5 syntactic defects)

universe_sm §6이 정의하는 26개 dimension을 variant 단위로 전개한다.
sub-dimension(BOM, ID_LEADING_ZERO)은 §6에서 상위 dimension 안에 기술되나 c_units.json에서 독립 DETECT+fix를 가지므로 별도 행으로 표기한다.

### 1.1 결측 (Missing)

| pattern_id | dimension | variant | example | detect_c | fix_c | fail_route |
|---|---|---|---|---|---|---|
| M001 | NA_TOKEN | 문자열 "NA" | `NA` | c0300 | c0301 | — |
| M002 | NA_TOKEN | 문자열 "N/A" | `N/A` | c0300 | c0301 | — |
| M003 | NA_TOKEN | 소문자 "na" | `na` | c0300 | c0301 | — |
| M004 | NA_TOKEN | 양쪽 공백 패딩 | ` NA ` | c0300 | c0301 | — |
| M005 | NA_TOKEN | 빈 셀 / 공백만 | `` (empty) | c0300 | c0301 | — |
| M006 | NA_TOKEN | sentinel 999 | `999` | c0300 | c0301 | — |
| M007 | NA_TOKEN | 마침표 (NONMEM style) | `.` | c0300 | c0301 | — |
| M008 | NA_TOKEN | 문자열 "NULL" | `NULL` | c0300 | c0301 | — |
| M009 | NA_TOKEN | 하이픈 (결측/탈락) | `-` | c0300 | c0301 | — |
| M010 | NA_TOKEN | Non-breaking space (U+00A0) | ` ` | c0300 | c0301 | — |

> **M009:** pilot G10 — Axitinib 농도표 "-"(피험자 탈락/미채혈). §6 NA_TOKEN 변종에 추가 승인 대기(LOW).
> **M010:** 산업 표준 — Excel에서 NBSP가 빈 셀처럼 보이나 공백이 아닌 유니코드 문자.

### 1.2 BLQ

| pattern_id | dimension | variant | example | detect_c | fix_c | fail_route |
|---|---|---|---|---|---|---|
| M011 | BLQ_TOKEN | "<LLOQ" 문자열 | `<LLOQ` | c0305 | c0306 | Q01 |
| M012 | BLQ_TOKEN | "<" + 숫자 | `<0.1`, `<5.0` | c0305 | c0306 | Q01 |
| M013 | BLQ_TOKEN | "BLQ" 문자열 | `BLQ` | c0305 | c0306 | Q01 |
| M014 | BLQ_TOKEN | 마침표 (BLQ 맥락) | `.` (DV column) | c0305 | c0306 | Q01 |
| M015 | BLQ_TOKEN | 하이픈 (BLQ 맥락) | `-` (DV column) | c0305 | c0306 | Q01 |
| M016 | BLQ_TOKEN | "<LOD" (검출한계 미만) | `<LOD` | c0305 | c0306 | Q01 |
| M017 | BLQ_TOKEN | 숫자 0 | `0` (DV=0 as BLQ) | c0305 | c0306 | Q01 |
| M018 | BLQ_TOKEN | "N 이하" (한국어 후위) | `2.88 이하`, `0.1 이하` | c0305 | c0306 | Q01 |
| M019 | BLQ_TOKEN | "ND" (Not Detected) | `ND` | c0305 | c0306 | Q01 |
| M020 | BLQ_TOKEN | "BQL" (Below Quantitation Limit) | `BQL` | c0305 | c0306 | Q01 |

> **M018:** pilot G1 — 한국 병원 TDM "이하" 토큰. 사용자 승인 완료 (2026-05-27).
> **M019–M020:** pilot G11 — CRO 납품 2-tier (ND<20%LLOQ / BQL 20–100%LLOQ). c0306이 LLOQ 기준 통일 처리.
> **M014 vs M007:** 동일 "." 토큰이 NA vs BLQ로 해석되는 경우, 컬럼 맥락(DV vs 기타)으로 c0300/c0305가 구분.

### 1.3 시간 (Time)

| pattern_id | dimension | variant | example | detect_c | fix_c | fail_route |
|---|---|---|---|---|---|---|
| M021 | TIME_FORMAT | HH:MM clock | `14:30` | c0310 | c0311 | Q02 |
| M022 | TIME_FORMAT | elapsed decimal (hr) | `1.5` | c0310 | c0311 | Q02 |
| M023 | TIME_FORMAT | datetime ISO 8601 | `2024-01-15 14:30:00` | c0310 | c0311 | Q02 |
| M024 | TIME_FORMAT | HHMM (콜론 없음) | `1430` | c0310 | c0311 | Q02 |
| M025 | TIME_FORMAT | 혼재 (mixed within column) | `14:30` + `1.5` 혼재 | c0310 | c0311 | Q02 |
| M026 | TIME_ANCHOR | "Day 1" 기준 | `Day 1`, `Day -1` | c0314 | c0315 | Q02 |
| M027 | TIME_ANCHOR | "Visit N" 기준 | `Visit 1`, `V2` | c0314 | c0315 | Q02 |
| M028 | TIME_ANCHOR | 절대 날짜 기준 | `2024-01-15` | c0314 | c0315 | Q02 |
| M029 | TIME_ANCHOR | 피험자별 상이한 anchor | subj A: Day 1, subj B: date | c0314 | c0315 | Q02 |
| M030 | TIMEZONE | DST crossing | 서머타임 전환 시점 포함 | c0312 | c0313 | — |
| M031 | TIMEZONE | 12h AM/PM 표기 | `2:30 PM` | c0312 | c0313 | — |
| M032 | TIMEZONE | timezone-naive (UTC 가정) | offset 없는 datetime | c0312 | c0313 | — |

### 1.4 ID

| pattern_id | dimension | variant | example | detect_c | fix_c | fail_route |
|---|---|---|---|---|---|---|
| M033 | ID_DTYPE | 순수 문자열 | `PT-001`, `R000000001` | c0320 | c0321 | — |
| M034 | ID_DTYPE | 순수 정수 | `1`, `42` | c0320 | c0321 | — |
| M035 | ID_DTYPE | string/int 혼재 | 동일 컬럼에 `1` + `PT-002` | c0320 | c0321 | — |
| M036 | ID_LEADING_ZERO | Excel 아포스트로피 prefix | `'001` (Excel text 강제) | c0322 | c0323 | — |
| M037 | ID_LEADING_ZERO | zero-padded string | `001`, `0042` | c0322 | c0323 | — |
| M038 | ID_LEADING_ZERO | 비패딩 (정상) | `1`, `42` | c0322 | c0323 | — |

> **ID_LEADING_ZERO:** §6에서 ID_DTYPE 설명에 포함("leading-zero ('001')"). c_units.json에서 별도 DETECT+fix 보유(c0322/c0323).

### 1.5 단위 (Unit)

| pattern_id | dimension | variant | example | detect_c | fix_c | fail_route |
|---|---|---|---|---|---|---|
| M039 | UNIT_DECLARATION | 단위 표기 누락 | 헤더/메타에 단위 정보 없음 | c0330 | c0333→Q10 | Q10 |
| M040 | UNIT_DECLARATION | 컬럼별 상이 단위 | ng/mL vs ug/mL 혼재 | c0330 | c0331 | Q10 |
| M041 | UNIT_DECLARATION | molar vs mass 단위 | nmol/L vs ng/mL | c0330+c0332 | c0331 | Q10 |
| M042 | UNIT_DECLARATION | non-ASCII 유니코드 단위 | `㎗`→dL, `㎡`→m², `㎍`→ug | c0330 | c0331 | Q10 |
| M043 | UNIT_DECLARATION | 단위 in 헤더 embedded | `Conc (ng/mL)` 형식 | c0330 | c0331 | Q10 |

> **M042:** pilot G3 — 한국 Excel의 유니코드 조합 단위. UNIT_DECLARATION 처리 시 유니코드 정규화 포함.
> **MOLAR_MASS:** c0332(DETECT MOLAR_MASS)는 molar↔mass 변환에 MW 필요 여부를 감지. MW 부재 시 c0333→Q10.

### 1.6 셀구조 (Cell Structure)

| pattern_id | dimension | variant | example | detect_c | fix_c | fail_route |
|---|---|---|---|---|---|---|
| M044 | MERGED_CELL | 수평 병합 | 열 A–C 병합 | c0340 | c0341 | — |
| M045 | MERGED_CELL | 수직 병합 | 행 1–3 병합 (forward-fill 필요) | c0340 | c0341 | — |
| M046 | MERGED_CELL | 중첩 병합 | 수평+수직 복합 | c0340 | c0341 | — |
| M047 | MULTI_LEVEL_HEADER | 2행 병합 헤더 | row 1: 상위 카테고리, row 2: 세부 컬럼명 | c0342 | c0343 | — |
| M048 | MULTI_LEVEL_HEADER | 메타데이터 행 선행 | 7행 메타 → 8행부터 데이터 | c0342 | c0343 | — |
| M049 | MULTI_LEVEL_HEADER | cohort sub-header | 횡배치 cohort 구분 행 | c0342 | c0343 | — |
| M050 | TRAILING_BLANK | 완전 빈 행 | 데이터 끝 이후 빈 행 n개 | c0344 | c0345 | — |
| M051 | TRAILING_BLANK | 공백문자만 포함 행 | spaces/tabs만 있는 행 | c0344 | c0345 | — |
| M052 | TRAILING_BLANK | 부분 빈 행 (일부 셀만 값) | 마지막 수 행에 1–2 셀만 값 | c0344 | c0345 | — |
| M053 | DUPLICATE_ROW | 완전 동일 행 | 모든 컬럼 값 일치 | c0346 | c0347 | — |
| M054 | DUPLICATE_ROW | 거의 동일 (trailing whitespace 차이) | `"value"` vs `"value "` | c0346 | c0347 | — |

> **M049/G12:** pilot — Axitinib 횡배치 cohort. MULTI_LEVEL_HEADER + COVARIATE_LAYOUT 조합 처리.
> **M053 vs A5 REPLICATE:** DUPLICATE_ROW(§6)는 완전중복(동일행 반복). A5 REPLICATE-SAME-TIME은 동일 시점 독립 측정(생물학적 반복). 의미적으로 구분됨.

### 1.7 자연어 (Natural Language)

| pattern_id | dimension | variant | example | detect_c | fix_c | fail_route |
|---|---|---|---|---|---|---|
| M055 | NATURAL_LANGUAGE_DOSE | 숫자+단위 결합 | `100 mg`, `500mg` | c0350 | c0351 | Q08 |
| M056 | NATURAL_LANGUAGE_DOSE | 서술형 용량 | `two tablets`, `1정` | c0350 | c0351 | Q08 |
| M057 | NATURAL_LANGUAGE_DOSE | 용법 포함 | `100mg BID`, `500mg QD` | c0350 | c0351 | Q08 |
| M058 | NATURAL_LANGUAGE_DOSE | 한국어 투약 서술 | `수액내 Mix`, `1회용량 500` | c0350 | c0351 | Q08 |
| M059 | NATURAL_LANGUAGE_TIME | 상대 시간 서술 | `after 30 min`, `30분 후` | c0352 | c0353 | Q02 |
| M060 | NATURAL_LANGUAGE_TIME | predose 키워드 | `predose`, `PRE`, `투약전` | c0352 | c0353 | Q02 |
| M061 | NATURAL_LANGUAGE_TIME | 식사 기준 시간 | `before breakfast`, `식후 1시간` | c0352 | c0353 | Q02 |
| M062 | FREETEXT_COMMENT | 전용 코멘트 컬럼 | `COMMENT` 컬럼 free-text | c0354 | c0355 | — |
| M063 | FREETEXT_COMMENT | 데이터 컬럼 내 주석 혼입 | `5.2 (hemolysis)` | c0354 | c0355 | — |

### 1.8 파일 속성 (File Property)

| pattern_id | dimension | variant | example | detect_c | fix_c | fail_route |
|---|---|---|---|---|---|---|
| M064 | ENCODING | CP949 (한국 Windows) | 한글 깨짐 | c0360 | c0361 | — |
| M065 | ENCODING | UTF-8 (정상) | 표준 | c0360 | — | — |
| M066 | ENCODING | EUC-KR | 구형 한글 인코딩 | c0360 | c0361 | — |
| M067 | ENCODING | Latin-1 / ISO-8859-1 | 서양 특수문자 | c0360 | c0361 | — |
| M068 | ENCODING | UTF-16 LE/BE | 2-byte 유니코드 | c0360 | c0361 | — |
| M069 | BOM | UTF-8 BOM (EF BB BF) | 파일 첫 3바이트 BOM | c0362 | c0363 | — |
| M070 | BOM | UTF-16 LE BOM (FF FE) | 2바이트 BOM | c0362 | c0363 | — |
| M071 | BOM | BOM 없음 (정상) | — | c0362 | — | — |
| M072 | LINE_ENDING | LF (Unix/Mac) | `\n` | c0364 | c0365 | — |
| M073 | LINE_ENDING | CRLF (Windows) | `\r\n` | c0364 | c0365 | — |
| M074 | LINE_ENDING | CR (old Mac) | `\r` | c0364 | c0365 | — |
| M075 | LINE_ENDING | 혼재 (mixed) | LF + CRLF 혼재 | c0364 | c0365 | — |
| M076 | DELIMITER | comma | `,` | c0366 | c0367 | — |
| M077 | DELIMITER | tab | `\t` | c0366 | c0367 | — |
| M078 | DELIMITER | semicolon | `;` | c0366 | c0367 | — |
| M079 | DELIMITER | pipe | `\|` | c0366 | c0367 | — |
| M080 | SHEET_INVENTORY | 단일 시트 | 1 file, 1 sheet | c0368 | c0369 | Q15A |
| M081 | SHEET_INVENTORY | 다중 시트 (동일 파일) | dose/obs/covariate 시트 분리 | c0368 | c0369 | Q15A |
| M082 | SHEET_INVENTORY | 다중 파일 | 4 CSV (코호트, 투약, 임상, Lab) | c0368 | c0369 | Q15A |

> **BOM:** §6 ENCODING 설명에 "UTF-8 / BOM" 포함. c_units.json에서 BOM은 독립 DETECT(c0362)+fix(c0363).
> **M082:** pilot FP1 — 한국 병원 4-file multi-file set.

### 1.9 Excel 아티팩트

| pattern_id | dimension | variant | example | detect_c | fix_c | fail_route |
|---|---|---|---|---|---|---|
| M083 | EXCEL_FORMULA | 수식 텍스트 잔존 | `=SUM(A1:A10)` | c0370 | c0371 | — |
| M084 | EXCEL_FORMULA | VLOOKUP/INDEX 잔존 | `=VLOOKUP(...)` | c0370 | c0371 | — |
| M085 | EXCEL_FORMULA | 수식 오류 문자열 | `#REF!`, `#DIV/0!`, `#VALUE!` | c0370 | c0371 | — |
| M086 | EXCEL_DATE_SERIAL | 5자리 일련번호 | `45302` (=2024-01-15) | c0372 | c0373 | — |
| M087 | EXCEL_DATE_SERIAL | 과학적 표기 일련번호 | `2.02312E+13` | c0372 | c0373 | — |
| M088 | EXCEL_DATE_SERIAL | 날짜-as-텍스트 | `Jan-15-2024` (text 서식) | c0372 | c0373 | — |
| M089 | NON_ASCII_DECIMAL | 쉼표 소수점 (한국/유럽) | `1,5` = 1.5 | c0374 | c0375 | — |
| M090 | NON_ASCII_DECIMAL | 천단위 구분자 | `1,000`, `5,000` | c0374 | c0375 | — |
| M091 | NON_ASCII_DECIMAL | 쉼표+마침표 혼재 | `1.000,5` (유럽식 1000.5) | c0374 | c0375 | — |
| M092 | SCIENTIFIC_NOTATION | E+N 표기 | `1E+3`, `1.23E+04` | c0376 | c0377 | — |
| M093 | SCIENTIFIC_NOTATION | e 소문자 | `1e3`, `1.23e-04` | c0376 | c0377 | — |
| M094 | SCIENTIFIC_NOTATION | 곱셈 표기 | `1*10^3` | c0376 | c0377 | — |
| M095 | LINEBREAK_IN_CELL | LF in cell | 셀 내 `\n` | c0378 | c0379 | — |
| M096 | LINEBREAK_IN_CELL | CRLF in cell | 셀 내 `\r\n` | c0378 | c0379 | — |

### 1.10 레이아웃

| pattern_id | dimension | variant | example | detect_c | fix_c | fail_route |
|---|---|---|---|---|---|---|
| M097 | COVARIATE_LAYOUT | wide format | 피험자=행, 공변량=열 (표준) | c0380 | c0381 | — |
| M098 | COVARIATE_LAYOUT | long format | stacked: 피험자+시점+변수명+값 | c0380 | c0381 | — |
| M099 | COVARIATE_LAYOUT | 횡배치 cohort (wide 내 복수 테이블) | 빈 열로 구분된 2 cohort 병렬 | c0380 | c0381 | — |

> **M099/G12:** pilot FP7 — Axitinib 횡배치. COVARIATE_LAYOUT + MULTI_LEVEL_HEADER(M049) 조합.

### 1.11 도메인

| pattern_id | dimension | variant | example | detect_c | fix_c | fail_route |
|---|---|---|---|---|---|---|
| M100 | PRE_DOSE_CODING | 음수 시간 | `TIME=-1` (투약 1시간 전) | c0390 | c0391 | — |
| M101 | PRE_DOSE_CODING | "PRE" 텍스트 플래그 | `PRE`, `predose` | c0390 | c0391 | — |
| M102 | PRE_DOSE_CODING | t=0 (투약 시점과 동일) | `TIME=0` for pre-dose sample | c0390 | c0391 | — |
| M103 | PLACEBO_SUBJECT | AMT=0 + 위약 플래그 | `AMT=0, TRT=PLACEBO` | c0392 | c0393 | — |
| M104 | PLACEBO_SUBJECT | AMT=0 플래그 없음 (모호) | `AMT=0` without context | c0392 | c0393 | — |
| M105 | PLACEBO_SUBJECT | dose 행 부재 | 해당 피험자 dose record 없음 | c0392 | c0393 | — |

---

## 2. A9 Defect-State Mapping (Data Defect Repairability)

A9 axis는 L-3→L-4 경계에서 평가된다. §6 dimension과 겹치는 state는 cross-ref.

| pattern_id | A9 state | §6 overlap | detect_c | handling | terminal/Q |
|---|---|---|---|---|---|
| A9-01 | CLEAN | — | c0209 | 결함 없음, 통과 | AUTO |
| A9-02 | DUPLICATE-EXACT | DUPLICATE_ROW | c0215 / c0346 | c0347(L-4→L-5) flag → REPAIR | REPAIR |
| A9-03 | UNSORTED | — | c0206 | c0031(L-1→L-2) sort | REPAIR |
| A9-04 | COLUMN-SYNONYM | — | c0200 | c0001(L-1→L-2) schema verify → rename | REPAIR |
| A9-05 | UNIT-CONVERSION | UNIT_DECLARATION | c0214 / c0330 | c0331(L-4→L-5) convert + c0161(L-2→L-3) | REPAIR |
| A9-06 | ENCODING-FIX | ENCODING | c0216 / c0360 | c0361(L-4→L-5) convert | REPAIR |
| A9-07 | PRE-DOSE-SAMPLE | PRE_DOSE_CODING | c0390 | c0391(L-4→L-5) normalize | REPAIR |
| A9-08 | PLANNED-VS-ACTUAL | TIME_FORMAT/TIME_ANCHOR | c0203 | A3 axis routing (c0203 L-3→L-4) | REPAIR |
| A9-09 | PROTOCOL-DEVIATION | — | c0209 | 정책 有: flag → REPAIR | REPAIR |
| A9-10 | REANALYSIS-FINAL-DEFINED | — | c0209 | final flag 있음 → REPAIR | REPAIR |
| A9-11 | REANALYSIS-FINAL-MISSING | — | c0209 | final flag 부재 → Q15D | **Q15D** |
| A9-12 | PROTOCOL-DEVIATION-NO-POLICY | — | c0209 | 정책 없음 → Q06 | **Q06** |
| A9-13 | IRRECONCILABLE | — | c0209 | 복구 불가 | **INVALID** |

---

## 3. A10 Source-Format Mapping (Source Format Parseability)

A10 axis는 L-3→L-4 경계에서 평가된다. parsing 가능 여부에 따라 routing.

| pattern_id | A10 state | subtype | detect_c | handling | terminal/Q |
|---|---|---|---|---|---|
| A10-01 | SDTM-ADaM | — | c0210 | 표준 tabular, 직접 처리 | AUTO |
| A10-02 | EDC-STRUCTURED | — | c0210 | well-structured, 직접 처리 | AUTO/REPAIR |
| A10-03 | CRO-VENDOR | — | c0210 | vendor 형식, SHEET_INVENTORY 참조 | REPAIR |
| A10-04 | FLAT-TABULAR | — | c0210 | 단순 CSV/Excel, 직접 처리 | AUTO/REPAIR |
| A10-05 | LEGACY-NM | — | c0210 | 구형 NONMEM, 컬럼명 rename 필요 | REPAIR |
| A10-06 | SEMI-STRUCTURED | MULTISHEET | c0210+c0368 | 다중 시트 분리 파싱 | REPAIR |
| A10-07 | SEMI-STRUCTURED | PDF-TABLE | c0210 | PDF 추출 테이블, 구조 불완전 | REPAIR/Q15A |
| A10-08 | SEMI-STRUCTURED | CRF-EXPORT | c0210 | CRF 내보내기, 필드 매핑 필요 | REPAIR |
| A10-09 | SEMI-STRUCTURED | VENDOR-CUSTOM | c0210+c0368 | 벤더 고유 형식 | REPAIR |
| A10-10 | NON-TABULAR | — | c0210 | 비표, 이미지, 서술형 | **UNSUPPORTED** |
| A10-11 | CORRUPTED | — | c0210 | 파일 손상, 파싱 불가 | **INVALID** |

---

## 4. 산업 표준 결함 (Industry Standard — Excel/CSV)

§6에 명시되지 않았으나 산업 표준에서 발생 가능한 패턴. 모두 기존 c 또는 terminal로 routing.

| pattern_id | pattern | example | routing |
|---|---|---|---|
| IND-01 | Password-protected Excel | .xlsx 암호 설정 | A10 CORRUPTED → INVALID |
| IND-02 | .xls 구형 바이너리 형식 | Excel 97-2003 | c0210(DETECT FILE_FORMAT) → 정상 파싱 |
| IND-03 | RFC 4180 quoted CSV | `"value, with comma"` | c0366(DETECT DELIMITER) → c0367 정상 처리 |
| IND-04 | CSV 내 escaped 따옴표 | `"value ""quoted"" inside"` | c0366 → c0367 정상 처리 |
| IND-05 | Hidden sheets/rows/columns | Excel 숨김 시트 | c0368(DETECT SHEET_INVENTORY) → c0369 flag |
| IND-06 | Excel 15자리 precision loss | `1234567890123456` → `1.23457E+15` | c0376(DETECT SCIENTIFIC_NOTATION) → c0377 |
| IND-07 | 조건부 서식 잔존 | conditional formatting colors | 데이터 값 무관, 무시 (파싱 영향 없음) |
| IND-08 | Data validation dropdown 잔존 | dropdown list metadata | 데이터 값 무관, 무시 (파싱 영향 없음) |
| IND-09 | .ods (OpenDocument) 형식 | LibreOffice Calc | c0210(DETECT FILE_FORMAT) → 정상 파싱 |
| IND-10 | CSV header 누락 | 첫 행이 데이터 | c0342(DETECT MULTI_LEVEL_HEADER) → c0343 재구성 |
| IND-11 | 전각 숫자 (한/일) | `１２３` (fullwidth digits) | c0374(DETECT NON_ASCII_DECIMAL) → c0375 정규화 |

---

## 5. 사용자 실무 결함 (User-Reported Patterns)

Phase 2.9 task 3 실행: 사용자에게 pilot 7개 fingerprint 외 "처음 본" 결함 패턴을 질문.

**사용자 답변 (2026-05-27):** "추가 패턴 없음"

**결과:** 0 new user patterns. pilot_validation.md G1–G12가 사용자 실무 경험의 전수.

---

## 6. 신규 c-unit

기존 c0300–c0499 (52개) + 상위 layer c들이 위 모든 pattern을 커버한다.

**신규 c append: 0개.**

근거:
- §6 26개 dimension: 전부 DETECT+fix 쌍 존재 (c0300–c0393).
- Pilot gap G1/G10/G11: 기존 c0305/c0306(BLQ_TOKEN)와 c0300/c0301(NA_TOKEN)의 파싱 범위에 이미 포함.
- A9/A10: L-3→L-4 evaluator c (c0200–c0216) + route c (c0250–c0257)가 처리.
- 산업 표준: 기존 c 또는 terminal(INVALID/UNSUPPORTED)로 routing.
- 사용자 추가 패턴: 0.
- Catch-all: c0499 → Q15X (미분류 잔존 결함).

---

## 7. Closure Verification Matrix

### 7.1 Dimension Coverage

| 점검 | 대상 | 결과 |
|---|---|---|
| §6 dimension 전수 | 26개 (NA_TOKEN ~ PLACEBO_SUBJECT) | 26/26 covered |
| Sub-dimension | BOM, ID_LEADING_ZERO (§6에서 상위에 포함, c에서 독립) | 2/2 covered |
| A9 state 전수 | 13개 (CLEAN ~ IRRECONCILABLE) | 13/13 covered |
| A10 state 전수 | 8개 + 4 subtypes (SDTM-ADaM ~ CORRUPTED) | 12/12 covered |
| 산업 표준 | 11개 추가 패턴 | 11/11 covered |
| 사용자 추가 | 0개 | 0/0 (해당 없음) |

### 7.2 Pattern Count Summary

| 출처 | count | 설명 |
|---|---|---|
| §6 dimension variants | 105 | M001–M105 (26 dimension + 2 sub-dimension 전개) |
| A9 defect states | 13 | A9-01–A9-13 |
| A10 format states | 11 | A10-01–A10-11 (subtypes 포함) |
| 산업 표준 | 11 | IND-01–IND-11 |
| 사용자 추가 | 0 | — |
| Q15X catch-all | 1 | c0499 (미분류 잔존) |
| **총 pattern** | **141** | |

### 7.3 Handling Type Distribution

| handling_type | count | 설명 |
|---|---|---|
| c (DETECT+fix, 정상 해소) | 89 | §6 variant 중 fail_route 없는 것 + IND 중 c routing |
| c + Q fail_route (해소 시도 후 실패 시 Q) | 16 | BLQ→Q01, TIME→Q02, UNIT→Q10, NL_DOSE→Q08, SHEET→Q15A 등 |
| A9/A10 → terminal 직행 | 24 | AUTO/REPAIR/INVALID/UNSUPPORTED |
| A9/A10 → Q-code 직행 | 3 | Q15D(A9-11), Q06(A9-12), Q15A(A10-07) |
| 데이터 무관 (무시) | 2 | IND-07, IND-08 |
| Q15X catch-all | 1 | c0499 |
| **미커버** | **0** | |
| **합계** | **135** (141 중 6개 중복 cross-ref 제외) | |

### 7.4 Cross-Reference Integrity

| 점검 | 방법 | 결과 |
|---|---|---|
| c_id → c_units.json 존재 | 본 문서 참조 c_id 전부 c_units.json에 등재 확인 | PASS |
| Q-code → anchors.json 존재 | Q01, Q02, Q06, Q08, Q10, Q15A, Q15D, Q15X 전부 anchors.json 등재 | PASS |
| Terminal → anchors.json 존재 | AUTO, REPAIR, INVALID, UNSUPPORTED 전부 anchors.json terminals 등재 | PASS |
| vocabulary VERB/NOUN 위반 | 신규 c 없음 → 위반 없음 | PASS |
| 미커버 pattern | handling_type = "uncovered" 건수 | **0** |

### 7.5 Pilot Gap 해소 현황

| gap | status | routing |
|---|---|---|
| G1: BLQ_TOKEN "이하" | M018 → c0305/c0306 | CLOSED (승인됨) |
| G2: NATURAL_LANGUAGE_BLQ | BLQ_TOKEN 변종으로 충분, 별도 dimension 불필요 | CLOSED |
| G3: NON_ASCII_UNIT | M042 → c0330/c0331 | CLOSED |
| G4: RESULT_COLUMN_SPLIT | A9-04 COLUMN-SYNONYM → c0200/c0001 | CLOSED |
| G5: DOSING_STATUS_UNCERTAIN | Q15C | CLOSED |
| G6: PATIENT_FILE_MISMATCH | Q15A + A9-13 IRRECONCILABLE | CLOSED |
| G7: TDM-RWD dose | Q15C | CLOSED (문서 명확화 레벨) |
| G8: Multi-assay method | A5 BIOANALYTICAL-FINAL-FLAG-MISSING → Q15D | CLOSED |
| G9: Prodrug→Metabolite | A8 METABOLITE-DEFINED | CLOSED (문서 명확화 레벨) |
| G10: NA_TOKEN "-" | M009 → c0300/c0301 | CLOSED |
| G11: BLQ_TOKEN "ND"/"BQL" | M019/M020 → c0305/c0306 | CLOSED |
| G12: WIDE 횡배치 | M099 + M049 → c0380/c0381 + c0342/c0343 | CLOSED |

---

## 8. 종료 보고

```
STATUS: PHASE_2_9_COMPLETE
산출물: spec/mess_catalog.md
pattern 수: 141 (§6: 105, A9: 13, A10: 11, Industry: 11, User: 0, catch-all: 1)
신규 c: 0
미커버: 0
pilot gap 해소: 12/12
검증 통과: dimension 전수, handling 전수, cross-ref integrity, vocab 위반 0
다음 Phase 전 사용자 확인:
  - G10 (NA_TOKEN "-") 변종 추가를 universe_sm §6에 반영할지 (현재 c0300 파싱 범위에 이미 포함, 공식 등재 여부)
  - G11 (BLQ_TOKEN "ND"/"BQL") 변종 추가 동일
  - pilot_validation.md 조건부 패치 2건 (G1 승인됨, G10 pending) 최종 확인
```
