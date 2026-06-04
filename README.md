# pmx-dt 스타터 팩 — 사용 가이드

Claude Code로 small-molecule data-wrangling decision tree를 빌드하기 위한 운영 매뉴얼.

> 스타터팩 v3.1 (review fix 반영 — CHANGELOG_v3.1.md 참조).

---

## 0. 폴더 준비 (한 번만)

```
pmx-dt/
├── CLAUDE.md          ← 그대로
├── PROMPTS.md         ← 그대로
├── README.md          ← 이 파일
├── refs/
│   ├── universe_sm.md            ← canonical (제공됨)
│   ├── frozen_universe_v4.1.md   ← 본인 파일 복사 (provenance)
│   └── frozen_universe_v4.2.md   ← 본인 파일 복사 (provenance)
└── spec/
    └── anchors.json   ← 제공됨 (cite-verify 색인)
```

1. 이 5개 파일을 위 구조대로 배치. `refs/`에 v4.1/v4.2 원본도 복사해 둔다(인용은 universe_sm.md 경유, 원본은 추적용).
2. `cd pmx-dt && git init && git add -A && git commit -m "starter pack"`.
3. 같은 폴더에서 `claude` 실행. Claude Code가 세션마다 CLAUDE.md를 자동으로 읽는다.

---

## 1. 작업 원칙 (외우기)

- **1 Phase = 1 세션.** Phase 끝 `STATUS: ..._COMPLETE` 뜨면 `/exit` → git commit → 새 세션.
- **자동 진행 없음.** 다음 Phase는 본인이 명시 발주("Phase N+1로 진행")해야 시작.
- **STOP·NEEDS_USER_INPUT를 신뢰.** Claude가 멈추고 물으면 그게 정상. 밀어붙이지 말 것.
- **self-check 결과만 믿지 말 것.** 매 Phase 후 spec/ 파일을 직접 열어 본인이 검토.

---

## 2. 세션별 발주 방법

각 세션은 딱 두 줄로 시작한다.

```
[새 셸] cd pmx-dt && claude
[Claude에게] PROMPTS.md의 Phase __ 블록을 그대로 붙여넣기
```

Phase 4(c 구현)만 예외: 블록 안 `__[c_id]__`에 실제 대상을 채운다.
```
PROMPTS.md Phase 4를 수행하라. 작업 대상 c_id: c0001
```
batch가 허용되면(같은 layer_pair·VERB family, 첫 c pass 후):
```
PROMPTS.md Phase 4를 batch로 수행하라. 대상: c0010..c0014 (모두 NORMALIZE 계열)
```

---

## 3. 전체 진행 순서 (체크리스트)

