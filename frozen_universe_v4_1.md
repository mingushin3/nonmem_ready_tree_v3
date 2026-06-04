# Frozen Universe v4.1

## Routine Clinical/Preclinical PMX-to-NONMEM Dataset Universe

---

## Part 0. v4 독립 검토 및 v4.1 보강 근거

### 0.1 독립 검토 판정

v4는 **설계 원칙 수준에서 옳다.** 핵심 기준 — "축의 상태가 달라질 때 wrangling code path가 달라지는가" — 은 실무적으로 방어 가능한 유일한 기준이며, 이를 일관되게 적용한 결과가 A0–A10의 11개 축이다.

특히 세 가지 구조적 결정이 v3 대비 크게 개선되었다.

첫째, A0(AIC)를 최상위 gate로 배치한 것. 분석 의도가 없으면 이후 모든 노드가 정의되지 않는다. Q11이 즉시 차단하도록 한 구조는 false AUTO와 false REPAIR의 가장 큰 원천을 막는다.

둘째, REPAIR를 "정책 + 유일한 알고리즘 출력"으로 엄격히 정의한 것. 정책 없는 변환은 QUARANTINE이라는 기준은 실무 시스템이 silent error를 내지 않도록 한다.

셋째, QUARANTINE을 실패가 아니라 review queue로 처리한 것. coverage 주장을 AUTO+REPAIR로 하지 않고 AUTO+REPAIR+QUARANTINE(review-inclusive)으로 제한한 점이 현실적이다.

**결론: v4는 routine clinical/preclinical PMX wrangling universe의 core pattern을 충분히 포착한다.** 다만 아래 4개 영역에서 코드 패스가 실제로 달라지는 시나리오가 아직 명시되지 않았다.

### 0.2 보강이 필요한 4개 영역과 독립 판단

#### 영역 1. A4 (Dose Completeness) — 3개 코드 패스 미분리

현재 A4가 ADDL-II 상태 하나로 묶고 있는 것 중 실제로 code path가 달라지는 경우가 세 가지 있다.

**TITRATION-ADAPTIVE**: 용량이 반응(또는 프로토콜 스케줄)에 따라 반복적으로 변경된다. ADDL-II는 동일 용량의 압축 반복을 전제하므로, 가변 용량 기록에 ADDL-II를 적용하면 AMT 시퀀스가 잘못 재구성된다. 재구성 알고리즘 자체가 달라지므로 별도 상태가 필요하다.

**LOADING-MAINTENANCE**: loading과 maintenance의 AMT, RATE, DUR가 모두 다를 수 있다. ADDL-II로 처리하면 transition point 이후 AMT 변화를 놓친다. NONMEM dose record 재구성 로직이 달라지므로 분리한다.

**INFUSION-STOP-RESTART**: RATE=0 이벤트 또는 DUR이 여러 행에 걸쳐 분할되는 패턴. RATE 컬럼 재구성 방식이 표준 infusion과 다르다. A6의 EVENT-SEPARABILITY와 중복되지 않는다 — A4는 용량 기록 완성을 다루고, A6는 행 분류를 다룬다.

또한 현재 Q14가 존재하지만 A4에 Q14를 트리거하는 명시적 상태가 없다. ADDL-II와 actual dose records가 혼재할 때의 충돌 해소 정책 부재는 Q14로 직접 연결되어야 한다.

#### 영역 2. A5/A9 — Bioanalytical reanalysis 최종 플래그 미처리

현재 A5는 BLQ 처리와 LLOQ 관련 상태를 잘 포착하지만, reanalysis로 인한 중복 결과값(최종 플래그 없음)에 대한 상태가 없다. 이것은 Q01/LLOQ 문제가 아니라 데이터 패키지 완결성의 문제다. DV값 자체가 여러 개 존재하므로 wrangler가 독립적으로 선택할 수 없고, 반드시 QUARANTINE으로 차단해야 한다. A9에 REPAIR 가능한 경우(final flag 있음)도 추가한다.

#### 영역 3. Q15 — 너무 넓어서 사유 추적 불가

