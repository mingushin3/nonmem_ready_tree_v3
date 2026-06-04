## Frozen Universe v4.2 검토 및 개선안

---

### Part 0. v4.1 독립 검토 및 v4.2 보강 근거

#### 0.1 검토 판정 기준 재확인

두 개의 평가 의견을 검토하기 전에, 판정 기준을 v4.1과 동일하게 유지한다.

> **패치 채택 기준: 해당 변경이 없으면 wrangling code path가 잘못된 terminal state를 산출하거나, QUARANTINE Q-code가 구조적으로 잘못 발행되는가?**

Q-code가 부정확하지만 terminal state(AUTO/REPAIR/QUARANTINE/UNSUPPORTED/INVALID)는 올바른 경우 — "정밀도 개선"으로 분류하고, 채택 우선순위를 낮춘다. Terminal state 자체가 틀릴 수 있는 경우 — "code path 오류"로 분류하고, 필수 패치로 채택한다.

#### 0.2 v4.1이 이미 올바르게 처리하는 영역

Document 3의 판단은 핵심에서 옳다. v4.1의 설계 철학(약물 종류가 아니라 wrangling code path 분기점만 축으로 삼는 것)은 대부분의 새 모달리티를 흡수한다.

구체적으로, 아래는 v4.1이 **이미 올바른 terminal state를 산출하는** 시나리오다.

|모달리티/집단|v4.1 처리 경로|Terminal state 정확도|
|---|---|---|
|ADC (단순 multi-analyte)|A8 MULTI-CMT-DEFINED 또는 CMT-POLICY-MISSING → Q09|정확|
|이중항체 PK|A8 MULTI-CMT-DEFINED + A5 MULTI-ANALYTE|정확|
|소아 PK (weight/BSA 기반)|A4 WEIGHT-BASED/BSA-BASED + A7 PEDIATRIC-MATURATION|정확|
|희귀질환 sparse PK|A3 NOMINAL-ONLY + A7 EXTERNAL-JOIN|정확|
|mRNA prime-boost 투약|A4 LOADING-MAINTENANCE (두 phase 상이)|정확 (REPAIR로 귀속)|
|TDM/RWD 희귀질환|A2 TDM-RWD + A4 TITRATION-ADAPTIVE|정확|
|raw FACS/qPCR (비정형)|F24(구) UNSUPPORTED|정확|

#### 0.3 v4.1에서 실제 code path 오류가 발생하는 영역

두 평가 의견을 교차 검증한 결과, terminal state가 잘못 산출될 위험이 있는 시나리오는 정확히 세 가지다.

**오류 1. CELLULAR_KINETICS DV — 잘못된 REPAIR 경로**

v4.1에서 CAR-T cellular kinetics 데이터(cells/μL, copies/μg DNA)는 A0의 `endpoint_data_type=CONTINUOUS_PD`로 귀속된다. 문제는 A5의 BLQ/LLOQ 처리 경로다. CONTINUOUS_PD를 가정하면 표준 농도-시간 방식의 LLOQ와 REPAIR 알고리즘이 적용되는데, 세포 수 기반 데이터의 LLOQ는 Poisson 통계 기반으로 완전히 다르다. LLOQ policy가 "있음"이면 REPAIR로 진행하지만, 실제로는 잘못된 BLQ canonicalization이 수행된다. 즉 **silent error REPAIR**가 발생한다.

**오류 2. IMMUNOGENICITY adjudication — 잘못된 Q-code 발행**

ADA/NAb titer 데이터에서 positivity adjudication rule이 없으면, v4.1은 Q01(BLQ handling policy not specified)을 발행한다. 그런데 ADA positivity는 BLQ 문제가 아니라 **DV 값 자체를 결정하는 pre-processing 규칙** 부재의 문제다. Q-code가 잘못 발행되면 리뷰 큐에서 담당자가 엉뚱한 해결책을 찾게 된다. terminal state는 QUARANTINE으로 올바르지만, Q-code가 구조적으로 부정확하다.

