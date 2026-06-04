# Pilot Validation — Preclinical (Phase P′, read-only probe)

> **목적:** 현 빌드(**57-wired**, 완주 439)가 실물 전임상 소분자 raw의 NONMEM-ready **wrangling lineage를 가이드 cover**하는지 경험 검증.
> **방법:** PROMPTS Phase P 차용. 대상 `raw_data_examples_3/`(Mouse/Rat/Dog Tacrolimus, 한국 CRO 전임상 PK, xlsx 3).
> **★ report-only:** spec/src/tests/render/c_units/universe_sm/decision_tree **무수정**. 기존 `spec/pilot_validation.md`(임상 TDM pilot) **frozen 유지** — 본 문서는 별도 신규.
> **★ symbolic 검증:** orchestrator를 실물 xlsx에 실행하지 않음(raw xlsx ingestion adapter 비존재 = L-5 추출 미구현). universe(`./universe_sm.md`)·anchors(`./anchors.json`, root=GAP-23 경로)·decision_tree.json·REGISTRY(src.orchestrator) **symbolic 매핑**으로 cite-verify.
> **★ probe 등급(통계 게이트 아님):** **n=3 · 단일 CRO 템플릿 · 단일 분자(Tacrolimus) · 단일 endpoint(PK_CONCENTRATION).** clean-route 비율은 일반화 주장 아님.
> baseline: git HEAD=2004d27 · pytest 974 green(무영향).

---

## §1. 파일별 fingerprint (openpyxl 직접 판독)

