# Provenance Gaps — c-unit chain 입력/출력 계약 불일치 기록

> 기록 전용 문서. 코드·spec·test 수정 없이 Phase 5(orchestrator chain) 진입 전 점검 대상을 모은다.
> 각 항목은 단위테스트(Phase 4)에서는 green이지만 c 간 chain 시 드러나는 계약 불일치다.

---

## [GAP-1] cmt_map 표기 불일치 (c0208 ↔ c0013)

- **현상:** `cmt_map` meta 키의 구조가 두 c에서 다르다.
  - c0208 fixture: **flat** — 예) `{"DrugA_IV_dose": 1}`
  - c0013 fixture: **nested** — 예) `{"DrugA": {"dose": 1, "obs": 2}}`
- **영향:** 현재는 각 단위테스트가 자기 fixture만 사용하므로 무충돌. 단 Phase 5에서 c0208→c0013을 chain하면 동일 `meta['cmt_map']` 계약이 불일치하여 깨진다.
- **status:** OPEN
- **영향 범위:** Phase 5 (orchestrator meta 계약)

---

## [GAP-2] dose_interval provenance (c0015 → c0016)

- **현상:** c0016(`assign_ii`)은 `dose_interval` 입력 컬럼에서 II를 도출한다. 그러나 선행 c0015(`assign_addl`)는 ADDL만 emit하고 반복 dose 행을 drop할 뿐 `dose_interval`을 산출하지 않는다.
- **현재 상태:** c0016 fixture가 `dose_interval`을 직접 주입하므로 단위테스트는 green. 하지만 c0015→c0016 chain에서는 입력 `dose_interval`이 부재한다.
- **해결 후보:** c0015가 등간격 압축 시 `dose_interval`을 emit하도록 spec 변경(사용자 승인 필요).
- **status:** OPEN
- **영향 범위:** Phase 5

---

## [GAP-3] covariate 컬럼명 리스트 provenance (생산자 부재; c0207 ↔ c0022/c0023/c0140/c0141)

- **현상:** 하류 공변량 transform c들이 `meta['baseline_covariates']`·`meta['tv_covariates']`(공변량 컬럼명 리스트)를 순회한다.
  - 소비: c0022(`ASSIGN BASELINE_COVARIATE`), c0023(`ASSIGN TIME_VARYING_COVARIATE`), c0140(`ASSIGN BASELINE_COVARIATE`, L-2→L-3), c0141(`ASSIGN TIME_VARYING_COVARIATE`, L-2→L-3). postcond/snippet이 `for cov in meta.get('baseline_covariates'|'tv_covariates', [])` 형태로 두 리스트를 직접 iterate. (2026-05-28 정정: 구 `c0024/c0025` 표기는 spec renumber 전 잔재 — 해당 c_id 파일·엔트리 부재, L962/L992의 실제 c는 c0140/c0141.)
  - 그러나 이 두 meta 키를 **`output_schema_delta`로 선언/생성하는 c가 c-unit 집합 어디에도 없다.** A7 detector c0207(`CLASSIFY COVARIATE_LAYOUT`)은 `meta['a7_state']`만 emit. mess 층 c0380(`meta['cov_layout']`)·c0381(`meta['cov_layout_classified']`)도 컬럼명 리스트는 미생성.
- **영향:** 단위테스트(Phase 4)는 fixture가 두 리스트를 직접 주입하면 green. Phase 5에서 c0207→c0022/c0023 chain 시 리스트 부재 → `meta.get(...,[])`가 빈 리스트 → `for` 루프가 빈 순회(silent no-op). 공변량 미코딩 상태로 postcond가 vacuously true → **silent error(Lock 3 위반) 위험**.
- **참고:** blq_detected는 mess 층(c0306-area, c_units.json L1737)이 생성하므로 c0205 책임 아님(gap 아님). 본 건은 그와 달리 **어떤 층에서도 생산되지 않는** 키라는 점이 다르다.
- **해결 후보:** c0207(`CLASSIFY COVARIATE_LAYOUT`)의 output_schema_delta를 확장해 `meta['baseline_covariates']`·`meta['tv_covariates']`도 emit(분류 결과로 컬럼명 리스트 산출). spec 변경 → 사용자 승인 필요. [[GAP-2]](dose_interval)와 동형(consumer가 읽는 derived 산출을 선행 c가 미생성).
- **status:** OPEN
- **영향 범위:** Phase 5 (+ c0207 구현 세션 전 spec 확장 결정 필요)

---

## [PRINCIPLE] happy fixture 입력 스키마 = 선행 c 출력 스키마

- happy fixture의 입력 컬럼은 선행 c(`requires_detection_by`)의 출력 스키마와 일치해야 한다. 불일치 시 단위테스트는 green이어도 chain에서 깨진다.
- → Phase 5 진입 전 전체 c의 input/output 컬럼 계약을 점검할 것.

---

## [GAP-4] A0 입력(analysis_intent / endpoint_data_type) 생산자 부재 — 외부 경계 입력 (c0200)

- **현상:** c0200(`VERIFY COLUMN_SCHEMA` = A0 axis classifier)은 `meta['analysis_intent']`(선언 AIC 코드, 1차 신호)와 `meta['endpoint_data_type']`(2차 fallback)을 read한다. 두 키 모두 c-unit 집합 어디에서도 `output_schema_delta`로 생성되지 않는다.
  - grep 결과: `analysis_intent`/`endpoint_data_type`은 c0200 spec과 하류 ROUTE c(c_units.json L1547, `precondition: a0_state=='AIC-MISSING'→Q11`)에서만 등장. 생산 c 없음.
- **성격:** A0는 진입 axis(N0)이며 두 키는 **sponsor/분석 프로토콜(외부)에서 오는 경계 입력**이다(spec `input_schema_delta`: "dataset metadata, analysis protocol"). GAP-1/2/3과 달리 c↔c chain 단절이 아니라 by-design 외부 입력 — 단 Phase 4 입력계약 점검 지시에 따라 기록한다.
- **영향:** 단위테스트는 fixture meta가 두 키를 직접 주입하므로 green. Phase 5 orchestrator는 sc/fixture meta가 이 키를 제공하는지(또는 미제공 시 AIC-MISSING→Q11으로 graceful) 확인 필요.
- **status:** OPEN (by-design 외부 입력, 기록 전용)
- **영향 범위:** Phase 5 (orchestrator가 외부 meta를 어떻게 주입하는지)

---

## [GAP-5] c0204 라우팅 범위 불일치 — universe_sm(Q04/INVALID) ↔ can_route_to_q([Q08,Q14])

- **현상:** universe_sm §3 A4(L131-136)는 `INFUSION-STOP-RESTART(無 정책)→Q04`, `UNRECOVERABLE→INVALID`로 라우팅한다. 그러나 c_units.json의 `c0204.can_route_to_q=[Q08,Q14]`이고 `verify_visualization.fail_route_to=Q08`이다.
- **구현 결정(사용자 승인):** c0204는 spec의 can_route_to_q를 준수해 `route_to_q ∈ {None, Q08, Q14}`만 산출한다. INFUSION-STOP-RESTART·UNRECOVERABLE은 a4_state로 **분류는 하되**(13-state 전수 분류 유지) `route_to_q=None`으로 둔다. Q04/INVALID 종착은 하류 ROUTE c의 책임(D-S1/D-S4)이다. (분류 범위 ≠ 라우팅 범위.)
- **영향:** c0204 단위테스트는 위 계약대로 green. Q04(INFUSION 정책 부재)·INVALID(UNRECOVERABLE) 종착이 실제 tree에 존재하려면 하류에 대응 ROUTE c(또는 conditional edge)가 있어야 한다. Phase 7 decision-tree 조립 시 고립 terminal/누락 conditional-edge로 드러날 수 있다.
- **해결 후보:** (a) c0204.can_route_to_q에 Q04 추가 + Q04 q_code 정의/연결, (b) UNRECOVERABLE→INVALID terminal을 별도 ROUTE c로 명시. 둘 다 spec 변경 → 사용자 승인 필요.
- **status:** ✅ RESOLVED (Phase 7 결정 A·B, 사용자 승인 — 해결후보 (a)+(b) 채택). (a) c0204.can_route_to_q에 Q04 추가 → c0204→Q04 conditional edge. (b) UNRECOVERABLE→INVALID는 c0252→INVALID terminal_routing(결정 B). cite: universe_sm §3 A4 '無 Q04'. 상세 [[GAP-34]].
- **영향 범위:** Phase 7 (decision-tree conditional-edge 재구성 D-S4), q_codes(Q04 SM 연결 여부)

---

## [GAP-6] A1 입력(study integration / harmonization policy) 생산자 부재 — 외부 경계 입력 (c0201)

- **현상:** c0201(`DETECT SHEET_INVENTORY BY ACROSS_FILE` = A1 axis classifier)은 선언 신호 `meta['study_integration']`(1차), `meta['interim_analysis']`, `meta['harmonization_policy_present']`(Q05 gating), `meta['studies']`/`meta['n_studies']` 및 df의 study 식별자 컬럼(`study_id`/`STUDYID`/`study`/`STUDY`)을 read한다. 이 meta 키들을 `output_schema_delta`로 생성하는 c가 c-unit 집합 어디에도 없다.
- **성격:** A1은 진입 인접 axis이며 study integration/harmonization 정책은 **sponsor·file inventory(외부)에서 오는 경계 입력**이다(spec `input_schema_delta`: "file inventory, study metadata"). [[GAP-4]](A0 외부 입력)와 동형 — c↔c chain 단절이 아니라 by-design 외부 입력.
- **영향:** 단위테스트는 fixture meta가 키를 직접 주입하므로 green. Phase 5 orchestrator는 sc/fixture meta가 이 키들을 제공하는지(미제공 시 df study 수로 graceful 추론) 확인 필요. harmonization_policy_present 부재 시 MULTI-*는 Q05로 라우팅됨에 유의.
- **status:** OPEN (by-design 외부 입력, 기록 전용)
- **영향 범위:** Phase 5 (orchestrator가 외부 meta를 어떻게 주입하는지)

---

## [GAP-7] A3 입력(time policy / time anchor) 생산자 부재 — 외부 경계 + 상류 시간 정규화 (c0203)

- **현상:** c0203(`DETECT TIME_FORMAT` = A3 axis classifier)은 선언 `meta['time_policy']`(1차)를 read하고, 부재 시 df의 시간 컬럼(`time_value` 또는 `TIME`, precondition이 보장)으로 fallback 추론한다(전부 파싱가능→ACTUAL / 혼재 토큰→AMBIGUOUS / 전부 결측→UNRECOVERABLE).
  - `time_policy`(및 spec python_snippet이 참조하는 `time_anchor`)는 생산 c 없음 → sponsor/protocol 외부 경계 입력(GAP-4/GAP-6 동형).
  - `time_value`/`TIME` 컬럼은 c0203 책임이 아니라 **상류 L-4 시간 정규화 mess c**(CONVERT TIME_FORMAT 계열)가 생산해야 한다. happy fixture는 이 컬럼을 직접 주입하므로 green이나, chain 시 선행 시간 정규화 c의 출력 컬럼명이 `time_value`/`TIME`와 일치하는지 점검 필요([[PRINCIPLE]] happy 입력=선행 출력).
- **라우팅 정합성(참고, gap 아님):** llm_prompt 산문은 "UNRECOVERABLE→INVALID"라 적었으나 `can_route_to_q=[Q02,Q12]`이고 q_codes Q12 trigger가 `A3 = UNRECOVERABLE`(human_decision_point: 복원 데이터 제공 또는 INVALID 수용)이다. 따라서 AMBIGUOUS→Q02, UNRECOVERABLE→Q12 모두 **scope 내**이며 c0204(GAP-5)와 달리 라우팅 scope 불일치가 **아니다**(INVALID는 Q12 이후 사람 결정).
- **status:** OPEN (외부 입력 + 상류 컬럼 provenance, 기록 전용)
- **영향 범위:** Phase 5 (time_value 컬럼 생산 c와의 계약 점검)

---

## [GAP-8] c0205 라우팅 범위 불일치 — universe_sm(ABSENT→INVALID) ↔ can_route_to_q([Q01,Q15D])

- **현상:** universe_sm/llm_prompt는 A5 `ABSENT → INVALID`로 라우팅한다. 그러나 `c0205.can_route_to_q=[Q01,Q15D]`이고 어떤 q_code trigger에도 ABSENT가 없다(Q01 trigger=BLQ/LLOQ/ULOQ/replicate-no-policy, Q15D trigger=BIOANALYTICAL-FINAL-FLAG-MISSING).
- **구현 결정(c0204 GAP-5 선례 준수):** c0205는 `route_to_q ∈ {None, Q01, Q15D}`만 산출한다. ABSENT는 a5_state로 **분류는 하되**(15-state 전수 분류 유지) `route_to_q=None`으로 둔다. INVALID 종착은 하류 ROUTE c의 책임(D-S1/D-S4)이다. (분류 범위 ≠ 라우팅 범위.) `pass = (route is None)` 계약상 ABSENT는 pass=True가 되지만, 이는 c0204 UNRECOVERABLE/INFUSION-STOP-RESTART와 동일한 scope-out 처리다.
- **입력 provenance(참고):** c0205는 선언 `meta['obs_blq_state']`(외부 경계 입력, 생산 c 없음)와 df `dv_value`로 fallback한다. `dv_value`는 상류(c0017 ASSIGN DV / 시간·관측 정규화 mess 층)가 생산. `blq_detected`(mess 층 c0306-area 생산)는 본 c가 직접 쓰지 않으므로 gap 아님([[GAP-3]] 참고).
- **영향:** c0205 단위테스트는 계약대로 green. ABSENT→INVALID terminal이 실제 tree에 존재하려면 하류에 대응 ROUTE c(또는 conditional edge)가 있어야 한다. Phase 7 조립 시 고립 terminal/누락 conditional-edge로 드러날 수 있다([[GAP-5]]와 동형).
- **해결 후보:** (a) ABSENT→INVALID terminal을 별도 ROUTE c로 명시, (b) 필요 시 q_code/terminal 연결. spec 변경 → 사용자 승인 필요.
- **status:** ✅ RESOLVED (Phase 7 결정 B). A5 ABSENT→INVALID는 c0253(ROUTE, postcond에 INVALID 선언)에서 `c0253→INVALID` terminal_routing edge(111 strand)로 표현 → INVALID 도달성 확보(고립 terminal 0). 라우팅 scope "불일치"는 by-design(INVALID는 Q-code 아님 → can_route_to_q 미포함이 정상). c0205 obs_blq_state 외부입력은 Phase 5/① by-design 잔여. 상세 [[GAP-34]].
- **영향 범위:** Phase 7 (decision-tree conditional-edge 재구성 D-S4)

---

## [GAP-9] A2 입력(study design / protocol) 생산자 부재 + fallback 한계 — 외부 경계 입력 (c0202)

- **현상:** c0202(`CLASSIFY REGIMEN_DESCRIPTOR` = A2 axis classifier)는 선언 `meta['study_design']`(1차)와 `meta['protocol']`(2차, clean token만)을 read한다. 두 키 모두 c-unit 집합 어디에서도 `output_schema_delta`로 생성되지 않는다(sponsor/protocol 외부 경계 입력). [[GAP-4]](A0) / [[GAP-6]](A1)와 동형.
- **fallback 한계(★ 정직하게 기록):** anchors.json A2는 정확히 10개 clean state로 **UNKNOWN/MISSING state가 없다**(A0의 AIC-MISSING→Q11 같은 graceful Q escape 부재). 따라서 선언 부재 시에도 deterministic하게 10개 중 하나를 반환해야 하는데, df fallback은 `period`+`sequence` 컬럼 동시 존재 → `CROSSOVER`, 그 외 → `PARALLEL` 기본값만 구분 가능하다. **나머지 8개 design(SAD-MAD/BE/DDI/FOOD-EFFECT/SPECIAL-POP/PEDIATRIC/TDM-RWD/PRECLINICAL)은 선언 없이는 구분하지 못하고 PARALLEL로 떨어진다**(test_adversarial `test_fallback_limit_sad_mad_to_parallel`로 한계를 고정). 정확한 A2 분류는 `study_design` 선언에 의존한다.
- **라우팅 정합성(참고, gap 아님):** universe_sm §3 A2(L124-125)는 10개 state 모두 Q/INVALID 라우팅 주석이 없다(A1→Q05, A3→Q02/INVALID, A4→Q14/Q08과 대조). `c0202.can_route_to_q=[]`와 일치 → **라우팅 scope 불일치가 아니다**([[GAP-5]]/[[GAP-8]]과 다른 순수 분류기). route_to_q 항상 None, pass 항상 True.
- **영향:** c0202 단위테스트는 fixture meta가 `study_design`을 직접 주입하므로 green. Phase 5 orchestrator는 sc/fixture meta가 `study_design` 선언을 제공하는지 확인 필요. 미제공 시 PARALLEL 기본값으로 silent 격하될 수 있으므로(8개 design 미구분) orchestrator가 외부 선언을 주입해야 한다.
- **해결 후보:** orchestrator가 sc/external meta에서 `study_design`을 주입(Phase 5). 필요 시 A2에 UNKNOWN/MISSING state + Q escape 추가는 spec/universe 변경 → 사용자 승인 필요.
- **status:** OPEN (by-design 외부 입력 + fallback 한계, 기록 전용)
- **영향 범위:** Phase 5 (orchestrator가 study_design 외부 meta를 어떻게 주입하는지)

---

## [GAP-10] c0206 Q03 교차축 라우팅 + 입력(occasion_partition_rule / event_row_state) 생산자 부재 (c0206)

- **현상:** c0206(`CLASSIFY ROW_ORDERING` = A6 axis classifier)은 a6_state를 6-state 전수 분류하고 q_codes SSOT로 라우팅한다. route_to_q ∈ {None, Q03, Q04}.
  - **Q04(자기축):** `A6 = AMBIGUOUS`(q_codes Q04 trigger의 A6 disjunct). Q04의 `A4=INFUSION-STOP-RESTART` disjunct는 c0204 소관([[GAP-5]]), c0206 scope 밖.
  - **Q03(교차축):** q_codes Q03 trigger=`AIC-POPPK + occasion partition rule 미기재`로 **A6 state가 아니다.** c0206은 `meta['a0_state']=='AIC-POPPK'`(c0200 생산) AND `meta['occasion_partition_rule']` 부재일 때 Q03 emit.