**오류 3. MATERNAL_INFANT dyad — N1 INVALID 오판 가능성**

수유부 mother-infant pair 연구에서 모체 혈장, 모유, 영아 혈장이 모두 존재하면, 현재 N1("Subject-level ID를 안정적으로 구성할 수 있는가?")에서 판단이 불명확해진다. 모체 ID와 영아 ID가 별도 레코드로 존재할 경우, ID 구성 실패로 INVALID로 빠질 수 있다. 실제로는 dyad linkage key가 있으면 처리 가능한데 INVALID로 오판되는 구조적 위험이 있다.

#### 0.4 채택/기각 판정 요약

|Document 2 제안|채택 여부|판단 근거|
|---|---|---|
|A0 `modality_class` 보조 필드|**채택**|가족 레지스터 라우팅 명확화 + audit trail. 축 아님, 보조 필드|
|endpoint_data_type: CELLULAR_KINETICS|**필수 채택**|code path 오류 (silent REPAIR) 방지|
|endpoint_data_type: IMMUNOGENICITY|**채택**|Q-code 정확도 문제 → Q19 연동|
|endpoint_data_type: MILK_PK|**채택**|모유 matrix는 N4에서 CMT/LLOQ가 plasma와 구조적으로 다름|
|endpoint_data_type: MATERNAL_INFANT_PK|**필수 채택**|N1 오판 방지|
|endpoint_data_type: TARGET_ENGAGEMENT|**기각**|CONTINUOUS_PD로 충분. 별도 code path 없음|
|endpoint_data_type: BIODISTRIBUTION|**기각**|조직 농도는 대부분 UNSUPPORTED 영역|
|A8 `analyte_role` 보조 필드|**채택**|Q09 root-cause 진단 정밀도. 축 아님, A8 보조 필드|
|A7 PRODUCT-LEVEL-COVARIATE 상태|**채택**|CAR-T lot→subject 역방향 join key. 기존 EXTERNAL-JOIN과 code path 상이|
|A7 LIFE-STAGE-COVARIATE 상태|**기각**|기존 TIME-VARYING + A3 주석으로 충분. 별도 code path 없음|
|A3 delivery/postpartum anchor 주석|**채택**|ELAPSED 모호성과 동일 구조의 anchor 문제|
|N1 dyad linkage 명시|**필수 채택**|INVALID 오판 방지|
|Q16 analyte role policy missing|**채택**|Q09 subtype으로 정밀도 향상. ADC/CAR-T 실무에서 반복 발생|
|Q17 product-level covariate linkage|**기각**|Q13(external covariate key)으로 흡수 가능|
|Q18 maternal-infant linkage ambiguous|**필수 채택**|기존 Q-code 어디에도 해당 안 됨|
|Q19 immunogenicity adjudication missing|**채택**|Q01과 구조적으로 다른 DV adjudication 문제|
|Family F24-F29 추가|**채택**|보조 필드 패치 후 operational coverage 주장 가능|
|Family F30 rare disease sparse|**기각**|F11/F16/F20의 조합으로 충분. 별도 family 불필요|

---

### Part 1. v4.1 → v4.2 Changelog

|#|위치|변경 유형|내용|
|---|---|---|---|
|C16|A0|TEMPLATE ADD|`modality_class` 보조 필드 추가 (AIC annotation, 결정 노드 아님)|
|C17|A0|TEMPLATE MOD|`endpoint_data_type` 확장: CELLULAR_KINETICS / IMMUNOGENICITY / MILK_PK / MATERNAL_INFANT_PK 추가|
|C18|A8|DEF ADD|`analyte_role` 보조 필드 정의 추가; 미선언 시 Q16 트리거 조건 명시|
|C19|A7|STATE ADD|`PRODUCT-LEVEL-COVARIATE` 상태 추가 (lot→subject reverse-key join)|
|C20|A3|NOTE ADD|delivery/postpartum date as TIME anchor — ELAPSED 모호성과 동일 처리 주석|
|C21|N1|NOTE ADD|MATERNAL_INFANT dyad linkage — 모체·영아 별도 ID 구성 가능 시 INVALID 오판 방지 경로 명시|
|C22|Q-codes|CODE ADD|Q16 / Q18 / Q19 추가; Q17 기각 (Q13 흡수)|
|C23|Family|REGISTER ADD|F24–F29 추가 (신규 operational families); 구 F24–F27(UNSUPPORTED/INVALID) → F31–F34 재번호|
|C24|Scope|TEXT MOD|v4.2 기준 버전 갱신; constraints 8개로 확장|

