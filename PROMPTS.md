# PROMPTS.md v3.1 — Phase별 발주 prompt

> 각 Phase = 별도 Claude Code 세션. 새 세션: 프로젝트 root에서 `claude` → 해당 Phase 블록 복사-붙여넣기.
> 종료: `STATUS: PHASE_*_COMPLETE` 확인 → `/exit` → `git commit -am "PHASE_N complete"`.
> **Phase 순서:** P → 0 → 1 → 2.0 → 2a 2b 2c 2d → 2.9 → 3 → 3.5 → 3.9 → 4(×N, batch) → 5 → 6 → 7 → 8 → 9

---

## Phase P — Pilot fingerprint (★ build 진입 게이트, 가장 먼저)

```
역할: pilot validator. 목표: build 착수 전에 universe_sm.md가 실무 raw file을 실제로 잡는지 경험 검증.

자료: refs/universe_sm.md, spec/anchors.json.

작업:
1. 사용자에게 실제 받아본 raw file(익명/합성) 10~40개(권장 ≥20, study family가 골고루 분포하도록 가중)의 "fingerprint"를 요청한다.
   각 fingerprint = {study design, 파일 구조, 시간형식, BLQ 표기, dose 위치, covariate layout, 알려진 결함}.
   사용자가 직접 기재하도록 spec/pilot_validation.md에 템플릿 표를 먼저 생성하고 STOP.
2. (사용자 입력 후 재개) 각 fingerprint를 손으로 A0 → N0–N7 + Mess Catalog에 통과시켜:
   - 도달 terminal(AUTO/REPAIR/구체 Q-code)
   - 어느 axis-state·mess dimension에 매핑되는지
   - 매핑 실패(어디에도 못 앉힘) 여부
3. 집계: clean-route 비율. miss는 어떤 패치가 필요한지(어느 axis/Q-code/mess) 명시.
4. 판정: clean-route ≥ 90%(18/20)이면 "RECOMMEND: 본 build 진행".
   미만이면 miss 목록을 universe_sm.md 패치 후보로 보고하고 "HOLD: universe 보강 필요".

규칙: universe_sm.md 수정 금지(보강은 사용자 승인 후 별도). src/·tests/ 작성 금지.

종료 보고:
STATUS: PHASE_P_COMPLETE | NEEDS_USER_INPUT
clean-route: <X/N>
miss 목록 + 패치 후보: <list>
판정: RECOMMEND 진행 | HOLD
```

---

## Phase 0 — Spec freeze (L0)

```
역할: SSOT 작성자. 목표: spec/L0_nonmem_ready.md 1개만 작성.
CLAUDE.md·universe_sm.md·anchors.json은 읽고 self-check만(수정 금지).

작업: NONMEM-ready dataset(SMALL_MOLECULE PK)의 formal spec. 각 항목 binary 판정 가능한 술어로.
A. Column schema: ID/TIME/DV/MDV/EVID/AMT/CMT/RATE/ADDL/II/covariate/BLQ flag/LLOQ — name,type,range,ordering,missing,format.
B. Cross-column invariants: AMT≠NA⟹EVID∈{1,4}; EVID=0⟹DV def & AMT==NA; EVID=1⟹AMT>0 & CMT def;
   TIME asc within ID; ADDL>0⟹II>0; RATE>0⟹AMT>0; MDV=1⟹DV ignored; 기타 표준.
C. Sorting: ID asc → TIME asc → EVID tiebreak(dose before obs at same time).
D. Encoding/format: CSV/comma, period decimal, no comma in numeric, UTF-8 no BOM, header, LF|CRLF.
E. 모호 항목 [AMBIGUOUS: 사유] 태그, STOP.

규칙: src/tests/render/fixtures 금지. spec/ 내 L0_nonmem_ready.md 외 금지.
각 invariant마다 universe_sm 섹션 인용(예: "universe_sm §1 terminal", anchors.json 검증).

self-check: 이 문서만으로 임의 dataset의 NONMEM-ready 여부 binary 판정 가능? 모호 0개?
종료: STATUS: PHASE_0_COMPLETE | NEEDS_USER_INPUT / 산출물 / self-check / 모호점
```

