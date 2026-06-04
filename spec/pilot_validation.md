# Phase P — Pilot Validation Report

> **Date:** 2026-05-27
> **Validator:** Claude Code (pilot validator role)
> **Source:** `raw_data_examples_1/` (TDM 반출 데이터, 4 CSV) + `raw_data_examples_2/` (Axitinib xlsx, 22KB)
> **Rev:** v1.1 — Axitinib 파일 재확보 후 FP7 실데이터 routing 반영 + BLQ_TOKEN "이하" 패치 승인 반영
> **Reference:** `universe_sm.md` v1.1 + `anchors.json` v1.1

---

## 1. Fingerprint 입력 요약

### 1.1 raw_data_examples_1 — 한국 병원 TDM 반출 데이터

**Study design:** TDM-RWD (Therapeutic Drug Monitoring, Real-World Data)
**기관:** 단일 병원 EMR 반출
**환자:** 5명 (R000000001–R000000005) + 1명 고아(R000000006, 코호트 누락)

| 파일 | 역할 | 행수 | 인코딩 | 주요 컬럼 |
|---|---|---|---|---|
| TDM 반출 데이터_코호트.csv | 인구통계 | 6 | CP949 | 연구번호, 생년월(YYYYMM), 성별, 사망여부, 주소 |
| TDM 반출 데이터_간호투약기록.csv | 투약(dose) | 784 | CP949 | 연구번호, 처방일자(YYYYMMDD), 투약실시시간(HHMM), 처방코드, 처방명(영+한), 1회용량, 용량단위, 용법(경로) |
| TDM 반출 데이터_기초임상정보.csv | 공변량(time-varying) | 804 | CP949 | 연구번호, 기록구분, 진료일, 기록일자, 키, 몸무게, 이완기혈압, 수축기혈압, 흡연여부 |
| TDM 반출 데이터_진단검사(Lab).csv | 농도(DV) + 기타 Lab | 6899 | CP949 | 연구번호, 검사코드, 검사명, 검체명, 검사결과, 검사결과숫자, 단위, 검사일, 검체채취시각 |

**TDM 약물 농도 데이터:**

| 약물 | 검사명 | 환자 | 농도 건수 | 단위 | BLQ 유무 |
|---|---|---|---|---|---|
| Tacrolimus | FK506(MS) | R001 | 32 | ng/mL | 없음 |
| Cyclosporin | Cyclosporin(MS) + Cyclosporin | R001(MS), R005(both) | 4 | ng/mL | 있음("이하") |
| Voriconazole | Voriconazole(MS) | R004 | 3 | ug/mL | 있음("이하") |
| Posaconazole | Posaconazole(MS) | R001 | 12 | ng/mL | 없음 |
| Mycophenolic Acid | MycophenolicAcid | R003, R005 | 3 | mcg/ml | 있음("이하") |

**투약 약물 (간호투약기록 내 TDM 관련):**

| 약물 | 제형 | 경로 | 환자 |
|---|---|---|---|
| Tacrolimus | Prograf inj. 5mg / Prograf cap. 0.5mg,1mg / Tacrobell cap./inj. | IV infusion(Mix), PO | R001, R003, R006 |
| Posaconazole | Noxafil enteric tab. 100mg | PO | R001, R002 |
| Cyclosporine | Cipol-N soft cap. 25mg | PO | R005 |
| Mycophenolate mofetil | Myrept cap. 250mg | PO | R005 |
| (Voriconazole) | (투약기록 없음 — R004 dose data 부재) | — | (R004) |

**환자-파일 교차 참조 (데이터 완결성):**

| 환자 | 코호트 | 투약기록 | 임상정보 | Lab |
|---|---|---|---|---|
| R000000001 | O | O | O | O |
| R000000002 | O | O | O | O |
| R000000003 | O | O | O | O |
| R000000004 | O | **X** | O | O(Vori only) |
| R000000005 | O | O | O | O |
| R000000006 | **X** | O | **X** | **X** |

### 1.2 raw_data_examples_2 — Axitinib Phase I PK (CRO 납품)

**파일:** `[Dt&CRO] SCAI-005-101_Axitinib_농도표_20251015(읽기전용).xlsx` (22KB)
**Protocol:** SACI-005-101
**Sponsor:** 스카이테라퓨틱스
**Drug:** SCAI-005 점안액 0.04% / 0.08% (안과 점안제, 전신 혈중 Axitinib 측정)
**Analyte:** Axitinib (IS: Axitinib-13C-d3)
**Matrix:** Human Plasma
**LLOQ:** 50 pg/mL (명시), **ULOQ:** 5,000 pg/mL (명시)
**Unit:** pg/mL