---

### Part 2. 변경된 섹션 전문 (v4.2 delta)

변경이 없는 축(A1, A2, A5, A6, A9, A10, N0/N2–N7)과 Q01–Q15D는 v4.1과 동일하다. 아래는 변경 또는 추가된 섹션만 기술한다.

---

#### N1 (변경) — Subject ID Construction [v4.2 — C21 적용]

```
N1. Subject-level ID를 안정적으로 구성할 수 있는가?
    → No: INVALID
    → Yes: N2로

    [v4.2 note — C21] MATERNAL_INFANT dyad 구조:
    모체 ID와 영아 ID가 별도 레코드로 존재하더라도,
    dyad linkage key(예: MOTHER_ID, INFANT_ID pair)가 존재하고
    AIC의 endpoint_data_type=MATERNAL_INFANT_PK가 선언된 경우,
    N1 통과 가능. key 없이 둘 중 하나만 있으면 → INVALID.
    dyad linkage가 가능하나 key policy가 없으면 → Q18 QUARANTINE.
```

---

#### A0 (변경) — Analysis Intent Contract [v4.2 — C16, C17 적용]

**`modality_class` 보조 필드 (AIC template annotation, 결정 노드 아님):**

이 필드는 family register 라우팅 근거와 audit trail을 위한 것이다. 이 필드의 값 자체가 N0–N7 결정을 바꾸지 않는다. 단, 필드가 선언되면 해당 modality에 대응하는 family (F24–F29)의 전제 조건 충족 여부를 N0에서 함께 확인한다.

```
modality_class 허용값:
  SMALL_MOLECULE
  PEPTIDE
  MAB
  ADC
  BISPECIFIC
  CELL_THERAPY          CAR-T, TIL, NK cell therapy 등
  GENE_THERAPY          viral vector, gene editing
  MRNA                  LNP-mRNA, saRNA 등
  VACCINE
  OLIGO_ASO_SIRNA
  RADIOPHARMACEUTICAL
  OTHER_CUSTOM          충분한 설명 필수
```

**`endpoint_data_type` 확장 허용값 [v4.2 — C17]:**

기존 6종(PK_CONCENTRATION, EXPOSURE_METRIC, CONTINUOUS_PD, CATEGORICAL_PD, COUNT_PD, TTE_EVENT)에 아래를 추가한다.

```
CELLULAR_KINETICS     CAR+ 세포 수, 벡터 카피 수, transgene-positive cells,
                      expansion/persistence 지표.
                      NOTE: LLOQ는 Poisson 통계 기반으로 산출.
                      A5 BLQ 처리 알고리즘이 PK_CONCENTRATION과 다름.
                      반드시 cellular LLOQ derivation policy를 AIC에 명시.

IMMUNOGENICITY        ADA/NAb titer, seroconversion, positivity status.
                      DV 값 자체가 positivity adjudication rule에 의존함.
                      rule 없이 titer raw value만 있으면 → Q19 QUARANTINE.
                      rule 있으면 N4로 진입.

MILK_PK               모유 내 약물 농도.
                      matrix-specific LLOQ, CMT 분리 정책 필수.
                      plasma PK와 CMT/LLOQ가 구조적으로 달라 N4 code path 분리.

MATERNAL_INFANT_PK    모체 혈장 + 모유 ± 영아 혈장의 dyad/triad 연결 endpoint.
                      N1 dyad linkage key + N2 delivery date anchor 필수.
                      어느 하나라도 없으면 → Q18 QUARANTINE (key 없음)
                      또는 Q12 QUARANTINE (anchor 없음).

-- 기각된 type (참고) --
TARGET_ENGAGEMENT     → CONTINUOUS_PD로 처리. 별도 code path 없음.
BIODISTRIBUTION       → 대부분 UNSUPPORTED 영역. tabular 유도 결과는
                         CONTINUOUS_PD 또는 COUNT_PD로 처리.
```