| 단계 | Phase | 세션 수 | 산출물 |
|---|---|---|---|
| ☐ | **P 파일럿** | 1+1 | pilot_validation.md (★ 통과해야 build 진입) |
| ☐ | 0 L0 freeze | 1 | L0_nonmem_ready.md |
| ☐ | 1 layers | 1 | layers.md |
| ☐ | 2.0 vocabulary | 1 | vocabulary.md |
| ☐ | 2a–2d c 열거 | 4 | c_units.json (초안) |
| ☐ | 2.9 mess closure | 1+ | mess_catalog.md, c_units.json(보강) |
| ☐ | 3 sc (symbolic) | 1 | starting_conditions.json, q_codes.json |
| ☐ | 3.5 best-strand | 1 | strands.json, strands_stats.md |
| ☐ | 3.9 closure | 1 | closure_proof.md |
| ☐ | 4 TDD 구현 | **N (batch로 단축)** | src/c_units/*, tests/* |
| ☐ | 5 orchestrator | 1 | orchestrator.py, test_strands/skeleton/coverage |
| ☐ | 6 merge | 1 | c_units.json(alias) |
| ☐ | 7 tree assembly | 1+ | decision_tree.json |
| ☐ | 8 HTML | 1 | render/index.html |
| ☐ | 9 adversarial | 1+ | issues/* |

**Phase 4의 N**: Phase 3.5의 c usage frequency 높은 순으로 진행. batch 정책으로 보통 c 수의 1/3~1/2 세션이면 끝난다.

**render 산출물 2종** (표현층만 다름 — 같은 spec, 같은 엔진/SSOT):

| 파일 | 생성기 | 용도 |
|---|---|---|
| `render/index.html` | `render/build_html.py` | **정본/전문가 뷰.** Lock 6/7 규약·코드(axis/state/Q/srp_intent) 그대로. DoD 검증 대상. |
| `render/index_v2.html` | `render/build_html_v2.py` | **쉬운 설명 뷰(UAT 피드백 반영).** 대학 1학년 수준 풀이 + 코드 배지·hover 용어집, 색을 **진한 앰버(자동 기본 경로)+청록 점선(질문 Q 갈림길)** 으로 교체, **‘🔍 내 파일 진단’ 마법사**(src/adapter 정본 1:1 미러). |

`build_html_v2.py`는 `build_html.py` 데이터층을 import해 재사용하고, 진단 마법사 판정 상수는 `src/adapter`에서 직접 import한다(drift 불가). `tests/test_render_v2.py`가 마법사 판정 == `src.adapter.ingest()` 임을 검증한다. spec/엔진/`index.html`/Lock7/CLAUDE.md는 **무변경(report-only)**.

---

## 4. 파일럿을 반드시 먼저 (왜)

universe_sm.md가 "웬만한 raw file을 잡는가"의 **유일한 경험적 답**은 Phase P다.
본인이 실제로 받아본 데이터(익명/합성) 10~40개(권장 ≥20, study family 골고루)의 fingerprint를 pilot_validation.md 템플릿에 적고, 각각이 합리적 terminal로 라우팅되는지 센다.

- **≥90% 깔끔(예: 18/20)** → build 진행. 자신감의 근거가 생김.
- **미만** → miss가 곧 universe 패치 타깃. universe_sm.md를 보강(승인 후)하고 anchors.json 갱신한 뒤 재실행.

이 게이트를 건너뛰면 5000 sc·수백 c를 다 만든 뒤에야 "실무 file이 안 잡힌다"를 발견하게 된다.

---

## 5. 의존성 주의 (재실행 트리거)

spec은 위에서 아래로 파생된다. 상류가 바뀌면 하류 재실행:

```
universe_sm.md/anchors.json  →  vocabulary  →  c_units  →  strands(3.5)  →  orchestrator(5)  →  tree(7)  →  html(8)
```

- **c_units 변경**(Phase 2.9에서 c 추가 등) → Phase 3.5 재실행 → 5 재검증 → 7 재압축.
- **universe_sm 패치**(파일럿 miss 반영) → anchors.json 갱신 → vocabulary부터 점검.

작은 변경이면 해당 Phase만, 골격(N0–N7)·vocabulary 변경이면 전 구간 재점검.

---

## 6. 이상 신호 대응

| 증상 | 의심 | 대응 |
|---|---|---|
| Phase 5 best-path 대량 mismatch | 3.5 graph의 detection 모델링(D-S1) | trigger_condition 말고 requires_detection_by/graph 점검 |
| Phase 7 dual fixed-point 안 멈춤 / Δ<0 | commutative c ordering(D-S2) | c_id normal form 정렬 확인 |
| "이 식별자 anchors.json에 없음" reject | hallucination 차단 정상 작동 | universe_sm에 실제 있는지 확인, 없으면 만들지 말 것 |
| Phase 8 "5000 sc 개별 진입노드가 안 보임" | Q5 표현 규약 오해 | 정상(D-S3): tree는 cell+경로로 표현, 개별 sc는 경로 추적, 다발은 펼쳐 c 확인 |
| Phase 7 "Q-code terminal이 unreachable" | conditional edge 재구성 누락(D-S4) | can_route_to_q→conditional edge inject 확인(Phase 7 step 2.5) |
| C_dead 다수 | sample 누락 or 무의미 c | Phase 3.9 옵션(제거/sc추가/유지) 본인 결정 |

별도 검증이 필요하면 새 세션에서: `Phase N의 X 부분이 의심된다. spec/Y.json을 열어 Z를 검증하라.`

---

## 7. 설계 결정 되돌리기

CLAUDE.md "v3 핵심 설계 결정"의 D-S1~D-G3는 이전 진단 기반의 변경이다. 동의하지 않는 항목이 있으면
해당 D-코드만 CLAUDE.md에서 제거/수정하면 된다. 특히:
- **D-S3(skeleton-first)** 를 빼고 순수 bottom-up suffix-tree 재발견으로 가고 싶다면 → Phase 7 step 1(골격 채택)을
  제거하고 v2 방식 suffix-tree 1차 도출로 교체. 단 S1/S2 문제는 그대로 남으니 권하지 않음.