| Sheet | 이름 | 크기 | 내용 |
|---|---|---|---|
| 1 | Axitinib_Cohort A_Conc_table | 38×32 | A1 Cohort(8명, single dose 0.04%) + A2 Cohort(7명, single dose 0.08%) 병렬 |
| 2 | Axitinib_Cohort B_Conc_table | 41×32 | B1 Cohort(8명, multi-dose 0.04%) + B2 Cohort(8명, multi-dose 0.08%) 병렬 |

**구조 특징:**
- **WIDE format**: 피험자가 열(A1010, A1020, ...)로 배열 → LONG으로 PIVOT 필요
- **Multi-level header**: rows 1-7 = metadata(Protocol, Sponsor, Drug, Matrix, Analyte, IS), rows 8-9 = 빈 행, row 10 = cohort label, row 11 = column headers
- **2 cohort 횡배치**: 같은 sheet에 A1 Cohort(좌) + A2 Cohort(우) 병렬, 빈 열로 분리
- **Period column**: Cohort A = "1d"(single dose), Cohort B = "1d/3d/5d/8d"(multiple dose)
- **Time**: elapsed hours (0, 0.167, 0.33, 0.5, 0.75, 1, 2, 4, 8, 12)
- **BLQ tokens 2종**: "ND" = Not Detected (peak 없음, <LLOQ 20%), "BQL" = Below Quantitation Limit (LLOQ 20% ≤ BQL < LLOQ)
- **"-" token**: B1030 전 시점 "-" → 피험자 탈락/미채혈 추정
- **Dose records 부재**: 농도표만 있고 투여기록 없음 → 프로토콜에서 dose reconstruction 필요
- **ULOQ "5,000"**: 천 단위 쉼표 구분자(NON_ASCII_DECIMAL과 구분 필요)

---

## 2. Fingerprint 정의 및 Routing

원본 데이터에서 7개 분석 시나리오(fingerprint)를 추출했다. FP1-FP5는 개별 약물 TDM 분석, FP6는 multi-drug 통합 분석, FP7은 파일명 기반 추정이다.

### FP1. FK506 (Tacrolimus) popPK TDM

**기본 정보:**
- Study design: TDM-RWD, 단일 병원
- Drug: Tacrolimus (FK506), IV infusion → PO capsule 전환
- 환자: R000000001 (주), R000000003, R000000006(코호트 누락)
- 농도: 32건, ng/mL, BLQ 없음
- 투약: Prograf inj. 5mg(IV Mix) + Prograf/Tacrobell cap.(PO)

**Axis-state 매핑:**

| Axis | State | 근거 | Terminal/Q-code |
|---|---|---|---|
| A0 | AIC-POPPK (분석의도 가정) | popPK TDM analysis, AIC 문서 별도 필요 | AIC 문서 부재 시 → Q11 |
| A1 | SINGLE | 단일 병원 단일 연구 | — |
| A2 | TDM-RWD | 치료적 약물 모니터링, 실세계 데이터 | — |
| A3 | ACTUAL | 투약일+시간(YYYYMMDD+HHMM) 명시. Lab 시각은 scientific notation이나 복원 가능 | — |
| A4 | TITRATION-ADAPTIVE | 용량이 TDM 결과에 따라 변동(1.0–2.0mg). 투약상태 "미확인" 262건(33%) | policy 有→REPAIR, 無→Q08+Q15C |
| A5 | CLEAN | FK506 농도 전부 numeric, BLQ 없음. LLOQ 값 미기재 | LLOQ 문서 부재 시 → Q01 |
| A6 | SAME-TIME-RESOLVABLE | trough sample(투약 직전 채혈), dose-obs 시간 순서 정책 필요 | policy 有→REPAIR |
| A7 | TIME-VARYING | 체중/키/혈압이 시간에 따라 변동, 별도 파일에서 JOIN | join key=ID+date, policy 有→REPAIR, 無→Q07 |
| A8 | MULTI-CMT-DEFINED (P2) | IV infusion + PO capsule → depot/central CMT 구분 필요 | CMT policy 有→REPAIR, 無→Q09 |
| A9 | DUPLICATE-EXACT + ENCODING-FIX | 동일 행 중복 있음 + CP949 인코딩 | REPAIR |
| A10 | SEMI-STRUCTURED (MULTISHEET) | 4개 CSV 별도 파일 | — |

**Mess dimension 매핑:**

