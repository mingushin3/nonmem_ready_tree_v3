# Universe-SM v1.1 — Small-Molecule PMX→NONMEM Wrangling Universe (consolidated, scoped, patched)

> **이 파일이 본 프로젝트의 단일 canonical reference다.**
> Frozen Universe v4.1(전문) + v4.2(소분자 관련분)을 small-molecule PK 범위로 합치고,
> pilot 검토에서 확인된 5개 state 구멍(P1–P5)을 패치했다.
> v4.1/v4.2 원본은 `refs/frozen_universe_v4.1.md`, `refs/frozen_universe_v4.2.md`에 provenance로 보관한다.
> 모든 인용은 이 파일의 식별자(axis/state/Q-code/family) + `spec/anchors.json`과 cite-verify 한다.

---

## 0. 설계 철학 (불변)

> **축의 기준: 이 축의 상태가 달라지면 wrangling code path가 달라지는가?** 달라지지 않으면 축이 아니다.

따라서 약물 종류(modality)는 축이 아니다. 본 프로젝트는 modality_class = `SMALL_MOLECULE` 으로 고정하며,
endpoint_data_type ∈ {`PK_CONCENTRATION`, `EXPOSURE_METRIC`, `CONTINUOUS_PD`} 만 다룬다.
v4.2의 신규 modality(CELL_THERAPY/ADC/BISPECIFIC/GENE_THERAPY/MRNA 등)와 그에 딸린 축 state·Q16/Q18/Q19·F24–F29는 **out of scope**.

---

## 0.1 두 개의 universe (★ 본 프로젝트의 핵심 구분 ★)

raw file → NONMEM-ready 문제는 서로 다른 두 universe의 곱집합이다. 둘을 분리해서 다뤄야 강건성이 나온다.

| | Universe A — Scenario/Routing | Universe B — Syntactic Mess |
|---|---|---|
| 질문 | "어떤 study·data 상황이고 deterministic하게 풀리나?" | "토큰을 어떻게 표기했나, 인코딩·구조 결함은?" |
| 결정 단위 | axis state → terminal (분기 많음) | 표기 정규화 (거의 commutative, 분기 거의 없음) |
| 정의처 | 본 파일의 N0–N7 + A0–A10 (§2, §3) | 본 파일의 Mess Catalog (§6) |
| 위치 | 상류 (L-3→L0) | 하류 (L-5→L-3) |

**분기/conditional의 거의 전부는 Universe A(상류)에 산다.** Universe B(하류)는 병렬·순서무관 정규화 파이프라인에 가깝다.
→ decision tree 골격 = N0–N7 + axis routing. Mess Catalog는 그 앞단에 붙는 normalization 전처리.

---

## 1. Terminal States (확정)

| State | 한 줄 정의 | 다음 행동 |
|---|---|---|
| `AUTO` | 정책+데이터 모두 있고, 변환 알고리즘이 유일 출력 | export + audit log |
| `REPAIR` | 정책 있고, deterministic 변환 후 출력 가능 | repair log + export |
| `QUARANTINE` | 데이터는 있으나 결정 불가 — **구체 Q-code 필수** | 사유별 review queue |
| `UNSUPPORTED` | 현재 엔진 기능 밖 | scope expansion 등록 |
| `INVALID` | 핵심 구성요소 부재 | reject + 부재 항목 명시 |

**운영 원칙:** Q-code 없는 QUARANTINE은 시스템 장애로 간주한다. REPAIR은 deterministic 유일 출력 알고리즘이 있을 때만; 정책 없으면 REPAIR이 아니라 QUARANTINE.

---

## 2. Master Decision Nodes N0–N7 (★ Decision Tree 골격 ★)

이 순서가 곧 상류 decision tree다. 모든 strand는 이 골격을 통과한다.

