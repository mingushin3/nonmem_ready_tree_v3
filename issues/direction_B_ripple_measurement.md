# Direction B — Ripple Measurement (report-only)

> **목적:** Direction B(raw CRO deliverable 수용) + mode (b) auto-ingest 확정 후, **패치/adapter 설계 전에** B 채택이 기존 산출물에 미치는 ripple를 코드 근거로 측정. **측정만 — 설계·수정 0.**
> **방법:** 직접 source read(추측 금지). 불확정이면 "구조상 불확정"으로 정직 보고.
> baseline: HEAD 2004d27 · pytest **974 green** (본 문서 = doc-only, 불변). 무수정: spec/src/anchors/decision_tree/universe_sm.

---

## §0. 방향 + 하드 선결 2건 (요약)

- **Direction B:** 입력 가정을 "이미-tabular/analyte-wide" → "raw CRO/bioanalytical deliverable(다중시트·QA혼재·subject-wide·inline-BLQ)"로 확장. **전임상 전용 아님** — 임상 분석실 raw도 동일. fork 축 = "진입점이 얼마나 raw인가".
- **mode (b) auto-ingest:** 실물 xlsx → 출발점 자동 detect + 이유 부착 → tree navigate(실사용).
- **하드 선결 2건(= [[GAP-37]]):** (A) INTRASHEET_QA_BLOCK §6 무·NOUN 무·FILTER flag-only 미커버. (B) subject-as-column wide — c0120=analyte-wide 미일치.

## §1. ripple 측정 — additive vs 재도출 (M1–M3, 코드 근거)

**M1 — `generate_sc.py` 신규 mess dim 추가 = membership reshuffle (additive 아님).**
- 단일 `random.Random(42)`(L443)를 `sample_cell`(L66–70, rejection)·`sample_mess_profile`(L73, `rng.sample(base_dims,k)` L76)·`derive_harmonization`(L102)·`derive_terminal`(rng.random ×5 L173/177/179/183/193)가 **위치 순서대로** 소비.
- budget **고정 5000**(`STRATA_BUDGET` L28, `sum=5000` L29), sc_id **위치 기반** `sc_{counter:04d}`(L460), `assert len(MESS_DIMENSIONS)==28`(L26), `base_dims=MESS_DIMENSIONS[:26]`(L74).
- `inject_for_coverage`: dim coverage `<5`(L236)면 K2 stratum sc를 **교체**(`scs[best_idx]=sc` L332).
- ∴ 신규 dim을 (LEGACY/RWD처럼 L82–90) rng.random으로 특수처리 → **rng 스트림 시프트 → 삽입점 이후 전 sc의 cell/mess/terminal 변동**. rng 무소비로 넣어도 coverage<5 → **≥5 sc 교체**. 위치 sc_id이므로 sc_0000…4999가 다른 내용으로 remap. → **(b) 전면 재도출.**
- additive(0000–4999 동결 + 5000+ append) = **현 코드 미지원**. 가능하려면: budget 증액 + inject 이후 별도 rng로 append + 신규 dim coverage 사전 시드 — **의도적 생성기 재설계**.

**M2 — strand derivator 부재 (★ 최대 ripple, B와 독립).**
- airtight: `grep strands\.json --include=*.py | (write_text|json.dump|open …'w')` → **0건**. 24개 언급 전부 reader(build_decision_tree·tests·render·orchestrator·route-c).
- Phase 3.5(state graph + feasibility filter + layered Dijkstra + `second_best_cost`/`alternative_paths_count`)를 만드는 스크립트가 **repo에 없음**. `spec/strands.json`(5000, c_sequence/terminal/cost/layer_trace/second_best) = 재실행 불가 committed artifact.
- ∴ strand가 바뀌면(재셔플이든 additive append든) **derivator를 먼저 재작성**해야 함. orchestrator는 주어진 c_sequence를 *실행/검증*만 — best-strand *도출* 불가.

**M3 — `build_decision_tree.py` = strands에서 자동 재생성(결정론), c-node는 수동 동기.**
- anchors/c_units/q_codes/strands read-only(L29–32), `PURE_COUNT`/`SCOPEOUT`를 strands에서 계산(L85–96), `"DETERMINISTIC; 재실행 시 동일"`(L249), `spec/decision_tree.json` write(L272).
- 단 `WIRED`(57) 하드코딩(L39–51) + `test_decision_tree.py`가 `REGISTRY==WIRED` 강제 → 신규 c는 **WIRED+REGISTRY 양쪽 수동 편집**. Phase 8 `build_html.py`가 tree 소비 → HTML도 재생성.

**측정 결론(§1):** 자연 패치 = **(b) 전면 재도출**(starting_conditions→[derivator 재작성]→strands→decision_tree→HTML) + Phase 4–9 재순환(milestone 235/439·scope_out 0·Q02=388/Q12=397·pure 3228 등 strand-파생 assertion 전부 재계산). additive append는 **derivator 재작성(M2) + 생성기 재설계(M1)** 선결 시에만 가능. → **strand-layer 재현성(M2)이 B 전체의 게이팅 의존.**

## §2. adapter "contained" 확인 (M4–M5)

**M4 — 성립(단서부): engine 무변경 front-end.**
- `dispatch(c_id, df, meta)`(L213), `run_strand(c_sequence, df, meta=None)`(L229), D-S1 `meta.get(f"{req}_ran")`(L222). L16: 런타임은 "mess_profile을 모른 채 DETECT 결과로만" 도달.
- `mess_profile`은 sc(symbolic) 전용 — 엔진 미소비. ∴ adapter = xlsx→df+초기 meta→DETECT c 실행. dispatch/run_strand **무변경**.
- **단서:** contained = "엔진 재작성 불요"일 뿐. adapter는 여전히 (a) xlsx ingester(미존재, pilot §6 L-5 추출 미구현), (b) 초기 meta(sheet_inventory 등) 빌더, (c) 신규 front-half c(QA/subject-wide) 존재+배선 필요.