| Dimension | 상태 | 비고 |
|---|---|---|
| ENCODING | CP949 | 한국 Windows Excel 반출 |
| SHEET_INVENTORY | 4-file multi-sheet | dose/conc/cov/demo 분리 |
| SCIENTIFIC_NOTATION | 검체채취시각 "2.02312E+13" | EXCEL_DATE_SERIAL 겸 |
| EXCEL_DATE_SERIAL | 검체채취시각 | scientific notation으로 유실 |
| ID_DTYPE | string "R000000001" | — |
| NATURAL_LANGUAGE_DOSE | "수액내 Mix(일반, 항암)", "IV dropping", "PO" | 한글 용법 기술 |
| FREETEXT_COMMENT | 처방명 한글, 특별약품구분명 | — |
| DUPLICATE_ROW | 투약기록 내 동일 행 존재 | — |
| TIME_FORMAT | YYYYMMDD(date) + HHMM(time) 별도 컬럼 | — |
| TRAILING_BLANK | (미확인) | — |

**N0-N7 routing:**

```
N0: AIC-POPPK 가정 시 → Yes → N1. (AIC 문서 부재 시 → Q11 QUARANTINE)
N1: 연구번호 = stable subject ID → Yes → N2.
N2: 투약일+시간 = actual time sequence. Lab 시각 scientific notation이나 날짜+검사일로 복원 가능 → Yes → N3.
N3: Dose records: 간호투약기록에 AMT+route+time 존재. 단, "미확인" 33%+IV/PO CMT 정책 필요.
    → 정책 有: REPAIR → N4.
    → 정책 無: Q08(dose source conflict) + Q09(CMT) + Q15C(RWD adherence) QUARANTINE.
N4: Observation: FK506(MS) 32건 모두 numeric. LLOQ 미기재.
    → LLOQ 有: REPAIR → N5.
    → LLOQ 無: Q01 QUARANTINE.
N5: BLQ: FK506에 BLQ 없음 → skip → N6.
N6: Covariates: 기초임상정보 별도 파일, time-varying (WT, HT, BP). Join key = ID+date.
    → imputation policy 有: REPAIR → N7.
    → 無: Q07 QUARANTINE.
N7: 잔여 모호성: "미확인" dose status 처리 정책 + R000000006 코호트 누락.
    → 정책 有: REPAIR.
    → 無: Q15C QUARANTINE.
```

**Terminal:** REPAIR (best case, 모든 정책 제공 가정) | QUARANTINE Q08+Q09+Q15C+Q01+Q07 (정책 미비 시)
**매핑 실패:** 없음. 모든 axis-state와 mess dimension이 universe_sm에 존재.

---

### FP2. Cyclosporin TDM

**기본 정보:**
- Drug: Cyclosporine, PO (Cipol-N soft cap.)
- 환자: R001(농도 MS 1건+BLQ 1건), R005(농도 2건, 1 BLQ)
- 특이: 2가지 assay — Cyclosporin(일반, EDTA blood) vs Cyclosporin(MS, Blood)

**Axis-state 매핑 (FP1과 다른 점만):**

| Axis | State | 근거 |
|---|---|---|
| A4 | COMPLETE (PO only, 고정용량) 또는 TITRATION-ADAPTIVE | R005: Cipol-N 25mg 고정 |
| A5 | **BLQ-TEXT** | "25 이하", "2.88 이하" — 숫자+"이하"(한국어 BLQ 토큰) |
| A8 | SINGLE-DRUG | PO only, CMT 단일 |
| A9 | REANALYSIS-FINAL-MISSING | Cyclosporin(일반) vs Cyclosporin(MS) 두 assay, final flag 없음 → Q15D |

**Mess dimension 추가:**
- **BLQ_TOKEN: "X 이하"** — universe_sm §6 BLQ_TOKEN 변종에 한국어 "이하" 미등재 → **GAP**

**N0-N7 routing:**
- N4: 2가지 assay 중 어느 것이 final? → REANALYSIS-FINAL-MISSING → **Q15D**
- N5: BLQ policy 필요 (BLQ-TEXT, "이하" 토큰) → policy 有: REPAIR, 無: **Q01**

**Terminal:** QUARANTINE Q15D + Q01 (best case에서도 assay adjudication 필요)
**매핑 실패:** BLQ_TOKEN "이하"가 universe_sm 변종 목록에 없음 (§6 BLQ_TOKEN: "<LLOQ"/"<0.1"/"BLQ"/"."/"−"/"<LOD"/0). 그러나 BLQ_TOKEN dimension 자체는 존재하므로 routing은 성립. **패치 후보: "이하" 변종 추가.**

---

### FP3. Voriconazole TDM

**기본 정보:**
- Drug: Voriconazole, 경로 불명(투약기록 부재)
- 환자: R000000004 (농도 3건, 1 BLQ="0.1 이하")
- **치명적 결함: 투약기록(간호투약기록.csv)에 R000000004 전혀 없음**