**N0에서 endpoint_data_type 관련 추가 확인 사항 [v4.2]:**

```
IF endpoint_data_type=CELLULAR_KINETICS
   AND cellular LLOQ derivation policy absent
THEN → Q01 QUARANTINE (BLQ handling policy not specified — cellular subtype)

IF endpoint_data_type=IMMUNOGENICITY
   AND positivity adjudication rule absent
THEN → Q19 QUARANTINE

IF endpoint_data_type=MATERNAL_INFANT_PK
   AND dyad linkage key absent
THEN → Q18 QUARANTINE
```

---

#### A3 (변경) — Time Derivation Policy [v4.2 — C20 적용]

변경 없음 (상태 테이블 동일). 주석만 추가.

```
[v4.2 note — C20] Delivery/postpartum date as TIME anchor:
임산부·수유부 연구에서 분만일(delivery date) 또는 분만 후 경과일
(postpartum day)이 TIME의 생물학적 기준점으로 사용되는 경우,
이를 ELAPSED anchor에 준하여 처리한다.

분만일이 데이터에 명확히 기재되어 있으면 → ACTUAL 또는 ELAPSED 적용 가능.
분만일 기재 없이 "postpartum day X"만 있으면 → ELAPSED와 동일하게
anchor 기준점 모호성 확인 필요 → 모호하면 AMBIGUOUS → Q02.

AIC-SPECIAL (임산부/수유부)에서 delivery/postpartum anchor 정책을
반드시 명시하도록 요구한다.
```

---

#### A7 (변경) — Covariate Attachment [v4.2 — C19 적용]

|Code|조건|처리|
|---|---|---|
|NONE-REQUIRED|공변량 없음|AUTO|
|BASELINE-CLEAN|baseline covariate, key 있음, 결측 없음|AUTO|
|BASELINE-IMPUTABLE|baseline 결측, imputation policy 있음|REPAIR|
|TIME-VARYING|시간변동 공변량, timing 명확|REPAIR|
|EXTERNAL-JOIN|KNHANES 등 외부 join, key+policy 있음|REPAIR|
|PEDIATRIC-MATURATION|연령/체중 기반 maturation 파라미터|REPAIR|
|**PRODUCT-LEVEL-COVARIATE** [NEW]|CAR-T/세포치료제 lot·batch·제조 속성; lot→subject 역방향 join key|REPAIR (linkage policy 있음) / Q13 (key 없음)|
|KEY-MISSING|merge key 없음|Q13 QUARANTINE|
|POLICY-MISSING|결측 처리 정책 없음|Q07 QUARANTINE|

**[v4.2 note — C19] PRODUCT-LEVEL-COVARIATE vs. EXTERNAL-JOIN 구분 기준:**

EXTERNAL-JOIN은 subject → 외부 데이터베이스 방향의 join이다. PRODUCT-LEVEL-COVARIATE는 manufacturing lot/batch → subject 방향의 역방향 join으로, join key 구조와 결측 발생 원인이 다르다. 구체적으로:

- lot → subject linkage key가 임상 데이터에 존재: REPAIR
- lot ID는 있으나 임상 데이터와의 mapping table이 없음: Q13 QUARANTINE (로그에 "product-level covariate linkage, lot→subject mapping absent" 명시)
- product attribute 자체(transduction efficiency, viability, CAR+ fraction 등)가 제조 기록 외부에만 있고 데이터 패키지에 미포함: Q15A QUARANTINE (upstream data package incomplete)

**[v4.2 note] Life-stage covariate (임산부/수유부):**