```
N0. Analysis intent가 action-resolving 수준으로 명시되어 있는가?
    → No: Q11 QUARANTINE
    → Yes: N1
    [note] endpoint_data_type 미기재이면 Q11.

N1. Subject-level ID를 안정적으로 구성할 수 있는가?
    → No: INVALID
    → Yes: N2

N2. 시간 순서가 있는 event sequence를 구성할 수 있는가? (dose+obs TIME anchor)
    → 완전 불가: INVALID
    → 정책 필요: Q04/Q12 QUARANTINE
    → 가능: N3

N3. Dose records를 완성할 수 있는가? (AMT, RATE|DUR, CMT for every EVID=1)
    → 불필요(obs-only intent, 예: AIC-ER + EXPOSURE_METRIC): N4
    → 정책 있으면 deterministic: REPAIR → N4
    → 정책 없음: Q06/Q08 QUARANTINE
    → 복원 불가: INVALID

N4. Observation records를 완성할 수 있는가? (DV, CMT, LLOQ for every EVID=0)
    → 정책 있으면 deterministic: REPAIR → N5
    → 정책 없음: Q01/Q09 QUARANTINE
    → 부재: INVALID
    [P4 note] subject 단위 obs 부재(예: dose-only/placebo subject)는
              해당 subject exclude/flag로 처리하고 dataset 전체를 INVALID로 만들지 않는다.
              dataset 전체에 단 하나의 obs도 없을 때만 INVALID.

N5. BLQ/missing/MDV 처리를 적용할 수 있는가?
    → 정책 명시, canonicalization 가능: REPAIR → N6
    → BLQ policy 없음: Q01 QUARANTINE
    → BLQ 없음: N6
    [P1 note] >ULOQ(우측 censoring/희석 초과)도 여기서 함께 판정 (A5 ABOVE-ULOQ).

N6. 명시된 공변량을 붙일 수 있는가?
    → 공변량 없음: N7
    → merge 가능(key + imputation policy 있음): REPAIR → N7
    → key/policy 없음: Q07/Q13 QUARANTINE

N7. 남은 모호성이 threshold 이하인가?
    → Yes: AUTO(N0–N6에 REPAIR 없음) 또는 REPAIR(하나라도 있음)
    → No: 해당 Q-code 발행
```

---

## 3. Axes A0–A10 (small-molecule scoped + 패치 P1–P5)

### A0. Analysis Intent Contract
| Code | 내용 | endpoint_data_type |
|---|---|---|
| AIC-MISSING | 분석 목적 없음 → N0에서 Q11 | — |
| AIC-PK | PK, BLQ/time policy 명시 | 불필요 |
| AIC-POPPK | popPK, occasion policy 명시 | 불필요 |
| AIC-PKPD | PK/PD, endpoint role·CMT policy 명시 | 필수 |
| AIC-ER | exposure-response, exposure metric 정의 | 필수 |
| AIC-DDI | DDI, victim/perpetrator role·CMT 분리 정책 | 불필요 |
| AIC-PEDS | 소아 PK, dose reconstruction(mg/kg·BSA) policy | 불필요 |
| AIC-SPECIAL | 신/간장애, dose adjustment policy | 불필요 |
| AIC-CUSTOM | 위 외, policy 문서 첨부 | 문서 명시 |

endpoint_data_type 허용값(SM): `PK_CONCENTRATION` / `EXPOSURE_METRIC` / `CONTINUOUS_PD`.
(CATEGORICAL_PD/COUNT_PD/TTE_EVENT 및 CELLULAR_KINETICS/IMMUNOGENICITY/MILK/MATERNAL_INFANT는 본 프로젝트 **out of scope** — anchors.json `out_of_scope_identifiers.endpoint_data_types`와 일치. endpoint scope는 anchors.json이 SSOT.)

### A1. Study Integration Level
SINGLE / MULTI-HOMO / MULTI-HETERO / MULTI-SITE / INTERIM.
MULTI 계열은 harmonization policy(A0 명시) 없으면 → Q05.

### A2. Study Design (SM)
PARALLEL / SAD-MAD / CROSSOVER / BE / DDI / FOOD-EFFECT / SPECIAL-POP / PEDIATRIC / TDM-RWD / PRECLINICAL.

### A3. Time Derivation Policy
ACTUAL / NOMINAL-ONLY / ACTUAL-PREFERRED / NOMINAL-PREFERRED / ELAPSED / INTERVAL / AMBIGUOUS(→Q02) / UNRECOVERABLE(→INVALID).
ELAPSED anchor(최초 vs 직전 투약) 불명확 → AMBIGUOUS → Q02.