---

## Phase 1 — Backward layer 분해 (bisection 명시)

```
역할: backward layer decomposer. 목표: spec/layers.md. L0→L-5 5개 layer의 entry_pre/exit_post를 formal predicate로.

★ 이등분 원칙(D-S3): L-3을 Universe A/B 경계로 명시.
- L-3 이상(상류): axis 평가 가능 → N0–N7 routing 영역(분기 다수).
- L-3 이하(하류): mess normalization 영역(거의 commutative).

Layer:
L-1  NONMEM 특수컬럼 부여 직전. 표준 long-format event table. dose/obs 의미 명확.
L-2  Tidy long-format. one event/row, one variable/column. NONMEM 컬럼 의식 없음.
L-3  ★경계★ 모든 mess 해소, A0–A10 axis가 deterministic하게 evaluate됨.
L-4  Normalization 완료(NA/단위/시간형식/ID타입 통일), axis 평가는 아직 불가.
L-5  Raw mess. universe_sm §6 모든 dimension union.

각 layer: Entry precondition / Exit postcondition / Violations & lower-layer routing.
추가: 인접 layer transition table. L0.entry_pre == L-1.exit_post 등 인접쌍 동일성 확인.

규칙: c 정의 금지, sc 열거 금지. spec/layers.md 외 금지.
종료: STATUS: PHASE_1_COMPLETE / self-check / 모호 경계
```

---

## Phase 2.0 — Controlled vocabulary

```
역할: vocabulary curator. 목표: spec/vocabulary.md.

A. VERBS(13, 추가 금지): ASSIGN VERIFY CONVERT NORMALIZE JOIN SPLIT PIVOT FILTER DETECT PROPAGATE CLASSIFY EXTRACT ROUTE.
   ★IMPUTE 제외(임의 결측보충 금지 — FLAG 후 정책 결정). ★FILTER=조건부 FLAG, row 삭제 금지.
B. NOUNS(카테고리별 fixed):
   NONMEM_COLUMN: ID TIME DV MDV EVID AMT CMT RATE ADDL II
   MESS_CONCEPT: BLQ_TOKEN NA_TOKEN TIME_FORMAT TIME_ANCHOR TIMEZONE ID_DTYPE ID_LEADING_ZERO
     MERGED_CELL MULTI_LEVEL_HEADER TRAILING_BLANK NATURAL_LANGUAGE_DOSE NATURAL_LANGUAGE_TIME
     FREETEXT_COMMENT DUPLICATE_ROW EXCEL_FORMULA EXCEL_DATE_SERIAL NON_ASCII_DECIMAL
     LINEBREAK_IN_CELL SCIENTIFIC_NOTATION ABOVE_ULOQ REPLICATE_OBS
     COVARIATE_LAYOUT PRE_DOSE_CODING PLACEBO_SUBJECT
   DOMAIN_ENTITY: DOSE_SHEET COVARIATE_SHEET ANALYTE_COLUMN BASELINE_COVARIATE
     TIME_VARYING_COVARIATE METABOLITE PARENT_DRUG OCCASION REGIMEN_DESCRIPTOR
   FILE_PROPERTY: ENCODING FILE_FORMAT SHEET_INVENTORY BOM LINE_ENDING DELIMITER
   UNIT_PROPERTY: UNIT_DECLARATION UNIT_CONSISTENCY UNIT_CANONICAL MOLAR_MASS
   SCHEMA_PROPERTY: COLUMN_SCHEMA ROW_ORDERING ROW_LEVEL_INVARIANT CROSS_COLUMN_INVARIANT
   ★새 NOUN 필요 시 STOP+보고.
C. MODIFIERS("BY {X}"): WITHIN_ID WITHIN_OCCASION WITHIN_ANALYTE ACROSS_SHEET ACROSS_FILE PER_SUBJECT PER_VISIT.

srp_intent 규칙: "{VERB} {NOUN}" 또는 "{VERB} {NOUN} BY {MOD}". 전부 대문자+underscore. 한글/자유서술 ZERO.
c_name_ko는 별개(사람가독 라벨, 자유).

규칙: spec/vocabulary.md 외 금지.
종료: STATUS: PHASE_2_0_COMPLETE / VERB 13 / NOUN count / 결정 필요사항
```