gestational age, trimester, postpartum day 등 생애 단계 공변량은 별도 상태 추가 없이 TIME-VARYING 또는 BASELINE-CLEAN으로 처리한다. 단, delivery date는 covariate가 아니라 TIME anchor(A3)로 처리한다. time-varying covariate의 timing policy가 없으면 Q07로 귀속되며, AIC에서 해당 정책을 명시하도록 요구한다.

---

#### A8 (변경) — Multi-Drug / CMT Assignment [v4.2 — C18 적용]

상태 테이블은 v4.1과 동일. `analyte_role` 보조 필드 정의 추가.

**`analyte_role` 보조 필드 [NEW — C18]:**

이 필드는 A8의 MULTI-CMT-DEFINED 또는 METABOLITE-DEFINED 상태 진입 시 CMT 할당 정책의 세부 근거를 문서화한다. 단일 analyte (SINGLE-DRUG)에서는 불필요.

```
analyte_role 허용값:
  PARENT
  TOTAL_ANTIBODY            ADC·이중항체: 전체 항체
  CONJUGATED_ADC            ADC: conjugated form
  UNCONJUGATED_PAYLOAD      ADC: 유리된 payload
  ACTIVE_METABOLITE
  SOLUBLE_TARGET            이중항체/TMDD: 가용성 표적
  DRUG_TARGET_COMPLEX
  ADA                       항약물항체
  NAB                       중화항체
  VECTOR_COPY               유전자치료/CAR-T: 벡터 카피
  TRANSGENE_EXPRESSION      유전자치료: 단백질 발현량
  CAR_POSITIVE_CELL         CAR-T: CAR+ 세포 수/분율
  OTHER_CUSTOM              충분한 설명 필수
```

**analyte_role 미선언 트리거 조건 [Q16 연동]:**

```
IF A8 ∈ {MULTI-CMT-DEFINED, DDI-VICTIM-PERPETRATOR, METABOLITE-DEFINED}
   AND modality_class ∈ {ADC, BISPECIFIC, CELL_THERAPY, GENE_THERAPY}
   AND analyte_role NOT declared for each analyte
THEN → Q16 QUARANTINE
```

standard MAB, SMALL_MOLECULE, PRECLINICAL 등에서는 analyte_role 미선언이 Q16을 트리거하지 않는다. analyte_role은 CMT policy가 ambiguous한 경우의 진단 정밀도 도구이지, 독립 결정 노드가 아니다.

---

#### QUARANTINE Q-code Dictionary (v4.2 추가분)

Q01–Q15D는 v4.1과 동일. 아래 3개 추가.

```
Q16   Modality-specific analyte role policy missing
        ADC total antibody vs. conjugated ADC vs. unconjugated payload 구분 불명확;
        CAR-T vector copy vs. CAR+ cell count 구분 불명확 등.
        MULTI-CMT-DEFINED 진입 전 CMT 할당 근거 부재.
        (Q09와의 차이: Q09는 CMT 번호 자체가 없음.
         Q16은 CMT는 있으나 analyte role 분류 정책이 없어 CMT 할당 타당성 불명확.)

Q17   [기각] → Q13으로 흡수. product-level covariate linkage key 부재는
        Q13에서 로그 메시지로 세분화.

Q18   Maternal–infant or pregnancy/lactation structural linkage ambiguous
        모체 ID, 영아 ID, dyad key, delivery date anchor 중 하나 이상 불명확.
        (Q12와의 차이: Q12는 TIME anchor 자체가 없음.
         Q18은 anchor 또는 ID key가 존재하나 연결 구조 정의 부재.)

Q19   Immunogenicity or DV adjudication rule missing
        ADA/NAb positivity rule, titer cut-point, receptor occupancy derivation rule,
        또는 기타 raw assay value → DV 변환 규칙 부재.
        (Q01과의 차이: Q01은 BLQ/LLOQ 기반 농도 처리 정책 부재.
         Q19는 DV 값 자체를 확정하는 상위 adjudication rule 부재.)
```