Q15가 "Other — specify"로 열려 있으면 시스템이 운영 단계에서 Q15를 남발할 위험이 있다. QUARANTINE의 핵심 가치는 "구체적 사유 코드 필수"인데, Q15가 블랙홀이 되면 이 원칙이 무너진다. Q15A–Q15D로 세분화한다. 세분화 기준은 담당 도메인(데이터 패키지, 레거시 플래그, 실사용 투약 이력, 분석 결과 최종화)으로 잡는다.

#### 영역 4. AIC template — endpoint_data_type 누락

A0에 AIC-PKPD, AIC-ER, AIC-TTE가 있지만, 실제 DV 데이터의 타입을 구분하지 않는다. Exposure metric(AUC/Cmax)이 input인지 raw concentration-time이 input인지에 따라 NONMEM dataset의 구조 자체가 달라진다(DV 해석, EVID, CMT 할당 모두 다름). 이것은 새로운 축을 추가하는 것이 아니라 AIC template의 required field로 해결한다. A0 AIC-ER, AIC-TTE, AIC-PKPD 사용 시 필수 기재 항목으로 명시한다.

### 0.3 보강하지 않는 항목과 이유

피드백에서 제안한 10개 패치 외에 검토한 추가 후보들과 판단:

|후보|판단|이유|
|---|---|---|
|A3 ELAPSED anchor 모호성|주석 추가로 처리|별도 상태 추가보다 A3 정의 강화로 충분|
|A7 time-varying covariate timing|AIC template 주석|LOCF/NOCB 정책은 AIC에서 명시 가능|
|F02 Q05 명시|Family register 주석 추가|축 변경 없이 family 설명에 명시|
|N3 obs-only 명확화|노드 설명 보강|N0–N7 구조는 유지|

A10 SEMI-STRUCTURED의 subtype 분리는 피드백과 동일하게 **auxiliary field 방식**을 채택한다. 축을 늘리면 조합 폭발 위험이 있고, subtype은 parser 선택에만 영향을 미치므로 A10 state와는 독립적으로 처리할 수 있다.

DDI A8 split(victim-only vs. victim+perpetrator measured)은 **채택**한다. CMT 할당 구조가 실제로 달라지기 때문이다.

---

## Part 1. v4 → v4.1 Changelog

|#|위치|변경 유형|내용|
|---|---|---|---|
|C01|A4|STATE ADD|`TITRATION-ADAPTIVE` 추가|
|C02|A4|STATE ADD|`LOADING-MAINTENANCE` 추가|
|C03|A4|STATE ADD|`INFUSION-STOP-RESTART` 추가|
|C04|A4|STATE ADD|`ADDL-ACTUAL-CONFLICT` 추가 (→ Q14 명시 트리거)|
|C05|A5|STATE ADD|`BIOANALYTICAL-FINAL-FLAG-MISSING` 추가 (→ Q15D)|
|C06|A8|STATE MOD|`DDI-ROLES-DEFINED` → `DDI-VICTIM-ONLY`, `DDI-VICTIM-PERPETRATOR` 분리|
|C07|A9|STATE ADD|`REANALYSIS-FINAL-DEFINED` 추가 (→ REPAIR)|
|C08|A9|STATE ADD|`REANALYSIS-FINAL-MISSING` 추가 (→ Q15D)|
|C09|A10|DEF MOD|`SEMI-STRUCTURED`에 `source_parser_subtype` 보조 필드 정의 추가|
|C10|Q-codes|CODE MOD|Q15 → Q15A / Q15B / Q15C / Q15D 세분화|
|C11|A0|TEMPLATE MOD|`AIC-PKPD`, `AIC-ER`, `AIC-TTE` 사용 시 `endpoint_data_type` 필수 기재 명시|
|C12|N3|NOTE ADD|obs-only intent 경로 명확화 주석|
|C13|A3|NOTE ADD|ELAPSED anchor(first vs. last dose) 모호성 처리 주석|
|C14|F02|NOTE ADD|harmonization policy 없을 시 Q05 QUARANTINE 명시|
|C15|Scope|TEXT MOD|v4.1 기준으로 버전 갱신|

---

## Part 2. Frozen Universe v4.1 (Full Specification)

---

### 설계 철학

> 축의 기준: 이 축의 상태가 달라지면 wrangling code path가 달라지는가?

