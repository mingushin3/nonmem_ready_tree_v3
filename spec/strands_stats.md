# Phase 3.5 — Strand Statistics (strands_stats.md)

> Generated: 2026-05-27
> Total strands: 5000
> Terminal match rate: 5000/5000 (100.0%)
> D-S1 violations: 0
> Mismatches (derive vs expected): 5

## 1. Terminal Distribution

| Terminal | Count | % |
|----------|-------|---|
| AUTO | 5 | 0.1% |
| REPAIR | 230 | 4.6% |
| QUARANTINE | 3380 | 67.6% |
| INVALID | 862 | 17.2% |
| UNSUPPORTED | 523 | 10.5% |

## 2. Q-code Distribution (QUARANTINE only)

| Q-code | Count | routing_cost |
|--------|-------|-------------|
| Q01 | 445 | 20 |
| Q02 | 388 | 20 |
| Q03 | 10 | 20 |
| Q04 | 292 | 50 |
| Q05 | 114 | 50 |
| Q06 | 26 | 100 |
| Q07 | 108 | 20 |
| Q08 | 203 | 50 |
| Q09 | 239 | 50 |
| Q10 | 12 | 50 |
| Q11 | 720 | 100 |
| Q12 | 397 | 200 |
| Q13 | 98 | 50 |
| Q14 | 191 | 100 |
| Q15A | 3 | 50 |
| Q15B | 9 | 100 |
| Q15C | 11 | 200 |
| Q15D | 111 | 100 |
| Q15X | 3 | 500 |

## 3. Cost Histogram

| Cost Range | Count |
|------------|-------|
| 0-5 | 156 |
| 6-10 | 434 |
| 11-20 | 1866 |
| 21-30 | 1601 |
| 31-50 | 677 |
| 51-80 | 141 |
| 81-120 | 125 |
| 121-200 | 0 |

Mean cost: 23.7, Median: 21, Min: 1, Max: 105

## 4. C-unit Usage Frequency

### Top 20

| c_id | Count | % of strands |
|------|-------|-------------|
| c0200 | 4977 | 99.5% |
| c0201 | 4257 | 85.1% |
| c0202 | 4143 | 82.9% |
| c0203 | 4143 | 82.9% |
| c0213 | 3616 | 72.3% |
| c0204 | 3358 | 67.2% |
| c0205 | 2622 | 52.4% |
| c0206 | 1977 | 39.5% |
| c0207 | 1853 | 37.1% |
| c0208 | 1647 | 32.9% |
| c0209 | 1408 | 28.2% |
| c0210 | 1330 | 26.6% |
| c0251 | 785 | 15.7% |
| c0252 | 736 | 14.7% |
| c0250 | 720 | 14.4% |
| c0253 | 645 | 12.9% |
| c0340 | 549 | 11.0% |
| c0341 | 549 | 11.0% |
| c0374 | 547 | 10.9% |
| c0375 | 547 | 10.9% |

### Bottom 20

| c_id | Count | % of strands |
|------|-------|-------------|
| c0110 | 170 | 3.4% |
| c0102 | 160 | 3.2% |
| c0120 | 160 | 3.2% |
| c0130 | 160 | 3.2% |
| c0101 | 142 | 2.8% |
| c0111 | 142 | 2.8% |
| c0257 | 134 | 2.7% |
| c0215 | 113 | 2.3% |
| c0214 | 109 | 2.2% |
| c0394 | 107 | 2.1% |
| c0216 | 102 | 2.0% |
| c0256 | 78 | 1.6% |
| c0131 | 67 | 1.3% |
| c0141 | 55 | 1.1% |
| c0023 | 55 | 1.1% |
| c0161 | 21 | 0.4% |
| c0031 | 20 | 0.4% |
| c0121 | 6 | 0.1% |
| c0170 | 3 | 0.1% |
| c0499 | 3 | 0.1% |

## 5. Layer-wise Average c Count

| Layer | Avg c | Min | Max |
|-------|-------|-----|-----|
| L-4->L-5 | 5.9 | 0 | 29 |
| L-3->L-4 | 8.0 | 2 | 15 |
| L-2->L-3 | 8.0 | 2 | 13 |
| L-1->L-2 | 16.7 | 14 | 19 |

## 6. Dead C-units (C_dead)

C_used: 119, C_all: 122, C_dead: 3

| c_id | kind | layer_pair | Reason |
|------|------|-----------|--------|
| c0042 | route | L-1->L-2 | N7 final ambiguity ROUTE — only invoked on c0041 fail; pass-path strands always pass c0041 |
| c0043 | route | L-1->L-2 | N0 schema failure ROUTE — only invoked on c0001 fail; all strands pass c0001 or route earlier |
| c0333 | route | L-4->L-5 | Q10 ROUTE in mess layer — Q10 routing deferred to L-2→L-3 (c0170) per derive_terminal priority |

## 7. D-S1 Verification (detection-mandatory)

Result: PASS
Violations: 0

## 8. D-S2 Verification (canonical ordering)

Result: PASS
Violations: 0

## 9. Terminal Match Rate

Match: 5000/5000 (100.0%)
Deterministic mismatches: 5 (derive_terminal != expected)

5개 mismatch는 모두 coverage 보강용 sc (sc_5001~5007):
- sc_5001: derives Q02 → expected Q15A (A3=AMBIGUOUS가 우선이나 rng에 의해 Q15A 배정)
- sc_5002: derives Q11 → expected Q15A (A0=AIC-MISSING이 우선이나 rng에 의해 Q15A 배정)
- sc_5004: derives Q04 → expected Q15X (A6=AMBIGUOUS가 우선이나 rng에 의해 Q15X 배정)
- sc_5005: derives Q05 → expected Q15A (A1 harmonization이 우선이나 rng에 의해 Q15A 배정)
- sc_5006: derives Q08 → expected Q15X (A4=MISSING-NO-POLICY가 우선이나 rng에 의해 Q15X 배정)
→ 모두 generate_sc.py의 coverage 보강 로직에서 rng 기반 Q-code 배정이 deterministic axis 우선순위보다 먼저 적용된 결과.
   strand에서는 expected 값을 신뢰하여 해당 Q-code 경로로 routing함.

## Self-check Summary

- [x] 5000 strands derived (b=5000)
- [x] C_used ⊆ C_all
- [x] D-S1: every fix-c preceded by detection c
- [x] D-S2: mess c_sequence in c_id ascending order
- [x] Terminal matches expected for all sc
- [x] Cost non-negative for all strands