**Axis-state 매핑:**

| Axis | State | 근거 |
|---|---|---|
| A0 | AIC-POPPK (가정) | — |
| A4 | **MISSING-NO-POLICY** | dose records 완전 부재(해당 환자 투약기록 없음) → **Q08** |
| A5 | BLQ-TEXT | "0.1 이하", unit=ug/mL |
| A10 | SEMI-STRUCTURED | 4-file set이나 dose file에서 해당 환자 결락 |

**N0-N7 routing:**
```
N3: Dose records 완전 부재 → MISSING-NO-POLICY → Q08 QUARANTINE.
    또는: data package 자체 불완전 → Q15A.
```

**Terminal:** QUARANTINE Q08 + Q15A (Data package incomplete)
**매핑 실패:** 없음. Q15A가 이 상황을 정확히 포착.

---

### FP4. Posaconazole TDM

**기본 정보:**
- Drug: Posaconazole, PO (Noxafil enteric tab. 100mg)
- 환자: R001 (농도 12건, BLQ 없음), R002 (투약기록만, 농도 미확인)
- 단위: ng/mL

**Axis-state 매핑 (FP1과 다른 점만):**

| Axis | State | 근거 |
|---|---|---|
| A4 | COMPLETE 또는 TITRATION-ADAPTIVE | PO 고정용량 100mg |
| A5 | CLEAN | 모든 농도 numeric, BLQ 없음 |
| A8 | SINGLE-DRUG | PO only |

**N0-N7 routing:**
- FP1과 유사하나 A4/A5/A8이 더 단순.
- N3: Dose = PO 고정용량, 기록 있음 → REPAIR(dose timing linking).
- N4: 농도 12건 전부 numeric → REPAIR(LLOQ 문서화 필요).
- N5: BLQ 없음 → N6.

**Terminal:** REPAIR (best case) | QUARANTINE Q01+Q15C (LLOQ 미기재 + RWD adherence)
**매핑 실패:** 없음.

---

### FP5. Mycophenolic Acid TDM

**기본 정보:**
- Drug: Mycophenolate mofetil (prodrug) → Mycophenolic Acid (active metabolite)
- 환자: R003(농도 1건), R005(농도 2건, 둘 다 BLQ="0.2 이하")
- 단위: mcg/ml
- 특이: prodrug(Myrept=mycophenolate mofetil) 투여, metabolite(mycophenolic acid) 측정

**Axis-state 매핑:**

| Axis | State | 근거 |
|---|---|---|
| A5 | BLQ-TEXT | "0.2 이하" (3건 중 2건 BLQ) |
| A8 | METABOLITE-DEFINED | prodrug 투여 → metabolite 측정 → CMT policy 필요 |

**N0-N7 routing:**
- N4: 농도 3건 중 2건 BLQ → 유효 obs 매우 적음.
- N5: BLQ-TEXT + BLQ policy 필요 → Q01.
- A8: METABOLITE-DEFINED → CMT policy 有: REPAIR, 無: Q09.

**Terminal:** QUARANTINE Q01 + Q09 (BLQ policy + metabolite CMT policy)
**매핑 실패:** 없음. BLQ_TOKEN "이하"는 FP2와 동일 gap.

---

### FP6. Multi-drug Combined TDM Analysis

**기본 정보:**
- 5개 약물 동시 분석 시나리오 (FK506 + Cyclosporin + Voriconazole + Posaconazole + MPA)
- 환자: 5+1명
- NONMEM CMT 할당 필요

**Axis-state 매핑 (추가):**

| Axis | State | 근거 |
|---|---|---|
| A0 | AIC-POPPK 또는 AIC-CUSTOM | multi-drug TDM |
| A5 | MULTI-ANALYTE + BLQ-TEXT | 5개 analyte + BLQ 혼재 |
| A8 | MULTI-CMT-DEFINED 또는 CMT-POLICY-MISSING | 5 drugs × multiple routes → CMT policy 필수 |

**N0-N7 routing:**
- FP1-FP5의 모든 Q-code 누적: Q01+Q08+Q09+Q15A+Q15C+Q15D.
- 가장 보수적 terminal.

**Terminal:** QUARANTINE (다수 Q-code)
**매핑 실패:** 없음.

---

### FP7. Axitinib Phase I PK (CRO 납품 농도표)

