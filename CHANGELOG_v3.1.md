# pmx-dt 스타터팩 v3 → v3.1 CHANGELOG (review fix)

> 직전 리뷰에서 확정한 결함만 외과적으로 패치. 골격(N0–N7)·7 Locks·Phase 순서·방법론은 불변.
> frozen_universe_v4.1/4.2는 provenance라 미변경. 변경 파일: universe_sm.md, anchors.json, CLAUDE.md, PROMPTS.md, README.md.

---

## 변경 요약 (7개 fix)

| # | 결함 (직전 리뷰) | 위험도 | 조치 | 파일·위치 |
|---|---|---|---|---|
| R1 | Phase 7에서 Q-code 분기가 best-strand에 없어 tree에서 unreachable로 보임 | **구조적 최우선** | **D-S4 신설** + Phase 7 step 2.5(conditional-edge 명시 재구성) | CLAUDE 설계로그·DoD#4 / PROMPTS Phase7·9 |
| R2 | Phase 3 `모든 cell≥1`이 `b≤5000`과 논리 충돌(|V_cell|>5000) | 높음(STOP 루프) | full-cell 제약 삭제 → marginal coverage(axis-state/Q/mess dim) | PROMPTS Phase 3 Step D |
| R3 | `CATEGORICAL_PD/COUNT_PD/TTE_EVENT`·F15가 anchors=out-of-scope ↔ universe_sm=보조(모순) | 높음(reject 혼선) | universe_sm을 anchors에 맞춰 **out-of-scope 확정**, scope SSOT=anchors 명시 | universe_sm §A0·§5·§8 / anchors note |
| R4 | §6 mess dim 3개·Phase 2b noun이 controlled vocab 부재 → Phase 2.0 STOP 유발 | 중(cycle 낭비) | `COVARIATE_LAYOUT/PRE_DOSE_CODING/PLACEBO_SUBJECT` NOUN 등록 + 2b/2d intent를 등록노운으로 교정 | PROMPTS Phase 2.0·2b·2d |
| R5 | Phase 8에 다발 펼침 UI 미명세 → Q4(c 가시성) 위협 | 중 | `[7-2b]` bundle 클릭→member c inline 펼침 명시 | PROMPTS Phase 8 / CLAUDE DoD#6 |
| R6 | "모든 sc 표시"(Q5)가 D-S3(cell+경로)와 표현 충돌 | 중(기대치) | 표현 규약 명문화: tree=cell+경로, 개별 sc=경로 추적 | CLAUDE D-S3 / PROMPTS Phase 8 / README §6 |
| R7 | pilot 10~20개는 family 다양성 대비 얇음 | 낮음(권고) | 10~40개(권장 ≥20, family 가중)로 상향, gate ≥90% 유지 | PROMPTS Phase P / README §4 |

---

## D-S4 (신규 설계 결정) — 전문

> best-strand는 항상 pass 가지만 통과하므로 fail→Q-code 분기는 strand 집합에 존재하지 않는다.
> 따라서 decision tree의 to-Q 분기 구조는 strand 압축이 아니라 각 c의 `can_route_to_q` /
> `verify_visualization.fail_route_to`에서 conditional edge로 **명시 재구성**한다(Phase 7 step 2.5).
> 다발 내부 routing verify/detect c는 linear bundle 흡수 금지 → branch node로 보존.
> 고립 Q-terminal(incoming conditional edge 0)은 결함 → STOP.

이것이 v3.1의 유일한 *신규* 설계 결정이며, README §7 철학대로 동의하지 않으면 CLAUDE.md에서 D-S4만 제거하면 된다.
단, 제거 시 Phase 7에서 Q-code terminal이 dead/unreachable로 남는 문제가 부활한다.

---

## 검증 (패치 후 자동 점검 통과)

- R3: universe_sm 내 endpoint/family "보조" 표현 0건(=anchors와 통일).
- R4: §6 26개 mess dimension 전부 PROMPTS vocab으로 매핑(미매핑 0). 미등록노운 `WIDE_TO_LONG` 잔존 0.
- R2: `모든 cell≥1` 제거 확인, marginal coverage로 교체.
- R1: D-S4 참조 — CLAUDE 3곳, PROMPTS 4곳 삽입.
- anchors.json: JSON 파싱 유효.

## 의존성 (README §5) 영향

- R3/R4는 상류(universe_sm/anchors/vocabulary) → 아직 build 전이므로 하류 재실행 불필요(첫 실행에 반영).
- R1(D-S4)은 Phase 7 prompt만 보강 — strands.json/c_units 구조 불변, Phase 3.5 재실행 불필요.
- 이미 build를 진행한 상태가 아니라면(=첫 실행) 전 항목이 그냥 초기값으로 들어간다.

## 미변경 (의도적)

- 골격 N0–N7 + A0–A10, 7 Locks, TDD 디시플린, batch 정책(D-G4), cost 모델, Phase 경계.
- frozen_universe_v4.1.md / v4.2.md (provenance, read-only).
