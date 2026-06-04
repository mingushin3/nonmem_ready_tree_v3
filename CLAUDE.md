# pmx-dt — Project Rules for Claude Code (v3.1)

> Claude Code가 모든 세션 시작 시 자동으로 읽는 규칙 파일. 수정은 사용자 승인 후에만.
> 본 규칙을 임의로 완화/우회하면 즉시 STOP.
> v3.1(review fix): D-S4 추가(conditional-edge 재구성), endpoint scope·coverage·vocabulary·HTML 가시성 정합화. 상세는 CHANGELOG_v3.1.md.

---

## 프로젝트 목표

Small-molecule PK의 raw 데이터 → NONMEM-ready data wrangling 경로를 **c-단위체**로 분해하고,
공통 sub-sequence를 **다발/노드**로 응축한 **decision tree**로 수렴시킨 뒤, Cytoscape.js 단일 인터랙티브 HTML로 시각화한다.

방법론: **역방향 분해(L0→L-5) + 정방향 pytest 검증.** Hallucination을 c 단위 시점에서 falsifiable test로 차단한다.

---

## ★ v3 핵심 설계 결정 (설계 결정 로그 — 사용자 통제용)

이전 v2 대비 다음을 바꿨다. 사용자가 동의하지 않으면 해당 항목만 되돌릴 것.

- **D-S3 (Skeleton-first):** decision tree 골격을 5000 strand에서 suffix-tree로 *재발견*하지 않는다.
  골격 = `refs/universe_sm.md`의 **N0–N7 + A0–A10 routing** (이미 hand-authored). c-단위체는 이 골격의
  axis-state 전이와 하류 normalization 층에 **부착**한다. suffix-tree 압축(Phase 7)은 *normalization 층의
  다발 발견 + 경험적 strand가 골격과 일치하는지 검증*하는 보조 도구로 강등. → 비용↓, frozen reference와 증명가능 일관성↑.
  - [표현 규약 ★ Q5] tree는 5000 sc를 개별 진입노드로 그리지 않는다. backbone(N0–N7 + axis-state cell)을 그리고,
    개별 sc는 그 cell을 지나는 **경로로 위치추적**한다. "모든 sc 표시" = "모든 sc-type(cell)을 경로로 도달 가능".
- **D-S4 (Conditional-edge 재구성):** best-strand는 항상 pass 가지만 통과하므로 fail→Q-code 분기는 strand 집합에
  존재하지 않는다. 따라서 decision tree의 to-Q 분기 구조는 strand 압축이 아니라 **각 c의 `can_route_to_q` /
  `verify_visualization.fail_route_to`에서 conditional edge로 명시 재구성**한다(Phase 7 step 2.5). 다발 내부의
  routing verify/detect c는 linear bundle로 흡수하지 않고 branch node로 보존. 고립 Q-terminal(incoming conditional
  edge 0)은 결함으로 STOP. 이 규칙이 없으면 Q-code terminal이 tree에서 dead/unreachable로 보인다.
- **D-S1 (Detection-mandatory):** runtime orchestrator는 mess_profile을 모른다. 따라서 모든 fix-c의
  precondition은 **대응 DETECT/VERIFY c를 통과해야만** 성립하도록 그래프를 구성한다(detection = mandatory cut-vertex).
  이 규칙이 없으면 Phase 5의 "actual == best" 검증이 구조적으로 대량 fail한다.
- **D-S2 (Canonical c-order):** commutative한 normalization c들은 압축 전에 **c_id 오름차순 normal form**으로 정렬한다.
  bundle 안정성 확보. ordering은 도메인 분기가 아니라 정규형임을 명시.
- **D-G2 (Correctness as constraint):** best-path 선택에서 determinism·silent-error-0는 **feasibility 제약**
  (위반 경로 prune)이고, cost는 적합 경로들 사이 **tie-breaker**다. cost가 correctness를 절대 이기지 못한다.
- **D-G3 (Symbolic sc):** sc는 mess_profile만으로 symbolic하게 다룬다. 실물 fixture는 c/edge **coverage**용으로만
  수백 개 생성(5000개 전부 materialize 금지).
- **D-G1 (Anchors):** `spec/anchors.json`는 이미 제공됨. 모든 universe 인용은 이와 cite-verify.

이 두 universe를 혼동하지 말 것:
- **Universe A (routing):** N0–N7 + A0–A10. 분기/conditional의 거의 전부. (universe_sm.md §2–§5)
- **Universe B (mess):** L-5 syntactic 결함 정규화. 거의 commutative. (universe_sm.md §6)

---

## Pilot 게이트 (선행 필수)