### A4. Dose Completeness
COMPLETE(AUTO) / WEIGHT-BASED / BSA-BASED / PLANNED-FALLBACK / ADDL-II /
ADDL-ACTUAL-CONFLICT(→Q14) / TITRATION-ADAPTIVE(정책有 REPAIR / 無 Q08) /
LOADING-MAINTENANCE(有 REPAIR / 無 Q08) / INFUSION-STOP-RESTART(有 REPAIR / 無 Q04) /
PARTIAL-RECOVERY(REPAIR+flag) / COMBINATION / MISSING-NO-POLICY(→Q08) / UNRECOVERABLE(→INVALID).
구분 기준: ADDL-II=고정용량 반복, TITRATION-ADAPTIVE=가변용량. 혼재+정책無 → ADDL-ACTUAL-CONFLICT 우선.

### A5. Observation Completeness & BLQ [+ P1, P3]
| Code | 조건 | 처리 |
|---|---|---|
| CLEAN | DV numeric, no BLQ, LLOQ 있음 | AUTO |
| BLQ-FLAGGED / BLQ-TEXT / BLQ-ZERO | BLQ + LLOQ + policy 있음 | REPAIR |
| MULTI-ANALYTE | 복수 analyte, CMT policy 있음 | REPAIR |
| LLOQ-CHANGED | 연구 중 LLOQ 변경, 날짜 기록 | REPAIR + flag |
| MISSING-MDV1 | DV 없음, MDV=1 명시 | AUTO |
| BIOANALYTICAL-FINAL-FLAG-MISSING | DV 후보 복수, final flag 없음 | Q15D |
| **ABOVE-ULOQ [P1 NEW]** | 값이 곡선 위(>ULOQ)/희석 초과; 처리정책 있음 | REPAIR(dilution factor 적용 또는 right-censor flag) |
| **ABOVE-ULOQ-NO-POLICY [P1 NEW]** | >ULOQ인데 처리정책 없음 | Q01 (subtype: uloq) |
| **REPLICATE-SAME-TIME [P3 NEW]** | 동일 (ID,TIME)에 유효 농도 ≥2, 처리정책(평균/우선/둘다 유지) 있음 | REPAIR |
| **REPLICATE-NO-POLICY [P3 NEW]** | 동일 (ID,TIME) 복수 유효 농도, 처리정책 없음 | Q01 (subtype: replicate) |
| BLQ-NO-POLICY / LLOQ-MISSING | 정책/LLOQ 없음 | Q01 |
| ABSENT | 관측값 없음(dataset 전체) | INVALID |

> **P3 주의:** `REPLICATE-SAME-TIME`은 A9 `DUPLICATE-EXACT`(완전중복 행 제거)와 **다르다**. 정당 replicate를 DUPLICATE-EXACT로 처리하면 silent data loss. 동일 (ID,TIME)에 *서로 다른* DV가 있으면 replicate, *동일* DV·전체 행 일치이면 DUPLICATE-EXACT.

### A6. Event Row Classification
SEPARABLE(AUTO) / SAME-TIME-RESOLVABLE / COVARIATE-CHANGE / RESET-NEEDED / URINE-INTERVAL / AMBIGUOUS(→Q04).
(SAME-TIME-RESOLVABLE = *투약+관측* 동시각 순서 정책. *관측+관측* 동시각은 A5 REPLICATE-SAME-TIME 소관.)

### A7. Covariate Attachment (SM)
NONE-REQUIRED(AUTO) / BASELINE-CLEAN(AUTO) / BASELINE-IMPUTABLE / TIME-VARYING / EXTERNAL-JOIN /
KEY-MISSING(→Q13) / POLICY-MISSING(→Q07).
(PEDIATRIC-MATURATION은 AIC-PEDS에서 사용 가능. PRODUCT-LEVEL-COVARIATE는 out of scope.)

### A8. Multi-Drug / CMT Assignment [+ P2]
SINGLE-DRUG(AUTO) / MULTI-CMT-DEFINED / DDI-VICTIM-ONLY / DDI-VICTIM-PERPETRATOR /
METABOLITE-DEFINED / CMT-POLICY-MISSING(→Q09).
> **P2 note (route-differentiated CMT):** 단일 약물이라도 두 경로(예: IV + PO 절대생체이용률)로 투여되어 depot vs central CMT 구분이 필요하면, `SINGLE-DRUG`이 아니라 `MULTI-CMT-DEFINED`로 라우팅한다(분석 의도상 CMT 분리 정책 필요). 정책 없으면 → Q09.