- **라우팅 정합성(★ scope, gap의 핵심):** universe_sm §3 A6 산문은 `AMBIGUOUS(→Q04)`만 적고 Q03을 누락한다(llm_prompt 산문 비신뢰 — c0203 선례). 그러나 q_codes `Q03.recover_to_c_id=c0206`이고 c0200(A0)은 Q11만 emit(Q03 미emit)하므로 **Q03의 유일한 emitter는 c0206**이다. 미구현 시 Q03은 incoming conditional edge 0의 고립 Q-terminal로 Phase 7에서 STOP(D-S4). 따라서 c0206이 Q03을 emit하는 것이 정합(사용자 승인 Option A). [[GAP-5]]/[[GAP-8]]의 "state→can_route_to_q 밖 Q"와는 역방향: can_route_to_q 안의 Q를 교차축 조건으로 emit.
- **우선순위:** `a6_state==AMBIGUOUS`(Q04) AND `popPK+occasion 부재`(Q03) 동시 충족 시 **Q04 우선**. universe_sm/q_codes에 명시 우선순위 부재 → 자기축 row-type blocker(Q04)를 교차축 occasion gate(Q03)보다 먼저 평가(test_adversarial `test_q04_precedence_over_q03`로 고정).
- **입력 provenance:**
  - `meta['a0_state']`: c0200(A0) 생산 → **c↔c chain 입력**(c0206 read-only 참조, write 금지). c0206은 c0200 선행을 전제한다(detection pass-chain). [[GAP-4]](A0 외부 입력)와 연결.
  - `meta['occasion_partition_rule']`: 생산 c 없음 → **sponsor/protocol 외부 경계 입력**([[GAP-4]]/[[GAP-6]]/[[GAP-9]] 동형). 부재=미기재.
  - `meta['event_row_state']`: 선언 descriptor, 생산 c 없음 → 외부 경계 입력. 부재 시 df(`time_value`+event)로 SEPARABLE/SAME-TIME-RESOLVABLE만 fallback 추론(나머지 4 state는 descriptor 의존). [[GAP-8]] obs_blq_state와 동형.
- **★ chain 전제(Phase 5 STOP 조건):** orchestrator가 A0 axis를 건너뛰어 c0206 실행 시점에 `meta['a0_state']`가 부재한 경로가 생기면 Q03 gate가 silent하게 미발화된다(graceful·날조 없음이나 Q03 미도달). 그런 경로가 가능하면 Phase 5에서 STOP·점검. 단위테스트 fixture meta는 a0_state를 포함한다.
- **status:** OPEN (기록 전용, 수정 안 함)
- **영향 범위:** Phase 5 (a0_state chain + occasion_partition_rule 외부 주입), Phase 7 (Q03 conditional edge 재구성 D-S4)

---

## [GAP-11] c0207 covariate_state 선언 생산자 부재 + df fallback 8-of-3 한계 (c0207)

- **현상:** c0207(`CLASSIFY COVARIATE_LAYOUT` = A7 axis classifier)은 a7_state를 8-state 전수 분류하고 q_codes SSOT로 라우팅한다. route_to_q ∈ {None, Q07, Q13}.
  - **Q07(자기축):** q_codes Q07 trigger=`A7 = POLICY-MISSING`. **Q13(자기축):** q_codes Q13 trigger=`A7 = KEY-MISSING`. 둘 다 A7 자기축 disjunct — [[GAP-10]] c0206 Q03 같은 교차축 trigger 없음(선행 axis 가용성 점검 불필요).
- **입력 provenance:**
  - `meta['covariate_state']`: 선언 descriptor, 생산 c 없음 → **sponsor/protocol 외부 경계 입력**([[GAP-4]]/[[GAP-6]]/[[GAP-9]]/[[GAP-10]] event_row_state 동형, orchestrator Phase 5 주입). {개념}_state 패턴(A5 obs_blq_state / A6 event_row_state)과 일관.
  - df의 covariate 컬럼(WT/AGE/SEX/...)은 상류 normalization이 생산([[PRINCIPLE]] happy 입력=선행 출력).
- **★ fallback 한계(정직하게 기록, c0202 [[GAP-9]] 동형):** 선언 부재 시 df fallback은 8개 중 **3개만** 도달한다 — cov 컬럼 없음→NONE-REQUIRED / cov 있고 결측 있음→BASELINE-IMPUTABLE / cov 있고 결측 없음→BASELINE-CLEAN. 나머지 5개(TIME-VARYING/EXTERNAL-JOIN/PEDIATRIC-MATURATION/KEY-MISSING/POLICY-MISSING)는 `covariate_state` 선언 없이는 도달 불가하며 BASELINE-* 3개로 떨어진다(test_adversarial `test_fallback_limit_time_varying_to_baseline`로 한계 고정). ★ df만으로 Q07/Q13(POLICY-MISSING/KEY-MISSING) **날조 금지**([[GAP-10]] c0206 'Q 날조 금지' 선례) — 라우팅은 선언 기반. 선언 있으면 항상 선언 우선.
- **GAP-3 관계(★ 유지):** [[GAP-3]]는 하류 consumer(c0022/c0023)가 읽는 `baseline_covariates`/`tv_covariates` 컬럼명 리스트의 생산자 부재 문제다. **c0207은 본 gap을 해소하지 않는다** — `meta['a7_state']`만 emit하고 두 리스트는 produce하지 않는다(output_schema_delta 확장 금지, 사용자 확정). GAP-3는 Phase 5 일괄 정산 대상으로 그대로 OPEN 유지.
- **영향:** c0207 단위테스트는 fixture meta가 `covariate_state`를 직접 주입(또는 df fallback)하므로 green. Phase 5 orchestrator는 sc/external meta가 `covariate_state` 선언을 제공하는지 확인 필요. 미제공 시 BASELINE-* 3개로 silent 격하될 수 있으므로(5개 도메인 state 미구분) orchestrator가 외부 선언을 주입해야 한다. POLICY-MISSING/KEY-MISSING 미선언 경로는 Q07/Q13 gate가 silent 미발화(GAP-3 silent-error 우려와 연결) — Phase 5 점검.
- **status:** OPEN (by-design 외부 입력 + fallback 한계, 기록 전용)
- **영향 범위:** Phase 5 (orchestrator가 covariate_state 외부 meta 주입), Phase 7 (Q07/Q13 conditional edge 재구성 D-S4)

---

## [GAP-12] c0209 입력계약(defect_state 생산자 부재) + srp NOUN↔구현 AUDIT + IRRECONCILABLE 라우팅 scope (c0209)

- **★ srp NOUN AUDIT(표면 불일치, 결함 아님):** `c0209.srp_intent = VERIFY CROSS_COLUMN_INVARIANT`는 *컬럼 간 불변식 검증*(예: AMT≠NA⟹EVID∈{1,4})을 시사하나, 실제 `postcondition_predicate`는 **membership 술어**(`meta.get('a9_state') in [...13 state...]`)이고 output은 `meta['a9_state']`, layer는 L-3→L-4(axis 평가)다. 즉 c0209는 **A9 axis-state 분류기**이며 c0200~c0208과 동형(membership 패턴). NOUN과 구현 의도의 표면 불일치만 기록(spec 수정 안 함).
- **★ 입력계약(사용자 가설 반증):** c0209가 EVID/AMT/DV/CMT 등 transform 산출 NONMEM 특수컬럼을 교차검증할 것이란 가설은 **반증된다.** 그 컬럼들은 하류 **L-1→L-2 transform**(c0010 ASSIGN EVID / c0012 ASSIGN AMT / c0017 ASSIGN DV / c0013 ASSIGN CMT)이 산출하며, A9 평가 시점(L-3→L-4)엔 **아직 부재**다. c0209는 그 컬럼들을 읽지 않는다 → **c↔c chain 의존 없음.** 실제 입력:
  - `meta['defect_state']`: 선언 descriptor(13-state). 생산 c 없음 → sponsor/protocol **외부 경계 입력**([[GAP-4]]/[[GAP-6]]/[[GAP-9]]/[[GAP-11]] 동형, orchestrator Phase 5 주입). `{개념}_state` 패턴 일관(A5 obs_blq_state / A6 event_row_state / A7 covariate_state).
  - df fallback: 완전중복은 전체 행, UNSORTED는 id 후보(`subject_id`/`ID`/`id`) + time 후보(`time_value`/`TIME`/`time`)로 판정. raw 컬럼은 상류 normalization 산출([[PRINCIPLE]] happy 입력=선행 출력).
- **fallback 한계(정직 기록, [[GAP-11]]/[[GAP-9]] 동형):** 선언 부재 시 df fallback은 13개 중 **3개**(DUPLICATE-EXACT/UNSORTED/CLEAN)만 도달. 나머지 10개(COLUMN-SYNONYM/UNIT-CONVERSION/ENCODING-FIX/PRE-DOSE-SAMPLE/PLANNED-VS-ACTUAL/PROTOCOL-DEVIATION/REANALYSIS-FINAL-DEFINED/REANALYSIS-FINAL-MISSING/PROTOCOL-DEVIATION-NO-POLICY/IRRECONCILABLE)는 `defect_state` 선언 의존. ★ df만으로 Q06/Q15D 날조 금지. ★ P3(universe_sm §6): full-row 완전중복만 DUPLICATE-EXACT(동일 (ID,TIME) 다른 DV = replicate, A5 소관)로 보아 silent data loss 차단.
- **라우팅 scope 불일치([[GAP-5]]/[[GAP-8]] 선례 준수):** universe_sm §3 A9는 `IRRECONCILABLE → INVALID`로 라우팅하나 `can_route_to_q=[Q06,Q15D]`이고 INVALID는 Q-code 아님. c0209는 `route_to_q ∈ {None, Q06, Q15D}`만 산출하고 IRRECONCILABLE은 **분류는 하되 route_to_q=None**(`pass=True`). INVALID 종착은 하류 ROUTE c 책임(D-S1/D-S4). (분류 범위 ≠ 라우팅 범위.) Q06=PROTOCOL-DEVIATION-NO-POLICY, Q15D=REANALYSIS-FINAL-MISSING은 q_codes SSOT trigger와 정합(둘 다 자기축 A9 disjunct; Q15D는 A5 disjunct와 OR이며 A5분기는 c0205 소관).
- **영향:** c0209 단위테스트는 fixture meta가 `defect_state`를 직접 주입(또는 df fallback)하므로 green. Phase 5 orchestrator는 sc/external meta가 `defect_state` 선언을 제공하는지 확인 필요(미제공 시 CLEAN/DUPLICATE-EXACT/UNSORTED 3개로 silent 격하 — 10개 도메인 state 미구분). IRRECONCILABLE→INVALID terminal이 tree에 존재하려면 하류 ROUTE c(또는 conditional edge) 필요 — Phase 7 D-S4에서 고립 terminal로 드러날 수 있음([[GAP-5]]/[[GAP-8]] 동형).
- **status:** Phase 7 facet ✅ RESOLVED (결정 B — A9 IRRECONCILABLE→INVALID는 c0256→INVALID terminal_routing edge(30 strand)로 표현, D-S4 고립 terminal 해소). 잔여 OPEN: defect_state 외부입력·df fallback 한계·srp NOUN audit는 Phase 5/① by-design. 상세 [[GAP-34]].
- **영향 범위:** Phase 5 (defect_state 외부 주입), Phase 7 (Q06/Q15D conditional edge + IRRECONCILABLE→INVALID terminal 재구성 D-S4)

---

## [GAP-13] c0210 위치 불일치(파일형식=front vs A10=chain 끝) + df fallback 1-of-8 한계 + 입력(file_format) 생산자 부재 + NON-TABULAR/CORRUPTED scope-out (c0210)

- **★ 위치/timing 불일치(핵심):** c0210(`DETECT FILE_FORMAT` = A10 axis classifier)의 `trigger_condition="파일 로드 직후"`와 의미상 역할(xlsx/csv·인코딩·시트·corrupted/non-tabular 파싱 가능성 = df가 생기기 *전* 파이프라인 맨 앞 게이트)은 **front**를 가리킨다. 그러나 axis 번호는 **A10(마지막)**, `layer_pair=L-3->L-4`, pass_route_to chain은 `c0209(A9)→c0210→"next axis"`로 c0210을 axis sweep **끝**에 배치한다. 즉 *axis 순서 vs 의미상 시점* 불일치다. [[GAP-12]] c0209의 NOUN↔구현 표면 불일치와 동류이나, 여기선 표면이 아니라 **실행 시점**의 불일치다.
- **★ falsifiable 귀결(df fallback 1-of-8 한계):** precondition `len(df) > 0 or meta.get('file_exists')` 하에서 A10이 sweep 끝에 평가되면, 파싱된 df가 존재한다는 것 자체가 **파일이 이미 성공적으로 열렸다**는 뜻이다. → `NON-TABULAR`/`CORRUPTED`는 df 검사로 **구조적 도달 불가**(그런 파일은 애초에 df를 만들지 못한다). 따라서 선언 부재 시 df fallback은 8개 중 **1개(FLAT-TABULAR)만** 도달하며, vendor/format 특화 state(SDTM-ADaM/EDC-STRUCTURED/CRO-VENDOR/LEGACY-NM/SEMI-STRUCTURED)와 두 실패 state는 `file_format` 선언에만 의존한다. 위치 불일치 때문에 [[GAP-9]] c0202(2/10)·[[GAP-11]] c0207(3/8)·[[GAP-12]] c0209(3/13)보다 도달폭이 좁다. df만으로 state 날조 금지(test_adversarial `test_fallback_limit_corrupted_unreachable_via_df`로 한계 고정).
- **입력 provenance:**
  - `meta['file_format']`(1차) / `meta['source_format']`(2차): 선언 descriptor, 생산 c 없음 → sponsor/file inventory **외부 경계 입력**([[GAP-4]]/[[GAP-6]]/[[GAP-9]]/[[GAP-11]]/[[GAP-12]] 동형, orchestrator Phase 5 주입). `{개념}_state`/declared-descriptor 패턴과 일관.
  - `meta['file_exists']`: precondition 사용, 경계/orchestrator 입력(생산 c 없음).
  - `df`: 파일 로드 단계가 생산 = A10이 "감지"하려는 그 대상 자체 → **순환**(위치 불일치의 핵심). df는 read-only로만 참조하며 c0210은 `meta['a10_state']`만 write.
  - ★ 시그니처 메모: spec `python_snippet`은 `detect_source_format(file_path, meta)`(file_path)이나, 형제 c(c0202/c0207/c0209) 및 conftest 하네스는 전부 `(df, meta)` 규약 → **`(df, meta)`로 구현**, file 신호는 meta 경유. (spec 수정 안 함; 표면 불일치 기록.)
- **라우팅 scope 불일치([[GAP-5]]/[[GAP-8]]/[[GAP-12]] 선례 준수):** universe_sm §3 A10은 `NON-TABULAR → UNSUPPORTED`, `CORRUPTED → INVALID`로 라우팅하나, UNSUPPORTED/INVALID는 universe_sm §2 **terminal**(Q-code 아님; anchors.json `terminals`에 존재)이고 `can_route_to_q=[]`이며 q_codes.json에 **A10/FILE_FORMAT 참조 0건**이다. → can_route_to_q=[]와 q_codes는 정합(순수 분류기, [[GAP-9]] c0202 A2 동형). c0210은 8 state를 **분류는 하되** `route_to_q ∈ {None}`만 산출하고 NON-TABULAR/CORRUPTED도 `route_to_q=None`(`pass=True`)으로 둔다. UNSUPPORTED/INVALID 종착은 하류 ROUTE c 책임(D-S1/D-S4). (분류 범위 ≠ 라우팅 범위.) `pass=(route is None)` 계약상 NON-TABULAR/CORRUPTED도 pass=True가 되지만, 이는 [[GAP-8]] c0205 ABSENT 처리와 동일한 scope-out이다.
- **영향:** c0210 단위테스트는 fixture meta가 `file_format`을 직접 주입(또는 df fallback)하므로 green. Phase 5 orchestrator는 (a) sc/external meta가 `file_format` 선언을 제공하는지(미제공 시 FLAT-TABULAR로 silent 격하 — 7개 state·실패 state 미구분), (b) **A10을 실제로 어디에서 실행할지**(의미상 front vs 현 chain 끝) 결정해야 한다. NON-TABULAR→UNSUPPORTED / CORRUPTED→INVALID terminal이 tree에 존재하려면 하류 ROUTE c(또는 conditional edge) 필요 — Phase 7 D-S4에서 고립 terminal로 드러날 수 있음([[GAP-5]]/[[GAP-8]]/[[GAP-12]] 동형).
- **status:** OPEN (위치 불일치 + by-design 외부 입력 + fallback 한계 + scope 기록, 수정 안 함)
- **영향 범위:** Phase 5 (file_format 외부 주입 + A10 실행 위치 결정), Phase 7 (UNSUPPORTED/INVALID terminal + scope-out conditional edge 재구성 D-S4)

---

## [GAP-14] axis c srp_intent NOUN ↔ 구현(axis 분류기) 체계적 불일치 일괄 — Phase 7/8 노드 라벨 매핑 필요 (c0200–c0210)

- **★ 현상(통합 audit):** 11개 axis classifier(c0200–c0210)는 전부 `layer_pair=L-3->L-4`, output=`meta['aN_state']`, postcondition=membership 술어인 **axis-state 분류기**다. 그러나 다수의 `srp_intent` NOUN이 L-1→L-2 컬럼-transform 어휘(COLUMN_SCHEMA/AMT/ROW_ORDERING 등)에서 차용되어 실제 분류기 역할과 표면 불일치한다. [[GAP-12]](c0209)·[[GAP-13]](c0210)에서 단위별로 기록한 NOUN-audit을 전 axis로 일반화한다(spec frozen — 수정 아닌 매핑으로 해소).
  - **명백(clear mismatch):**
    - c0200 `VERIFY COLUMN_SCHEMA` → 실제 A0 analysis_intent 분류(endpoint 기반). COLUMN_SCHEMA 검증 아님.
    - c0201 `DETECT SHEET_INVENTORY BY ACROSS_FILE` → 실제 A1 study integration level 분류([[GAP-6]]).
    - c0202 `CLASSIFY REGIMEN_DESCRIPTOR` → 실제 A2 study design 분류([[GAP-9]]).
    - c0204 `VERIFY AMT` → 실제 A4 dose completeness 분류. AMT 컬럼 transform/검증 아님([[GAP-5]]는 라우팅 scope, 본 항은 NOUN).
    - c0206 `CLASSIFY ROW_ORDERING` → 실제 A6 event-row type 분류. **★ 라벨 충돌:** c0030 `VERIFY ROW_ORDERING BY WITHIN_ID` / c0031 `ASSIGN ROW_ORDERING`(둘 다 L-1→L-2 물리적 행 정렬 c)와 동음이의 — c0206은 물리 정렬이 아니라 event-row 분류([[GAP-10]]).
    - c0209 `VERIFY CROSS_COLUMN_INVARIANT` → 실제 A9 defect repairability 분류([[GAP-12]] 상세; EVID/AMT/DV/CMT 교차검증 아님).
    - c0210 `DETECT FILE_FORMAT` → 실제 A10 source-format 분류([[GAP-13]] 상세; 추가로 실행 위치 불일치).
  - **경미(minor — DETECT/CLASSIFY verb는 분류기와 호환되나 NOUN이 컬럼 개념):**
    - c0203 `DETECT TIME_FORMAT`(A3 time derivation [[GAP-7]]), c0205 `DETECT BLQ_TOKEN`(A5 obs/BLQ [[GAP-8]]), c0208 `CLASSIFY ANALYTE_COLUMN`(A8 multi-drug/CMT).
  - **상대적 정합:** c0207 `CLASSIFY COVARIATE_LAYOUT`(A7 [[GAP-11]]) — CLASSIFY+layout이 axis 역할과 비교적 일치.
