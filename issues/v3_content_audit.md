# v3 내용 전수검토 (보고-전용) — EASY 카드 안내문 · R/Python 골격 · LLM 워크플로 best-practice

> 작성: v3 표현층 보완 세션(2026-06-04). **report-only.** spec(`c_units.json`)·엔진·V2 copy **무수정.**
> 근거는 read-only 검사(코드 `file:line` · 기존 pytest · `universe_sm`/anchors cite). 불확실은 `[UNCERTAIN]` 표기.
> 사용자 마무리 메모의 질문에 답함: "EASY 카드 안내문(① 준비 확인 → ② 쉬운 설명 → ③ 내 파일 보기/어디로 →
> ④ 🤖 LLM 복사 프롬프트 → ⑤ 참고 R·Python 골격) 내용이 틀린 데 없고, 해당 안내가 실제로 best practice인가?"

---

## 0. 검토 대상·방법
- **대상:** 122개 c-단위체의 쉬운 카드(EASY) 안내 흐름과 정본 R/Python 골격, 그리고 "LLM이 R 생성 → 정본 Python 골격으로
  검증·비교"라는 워크플로의 타당성.
- **방법:** `render/build_html_v2.py`(카드 렌더·프롬프트 생성기)와 `spec/c_units.json`(정본 122 entry) 정독 +
  기존 pytest가 무엇을 잠그는지 확인. 새 코드/실험 없음.

## 1. EASY 카드 5단 구조 — 사용자 모델과 정합 (PASS)
`renderEasyCPanel`(`build_html_v2.py:1600-1635`)이 그리는 실제 섹션은 사용자 기술과 정확히 일치한다:

| # | 섹션 제목(실제 문구) | 출처 필드 | 검토 |
|---|---|---|---|
| ① | "시작 전 — 내 데이터가 이 작업을 받을 준비가 됐는지 확인" | `precondition_checklist_ko`(체크박스) | 정본 파생·OK |
| ② | "이 작업이 무슨 일을 하나 (쉬운 말)" — 🎯goal/🧩explain/📥input/📤output/종류/근거(ref) | `_EASY_SEED`(사람 큐레이트 goal/explain/input/output) + `kind`·`ref` | OK |
| ③ | (detect/축) "보기 — 내 파일이 어디에 해당하고, 그러면 어디로 가나" / (transform) "고치기 전·후" / (그 외) "무엇을 검사·분기, 통과→/막힘→" | `verify_visualization`·`can_route_to_q`·`before_after_toy_example` | kind별 분기 정확·OK |
| ④ | "🤖 LLM에게 이대로 복사해 요청하세요 — 이 작업에 맞는 R 스크립트를 만들어 줍니다"(📋복사) | `_llm_request`(`build_html_v2.py:1283-1308`) | OK |
| ⑤ | "참고 코드 골격 (위 요청문으로 받은 R을 검증·비교할 때 — 위 R · 아래 Python)" | `r_skeleton`/`r_snippet`(위) + `python_snippet`(아래) | OK |

**판정:** 구조·순서·문구 **오류 없음.** 5단은 "준비→이해→분기→생성요청→검증"으로 논리적으로 완결적이며,
②~⑤의 본문은 사람이 큐레이트한 4필드(goal/explain/input/output)를 제외하면 전부 정본 필드에서 **결정적으로 파생**
(`build_html_v2.py:387-391` 설계 주석) → 안내문이 정본과 따로 놀 위험이 구조적으로 차단됨.

## 2. 내용 정확성 검사
### 2.1 R↔Python 골격 정합 (대체로 PASS, 실행-동치 커버리지는 부분)
- 122/122 c 모두 `python_snippet` + `r_snippet` 보유(실측). 스키마 변화는 `input_schema_delta`·`output_schema_delta`
  필드로 명시(예 `c0011`: `srp_intent="ASSIGN MDV"`, `ref="universe_sm §2 N5 …"`).
- **기존 pytest 잠금(견고):**
  - `test_simulation_realdata::test_all_python_snippets_compile` — 122 python 전부 compile.
  - `::test_all_r_snippets_parse_except_known` — 122 R 전부 **parse**(`KNOWN_R_NONPARSE=∅`).
  - `::test_python_transform_execution`·`::test_r_transform_execution` — **대표** transform(c0011 MDV, c0341 fill 등)을
    python·R 양쪽 실행 → before→after **동일** 실측.
  - `tests/test_c_units.py` — 각 c의 `postcondition_predicate`(정본에서 1글자 변경 없이 복사)로 python 동작을 잠금.