---

## Phase 2 — c-단위체 backward enumeration (skeleton-attached)

> 4개 sub-session 2a→2b→2c→2d. 공통 schema는 아래.

### [공통 schema] spec/c_units.json entry
```json
{
  "c_id": "c0001",
  "c_name_ko": "EVID 부여",
  "srp_intent": "ASSIGN EVID",
  "layer_pair": "L-1->L-2",
  "kind": "transform | verify | detect",
  "cost": 2,
  "requires_detection_by": "c00XX",   // ★ D-S1: 이 fix를 trigger하는 DETECT/VERIFY c. detect/verify면 null.
  "llm_prompt": "이 c를 정의하는 LLM 요청 원문(Identity Card)",
  "input_schema_delta": "...", "output_schema_delta": "...",
  "precondition_predicate": "Python bool expr (★ detection 통과 상태 포함)",
  "postcondition_predicate": "Python bool expr (pytest로 그대로)",
  "precondition_checklist_ko": ["3-7 평이한 한글 체크"],
  "r_snippet": "<=15줄 + 일타강사 주석", "python_snippet": "<=15줄 + 주석",
  "trigger_condition": "어떤 DETECT 결과에서 호출되는가",
  "can_route_to_q": ["Q01"],
  "skeleton_hook": "이 c가 붙는 골격 위치 (예: 'A5->N5 transition' | 'mess:NA_TOKEN' )",  // ★ D-S3
  "verify_visualization": { "target_columns":[], "criterion_predicate_ko":"", "pass_route_to":"", "fail_route_to":"Q01" }, // kind=verify/detect 필수
  "before_after_toy_example": { "before":"mini CSV", "after":"mini CSV(변경셀 표시)" },
  "ref": "universe_sm §A5 ABOVE-ULOQ"
}
```
cost: VERIFY/DETECT 1 · ASSIGN/NORMALIZE/CONVERT 2 · PROPAGATE/CLASSIFY 3 · SPLIT/JOIN/PIVOT 4–5 · EXTRACT 5–7 · 도메인추론 6–8 · ROUTE 0.
★ 모든 transform c는 requires_detection_by 필수(D-S1). detection 없는 transform은 reject.