### A9. Data Defect Repairability (SM)
CLEAN(AUTO) / DUPLICATE-EXACT(REPAIR 제거) / UNSORTED / COLUMN-SYNONYM / UNIT-CONVERSION /
ENCODING-FIX / PRE-DOSE-SAMPLE / PLANNED-VS-ACTUAL / PROTOCOL-DEVIATION /
REANALYSIS-FINAL-DEFINED(REPAIR) / REANALYSIS-FINAL-MISSING(→Q15D) /
PROTOCOL-DEVIATION-NO-POLICY(→Q06) / IRRECONCILABLE(→INVALID).

### A10. Source Format Parseability
SDTM-ADaM(AUTO) / EDC-STRUCTURED / CRO-VENDOR / FLAT-TABULAR / LEGACY-NM /
SEMI-STRUCTURED(보조필드 source_parser_subtype: MULTISHEET/PDF-TABLE/CRF-EXPORT/VENDOR-CUSTOM) /
NON-TABULAR(→UNSUPPORTED) / CORRUPTED(→INVALID).

---

## 4. QUARANTINE Q-code Dictionary (SM 부분집합 + P-subtypes + catch-all)

```
Q01  BLQ/LLOQ handling policy not specified
       subtypes: (default) BLQ | uloq [P1] | replicate [P3]
Q02  Time policy (actual vs nominal) not specified / ELAPSED anchor 모호
Q03  Occasion definition not specified
Q04  Dose–sample linkage 또는 row 유형 모호, 정책 없이 해소 불가
Q05  Multi-study ID conflict, harmonization rule 없음
Q06  Protocol deviation handling policy 없음
Q07  Missing covariate imputation policy 없음
Q08  Multiple valid dose sources conflict / dose 복원 정책 없음
Q09  Analyte/CMT assignment policy 없음 (CMT 번호 자체 부재)
Q10  Unit dictionary incomplete
       [P5 note] molar↔mass 변환(nM↔ng/mL)에는 약물별 MW가 dictionary에 있어야 함.
                 MW 부재로 변환 불가 시 Q10.
Q11  Analysis intent insufficient (endpoint_data_type 미기재 포함)
Q12  Time anchor irrecoverable without additional data
Q13  External covariate linkage key 모호
Q14  ADDL/II vs actual dose history conflict, resolution policy 없음
Q15A Data package incomplete — upstream adjudication 미완
Q15B Legacy flag undocumented — flag 의미 확인 불가
Q15C Real-world adherence/administration history unresolved (TDM/RWD 환자진술만)
Q15D Assay reanalysis / final-result adjudication missing
Q15X [catch-all] 위 어디에도 매칭 안 되는 정체불명 결함 (강한 페널티, 최후 수단)
```
**out of scope:** Q16/Q18/Q19 (biologics/special-population 전용).

---

## 5. Family Register (SM operational subset, 참고용)

F01 SDTM/ADaM popPK · F02 Multi-study pooled popPK · F03 EDC multi-table · F04 CRO conc+dosing ·
F05 Flat Excel/CSV · F06 Legacy NM-like · F07 SAD/MAD escalation · F08 Crossover/BA-BE ·
F09 DDI(victim-only) · F22 DDI(victim+perpetrator) · F10 Food-effect · F11 Special pop(renal/hepatic) ·
F12 Pediatric · F13 PK/PD continuous · F14 Exposure-response · F16 External covariate linkage ·
F19 Simple preclinical · F20 TDM/real-world · F21 Urine/interval · F23 Combination therapy.
(F15 TTE/categorical 및 F17/F18, biologics families는 본 프로젝트 **out of scope** — anchors.json `families_sm` 미포함과 일치.)

---

## 6. Mess Catalog (Universe B — L-5 syntactic defects)

v4.1/v4.2가 다루지 않는 부분. **실제 raw file 강건성은 여기서 결정된다.** 각 dimension은 독립 발생 가능.