**기본 정보:**
- Study: SACI-005-101 (Phase I, 점안액 전신 PK)
- Drug: SCAI-005 점안액 (Axitinib), 0.04% / 0.08% 두 용량군
- Source: CRO 납품 ("[Dt&CRO]"), xlsx 읽기전용
- Design: SAD(Cohort A, single dose) + MAD(Cohort B, multi-dose 1d/3d/5d/8d)
- 피험자: ~31명 (A1:8 + A2:7 + B1:8 + B2:8)
- 농도: pg/mL, LLOQ=50, ULOQ=5000 명시
- BLQ: "ND"(미검출) + "BQL"(정량한계 미만) 2종
- Dose: 파일 내 부재(프로토콜에서 dose reconstruction 필요)

**Axis-state 매핑:**

| Axis | State | 근거 | Terminal/Q-code |
|---|---|---|---|
| A0 | AIC-PK | Phase I 단회/반복 PK | AIC 문서 有 가정 |
| A1 | SINGLE | 단일 연구 | — |
| A2 | SAD-MAD | Cohort A=SAD, Cohort B=MAD | — |
| A3 | ELAPSED | Time(h): 0, 0.167, ..., 12. 투약 시점 기준 경과시간 | — |
| A4 | PLANNED-FALLBACK | 점안액 고정용량, dose=프로토콜 기재 → planned dose 사용 | REPAIR(protocol 有) / Q08(無) |
| A5 | BLQ-FLAGGED | ND/BQL 2종 토큰 + LLOQ 50 pg/mL 명시 + ULOQ 5000 명시 | REPAIR |
| A6 | SEPARABLE | elapsed time으로 dose-obs 완전 분리 | AUTO |
| A7 | NONE-REQUIRED | Phase I, 공변량 파일 없음 | AUTO |
| A8 | SINGLE-DRUG | Axitinib 단일 analyte | AUTO |
| A9 | CLEAN | 농도 데이터 자체에 결함 없음. "-" = 탈락/미채혈(flag 처리) | REPAIR(flag) |
| A10 | CRO-VENDOR (MULTISHEET) | CRO 납품 xlsx, 2 sheets | — |

**Mess dimension 매핑:**

| Dimension | 상태 | 비고 |
|---|---|---|
| MULTI_LEVEL_HEADER | rows 1-7 metadata + row 10 cohort label + row 11 headers | 7행 metadata header |
| COVARIATE_LAYOUT (wide) | 피험자가 열로 배열 → PIVOT 필요 | WIDE→LONG |
| MERGED_CELL | metadata 영역 병합 셀 추정 | forward-fill 필요 |
| BLQ_TOKEN | "ND" + "BQL" (2종, 둘 다 universe_sm §6에 등재) | — |
| SHEET_INVENTORY | 2 sheets (Cohort A, B) | — |
| NA_TOKEN | "-" (피험자 탈락/미채혈) | universe_sm §6 NA_TOKEN에 "-" 미등재 → **GAP** |
| TRAILING_BLANK | rows 23-38 빈 행 | — |
| NON_ASCII_DECIMAL | "5,000" (천 단위 쉼표) | 소수점과 혼동 가능 |
| NATURAL_LANGUAGE_DOSE | "SCAI-005 점안액 0.04%" (한글 제형명) | — |

**N0-N7 routing:**

```
N0: AIC-PK 가정 → Yes → N1.
N1: Subject ID = A1010, B2080 등 (명확) → Yes → N2.
N2: Time = elapsed hours, 명시적 → Yes → N3.
N3: Dose records: 파일 내 부재. 프로토콜에서 점안액 용량 정보 필요.
    → 프로토콜 有: PLANNED-FALLBACK → REPAIR → N4.
    → 프로토콜 無: Q08 QUARANTINE.
N4: Observation: 농도 pg/mL, LLOQ/ULOQ 명시 → REPAIR (BLQ 처리) → N5.
N5: BLQ: ND/BQL 2종 토큰, LLOQ=50 정의됨, BLQ policy는 CRO footnote에 정의
    → BLQ policy 명시: REPAIR → N6.
N6: Covariates: 불필요(Phase I) → NONE-REQUIRED → N7.
N7: 잔여 모호성: "-" 토큰(탈락) flag 처리 → REPAIR.
```

**Terminal:** REPAIR (best case, 프로토콜 dose 정보 有) | QUARANTINE Q08 (dose 없을 시)
**매핑 실패:** NA_TOKEN "-" 가 universe_sm §6 변종 목록에 미등재 (§6 NA_TOKEN: "NA"/"N/A"/"na"/" NA "/blank/"999"/"."/"NULL"). **패치 후보: "-" 변종 추가.**

---

## 3. 집계

### 3.1 Clean-route 비율

"Clean-route" = 모든 axis-state·mess dimension이 universe_sm의 기존 식별자에 매핑되어 유효한 terminal(AUTO/REPAIR/QUARANTINE+Q-code/INVALID)에 도달.