달라지지 않으면 축이 아니다.

---

### Coverage Targets

|지표|정의|v4.1 목표|비고|
|---|---|---|---|
|Capture coverage|어떤 terminal state로든 귀속|≥99%|시스템이 조용히 죽으면 안 됨|
|Review-inclusive coverage|AUTO+REPAIR+QUARANTINE|≥95%|이것이 "95% 커버"|
|Operational coverage|AUTO+REPAIR|≥75%|현실적 자동화 효율|
|Auto coverage|AUTO만|≥35%|낙관적 예상|
|Unsupported+Invalid|—|≤5%|초과 시 universe 재정의|

---

### Terminal State (확정 정의)

|State|한 줄 정의|다음 행동|
|---|---|---|
|`AUTO`|정책+데이터 모두 있고, 변환 알고리즘이 유일한 출력 생성|export + audit log|
|`REPAIR`|정책 있고, deterministic 변환 후 출력 생성 가능|repair log + export|
|`QUARANTINE`|데이터는 있으나 결정 불가 — 구체적 Q-code 필수|사유별 review queue|
|`UNSUPPORTED`|현재 엔진 기능 밖 — 미래 버전 후보|scope expansion 등록|
|`INVALID`|핵심 구성요소 부재 — 추가 정보 없이 처리 불가|reject + 부재 항목 명시|

---

### QUARANTINE Q-code Dictionary (v4.1)

```
Q01   BLQ handling policy not specified
Q02   Time policy (actual vs nominal) not specified
Q03   Occasion definition not specified
Q04   Dose–sample linkage ambiguous, cannot resolve without policy
Q05   Multi-study ID conflict, harmonization rule not specified
Q06   Protocol deviation handling policy absent
Q07   Missing covariate imputation policy not specified
Q08   Multiple valid dose sources conflict, selection rule absent
Q09   Analyte/CMT assignment policy not specified
Q10   Unit dictionary incomplete
Q11   Analysis intent insufficient to determine action labels
Q12   Time anchor irrecoverable without additional data
Q13   External covariate linkage key ambiguous
Q14   ADDL/II vs actual dose history conflict, resolution policy absent
Q15A  Data package incomplete — unresolved upstream adjudication
        (예: final reanalysis package 미수령, 검체 결과 adjudication 미완)
Q15B  Legacy flag undocumented — flag 의미 확인 불가
        (예: QC flag, include/exclude flag 정의 문서 없음)
Q15C  Real-world adherence or administration history unresolved
        (예: TDM/RWD에서 actual dose time 환자 진술만 있고 EMR 확인 불가)
Q15D  Assay reanalysis / final-result adjudication missing
        (예: ISR repeat 또는 dilution repeat 결과 여러 개, final flag 없음)
```

**운영 원칙**: QUARANTINE은 반드시 Q-code를 포함해야 한다. Q-code 없는 QUARANTINE은 시스템 장애로 간주한다. Q15A–Q15D 중 어느 하나에도 명확히 해당하지 않을 경우에만 Q15B 또는 Q15A를 쓰고 세부 사유를 텍스트로 기재한다.

---

### Master Decision Nodes (N0–N7) [v4.1]

