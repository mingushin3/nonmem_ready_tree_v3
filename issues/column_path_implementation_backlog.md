# Column-path 구현 백로그 — 173 → 467 → 5000 도달 지도 (living)

> **목적:** Phase 5 full-integration 완주(완료 strand 수)를 끝까지 끌어올리는 데 필요한 **신규 c 구현**을
> family/layer별 coherent batch(≤5)로 분해하고, 각 묶음이 완주 strand를 얼마나 올리는지 누적 곡선으로 고정한다.
> 이후 ~6–7개 column-path 슬라이스(+ mess까지면 ~13)가 이 지도를 따라간다.
> **위상:** `spec/strands.json` + REGISTRY에서 **파생한 측정 뷰**(SSOT는 strands.json). 수치는
> `tests/test_integration_slice7b.py`가 falsifiable하게 고정한다. **갱신:** 슬라이스 종료마다 하단 규약대로.
> **기준 시점:** 2026-06-01 · slice 7b(GAP-29 정규화 + 프런티어 측정) 후. (완주 439는 slice 9 Batch B 기준; 본 백로그 곡선 유효.)
> **직교 노트(2026-06-03):** Phase 7 step 1~2.6(decision_tree.json 골격 + 결정 A·B)는 **이 백로그와 직교**다 — run_strand 무변경·① 비의존이라 완주 strand(439)·realized(88) 불변. 결정 A(c0252 INFUSION→Q04 spec-change)·결정 B(terminal_routing INVALID)도 tree 구조/spec 변경일 뿐 신규 c 구현이 아니라 완주 곡선 무영향. 본 백로그(신규 c 구현→완주↑)와 Phase 7(tree 구조·D-S4 edge)은 별개 축. [[GAP-33]]/[[GAP-34]] 참조.

---

## 1. 프런티어 사실 (왜 이 백로그가 필요한가)

slice 7a가 backbone 46c를 배선해 완주 strand 173을 만들었다. **7b 발주 전제는 "미배선-구현 c를 더
배선해 467로 올린다"였으나, read-only 측정으로 반증됐다:**