### Phase 2a — L-1↔L-2 (NONMEM 특수컬럼)
```
역할: c enumerator 2a. 범위: L-1↔L-2만. [공통 schema] 적용.
후보(추가 가능): ASSIGN EVID / ASSIGN MDV / ASSIGN RATE / ASSIGN CMT / CONVERT ADDL FROM REPEATED_ROWS /
  ASSIGN ADDL / ASSIGN II / VERIFY ROW_ORDERING WITHIN_ID / ASSIGN ROW_ORDERING / VERIFY CROSS_COLUMN_INVARIANT.
self-check: 모든 c postcond 합 ⊇ L-1 entry_pre? 각 c precond가 직전 postcond로 충족? vocab 위반 0? 
  transform c 전부 requires_detection_by 有? cost 有?
종료: STATUS: PHASE_2A_COMPLETE / 신규 c / vocab위반(0) / self-check
```
### Phase 2b — L-2↔L-3 (구조 변형)
```
범위 L-2↔L-3. 후보: PIVOT ANALYTE_COLUMN / JOIN DOSE_SHEET / PIVOT COVARIATE_LAYOUT /
  ASSIGN BASELINE_COVARIATE / ASSIGN TIME_VARYING_COVARIATE / JOIN ACROSS_SHEET /
  VERIFY ANALYTE_COLUMN / VERIFY DOSE_SHEET JOIN_KEY. [규칙·종료 2a 동일, PHASE_2B]
```
### Phase 2c — L-3↔L-4 (axis evaluator = DETECT c)
```
범위 L-3↔L-4. ★ 각 axis 평가 c는 universe_sm A0–A10을 1:1 매핑(명칭 변경 금지, anchors.json 검증).
이들은 대부분 kind=detect/verify이며, 하류 fix-c들의 requires_detection_by 대상이 된다(D-S1).
예: DETECT TIME_FORMAT / VERIFY TIME_ANCHOR(→Q02) / VERIFY BLQ_TOKEN / VERIFY LLOQ_VALUE(→Q01) /
  VERIFY UNIT_DECLARATION(→Q10) / CLASSIFY COVARIATE / CLASSIFY ANALYTE_COLUMN /
  DETECT ABOVE_ULOQ(→Q01.uloq) / DETECT REPLICATE_OBS(→Q01.replicate).
[규칙·종료 2a 동일, PHASE_2C]
```
### Phase 2d — L-4↔L-5 (mess normalization, 1차)
```
범위 L-4↔L-5. universe_sm §6 dimension별 NORMALIZE/CONVERT/EXTRACT/PROPAGATE fix-c + 각자의 DETECT 짝.
군: NA정규화 / 셀구조(MERGED forward-fill, MULTI_LEVEL_HEADER, TRAILING_BLANK, DUPLICATE_ROW flag) /
  자연어(EXTRACT DOSE·TIME, SPLIT FREETEXT) / ID(CONVERT ID_DTYPE, NORMALIZE ID_LEADING_ZERO) /
  단위(CONVERT UNIT_CANONICAL, MOLAR_MASS) / 시간(CONVERT TIME_FORMAT, NORMALIZE TIMEZONE) /
  dose(JOIN DOSE_SHEET) / covariate(PIVOT COVARIATE_LAYOUT) / 파일(DETECT/CONVERT ENCODING, BOM, LINE_ENDING) /
  Excel(FORMULA, DATE_SERIAL, NON_ASCII_DECIMAL, SCIENTIFIC_NOTATION, LINEBREAK) /
  catch-all(ROUTE TO_Q15X IF UNKNOWN_MESS_PATTERN).
추가 self-check: universe_sm §6 모든 dimension이 어느 c/Q-code로 매핑되는지 표. 미매핑 1개라도 → STOP.
[규칙·종료 2a 동일, PHASE_2D]
```

---

## Phase 2.9 — Mess catalog closure (Universe B 관문)

```
역할: mess catalog closer. 목표: spec/mess_catalog.md (pattern × handling_c|Q-code 매핑, 100% cover).

작업:
1. universe_sm §6 + A9/A10 결함 state를 모두 pattern으로 전개.
2. Excel/CSV 산업 표준 결함(cp949/BOM/CRLF/delimiter/formula/serial/한국식 소수점/scientific) 점검.
3. 사용자 실무 결함(과거 의뢰사 raw에서 "처음 본" 패턴) 질문으로 수집.
4. 미커버 pattern → 신규 c append(기존 c_id 변경 금지, vocab 준수, requires_detection_by 필수).
5. closure: 모든 pattern이 c / Q-code / Q15X 중 하나로 100% routing. 미커버 0.

규칙: c_units.json append만. 새 VERB/NOUN 필요 시 STOP. mess_catalog.md 외 금지.
종료: STATUS: PHASE_2_9_COMPLETE | NEEDS_USER_INPUT / pattern 수 / 신규 c / 미커버(0) / confirm 요청
```

---

## Phase 3 — sc symbolic stratified enumeration (★ D-G3)