```
N0. Analysis intent가 action-resolving 수준으로 명시되어 있는가?
    → No: Q11 QUARANTINE
    → Yes: N1으로
    [v4.1 note] AIC-PKPD / AIC-ER / AIC-TTE 사용 시
                endpoint_data_type 필드 기재 여부를 N0에서 함께 확인.
                미기재이면 Q11.

N1. Subject-level ID를 안정적으로 구성할 수 있는가?
    → No: INVALID
    → Yes: N2로

N2. 시간 순서가 있는 event sequence를 구성할 수 있는가?
    (TIME anchor for both dose and observation)
    → 완전 불가: INVALID
    → 정책 필요: Q04/Q12 QUARANTINE
    → 가능: N3으로

N3. Dose records를 완성할 수 있는가?
    (AMT, RATE or DUR, CMT for every EVID=1 row)
    → 불필요 (obs-only intent: e.g. AIC-ER with summarized exposure metric,
               또는 AIC에서 dose records 불요로 명시): N4로
    [v4.1 note] obs-only로 N4를 직접 통과할 때, N4의 DV가
                AIC endpoint_data_type과 일치하는지 확인.
    → 정책 있으면 deterministic: REPAIR → N4로
    → 정책 없음: Q06/Q08 QUARANTINE
    → 복원 불가: INVALID

N4. Observation records를 완성할 수 있는가?
    (DV, CMT, LLOQ for every EVID=0 row)
    → 정책 있으면 deterministic: REPAIR → N5로
    → 정책 없음: Q01/Q09 QUARANTINE
    → 부재: INVALID

N5. BLQ/missing/MDV 처리를 적용할 수 있는가?
    → 정책 명시, BLQ canonicalization 가능: REPAIR → N6으로
    → BLQ policy 없음: Q01 QUARANTINE
    → BLQ 없음: 그대로 N6으로

N6. 명시된 공변량을 붙일 수 있는가?
    → 공변량 없음: N7으로
    → merge 가능 (key 있고, imputation policy 있음): REPAIR → N7로
    → key 없거나 policy 없음: Q07/Q13 QUARANTINE

N7. 남은 모든 모호성이 threshold 이하인가?
    → Yes: AUTO (N0–N6 모두 REPAIR 없으면) 또는 REPAIR (하나라도 있으면)
    → No: 해당 Q-code 발행
```

---

### Axes (v4.1 확정 — 11개)

---

#### A0. Analysis Intent Contract [v4.1 — C11 적용]

|Code|내용|endpoint_data_type 요구|
|---|---|---|
|AIC-MISSING|SAP/분석 목적 없음 → N0에서 Q11|—|
|AIC-PK|PK, BLQ policy, time policy 명시|불필요|
|AIC-POPPK|popPK, occasion policy 명시|불필요|
|AIC-PKPD|PK/PD, endpoint role, CMT policy 명시|**필수**|
|AIC-ER|exposure-response, exposure metric 정의 명시|**필수**|
|AIC-TTE|TTE, event definition 명시|**필수**|
|AIC-DDI|DDI, victim/perpetrator role, CMT 분리 정책 명시|불필요|
|AIC-PEDS|소아 PK, dose reconstruction policy(mg/kg/BSA) 명시|불필요|
|AIC-SPECIAL|특수집단(신/간장애), dose adjustment policy 명시|불필요|
|AIC-BIOMARKER|biomarker kinetics, endpoint derivation policy 명시|**필수**|
|AIC-CUSTOM|위 분류 외, 충분한 policy 문서 첨부|문서에서 명시|

**endpoint_data_type 허용값 (AIC template 필수 필드):**

```
PK_CONCENTRATION      원시 농도-시간 데이터 (표준 NONMEM DV)
EXPOSURE_METRIC       AUC/Cmax/Ctrough 등 요약 지표
CONTINUOUS_PD         연속형 PD endpoint (DVID 별도 정의)
CATEGORICAL_PD        순서형/명목형 PD endpoint
COUNT_PD              카운트 endpoint
TTE_EVENT             생존/이벤트 데이터 (DV = event indicator)
```

AIC-ER이면서 endpoint_data_type=EXPOSURE_METRIC인 경우, N3의 "obs-only intent"에 해당할 수 있다. AIC에서 명시 필요.

**AIC-MISSING이면 이후 모든 노드가 의미 없다. N0에서 즉시 Q11 QUARANTINE.**

---

#### A1. Study Integration Level

|Code|내용|실무 영향|
|---|---|---|
|SINGLE|단일 연구|ID 구성 단순|
|MULTI-HOMO|다중 연구, 동일 프로토콜 계열|STUDYID prefix 추가|
|MULTI-HETERO|다중 연구, 이종 프로토콜|연구별 시간 기준 통일 필요|
|MULTI-SITE|단일 연구, 기관별 컨벤션 다름|site-level harmonization|
|INTERIM|미잠금 DB|날짜 기준 subset 처리|

MULTI 계열은 study-level harmonization이 A0에서 정책으로 명시되어야 AUTO/REPAIR 가능. 없으면 Q05 QUARANTINE.

---

#### A2. Study Design