- 구현 파일(src/c_units/*.py) **46** = REGISTRY 배선 **46** → **미배선-구현 c = 0**. wiring 천장 = 173.
- 467 완주에 필요한 상류 c는 **전부 미구현**(spec/c_units.json엔 entry, src엔 파일 부재).
- 측정 확정(재현: `test_upstream27_yields_467` / `test_all73_blockers_yield_5000`):

| 마일스톤 | 추가 구현 c | 완주 strand |
|---|---|---|
| slice 7a/7b 배선 | — | 173 |
| slice 8 = Batch A 6 ROUTE | L-3→L-4 ROUTE 6 (c0250/c0252/c0254/c0255/c0256/c0257) | 353 ✅실측 |
| **현재(slice 9 = Batch B 5 DET/VER)** | L-3→L-4 DETECT/VERIFY 5 (c0211/c0212/c0214/c0215/c0216) | **439** ✅실측 |
| + 남은 상류 column-path 16c | L-1→L-2 4 + L-2→L-3 12 (L-3→L-4 전부 완성) | **467** |
| + mess L-4→L-5 46c | 정규화/탐지 잔여 | **5000** (전수) |

- missing-c-per-strand 분포: 정확히 1개 missing 254 strand · 2개 535 · 3개 716 · … (long tail) — 즉 대부분
  strand가 2개 이상 미구현 상류 c를 동시에 필요로 한다(conjunctive).

➡ **"467 column-path 완주"는 배선이 아니라 신규 구현 과제다.** batch≤5 규율상 1세션 불가. DECISION-D2
  (미구현 c를 Phase 5 슬라이스로 발주하는 패턴)를 column-path로 확장해 아래 묶음으로 진행한다.

---

## 2. 누적 로드맵 (build order = 레버리지 + D-S1)

완주는 strand의 **모든** c가 배선돼야 일어난다(conjunctive). 아래는 검증된 누적 곡선:

| 배치 | c (kind/layer) | 신규수 | 누적 완주 | Δ | 비고 |
|---|---|---|---|---|---|
| **A1** ✅ | c0250 c0252 (ROUTE, L-3→L-4) | 2 | **312** ✅실측 | +139 | **slice 8 완료**. c0250 74·c0252 65 sole-blocker. axis req_det 기배선. ★ c0252 INFUSION-STOP-RESTART→Q04 = GAP-31 ✅RESOLVED(결정 A: INFUSION→Q04, [[GAP-34]]). |
| **A2** ✅ | c0254 c0255 c0256 c0257 (ROUTE, L-3→L-4) | 4 | **353** ✅실측 | +41 | **slice 8 완료**. 同 VERB(ROUTE), axis req_det 기배선. c0257 Q03 4-state = c0251 선례 clean. |
| **B** ✅ | c0211 c0212 c0214 c0215 c0216 (DET/VER, L-3→L-4) | 5 | **439** ✅실측 | +86 | **slice 9 완료**. req_det None. detect/verify(중간 c)→완주 path +86, Batch B c 종착 0. df-default: c0214→Q10(fail, [[GAP-32]]); 나머지 4 pass-through. ① 실현 0 추가(40 starve + 46 axis-None=c0210). ★ L-3→L-4 층 전부 완성(6 ROUTE + 5 DET/VER = 11). |
| **C1** | c0100 c0101 c0102 (VERIFY sheet, L-2→L-3) | 3 | 439 | +0 | req_det None. ★ 단독 완주 0(아래 ‡ 꼬리). |
| **C2** | c0130 c0131 c0150 c0160 (CLASSIFY/VERIFY, L-2→L-3) | 4 | 439 | +0 | req_det None. |
| **D** | c0110 c0111 c0120 c0161 c0170 (TF/ROUTE, L-2→L-3) | 5 | 439 | +0 | req_det ∈ C(c0100/c0101/c0102/c0160) → **C 먼저**. |
| **E** | c0030 c0031 c0040 c0041 (L-1→L-2) | 4 | **467** | +28 | c0031 req_det c0030(同 배치 내 순서). ‡ 꼬리 실현. |

‡ **co-dependent 꼬리(439→467, 28 strand):** C·D·E는 *단독 추가 시 완주 0*이고, 셋이 **모두** 배선돼야
마지막 28 strand가 완주한다(이들이 L-2→L-3 컬럼 + L-1→L-2 컬럼 부여를 함께 통과). 즉 A·B는 독립 고레버리지
(173→439 = 467 증가분의 ~76%), C·D·E는 한 묶음으로 끝내야 값이 나오는 꼬리. **권장 순서: A1 → A2 → B →
(C1+C2+D+E를 연속 슬라이스로) .** 최종 27c 전수 = 467(검증 OK).

---

## 3. 상류 27c 전수 (spec 존재, src 부재 — 구현 대상)

각 c는 TDD 5단계(c_units.json entry 읽기 → test → happy/edge/trap fixture → impl → adversarial trap).
postcondition_predicate는 spec→docstring 1글자 변경 금지(Hallucination 차단 #1). `req_det_wired`=구현 시
D-S1 게이트가 이미 충족되는지(배선된 detection이 선행 보장되는지).

### L-3→L-4 (11c) — 최우선(ROUTE는 axis req_det 기배선)
| c | srp_intent | kind | req_det | req_det_wired |
|---|---|---|---|---|
| c0250 ✅slice8 | ROUTE COLUMN_SCHEMA | route | c0200 | ✅ |
| c0252 ✅slice8 | ROUTE AMT | route | c0204 | ✅ (GAP-31 ✅RESOLVED 결정 A: INFUSION→Q04) |
| c0254 ✅slice8 | ROUTE COVARIATE_LAYOUT | route | c0207 | ✅ |
| c0255 ✅slice8 | ROUTE ANALYTE_COLUMN | route | c0208 | ✅ |
| c0256 ✅slice8 | ROUTE CROSS_COLUMN_INVARIANT | route | c0209 | ✅ |
| c0257 ✅slice8 | ROUTE ROW_ORDERING | route | c0206 | ✅ (Q03 4-state c0251 선례) |
| c0211 ✅slice9 | DETECT ABOVE_ULOQ | detect | None | ✅ (sub-flag; runtime Q01 라우터=c0253) |
| c0212 ✅slice9 | DETECT REPLICATE_OBS | detect | None | ✅ (sub-flag; runtime Q01 라우터=c0253) |
| c0214 ✅slice9 | VERIFY UNIT_DECLARATION | verify | None | ✅ (df-default=fail→Q10, GAP-32; runtime 미실현) |
| c0215 ✅slice9 | DETECT DUPLICATE_ROW | detect | None | ✅ (A9 helper, no Q) |
| c0216 ✅slice9 | DETECT ENCODING | detect | None | ✅ (A9 helper, no Q) |

### L-2→L-3 (12c) — DET/VER 먼저, TF/ROUTE 뒤(req_det 의존)
| c | srp_intent | kind | req_det | req_det_wired |
|---|---|---|---|---|
| c0100 | VERIFY DOSE_SHEET | verify | None | — |
| c0101 | VERIFY COVARIATE_SHEET | verify | None | — |
| c0102 | VERIFY ANALYTE_COLUMN | verify | None | — |
| c0130 | CLASSIFY ANALYTE_COLUMN | detect | None | — |
| c0131 | CLASSIFY METABOLITE | detect | None | — |
| c0150 | CLASSIFY REGIMEN_DESCRIPTOR | detect | None | — |
| c0160 | VERIFY UNIT_CONSISTENCY | verify | None | — |
| c0110 | JOIN DOSE_SHEET BY ACROSS_SHEET | transform | c0100 | ⛔(C 먼저) |
| c0111 | JOIN COVARIATE_SHEET BY ACROSS_SHEET | transform | c0101 | ⛔(C 먼저) |
| c0120 | PIVOT ANALYTE_COLUMN | transform | c0102 | ⛔(C 먼저) |
| c0161 | CONVERT UNIT_CANONICAL | transform | c0160 | ⛔(C 먼저) |
| c0170 | ROUTE CROSS_COLUMN_INVARIANT | route | c0160 | ⛔(C 먼저) |

### L-1→L-2 (4c)
| c | srp_intent | kind | req_det | req_det_wired |
|---|---|---|---|---|
| c0030 | VERIFY ROW_ORDERING BY WITHIN_ID | verify | None | — |
| c0040 | VERIFY ROW_LEVEL_INVARIANT | verify | None | — |
| c0041 | VERIFY CROSS_COLUMN_INVARIANT | verify | None | — |
| c0031 | ASSIGN ROW_ORDERING | transform | c0030 | ⛔(c0030 먼저, 同 배치) |

---

## 4. 467 → 5000 잔여 (mess L-4→L-5 46c) — 별개 후속

VERB 분포: DETECT 24 · NORMALIZE 9 · CONVERT 5 · EXTRACT 2 · SPLIT 2 · FILTER 2 · ROUTE 1 · VERIFY 1.
slice 1–6이 다룬 mess 패턴(MERGED/TIME/TIMEZONE/COVARIATE/PLACEBO/BLQ)의 **나머지 dimension**.
column-path 27c(467) 완료 후 별도 백로그로 전개. 본 문서는 467까지를 1차 범위로 둔다.

---

## 5. ★ 범위 경계 — 27c가 해소하지 *않는* 것 (①/②와 분리)

27c 구현은 완주 **경로**만 연다. 다음은 27c 후에도 **잔존하는 별개 결손**이며 다른 Phase가 흡수한다:

- **① 외부 meta 주입 규약(GAP-4/6/7/9/10/11/12/14):** ROUTE/axis c가 기대 Q/terminal을 실현하려면 외부
  축-state meta가 필요. 미주입 시 default INVALID 오라우팅. slice 8(Batch A)에서 A0/A4 df-default=fail로 88 실현
  (부분 falsify), slice 9(Batch B)는 실현 0 추가(40 starve + 46 axis-None) → 완주 439 중 88 실현. full-orchestrator
  통합 시 1회 설계. ← `test_terminal_realization_partial_post_batch_a`(7b) + slice 8/9 하네스로 측정 고정.
- **② Phase 7 D-S4 conditional/terminal edge(GAP-13 잔여; ✅결정 A·B로 GAP-5/8/31 RESOLVE·GAP-12 Phase7-facet, [[GAP-34]]):** axis evaluator 종착 strand(현 114; slice 9가 c0210 종착 +46)·
  fail-branch는 best-strand에 없어 tree 조립 시 conditional edge로 재구성(고립 Q-terminal 0). ★ 27c 중 축
  DETECT/VERIFY(Batch B)는 ②의 population을 늘린다(해소 아님). ← `test_d_s4_axis_terminal_grows_to_114_post_batch_b`(7b).

즉 **완주 467 ≠ terminal 467 실현.** 27c(경로) → ①(실현) → ②(tree 구조)는 직교한 세 축이다.

---

## 갱신 규약 (living)
슬라이스 종료마다: 1) 구현·배선 완료한 c 행에 ✅(slice N) 표기 + §2 누적표의 해당 마일스톤 실측 갱신.
2) 완주 strand 실측을 `tests/test_integration_slice7b.py` 상수와 동기화(불일치 시 테스트가 SSOT).
3) §1 프런티어 표 재산출(완주 수 이동). 4) provenance_gaps.md(GAP 원장)·phase_settlement_checklist.md와
교차 동기화(원장 우선). 5) 467 도달 시 §4 mess 백로그로 범위 확장.

> 이력: 2026-06-01 slice 7b 최초 작성(GAP-29 정규화 후 프런티어 측정). 구현 0(측정·문서만). [[GAP-30]] 근거.
> 2026-06-01 slice 8 = **Batch A 완료**(c0250/c0252/c0254/c0255/c0256/c0257 6 ROUTE 신규 구현+배선). 완주 173→**353**(A1 312 + A2 353, 실측=예측). 남은 column-path = 21 upstream(L-1→L-2 4 + L-2→L-3 12 + L-3→L-4 5). pytest 806→866 green. 신규 [[GAP-31]](c0252 INFUSION-STOP-RESTART→Q04 ∉ postcond, postcond-faithful INVALID). [[GAP-30]] ① 영향 노트 갱신(empty meta로 88 실현 — A0/A4 df-default=fail). 다음 = Batch B(c0211/c0212/c0214/c0215/c0216, DET/VER, req_det None → 신규 detection, 353→439).
> 2026-06-02 slice 9 = **Batch B 완료**(c0211/c0212/c0214/c0215/c0216 5 DETECT/VERIFY 신규 구현+배선). 완주 353→**439**(+86, 실측=예측). L-3→L-4 층 전부 완성(6 ROUTE + 5 DET/VER = 11) → 남은 column-path = 16 upstream(L-1→L-2 4 + L-2→L-3 12). pytest 866→**917** green(+51). detect/verify(중간 c)라 완주 path만 +86·Batch B c 종착 0. 신규 [[GAP-32]](c0214 df-default=fail→Q10, c0213 scope-out와 정반대; Q10 ROUTE c 부재라 runtime 미실현 ②). [[GAP-30]] ① 영향 노트 갱신(Batch B 실현 0 추가 = 40 starve + 46 axis-None; ② axis-only 종착 68→114). 다음 = **Batch C(co-dependent 꼬리 439→467)**: C1(c0100/c0101/c0102)+C2(c0130/c0131/c0150/c0160)+D(c0110/c0111/c0120/c0161/c0170)+E(c0030/c0031/c0040/c0041) — C·D·E는 단독 완주 0, 셋 다 배선돼야 마지막 28 strand 완주(연속 슬라이스 필요).
