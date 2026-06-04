# 다발(bundle) 압축 실현가능성 측정 — 57-wired scope (read-only, report-only)

> **추적성 스탬프:** engine/SSOT baseline **2004d27** (frozen, ZERO-diff) · 측정 코드/spec 무수정 ·
> 본 문서 = doc/measurement only, **미커밋**. (direction_B_ripple_measurement.md 양식 계승.)
> **목적:** "최선의 최종 decision tree HTML"의 핵심 구성요건인 **응축(다발/노드)** 이 현 산출물에 부재
> (`spec/decision_tree.json` `bundles=[]`)한 것이 *결함인가 정답인가* 를 측정으로 판정. Phase 7 step 2
> (다발 압축) 착수 전 measure-first 게이트.
> **방법:** `spec/strands.json`(5000 best-strand) c_sequence에서 contiguous 부분열 빈도 스캔(openpyxl 무관, 순수 read).

---

## §0. 측정 결과 (실측)

- **입력:** 5000 strand. c_sequence 길이 min 2 / max 54 / mean 15.0.
- **다발 임계(PROMPTS Phase 7 step 2 / Lock 5):** 빈도 ≥ `ceil(b/10)` = `ceil(5000/10)` = **500** ∧ 길이 ≥ **3**.
- **임계 통과 후보: 76개 — 전부 axis/backbone 층(c0200–c0213 DETECT 밴드).**

| 종류 | 예시 부분열 | 빈도 |
|---|---|---|
| 최장(len 12) | `c0200 c0201 c0202 c0213 c0203 c0204 c0205 c0206 c0207 c0208 c0209 c0210` | 650 |
| 최빈(len 3) | `c0200 c0201 c0202` | 4143 |
| 중간(len 6) | `c0200 c0201 c0202 c0213 c0203 c0204` | 2831 |

- **정규화(mess/normalization) 층:** 빈도 ≥ 500 ∧ 길이 ≥ 3 공통 부분열 **0개**.
  (mess c — c0020/c0021·c0300계열·c0305/c0306·c0312/c0313·c0340/c0341·c0350/c0351·c0374/c0375·
  c0380/c0381·c0390–c0393 등 — 은 임계 다발 후보 어디에도 등장하지 않음.)

---

## §1. 판정 — `bundles=[]`는 결함이 아니라 측정 정당화된 정답 상태