```
역할: sc enumerator(symbolic). 목표: spec/starting_conditions.json + spec/q_codes.json.

1. q_codes.json: universe_sm §4 SM Q-code(Q01–Q15D + Q15X, subtypes 포함) 추출.
   각 Q: name / trigger_condition / clarification_to_sponsor[] / human_decision_point /
   recover_to_c_id / routing_cost / human_effort_score(1-10) / ref.
   routing_cost: 단순 clarification 20 / 추가데이터 50 / protocol 결정 100 / 둘다 200 / Q15X 500.
2. starting_conditions.json (★symbolic — mess_profile dict만, 실물 CSV 생성 안 함):
   Step A. anchors.json SM 유효 axis-state cell V_cell 도출(양립불가 prune).
   Step B. mess strata K=활성 결함 수.
   Step C. budget(b=5000): K0 100 / K1 1000 / K2 1500 / K3 1200 / K4 700 / K5 400 / K6+ 100.
   Step D. within-stratum uniform sampling(seed 42), coverage 제약(모든 mess dimension≥5, 모든 Q-code≥3,
           모든 axis-state[A0..A10 각 state]≥1; ★full-cell 전수 제약 아님 — |V_cell|>b 가능, marginal coverage만)
           rejection sampling으로 충족.
   Step E. sc schema: {sc_id, stratum, v42_cell{A0..A10}, mess_profile{§6 dimensions}, expected_terminal, expected_q_code}.
   ★ expected_path 두지 말 것(Phase 3.5 Dijkstra가 도출).
3. ★ coverage용 실물 fixture만 별도 생성: 모든 c·edge·Q를 최소 1회 exercise하는 최소 sc 부분집합(수백 개)을
   fixtures/starts/에 합성(1-comp exponential, mess_profile instantiate, cp949 등 실제 인코딩). 실제환자 데이터 금지.

규칙: src/tests 금지. anchors.json 외 식별자 금지. expected_path 금지.
종료: STATUS: PHASE_3_COMPLETE / b / strata 분포 / 실물 fixture 수 / Q·cell·dimension coverage(미달 0)
```

---

## Phase 3.5 — Backward best-strand (★ D-S1 detection-mandatory + D-G2 constraint-first)

```
역할: best-strand derivator. 목표: spec/strands.json + spec/strands_stats.md.

1. State graph:
   - node: sc(source) / L0(sink) / 각 Q-code(terminal) / 각 c postcondition state / layer 경계.
   - edge: c별 precond→postcond, weight=cost. ROUTE c: 현 state→Q-code, weight=Q.routing_cost.
   - ★ D-S1: fix-c로 가는 edge는 대응 DETECT/VERIFY node를 cut-vertex로 통과해야만 존재.
     (requires_detection_by가 가리키는 c를 거치지 않으면 fix-c precondition 미성립.)
2. ★ D-G2: 경로 탐색은 2단계.
   (a) feasibility filter: deterministic·silent-error-0 위반 경로 prune.
   (b) 남은 적합 경로 중 layered Dijkstra로 최소 cost. tie-break: c_id 사전식(canonical, D-S2).
3. 각 sc: cost-optimal path P_sc 도출. c_sequence / terminal / total_cost / cost_breakdown / layer_trace /
   alternative_paths_count / second_best_cost. 도달 path 0개면 STOP(c 누락 의심).
4. closure check: C_used ⊆ C_all. C_dead(미사용 c) 보고. 누락 c 발견 시 STOP→Phase 2.9 재발주.
5. strands_stats.md: terminal 분포 / cost histogram / c usage frequency top·bottom20 / layer별 평균 c.

규칙: strands.json·strands_stats.md 외 금지. c_units.json 수정 금지.
self-check: b개 strand 도출? C_used⊆C_all? 인접 c predicate implication? 각 fix-c 앞에 detection c 존재(D-S1)?
종료: STATUS: PHASE_3_5_COMPLETE | NEEDS_USER_INPUT / strand 수 / terminal 분포 / C_dead / 누락 c / implication 위반 / detection-precede 위반
```

---

## Phase 3.9 — c-set closure verification

```
역할: closure verifier. 목표: spec/closure_proof.md.
1. 모든 strand의 모든 c_id ∈ c_units.json? 인접 쌍 predicate implication? dead c 0?
2. ★ 모든 transform c가 strand 내에서 detection c 뒤에 옴(D-S1)?
3. C_dead 처리 옵션(제거/sc추가/유지)을 사용자에게 보고(결정권 없음).
4. closure_proof.md: 위 invariant를 true/false 결정 술어로 기록.
규칙: 검증 전용, spec 수정 금지. 위반 시 STOP+보고.
종료: STATUS: PHASE_3_9_COMPLETE | NEEDS_USER_INPUT / closure / C_dead / 누락 c / 위반 쌍 / 결정 필요
```

---

## Phase 4 — TDD c 구현 (★ batch 정책 D-G4)

