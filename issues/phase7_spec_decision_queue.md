# Phase 7 — spec 결정 대기 목록 (decision_tree.json 잔여 edge)

> **목적:** decision_tree.json 골격(step 1~2.5, 순수-edge) 조립 후, **spec 결정이 있어야** 주입 가능한 잔여 conditional edge를 모은 승인 대기 큐.
> **위상:** [[GAP-33]] 파생. 원장 `issues/provenance_gaps.md`가 SSOT. 본 파일의 각 항은 **사용자 승인 후에만** decision_tree.json/c_units.json에 반영(SSOT 순서 spec→test→구현).
> **기준:** 2026-06-03 · Phase 7 step1~2.5 골격 생성 직후 · baseline 934 green · `spec/decision_tree.json` `deferred{}` 와 동기.
> **불변:** 본 파일 생성 세션(골격)은 아래 항목을 **주입하지 않았다**(`test_scope_out_edges_not_injected`로 부재 고정). 결정 전까지 미주입 유지.

> **★ 갱신(2026-06-03 결정 A·B 반영 — [[GAP-34]]):** 사용자 승인 결정 A(c0252/c0204 INFUSION-STOP-RESTART→Q04 spec-change)·결정 B(`terminal_routing` INVALID 3 edge)를 SSOT 순서로 반영했다. 아래 A·D·권장순서에 처리(✅)/이월(⏸) 표기. **A+B 후 잔존 scope-out = c0253→Q15D(89, 유일)** → **결정 C(2026-06-03)로 RESOLVE**(c0253.can_route_to_q +Q15D). 잔여 = UNREACHED-Q 4(일괄 이월). decision_tree: conditional **52** / terminal 3(315) / scope_out **0** / pure **3228**. `pytest` 937 green.

---

## A. scope-out edge — 실제 라우팅 ⊋ can_route_to_q (572 strand)
런타임/SSOT는 라우팅하나 c의 `can_route_to_q`/postcond에 **선언이 없어** 순수 주입 불가. measure-not-fix로 이월됨.

| edge | strand | 출처 GAP | 쟁점 | 처리 후보(승인 대상) |
|---|---|---|---|---|
| c0252 → **Q04** | 168 | [[GAP-31]] | A4=INFUSION-STOP-RESTART→Q04가 strands SSOT이나 **Q04 ∉ c0252.postcond**(verbatim 1글자 금지). 현 INVALID-default. | (a) c_units c0252 precond/postcond/can_route_to_q에 INFUSION+Q04 추가(Phase 2.9-style, 승인) / (b) strands A4→Q04 라우팅 재모델(더 큰 범위) |
| c0204 → **Q04** | — | [[GAP-5]] | universe_sm A4→Q04/INVALID이나 Q04 ∉ c0204.can_route_to_q([Q08,Q14]). | c0252와 동반 결정(A4 축 Q04 라우팅 주체 확정) |
| ~~c0253 → Q15D~~ ✅ | 89 | [[GAP-28]] | A5=BIOANALYTICAL-FINAL-FLAG-MISSING→Q15D 실제 라우팅이나 c0253.can_route_to_q=[Q01]이었음. Q15D는 c0256(A9)에서도 주입됨. | **✅ RESOLVED(결정 C, 2026-06-03):** c0253.can_route_to_q +Q15D → conditional edge(89 pure, scope_out 1→0). cite-verify 완료(해결후보 (a) 채택, impl 무변경). |
| c0252 → **INVALID** | 174 | [[GAP-31]] | INVALID는 terminal(Q 아님). conditional edge 대상 외(현 골격은 Q-edge만). | terminal-edge 표현 규약 결정(아래 D와 함께) |
| c0253 → **INVALID** | 111 | [[GAP-8]] | A5=ABSENT→INVALID scope-out. | 동상 |
| c0256 → **INVALID** | 30 | [[GAP-12]] | A9=IRRECONCILABLE→INVALID scope-out. | 동상 |

> **★ 처리(2026-06-03 — [[GAP-34]]):**
> - ✅ **c0252→Q04(168) · c0204→Q04** = 결정 A spec-change RESOLVE([[GAP-31]]/[[GAP-5]]); conditional edge 주입(pure 2971→3139).
> - ✅ **c0252→INVALID(174) · c0253→INVALID(111) · c0256→INVALID(30)** = 결정 B `terminal_routing` RESOLVE([[GAP-31]]/[[GAP-8]]/[[GAP-12]]); 315 strand, INVALID 도달성 확보(고립 0).
> - ✅ **c0253→Q15D(89, [[GAP-28]])** = **결정 C로 RESOLVE**(2026-06-03, 사용자 승인 — 해결후보 (a)). 결정 A와 동형(ROUTE c SSOT가 can_route_to_q 미선언 Q로 라우팅). cite-verify 완료(`universe_sm` §3 A5 :146 · `q_codes` Q15D.trigger :278 · `anchors` :54 · c0205 선례). c0253.can_route_to_q +Q15D(최소 변경, impl/postcond 무변경) → conditional edge 편입(89 pure, scope_out 1→0). **§A scope-out 전부 종결(0).**