|Code|내용|NONMEM 영향|
|---|---|---|
|PARALLEL|평행군|표준 구조|
|SAD-MAD|단회/반복 용량 증량|ADDL/II 또는 full dosing history|
|CROSSOVER|교차설계 (2-period 이상)|period/sequence/carryover 변수 필요|
|BE|생물학적 동등성|crossover와 동일 + reference/test 구분|
|DDI|약물 상호작용|복수 CMT, victim/perpetrator role|
|FOOD-EFFECT|식이 영향|fed/fasted flag, period 구분|
|SPECIAL-POP|신/간장애, 특수집단|renal/hepatic category covariate|
|PEDIATRIC|소아|연령/체중/성숙도 covariate, mg/kg 재구성|
|TDM-RWD|TDM/실사용 데이터|불규칙 투약 기록, actual dose history|
|PRECLINICAL|전임상|animal ID, species/sex/strain covariate|

---

#### A3. Time Derivation Policy

NONMEM에서 TIME은 모든 것의 기반이다. 이 결정이 가장 중요하다.

|Code|조건|TIME 계산 방법|
|---|---|---|
|ACTUAL|투약+채혈 모두 실제 datetime 있음|(PCDTC − EXSTDTC) in hours|
|NOMINAL-ONLY|실제 datetime 없음, nominal time만 있음|프로토콜 스케줄 사용|
|ACTUAL-PREFERRED|실제 datetime 있으나 일부 nominal fallback|실제 우선, 누락 시 nominal|
|NOMINAL-PREFERRED|AIC에서 nominal 우선 명시|nominal 우선, 실제는 참고만|
|ELAPSED|첫 투약 또는 직전 투약으로부터 경과 시간|elapsed 직접 사용|
|INTERVAL|urine 등 interval collection|START_TIME + INTERVAL 계산|
|AMBIGUOUS|정책 없고 actual/nominal 혼재|Q02 QUARANTINE|
|UNRECOVERABLE|time 정보 없음|INVALID|

[v4.1 note — C13] ELAPSED를 사용할 때, elapsed의 기준점(최초 투약 vs. 직전 투약)이 데이터에서 명확하지 않으면 AMBIGUOUS → Q02로 처리한다. AIC에서 ELAPSED anchor 기준을 명시하도록 요구한다.

---

#### A4. Dose Completeness [v4.1 — C01, C02, C03, C04 적용]

|Code|조건|처리|
|---|---|---|
|COMPLETE|AMT, ROUTE, TIMING 모두 있음|AUTO|
|WEIGHT-BASED|mg/kg, 체중 있음|REPAIR (계산)|
|BSA-BASED|mg/m², BSA/체중 있음|REPAIR (계산)|
|PLANNED-FALLBACK|actual 없음, 프로토콜 용량 사용 허가|REPAIR (AIC 필요)|
|ADDL-II|동일 용량 반복 투약 요약 기록 (fixed dose 전제)|REPAIR|
|**ADDL-ACTUAL-CONFLICT** [NEW]|ADDL/II 기록과 actual dose records 혼재, 해소 정책 없음|Q14 QUARANTINE|
|**TITRATION-ADAPTIVE** [NEW]|반응/스케줄에 따라 용량이 변경되는 regimen; ADDL-II로 재구성 불가|REPAIR (적응 정책 있음) / Q08 (없음)|
|**LOADING-MAINTENANCE** [NEW]|부하 용량과 유지 용량의 AMT/RATE/DUR이 다른 2-phase regimen|REPAIR (전환점 기록 있음) / Q08 (없음)|
|**INFUSION-STOP-RESTART** [NEW]|주입 중단 후 재개 — RATE=0 이벤트 또는 DUR 분할 행 존재|REPAIR (재구성 정책 있음) / Q04 (없음)|
|PARTIAL-RECOVERY|일부 투약 기록 누락, 추론 가능|REPAIR + flag|
|COMBINATION|복수 약물, CMT 분리 정책 있음|REPAIR|
|MISSING-NO-POLICY|용량 없고 복원 정책 없음|Q08 QUARANTINE|
|UNRECOVERABLE|복원 불가|INVALID|

**ADDL-ACTUAL-CONFLICT 트리거 조건:**