- **★ 영향(신규 — 기존 GAP과 차별):** Phase 8 HTML 노드 라벨이 `srp_intent`를 그대로 렌더하면 사용자를 오도한다(Lock-4 semantic equivalence 위반 소지: "VERIFY AMT" 노드가 실제로는 dose-completeness 분류기). Phase 7 decision_tree 조립·Phase 8 HTML에서 노드 표시명은 raw srp_intent가 아니라 **axis 개념으로 매핑**해야 한다(anchors.json `axes` SSOT):
  - A0=analysis_intent, A1=sheet_inventory, A2=regimen_descriptor, A3=time_format, A4=amt(dose completeness), A5=blq_token(obs/BLQ), A6=row_ordering(event-row type), A7=covariate_layout, A8=analyte_column, A9=cross_column_invariant(defect repairability), A10=file_format.
- **외부입력 provenance 보강(#5 — c0204/c0208 전용 gap 부재 보강):**
  - **c0204:** `meta['dose_regimen']`(1차 선언 descriptor) 및 `has_addl_actual_conflict`/`unrecoverable`/`dose_policy_present`(라우팅·gating 플래그)는 생산 c 없음 → sponsor/protocol **외부 경계 입력**([[GAP-4]]/[[GAP-6]]/[[GAP-9]]/[[GAP-12]] 동형). c0204 기존 [[GAP-5]]는 라우팅 scope 한정 — 입력 provenance는 본 항에서 보강.
  - **c0208:** `meta['study_type']`(=="DDI" 시 DDI-VICTIM-* 최우선 분기), `perpetrator_analytes`, `parent_metabolite_map`, `cmt_map`는 생산 c 없음 → study-level **외부 경계 입력**. ⚠ `cmt_map` 구조 불일치(c0208 flat vs c0013 nested)는 이미 [[GAP-1]]에 기록 — **중복 금지**, cmt_map은 [[GAP-1]] 참조하고 본 항은 study_type 등 나머지 외부입력 provenance만 보강한다.
- **해결 후보:** Phase 7/8에서 노드 라벨을 axis 개념으로 매핑하는 표시명 사전 도입(spec srp_intent는 frozen 유지). c0204 dose_regimen·c0208 study_type 등 외부입력은 Phase 5 orchestrator가 sc/external meta로 주입.
- **status:** OPEN (표면 NOUN 불일치 + HTML 라벨 매핑 + 외부입력 provenance 기록 전용, spec 수정 안 함)
- **영향 범위:** Phase 7 (decision_tree 노드 명명 — axis 개념 매핑), Phase 8 (HTML 노드 라벨), Phase 5 (c0204 dose_regimen / c0208 study_type 외부 주입)

---

## [GAP-15] c0020/c0021 BLQ·LLOQ assign 입력 chain (blq_detected/lloq_value←c0306, blq_policy 생산자 부재, BLQ_FLAG 형제 chain)

> 기록: 2026-05-28 (Phase 4 사전 transform 입력계약 점검).

- **현상:** L-1→L-2 BLQ/LLOQ assign transform 2종의 데이터 입력이 detection gate(c0205) 밖에서 온다.
  - **c0020(`ASSIGN BLQ_FLAG`):** `df['blq_detected']`(bool) + `meta['blq_policy']`(M1/M3/M4/M5) + `df['EVID']`(c0010 산출) + `meta['a5_state']`(c0205 산출)를 read.
  - **c0021(`ASSIGN LLOQ`):** `df['lloq_value']` + `df['BLQ_FLAG']`(존재 시) + `df['EVID']` + `meta['a5_state']`를 read.
- **provenance:**
  - `blq_detected`·`lloq_value`: mess 층 **c0306(`NORMALIZE BLQ_TOKEN`, L-4→L-5, 미구현)**가 생산(c_units.json c0306 output: blq_detected mask + lloq_value 추출). [[GAP-8]]에서 "c0205 소관 아님"으로 정리된 키들이며 실제 생산자는 c0306 → c0306→c0020/c0021 **상향 cross-layer chain**(c0306 미구현 시 단위테스트는 fixture 주입, Phase 5 chain서 컬럼 부재).
  - `blq_policy`: **생산 c 전무 → sponsor/bioanalytical 외부 경계 입력**([[GAP-4]]/[[GAP-6]]/[[GAP-9]]/[[GAP-11]] 동형). M1(제외)/M3/M4(likelihood)/M5는 사람 정책 결정(Q01 routing 해소). 기존 GAP 미기록 → 본 항 신규.
  - `BLQ_FLAG`(c0021 입력): **c0020 형제 transform 생산** → c0020→c0021 c↔c chain(같은 layer 내 순서 의존).
- **★ detection gate ≠ 입력계약(핵심):** `requires_detection_by=c0205`는 a5_state(분류)만 보장 — BLQ 토큰의 *정규화 산출물*(blq_detected/lloq_value)은 보장하지 않는다. D-S1 gate 충족이 입력계약 충족을 함의하지 않는다.
- **영향:** c0020/c0021 단위테스트는 fixture가 blq_detected/lloq_value/blq_policy/BLQ_FLAG를 직접 주입하면 green([[PRINCIPLE]]). Phase 5 orchestrator는 (a) c0306이 c0020/c0021보다 선행하는지(cross-layer 순서), (b) blq_policy 외부 meta 주입 여부, (c) c0020→c0021 순서를 보장해야 한다. blq_policy 부재 시 M1/M5 분기(BLQ_FLAG/LLOQ 컬럼 미생성)로 silent 격하 가능.
- **★ 종결(Phase 5 slice 6 — effective producer 배선·활성화):** mess 층 producer **c0306(`NORMALIZE BLQ_TOKEN`) 구현·배선 완료**(`src/c_units/c0306_*`; orchestrator REGISTRY). c0306이 산출하는 `blq_detected`(mask)·`lloq_value`(토큰서 추출)가 기구현 휴면 자산 **c0020(`ASSIGN BLQ_FLAG`)·c0021(`ASSIGN LLOQ`)를 cross-layer 활성화**함을 동적 테스트로 증명(`tests/test_strands.py::test_blq_activation_chain_dynamic` — `["c0305","c0306","c0205","c0020","c0021"]`, blq_policy=M3 주입 → BLQ_FLAG=[1,1,1]·LLOQ=[0.1,0.1,0.05]). (a) cross-layer 순서(c0306 ≺ c0020/c0021)·(c) c0020→c0021 형제 순서 모두 orchestrator로 실현. D-S1 cut-vertex는 `test_d_s1_blq_flag_cut_vertex_negative`(c0205_ran 부재 시 RuntimeError — blq_detected가 df에 있어도 거부, gate=감지 '실행')로 고정.
- **잔여(by-design 외부입력 — 통합 시 주입, 종결 아님):** (b) `blq_policy`(M1/M3/M4/M5)는 **생산 c 전무 = sponsor/bioanalytical 경계 입력**이라 producer 종결 대상이 아니다 — checklist ① 외부입력 GAP([[GAP-4]]/[[GAP-6]]/[[GAP-9]]/[[GAP-11]] 동형)과 함께 full-orchestrator 통합 시 외부 meta 1회 주입으로 해소. 미주입 시 M1/M5 분기로 BLQ_FLAG/LLOQ 컬럼 미생성(silent 격하 가능)은 통합 정산의 외부입력 규약으로 차단. ★ GAP-15는 **producer/detection 층 + input-contract 층** 둘을 가지며 *전자만* 종결(그 구분 유지).
- **status:** RESOLVED (effective producer/detection 배선·활성화 증명 완료 — slice 6; blq_policy 외부입력은 ① 통합 시 주입, by-design 잔여). [[GAP-28]](Q01 라우터=c0253 멘탈모델 교정) 연계.
- **영향 범위:** Phase 4 (fixture 주입 컨벤션), Phase 5 slice 6 (c0305/c0306 구현 + c0306→c0020/c0021 cross-layer 활성화 — 완료), 통합 (blq_policy 외부 주입 — 대기)

---

## [GAP-16] c0121 PIVOT COVARIATE_LAYOUT detection 오지정 (req_det=c0207이나 분기키 cov_layout는 c0380/c0381 생산)

> 기록: 2026-05-28 (Phase 4 사전 transform 입력계약 점검).

- **현상:** c0121(`PIVOT COVARIATE_LAYOUT`, L-2→L-3)의 `requires_detection_by=c0207`이고 precond/snippet은 `meta.get('cov_layout') == 'wide'`로 분기한다. 그러나 c0207(`CLASSIFY COVARIATE_LAYOUT` = A7)은 `meta['a7_state']`만 emit하고 **`cov_layout`은 생산하지 않는다**([[GAP-11]] 확정: c0207 output=a7_state 단일). `cov_layout` 생산자는 mess 층 **c0380(`DETECT COVARIATE_LAYOUT`)·c0381(`CLASSIFY COVARIATE_LAYOUT`, 둘 다 L-4→L-5, 미구현)**이다(c_units.json c0380 output: `meta['cov_layout']`∈{wide,long,none}).
- **★ D-S1 함의:** c0121을 실제로 trigger하는 detection은 c0381(cov_layout 산출)이지 c0207이 아니다. 현 req_det는 *axis 평가*(a7_state)는 보장하나 *c0121이 읽는 분기키*(cov_layout)는 보장하지 못한다 → 명목상 gate 충족, 실효 gate 미충족. cov_layout 부재 시 precond False → c0121 **silent no-op**(pivot 미수행; Lock 3 silent-error 우려).
- **[[GAP-11]] 관계:** GAP-11은 c0207이 baseline_covariates/tv_covariates 리스트를 미생산함을 다룬다([[GAP-3]] 소관). 본 항은 별개 키 `cov_layout`의 생산자가 c0380/c0381임을 명시 — c0207은 cov_layout도 미생산.
- **해결 후보:** (a) c0121.requires_detection_by를 c0381로 정정(spec 변경, 사용자 승인), (b) orchestrator가 c0380/c0381을 c0121 선행으로 배선(Phase 5).
- **★ 종결(Phase 5 slice 4 — 해결후보 (b) 채택):** c0380(`DETECT COVARIATE_LAYOUT`)·c0381(`CLASSIFY COVARIATE_LAYOUT`) 구현·배선 완료(`src/c_units/c0380_*`·`c0381_*`; orchestrator REGISTRY 4 엔트리). orchestrator가 c0380(→`meta['cov_layout']`)→c0381→c0207(→`c0207_ran`)→c0121 chain을 실행하면 **휴면 자산이던 c0121이 c0380 산출 `cov_layout='wide'`로 실제 wide→long pivot을 수행**함을 동적 테스트로 증명(`tests/test_strands.py::test_c0121_activation_chain_dynamic` — WT_V1,WT_V2 → long 4행). D-S1 cut-vertex도 `test_d_s1_covariate_cut_vertex_negative`(c0207_ran 부재 시 RuntimeError)로 고정. ⇒ **실효(effective) detection 결손 해소.**
- **잔여(별도 승인 — 해결후보 (a)):** `requires_detection_by` 필드 자체를 c0207→c0381로 *정정*하는 것은 spec 변경이라 미수행. c0121 precond은 **이중 의존**(`cov_layout` ← c0380, `c0207_passed` ← c0207)이라 단일 req_det 필드로 둘 다 표현 불가 — respec 시 (i) req_det=c0381(cov_layout 실효 detection)로 바꾸고 c0207_passed는 precond에 유지, 또는 (ii) dual-detector 표기 도입 중 택1을 사용자 승인 후 결정. c0121.py docstring "둘 다 미구현" 문구는 stale(현재 구현·배선됨) → 차기 spec 정산 시 동반 수정.
- **status:** RESOLVED (effective detection 배선·활성화 증명 완료 — slice 4; req_det 필드 respec만 spec 승인 대기). [[GAP-21]]/[[GAP-22]] 연계.
- **영향 범위:** Phase 5 slice 4 (c0380/c0381 구현 + orchestrator 배선 + 활성화 검증 — 완료), spec (req_det 정정 결정 — 승인 대기)

---

## [GAP-17] c0140 ASSIGN BASELINE_COVARIATE 시점 오류 (L-2→L-3서 미부여 TIME 참조) + c0023/c0140/c0141 groupby 키 불일치

> 기록: 2026-05-28 (Phase 4 사전 transform 입력계약 점검).

- **현상:** c0140(`ASSIGN BASELINE_COVARIATE`, L-2→L-3)의 python_snippet은 `baseline = df.loc[df['TIME']==0, ...]`로 **`TIME`**(NONMEM 컬럼)을 read한다. 그러나 `TIME`은 하류 **L-1→L-2의 c0019(`ASSIGN TIME`)**가 부여한다. forward 처리에서 L-2→L-3는 L-1→L-2보다 먼저 실행되므로 c0140 시점엔 `TIME`이 아직 없고 `time_value`(semantic)만 존재한다 → `df['TIME']` KeyError 또는 빈 필터(baseline 0행) 위험.
- **대조:** 형제 c0022(L-1→L-2 동일 srp_intent)는 TIME 미사용(SEX map / WT median). c0141(L-2→L-3 TIME_VARYING)도 `df.groupby('subject_id').ffill()`로 TIME 미사용. c0140만 TIME==0 baseline 필터를 쓴다.
- **부수(경미):** 동치쌍에서 groupby 키 불일치 — c0023(L-1→L-2)은 `'ID'`, c0140은 `subject_id`(baseline merge 키), c0141은 `subject_id`. ID(c0018 정수화)는 L-1→L-2 산출이므로 L-2→L-3 c(c0140/c0141)는 `subject_id`로 group해야 정합([[PRINCIPLE]]). c0023의 `'ID'` 사용은 L-1→L-2 시점엔 가용하나 c0141과 키가 어긋남.
- **해결 후보:** c0140 snippet의 `TIME`→`time_value`, 동치쌍 group 키 통일(spec snippet 변경, 사용자 승인). [[GAP-3]](cov 리스트 미생산)과 함께 c0140 구현 세션 전 정산.
- **status:** OPEN (layer 시점 + 키 불일치, 수정 안 함)
- **영향 범위:** Phase 4 (c0140 happy fixture: time_value 기반 baseline), spec (snippet 정정 결정)

---

## [GAP-18] c0019 ASSIGN TIME 입력계약 — time_value 생산자(상류 L-4→L-5 시간 정규화 mess c) 부재 (↔ GAP-7 동형)

> 기록: 2026-05-29 (Phase 4 c0019 구현 — 입력계약 점검).

- **현상:** c0019(`ASSIGN TIME`, L-1→L-2)는 `df['time_value']`(numeric, mess 정규화 완료)를 read해 NONMEM `TIME`을 부여한다(spec python_snippet: `pd.to_numeric(df['time_value'], errors='coerce')`). 그러나 `time_value`를 numeric으로 `output_schema_delta`에 생산하는 c는 **상류 L-4→L-5 시간 정규화 mess c**(c0311 `CONVERT TIME_FORMAT`, 미구현)이며 c-unit 구현 집합 어디에도 없다.
- **provenance(★ [[GAP-7]] 동형 — c0019도 동일 의존):** [[GAP-7]]은 A3 axis classifier c0203 측에서 동일한 `time_value`/`TIME` 컬럼 provenance(상류 시간 정규화 mess c가 생산)를 이미 기록했다. **c0019도 정확히 같은 상류 의존을 가진다** — c0203(detect)이 a3_state를 분류하고 c0019(transform)가 TIME을 부여하는데, 둘 다 선행 mess 층이 `time_value`를 numeric으로 정규화했음을 전제한다. `requires_detection_by=c0203`(D-S1 gate)는 a3_state 분류만 보장하지 *time_value 컬럼 산출*은 보장하지 않는다(detection gate ≠ 입력계약, [[GAP-15]] 선례와 동형).
- **영향:** c0019 단위테스트는 fixture가 `time_value`를 직접 주입하므로 green([[PRINCIPLE]] happy 입력=선행 출력). Phase 5에서 c0311(또는 동급 L-4→L-5 시간 정규화 c)→c0019 cross-layer 순서·출력 컬럼명(`time_value`) 일치를 점검해야 한다. `time_value` 부재 시 c0019는 precond 위반으로 fail(route_to_q=Q02)이며 silent no-op 아님(spec snippet의 notna assert와 동형 방어).
- **status:** OPEN (상류 컬럼 provenance, 기록 전용 — [[GAP-7]]과 동일 의존)
- **영향 범위:** Phase 5 (시간 정규화 mess c → c0019 배선 + time_value 컬럼 계약)

---

## [GAP-19] c0022 ASSIGN BASELINE_COVARIATE snippet(fillna median) ↔ vocab §A IMPUTE-제외 충돌 — 구현 레벨 override (c0140 동일 적용 예정)

> 기록: 2026-05-29 (Phase 4 c0022 구현 — 사용자 ★★★ 확정 결정).

- **현상:** spec c0022의 `python_snippet`(`df['WT'] = df['WT'].fillna(df['WT'].median())`)·`r_snippet`(`df$WT[is.na(df$WT)] <- median(df$WT, na.rm=TRUE)`)·`before_after_toy_example`(row3 `WT=. → 62.75`=median)이 **자의적 median imputation**을 수행한다. 이는 `spec/vocabulary.md §A 설계결정`(L49) "★ IMPUTE 제외: 임의 결측 보충은 silent error 원천. 결측은 DETECT → FILTER(FLAG) → 정책 문서 기반 처리. 자의적 IMPUTE 금지" **전역 규칙을 정면 위반**한다. (snippet의 범주형 코딩 `SEX.map({'M':0,'F':1})` 부분은 위반 아님 — fillna(median) IMPUTE 부분만 충돌.)
- **결정(사용자 ★★★ 확정):** 전역 vocab 규칙 > 개별 c snippet. median 대입 **미준수**. 결측 공변량은 명시 `NaN`으로 보존(= vocab "FLAG 후 정책 결정"의 구현)하고 `can_route_to_q` 내 **Q07**(missing covariate imputation policy)로 라우팅한다. 결측 없는 정상 공변량만 numeric ASSIGN. 계량약리 근거: 임의 median 대입은 결측 정보를 파괴해 규제 제출에서 방어 불가(예: 타크로리무스 WT 46% 결측).
- **구현(spec frozen, 구현 레벨 override):** spec `python_snippet`/`r_snippet`/`toy_example`은 **수정하지 않는다**(SSOT frozen). c0022 구현이 fillna를 생략하고 NaN-보존 + Q07 라우팅을 수행. **[[GAP-17]]**(c0140 TIME 시점 graceful fallback)·DECISION-D3·"c0019 산문 무시" 선례와 동형(spec 텍스트 유지, 구현이 전역 규칙 우선).
- **★ verbatim postcond STOP-check(사용자 재확인 항목):** `postcondition_predicate`는 토큰 단위 그대로 복사(test `TestC0022._check_postcond`, src docstring). 검증 결과 postcond는 `isinstance(np.nan, float)==True`로 **NaN-as-float를 통과**시켜 "결측 0"을 강제하지 않는다 → fillna 미준수가 postcond 위반이 **아니다**(STOP 조건 미발동). 방어적 `pd.to_numeric(errors='coerce')`가 결측을 `None`이 아닌 `np.nan`으로 만들어 술어의 유일한 실패 분기(non-numeric AND missing)를 회피.
- **schema 영향:** NaN-보존 + route(마커 컬럼 미추가)이므로 `output_schema_delta`("covariate columns → all numeric") **준수** — 별도 marker 컬럼 schema-초과 GAP은 발생하지 않는다(사용자 Option 1 선택).
- **silent-error 고정:** median/mean silent-fill 금지를 `test_adversarial.TestC0022Adversarial.test_missing_wt_not_median_filled`(★)·`test_unmapped_sex_not_fabricated`로 falsifiable 고정.
- **관계:** **[[GAP-3]]**(baseline_covariates 리스트 생산자 부재) 소비 c 동일. **c0140**(`ASSIGN BASELINE_COVARIATE`, L-2→L-3 형제, [[GAP-17]] 기록)도 동일 snippet 패턴 → 구현 시 **동일 override 적용 필요**. c0023(`ASSIGN TIME_VARYING_COVARIATE`)의 LOCF(`groupby('ID').ffill()`)는 vocab §A V10 **PROPAGATE**(forward-fill/carry-forward 정의 연산)이므로 본 충돌과 **무관**(자의적 IMPUTE 아님 — 관측값 within-ID 전파; residual leading 결측만 Q07).
- **status:** OPEN (구현 override 확정 — 사용자 ★★★; spec snippet frozen, 수정 안 함).
- **영향 범위:** Phase 4 (c0022 구현 완료), Phase 4 향후 (c0140 동일 override), Phase 6 (alias 병합 시 c0022/c0140 동일 처리 확인).

---

## [GAP-20] c0140 postcond(.first().notna()) ↔ GAP-19(IMPUTE 금지) 양립성 + c0022↔c0140 postcond 상이 비모순 (c0140/c0141 구현 확정)

> 기록: 2026-05-29 (Phase 4 c0140 구현 — 사용자 ★★★ 확정 STOP-check 판정 = 1번 진행).

- **배경:** c0140(`ASSIGN BASELINE_COVARIATE`, L-2→L-3) verbatim postcond는
  `all(df.groupby('subject_id')[cov].first().notna().all() for cov in meta.get('baseline_covariates', [])) if meta.get('a7_state') != 'NONE-REQUIRED' else True`.
  c0022(L-1→L-2 형제)의 postcond(`isinstance(x,numeric) or pd.isna(x)==False`)는 NaN-as-float를 통과시켜
  "결측 0"을 강제하지 않았으나([[GAP-19]]), c0140 postcond는 `.notna()`로 NaN을 명시 거부한다 → 표면상
  GAP-19(median 금지, 결측 NaN 보존)와 충돌 우려(STOP-check 대상).

- **(a) STOP-check 판정 — STOP 미발동(사용자 ★★★ 확정):** `GroupBy.first()`는 skipna=True
  (검증: `pd.DataFrame({'g':[1,1],'v':[nan,5.0]}).groupby('g')['v'].first()==[5.0]`)이므로 postcond는
  "각 subject가 baseline 공변량당 **≥1 non-null**"을 요구할 뿐 "전 행 notna(결측0)"가 **아니다.** 따라서
  자의적 median IMPUTE를 강요하지 않는다. 충족 기전은 **관측 baseline의 within-subject PROPAGATE**(존재
  baseline 값을 그 subject 전 행으로 carry — vocab §A V10 PROPAGATE, c0023 ffill과 동류, 자의적 IMPUTE
  아님; cross-subject bleed 금지). baseline이 진짜 전무한 subject만 Q07. verbatim postcond(`_check_postcond`)는
  c0022/c0023 선례대로 **happy/edge에만 assert**(trap 출력엔 미호출). → STOP 미발동, GAP-19 override(결측
  baseline NaN 보존 + Q07) 그대로 구현. baseline-row 식별(time==0, [[GAP-17]] fallback)은 postcond와
  **독립** 테스트(spurious pass 방지: `test_baseline_identified_by_time_not_row_order`). **Phase 9-A(adversarial)
  에서 "postcond too strict" 오판 방어 근거.**

- **(b) c0022(NaN 보존) ↔ c0140(PROPAGATE) postcond 상이 = 비모순(원칙 family):** 두 c는 같은
  srp_intent(`ASSIGN BASELINE_COVARIATE`)이나 postcond가 다르다 — c0022는 NaN-tolerant(결측 보존 허용),
  c0140은 PROPAGATE 후 subject당 ≥1 non-null 요구. 이는 **layer 차이**(c0022 L-1→L-2 numeric 코딩 /
  c0140 L-2→L-3 baseline 부착)에 따른 정당한 분화이며 **둘 다 [[GAP-19]](median 금지) 준수 — 동일 원칙
  family**다(자의적 IMPUTE 금지 → 결측은 Q07). 모순 아님. **Phase 6:** in/out schema delta·layer가 달라
  semantic equivalence(Lock 4) **alias 아님**(별도 c 유지). **Phase 7:** decision-tree에서 N6 covariate
  attachment 같은 **family로 취급**(skeleton_hook 계열 동일).

- **status:** RESOLVED (c0140/c0141 구현 완료, 541 green; STOP 미발동 확정 — 사용자 ★★★).
- **영향 범위:** Phase 9-A (adversarial postcond too-strict 오판 방어), Phase 6 (c0022↔c0140 alias 아님),
  Phase 7 (covariate family node 매핑). [[GAP-17]]/[[GAP-19]]/[[GAP-3]] 연계.

---

## [GAP-21] c0121 PIVOT COVARIATE_LAYOUT — snippet(plain melt) ↔ postcond/toy(refined) 충돌 + covariate_columns 생산자 부재

> 기록: 2026-05-29 (Phase 4 c0121 구현 — 사용자 ★★★ 확정: 출력 shape = REFINED, postcond 우선).

- **(A) snippet ↔ postcond/toy 출력 shape 충돌(구현 override, [[GAP-19]] 선례 동형):** c0121 spec 엔트리가 내부 충돌한다.
  - `python_snippet`/`r_snippet`: **plain melt**(`var_name='visit', value_name='cov_value'`) → 단일 `cov_value` 값 컬럼.
  - `before_after_toy_example` + verbatim `postcondition_predicate`: **refined** wide→long(WT_V1,WT_V2 → 'visit' 컬럼 + 'WT' 값 컬럼). postcond는 plural `meta['covariate_columns']`를 순회하며 `df[col]`(col=base명)을 요구한다.
  - **판정(사용자 ★★★):** SSOT 위계 **postcond > snippet/toy**. plain melt는 단일 `cov_value`만 만들어 plural `covariate_columns`(예: ['WT','AGE'])를 충족 못함(multi-cov가 한 컬럼에 섞임) → postcond 위반. 따라서 snippet **미준수**, refined 구현. spec snippet은 **frozen 유지**(수정 없음), 구현이 postcond 우선. c0019(산문 무시, postcond 최상위)·[[GAP-19]](c0022 fillna snippet 미준수)·DECISION-D3 선례 동형. (차이: c0019 snippet은 postcond 안 어겨 따랐고, c0121 snippet은 어겨 못 따름.)
  - **구현:** `pd.wide_to_long(df, stubnames=bases, i=id_cols, j='visit', sep='_', suffix='.+')` + id_cols+visit 사전식 정렬(deterministic). multi-cov는 별도 컬럼 보존. silent-error 고정: `test_adversarial.TestC0121Adversarial.test_value_column_named_by_base_not_cov_value`(①)·`test_multi_covariate_not_mixed`(③)·`test_pivot_no_row_loss_or_dup`(무결성).
- **(B) `meta['covariate_columns']` 생산자 부재([[GAP-3]] 동형):** postcond가 순회하는 `meta['covariate_columns']`를 `output_schema_delta`로 생성하는 c가 c-unit 집합 어디에도 없다(grep: c0121 postcond에만 등장). [[GAP-3]](baseline_covariates/tv_covariates 생산자 부재)와 동형 — 어느 층도 생산하지 않는 키. 단위테스트는 fixture meta로 직접 주입. silent no-op 방지를 위해 부재 시 df fallback(`{base}_{visit}`에서 base가 `_COVARIATE_COLS`면 채택; c0207/c0140 `_covariate_columns` 동형). Phase 5 일괄 정산.
- **(C) cov_layout 분기키 생산자 = c0380/c0381([[GAP-16]] 참조, 중복 금지):** 분기키 `meta['cov_layout']`(∈{wide,long,none})는 c0207(a7_state만 emit)이 아니라 mess층 c0380/c0381(미구현)이 생산 — 이미 [[GAP-16]]에 기록. cov_layout 부재 시 silent no-op 금지(Lock 3): success=False + route_to_q=None(can_route_to_q=[] → scope-out None, Q 날조 금지; [[GAP-5]]/[[GAP-8]]/[[GAP-13]] 선례). `test_trap_cov_layout_missing`·`test_cov_layout_missing_not_silent_noop`로 고정.
- **★ 종결(Phase 5 slice 4):** (C) 분기키 `cov_layout` 생산자 c0380/c0381 **구현·배선 완료** → c0121이 외부 fixture 주입 없이 orchestrator chain(c0380→…→c0121)으로 실제 pivot(`test_c0121_activation_chain_dynamic`). (A) refined 구현은 Phase 4 완료 유지. (B) `meta['covariate_columns']` 생산자는 여전히 부재 → c0121 df fallback(`{base}_{visit}`에서 base∈`_COVARIATE_COLS`)으로 처리(GAP-3 family 잔여-by-design; 활성화 테스트가 WT_V1/WT_V2 fallback 경로를 green으로 고정). [[GAP-16]] 동반 종결.
- **status:** RESOLVED ((A) Phase 4 / (C) slice 4 배선·활성화 완료; (B) covariate_columns df fallback 잔여 — spec 신설은 범위 밖). 전체 테스트 704 passed.
- **영향 범위:** Phase 4 (c0121 구현 완료 — refined), Phase 5 slice 4 (cov_layout 생산자 c0380/c0381 배선 + 활성화 — 완료), Phase 7/8 (HTML snippet 렌더 시 plain-melt snippet ↔ refined 구현 불일치 주의 — [[GAP-14]] 노드 라벨 매핑 동류). [[GAP-16]]/[[GAP-3]]/[[GAP-19]] 연계.

---

## [GAP-22] c0015 ASSIGN ADDL — a4_state→Q14 분기가 req_det(c0010) 밖 detector(c0204) 산출 키 의존 (detection 명목≠실효)

> 기록: 2026-05-29 (Phase 5 readiness 사전점검 — detection 명목/실효 전수 스캔에서 신규 발견).

- **현상:** c0015(`ASSIGN ADDL`, L-1→L-2) 구현(`src/c_units/c0015_assign_addl.py` L36)은 `if meta.get("a4_state") == "ADDL-ACTUAL-CONFLICT": return {"success": False, "route_to_q": "Q14", ...}`로 **a4_state에 분기**한다. 그러나 c0015의 `requires_detection_by=c0010`(`ASSIGN EVID`)은 EVID/df-컬럼만 보장하고 **a4_state를 생산·보장하지 않는다.** a4_state 생산자는 **c0204(A4 axis classifier, 구현됨)**다.
- **★ D-S1 함의(명목≠실효):** c0015의 Q14(ADDL-ACTUAL-CONFLICT) 게이트를 실제로 trigger하는 detection은 c0204(a4_state 산출)이지 선언 req_det c0010이 아니다. 현 req_det는 *EVID 부여*는 보장하나 *c0015가 읽는 분기키*(a4_state)는 보장하지 못한다 → 명목 gate 충족, 실효 gate 미충족. [[GAP-16]](c0121 cov_layout)과 동형이며, transform c가 **교차축(A4) state**를 읽는다는 점에서 [[GAP-10]](c0206가 a0_state를 교차축 read)과도 동류.
- **실패양상:** orchestrator가 c0204 미선행 경로로 c0015 도달 시 `meta.get("a4_state")`=None → `None == "ADDL-ACTUAL-CONFLICT"`=False → **Q14 silent 미발화**, implied/actual dose 충돌이 있어도 ADDL 압축을 강행(Lock 3 silent-error 우려).
- **완화(★ GAP-16보다 저위험):** (1) 실효 생산자 c0204가 **이미 구현됨**(c0380/c0381 미구현인 [[GAP-16]]과 대조). (2) strand 순서상 axis classifier(L-3→L-4)는 L-1→L-2 transform보다 항상 선행 → strand-order-safe. 위험은 orchestrator가 strand 순서를 벗어나 c0204를 건너뛸 때만 발생.
- **해결 후보:** (a) c0015 구현 유지 + **Phase 5 orchestrator가 axis-classifier(c0200–c0210) ≺ L-1→L-2 transform 순서를 불변식으로 보장**(권고). (b) c0015.requires_detection_by를 a4 detector 동반 형태로 respec(spec 변경, 사용자 승인). 본 단계는 기록만(코드·spec 무수정).
- **status:** OPEN (detection 명목≠실효, 기록 전용 — 수정 안 함).
- **영향 범위:** Phase 5 (orchestrator axis≺transform 순서 불변식 + c0015 a4_state chain 보장). [[GAP-16]]/[[GAP-10]]/[[GAP-5]] 연계.

---

## [GAP-23] 문서/경로 drift — CLAUDE.md layout(refs/·spec/anchors.json) ↔ 실제 파일 위치(root) 불일치 (readiness)

> 기록: 2026-05-29 (slice 1 사후 readiness — 파일 위치/경로 정합 스캔에서 발견).

- **현상:** `CLAUDE.md §디렉토리 layout` 및 `§Canonical Reference`가 선언한 경로와 실제 파일 위치가 어긋난다.
  - 선언: `refs/ universe_sm.md  frozen_universe_v4.1.md  frozen_universe_v4.2.md`, `spec/ anchors.json`.
  - 실제(glob 확인): `universe_sm.md`·`frozen_universe_v4_1.md`·`frozen_universe_v4_2.md`·`anchors.json`이 전부 repo **root**. `refs/` 하위엔 해당 파일 0건(`**/*.{md,json,py,html}` glob상 refs/ 항목 부재). 파일명 drift: CLAUDE.md `v4.1`/`v4.2`(dot) ↔ 실제 `v4_1`/`v4_2`(underscore).
- **★ 코드 정합(active bug 아님 — latent):** 기존 코드는 실제(root)와 일치하게 resolve한다 — `verify_phase3.py:11`·`generate_sc.py:12`가 `ROOT / "anchors.json"`(root)로 로드. spec/*.json은 전부 `ROOT / "spec" / ...`(정상). `universe_sm.md`·`frozen_*`는 **어떤 코드도 경로 로드하지 않음**(docstring 텍스트 인용 "universe_sm §..."만) → 현재 깨지는 코드 없음.
- **잠재 위험(latent path-resolution):** CLAUDE.md의 *문서화된* layout(`spec/anchors.json`, `refs/universe_sm.md`)을 신뢰하는 향후 c/도구/Phase가 `ROOT/"spec"/"anchors.json"` 또는 `ROOT/"refs"/...`로 경로를 구성하면 FileNotFoundError. doc과 실제·기존코드가 어긋나 신규 작업자가 doc을 따르면 오류.
- **해결 후보(Phase 5b 정산):** (a) CLAUDE.md layout/Canonical Reference를 실제 root 위치 + underscore 파일명으로 정정, 또는 (b) 파일을 refs//spec/로 이동해 doc과 일치(이동 시 `verify_phase3.py:11`·`generate_sc.py:12`의 `ROOT/"anchors.json"`도 동반 수정). 둘 다 변경 → 사용자 승인. 본 단계는 기록만.
- **status:** OPEN (문서/경로 drift, 기록 전용 — 수정 안 함).
- **영향 범위:** Phase 5b (경로/문서 정합). [[GAP-24]]와 동반 기록(slice 1 readiness loose findings).

---

## [GAP-24] c0341 global ffill의 cross-subject(행) bleed — pre-subject 전파 latent 위험 + verbatim postcond(global shift) ↔ subject-scope fill 충돌 (slice 1)

> 기록: 2026-05-29 (Phase 5 slice 1 MERGED_CELL 사후 — cross-subject 전파 위험 점검).

- **현상:** c0341(`PROPAGATE MERGED_CELL`, L-4->L-5)은 `df.ffill()`(전역 수직 forward-fill, groupby 無)를 수행한다. L-4->L-5는 forward 처리 최심부로 **subject(ID) 미확립** 시점이다(ID는 하류 c0018 `ASSIGN ID`, L-1->L-2 산출 — [[GAP-17]]). 게다가 raw 시트에서 subject_id 자체가 병합 셀일 수 있어(= c0341이 채우는 대상) groupby 키가 신뢰 불가 → **global ffill은 이 layer의 올바른 유일 선택**(universe_sm §6 "병합 잔존(forward-fill 필요)"; vocab §A V10 PROPAGATE — "PROPAGATE MERGED_CELL"은 BY 수식어 無=global, cf. "PROPAGATE BASELINE_COVARIATE BY WITHIN_ID"). [[PRINCIPLE §6 전파]] 참조.
- **★ 위험(cross-subject row bleed):** 행 순서가 subj1…→subj2…인데 subj2 첫 행(예: dosing 행/공변량)이 결측이면 global ffill이 **subj1의 마지막 값을 subj2로 상속** → 타 subject 값 오염. 이는 c0023/c0141이 명문으로 금지한 바로 그 silent-error다("groupby 없는 ffill은 타 subject 값 오염 silent-error" — c0023 L23·c0141 L24; c0140 within-subject PROPAGATE도 cross-subject bleed 금지 — [[GAP-20]]). c0341만 (pre-subject라) groupless ffill을 쓰는 유일 지점.
- **★ 결함 아님 / 위험임(memory 정합):** c0341 자체는 버그 아님(layer 제약상 올바름; slice 1 memo "cross-subject/row propagation is spec-defined behavior, NOT a bug"). 단 그 부작용이 **NONMEM-ready 출력까지 살아남으면** 규제 제출 데이터 오염. 기존 trap은 cross-**column**/구조/역방향/no-op만 커버(cross-**subject 행** bleed 미커버) → 본 위험은 미고정 상태였다.
- **★ verbatim postcond(global shift) ↔ subject-scope fill 충돌:** c0341 `postcondition_predicate`(`not meta.get('has_merged_cells', False) or not any((df[c].isna() & df[c].shift().notna()).any() for c in df.columns)`)의 `df[c].shift()`는 **전역 shift**다. global ffill과는 정합(잔존 gap 0 검증)이나, cross-subject bleed를 c0341에서 막으려 **subject-scope fill**로 바꾸면 각 subject의 leading 결측 직전 행이 *이전 subject*의 notna 값과 인접 → `isna & shift().notna()`=True → postcond를 **거짓 실패**시킨다. 즉 verbatim postcond가 c0341을 global 거동에 **고정**한다(postcond frozen, 토큰 변경 금지 — Hallucination 차단 #1). ⇒ 수정 지점은 c0341이 아니라 **하류**여야 한다.
- **완화(mitigation, 제안):** subject 확립(c0018) **후** 하류에 **subject-boundary VERIFY cut-vertex**를 두어 NONMEM-ready 출력 *전* 의무 통과(D-S1 cut-vertex 패턴). 검사 = 어떤 컬럼 값도 subject 경계를 넘어 채워지지 않음(within-subject 일관). ★ 현 c-unit 집합엔 *subject-boundary fill-integrity VERIFY 부재*(c0209는 A9 분류기로 within-ID time 단조만 검사) → **신규 하류 VERIFY 제안**(Phase 5/7). ★ Q-route: c0341은 `can_route_to_q=[]`라 자체 emit 불가 → Q-route는 하류 VERIFY 책임. **정확히 들어맞는 기존 q_code 부재**(Q07=covariate-imputation, Q05=multi-study ID harmonization, Q08=dose MISSING-NO-POLICY, Q15X=catch-all) → 특정 Q는 **TBD**(날조 금지, 후보만 기록; 확정은 mitigation 설계 시 사용자 승인 — [[GAP-5]]/[[GAP-8]] "scope-out None" 선례).
- **status:** OPEN (latent 위험 + postcond 충돌 + 하류 VERIFY 제안, 기록 전용 — 수정 안 함).
- **영향 범위:** Phase 5 (c0018 후 subject-boundary VERIFY 배선), Phase 7 (D-S4 conditional edge: VERIFY fail→Q), NONMEM-ready 출력 게이트. [[GAP-17]]/[[GAP-19]]/[[GAP-20]]/[[PRINCIPLE §6 전파]] 연계. test_adversarial xfail로 known-risk 고정(본 작업).

---

## [PRINCIPLE §6 전파] PROPAGATE scope: pre-subject global ffill vs post-subject groupby(subject)

> 기록: 2026-05-29 (slice 1 MERGED_CELL — [[GAP-24]]에서 일반화). 이후 PROPAGATE형 슬라이스 적용 기준.

- **원칙:** forward-fill/carry-forward(vocab §A V10 PROPAGATE)의 **scope**는 subject 확립 시점으로 갈린다.
  - **pre-subject(syntactic):** subject 키(ID/subject_id)가 아직 신뢰 불가한 L-4->L-5 mess 층에서는 **groupless global ffill**만 가능·정당. 현 유일 사례 = c0341(`PROPAGATE MERGED_CELL`). 어휘상 "PROPAGATE {NOUN}"(BY 수식어 無).
  - **post-subject(longitudinal):** subject 키 확립(c0018 ID, L-1->L-2) 이후 모든 행-전파는 **`groupby(subject-key).ffill()` 의무**. 사례 = c0023(`'ID'`)·c0141/c0140(`'subject_id'`). 어휘상 "PROPAGATE {NOUN} BY WITHIN_ID"(vocab §A V10 전형 pairing). groupby 없는 ffill = cross-subject 오염 = silent-error(Lock 3 위반).
- **경계·근거:** universe_sm §6는 "forward-fill 필요"만 명시하고 scope는 침묵 → scope는 구현 결정. vocab §A V10 SRP 경계 "전파 대상·방향 결정은 DETECT 소관" — 전파 *scope*도 DETECT 책임이나 c0340은 존재만 감지(subject 경계 미감지, pre-subject라 불가) ⇒ pre-subject 전파의 scope 부재가 [[GAP-24]] cross-subject bleed의 구조적 원인.
- **향후 PROPAGATE형 슬라이스 적용 기준:** 새 PROPAGATE c는 ① subject 확립 *이전* AND subject 키 컬럼이 신뢰 불가일 때만 groupless global ffill 허용(+ [[GAP-24]] 식 하류 subject-boundary VERIFY 동반), ② 그 외(키 가용)엔 반드시 `groupby(subject-key)`. groupby 키는 layer별 정합([[GAP-17]]: L-1->L-2 'ID' / L-2->L-3 'subject_id'). PROPAGATE는 IMPUTE 아님([[GAP-19]] — 관측값 전파, 자의적 보충 금지).
- **status:** 기록(원칙). [[GAP-24]]/[[GAP-17]]/[[GAP-19]]/[[GAP-20]] 근거.

---

## [DECISIONS] Phase 4 범위 확정 (사용자 결정 로그)

> 기록: 2026-05-29. 사용자 통제용 결정 로그. GAP(불일치 기록)와 달리 본 섹션은 *결정* 고정 — 변경은 사용자 승인 후에만.

### [DECISION-D1] c0022/c0023(L-1→L-2)·c0140/c0141(L-2→L-3) 양 layer 모두 구현 유지.
spec이 양 layer에 covariate 부여 책임을 명시하므로 Phase 4는 spec대로. Phase 6 alias 병합은 시각화 단계 결정(별도).

### [DECISION-D2] 보류 30개 해금 위한 mess detect/verify 발주는 Phase 4 범위 밖.
Phase 4는 "즉시 빌드 가능 8개 + 기존 axis 11개 + transform 9개 = 28개"로 완결. 나머지 30개는 Phase 5에서 mess 층(c0306/c0341/c0375/c0380/c0381 등) 발주 + chain wiring과 함께 진행.

### [DECISION-D3] GAP-15/16/17 처리:
- **GAP-15(BLQ chain):** 기록 유지, fixture 주입으로 단위 green. Phase 5 정산.
- **GAP-16(c0121 req_det):** 기록 유지, fixture `cov_layout` 주입. Phase 5 정산.
- **GAP-17(c0140 TIME 시점):** ★구현 시 graceful fallback — `df['TIME']==0` 대신 `df.get('TIME')`이 None이면 `df['time_value']==0`로 fallback. groupby도 `'subject_id'` 우선, 없으면 `'ID'`. spec snippet은 frozen 유지(수정 없음), 구현 레벨에서 cross-layer 시점 불확실성 방어. c0015→c0016 dose_interval([[GAP-2]]) 선례와 동형.

---

## [GAP-25] [RENDER/LOCK6] Phase 8 렌더 성능 게이트(DoD #6-5) — naive FAIL / collapse-by-default PASS, Lock 6 유지

> 기록: 2026-05-30 (Phase 8 pre-spike 측정). ★ c-unit chain 계약(GAP-1~24)과 테마가 다른 렌더/Lock-6 영역. 번호 충돌 방지로 현 최대(24) 다음에 둠.

- **판정:** Cytoscape.js+dagre로 5000 strand 표현 시 **개별 노드 naive 렌더는 dagre 레이아웃 단독이 게이트(10s) 초과 → FAIL**, 그러나 **D-S3 경로표현(backbone collapse-by-default + virtual culling + 증분 expand)으로는 PASS**. ⇒ Lock 6(Cytoscape.js+dagre) 스택 유지. 병목 = dagre layout(노드수 초선형), render 플래그로 미해소.
- **cite-verify ledger(출처 구분):**
  - **[코드 검증 — render/spike_interaction.html, 재현가능]:** collapsed 동시표시 **248 노드** = Σ COLLAPSE_W(236)+terminal 6+bundle 6 (L4952·L4965–5018, COLLAPSE_W 주석 "합 236"); strand 방문 **cell 236/236**(Σ COLLAPSE_W, coverageOK=모든 non-stage0 cell ≥1 incoming); naive 참조 t_layout **13,240ms** = renderComparison REF(L5092).
  - **[사용자 라이브 브라우저 측정 — 같은 기기 2026-05-30, falsifiable]:** naive t_layout 13,240ms·optimized 12,808ms → FAIL(>10s); collapsed t_layout 676ms·t_total 727ms → PASS; 증분 expand 6ms. (REF의 optimized 상수 17,633ms는 placeholder, 라이브 우선.)
  - **[★ Phase 8 실데이터 재측정 대상]:** 248/236은 spike **synthetic backbone**(COLLAPSE_W mock 폭 Σ236)에서 나온 값 — 메커니즘 확장성만 증명. 실 axis-state cell은 anchors.json 11축 **101 state**이고 **decision_tree.json 부재**(Phase 7 미완). Phase 7이 실 tree 생성 시 재측정해 본 수치 갱신.
  - **[✅ Phase 7 실측 갱신 — 2026-06-03, decision_tree.json 생성]:** 실 backbone 노드수 = **collapsed 100**(8 N + 11 axis collapsed + 5+19 terminal + 57 c) / **expanded worst 190**(axis 101 state 펼침). synthetic 248/236을 대체. 둘 다 **≪ 5000**이고 dagre sub-second 영역 → node-count 측면 **PASS 확정**(dagre ms 라이브 측정은 Phase 8 잔존). 다발 압축(step 2 하류)·virtual culling은 미적용(bundles=[]) — 적용 시 collapsed는 더 감소. 측정 근거: `spec/decision_tree.json` stats.gap25_remeasure + `tests/test_decision_tree.py::test_gap25_node_count_remeasure`.
  - **[✅✅ Phase 8 dagre 라이브 ms 확정 — 2026-06-03, headless Chrome(번들 바이너리 + Node CDP, no-install) falsifiable 측정]:** 실 tree `render/index.html`(build_html.py 생성, collapsed **101 노드** = 100 canonical + 1 합성 stage)를 `/Applications/Google Chrome.app --headless=new`로 로드·자가측정 → **dagre t_layout = 61–64ms · t_total = 120–122ms ≪ 10,000ms 게이트 = PASS**(여유 ~82×; 3회 재현 일관). 증분 expand(A5 +15 state → 116 노드) **62ms**. dagreOK·cy 렌더(canvas 3)·JS 예외 0. 자가측정 배지 `window.__PERF__`가 화면 표기(GAP-25 정본 methodology — 기존 사용자 라이브 676ms 방식의 실 tree 연장; 실 backbone 101 노드라 spike synthetic 248보다 빠름). **⇒ node-count(100/190)에 더해 dagre 라이브 ms까지 PASS 확정 — GAP-25 완전 해소.**
- **영향(Phase 8 필수 설계 제약):** collapse-by-default 동시표시 노드 상한 + virtual culling(멤버 미생성) + 증분 expand(부분 dagre)는 `render/build_html.py`·`index.html` 필수 제약. 정본 시드=render/spike_interaction.html. ★ Phase 8 본 렌더 라이브러리 로딩 정본 = **inline**(spike 방식); slice1의 CDN은 부분점검용.
- **status:** ✅ **RESOLVED (완전)** — naive FAIL / collapsed PASS, Lock 6 유지. node-count 실측(100/190 ≪5000) + **Phase 8 dagre 라이브 ms 실측(t_layout 64ms·t_total 122ms ≪ 10s, headless falsifiable)** 둘 다 PASS. 잔여 측정 없음. [[GAP-33]] 연계.
- **영향 범위:** ~~Phase 8(렌더 — collapse/cull/증분 필수, ms 라이브)~~ ✅완료, ~~Phase 7(decision_tree.json 생성 후 실측)~~ ✅완료. CLAUDE.md DoD #6 정밀화 연계.

---

## [GAP-26] Phase 5 slice 2 발주 멘탈모델 ↔ spec 불일치 — Q02/Q12 라우터는 c0019가 아니라 c0251(ROUTE)

> 기록: 2026-05-31 (Phase 5 slice 2 TIME family 착수 cite-verify). 기록 전용(spec·코드 무수정; slice 2 검증목표 재정의로 반영).

- **현상(발주 가정):** slice 2 발주문은 "이미 구현된 c0019(ASSIGN TIME)가 Q02/Q12로 라우팅되는 strand"를 전제하고 검증목표를 "c0019가 conditional edge를 타고 Q-terminal 도달"로 설정했다.
- **★ falsifiable 반증(strands.json 5000):** Q02/Q12 strand는 785개(Q02 388 + Q12 397)이고 **전부 c0251(ROUTE TIME_FORMAT)을 last-c로 두고 terminal=QUARANTINE에 도달**한다(`c_sequence[-1]=="c0251"` 100%). `c0019.can_route_to_q=[Q02,Q12]`는 **best-strand 0개**에 등장한다(c0019는 L-1→L-2이고, Q02/Q12 strand는 L-3→L-4 축에서 c0203→c0251로 이미 라우팅되어 c0019 도달 전 종착). 즉 c0019의 Q-route는 어떤 strand에도 없는 **fail-branch conditional edge = Phase 7(D-S4) 재구성 소관**이며 Phase 5 strand로는 검증 불가.
- **실제 라우팅 메커니즘(SSOT):** c0203(DETECT TIME_FORMAT, a3_state 생산) → c0251(ROUTE, reqdet=c0203) → **AMBIGUOUS→Q02 / UNRECOVERABLE→Q12**([[GAP-7]] 매핑 + q_codes trigger 정합). c0213(VERIFY TIME_ANCHOR)은 3616 strand·전 Q02/Q12 strand에 선행.
- **연계 — c0251 snippet 산문 무시([[GAP-7]] 동형):** c0251의 `python_snippet`은 "UNRECOVERABLE→INVALID"라 적었으나 `can_route_to_q=[Q02,Q12]`·strands 397 Q12·postcond(`routing_decision in ['Q02','Q12','INVALID']`이 Q12 허용)에 따라 구현은 UNRECOVERABLE→**Q12**다(spec snippet frozen, 구현이 postcond/SSOT 우선 — c0019·c0203·[[GAP-19]] '산문 무시' 선례). 이는 postcond override가 아님(Q12가 postcond 집합 내).
- **검증목표 재정의(slice 2 채택):** "c0251이 a3_state(c0203 생산)를 → Q02(AMBIGUOUS)/Q12(UNRECOVERABLE)로 정확히 라우팅하고, Q02·Q12 고립 Q-terminal 0(둘 다 c0251 incoming ≥1)임을 orchestrator·strand로 검증"(tests/test_strands.py: route_ambiguous/unrecoverable_dynamic·q02_q12_routed_by_c0251_last; test_coverage.py C3; test_skeleton.py D-S4).
- **orchestrator 함의:** slice 1 orchestrator는 terminal=None·ROUTE 미처리였다. slice 2가 `kind=="route"` 처리 + terminal=QUARANTINE/q_code 도출 + D-S1 route 확장을 신설(src/orchestrator.py) — 핵심목표를 가능케 한 실제 작업.
- **status:** RESOLVED(기록 + slice 2 검증목표 재정의 반영). c0019 Q-route conditional edge는 Phase 7 D-S4 재구성으로 이월.
- **영향 범위:** Phase 5 slice 2(검증목표·orchestrator), Phase 7(c0019/c0311/c0315/c0213 fail→Q conditional edge 재구성·고립 Q-terminal 점검). [[GAP-7]]/[[GAP-18]] 연계.

---

## [GAP-27] Phase 5 slice 3 — c0313 NORMALIZE TIMEZONE postcond vacuous-default(silent no-op) + FORMAT↔TIMEZONE 정렬 상호작용

> 기록: 2026-05-31 (Phase 5 slice 3 TIMEZONE family 구현). 기록 전용(spec·snippet 무수정; postcond override 아님 — 구현·trap·orchestrator로 enforce).

- **(A) vacuous-default postcond(silent no-op 위험, [[GAP-3]] 동형):** c0313 verbatim `postcondition_predicate = meta.get('tz_normalized', True)`는 **default=True**라 `tz_normalized`를 한 번도 set하지 않는 no-op도 vacuously 통과한다(Lock 3 silent-error). 형제 c0315(`… else True`)와 동형 vacuity이나, c0315의 vacuity는 *대상 컬럼 부재* 시에만 발동하는 반면 c0313은 *정규화가 필요한 경우에도* 무조건 True라 더 약하다.
- **★ 해소(spec frozen, override 아님 — [[GAP-19]]/[[GAP-21]]/[[GAP-26]] 선례):** postcond 토큰 1자도 바꾸지 않고(Hallucination 차단 #1) 구현·test가 실제 의미를 강제한다:
  ① tz 토큰 ≥1 → 모든 time_value를 단일 target tz로 실제 변환 후에만 `meta['tz_normalized']=True`. ② 정규화 대상 부재(토큰 0) → 정당 idempotent(flag set, 부재≠silent — c0311 edge 'already-numeric' 동형). ③ requires_detection_by(c0312) 산출물 `meta['tz_issues']` 부재 → `success=False`·`route_to_q=None`(can_route_to_q=[] → **Q 날조 금지**, [[GAP-21]](C) 선례)·flag 미설정. ④ tz 토큰 有 + 시각 파싱 불가 → 부분 변환 silent 통과 금지(`success=False`).
  - 고정 test: `TestC0313.test_trap`(명시 `tz_normalized is True` + 단일 tz 통일 + 값 정확)·`test_tz_issues_missing_not_silent_noop`; `TestC0313Adversarial.test_vacuous_postcond_not_bypassed_when_detection_missing`/`test_silent_noop_caught`/`test_unparseable_time_with_tz_not_partial`; orchestrator `test_timezone_normalize_chain_dynamic`(silent no-op 0).
- **(B) FORMAT↔TIMEZONE 정렬 상호작용(Phase 7 이월):** c0313(TIMEZONE)은 c0311(CONVERT TIME_FORMAT)과 **55 strand 공존**하고 canonical c_id order(D-S2)상 c0311(→numeric)이 c0313보다 **먼저** 온다. spec embedded-tz-token 모델(`"08:00 KST"`)에서 c0311이 numeric으로 변환하면 tz 토큰이 소실되어 c0313이 읽을 대상이 사라진다 → FORMAT vs TIMEZONE이 진정 commutative가 아닐 수 있음(D-S2 정규형 가정과 잠재 충돌). slice 3는 **TIMEZONE 단독**(`run_strand(["c0312","c0313"])`)으로 검증; 결합 chain 정합·순서는 Phase 7 conditional-edge/commutativity 재검토로 이월. (TIME_ANCHOR c0314와는 48 strand 공존하나 c0313이 먼저 — 충돌 없음.)
- **(C) 결정적 tz 모델(Lock 3 determinism):** `_TZ_OFFSETS`(UTC/GMT/Z 0, KST/JST +9, EST −5, EDT −4, CST −6, CDT −5, MST −7, PST −8, PDT −7, CET +1, CEST +2, BST +1, IST +5.5) offset 차분 + mod24 wrap. target tz = `meta['tz_target']`(유효 시) > tokens에 'UTC' 존재 시 'UTC' > `sorted(tokens)[0]`. c0312/c0313이 `_extract_tz`·`_TZ_OFFSETS`를 공유(known-set 토큰만 인식 — false positive 차단).
- **status:** RESOLVED(slice 3 — (A)/(C) enforce 완료; (B) Phase 7 이월). c0312/c0313 freq 532·can_route_to_q=[] → C3 N/A·D-S4 무기여(고립 Q-terminal 0).
- **영향 범위:** Phase 5 slice 3(검증목표·orchestrator REGISTRY 확장), Phase 7(FORMAT↔TIMEZONE 순서·commutativity 재검토; c0313은 can_route_to_q=[]라 conditional Q-edge 무). [[GAP-3]]/[[GAP-18]]/[[GAP-21]] 연계.

---

## [GAP-28] Phase 5 slice 6 발주 멘탈모델 ↔ spec — Q01 라우터는 c0306이 아니라 c0253(ROUTE) ([[GAP-26]] 동형)

> 기록: 2026-06-01 (Phase 5 slice 6 BLQ_TOKEN family 착수 cite-verify). 기록 전용(spec·코드 무수정; slice 6 검증목표 반영).

- **현상(발주 가정):** slice 6 발주문은 BLQ family를 "c0305(DETECT)/c0306(NORMALIZE)"로 지목하고 "이 family의 Q-code(Q01)가 strand에서 trigger"를 검증목표로 두었다. c0306.can_route_to_q=[Q01]이 있어 c0306이 Q01 라우터로 읽힐 수 있다.
- **★ falsifiable 반증(strands.json 5000):** Q01 strand는 445개이고 **전부 c0253(ROUTE BLQ_TOKEN)을 last-c로 두고 terminal=QUARANTINE에 도달**한다(`c_sequence[-1]=="c0253"` 100%). c0306(NORMALIZE, L-4→L-5)은 mess 토큰 정규화 transform이고 `can_route_to_q=[Q01]`은 **best-strand 0개**에서 runtime 라우팅으로 실현되지 않는다(c0306은 토큰만 canonical화; 정책 부재→Q01은 상류 A5 축에서 결정). 즉 c0306발 Q-route는 fail-branch conditional edge = Phase 7(D-S4) 재구성 소관이며 Phase 5 strand로 c0306발 라우팅은 검증 불가(slice 2 c0019→c0251=[[GAP-26]] 정확히 동형).
- **실제 라우팅 메커니즘(SSOT):** c0205(DETECT BLQ_TOKEN, A5 axis, a5_state 생산) → c0253(ROUTE, reqdet=c0205). c0253 last-c 645개가 **(QUARANTINE,Q01)=445 / (QUARANTINE,Q15D)=89 / (INVALID,None)=111**로 분해된다(c0205._route_a5 동형; q_codes Q01 trigger 정합).
- **★ can_route_to_q ⊊ 실제 라우팅(추가 발견):** c0253.can_route_to_q=[Q01]은 실제 라우팅 {Q01,Q15D,INVALID}의 **부분집합**이다 — Q15D(89, BIOANALYTICAL-FINAL-FLAG-MISSING)·INVALID(111, ABSENT)는 c0253 선언에 없다. Phase 7 D-S4에서 c0205.can_route_to_q=[Q01,Q15D] + [[GAP-8]](c0205 ABSENT→INVALID scope-out)으로 conditional edge 재구성(고립 terminal 0). c0306.can_route_to_q=[Q01]도 동일하게 D-S4 선언.
- **검증목표 재정의(slice 6 채택):** "c0253이 a5_state(c0205 생산)를 → Q01(정책 부재)/Q15D(adjudication 부재)로 정확히 라우팅하고, 고립 Q-terminal 0(c0253 incoming ≥1)임을 orchestrator·strand로 검증"(tests/test_strands.py: route_blq_no_policy_to_q01/bioanalytical_to_q15d_dynamic·q01_routed_by_c0253_last·q01_terminal_reachable_not_isolated). c0305/c0306은 mess detect+normalize(silent no-op 0)로 별도 검증.
- **status:** ✅ RESOLVED (Phase 7 결정 C, 사용자 승인 2026-06-03 — 해결후보 (a): c0253.can_route_to_q +Q15D, 최소 변경). c0253→INVALID(111)는 결정 B terminal_routing으로 기해소. **c0253→Q15D(89)** = A+B 후 유일 잔존 scope-out이었으며 결정 C로 conditional edge 편입(89 pure, scope_out 1→0, conditional 51→52, pure 3139→3228). 결정 A(c0252→Q04)와 동형(ROUTE c SSOT가 can_route_to_q 미선언 Q로 라우팅). **cite-verify 완료:** universe_sm §3 A5 BIOANALYTICAL-FINAL-FLAG-MISSING→Q15D(:146) · q_codes Q15D.trigger(A5 disjunct, :278) · anchors Q15D(:54) · c0205.can_route_to_q=[Q01,Q15D] 선례 · c0253 impl/postcond/snippet 이미 Q15D 산출(선언만 결손). impl/postcond 무변경. [[GAP-15]]/[[GAP-26]]/[[GAP-8]]/[[GAP-34]] 연계.
- **영향 범위:** Phase 5 slice 6(검증목표·orchestrator c0253 ROUTE 배선), Phase 7(c0306 can_route_to_q + c0253 Q15D/INVALID conditional edge 재구성·고립 Q-terminal 점검).

---

## [GAP-29] backbone 컬럼 8c (df)-only 시그니처 ↔ orchestrator fn(df,meta) 호출규약 불일치 (slice 7a)

> 기록: 2026-06-01 (Phase 5 slice 7a backbone-activation 통합 하네스 최초 가동 cite-verify). 기록 전용(c-unit·dispatch 무수정; slice 7a는 bare ref 배선만 = Option 1).

- **현상:** Phase 4 초기 구현 c0001/c0010/c0011/c0012/c0014/c0016/c0017/c0018은 공개 시그니처가 `(df)` 단일인자다. 그러나 orchestrator `dispatch()`는 모든 c를 `fn(df, meta)`로 호출한다 → 이 8c가 dispatch되면 `TypeError`. (나머지 backbone c0013/c0015/c0019/c0022/c0023/c0140/c0141·axis c0200–c0210은 `(df, meta)`로 정합.)
- **★ falsifiable 측정(slice 7a 라이브):** 이 8c는 **173 완주 strand에 0회 등장**한다 — 전부 7b 미배선 상류(c0150/c0160/c0030/c0040/c0041) 하류라 완주 경로에 도달하지 못한다. 따라서 7a에서 실제 호출이 발생하지 않아 **green 무영향**(tests/test_integration_slice7a.py::test_c1_axis_covered_by_completing_strands가 NOMETA ∉ exercised를 명시 고정). 결함은 latent이며 7a는 bare ref 배선만 수행.
- **처리(✅ slice 7b 완료):** 8c 시그니처를 `def fn(df: pd.DataFrame, meta: dict | None = None)`로 정규화(본문 무변경). **cite-verify 결론:** `meta=None` 기본값으로 **충분** — 8c 전부 본문이 meta를 미참조하며((df)-only라 구조적으로 불가, 8개 본문 read 확인) 현재 postcondition을 df만으로 충족한다. 어떤 c도 meta를 read할 필요 없음. D-S1 detection 게이트는 함수 안이 아니라 orchestrator `dispatch()`가 `meta['{req}_ran']`로 외부 enforce(예: c0010 reqdet c0001).
- **falsifiable 근거:** (i) diff = 파일당 def 1줄(본문 0); (ii) 기존 단위테스트 호출부 전수 `fn(df)`/`fn(df_in)` 단일인자 green 유지(후방호환); (iii) `tests/test_integration_slice7b.py::test_gap29_dispatch_callable_no_typeerror`(dispatch `fn(df,meta)` TypeError 0)·`test_gap29_backward_compatible_single_arg`; (iv) baseline 796 → 806 green(+10 측정테스트, 회귀 0).
- **status:** RESOLVED (slice 7b — 시그니처 정규화 완료, meta=None 충분 cite-verify). 최종 호출규약(meta 실주입)은 **① full-orchestrator 통합 시점** 소관이나 8c는 meta read 불요라 무영향. [[GAP-30]](7b wiring 전제 반증)·[[GAP-19]](c0022/c0140 Phase 6 alias) 연계.
- **영향 범위:** Phase 7b(정규화 완료), Phase 6(c0022/c0140 alias·시그니처 일괄 — 잔여).

---

## [GAP-30] 7b wiring 전제 falsifiable 반증 — column-path 완주는 배선이 아니라 27c 신규 구현 (slice 7b)

> 기록: 2026-06-01 (Phase 5 slice 7b 프런티어 측정). 기록 전용 + 구현 백로그 산출([[GAP-26]]/[[GAP-28]] 멘탈모델 교정 동류).

- **현상(발주 가정):** slice 7b 발주문은 "구현됐는데 미배선인 상류 c를 REGISTRY에 배선해 완주 strand를 173→~467로 올린다"를 전제하고, 식별 기준을 "파일 존재 ∧ REGISTRY 부재 ∧ 7a 미포함"으로 두었다(7a가 23 기구현 c를 배선한 패턴의 연장으로 가정).
- **★ falsifiable 반증(src/c_units + REGISTRY + strands.json):** 구현 파일 **46** = REGISTRY 배선 **46** → "파일 존재 ∧ REGISTRY 부재"인 c = **0개**. wiring만으로 도달 가능한 완주 천장 = **173**(= 현재). 배선으로 더 열 strand가 없다. 467 완주에 필요한 상류 column-path **27c**(L-1→L-2 4 + L-2→L-3 12 + L-3→L-4 11)는 **전부 미구현**(spec/c_units.json엔 entry, src엔 파일 부재) → "배선"이 아니라 **신규 구현**(spec→test→fixture→impl→trap) 과제. 측정: 27c 구현+배선 = 완주 정확히 467, 전체 73 blocking c = 5000(`tests/test_integration_slice7b.py::{test_wiring_ceiling_reached,test_upstream27_yields_467,test_all73_blockers_yield_5000,test_all_blockers_unimplemented}`).
- **근거 — DECISION-D2 확장:** 미구현 c를 Phase 5 슬라이스로 발주하는 DECISION-D2 패턴(slice 1–6 mess 층)이 column-path에도 적용된다. batch≤5 규율상 27c = ~6–7 family-슬라이스(+ mess 46c까지면 ~13). 구현 지도 = `issues/column_path_implementation_backlog.md`(누적 곡선·coherent batch·D-S1 build order; A=L-3→L-4 ROUTE 173→353 최고 레버리지).
- **★ ①/②와 직교(혼동 금지):** 27c는 완주 **경로**만 연다. terminal **실현**(① 외부 meta 주입, GAP-4/6/7/9/10/11/12/14)·tree **구조**(② D-S4 conditional edge, GAP-5/8/12/13)는 27c 후에도 잔존하는 별개 결손. 7b 측정: 완주 strand 기대-q 실현 0(①)·axis 종착 68 terminal=None(②).
- **★ 영향 노트 갱신 (slice 8 / 2026-06-01, Batch A 6 ROUTE 구현+배선 — 완주 173→353):** 위 "① 실현 0 · 7a와 불변" 주장은 **slice 8에서 A0/A4 한정 falsifiable 갱신**된다. cite-verify(empty meta): `c0200→AIC-MISSING`·`c0204→MISSING-NO-POLICY`처럼 **df-default가 fail-state**인 axis의 ROUTE c는 외부 meta 없이도 실현한다 → 완주 353 중 **88 실현**(c0250 74×Q11 + c0252 14×Q08). 즉 "① realization=0"은 c0251/c0253(df-default=pass)의 **backbone-only 특성**이었다. **① 자체는 미해소**: 나머지 신규 ROUTE 종착 strand는 meta 부재로 **64 mis-realize + 28 INVALID-starve**되며 그 규모가 ① 결손을 측정한다(measure-not-fix). 올바른 descriptor 주입 시 정상 실현됨을 대조군으로 falsifiable 분리(`tests/test_integration_slice8_batchA.py::{test_realization_88_correct_without_meta,test_runtime_terminal_table_empty_meta,test_realization_deficit_scale,test_route_realizes_expected_q_with_meta}`). ② axis 종착 68·Q05 4는 Batch A에서 불변(`test_d_s4_axis_terminal_unchanged`). 7a/7b의 ①/② 측정 단언은 본 갱신에 맞춰 동기화됨(`test_terminal_realization_partial_without_meta`/`test_terminal_realization_partial_post_batch_a`/`test_d_s4_*`). → [[GAP-31]](c0252 Q04 divergence) 연계.
- **★ 영향 노트 갱신 (slice 9 / 2026-06-02, Batch B 5 axis DETECT/VERIFY 구현+배선 — 완주 353→439):** Batch B(c0211/c0212/c0214/c0215/c0216, req_det None)는 detect/verify(중간 c, terminal 키 미반환)라 완주 path만 +86 열 뿐 **runtime Q 실현 0 추가**다. 신규 86 = ok 0 + mis 0 + **starve 40**(전부 INVALID; c0253 a5=CLEAN→INVALID · c0254/c0255/c0256 axis default=pass→INVALID) + **axis-None 46**(c0210 종착, terminal 미실현=②). Batch A(88 실현)와 대비 — c0211/c0212의 has_above_uloq/has_replicates sub-flag는 a5_state(c0205)에 안 먹이고 실주체 c0253은 a5=CLEAN→INVALID. **df-default(axis별 누적, empty meta+neutral df):** c0211 has_above_uloq=False · c0212 has_replicates=False · c0215 has_exact_duplicates=False · c0216 has_encoding_issues=False(전부 no-route, df-default=pass-through) / **c0214 unit_declaration_complete=False→Q10(df-default=fail, [[GAP-32]])** 그러나 Q10 ROUTE c 부재라 runtime 미실현(② D-S4). **② axis-only 종착 68→114**(Batch B가 c0210 종착 +46; Phase 7 D-S4 소관, 미실현 class 불변 — 'still unchanged' 전제는 Batch B가 갱신). falsifiable: `tests/test_integration_slice9_batchB.py::{test_realization_zero_without_meta,test_runtime_terminal_table_empty_meta,test_df_default_flags_empty_meta,test_d_s4_axis_terminal_grows_to_114}`; 7a/7b 추적 단언 동기화(`test_d_s4_axis_terminal_grows_to_114_post_batch_b`). → [[GAP-32]](c0214 df-default divergence) 연계.
- **status:** OPEN (전제 반증 기록 + 작업=27c 신규 구현, 백로그가 추적). **진행: slice 8 Batch A 6 ROUTE + slice 9 Batch B 5 DET/VER 완료(완주 173→353→439, upstream 11/27 구현, L-3→L-4 층 전부 완성), 남은 16 upstream(L-1→L-2 4 + L-2→L-3 12) + 46 mess.** measure-not-fix(7b 구현 0; slice 8 6c; slice 9 5c).
- **영향 범위:** Phase 5 이후 column-path 슬라이스 시퀀스(백로그 따라 진행), Phase 5 full-integration 완료 판정(나머지 16 upstream 선결로 **미완**). [[GAP-29]](정규화 = 27c 호출 전 선결, RESOLVED)·[[GAP-31]](slice 8 c0252 divergence)·[[GAP-32]](slice 9 c0214 df-default divergence) 연계.

---

## [GAP-31] c0252 ROUTE AMT — strands SSOT(INFUSION-STOP-RESTART→Q04) ↔ postcond(Q04 미선언) divergence (slice 8)

> 기록: 2026-06-01 (Phase 5 slice 8 Batch A 구현 중 cite-verify). 기록 전용(c-unit·spec 무수정; postcond-faithful 구현). [[GAP-28]] 동형(선언 ⊊ 실제 라우팅)의 더 심한 sub-case — 여기선 SSOT target이 postcond **밖**.

- **현상:** strands.json은 `a4_state='INFUSION-STOP-RESTART'`인 **168 strand**를 c0252(ROUTE AMT) last-c로 **Q04**(QUARANTINE)에 라우팅한다(cite-verify: c0252 last-c 736 = Q08 203 / Q14 191 / INVALID 174 / **Q04 168**). 그러나 c0252 spec(c_units.json)은 **Q04를 어디에도 선언하지 않는다**: `postcondition_predicate: routing_decision in ['Q08','Q14','INVALID']`, `precondition_predicate: a4_state in ['MISSING-NO-POLICY','ADDL-ACTUAL-CONFLICT','UNRECOVERABLE']`(INFUSION-STOP-RESTART 부재), `can_route_to_q: ['Q08','Q14']`.
- **★ c0251 선례로 해소 불가:** c0251(ROUTE TIME_FORMAT)은 spec 산문('UNRECOVERABLE→INVALID')을 무시하고 SSOT(Q12)를 채택했으나 **Q12 ∈ postcond**였기에 가능했다([[GAP-7]]). c0252는 **Q04 ∉ postcond**이라 SSOT(Q04) 채택 시 verbatim postcond(Hallucination 차단 #1, 1글자 변경 금지)를 위반한다 — postcond와 strands.json이 직접 모순.
- **처리(✅ slice 8, postcond-faithful — 사용자 결정 1번):** c0252는 INFUSION-STOP-RESTART를 `_A4_FAIL_TO_Q.get(a4,'INVALID')` default로 **INVALID**에 라우팅한다(c0253 ABSENT→INVALID 선례 동형). postcond 준수, spec 무변경. falsifiable 고정: `TestC0252::test_trap`, `TestC0252Adversarial::test_infusion_stop_restart_routes_invalid_not_q04`.
- **★ 미해소 잔존(divergence):** INFUSION-STOP-RESTART 완주 strand(slice 8에서 11 완주)는 strands.json 기대(Q04)와 런타임(INVALID)이 불일치 — ①(외부 meta 주입: full-orchestrator에서 c0204가 INFUSION-STOP-RESTART를 실제 산출하는지 포함)·②(Phase 7 D-S4: c0252의 Q04 분기를 strand 밖 conditional edge로 재구성)가 흡수. measure-not-fix(slice 8 mis-realize bucket의 일부).
- **해결 후보(사용자 승인 필요):** (a) c_units.json c0252 precond에 INFUSION-STOP-RESTART + postcond/can_route_to_q에 Q04 추가(Phase 2.9-style spec 변경 — verbatim postcond 확장이라 승인 필요); 또는 (b) strands.json A4→Q04 라우팅이 Phase 3.5 모델 오류인지 재검(더 큰 범위). 본 slice는 미수행, 기록·이월만.
- **status:** ✅ RESOLVED (Phase 7 결정 A, 사용자 승인 — 해결후보 (a) 채택). c0252 precond에 INFUSION-STOP-RESTART, postcond/can_route_to_q에 Q04 + impl 매핑 INFUSION→Q04 + c0204.can_route_to_q +Q04. decision_tree에 c0252→Q04 conditional edge(168 strand pure 편입). cite-verify: universe_sm §3 A4 '無 Q04', q_codes Q04.trigger. ★ slice 8의 postcond-faithful INVALID workaround(위 처리·미해소 잔존)는 **SUPERSEDED**. 단 런타임 실현(c0204 verify가 INFUSION을 fail-route→c0252)은 ① 재배선 잔여([[GAP-30]]; spec/tree divergence는 해소, 실현은 별개). 상세 [[GAP-34]].
- **영향 범위:** Phase 7(D-S4 c0252 Q04 재구성), ①(meta 주입 시 c0204 INFUSION 산출 정합), Phase 6/2.9(spec 정합 결정 시). [[GAP-28]](c0253 동형)·[[GAP-7]](c0251 산문≠SSOT, Q∈postcond라 해소)·[[GAP-30]](slice 8 ① 영향 노트) 연계.

---

## [GAP-32] c0214 VERIFY UNIT_DECLARATION — df-default divergence (c0213 scope-out-pass ↔ c0214 incomplete-fail) (slice 9)

> 기록: 2026-06-02 (Phase 5 slice 9 Batch B 구현 중 cite-verify). 기록 전용(c-unit·spec 무수정; SSOT-faithful 구현). [[GAP-28]]/[[GAP-31]](선언/실제 라우팅 정합 계열) 동형 — 여기선 **두 VERIFY c의 df-default가 정반대**.

- **현상:** 같은 kind=verify·같은 postcond 형태(`meta.get('<flag>', True)`)인데 신호 부재 시 df-default가 정반대다. **c0213(VERIFY TIME_ANCHOR):** 앵커 토큰이 하나도 없으면 기본 `time_anchor_consistent=True`(scope-out, 날조 금지 — pass). **c0214(VERIFY UNIT_DECLARATION):** numeric 컬럼이 존재하고 meta['units'] 미선언이면 `unit_declaration_complete=False`(incomplete→Q10 — fail). empty meta + neutral df(numeric 컬럼 존재)에서 c0213=pass, c0214=fail.
- **★ 왜 divergence가 정당(SSOT-faithful):** c0214의 SSOT가 fail-default를 지시한다 — llm_prompt '단위 사전 불완전 시 Q10 routing', python_snippet `all(meta['units'].get(c) is not None for c in numeric_cols)`(units 부재 → all 거짓 → False), can_route_to_q=[Q10]. 반면 c0213의 '토큰 부재→consistent=True'는 그 c docstring 명시 scope-out. 즉 둘 다 각자 SSOT에 충실하며 df-default는 c별 의미(검출 대상의 부재가 'pass'인가 'incomplete'인가)에 따라 갈린다. postcond는 둘 다 flag-based라 SSOT와 무모순(GAP-31식 'SSOT target ∉ postcond'가 아님 — divergence는 *구현 default 방향*이지 postcond 위반 아님).
- **★ runtime 영향(measure-not-fix):** c0214의 Q10은 **runtime 미실현**이다 — Q10 종착 ROUTE c가 부재(c025X 중 Q10 라우터 없음)하고 c0214는 verify(terminal 키 미반환). 따라서 df-default=fail은 meta 플래그(unit_declaration_complete=False)·return route_to_q=Q10에만 나타나고 run_strand 종착 terminal은 None(② D-S4 conditional edge 소관, GAP-5/8/12/13 동류). slice 9 신규 86 완주 중 c0214가 중간에 등장해도 strand terminal은 c0210/c0253/축으로 결정.
- **처리(✅ slice 9, SSOT-faithful):** c0214는 declared `meta['unit_declaration_complete']`(bool) > `all(meta.get('units',{}).get(c) is not None for c in numeric_cols)` 순; numeric 컬럼 부재 시 공허 True(scope-out). silent-error 0 위해 `meta.get('units',{})`. falsifiable 고정: `TestC0214::test_trap`(units 일부 누락→Q10), `TestC0214Adversarial::{test_df_default_fail_empty_meta,test_declared_override_wins,test_no_numeric_cols_vacuous_pass}`, `test_integration_slice9_batchB.py::test_df_default_flags_empty_meta`.
- **status:** OPEN (SSOT-faithful 구현 완료 + divergence 명문화). Phase 7 D-S4(c0214 Q10 conditional edge)·①(외부 units meta 주입) 소관. '결손'이 아니라 두 c의 df-default 의미 차이 기록.
- **영향 범위:** Phase 7(D-S4 Q10 분기), ①(units meta 주입 시 c0214 실현), 후속 VERIFY c 구현 시 df-default 방향 결정 선례. [[GAP-30]](slice 9 ① 영향 노트)·[[GAP-28]]/[[GAP-31]](선언/SSOT 정합 계열) 연계.

---

## [GAP-33] Phase 7 step 1~2.5 — decision_tree.json 최초 조립(골격) 생성 근거 + 순수-edge 주입 정산

> 기록: 2026-06-03 (Phase 7 진입, decision_tree.json 최초 생성). 기록 + 산출물 근거. c_units/spec 무수정, run_strand 무변경.
> 산출: `spec/decision_tree.json`(생성기 `build_decision_tree.py`, DETERMINISTIC) · 검증 `tests/test_decision_tree.py`(17, green) · baseline **917→934**.

- **범위(이번 세션):** PROMPTS Phase 7 **step 1(골격 채택)→2(c 부착)→2.5(D-S4 conditional-edge 재구성)** 중 **"순수 edge"(spec 결정 불요)** 만. 즉 57 wired c의 `can_route_to_q`/`verify_visualization.fail_route_to`에서 **직접 도출**되는 conditional edge만 정적 주입. suffix-tree 다발 압축(step 2 하류)·안정화(step 5)·orchestrator 재배선·spec-결정 edge는 **제외**.
- **★ 조립 결과(falsifiable, `build_decision_tree.py` 재실행 동일):**
  - node **100** = 8 N0–N7(branch) + 11 A0–A10(conditional, 101 axis-state) + 5 process terminal + 19 Q terminal + 57 c. **임의 식별자 0**(전부 anchors∪REGISTRY; `test_no_foreign_identifiers`). c node == orchestrator REGISTRY(57; `test_c_nodes_equal_registry`로 generator WIRED↔배선 drift 봉쇄).
  - conditional edge **49** = Σ(wired c.can_route_to_q). 모든 배선 c.can_route_to_q **전수 주입**(`test_every_wired_can_route_to_q_has_edge`). bundles **0**(scope).
- **★ Q-terminal partition(두 lens 일치 — 구조적 c_units + strands 실측):** **EXERCISED 13**(wired ROUTE c can_route_to_q: Q01/02/03/04/06/07/08/09/11/12/13/14/15D) / **STATIC 2**(Q05←c0201·Q10←c0214, nonroute detect/verify라 edge는 있으나 realizing route c 없음=검증 strand 없음) / **UNREACHED 4**(Q15A/B/C/X, wired c edge 0; source c 미배선 c0368/c0499/c0209). **고립 Q-terminal 0**은 EXERCISED 13에 한정 성립(`test_no_isolated_exercised_q_terminal`); STATIC/UNREACHED는 deferred에 명문 기록(silent drop 아님). ★ 발주문 추정 "12/7"의 실측 정정 = **13/2/4**(=13 exercised, 6 비-exercised).
- **★ 압축 불변성(① 비의존, empty meta):** ⓐ **cost**: 5000 strand 전부 `total_cost == Σc.cost`(`test_cost_invariance_all_5000`; Q.routing_cost 경로 비가산 명시) — 선검증(pre-flight)에서도 확인. ⓑ **terminal**: last-c∈wired ROUTE & q∈can_route_to_q인 **PURE 2971 strand**는 tree conditional edge가 동일 Q 재현(`test_terminal_invariance_pure_scope`).
- **★ scope 규율(실제 라우팅 ⊋ can_route_to_q = 미주입·이월):** **scope-out 5 edge / 572 strand** — c0252→Q04(168, [[GAP-31]]) · c0253→Q15D(89, [[GAP-28]]) · c0252→INVALID(174, [[GAP-31]]) · c0253→INVALID(111, [[GAP-8]] ABSENT) · c0256→INVALID(30, [[GAP-12]] IRRECONCILABLE). conditional_routing에 **미주입**(`test_scope_out_edges_not_injected`) + `deferred.scope_out_edges`에 strand_count와 기록(`test_scope_out_documented_in_deferred`).
- **★ 순수-edge GAP 5건 정산(발주 핵심):** [[GAP-8]](c0205→Q01/Q15D) · [[GAP-10]](c0206→Q03/Q04) · [[GAP-12]](c0209→Q06/Q15D) · [[GAP-26]](c0251→Q02/Q12; c0019/c0203/c0311/c0315 동반) · [[GAP-28]](c0253/c0306→Q01)의 **선언된** conditional edge는 skeleton에 **주입 완료**. 각 GAP의 "실제 라우팅 ⊋ 선언"(Q15D/INVALID/Q04) 잔여는 scope-out으로 이월(위 항).
- **★ GAP-25 node-count 재측정:** collapsed **100** / expanded worst **190**(synthetic 248/236 대체, ≪5000) — [[GAP-25]] 갱신.
- **spec 결정 대기(범위 밖, 사용자 승인 대상):** `issues/phase7_spec_decision_queue.md` 산출 — [[GAP-5]]/[[GAP-31]] Q04 라우팅, [[GAP-13]] A10 위치+UNSUPPORTED/INVALID terminal, [[GAP-27]]B FORMAT↔TIMEZONE, c0040 placeholder, UNREACHED-Q(Q15A/X 비-axis trigger) 처리안.
- **status:** 골격(step1~2.5) 완료 + ★ 후속 [[GAP-34]](결정 A·B: c0252/c0204 INFUSION→Q04 spec-change + terminal_routing INVALID) + [[GAP-28]] 결정 C(c0253→Q15D 편입, scope-out 0; 57-wired D-S4 conditional/terminal-routing 층 완전). Phase 7 잔여: (1) 미배선 source c(UNREACHED-Q Q15A/B/C/X) → (2) step 2 다발 압축·step 4 orchestrator 재배선(①/C·D·E와 연계).
- **영향 범위:** Phase 7(잔여 step)·Phase 8(decision_tree.json 소비)·①(재배선). [[GAP-8]]/[[GAP-10]]/[[GAP-12]]/[[GAP-26]]/[[GAP-28]](순수-edge 출처)·[[GAP-5]]/[[GAP-13]]/[[GAP-31]]/[[GAP-32]](spec 결정/scope-out)·[[GAP-25]](perf 재측정)·[[GAP-34]](결정 A·B) 연계.

---

## [GAP-34] Phase 7 결정 A·B 반영 — c0252/c0204 INFUSION→Q04 spec-change + terminal_routing(INVALID) 주입 정산

> 기록: 2026-06-03 (Phase 7 골격 [[GAP-33]] 직후, 사용자 승인 spec 결정 반영 세션). 산출 근거. SSOT 순서 spec→test→구현 준수, run_strand 무변경(① 비의존).
> 산출: `spec/c_units.json`(c0252/c0204) · `src/c_units/c0252_route_amt.py` · `spec/decision_tree.json` 재생성(`build_decision_tree.py`, DETERMINISTIC) · `tests/test_decision_tree.py`(17→19).

- **결정 A(GAP-31/5 RESOLVE, spec-change):** c0252 precond +`INFUSION-STOP-RESTART`, postcond `routing_decision in ['Q04','Q08','Q14','INVALID']`, can_route_to_q +Q04, snippet 매핑 +INFUSION→Q04; c0204 can_route_to_q +Q04(postcond 불변). cite-verify: universe_sm §3 A4 `INFUSION-STOP-RESTART(無 Q04)`, q_codes Q04.trigger `(A4=INFUSION-STOP-RESTART AND policy 부재)`. → conditional edge **+2**(c0252→Q04 168 pure / c0204→Q04 0; realizing c0252·c0257), PURE **2971→3139**. 선택: tree-edge-only(a) 아닌 spec-change(b) — step 2.5는 edge를 can_route_to_q에서 도출하므로 tree-only는 `source=can_route_to_q` 불변식·`test_deterministic_regeneration` 모순.
- **결정 B(GAP-8/12 RESOLVE + GAP-31 INVALID facet, 표현 규약):** process-terminal edge를 conditional_routing(Q-only)과 분리한 **`terminal_routing`** 배열로 표현. SSOT = 각 wired ROUTE c의 postcond routing_decision의 INVALID(c_units 무변경). **3 edge / 315 strand**: c0252→INVALID(174)·c0253→INVALID(111)·c0256→INVALID(30). INVALID process terminal incoming≥1(고립/dead 해소). 결정론 도출(하드코딩 0). c0251→INVALID(postcond 선언이나 측정 strand 0)는 `stats.terminal_declared_unexercised`에 falsifiable 기록(silent drop 0).
- **★ 압축 불변성(① 비의존) 유지:** cost-invariance 5000 + pure 재현(3139) + orchestrator realized **88 불변**(통합 slice7a/7b/8/9 green) — empty meta→df-default `MISSING-NO-POLICY`→Q08 경로라 INFUSION 미도달, c0252 impl 변경이 realized 분포 무영향. 결정 A 런타임 실현(c0204 verify→c0252 fail-route)은 ① 재배선 잔여([[GAP-30]]).
- **★ 잔여(deferred, 사용자 확정):** ~~c0253→Q15D(89, [[GAP-28]])~~ → **결정 C로 RESOLVE**(2026-06-03, can_route_to_q +Q15D, scope-out 1→0). 잔여 = **UNREACHED-Q Q15A/B/C/X**(source c 미배선 c0368/c0499/c0209; Q15C 단독 비대칭 주입 금지 — 일괄 이월) · [[GAP-13]](c0210 A10)/[[GAP-27]]B/c0040(명시 이월). scope-out 5→1(A·B)→**0**(C)/572→89→**0**.
- **falsifiable(`tests/test_decision_tree.py` 19 green):** `test_terminal_routing_injected`(3/315/postcond 정합/INVALID incoming≥1/Q-edge 미혼재)·`test_terminal_declared_unexercised_documented`(c0251)·`test_scope_out_edges_not_injected`(c0253→Q15D만)·`test_scope_out_documented_in_deferred`(89)·`test_terminal_invariance_pure_scope`(3139)·`test_deterministic_regeneration`. stats: conditional **51**/terminal **3(315)**/scope_out **1(89)**/node 100 불변.
- **status:** ✅ RESOLVED (결정 A·B 반영 완료). [[GAP-5]]/[[GAP-8]]/[[GAP-12]]/[[GAP-31]] RESOLVE 근거. 잔여 [[GAP-13]]/[[GAP-27]]B/UNREACHED-Q deferred ([[GAP-28]]은 후속 결정 C로 RESOLVE — scope-out 0).
- **영향 범위:** Phase 7(잔여=다발 압축·재배선)·Phase 8(terminal_routing 소비)·①(c0204 INFUSION 실현). [[GAP-33]](골격 선행)·[[GAP-30]](① 실현)·[[GAP-28]](유일 잔존 scope-out) 연계.

---

## [GAP-35] Phase 8b UAT — 끊김 판정(정상) + 렌더 시각 명료성·종착유형 색·recover edge (render 표현층, clean)

> 기록: 2026-06-03 (Phase 8 직후 사용자 Chrome 실물 UAT 반영). **record-only/clean — 신규 결함 0.** SSOT/엔진(decision_tree/c_units/strands/q_codes/orchestrator) 무변경, `render/build_html.py` 표현층만 수정. 산출 `render/index.html` deterministic 유지.

- **★ 끊김 판정(falsifiable, 결함 아님):** 사용자 "어떤 경로는 NONMEM-ready까지 가고 어떤 건 중간에 끊겨 보임" 보고를 reachability로 검증.
  ① **strand-level:** strands.json 5000개 **전부 terminal 도달**(AUTO 5·REPAIR 230·QUARANTINE 3380·INVALID 862·UNSUPPORTED 523, 합 5000) — **terminal=None 고립 0**.
  ② **render directed dead-end 26개** = axis A0~A10(11) + `stage:L-4→L-5`(1) + 정규화/no-route c(14). 이는 **렌더 모델 아티팩트**: attach edge가 `c→backbone` 방향이고 axis/stage는 **분류 앵커**(passing-through cell)라 forward flow 미보유 = *구조 그래프이지 실행 flow 그래프 아님*. 사용자 지목 **c0201은 Q05로 라우팅(terminal 도달) → dead-end 아님**(인접 axis A1/A7/A8가 분류 앵커라 시각적으로 멈춰 보인 것).
  ③ 유일 고립노드 = unreached Q15A/B/C/X(edge 0, **의도된 deferred** — `tests/test_render.py::test_no_isolated_nodes_except_deferred` 통과 중). → **∴ '끊김'은 결함 아님**. Problem B 범례/배너 + "구조 그래프(axis=분류 앵커)" 설명으로 해소.
- **★ 문제 A(분기 가시성) — Lock 7 frozen 범위 cite-verify:** Lock 7은 **클릭-하이라이트**만 규정(single `#FFD700`/5px, conditional `#FFF8B0`/3px). resting conditional edge 색은 **Lock 미규정 = Phase 8 렌더 선택(비-frozen)**이었고 `#bcaaa4`(taupe)/width2라 회색 backbone·attach와 대비 낮아 안 보였음(legend swatch는 `#FFF8B0`로 실제와 불일치). → resting conditional `#c9920e`(골드/앰버) dashed **width 3.6**(하이라이트 #FFF8B0과 '노랑 계열' 일관, resting 진/HL 옅) · terminal_routing width 2.5→3.2(적갈 유지) · legend swatch 실제값 정정. **Lock 7 hue(#FFD700/#FFF8B0) 불변.**
- **★ 문제 B(끊김 의미) — 종착유형 6+ 색 + 경계 배너:** 완주 AUTO/REPAIR=녹(`#43a047`/`#a5d6a7`) · QUARANTINE=주황(`#ffa726`, 사람개입대기; ★Lock7 #FFD700 선택테두리가 노랑 fill서 안보이는 충돌 회피로 주황) · Q-code=빨강(`#ef5350` 보존) · 미실현 terminal(Q05/Q10 static)=회색 점선(`#b0bec5`) · INVALID=slate 8각(`#546e7a`, 복원불가, 실 315 wired strand) · UNSUPPORTED=회보라 8각(`#9e8aa8`, 미지원; tree상 GAP-13 deferred 경로로만 도달=주석 명시) · 미배선·deferred=ghost. 종착색=fill, 하이라이트=border → 채널 분리(위계 충돌 0). **경계 배너**(build-time 계산·검증가능): oracle(5000 strand 종착) ↔ 57-wired 구현범위 **두 축 명확 구분**; 미배선 c **62**(strands 등장·미구현)·미실현 Q **2**·deferred **7**(unreached Q4+GAP c3)·realized(pure) 3228. ★ 발주문의 orchestrator 런타임 지표(완주 439·realized 88)는 render 입력서 재계산 불가(일부 oracle과 불일치: oracle 완주=235·미배선 c=62)라 **배너 미포함**(별도 안내) — 날조 0.
- **★ recover edge(human-in-the-loop):** q_codes `recover_to_c_id`의 **시각화**(라우팅 신설 아님). 도달가능 Q(exercised∪static)+타깃 wired c일 때만 Q→c **파랑 점선**(`#1976d2`, 별도 ekind="recover", **+14 edge**: Q01/02/03/04/05/06/07/08/09/11/12/13/14/15D). 미배선 타깃(Q10→c0330) edge 생략·패널 명시; unreached Q(Q15A/B/C/X) 제외(고립 불변 보존). 하이라이트는 `flowNeighborhood`로 recover 제외(Lock 7 auto-flow union 의미 보존), 선택 노드 incident recover만 `hlRecover`(파랑) 강조 — "자동 복귀 아님" 명확. ★ conditional **52**·terminal_routing **3** 카운트 불혼입(별도 카운트 회귀 `test_recover_edges_separate_ekind`).
- **falsifiable(`tests/test_render.py` +9 = 962 green):** `test_recover_edges_separate_ekind`(recover 14·cond 52·termr 3)·`test_recover_only_reachable_q_to_wired_c`·`test_recover_unwired_target_and_unreached_skipped`·`test_recover_isolation_invariant_preserved`·`test_boundary_banner_numbers`(전 수치 build-time 산출)·`test_termination_legend_present`·`test_termination_status_colors`·`test_conditional_gold_visibility`·`test_recover_edge_style_and_lock7_separation`. 기존 19 render test(node 100·attach 76·cond 52·termr 3·isolation·Lock7 #FFD700/#FFF8B0·#ef5350·6 shape·inline·determinism) 전부 보존.
- **GAP-25 perf 재측정:** headless Chrome `✅ 101 nodes · dagre 94 ms · total 281 ms`(class=pass) ≪10s — +14 recover edge·배너 perf 무영향 재확인.
- **status:** ✅ clean (record-only — 신규 결함 0; 구조 invariant 무변경). 끊김 판정 = 정상(범례/배너로 설명). [[GAP-25]](perf 재측정)·[[GAP-13]](UNSUP/A10 deferred 주석)·[[GAP-33]]/[[GAP-34]](Phase 8 렌더 소비 대상) 연계.
- **영향 범위:** Phase 8(render/index.html 표현층)·재UAT. 엔진/SSOT 무영향(① ② 미배선 backlog 불변).

---

## [GAP-36] Phase 9 적대 sweep — C_dead {c0042/c0043/c0333} "tree-live" 처분 미실현 + DoD#3 C1 119/122 bound가 living ledger 미기록

> 기록: 2026-06-03 (Phase 9 adversarial review, mode: skeptical). **미기록 결손 1건 — ②latent(즉시 결함 아님).** Phase 9 report-only(spec/src 무수정 — 기록만). 산출: `tests/test_phase9_adversarial.py`(+12, durable cross-SSOT guard)·`issues/phase9_adversarial_review.md`(매트릭스 doc).

- **발견(falsifiable):** Phase 9 기계 sweep이 **strand 미등장 dead c = {c0042, c0043, c0333}**(셋 다 미배선 fail-branch ROUTE c)를 재확인. DoD#3 **C1**("모든 c가 ≥1 strand OR conditional-edge incoming≥1")의 두 절 모두 불충족 → **C1 = 119/122 bound**. 이 3 C_dead는 `spec/closure_proof.md`(INV-3 `C_dead: 3 {c0042,c0043,c0333}`, :103)·`spec/strands_stats.md`(§6 `C_used 119/C_all 122/C_dead 3`)에 **문서화됨**(∴ 은폐 아님). **그러나** closure_proof는 이들을 "strand에서 dead이나 **tree에서는 live**"(Option C 처분 권고, :74)라 기술하는데, **실측상 셋 다 미배선 → `spec/decision_tree.json` 부재**(is_tree_node=False·conditional/attach edge 0): closure_proof의 "tree-live"가 Phase 7 57-wired scope에서 **미실현**. 이 실현-gap + C1 bound + closure_proof 처분(Option A/B/C) pending이 **living GAP ledger(provenance_gaps.md)에 미기록**이었다(grep `C_dead|119|c0042` → 0건).
- **분류(② latent, 즉시 결함 아님):** banner "미배선 c 62"는 `strand 등장 ∧ 미배선`(STRAND_CS−REGISTRY)이라 이 3개(`strand 미등장 ∧ 미배선`)는 미포함 — 122 = 57 wired + 62 unwired-in-strand + **3 orphan C_dead**. fail-branch ROUTE c는 best-strand(pass-only)에 미등장이 **D-S4 정상**이며, 배선 시 can_route_to_q→conditional edge로 tree-live가 된다(c0042→Q01/Q04/Q08/Q09·c0043→Q11/Q15X·c0333→Q10). 즉 현 경계의 **정직한 미구현**.
- **해소 경로:** c0042/c0043(L-1→L-2 Batch E)·c0333(L-4→L-5 mess) 배선 시 D-S4 conditional edge 편입 → C1 OR절 충족·tree-live 실현. [[GAP-30]](27c 신규 구현 백로그) 연계. closure_proof Option A(remove)/C(keep) 처분은 **사용자 결정 pending**(Phase 9 report-only라 미변경).
- **처리(2026-06-03 honesty-ledger 닫음, Direction C):** ✅ (1) `spec/closure_proof.md` 시제 정정 **적용** — c0042 "strand에서 dead이나 tree에서는 live" → "strand에서 dead; 배선 시 tree-live 후보(현 57-wired 미배선→incoming edge 0=tree 부재)" + disposition 표 아래 **57-wired 시제 주의 노트**(c0042/c0043/c0333 일괄 + C1 119/122 명시). ✅ **C1 = 119/122**(C_dead 3) 및 **C3 partition = 13 exercised / 2 static(Q05·Q10) / 4 unreached(Q15A/B/C/X, 사용자 defer)** 를 본 원장(여기) + `phase_settlement_checklist.md`에 명시 = **living ledger 기록 완료**(이전 미기록 결손 해소). ⏸ (2) C_dead 처분(Option A/B/C) = [[GAP-30]] 배선과 함께 일괄 pending. ⏸ (3) banner "orphan C_dead 3" 보조 표기 = render 표현층 검토 이월.
- **falsifiable(`tests/test_phase9_adversarial.py` 12 green):** `test_p9_11_c1_dead_c_matches_documented`(dead c == 문서화 C_dead {c0042,c0043,c0333}, **미기록 dead 0** 회귀방지)·`test_p9_2_ds4_wired_no_missing_edge`(wired scope C1/D-S4 무결)·closure_proof.md :103 INV-3·strands_stats.md §6. (시제 정정은 docstring만 동반 sync; assertion 무변경, green.)
- **status:** ✅ RESOLVED (honesty-ledger 기록 + closure_proof 시제 정정, 2026-06-03 Direction C). C1 119/122 · C3 13/2/4가 원장·checklist·closure_proof에 명시 = **문서화된 정직한 경계**(미기록 결손 해소). ②latent 실현분(C_dead 3의 실제 tree-live)은 별개 미구현으로 [[GAP-30]](상류 배선 Batch E/mess) + 처분 결정 pending에서 추적. wired scope(57)는 무결(C1 119/122의 3 예외 = 문서화 C_dead 전부). [[GAP-33]]/[[GAP-34]](Phase 7 골격·결정)·[[GAP-13]]/[[GAP-27]]B/[[GAP-38]](기타 Phase 7 deferred) 연계.
- **영향 범위:** `spec/closure_proof.md`(시제 staleness)·DoD#3 C1 충족 경계·①/Batch E·mess wiring(GAP-30). 엔진/SSOT/render 무영향(Phase 9 무수정).

---

## [GAP-37] Direction B(raw CRO deliverable 수용) + mode (b) auto-ingest 확정 — front-half 하드 선결 2건(INTRASHEET_QA_BLOCK · subject-as-column wide) + B ripple 측정(generate_sc reshuffle · strand derivator 부재)

> 기록: 2026-06-03 (Batch-C 슬라이스 진입 시 하드 선결 게이트 → 방향 결정 + report-only ripple 측정 세션). **측정만 — spec/src/anchors/decision_tree/universe_sm 무수정, 패치/adapter 설계 금지(제안서는 별도 세션).** baseline 974 green·HEAD 2004d27 불변.
> 산출: 본 GAP 기록 + `issues/direction_B_ripple_measurement.md`(측정·로드맵 상세).

- **★ 방향 결정(사용자 확정):** **Direction B** = raw CRO/bioanalytical deliverable를 입력으로 수용(이미-tabular/analyte-wide 가정 해제). **mode (b) auto-ingest** = 실물 xlsx 투입 → 출발점 자동 detect + 이유(reason) 부착 → decision tree navigate가 실사용 목적. ([[GAP-30]] 배선 백로그·pilot §4/§5 SELECTIVE-wire 판정과 연계.)
- **하드 선결 2건(cite-verify, 직접 source read):**
  - **(A) intra-sheet QA block:** `refs/universe_sm.md §6`에 `INTRASHEET_QA_BLOCK` **무**(grep 0), `anchors.json` MESS_CONCEPT NOUN **무**(grep 0). `FILTER`=조건부 FLAG(행삭제 아님)·후보 NOUN(FREETEXT_COMMENT/TRAILING_BLANK/DUPLICATE_ROW)은 QA/Calibration/QC 행(구조적·비공백·비중복 레코드)과 **의미 불일치** → 기존 vocab 미커버. `pilot_validation_preclinical.md` §2 row5·§3 step2가 ⛔ not-accepted로 명기.
  - **(B) subject-as-column wide:** `c0120 PIVOT ANALYTE_COLUMN`은 **analyte-wide**(input `DRUG_A,DRUG_B` → `analyte_label`+`dv_value`, ref `§3 A5 MULTI-ANALYTE`). 전임상 raw는 **subject-wide**(동물 #1–6 열 → `ID`). 다른 pivot 의미 → c0120 미일치(pilot §2 row3·§4A `CONC_WIDE/SUBJECT_AS_COLUMN` 후보).
- **★ 정확한 프레이밍(전임상 전용 아님):** 이 결손은 raw CRO/bioanalytical deliverable **일반**의 front-half gap(임상 분석실 raw도 동일 구조 — 다중시트·QA혼재·wide). 현 **57-wired = "이미-tabular/analyte-wide 입력엔 완성, raw 분석실 deliverable 입력엔 미완"**. fork 축 = **"진입점이 얼마나 raw인가"**(tidy long 이후 step5~8은 가이드, raw→tidy long 앞단 step2~4는 미실현).
- **★ B ripple 측정(상세 = direction_B_ripple_measurement.md, 코드 근거):**
  - **M1 sc 생성기 = reshuffle(additive 아님):** `generate_sc.py` 단일 `random.Random(42)`(L443) 위치순 소비 + 고정 budget 5000(L28–29) + 위치 sc_id(L460) + 미달 dim(<5) 시 K2 sc **교체**(L332). 신규 §6 dim 자연 추가 → rng 스트림 시프트/≥5 교체 → 5000 membership 재셔플 → starting_conditions→strands→decision_tree→HTML 전면 재도출. additive(0000–4999 동결 + 5000+ append)는 **현 구조 미지원**(생성기 수술 + budget 증액 + 별도 rng 필요).
  - **M2 strand derivator 부재(★ 최대 비용):** `spec/strands.json` 쓰는 `.py` **0건**(airtight grep) — Phase 3.5 best-strand 엔진(Dijkstra/feasibility/second_best)이 repo에 **없음**. strand 변경(재셔플이든 additive append든)은 **derivator 재작성 선결**. Direction B와 무관한 **잠재 재현성 결손**.
  - **M3 tree 자동 재생성:** `build_decision_tree.py` DETERMINISTIC, strands SSOT 소비(L29–32) → strands 변경 시 자동 재생성. 단 `WIRED`(57) 하드코딩(L39–51, `REGISTRY==WIRED` 강제) → 신규 c는 WIRED+REGISTRY 수동 동기.
  - **M4 adapter contained = 성립(단서부):** 엔진 `dispatch(c_id,df,meta)`/`run_strand`는 df+meta 소비, mess_profile 미소비(L16, D-S1) → auto-ingest adapter는 **순수 front-end**(dispatch/run_strand 무변경). 단 xlsx ingester(미존재)·초기 meta 빌더·신규 front-half c 필요 → contained≠trivial.
  - **M5 reason single-source = 성립:** detect/verify 62 중 `criterion_predicate_ko` **60/62**·`ref` **62/62** → mode (b) "이유 부착"을 spec에서 단일출처 재사용 가능.
- **분류:** **② latent + scope-boundary**(즉시 결함 아님 — 현 경계의 정직한 미실현). **OPEN → Phase 2.9′ 경로**(측정 선행, 본 세션 = 측정만).
- **해소 경로(설계 아님, 측정 결과):** ① (선결, B 전체) Phase 3.5 strand derivator 재작성(M2). ② Tier 0 adapter(M4)는 ①·패치 불요 = 최소 "넣고 navigate" 부분효용 first. ③ 이후 2.9′ 패치(QA/subject-wide/inline-BLQ/sparse) + Batch C/D/E 배선 = navigate 사거리 점증(all-or-nothing 아님). 상세 tier/비용 = direction_B_ripple_measurement.md §3–§4.
- **status:** OPEN (② latent — 측정 완료, 패치/adapter 미설계). 다음 = 측정 결과 기반 **2.9′ 패치 + adapter 제안서**(별도 세션, 사용자 승인). [[GAP-30]](배선 백로그)·[[GAP-33]]/[[GAP-34]](decision_tree 골격/결정 — strand 재도출 시 재생성 대상)·[[GAP-36]](Batch E/mess 배선)·[[GAP-23]](anchors root 경로) 연계.
- **영향 범위:** Phase 2.9′(universe 패치)·3.5(strand 재도출 — derivator 재작성)·4–5(신규 c)·7–8(tree/HTML 재생성)·신규 adapter(xlsx ingest)·P″(재-probe). 본 세션 = 무수정(엔진/SSOT/render 불변).

---

## [GAP-38] 다발(bundle) 압축 실현가능성 측정 — 57-wired `bundles=[]`는 측정 정당화된 정답 상태 + 응축은 정규화 밀도화 후 미래기능

> 기록: 2026-06-03 (Direction C — 57-wired 정직 종결[A] 준비, measure-first). **측정/기록만 — 엔진/SSOT-data/decision_tree.json 무수정.** 산출: 본 GAP + `issues/bundle_feasibility_measurement.md`(측정 상세·재현법·경계).

- **측정(falsifiable):** `spec/strands.json` 5000 strand의 c_sequence에서 contiguous 부분열 빈도 ≥ ceil(5000/10)=**500** ∧ 길이 ≥ **3** 스캔 → 임계 후보 **76개 전부 axis/backbone 층(c0200–c0213 DETECT 밴드)**(최장 `[c0200..c0210]` len12 f650, 최빈 `[c0200,c0201,c0202]` f4143). **정규화(mess)층 = 임계 공통 부분열 0개.**
- **판정:** axis/backbone 층은 **D-S3 / PROMPTS Phase 7 step 2가 "압축 금지"로 명시**("상류 axis 층: 골격이 이미 분기 구조"; Lock 5 = 다발은 *정규화 층 strand 한정*). 다발 유일 대상인 정규화 층은 임계 후보 0 → **현 57-wired에 압축할 다발이 존재하지 않는다.** ∴ `spec/decision_tree.json` `bundles=[]`는 **미룬 결함이 아니라 측정 정당화된 정답 상태**(지금 압축 강행 시 산출 0 또는 backbone 압축=D-S3 위반 — 둘 다 무익·유해).
- **원인:** (1) 정규화 mess c가 슬라이스 1–9만 구현([[GAP-30]] 백로그) → 정규화 층 sparse. (2) stratified mess sampling(K=0–6 활성결함, seed 42)이라 strand마다 활성 mess 조합 상이 → 긴 공통 정규화 run 미형성(backbone은 결정적 통과라 고빈도 공통열이 전부 backbone으로 나옴).
- **함의(미래 기능 이월):** "응축(다발)"(CLAUDE.md 목표문)은 **정규화층 밀도화(고빈도 미구현 mess c 구현 = 사용자 보류한 Direction B [[GAP-37]] 줄기) 후**에야 실현 → **step 4 이후 미래 기능으로 falsifiable 이월**(본 세션 재개 안 함). 재측정 게이트: 정규화 c 추가 시 측정 doc §5 probe 재실행 → 임계 정규화 다발 출현 시 step 2 착수(전까지 `bundles=[]` 유지가 정답).
- **[[GAP-27]]B moot:** 다발 0이므로 FORMAT↔TIMEZONE 비가환 다발 순서 문제는 현재 적용 대상 없음(moot). 정규화 밀도화로 실제 다발 출현 시 live(비가환 쌍 제외 또는 고정 canonical order — 승인 대상).
- **status:** OPEN (측정 완료 — `bundles=[]`가 현 57-wired scope 정답임을 기록; 응축은 정규화 밀도화 gated 미래 기능, deferred). **★ 2026-06-03 Phase 9 2nd cycle: §0/§1 measurement prose가 falsifiably 부정확함이 적발 → [[GAP-39]] 정정(결론 `bundles=[]`는 불변·옳음, 근거 서술만 정밀화).** [[GAP-37]](Direction B mess 확장)·[[GAP-30]](배선 백로그)·[[GAP-27]]B(비가환)·[[GAP-33]]/[[GAP-34]](decision_tree)·[[GAP-25]](render perf, collapse-by-default) 연계.
- **영향 범위:** Phase 7 step 2(다발 압축)·Phase 8(bundle-펼침 UI 먹이기)·Direction B(정규화 밀도화). 본 세션 = 무수정(엔진/SSOT-data/decision_tree.json 불변).

---

## [GAP-39] Phase 9 2nd cycle — `bundle_feasibility_measurement.md` §0/§1 measurement prose 부정확(결론 `bundles=[]`는 옳음·증거 서술만 정정)

> 기록: 2026-06-03 (Phase 9 2nd adversarial cycle, skeptical). **report-only — 엔진/SSOT-data/decision_tree.json/render 무수정.** 산출: 본 GAP + `tests/test_phase9_adversarial.py` P9-16(정확한 정당화 고정) + bundle doc §1 교정노트. cross-ref [[GAP-38]].

- **발견(falsifiable, cite-verify):** [[GAP-38]] 측정 doc §5 probe를 frozen `spec/strands.json`에 재실행 →
  임계(freq≥500∧len≥3) 후보 **76개**(count 일치). 그러나 §0/§1 서술 **"전부 axis/backbone(c0200–c0213)"** 와
  **"정규화 층 공통 부분열 0개"** 는 **부정확**: 76 中 16개가 비-backbone c 포함(c0251/c0252 routing; c0320–c0323,
  c0360–c0363 normalization). 특히 `('c0320','c0321','c0322','c0323')` freq **531** = L-4→L-5 정규화(ID_DTYPE/
  ID_LEADING_ZERO) contiguous 부분열이 임계 통과 — "정규화층 0"과 직접 모순.
- **그러나 결론 `bundles=[]`는 옳다(정밀 근거):** 다발 압축은 **57-wired tree** 대상인데 그 정규화 후보들은
  **전부 미배선**(c0320–c0323 등 4개 미배선) → tree에 부재 → 압축 불가. 완전배선 후보 70개는 backbone/axis/routing
  (D-S3 압축금지). 완전배선이며 L-4→L-5 건드리는 유일 후보 `('c0392','c0393','c0200')` = DETECT/CLASSIFY+VERIFY
  (비-transform). ∴ **완전배선 commutative-normalization-transform run = 0 ⟹ `bundles=[]` 정당**(wired scope 한정).
- **원인:** doc의 측정 scope 혼동 — §5 probe는 **5000-oracle strand**(미배선 c 포함)를 측정하는데, §0/§1은 그 결과를
  곧장 "**57-wired tree**의 정규화층 0"으로 일반화함(scope 불일치). 정확히는 "oracle엔 정규화 다발 후보가 있으나
  미배선이라 57-wired tree엔 없다 + 완전배선 후보는 backbone(압축금지) → bundles=[]".
- **분류:** **②latent 문서 정확성·정직성 결손** — 결론 옳음·증거 서술 부정확. **non-critical**(closure 미차단,
  SSOT/decision_tree 결함 0, DoD 미블록). Phase 9 적대 sweep이 "PASS라 한 곳(Direction C 산출물)"을 의심해 실제 1건을 적출한 정직 결과.
- **처분(거장 Option 1):** (1) [[GAP-38]] status에 [[GAP-39]] 정정 포인터. (2) `tests/test_phase9_adversarial.py`
  **P9-16** = bundles=[] + 완전배선 정규화-transform run 0 + 미배선 정규화 후보 ≥1 (정확한 정당화 falsifiable 고정).
  (3) `issues/bundle_feasibility_measurement.md` §1에 **날짜박은 2nd-cycle 교정노트**(커밋된 측정 문서가 falsifiably-wrong로
  남지 않게 — Direction C closure_proof 시제정정과 동성격의 사실 정정, 신규 spec 아님).
- **status:** RESOLVED (교정 기록 + P9-16 회귀가드 + bundle doc 교정노트로 닫음; `bundles=[]` 결론·decision_tree.json 불변). 미래 정규화 밀도화([[GAP-37]]/[[GAP-30]]) 시 측정 doc §5 재실행 게이트는 [[GAP-38]]에 유지.
- **영향 범위:** `issues/bundle_feasibility_measurement.md`(측정 doc 정확성) · Phase 9 DoD#5(적대 sweep 정직성 입증). 엔진/SSOT/decision_tree/render ZERO-diff.