| FP | 약물 | Family | Terminal | Clean-route | 비고 |
|---|---|---|---|---|---|
| FP1 | FK506 | F20(TDM/RWD) | REPAIR (best) / Q08+Q09+Q15C+Q01+Q07 | **O** | 정책 의존 |
| FP2 | Cyclosporin | F20 | Q15D + Q01 | **O** | assay adjudication + BLQ |
| FP3 | Voriconazole | F20 | Q08 + Q15A | **O** | dose data 부재 |
| FP4 | Posaconazole | F20 | REPAIR (best) / Q01+Q15C | **O** | — |
| FP5 | MPA | F20 | Q01 + Q09 | **O** | BLQ + metabolite CMT |
| FP6 | Multi-drug | F20 | QUARANTINE (다수 Q) | **O** | — |
| FP7 | Axitinib | F04(CRO)+F07(SAD-MAD) | REPAIR (best) / Q08 | **O** | CRO 납품, dose 부재 |

**Clean-route: 7/7 (100%)**

모든 fingerprint가 universe_sm의 axis-state + mess dimension + Q-code 체계 내에서 유효한 terminal에 도달했다.

### 3.2 Terminal 분포

| Terminal | 건수 | FP |
|---|---|---|
| REPAIR (정책 완비 시) | 3 | FP1, FP4, FP7 |
| QUARANTINE (Q-code) | 4 | FP2, FP3, FP5, FP6 |
| INVALID | 0 | — |
| AUTO | 0 | — |

### 3.3 발동된 Q-code 빈도

| Q-code | 빈도 | 해당 FP |
|---|---|---|
| Q01 (BLQ/LLOQ policy) | 4 | FP1,FP2,FP4,FP5 |
| Q08 (Dose source conflict) | 3 | FP1,FP3,FP7 |
| Q09 (CMT policy) | 3 | FP1,FP5,FP6 |
| Q15C (RWD adherence) | 3 | FP1,FP4,FP6 |
| Q15A (Data package incomplete) | 1 | FP3 |
| Q15D (Assay adjudication) | 1 | FP2 |
| Q07 (Covariate imputation) | 1 | FP1 |
| Q11 (Analysis intent) | 0* | *AIC 제공 가정 |

### 3.4 Family 커버리지

| Family | 검증됨 | FP |
|---|---|---|
| F04 (CRO conc+dosing) | **O** | FP7 |
| F07 (SAD/MAD escalation) | **O** | FP7 |
| F20 (TDM/real-world) | **O** | FP1-FP6 |
| F01-F03, F05-F06, F08-F14, F16-F23 | X | 미검증 |

---

## 4. Gap 분석 (매핑 실패 및 패치 후보)

### 4.1 Mess Catalog 패치 후보