```
IF A4=ADDL-II AND actual individual dose records partially coexist
   AND resolution policy (우선순위 또는 통합 규칙) absent
THEN → Q14 QUARANTINE
```

**TITRATION-ADAPTIVE vs. ADDL-II 구분 기준:**

- ADDL-II: 동일 AMT가 II 간격으로 반복됨 (고정 용량 가정)
- TITRATION-ADAPTIVE: AMT가 방문/결과에 따라 변경됨 (적응 용량 가정) 두 기록이 혼재하면 ADDL-ACTUAL-CONFLICT 처리 우선.

---

#### A5. Observation Completeness & BLQ [v4.1 — C05 적용]

|Code|조건|처리|
|---|---|---|
|CLEAN|DV numeric, no BLQ, LLOQ 있음|AUTO|
|BLQ-FLAGGED|BLQ flag 있음, LLOQ 있음, policy 있음|REPAIR|
|BLQ-TEXT|`<0.1`, `BLQ` 등 text, LLOQ 있음, policy 있음|REPAIR|
|BLQ-ZERO|DV=0 + BLQ flag, policy 있음|REPAIR|
|MULTI-ANALYTE|복수 analyte, CMT policy 있음|REPAIR|
|LLOQ-CHANGED|연구 중 LLOQ 변경, 날짜 기록 있음|REPAIR + flag|
|MISSING-MDV1|DV 없음, MDV=1 명시|AUTO|
|**BIOANALYTICAL-FINAL-FLAG-MISSING** [NEW]|reanalysis/ISR/dilution repeat 등으로 DV 후보가 복수이고 final flag 없음|Q15D QUARANTINE|
|BLQ-NO-POLICY|BLQ 있음, 정책 없음|Q01 QUARANTINE|
|LLOQ-MISSING|LLOQ 없고 추론 불가|Q01 QUARANTINE|
|ABSENT|관측값 없음|INVALID|

---

#### A6. Event Row Classification

|Code|조건|처리|
|---|---|---|
|SEPARABLE|투약/관측 행 구분 가능|AUTO|
|SAME-TIME-RESOLVABLE|동시각 투약+관측, 순서 정책 있음|REPAIR|
|COVARIATE-CHANGE|공변량 변화 row 필요, 정책 있음|REPAIR|
|RESET-NEEDED|washout/reset 필요, 정책 있음|REPAIR|
|URINE-INTERVAL|interval collection event, 정책 있음|REPAIR|
|AMBIGUOUS|행 유형 불명확, 정책 없음|Q04 QUARANTINE|

---

#### A7. Covariate Attachment

|Code|조건|처리|
|---|---|---|
|NONE-REQUIRED|공변량 없음|AUTO|
|BASELINE-CLEAN|baseline covariate, key 있음, 결측 없음|AUTO|
|BASELINE-IMPUTABLE|baseline 결측, imputation policy 있음|REPAIR|
|TIME-VARYING|시간변동 공변량, timing 명확|REPAIR|
|EXTERNAL-JOIN|KNHANES 등 외부 join, key+policy 있음|REPAIR|
|PEDIATRIC-MATURATION|연령/체중 기반 maturation 파라미터|REPAIR|
|KEY-MISSING|merge key 없음|Q13 QUARANTINE|
|POLICY-MISSING|결측 처리 정책 없음|Q07 QUARANTINE|

---

#### A8. Multi-Drug / CMT Assignment [v4.1 — C06 적용]

|Code|조건|처리|
|---|---|---|
|SINGLE-DRUG|단일 약물, CMT=1 또는 미지정|AUTO|
|MULTI-CMT-DEFINED|복수 analyte/약물, CMT 할당 정책 있음|REPAIR|
|**DDI-VICTIM-ONLY** [NEW]|DDI 설계, victim만 샘플링됨 (perpetrator 투여되나 농도 측정 없음)|REPAIR (victim CMT만 필요)|
|**DDI-VICTIM-PERPETRATOR** [NEW]|DDI 설계, victim + perpetrator 모두 샘플링됨|REPAIR (dual CMT, 각 analyte CMT 정책 필수)|
|METABOLITE-DEFINED|parent+metabolite, CMT 정책 있음|REPAIR|
|CMT-POLICY-MISSING|복수 analyte/약물, CMT 정책 없음|Q09 QUARANTINE|