**운영 원칙 추가:** Q16/Q18/Q19 발행 시 반드시 해당 modality_class 또는 endpoint_data_type을 Q-code 로그에 함께 기재한다.

---

#### Family Register v4.2 (신규 추가분)

**신규 operational families (F24–F29):**

|ID|Family|핵심 조건|예상 terminal|실무 빈도|
|---|---|---|---|---|
|F24|ADC PK/PKPD|total Ab + conjugated ADC + payload/metabolite ± ADA; A8 analyte_role 선언|REPAIR|중간|
|F25|Bispecific / T-cell engager PKPD|parent PK + soluble target ± cytokine; MULTI-CMT + CONTINUOUS_PD|REPAIR|중간|
|F26|CAR-T / 세포치료제 cellular kinetics|CELLULAR_KINETICS endpoint + qPCR/FACS + product-level covariate; A7 PRODUCT-LEVEL-COVARIATE|REPAIR|낮음~중간|
|F27|mRNA / vaccine-like|prime/boost (LOADING-MAINTENANCE) + IMMUNOGENICITY endpoint; Q19 없으면 REPAIR|REPAIR|낮음|
|F28|Pregnancy PK|maternal PK + gestational/postpartum time anchor + TIME-VARYING covariate; A3 delivery anchor 명시|REPAIR|낮음|
|F29|Lactation / mother–infant PK|MATERNAL_INFANT_PK endpoint + dyad linkage key; N1 dyad 처리 경로|REPAIR|낮음|

[v4.2 note] **F24**: analyte_role 미선언이면 Q16 QUARANTINE으로 먼저 차단. CMT 할당 정책이 있으면 MULTI-CMT-DEFINED → REPAIR.

[v4.2 note] **F26**: endpoint_data_type=CELLULAR_KINETICS 선언 필수. cellular LLOQ derivation policy 없으면 Q01 QUARANTINE (cellular subtype).

[v4.2 note] **F27**: prime/boost 구조는 A4 LOADING-MAINTENANCE로 처리. IMMUNOGENICITY endpoint 선언 + positivity adjudication rule 있으면 REPAIR. 없으면 Q19 QUARANTINE.

[v4.2 note] **F28/F29**: delivery date anchor를 A3에서 명시 필요. dyad linkage key 없으면 Q18 QUARANTINE.

**기존 UNSUPPORTED/INVALID family 재번호:**

|구 ID|신 ID|Family|처리|
|---|---|---|---|
|F24 (구)|F31|raw FCS/qPCR without derivation|UNSUPPORTED|
|F25 (구)|F32|omics/imaging/waveform raw|UNSUPPORTED|
|F26 (구)|F33|unstructured notes only|UNSUPPORTED|
|F27 (구)|F34|unrecoverable core missing|INVALID|

---

### V4.2 Scope Statement (공식 문서용)