- **[정직한 커버리지 한계]** R은 122개 전부 *parse*되지만, R↔Python **실행-동치**는 *대표 소수*만 검증된다
  (`test_r_transform_execution`는 c0011·c0341만 R 실행). 즉 "⑤의 R 골격을 그대로 돌리면 Python과 같은 결과"가
  **122개 전부에 대해 자동 보장되진 않음.** 단 정본은 **Python**이고 R은 교육용 등가 표현(Lock 4)이므로 설계상 수용 가능.
  → 권고(R-9, 아래).

### 2.2 ④ LLM 요청문 — 프롬프트 품질 (PASS, best-practice 요소 다수)
`_llm_request`(`build_html_v2.py:1283-1308`)가 묶는 요소:
- `[목표]`·`[내 데이터]`·`[해야 할 일]`(srp_intent→평이어 변환)·`[분류 보기]`(states, 정확히 하나로 판정)
  ·`[막히면 보낼 질문(Q)]`(can_route_to_q 라우팅)·`[예시]`(before_after_toy_example, **few-shot**)
  ·`[결과(출력 계약)]`(output contract)·`[형식]`(dplyr/tidyr·한국어 주석·helper 정의 포함).
- **강점:** (a) 출력 계약 명시, (b) few-shot 예시, (c) **"없는 값을 새로 지어내지 마(IMPUTE 금지)"** 라는
  반-환각 지시(`build_html_v2.py:1306`) — CLAUDE.md Hallucination 차단·universe_sm IMPUTE 정책과 정합.
  (d) 분기 옵션을 "정확히 하나로 판정"하도록 강제 → 모호 silent 진행 차단(Lock 3 정합).

## 3. "LLM이 R 생성 → 정본 Python 골격으로 검증" 워크플로 — best-practice 평가
**판정: best practice에 부합**(reference-oracle 검증 + 반-환각 + falsifiable 기준), 단 아래 2개 보완 권고.

근거(왜 best practice인가):
1. **Oracle 기반 검증.** LLM 산출물(R)을 *신뢰*하지 않고, 독립적으로 큐레이트된 **정본(Python) + postcondition**과
   대조한다. 이는 LLM 코드의 표준적 검증 패턴(생성≠정답, 외부 oracle로 falsify)과 일치.
2. **Falsifiable 기준 존재.** 각 c의 `postcondition_predicate`는 통과/실패가 1줄로 판정되는 검사식(verbatim copy로
   pytest에 잠김) → "맞다고 우기기" 불가. CLAUDE.md "자기검증 대신 pytest로 검증"과 정합.
3. **반-환각 내장.** 프롬프트의 IMPUTE 금지 + 출력 계약 + 예시가 LLM이 값을 날조하거나 스키마를 벗어날 여지를 줄인다.
4. **정본 단일화(Lock 4).** R은 교육용 등가, Python이 정본. 두 스니펫의 input/output `schema_delta`가 동일하다는
   불변식이 "R 검증의 기준"을 명확히 한다.

보완 권고(이번 세션 미적용 — 표현/문서 변경은 사용자 승인 후 별도 세션):
- **R-9 (acceptance test 노출).** ⑤에 Python 골격과 함께 그 c의 **`postcondition_predicate`(합격 조건)**를 "이 조건이
  참이면 LLM의 R이 맞다"로 함께 보여주면, 사용자가 눈대중 비교가 아니라 *실행 가능한 합격 기준*으로 검증 가능 →
  oracle 워크플로가 닫힌다. (현재는 R/Python을 나란히 보여줄 뿐, 합격식 미노출.)
- **R-10 (IMPUTE-override c 주의 배지).** 일부 c는 정본 `python_snippet`을 **런타임이 의도적으로 미준수**한다
  (예: baseline median `fillna(median())` 대신 NaN 보존 + Q07로 라우팅 — `test_c_units.py:3196,3370` 문서화,
  "사용자 ★★★ 확정 IMPUTE override"). ⑤의 Python을 *문자 그대로* 복사하면 자의적 IMPUTE가 재유입될 수 있다.
  → 해당 c 카드에 "이 스니펫의 median 대입은 정책상 미준수 — NaN 보존 + Q07" 주의를 표기 권고.
  **이는 결함이 아니라**(postcondition·정책은 일관됨) *복사 사용자 오해 방지*용 안내 보완임.

## 4. 요약
- EASY 5단 구조·문구: **오류 없음.** 정본 파생으로 안내-정본 괴리 차단.
- R/Python 골격: 122/122 존재·parse, schema_delta 명시. **실행-동치는 대표 표본만 자동검증**(정직한 한계; 정본=Python).
- LLM→R→정본검증 워크플로: **best practice 부합.** 보완 2건(R-9 합격식 노출, R-10 IMPUTE-override 배지)은
  표현/문서 레벨 권고로, **사용자 승인 시 별도 세션**에서 처리(spec 무수정 원칙 유지).
- **이번 세션에서 코드/spec/copy 변경 0.** 본 문서는 발견·근거·권고 기록만.