**M5 — 성립: reason single-source.**
- detect/verify 62 중 `verify_visualization.criterion_predicate_ko` **60/62**, `ref` **62/62**(예 c0001 criterion_ko + `ref=universe_sm §2 N1-N4, L0_nonmem_ready.md §A`).
- ∴ mode (b) "출발점 자동 detect + 이유 부착"의 reason = 각 DETECT c의 criterion_predicate_ko(사람가독) + ref(provenance)로 단일출처 재사용. (criterion_ko 결손 2건 = minor.)

## §3. Direction B 로드맵 비용표 (측정, 설계 아님)

| 단계 | 내용 | 신규 산출(추정) | 게이팅 의존 |
|---|---|---|---|
| **2.9′** universe 패치 | §6 신규 dim(QA/subject-wide/inline-BLQ) + axis sub-state(sparse) + anchors NOUN/axis + 신규 c spec | 신규 c ≈ QA 3 · subject-wide PIVOT 1–2 · inline-BLQ 1 · sparse 2 (= 7–8c) | 사용자 승인 spec-change(cite-verify) |
| **3.5** strand 재도출 | sc 재열거 + best-strand 재도출 | — | **★ derivator 재작성(M2)** — 부재 |
| **4** TDD 구현 | 신규 c (test/fixture/impl/trap) + 기존 accepted+unwired Batch C/D/E(c0100-02·c0110/11/20/61/70·c0030-41 = 27c 백로그) | ~7–8 신규 + 27 backlog | 3.5(strand으로 C1 검증) |
| **5** orchestrator 배선·검증 | REGISTRY 배선 + skeleton/coverage(C1–C5) | — | 4 |
| **7** tree 재생성 | `build_decision_tree.py` 재실행(자동) + WIRED 동기(수동) | — | 5(REGISTRY) |
| **8** HTML 재생성 | `build_html.py` 재실행 | — | 7 |
| **adapter**(별 line) | xlsx ingester + 초기 meta 빌더 + reason 부착(M5) | front-end 모듈(엔진 무변경, M4) | (c) 신규 c 존재 시 사거리↑; Tier 0은 불요 |
| **P″** 재-probe | 3 실물 파일 재통과(drop-point 해소 falsify) | — | adapter |
| **9** adversarial | 재순환 review | — | 전체 |

**비용 핵심:** (1) **M2(derivator 부재)가 3.5 이후 전부의 선결** — Direction B의 가장 큰 단일 비용. (2) 자연 패치 시 기존 5000 strand·milestone·strand-파생 test 전면 재순환(M1). (3) adapter는 엔진 contained(M4)지만 ingester+초기meta가 신규.

## §4. 최소 착수 단위 (all-or-nothing 아님 — navigate 사거리 사다리)

| Tier | 추가물 | 실물 "넣고 navigate" 도달 범위 | 패치/reshuffle |
|---|---|---|---|
| **Tier 0** (★ 최소) | adapter만(xlsx→df+초기meta + wired DETECT c 실행 + gap-reason) | 자동 출발점 detect → **현 57-wired 백본 navigate** → 첫 미지원 구조에서 **이유 붙여 정직 정지**(예 "QA-block 감지·미배선") | **불요**(M4 contained·M2/M1 무관) |
| **Tier A** | +QA 패치+배선 | step2(QA제거) 통과 → PIVOT gap 도달 | 패치+strand |
| **Tier B** | +subject-wide 패치+배선 | step3(wide→long) 통과 → JOIN gap | 패치+strand |
| **Tier C/D** | +JOIN/UNIT(c0110/11/20/61 accepted backlog) | step4(dose/BW JOIN) 통과 → BLQ/dose-event(기배선 step5~8) | strand(배선) |
| **Full** | +inline-BLQ +sparse | 전임상 lineage 전구간 navigate | 패치+strand |

**∴ 최소 단위 = Tier 0 adapter** — universe 패치/strand 재도출 **불요**로 즉시 부분효용(자동 detect + 이유 + 백본 navigate + 정직한 경계 정지). 이후 각 Tier가 navigate 사거리를 **점증 확장**(첫 미지원 경계를 뒤로 밀기). Tier A+ 만이 §1 reshuffle/§2 derivator 비용을 유발.

## §5. 다음 (측정 결과 → 제안서)

1. **(선결, B 전체)** Phase 3.5 strand derivator **재작성**(M2) — strand 변경의 게이팅 의존. *제안서 대상.*
2. **(즉효, 독립)** Tier 0 adapter 제안서 — 패치/reshuffle 불요 first 실사용. *제안서 대상.*
3. **(주력)** 2.9′ 패치(QA/subject-wide/inline-BLQ/sparse) + Batch C/D/E 배선 제안서 — additive append 가능 여부는 1 이후 재판정. *제안서 대상.*
- 본 세션 = **측정 종료**. 패치/adapter **설계·수정 0**. 제안서는 별도 세션(사용자 승인).

**경계(정직):** 측정은 generate_sc.py·build_decision_tree.py·orchestrator.py·c_units.json 직접 read 기반. M1/M2/M3/M4/M5 전부 코드 근거 단정(불확정 0). 비용표 신규-c 수치는 **추정 sizing**(설계 아님). pilot probe = n=3 등급(일반화 아님, [[GAP-37]]·pilot §5 경계 계승).