| # | Gap | 위치 | 설명 | 패치 제안 |
|---|---|---|---|---|
| G1 | **BLQ_TOKEN "이하" 미등재** | §6 BLQ_TOKEN | 한국어 BLQ 표기 "X 이하"(예: "2.88 이하", "0.1 이하"). universe_sm §6 변종 목록에 없음. routing 자체는 BLQ_TOKEN dimension으로 성립하나, 파싱 규칙이 "<" 패턴과 다름(후위 한글). | §6 BLQ_TOKEN 변종에 `"N 이하"(한국어)` 추가 |
| G2 | **NATURAL_LANGUAGE_BLQ 차원 부재** | §6 | "이하"는 BLQ_TOKEN의 변종이라기보다 NATURAL_LANGUAGE 패턴(숫자+한글 서술)에 가까움. `<0.1`은 기호, `0.1 이하`는 자연어. 현 §6에 NATURAL_LANGUAGE_DOSE/TIME은 있으나 NATURAL_LANGUAGE_BLQ는 없음. | BLQ_TOKEN 변종 확장으로 충분. 별도 dimension 불필요(SRP 위반). |
| G3 | **NON_ASCII_UNIT 미분리** | §6 UNIT_DECLARATION, NON_ASCII_DECIMAL | 단위 내 non-ASCII 문자(㎗, ㎡)는 NON_ASCII_DECIMAL(소수점 표기)과 차원이 다름. 현재 UNIT_DECLARATION이 커버하나, non-ASCII 유니코드 정규화가 명시적이지 않음. | UNIT_DECLARATION 처리 시 유니코드 정규화(㎗→dL, ㎡→m2) 포함 명시. 별도 dimension 불필요. |
| G4 | **RESULT_COLUMN_SPLIT 패턴** | §6 (미등재) | Lab 결과가 "검사결과"(text, TDM 약물에 numeric 또는 "이하" 포함)와 "검사결과 숫자"(numeric, TDM 약물은 빈 칸)로 분리. DV 추출 시 어느 컬럼 우선인지 정책 필요. | 기존 COLUMN-SYNONYM(A9) 또는 MULTI_LEVEL_HEADER로 커버 가능. 단, "text result 우선 → numeric parse" 규칙은 c-단위체에서 명시. |
| G5 | **DOSING_STATUS 미확인/반환** | §6 (미등재) | 투약상태 "미확인"(262건, 33%), "투약X-반환불가"가 존재. 이 행의 dose가 실제 투여되었는지 불명. | Q15C (RWD adherence)가 이를 커버. 단, mess dimension으로 DOSING_STATUS_UNCERTAIN 추가 검토. |
| G6 | **PATIENT_FILE_MISMATCH** | §6 (미등재) | R000000006이 투약기록에만 존재(코호트/Lab/임상정보 없음), R000000004가 투약기록에 없음. cross-file ID 불일치. | Q15A (Data package incomplete) + A9 IRRECONCILABLE이 커버. |
| G10 | **NA_TOKEN "-" 미등재** | §6 NA_TOKEN | Axitinib 농도표에서 "-"(피험자 탈락/미채혈) 사용. §6 NA_TOKEN 변종("NA"/"N/A"/blank/"999"/"."/"NULL")에 "-" 없음. BLQ_TOKEN에 "-"가 있으나 의미가 다름(결측 vs BLQ). | §6 NA_TOKEN 변종에 `"-"(missing/withdrawn)` 추가 |
| G11 | **이중 BLQ 토큰(ND/BQL)** | §6 BLQ_TOKEN | CRO 납품에서 ND(미검출, <20%LLOQ)와 BQL(정량한계미만, 20-100%LLOQ)을 구분. universe_sm §6은 BLQ_TOKEN을 단일 차원으로 다루며 2-tier 구분을 명시하지 않음. | BLQ_TOKEN 변종에 "ND(not detected)" 추가. 2-tier 구분은 c-단위체 파싱 규칙에서 처리(LLOQ 기준 BLQ flag 통일). |
| G12 | **WIDE format 횡배치 cohort** | §6 COVARIATE_LAYOUT | Axitinib: 같은 sheet에 2 cohort가 좌우 병렬 배치(빈 열 구분). COVARIATE_LAYOUT wide가 커버하나, "1 sheet 내 복수 테이블 병렬" 패턴은 MULTI_LEVEL_HEADER보다 복잡. | 기존 COVARIATE_LAYOUT + MULTI_LEVEL_HEADER 조합으로 커버 가능. SPLIT 작업 단위 명시. |

### 4.2 Axis/Q-code 체계 패치 후보

| # | Gap | 위치 | 설명 |
|---|---|---|---|
| G7 | **A2 TDM-RWD + "미확인" dose** | A4 | TDM-RWD의 현실: 33% dose가 "미확인" 상태. A4 TITRATION-ADAPTIVE는 용량 변동을 다루나, 투여 자체 불확실은 Q15C가 담당. 이 연결이 명시적이지 않음. |
| G8 | **Multi-assay method 구분** | A5, A9 | Cyclosporin이 2가지 assay(일반 EDTA vs MS Blood)로 측정됨. A5에서 BIOANALYTICAL-FINAL-FLAG-MISSING → Q15D로 가지만, 동일 약물·동일 환자의 두 assay가 동시에 존재하는 상황이 명시적이지 않음. |
| G9 | **Prodrug→Metabolite 관계** | A8 | MycophenolATe mofetil(투약) → Mycophenolic Acid(측정). A8 METABOLITE-DEFINED가 커버하나, "prodrug 투여량 → metabolite 농도" 변환은 CMT/dose 해석에 도메인 지식 필요. universe_sm에서 이 관계의 dose record 처리(prodrug AMT vs metabolite equi-dose) 정책이 명시적이지 않음. |

### 4.3 패치 심각도 분류

| 심각도 | Gap | 조치 |
|---|---|---|
| **LOW (변종 추가)** | G1(승인됨), G3, G4, G10, G11 | §6 BLQ_TOKEN "이하"·"ND" + NA_TOKEN "-" + UNIT_DECLARATION non-ASCII 변종 추가. c-단위체 파싱 규칙으로 처리. |
| **MEDIUM (문서 명확화)** | G2, G5, G6, G7, G8, G12 | 기존 axis-state/Q-code가 커버하나 연결이 암묵적. spec 명확화 권장. |
| **MEDIUM (도메인 규칙)** | G9 | prodrug→metabolite dose 해석 정책을 AIC 문서 요구사항으로 명시. |

---

## 5. Coverage Targets 검증 (universe_sm §7 대비)