본 CLAUDE.md는 **pilot validation 통과 후에만** build phase에 유효하다.
- `spec/pilot_validation.md`가 존재하고 "RECOMMEND: 본 build 진행"으로 끝나야 함 (PROMPTS Phase P).
- 부재 시 Claude Code는 build phase 진입을 거부하고 Phase P 실행을 요청한다.

---

## 단일 진실원천 (SSOT)

- `spec/`가 모든 canonical truth. `src/`·`tests/`는 `spec/`에서 파생.
- **spec 없는 c는 코드 금지.** 순서: spec → test → implementation.
- 사용자 지시 없이 spec 수정 금지. 필요 시 보고 후 승인 대기.

---

## Canonical Reference & Cite-verify

- `refs/universe_sm.md`: 본 프로젝트 단일 canonical reference (read-only).
- `refs/frozen_universe_v4.1.md`, `v4.2.md`: provenance only (read-only, 직접 인용 금지 — universe_sm.md 경유).
- `spec/anchors.json`: axis/state/Q-code/family 식별자 색인.
- 인용 형식: `"ref": "universe_sm §A5 ABOVE-ULOQ"`. 식별자가 anchors.json에 없으면 **reject**(hallucination 의심).
- 외부 출처는 URL + 버전 명시 시에만 허용. 출처 불명 인용 금지.

---

## 7개 잠금 조항 (The 7 Locks) — 사용자 승인 없이 변경 금지

### Lock 1 — sc 열거 (symbolic, stratified, seed 고정)
1. universe_sm.md SMALL_MOLECULE 유효 axis-state cell을 문서로부터 deterministic하게 enumerate. Frequency 추정 금지.
   - 제약: modality=SMALL_MOLECULE, endpoint_data_type ∈ scope.
   - 양립불가 조합 prune (anchors.json 기준).
2. 각 cell에 mess_profile(§6 dimension) 조합 attach (random.seed(42) 고정).
3. mess complexity strata(K=활성 결함 수)별 uniform stratified sampling, b ≤ 5000.
4. sc는 **symbolic**(mess_profile dict)으로 보관. 실물 fixture는 coverage용만(D-G3).
5. Coverage 보강: 모든 axis-state·Q-code·mess dimension이 최소 기준치 이상 등장하도록 rejection sampling.

### Lock 2 — c-단위체 granularity
SRP. 한 c는 하나의 검증 OR 하나의 변환만. LLM 코드 요청 1회분 = c 1개.

### Lock 3 — Best-path 평가 (★ D-G2: 제약 우선, 비용 후순위)
- **제약(feasibility, 위반 시 경로 무효):** ① deterministic outcome 보장 ② silent error 0.
- **비용(적합 경로 간 tie-break):** ③ 최소 c-count ④ 최소 token cost.
- 애매하면 Q-code routing (silent 진행 금지).

### Lock 4 — Semantic equivalence (Python 정본 기준)
다음 모두 충족 시 동치(alias): 같은 srp_intent(controlled vocab) + 같은 input/output schema delta + 같은 R 함수 family.

### Lock 5 — Convergence (★ D-S3: 검증 보조 도구)
골격은 N0–N7 + axis routing으로 고정. normalization 층 strand에 한해 generalized suffix tree로 다발 압축.
압축 전 commutative c는 c_id normal form 정렬(D-S2). 압축 결과가 골격과 모순되면 STOP.

### Lock 6 — HTML 스택
Cytoscape.js + dagre. 단일 HTML. localStorage persist. CDN 또는 inline. 외부 image asset 금지(SVG inline만).

### Lock 7 — Downstream highlight
클릭 c에서 upstream backtrace + downstream BFS의 union. 단일 path 짙은 노랑(`#FFD700`, 5px), conditional branch 옅은 노랑(`#FFF8B0`, 3px). 현재 위치 z-index 최상위.

---

## Detection-Mandatory 규칙 (★ D-S1)

- 모든 transform c는 자신을 trigger하는 DETECT/VERIFY c가 선행해야 한다. fix-c의 precondition은
  "mess가 존재함이 **감지된** 상태"이지 "mess가 존재함"이 아니다.
- Phase 3.5 state graph: fix-c로 가는 edge는 반드시 대응 DETECT/VERIFY node를 cut-vertex로 통과한다.
- 따라서 oracle-strand(정답 아는 경로)과 runtime-path(감지 후 경로)가 동일 c-set·동일 cost로 수렴한다.

---

## TDD 디시플린 (절대 우회 금지)

각 c-단위체:
```
1. spec/c_units.json에 entry (postcondition_predicate 필수)
2. tests/test_c_units.py에 pytest (postcondition 1글자 변경 없이 복사)
3. fixtures/intermediate/{c_id}/ 최소 3 fixture: happy / edge / trap
4. src/c_units/{c_id}_*.py 구현
5. pytest pass → tests/test_adversarial.py에 trap 추가
```
- pytest 통과 못한 c는 commit 금지. 모든 c는 silent-error trap fixture 1개 이상.