| 항목 | 1. Mouse PK | 2. Rat PK | 3. Dog PK |
|---|---|---|---|
| 분자/매트릭스 | Tacrolimus / Whole Blood | Tacrolimus / Blood | Tacrolimus / Blood |
| 시트 | Report_Summary·1.Data·**2.Result**·1(1).LCMS·**BW** | 결과처리본·Report_Summary·1.Data·**2.Result**·LCMS·**2.Result(2)** | Report_Summary·1.Data·**2.Result**·**Body weights**·3.LCMS |
| design | SC 7.5/15/30 mg/kg, ICR, **n=3/군** | 2군(1M), DKF-MB101 batch 56/78 | **Advagraf(RLD 대조) vs DKF-MB101(시험)** 3.5/7 mg |
| 샘플링 | **sparse/destructive**(#1-6 시간마다 교대 = 개체 프로파일 불완전) | **longitudinal**(G1=#1-6, G2=#7-12 고유 ID, 0.25~1176hr) | longitudinal + **다회투여**(0/2/4 Day, 48.5/49hr 재투여 dense) |
| conc layout | **wide**(시간=행, 동물 #1-6=열) + Mean/SD 열 | wide + Mean/SD | wide(다 arm) + Mean/SD |
| 시간형식 | hr(decimal) | hr(0.25~1176) | **혼재**: hr · day-fraction(0.0104=15min) · "N Day" 섹션라벨 |
| BLQ표기 | "BQL", "below quantification level", **inline "0.03 (BQL)"** | "BQL, <0.1 ng/mL" | **inline "0.09 (BQL)"**(값+플래그 한 셀) |
| dose 위치 | Report_Summary(mg/kg·route·vehicle) 분리시트 | 시트별 헤더 | Report_Summary + Result 헤더 |
| covariate | **BW 별도시트**(mg/kg→mg) | (BW 시트) | **Body weights 별도시트** |
| QA 혼재 | Standard/DBLK/BLK/LQC·MQC·HQC/Calibration/Dilution QC 가 **실샘플 위에 동일시트 혼재** | 동일 | 동일 |
| 중복/재산출 | **G2/G3 (재산출)** 중복그룹 · Blood 1·2차 배치 | **2.Result(2)** 중복 | Blood 1·2차 |
| 언어/인코딩 | 한글('시험물질','재산출') | 한글('결과 처리본') | 한글('대조약'=RLD,'시험약') |

---

## §2. 2층 사분면 gap map (★ feature × [L1 universe-accept] × [L2 wired])

cite: `universe_sm.md`(line) · `anchors.json` 식별자 · REGISTRY/decision_tree.json. 사분면 = **✓**(accepted+wired) / **○**(accepted+**unwired**=GAP-30 배선) / **✗**(**not-accepted**=universe gap).

| # | feature | L1: universe 수용? (cite) | L2: wired? | 사분면 |
|---|---|---|---|---|
| 1 | 다중시트 inventory | ✓ A10 `SEMI-STRUCTURED`/MULTISHEET(:178)·§6 `SHEET_INVENTORY`(:247) | **DETECT** wired(c0201) | ✓/○ |
| 2 | 시트 **JOIN**(dose/BW→event table) | ✓ §6 SHEET_INVENTORY·A7 covariate(:160) | **unwired** c0110/c0111(Batch D) | ○ |
| 3 | wide(동물=열)→long **PIVOT** | △ §6 `COVARIATE_LAYOUT` wide/long(:253)은 covariate용·`PIVOT ANALYTE_COLUMN`(c0120)은 analyte-wide; **subject-as-column 미명시** | **unwired** c0120 | ○/✗(refine) |
| 4 | Mean/SD 집계열 drop | ✗ 전용 dim 무(파싱 detail) | unwired | ✗(minor) |
| 5 | **QA블록 혼재** 제거(intra-sheet) | ✗ §6 전용 dim 무; A10 SEMI-STRUCTURED 포괄 모호 | unwired | ✗ |
| 6 | dose mg/kg(WEIGHT-BASED) | ✓ A4 `WEIGHT-BASED`(:132)·AIC-PEDS mg/kg(:113) | JOIN/CONVERT **unwired** c0110/c0161 | ○ |
| 7 | route SC/PO | ✓ N3 dose records·A8(:165) | ASSIGN wired(c0010 등); dose-event upstream unwired | ✓/○ |
| 8 | BLQ token("BQL"/"<0.1") | ✓ §6 `BLQ_TOKEN`(:231)·A5 `BLQ-TEXT`(:142) | **wired** c0205/c0305/c0306 | ✓ |
| 9 | **inline BLQ "0.09 (BQL)"**(값+플래그) | △ §6 BLQ_TOKEN은 토큰 나열·**결합셀 미명시** | c0305 토큰파싱(결합셀 미보장) | ✗ |
| 10 | 시간 다형(hr/day-frac/"N Day") | ✓ §6 `TIME_FORMAT` mixed(:232)·`TIME_ANCHOR`(:233)·A3(:127) | **wired** c0203/c0213/c0310-c0315 | ✓ |
| 11 | **다회투여**(재투여 event) | ✓ A4 `ADDL-II`/`LOADING-MAINTENANCE`(:132-134)·Q14(:202) | ASSIGN ADDL/II wired(c0015/c0016); dose-event 재구성 upstream **unwired** | ✓/○ |
| 12 | **RLD 비교**(Advagraf vs 시험) | ✓ A2 `BE`(:125); **✗ formulation 공변량 = `PRODUCT-LEVEL-COVARIATE` out-of-scope(:163)** | unwired | ○/✗(scope-out) |
| 13 | **sparse/destructive 샘플링** | **✗ A2 `PRECLINICAL`(:125)·F19(:219) 도메인은 있으나 sparse/destructive/naive-pool sub-state·Q 무**; N1~N2는 per-subject 프로파일 가정(:61-68) | n/a | ✗(**핵심**) |
| 14 | 재산출/재분석 중복 | ✓ A9 `REANALYSIS-FINAL-DEFINED/MISSING`(:173)·A5 `BIOANALYTICAL-FINAL-FLAG-MISSING`→Q15D(:146) | axis eval wired(c0209); reconcile transform unwired | ✓/○ |
| 15 | 한글/cp949 | ✓ §6 `ENCODING`(:244) | **DETECT** wired(c0216); NORMALIZE unwired | ✓/○ |
| 16 | ID 구성(group×animal열) | ✓ N1(:61)·`ASSIGN ID`(c0018)·§6 `ID_DTYPE`(:235) | ASSIGN ID wired; **pivot upstream unwired** | ✓/○ |
| 17 | NCA-deliverable(Cmax/AUC 시트 무시) | ✓ A10 MULTISHEET→2.Result 선택(:178) | sheet-pick JOIN/inventory **unwired** | ○ |
| 18 | whole-blood matrix | — NONMEM 구조와 무관(농도는 농도) | n/a | out-of-scope(비-이슈) |

**집계(probe, n=3):** ✓ accepted+wired **6** · ○ accepted+**unwired 7**(GAP-30 배선) · ✗ not-accepted **4**(+1 deliberate scope-out, +1 minor).

---

## §3. 파일별 lineage drop-point (현 57-wired가 어디서 사용자를 떨어뜨리나)

의도 lineage: **sheet-select → QA블록 제거 → wide→long PIVOT → dose/BW JOIN → BLQ 정규화 → dose-event → 축평가 → terminal.**

| step | Mouse | Rat | Dog |
|---|---|---|---|
| 1 sheet-select | ⚠ DETECT만(c0201) — 선택/추출 **미실현** | ⚠ | ⚠ |
| 2 QA블록 제거 | ⛔ **not-accepted**(무매핑) | ⛔ | ⛔ |
| 3 wide→long PIVOT | ⛔ **unwired**(c0120) | ⛔ | ⛔ |
| 4 dose/BW JOIN | ⛔ **unwired**(c0110/c0111) | ⛔ | ⛔ |
| 5 BLQ 정규화 | ✓ wired(c0305/c0306) — 단 inline"(BQL)"는 ✗ | ✓ | ⛔ inline BLQ ✗ |
| 6 dose-event | ⚠ ASSIGN wired·재구성 upstream unwired | ⚠ | ⛔ **다회투여 재구성 미실현** |
| 7 축평가(A0-A10) | ✓ wired(c0200-c0216) | ✓ | ✓ |
| 8 terminal | ✓ | ✓ | ✓ |
| **추가 차단** | ⛔ **sparse/destructive 미수용**(13) | — | ⛔ RLD formulation scope-out(12) |

**∴ drop-point 공통:** 실물은 **step 2~4(QA제거·PIVOT·JOIN)에서 막힌다.** 현 빌드는 **tidy long이 주어진 후(step 5~8)**는 가이드하나, raw 다중시트 Excel→tidy long의 **앞단(구조 조립)을 실현 못 함.** 축평가 코어(step 7)는 정확하나 도달 불가. Mouse는 추가로 **sparse 샘플링이 universe에 무매핑**(N1 가정 위반).

---

## §4. 집계 — 보강 후보 vs 배선 항목 (분리)

### (A) not-accepted → ★ universe 패치 후보 (승인 spec-change 대상)
| 결손 | 어디에 추가? | 제안 |
|---|---|---|
| **sparse/destructive/composite 샘플링**(핵심) | A2 sub-state 또는 신규 Q-code | A2에 `PRECLINICAL-SPARSE`/`DESTRUCTIVE-COMPOSITE` 또는 "sampling design → naive-pool vs individual ID policy" Q-code. N1 가정(per-subject 프로파일) 예외 명시. |
| **QA블록 intra-sheet 혼재** | §6 신규 dimension | §6에 `INTRASHEET_QA_BLOCK`(Standard/QC/Calibration vs study-sample 추출) 또는 A10 SEMI-STRUCTURED 처리규칙 명시. |
| **inline BLQ "값 (BQL)"** | §6 BLQ_TOKEN 변종 | §6 BLQ_TOKEN에 "embedded value+flag"(예: `0.09 (BQL)`) 변종 + 파싱규칙(값 보존 + BLQ flag). |
| **subject-as-column conc wide** | §6 COVARIATE_LAYOUT 일반화 또는 신규 | §6에 `CONC_WIDE`/`SUBJECT_AS_COLUMN` 또는 PIVOT ANALYTE_COLUMN scope 확장(subject 축). |
| (minor) Mean/SD 집계열 | §6 또는 pivot 규칙 | aggregate-column drop 규칙(MULTI_LEVEL_HEADER 처리 부속). |
| (scope-out, 보강 아님) RLD formulation 공변량 | A7 PRODUCT-LEVEL(:163) | **현재 의도 out-of-scope** — BE/생동 분석 확장 시 재검토(별도 결정). |

### (B) accepted+unwired → ★ GAP-30 배선 항목 (구조 front-half, Batch C/D/E)
`c0100/c0101/c0102`(sheet VERIFY) · `c0110`(JOIN DOSE_SHEET) · `c0111`(JOIN COVARIATE/BW) · **`c0120`(PIVOT wide→long)** · `c0150`(CLASSIFY REGIMEN) · `c0160`(VERIFY UNIT_CONSISTENCY) · `c0161`(CONVERT UNIT) · `c0170`(ROUTE) · `c0030/c0031/c0040/c0041`(L-1→L-2 schema/dose-event VERIFY/ROUTE). → 이미 [[GAP-30]] 백로그(완주 439→467→5000)에 등재. **이 배선이 step 2~4 drop-point를 해소.**

---

## §5. 판정 (probe 등급) + 다음 Phase

**판정: SELECTIVE-wire (primary) + 소규모 universe-augment (precedent).**

근거:
- **막힘의 다수는 배선 gap(○ 7건)** — universe는 전임상을 nominal 수용(A2 PRECLINICAL·F19·A4 WEIGHT-BASED·A2 BE·A9 REANALYSIS·A10 MULTISHEET). 구조 front-half(JOIN/PIVOT, Batch C/D/E)만 배선하면 step 2~4 drop이 해소된다.
- **단 진짜 not-accepted 소수(✗ 4건)** — 특히 **sparse/destructive 샘플링**은 N1 가정을 위반해 무매핑(전임상 핵심). inline-BLQ·QA블록·subject-wide는 §6 소규모 패치로 수용 가능.
- ∴ **RECOMMEND-asis-clinical 아님**(전임상은 scope 내·대부분 수용) · **full HOLD 아님**(universe 대부분 정상) · **SELECTIVE-wire가 정답**, 단 sparse-sampling 등 ✗4는 배선만으로 안 풀리므로 **선행/병행 소규모 universe 패치** 필요.

**권고 다음 Phase(순서):**
1. **(소규모, 선행) Phase 2.9′ universe 패치** — §4(A)의 sparse-sampling Q/axis-state + inline-BLQ + QA블록 §6 dim 추가(승인 spec-change, cite-verify). *전임상 도메인을 정식 seat.*
2. **(주력) Phase 5 연속 슬라이스 — Batch C/D/E 배선**(구조 front-half): C(c0100-c0102)→D(c0110 JOIN·**c0120 PIVOT**·c0111 BW JOIN·c0161 UNIT)→E(c0030-c0041 dose-event). 실물 우선순위 = **JOIN/PIVOT 먼저**(step 2~4 해소). 완주 439→467→…
3. **(검증) Phase P″ 재-probe** — 동일 3 파일을 재배선 빌드에 통과시켜 drop-point 해소 falsify. (raw xlsx ingester는 별도 결정 — 현재 symbolic.)

**경계(정직):** 본 판정은 **n=3·단일 CRO·단일 분자** probe다. 임상 RWD(원 pilot 7/7)와 직교 도메인이며, 통계적 일반화가 아니라 **방향 신호**다. 더 강한 결론엔 다양 CRO·다분자·다endpoint(EXPOSURE_METRIC/CONTINUOUS_PD 미검증) 확장 probe 필요.

---

## 부록 — cite 원천
- `./universe_sm.md`(root, GAP-23 경로): §1 terminals(:37) · §2 N0-N7(:51) · §3 A0-A10(:102, A2:125·A4:131·A5:138·A7:160·A8:165·A9:170·A10:176) · §4 Q-codes(:183) · §5 families(:213) · §6 Mess(:224).
- `./anchors.json`(root): axes(A0-A10)·q_codes(19)·terminals(5)·families_sm·out_of_scope_identifiers(PRODUCT-LEVEL-COVARIATE 등).
- `spec/decision_tree.json` + `src.orchestrator.REGISTRY`(wired 57): L2 판정 원천.
- 실물: `raw_data_examples_3/{1.Mouse,2.Rat,3.Dog} PK/*.xlsx`(openpyxl read-only).