```
Frozen Universe v4.2
Routine Clinical/Preclinical PMX-to-NONMEM Dataset Universe
(New Modality & Special Population Extended)

Definition:
A scenario is defined by the combination of
  (analysis intent state) × (data availability state) × (policy availability state).
Two inputs belong to the same scenario if and only if
they require identical wrangling action sequences.

Coverage claims:
  Capture coverage:         ≥99%
  Review-inclusive (95%):   AUTO + REPAIR + QUARANTINE
  Operational (no-manual):  AUTO + REPAIR  ≥75%
  Auto-only:                AUTO           ≥35%
  Unsupported + Invalid:                   ≤5%

Key constraints:
  1. QUARANTINE always carries a specific Q-code (Q01–Q19).
     QUARANTINE without a Q-code is a system failure.
  2. REPAIR requires a deterministic algorithm producing
     a unique output. Policy absent → QUARANTINE, not REPAIR.
  3. Analysis Intent Contract (A0) is evaluated first.
     Missing or insufficient intent → Q11 QUARANTINE,
     regardless of data quality.
  4. AIC-PKPD / AIC-ER / AIC-TTE / AIC-BIOMARKER require
     endpoint_data_type to be declared. Missing → Q11.
  5. ADDL/II applies to fixed-dose repeated regimens only.
     Variable-dose (titration/adaptive) → A4=TITRATION-ADAPTIVE.
     Mixed ADDL and actual records without policy → A4=ADDL-ACTUAL-CONFLICT → Q14.
  6. Coverage percentages are empirical targets to be
     validated against ≥100 historical PMX projects
     (minimum: 10–20 pilot fingerprints before final freeze).
  7. CELLULAR_KINETICS endpoint uses Poisson-derived LLOQ.
     Applying concentration-based LLOQ to cellular data is a
     system error. Policy mismatch → Q01 (cellular subtype).
  8. MATERNAL_INFANT dyad requires explicit dyad linkage key
     AND delivery/postpartum time anchor declaration.
     Either absent → Q18 QUARANTINE, not INVALID.

Operational scope: F01–F29
Out-of-scope but captured: F31–F34

Version history:
  v4.0  Initial freeze candidate
  v4.1  Targeted patches: A4 regimen states (C01–C04),
        A5 bioanalytical final flag (C05),
        A8 DDI split (C06),
        A9 reanalysis states (C07–C08),
        A10 SEMI-STRUCTURED subtype (C09),
        Q15 decomposition (C10),
        AIC endpoint_data_type (C11),
        N3/A3/F02/F09 clarifications (C12–C15)
  v4.2  New modality & special population extension:
        A0 modality_class + endpoint_data_type expansion (C16–C17),
        A8 analyte_role auxiliary field (C18),
        A7 PRODUCT-LEVEL-COVARIATE state (C19),
        A3 delivery/postpartum anchor note (C20),
        N1 maternal-infant dyad path (C21),
        Q16/Q18/Q19 (C22),
        F24–F29 new operational families (C23),
        scope constraints extended to 8 (C24)
```

---

### v4.1 vs v4.2 핵심 차이 요약

|항목|v4.1|v4.2|
|---|---|---|
|A0 보조 필드|endpoint_data_type (6종)|+ modality_class + endpoint_data_type (10종)|
|A7 상태 수|8개|9개 (+PRODUCT-LEVEL-COVARIATE)|
|A8 보조 필드|없음|analyte_role (12종)|
|Q-code 수|Q01–Q15D (18개)|Q01–Q19 (21개, Q17 기각으로 실질 +3)|
|Operational family 수|F01–F23|F01–F29 (+6)|
|Scope constraints|6개|8개|
|CELLULAR_KINETICS silent REPAIR 위험|존재|차단 (constraint 7)|
|MATERNAL_INFANT INVALID 오판 위험|존재|차단 (N1 note + constraint 8 + Q18)|
|New modality coverage (operational)|80–85% 추정|≥90% 추정|
|축 수|11개|**11개 (불변)**|

---

### 보강하지 않은 항목과 이유

|제안|기각 이유|
|---|---|
|TARGET_ENGAGEMENT endpoint_data_type|receptor occupancy는 CONTINUOUS_PD (0–1 또는 %) 범위 내 연속형 변수. 별도 N4 code path 없음|
|BIODISTRIBUTION endpoint_data_type|조직 농도 tabular output은 PK_CONCENTRATION으로 처리 가능. raw imaging/tissue raw는 F32(UNSUPPORTED). 중간 지점이 없음|
|LIFE-STAGE-COVARIATE A7 상태|gestational age/trimester는 TIME-VARYING로 처리. delivery date는 A3 문제. 별도 code path 없음|
|Q17|product-level covariate linkage key 부재는 Q13(external covariate linkage key ambiguous)의 하위 사례. Q13 발행 시 로그에 "product-level, lot→subject" 명시로 충분|
|F30 rare disease sparse|F11(special population) + F16(external covariate) + F20(TDM/RWD)의 조합으로 처리 가능. 별도 family로 묶을 의의 없음|
|새 축 추가 (modality axis 등)|핵심 설계 원칙 위반. 약물 종류 자체는 wrangling code path를 직접 바꾸지 않음. 보조 필드(modality_class)로 충분|