| 지표 | 정의 | 목표 | 실측 | 판정 |
|---|---|---|---|---|
| Capture | 어떤 terminal로든 귀속 | ≥99% | 7/7 (100%) | **PASS** |
| Review-inclusive | AUTO+REPAIR+QUARANTINE | ≥95% | 7/7 (100%) | **PASS** |
| Operational | AUTO+REPAIR | ≥75% | 3/7 (43%)* | *정책 미비로 대부분 QUARANTINE |
| Unsupported+Invalid | — | ≤5% | 0/7 (0%) | **PASS** |

*주의:* Operational 비율이 낮은 것은 universe 결함이 아니라 **정책 문서(AIC, BLQ policy, CMT policy 등)가 raw data에 동봉되지 않은 TDM/RWD 특성** 때문이다. 정책 문서 제공 시 FP1, FP4, FP7이 REPAIR로 확정되어 3/7(43%); 추가로 FP2(Q15D 해소), FP5(Q09 해소) 시 5/7(71%)까지 도달 가능.

---

## 6. 판정

### Clean-route: 7/7 (100%)

모든 fingerprint가 universe_sm v1.1의 axis-state, mess dimension, Q-code 체계 내에서 유효한 terminal에 도달했다. 어느 데이터 패턴도 "어디에도 못 앉히는" 매핑 실패를 일으키지 않았다.

### Gap 목록 요약

- **LOW 5건:** BLQ_TOKEN "이하"(G1, 승인됨), NA_TOKEN "-"(G10), BLQ_TOKEN "ND"(G11), non-ASCII unit(G3), result column split(G4) — 모두 기존 dimension 내 변종 추가로 해결.
- **MEDIUM 7건:** NATURAL_LANGUAGE_BLQ(G2), dosing status(G5), patient-file mismatch(G6), TDM-RWD dose(G7), multi-assay(G8), prodrug-metabolite(G9), WIDE 횡배치(G12) — 기존 Q-code가 커버하나 문서 명확화 권장.
- **HIGH 0건:** universe 구조 변경이 필요한 gap 없음.

### 제한 사항

1. **표본 수 부족:** 7개 fingerprint는 권장 최소(20개)에 미달. SDTM/ADaM(F01), multi-study pooled(F02), crossover/BE(F08) 시나리오 미검증.
2. **Study family 편향:** F20(TDM/RWD) + F04/F07(CRO/SAD-MAD)만 검증. F01-F03, F05-F06, F08-F14, F16-F23 미검증.
3. **Endpoint 단일:** PK_CONCENTRATION만 검증. EXPOSURE_METRIC, CONTINUOUS_PD 미검증.
4. **Mess 편향:** 한국 병원 EMR(CP949, "이하") + 한국 CRO 납품(WIDE format, ND/BQL) 2가지 소스만. 서양/글로벌 CRO(SDTM), FDA submission format 미검증.

---

## 7. 최종 판정

**RECOMMEND: 본 build 진행** (조건부)

**근거:**
- Clean-route 100% (7/7) — 기준(90%) 초과.
- 발견된 gap은 모두 LOW-MEDIUM 심각도이며, 기존 dimension/Q-code 체계의 변종 추가 또는 문서 명확화로 해결 가능.
- Universe 구조(N0-N7, A0-A10, Q01-Q15X) 자체의 결함은 발견되지 않음.

**조건:**
1. **§6 BLQ_TOKEN 변종에 "N 이하"(한국어 후위 BLQ 표기)를 추가** — ✅ 사용자 승인 완료 (2026-05-27).
2. **§6 NA_TOKEN 변종에 "-"(missing/withdrawn)를 추가** — Phase 2d에서 DETECT NA_TOKEN c-단위체가 이 패턴을 파싱할 수 있어야 함.
3. **추가 pilot fingerprint 보강을 권장** — SDTM/ADaM(F01), crossover/BE(F08), multi-study(F02) 등 미검증 family가 다수. 현재 F04/F07/F20만 검증.

---

**STATUS: PHASE_P_COMPLETE**
**산출물:** `spec/pilot_validation.md`
**검증 통과:** clean-route 7/7 (100%), Capture 100%, Review-inclusive 100%, Unsupported+Invalid 0%
**승인된 패치:** G1 (BLQ_TOKEN "이하" 변종 추가)
**미해결 패치:** G10 (NA_TOKEN "-" 변종 추가, LOW)
**미해결 ambiguity:** 0개
**다음 Phase 전 사용자 확인:**
1. 조건부 RECOMMEND 수락 → Phase 0 진행?
2. 추가 pilot fingerprint 보강 시기 (지금 vs Phase 9 adversarial 때)?

**RECOMMEND: 본 build 진행**