- 임계를 넘는 76 후보가 **전부 c0200–c0213 = N0–N7 + A0–A10 axis/backbone 층**이다. 이 층은
  **D-S3 / PROMPTS Phase 7 step 2가 "압축하지 않음"으로 명시**한 곳이다("상류 axis 층: 골격이 이미
  분기 구조"; Lock 5 = 다발 압축은 *normalization 층 strand에 한해*).
- **다발 압축의 유일 대상인 정규화 층은 임계 공통 부분열이 0개**다. → 현 57-wired scope에서 압축할
  정규화 다발이 **존재하지 않는다.**
- ∴ `spec/decision_tree.json`의 `bundles=[]`는 **미룬 결함이 아니라 측정으로 정당화되는 정답 상태**다.
  지금 step 2 압축을 강행하면 (a) 산출 0(정규화 후보 없음), 또는 (b) 금지된 backbone을 압축(D-S3 위반)
  — 둘 다 무익·유해. **measure-first가 "지금 다발은 무익"을 falsifiable하게 확인.**

> ★ **2026-06-03 Phase 9 2nd-cycle 교정 ([[GAP-39]]):** 위 §0/§1 서술 **"전부 axis/backbone(c0200–c0213)"** ·
> **"정규화 층 공통 부분열 0개"** 는 **부정확**하다(§5 probe를 frozen `strands.json`에 재실행해 적발).
> 정확히는: 임계(freq≥500∧len≥3) 후보 76개 中 **16개가 비-backbone c 포함**(c0251/c0252 routing; c0320–c0323,
> c0360–c0363 normalization). 특히 `('c0320','c0321','c0322','c0323')` freq **531** = L-4→L-5 정규화 contiguous
> 부분열로 임계를 통과한다. **scope 혼동이 원인** — §5 probe는 **5000-oracle strand**(미배선 c 포함)를 측정하는데
> §0/§1은 그 결과를 곧장 "**57-wired tree**의 정규화층 0"으로 일반화했다.
> **그러나 결론 `bundles=[]`는 옳다(정밀 근거):** 다발 압축은 57-wired tree 대상인데 그 정규화 후보들은 **전부
> 미배선**(c0320–c0323 등 4개 미배선) → tree에 부재. 완전배선 후보 70개는 backbone/axis/routing(D-S3 압축금지).
> 완전배선이며 L-4→L-5를 건드리는 유일 후보 `('c0392','c0393','c0200')`는 DETECT/CLASSIFY+VERIFY(비-transform).
> ∴ **완전배선 commutative-normalization-transform run = 0 ⟹ `bundles=[]` 정당(wired scope 한정).** 이 정밀
> 정당화는 `tests/test_phase9_adversarial.py` **P9-16**으로 falsifiable 고정. (결론·`decision_tree.json` 불변;
> 본 교정은 커밋된 측정 문서의 사실 정정 — Direction C closure_proof 시제정정과 동성격, 신규 spec 아님.)

## §2. 왜 정규화 층이 희소한가 (원인)

1. **구현 범위:** 정규화(L-4→L-5) mess c는 슬라이스 1–9만 구현(나머지 고빈도 mess pair 미구현,
   `column_path_implementation_backlog.md` / [[GAP-30]]). 정규화 층 자체가 아직 sparse.
2. **설계상 다양성:** sc는 stratified mess sampling(K=0–6 활성 결함, stratum 내 uniform, seed 42). strand마다
   활성 mess 조합이 달라 **긴 공통 정규화 run이 형성되지 않는다.** 반면 backbone axis 밴드는 모든 strand가
   결정적으로 통과 → 고빈도 공통 부분열은 전부 backbone(압축 금지)으로 나온다.

## §3. 함의 — 응축은 "정규화층 밀도화 후"의 미래 기능 (falsifiable 이월)

- "응축(다발)" 목표(CLAUDE.md)는 **정규화 층을 밀도화**해야 실현된다 = 고빈도 미구현 mess c
  (NON_ASCII_DECIMAL c0374/c0375 f547 · PRE_DOSE/ID c0320–0323+c0390/c0391 f531 · NL-dose c0350/c0351
  f528 · NA_TOKEN c0300/c0301 f514 …)를 더 구현해 strand의 정규화 run을 길고 빈번하게 만든 *후*에야
  step 2 압축이 의미를 가진다.
- 이 밀도화 작업은 **사용자가 보류 결정한 Direction B mess 확장([[GAP-37]]) 줄기**와 동일하다. 따라서
  다발은 **step 4(정규화 구현) 이후의 미래 기능으로 falsifiable 이월**한다(현 세션 재개 안 함).
- **재측정 게이트:** 정규화 c가 추가될 때마다 본 §0 probe를 재실행해 정규화 층에 임계(freq≥500∧len≥3)
  공통 부분열이 출현하는지 확인 → 출현 시 step 2 압축 착수. (전까지 `bundles=[]` 유지가 정답.)

## §4. GAP-27B(FORMAT↔TIMEZONE 비가환)는 현재 moot

`spec/decision_tree.json` 다발이 0이므로, 다발 내부 비가환 c 순서(D-S2 canonical order의 예외, c0313
FORMAT↔TIMEZONE) 문제는 **현재 적용 대상이 없다(moot).** 정규화 밀도화로 실제 다발이 생기는 시점에
비로소 live가 되며, 그때 (a) 비가환 쌍을 다발에서 제외, 또는 (b) 고정 canonical order 부여로 결정한다(승인 대상).

## §5. 측정 재현법 (read-only)

```python
import json, collections
strands = json.load(open("spec/strands.json"))
THRESH = (len(strands) + 9) // 10          # ceil(b/10) = 500
cnt = collections.Counter()
for s in strands:
    seq, seen = s["c_sequence"], set()
    for i in range(len(seq)):
        for j in range(i + 3, len(seq) + 1):   # 길이 ≥ 3 contiguous
            seen.add(tuple(seq[i:j]))
    for sub in seen:
        cnt[sub] += 1
cand = {k: v for k, v in cnt.items() if v >= THRESH}   # → 76, 전부 c0200–c0213
```

## §6. 경계 (정직)

- 측정은 `spec/strands.json`(5000 best-strand SSOT) 직접 read 기반. 임계·층 판정 단정(불확정 0).
- 본 측정은 **현 57-wired scope 한정** 신호다. 정규화 밀도화 후의 다발 출현은 §3 재측정으로 확정해야 하며,
  본 문서는 그 전까지 `bundles=[]`가 정답임을 고정한다(원장 [[GAP-38]]).
- 무수정: 엔진/SSOT-data/decision_tree.json 불변. 측정·기록만. 미커밋.