**[이전 v4] DDI-ROLES-DEFINED** 삭제 — DDI-VICTIM-ONLY와 DDI-VICTIM-PERPETRATOR로 대체. 두 경우는 NONMEM CMT structure가 다르므로 분리한다.

---

#### A9. Data Defect Repairability [v4.1 — C07, C08 적용]

|Code|조건|처리|
|---|---|---|
|CLEAN|결함 없음|AUTO|
|DUPLICATE-EXACT|완전 중복 행|REPAIR (제거)|
|UNSORTED|정렬 오류|REPAIR (재정렬)|
|COLUMN-SYNONYM|컬럼명 동의어|REPAIR (rename)|
|UNIT-CONVERSION|단위 변환, dictionary 있음|REPAIR|
|ENCODING-FIX|인코딩/타입 변환|REPAIR|
|PRE-DOSE-SAMPLE|첫 투약 전 채혈, policy 있음|REPAIR + flag|
|PLANNED-VS-ACTUAL|계획/실제 용량 충돌, policy 있음|REPAIR|
|PROTOCOL-DEVIATION|PD 발생, SAP policy 있음|REPAIR|
|**REANALYSIS-FINAL-DEFINED** [NEW]|reanalysis duplicate 있음, final flag 명시됨|REPAIR (final 선택)|
|**REANALYSIS-FINAL-MISSING** [NEW]|reanalysis duplicate 있음, final flag 없음|Q15D QUARANTINE|
|PROTOCOL-DEVIATION-NO-POLICY|PD 발생, policy 없음|Q06 QUARANTINE|
|IRRECONCILABLE|해소 불가 모순|INVALID|

---

#### A10. Source Format Parseability [v4.1 — C09 적용]

|Code|조건|처리|
|---|---|---|
|SDTM-ADaM|표준 CDISC 구조|AUTO|
|EDC-STRUCTURED|EDC multi-table, 구조 문서화됨|AUTO or REPAIR|
|CRO-VENDOR|CRO PK concentration + dosing|REPAIR|
|FLAT-TABULAR|Excel/CSV, 컬럼 식별 가능|REPAIR|
|LEGACY-NM|기존 NONMEM-like dataset|REPAIR|
|SEMI-STRUCTURED|구조 추론 필요; `source_parser_subtype` 보조 필드로 세분화|REPAIR|
|NON-TABULAR|raw FCS, omics, 비정형|UNSUPPORTED|
|CORRUPTED|파일 손상|INVALID|

**SEMI-STRUCTURED `source_parser_subtype` 보조 필드 정의 [NEW]:**

```
MULTISHEET          multi-sheet Excel — sheet detection + schema inference 필요
PDF-TABLE           PDF embedded table — table extraction + validation 필요
CRF-EXPORT          CRF 방문/시점 매핑 — visit-timepoint mapping 필요
VENDOR-CUSTOM       vendor 고유 레이아웃 — mapping dictionary 필요
```

이 필드는 A10 상태(SEMI-STRUCTURED)와 독립적으로 parser 선택에만 영향을 미친다. A10 axis의 code path는 동일하게 REPAIR이지만, 세부 parser 구현 분기가 달라진다. `source_parser_subtype`을 반드시 기재해야 audit log에 근거가 남는다.

---

### Family Register v4.1 (F01–F26)

operational coverage(≥95%) 분모에 포함되는 family: F01–F22.