```
역할: TDD implementer. ★ 작업 대상 c_id 또는 batch: __[명시, 예: c0001 또는 c0010..c0014]__

순서(엄격): 
1. c_units.json entry 읽기(postcond/precond/cost/srp_intent/requires_detection_by).
2. tests/test_c_units.py에 test_{c_id}: docstring=c_name_ko + postcond 1글자 변경없이 복사 + srp_intent.
   assertion: fixture에 c 적용 결과가 postcond 만족. happy/edge/trap 최소 3 case.
   kind∈{verify,detect}: verify_visualization pass/fail routing도 assert.
3. fixtures/intermediate/{c_id}/ happy·edge·trap in/expected. trap=silently 통과 시 잘못된 c.
4. pytest -k {c_id} → fail 확인.
5. src/c_units/{c_id}_*.py 구현(docstring=srp_intent+c_name_ko+postcond 복사). R 등가 idiom 가깝게.
6. pytest pass까지. 7. test_adversarial.py에 trap 추가. 8. 전체 pytest green.

batch 규칙(CLAUDE.md D-G4): 같은 layer_pair·VERB family에서 첫 c pass 후 최대 5개 동일패턴 batch. 패턴 갈리면 1:1.
규칙: spec 수정 금지(필요 시 STOP+보고). pytest pass 후 STOP.
종료: STATUS: PHASE_4_{c_id}_COMPLETE / fixture 수 / pytest / trap 추가 / 다음 c 권장(usage freq 순)
```

---

## Phase 5 — Orchestrator + skeleton + best-path 검증

```
역할: orchestrator + verifier (★ DECISION-D2 지배: Phase 4/5 family-슬라이스 interleave). 전제: strands.json 존재 + 대상 슬라이스 family의 transform c + 그 detection 생산자 구현 완료(전체 c 구현 불요). 각 슬라이스 = ① 해당 family c 구현 → ② 그 family를 지나는 strand 부분집합으로 orchestrator 실행 + coverage(C1–C3) + skeleton(D-S3/D-S4) 검증 → ③ 부분 tree 렌더·점검. 임시 fixture는 슬라이스 밖으로 넘기지 않음(영구 stub 금지).
(아래 step 1–5는 슬라이스의 strand 부분집합에 적용. 미구현 c 호출 시 NotImplementedError로 슬라이스 경계를 명시.)

1. src/orchestrator.py: 입력 sc/fixture → (terminal, actual_c_sequence, total_cost).
   ★ trigger_condition(=DETECT 결과)으로 순차 호출(runtime는 mess_profile 모름, D-S1 그대로 반영).
   c_units.json에 없는 c 호출 → NotImplementedError. 경로 fixtures/actual/sc_{id}_path.json 기록.
2. tests/test_strands.py:
   - assert terminal == expected_terminal.
   - assert actual_c_sequence == strands.json[sc].c_sequence (또는 actual_cost == best_cost, tie 동률).
   - ★ best-path mismatch가 다수면 routing 결함 아니라 3.5 graph의 detection 모델링 의심(D-S1) → 보고.
3. tests/test_skeleton.py (★ D-S3): 모든 sc의 actual 경로가 universe_sm N0–N7 골격을 모순없이 통과.
   (각 transition이 골격 노드 순서를 위반하지 않음.)
4. tests/test_coverage.py: C1 dead c / C2 edge / C3 Q / C4 implication / C5 cost-optimal(랜덤100, ≤best+1).
5. pytest green까지.
규칙: spec 수정은 보고 후. 새 c 금지. 어느 invariant fail이면 STOP.
종료: STATUS: PHASE_5_COMPLETE / terminal 일치율 / best-path 일치율 / skeleton 통과 / C1-C5 / drift
```

---

## Phase 6 — Semantic equivalence merge

```
역할: merger. 목표: 중복 c alias 처리.
1. 동치(Lock 4): 같은 srp_intent + 같은 in/out schema delta + 같은 R 함수 family. 모호 시 비동치(보수적).
2. canonical = 그룹 내 최소 c_id. alias 필드 기록. alias entry는 canonical_of로 유지(삭제 금지).
3. orchestrator alias→canonical redirect. strands.json c_sequence alias 치환, cost 재계산(다르면 STOP).
4. 전체 pytest green 유지.
종료: STATUS: PHASE_6_COMPLETE / merge 전·후 c 수 / alias 그룹 / 모호 case / pytest
```