| 군 | dimension | 통상 표기 변종 |
|---|---|---|
| 결측 | NA_TOKEN | "NA" / "N/A" / "na" / " NA " / blank / "999" / "." / "NULL" |
| BLQ | BLQ_TOKEN | "<LLOQ" / "<0.1" / "BLQ" / "." / "-" / "<LOD" / 0 |
| 시간 | TIME_FORMAT | clock / elapsed / decimal / datetime / mixed |
| 시간 | TIME_ANCHOR | subject별 anchor 상이 / "Day 1" vs "Visit 1" vs date 혼재 |
| 시간 | TIMEZONE | DST crossing / 24h vs 12h+AM/PM |
| ID | ID_DTYPE | string/int 혼재 / leading-zero ("'001") / 중복 |
| 단위 | UNIT_DECLARATION | 단위 표기 누락 / column별 상이 / molar vs mass |
| 셀구조 | MERGED_CELL | 병합 잔존(forward-fill 필요) |
| 셀구조 | MULTI_LEVEL_HEADER | 1–2행 병합 헤더 |
| 셀구조 | TRAILING_BLANK | 꼬리 빈 행 |
| 셀구조 | DUPLICATE_ROW | 완전중복(↔ A5 replicate와 구분) |
| 자연어 | NATURAL_LANGUAGE_DOSE | "100 mg" / "two tablets" |
| 자연어 | NATURAL_LANGUAGE_TIME | "after 30 min" / "predose" |
| 자연어 | FREETEXT_COMMENT | 자유 코멘트 컬럼 |
| 파일 | ENCODING | cp949(한국 Excel) vs UTF-8 / BOM |
| 파일 | LINE_ENDING | LF / CRLF / CR |
| 파일 | DELIMITER | comma / tab / semicolon |
| 파일 | SHEET_INVENTORY | dose 별도 시트 / covariate 별도 시트 |
| Excel | EXCEL_FORMULA | "=SUM(...)" 텍스트 잔존 |
| Excel | EXCEL_DATE_SERIAL | 43000 vs DATE 문자열 |
| Excel | NON_ASCII_DECIMAL | "1,5" = 1.5 (한국식) / thousand sep "1,000" |
| Excel | SCIENTIFIC_NOTATION | 1e3 / 1E+3 / 1*10^3 |
| Excel | LINEBREAK_IN_CELL | 셀 내 줄바꿈 |
| 레이아웃 | COVARIATE_LAYOUT | wide vs long |
| 도메인 | PRE_DOSE_CODING | 음수시간 / "PRE" / t=0 |
| 도메인 | PLACEBO_SUBJECT | AMT=0 / 위약 vs 누락 dose 구분불가 |

**closure 원칙:** 모든 mess pattern은 (a) 처리 c, (b) Q-code, (c) **Q15X catch-all** 중 하나로 100% routing 되어야 한다. 미커버 0개.

---

## 7. Coverage Targets (★ 미검증 목표, 증명은 pilot로 ★)

| 지표 | 정의 | 목표 |
|---|---|---|
| Capture | 어떤 terminal로든 귀속 | ≥99% |
| Review-inclusive | AUTO+REPAIR+QUARANTINE | ≥95% |
| Operational | AUTO+REPAIR | ≥75% |
| Auto-only | AUTO | ≥35% |
| Unsupported+Invalid | — | ≤5% |

이 수치는 **달성 주장이 아니라 검증 대상**이다. freeze 전 실제 raw file 10–20개 pilot fingerprint로 검증한다(§ PROMPTS Phase P).
도달 가능한 정직한 주장은 *"명시적 catch-all(Q15X)을 가진, 모델링된 SM universe에 대한 closed-form coverage"* 이며, "완벽/모든"이 아니다.

---

## 8. 패치 요약 (Universe-SM v1.0이 v4.1/v4.2에 더한 것)

| ID | 위치 | 내용 |
|---|---|---|
| P1 | A5, N5 | `ABOVE-ULOQ` / `ABOVE-ULOQ-NO-POLICY`(→Q01 uloq) — 우측 censoring/희석 초과 |
| P2 | A8 | route-differentiated CMT(IV+PO 단일약물)을 MULTI-CMT-DEFINED로 명시 |
| P3 | A5 | `REPLICATE-SAME-TIME` / `REPLICATE-NO-POLICY`(→Q01 replicate) — 정당 replicate ≠ DUPLICATE-EXACT |
| P4 | N4 | subject 단위 obs 부재는 exclude/flag, dataset INVALID 아님 |
| P5 | Q10 | molar↔mass 변환에 MW 필요 명시 |
| SCOPE | 전역 | SMALL_MOLECULE로 축소, v4.2 신규 modality/Q16-19/F24-29 제거 |
| SCOPE2 (v1.1) | §A0, §5, §8 | CATEGORICAL_PD/COUNT_PD/TTE_EVENT·F15를 "보조"에서 **out-of-scope**로 확정(anchors.json과 일치). review fix. |