## 5. 참조(read-only)
- `render/build_html_v2.py`: renderEasyCPanel(1600-1635) · _llm_request(1283-1308) · easy_card/EASY(1311-1326) · 설계주석(387-391).
- `spec/c_units.json`: 122 entry(필드 `srp_intent·ref·input_schema_delta·output_schema_delta·postcondition_predicate·python_snippet·r_snippet·before_after_toy_example·precondition_checklist_ko·can_route_to_q·verify_visualization`).
- `tests/test_simulation_realdata.py`: python compile/R parse/대표 transform 동치. `tests/test_c_units.py`: postcondition·IMPUTE-override(3196·3370·3548).
- 정책 근거: `CLAUDE.md`(Hallucination 차단·Lock 3·Lock 4), `universe_sm.md`(IMPUTE 정책).

---

## 6. 추가 발견 (UAT 문답 중 — 마법사 c_sequence vs 그래프 layer 표현)

### R-11 — 마법사 breadcrumb의 선형 화살표가 "순차 경로"로 오해됨 → **이번 세션에 해소(표현층)**
- **증상:** 마법사 진단 결과의 `N0 → … → c0314 → 🏁` breadcrumb가 c0314를 "🏁 직전 단계"처럼 보이게 함.
- **원인(정본):** `navigator._CANON_ORDER`는 **실행 순서가 아니라 D-S2 정규형 정렬**(≈c-id 오름차순)의 DETECT 체크리스트.
  c0314는 c-id가 커서 마지막에 올 뿐, 실제로는 `kind=detect`·`layer_pair=L-4->L-5`·`trigger="L-5 로드 직후"`인
  **최하층 검사**. navigable band 13개는 `requires_detection_by=None`(서로 독립·순서 무관).
- **조치:** `build_html_v3.py`의 v3 override에 **DOM 후처리(MutationObserver)** 추가 — `.breadcrumb`의 `.cchip`을
  `layer_pair`별 띠(L-4↔L-5 표기정규화[최하층] → L-3↔L-4 축 → …)로 재그룹(칩 이동 → V2 onclick 보존). c0314가 최상단
  최하층 띠에 들어가 🏁(맨 아래)와 분리됨. "이 목록은 실행 순서가 아님" 주석 표기. **spec/V2 무수정**(pathBreadcrumb은
  wizard IIFE private라 재대입 불가 → DOM 후처리). 테스트 `test_v3_breadcrumb_layer_banding`.

### R-12 — decision tree 그래프가 mess-layer detect→transform pass edge(c0314→c0315)를 안 그림 (report-only)
- **사실(정본):** `c0314.verify_visualization.pass_route_to = "c0315"`. c0315 = `CONVERT TIME_ANCHOR`(`kind=transform`,
  `requires_detection_by="c0314"`, `trigger="c0314 완료"`, `can_route_to_q=["Q02"]`). 즉 **DETECT→CONVERT의 D-S1 detect→fix 쌍**.
  이 관계는 c0314 detail 패널에 "pass → c0315"로 **텍스트 표시됨**(`build_html.py:739`).
- **그래프 표현:** c0314·c0315 둘 다 실 c(CUNITS 57, spec_only 아님)이며 **각각 `stage:L-4→L-5`에 `attach`로 클러스터**됨.
  `c0315→Q02`(conditional)는 그려지나, **`c0314→c0315` linear pass edge는 그래프에 없음**(직접 edge 0). `pass_route_to`는
  엣지 생성에 쓰이지 않고(패널 텍스트에만 사용) — `grep pass_route_to`는 `build_html.py:739` 1곳뿐.
- **이유:** D-S3 — Universe B(L-4→L-5 표기 정규화)는 거의 commutative라 **단일 stage 노드 클러스터**로 표현하고,
  내부 detect→transform 배선은 "다발 부착=step2 압축, 범위 밖"으로 스코프 아웃됨.
- **판정:** backbone→🏁 선로 끊김 아님(정상). 단 **mess-layer의 detect→transform 관계를 그래프가 under-represent**하는
  표현 완전성 갭(같은 층에서 conditional 엣지는 그리고 linear pass 엣지는 안 그리는 비대칭). 사용자 혼동의 정당한 근거.
- **보완 옵션(승인 시 별도 세션):** v3 **표현층에서만** `c_units.json`의 `verify_visualization.pass_route_to`를 읽어
  mess-layer(같은 layer_pair) detect→transform pass 엣지를 점선 등으로 그릴 수 있음(spec/decision_tree 무수정).
  단 그래프 topology 추가 → `flowNeighborhood` 솔리드 트랙·spec_only collapse 셋과의 상호작용 검토 필요(c0314→c0315는
  🏁로 onward 없으므로 거짓 🏁 도달은 유발 안 함; c0315→Q02만 추가 점등). **자동 적용 안 함 — 사용자 결정 대기.**