---

## Phase 7 — Decision tree assembly (★ D-S3: 골격 채택 + suffix-tree는 검증)

```
역할: tree assembler. 목표: spec/decision_tree.json.

1. 골격 채택: universe_sm N0–N7 + A0–A10 routing을 tree backbone으로 직접 import.
   각 axis-state 전이 = conditional node, terminal(AUTO/REPAIR/Q-code) = terminal node.
2. c 부착: 각 c의 skeleton_hook으로 backbone에 매단다.
   - 하류 mess 층: commutative c는 c_id normal form 정렬(D-S2) 후 generalized suffix tree로 다발 압축.
     빈도 ≥ ceil(b/10), 길이 ≥ 3. longest common substring iterative 추출 = bundle.
   - 상류 axis 층: 압축하지 않음(골격이 이미 분기 구조).
2.5 ★ D-S4 conditional-edge 재구성: best-strand는 pass 가지만 통과 → fail→Q 분기는 strand 집합에 없다.
   각 c의 can_route_to_q / verify_visualization.fail_route_to를 backbone에 conditional edge로 명시 inject.
   다발 내부 verify/detect c가 fail_route_to를 가지면 linear bundle 흡수 금지 — branch node로 보존(다발은 앞뒤 분할).
   모든 Q-terminal은 ≥1 conditional edge incoming(고립 Q-terminal 금지).
3. node/edge/bundle/conditional_routing JSON 산출(branch/merge/conditional/terminal type). conditional edge는 2.5 산출.
4. ★ 검증(재발견 아님): 압축된 tree로 orchestrator 재배선 후 test_strands.py + test_skeleton.py 재실행.
   모든 sc 동일 terminal·동일 cost·골격 무모순. 깨지면 STOP.
   또한 모든 can_route_to_q가 conditional edge로 존재 + 고립 Q-terminal 0(D-S4). 위반 시 STOP.
5. 안정화: normalization 층 bundle에 한해 Δnodes==0 ∧ Δbundle_length==0까지 반복.
   Δbundle_length<0(분해 중)이면 이상신호 STOP.

규칙: c_units.json 수정·새 c 금지. 골격 모순 시 STOP.
종료: STATUS: PHASE_7_COMPLETE / node·bundle 수 / total_bundle_length / iteration / 골격 무모순(PASS) / terminal·cost 동일성 / conditional-edge 재구성(D-S4 PASS) / 고립 Q-terminal(0)
```

---

## Phase 8 — HTML 렌더 (Lock 6/7, universe_sm 7-1~7-4)