### Phase 4 batch 정책 (★ D-G4)
- 기본은 1세션 1c. 단, 같은 layer_pair · 같은 VERB family에서 **첫 c가 pass한 뒤**에는, 동일 패턴의 c를
  최대 5개까지 한 세션 batch 허용(각 c는 여전히 독립 fixture·독립 test·독립 trap 보유). 패턴이 갈리면 다시 1:1.

---

## R vs Python 역할
- 정본: Python (`src/c_units/*.py`, pytest 검증). R snippet: HTML 교육용 등가 표현(`r_snippet`).
- 두 snippet의 input/output schema delta 동일. Semantic equivalence(Lock 4) 판정은 Python 정본 기준.

---

## Phase 경계 (절대 우회 금지)
- 각 Phase = 별도 세션. **자동 다음 Phase 진행 금지.**
- 종료 보고:
```
STATUS: PHASE_N_COMPLETE | NEEDS_USER_INPUT | BLOCKED
산출물: <파일 경로>
검증 통과: <list>
미해결 ambiguity: <list>
다음 Phase 전 사용자 확인: <list>
```
- "Phase N+1로 진행" 발주 전 STOP. 현 Phase scope 외 파일 수정 금지.

---

## Definition of Done
1. **Pilot:** spec/pilot_validation.md "RECOMMEND 진행".
2. **Test green:** `pytest tests/ -v` 전부 pass.
3. **Coverage invariants:** C1 모든 c가 ≥1 strand OR Phase7 conditional-edge incoming ≥1 / C2 모든 edge traverse / C3 모든 Q-code trigger / C4 인접 c predicate implication / C5 actual_cost ≤ best_cost+ε.
4. **Skeleton consistency (D-S3):** 모든 strand가 N0–N7 골격을 모순 없이 통과(tests/test_skeleton.py). 모든 c.can_route_to_q가 decision_tree conditional edge로 표현되고 고립 Q-terminal 0(D-S4).
5. **Adversarial:** Phase 9 critical 0개 2 cycle 연속.
6. **HTML:** Chrome 최신에서 초기 fit / c 클릭 split+4섹션 / downstream highlight / localStorage persist / collapse-by-default 동시표시 노드 10초 내 렌더(5000 동시 dagre는 비요구·비실사용 worst-case, D-S3 경로표현; 근거: issues/provenance_gaps.md GAP-25) / bundle 클릭 시 member c 펼침(다발로 묶여도 c 가시성 보장).
7. **UAT:** 사용자가 임의 3 sc 클릭 시연 후 "의도대로다" 확인.
8. **No ambiguity:** spec/·CLAUDE.md·PROMPTS.md에 [AMBIGUOUS] 0개.

하나라도 미충족 → 미종료, 안정화 cycle 추가.

---

## Hallucination 차단
1. Postcondition predicate는 spec→docstring 복사 시 토큰(식별자·연산자·리터럴) 1글자 변경 금지.
   whitespace/줄바꿈/들여쓰기는 가독성 재포맷 허용(ast.parse 동치면 PASS).
2. 모든 universe 참조는 anchors.json 식별자 + universe_sm.md 섹션 명시.
3. NONMEM 동작 주장은 universe_sm.md·NONMEM 공식 문서·사용자 확인 근거.
4. "모름"은 허용, 날조 금지. 불확실하면 `[UNCERTAIN: 사유]`.
5. 임의 새 axis/state/Q-code/family 생성 금지. anchors.json에 있는 것만.
6. 자기검증 대신 pytest로 검증.

---

## 작업 격리
- 1세션 = 1c(또는 batch 정책 내) 또는 1 sub-phase. 끝나면 보고 후 STOP.
- 동일 파일 대규모 rewrite 금지. 작은 diff 권장.

---

## 디렉토리 layout
```
pmx-dt/
├── CLAUDE.md  PROMPTS.md  README.md
├── refs/      universe_sm.md  frozen_universe_v4.1.md  frozen_universe_v4.2.md
├── spec/      anchors.json  pilot_validation.md  L0_nonmem_ready.md  layers.md
│              vocabulary.md  c_units.json  mess_catalog.md  starting_conditions.json
│              q_codes.json  strands.json  closure_proof.md  decision_tree.json
├── fixtures/  starts/  intermediate/  expected/  actual/
├── src/       c_units/  orchestrator.py  postcondition_checks.py
├── tests/     test_c_units.py  test_strands.py  test_skeleton.py  test_coverage.py  test_adversarial.py
├── render/    build_html.py  index.html
└── issues/
```