|ID|Family|핵심 조건|예상 terminal|실무 빈도|
|---|---|---|---|---|
|F01|Standard SDTM/ADaM popPK|DM+EX+PC±LB, single study|AUTO|높음|
|F02|Multi-study pooled popPK|≥2 study, harmonization policy 있음|REPAIR|매우 높음|
|F03|EDC multi-table clinical PK|subject+dose+sample, key 명확|REPAIR|높음|
|F04|CRO PK concentration + dosing|vendor file, dose admin table|REPAIR|높음|
|F05|Flat Excel/CSV PMX|ID/TIME/DV/AMT-like 컬럼|REPAIR|중간|
|F06|Legacy NONMEM-like|partial NM variables|AUTO/REPAIR|중간|
|F07|SAD/MAD dose-escalation|full dosing history or ADDL/II|REPAIR|높음|
|F08|Crossover / BA-BE|period/sequence/treatment, 2+ periods|REPAIR|중간|
|F09|DDI (victim-only sampled)|victim CMT, perpetrator dose만 기록|REPAIR|중간|
|F22|DDI (victim+perpetrator sampled)|dual CMT, 양쪽 농도 측정|REPAIR|중간|
|F10|Food-effect|fed/fasted flag, period 구분|REPAIR|낮음|
|F11|Special population (renal/hepatic)|organ function covariate, category rule|REPAIR|중간|
|F12|Pediatric PK|mg/kg or BSA, age/WT/maturation|REPAIR|중간|
|F13|PK/PD continuous biomarker|PK + biomarker, CMT+endpoint policy|REPAIR|중간|
|F14|Exposure-response|exposure metric or concentration + endpoint|REPAIR|중간|
|F15|TTE/count/categorical|event/count/category endpoint|REPAIR|낮음|
|F16|External covariate linkage|KNHANES/lab/genotype, key+policy|REPAIR|낮음|
|F17|FACS-derived endpoint|gated tabular output, CMT policy|REPAIR|낮음|
|F18|qPCR-derived endpoint|Ct/ΔCt policy, scaling rule 있음|REPAIR|낮음|
|F19|Simple preclinical PK|animal ID+dose+sample+conc|AUTO/REPAIR|중간|
|F20|TDM/real-world PK|irregular dosing, time recoverable|REPAIR|중간|
|F21|Urine/interval collection PK|amount/rate/interval event|REPAIR|낮음|
|F23 (구 F22)|Combination/concomitant therapy|multi-drug, CMT policy, regimen table|REPAIR|낮음|

[v4.1 note — C14] **F02**: harmonization policy가 없으면 Q05 QUARANTINE. Family register에 포함되기 위한 전제 조건이 "harmonization policy 있음"임을 명시. 정책 없는 multi-study data는 F02 operational scope 밖이다.

[v4.1 note] **F09/F22 재편**: v4의 F09(DDI)를 A8 분리에 맞춰 F09(victim-only)와 F22(victim+perpetrator)로 분리. 구 F22(Combination)는 F23으로 번호 변경.

**UNSUPPORTED/INVALID (분모 제외):**

|ID|Family|처리|
|---|---|---|
|F24|raw FCS/qPCR without derivation|UNSUPPORTED|
|F25|omics/imaging/waveform raw|UNSUPPORTED|
|F26|unstructured notes only|UNSUPPORTED|
|F27|unrecoverable core missing|INVALID|

---

### V4.1 Scope Statement (공식 문서용)

```
Frozen Universe v4.1
Routine Clinical/Preclinical PMX-to-NONMEM Dataset Universe

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
  1. QUARANTINE always carries a specific Q-code (Q01–Q15D).
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

Operational scope: F01–F23
Out-of-scope but captured: F24–F27

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
```

---

### v4 vs v4.1 핵심 차이 요약

| 항목                          | v4                    | v4.1                                            |
| --------------------------- | --------------------- | ----------------------------------------------- |
| A4 상태 수                     | 9개                    | 13개 (+4)                                        |
| A5 상태 수                     | 10개                   | 11개 (+1)                                        |
| A8 DDI 처리                   | DDI-ROLES-DEFINED 단일  | DDI-VICTIM-ONLY / DDI-VICTIM-PERPETRATOR 분리     |
| A9 상태 수                     | 12개                   | 14개 (+2)                                        |
| A10 SEMI-STRUCTURED         | 단일 상태                 | 보조 필드 `source_parser_subtype` 추가                |
| Q-code 수                    | Q01–Q15 (15개)         | Q01–Q15D (18개)                                  |
| AIC template                | endpoint_data_type 없음 | AIC-PKPD/ER/TTE/BIOMARKER에서 필수                  |
| DDI family                  | F09 단일                | F09 (victim-only) + F22 (victim+perpetrator) 분리 |
| 전체 operational family       | F01–F22               | F01–F23 (재번호)                                   |
| Scope statement constraints | 4개                    | 6개 (+2)                                         |