## B. c0210 A10 — 위치 + terminal 라우팅 ([[GAP-13]])
- **쟁점 1(terminal 라우팅):** A10 NON-TABULAR→**UNSUPPORTED**, CORRUPTED→**INVALID**. 둘 다 process terminal(Q 아님), `can_route_to_q=[]`. 현 골격 미표현.
- **쟁점 2(실행 위치):** c0210 의미는 파이프라인 **front**(df 생성 前 게이트)이나 axis 번호·layer_pair은 **A10(chain 끝)**. tree backbone에서 A10을 어디에 둘지 결정 필요.
- **처리 후보:** (a) front pre-gate 노드 신설 + A10 표시 분리 / (b) chain 끝 유지 + terminal-edge 규약(D)으로 UNSUPPORTED/INVALID 연결.

## C. 잔여 mess/transform edge (구조)
- **[[GAP-27]]B — c0313 FORMAT↔TIMEZONE 정렬 상호작용:** 정규화 순서 상호작용의 tree 노드화는 step 2 다발 압축/merge 노드 설계와 함께 결정(현 골격은 linear 부착 보류).
- **c0040 placeholder:** REGISTRY 미배선 c. node 부재 → 부착·라우팅 전부 보류(배선 시 자동 편입).

## D. UNREACHED Q (Q15A/B/C/X) — wired c edge 0
4 Q는 어떤 wired c의 can_route_to_q에도 없어 incoming edge 0(고립). recover_to_c_id가 **미배선 c**(c0368/c0499/c0209)다.

| Q | trigger(q_codes) | recover | 도달 경로(strands last-c) | 처리 후보 |
|---|---|---|---|---|
| Q15A | 필수 deliverable 부재 | c0368(미배선) | 미배선 c | source c(c0368류) 배선 시 edge. 비-axis trigger → 정적 placeholder 유지 |
| Q15B | legacy marker 의미 미정의 | c0209 | 미배선 last-c(9) | A10=LEGACY-NM 축 정적 edge 후보(승인) 또는 source c 배선 |
| Q15C | A2=TDM-RWD + recall | c0209 | 미배선 last-c(11) | **A2 TDM-RWD 축 정적 edge** 주입 후보(축 trigger 명확) |
| Q15X | catch-all(매칭 불가) | c0499(미배선) | 미배선 c(3) | catch-all → 정적 placeholder 유지(축 trigger 없음) |

- **권장:** Q15C는 A2 축 trigger가 명확해 backbone axis-state→Q **정적 edge** 주입 가능(순수 근접). Q15A/Q15X는 axis-state가 아니어서(deliverable/catch-all) **placeholder 유지**가 정직. Q15B는 A10 LEGACY-NM 연결 여부 결정 필요. 모두 검증 strand는 없음(57-wired 한정).
- **★ 결정(2026-06-03, 사용자 확정 — [[GAP-34]]):** UNREACHED 4 = **4개 모두 이월**. 미배선 source c(c0368/c0499/c0209) 구현 시점(C/D/E 또는 후속)에 **일괄 처리**. Q15C는 A2 축 trigger 명확이나 **단독 주입 시 비대칭**(Q15A/B/X와 깨짐)이라 묶어서 이월. exercised partition 불변(13), `deferred.unreached_q` 문서화 유지(silent drop 0).

---

## 권장 처리 순서 (사용자 결정 후)
1. ✅ **A4 Q04 일원화**([[GAP-5]]/[[GAP-31]]) — **DONE(결정 A)**: c0204/c0252 can_route_to_q+postcond에 Q04 spec-change, 168 strand pure 편입.
2. ✅ **terminal-edge 표현 규약** — **DONE(결정 B)**: 별도 `terminal_routing` 배열 채택. INVALID 3 edge(c0252/c0253/c0256, 315) 주입. UNSUPPORTED는 c0210([[GAP-13]]) deferred라 미주입(동일 규약 추후 적용).
3. **c0210 A10 위치**([[GAP-13]]).
4. **UNREACHED-Q 정적 edge**(D) — Q15C(A2) 주입, Q15A/B/X 처리 확정.
5. 이후 step 2 다발 압축 → step 4 orchestrator 재배선(①/C·D·E).

> 각 항은 1세션 1결정 권장(SSOT 순서 spec→test→구현, verbatim postcond 1글자 금지 준수).