```
역할: HTML renderer. 목표: render/build_html.py → render/index.html(단일).
자료: decision_tree.json / c_units.json(canonical) / q_codes.json / strands.json.
스택: Cytoscape.js + dagre(CDN), 단일 HTML, localStorage, 외부 image 금지(SVG inline).

[7-1] 초기: 전체 fit default. view toggle [전체|Family]. 노드 type별 모양:
  transform=원 / verify·detect=원+dashed / branch=다이아 / merge=둥근사각 / conditional=육각 /
  terminal NONMEM=별 / terminal Q-code=빨강사각.
[7-2] 클릭: 좌:우 1:1 split. 좌 tree fit. 현재 위치 outline 3px + 대비 + 1Hz pulse(절대 안 가려짐).
  full-strand: upstream backtrace BFS + downstream BFS union 노랑(단일 #FFD700/5px, conditional #FFF8B0/3px).
[7-2b] bundle 클릭(★ Q4): bundle은 collapse-by-default(5000 perf). 클릭 시 좌측 trim에서 member c sequence를
  inline 펼침(expand/collapse 명시 affordance). 우측은 bundle 내 첫 c의 4섹션 + "이 다발의 c 목록" 네비.
  → 다발로 묶여도 모든 member c는 항상 도달·표시 가능.
[표현 규약 ★ Q5/D-S3] tree는 5000 sc를 개별 진입노드로 그리지 않는다. backbone(N0–N7 + axis-state cell)을
  그리고 개별 sc는 해당 cell 경로로 위치추적. "모든 c 표시"는 c_units 전수 + bundle 펼침으로 보장.
[7-3] c 클릭 우측 4섹션: (A) precondition_checklist_ko 체크박스(모두체크→"위치 확인됨")
  (B) Identity: c_name_ko + srp_intent(mono) + llm_prompt 박스 + c_id
  (C) kind=transform: before/after mini table 변경셀 강조. kind∈{verify,detect}: verify_visualization
      (target_columns / criterion_predicate_ko / pass→next / fail→Q-code 빨강).
  (D) R snippet(상)+Python snippet(하), 일타강사 주석 인라인.
[7-4] Q-code terminal 클릭: (A')도달사유(conditional_routings to=Q 매칭) (B')clarification_to_sponsor
  (C')human_decision_point (D')recover_to_c_id 복귀.
[노드 클릭] branch/merge/conditional 3섹션 N1 역할 / N2 분기·병합 정보 / N3 영향 strand 수.
추가 UI: 미니맵 / view toggle / breadcrumb / zoom. localStorage key "pmx_dt_state", corruption graceful fallback.
스타일: 색맹 친화(노랑+stroke pattern), 한글 시스템폰트, 영문 식별자 그대로, 5000노드 virtual culling.

검증: 초기 전체fit / toggle / c클릭 split+4섹션 / verify_visualization / 노드 3섹션 / bundle 클릭 member c 펼침 /
  full-strand upstream+downstream / localStorage / Q-code A'~D'.
종료: STATUS: PHASE_8_COMPLETE / index.html KB / self-check / 호환성
```

---

## Phase 9 — Adversarial review (mode: skeptical)

```
역할: adversarial reviewer. ★ 산출물이 옳다고 가정 금지. weakness 발굴이 목적.
자료: 모든 spec/src/tests/render/fixtures.

점검(발견은 issues/issue_{NN}_{slug}.md에 기록, 직접 수정 금지):
A. c_units: postcond too loose / srp_intent vocab위반·SRP위반 / snippet 안돌아감 / llm_prompt 모호 /
   checklist 모호 / before_after 비현실 / cost 부적절 / verify_visualization 누락 /
   ★ requires_detection_by 누락·잘못된 detect 지정(D-S1).
B. starting_conditions: 비현실 sc / expected_terminal 어긋남 / mess 조합 inconsistent / strata 비율 어긋남.
C. strands: best보다 cheap한 path 존재 / 인접 implication 위반 / layer 잘못 통과 / dead·missing c /
   ★ fix-c 앞 detection 누락(D-S1).
D. decision_tree: unreachable edge / dead end / conditional 비배타 / incoming disjoint cover 실패 /
   ★ 골격(N0–N7) 모순(D-S3) / dual fixed-point 미도달 / ★ can_route_to_q 누락 conditional edge·고립 Q-terminal(D-S4).
E. src: 구현≠postcond / 미정의 c 호출 / silent exception / NaN·Inf·empty 미처리 / actual≠best.
F. tests: trap trivially detect / assertion too weak / parametrize 누락.
G. html: 5000 freeze / 색맹 구분불가 / localStorage fallback 없음 / full-strand upstream 누락 / toggle state 불일치.
H. 일관성: c_units↔src 누락 / Q-code 미참조 / CLAUDE·universe_sm↔구현 mismatch / vocab NOUN 과잉 / mess pattern 미등장 /
   ★ anchors.json에 없는 식별자 인용(G1).

규칙: "별 문제 없음" 불가. 최소 5개 issue. 
종료: STATUS: PHASE_9_COMPLETE / issue 수 / 우선순위 분포 / critical 3개 / 다음: critical 해결 mini-cycle
```

---

## Phase 9 이후 — Critical issue mini-cycle
```
역할: issue resolver. ★ 대상: __[issue_NN]__. 
1. 정독 2. 권장 수정(spec이면 SSOT 순서 spec→test→구현, 승인 후) 3. 회귀방지 pytest 추가
4. 전체 pytest green 5. issues/resolved/ 이동, commit에 issue_NN 명시.
규칙: 지정 issue 외 금지. 1세션 1 issue.
```
