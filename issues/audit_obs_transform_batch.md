# Audit Observations — transform 일괄 (c0019·c0020·c0021·c0022·c0023·c0140·c0141·c0121)

> 기록: 2026-05-29. auditor (transform 일괄) 세션 산출. **코드/spec/test/fixture 무수정 — 기록 전용.**
> provenance_gaps.md(입력/출력 계약 gap)와 별개로, 본 문서는 *감사 관찰(postcond 전략·테스트 설계·커버리지)*을 기록한다.

## 베이스라인 & 판정

- **pytest:** `python -m pytest tests/ -q` → **557 passed (0.94s)** — 2026-05-29 본 세션 실측 확인.
- **판정:** 8개 transform c 전부 점검 1~6 + 축 교차점검 A~F **PASS · FAIL 0 · STOP 미발동.**
  - spec snippet 표면 위반(c0022/c0140 `fillna(median)`, c0021 bare `lloq_value`, c0121 plain `melt`)은
    전부 frozen-snippet + 구현 레벨 override(GAP-19/20/21)로 해소, verbatim postcond 토큰 1:1 보존,
    실효 강제는 구현 guard + adversarial trap으로 이전됨(날조·silent-error 차단 견고).
- 상세 표/근거: 감사 보고(세션 plan 파일 `glittery-doodling-sparkle.md`).

---

## [OBS-1] verbatim postcond 공허 → correctness는 adversarial trap이 담보 (Phase 9 항목)

- **현상:** 다음 c의 verbatim `postcondition_predicate`가 c의 *실제 계약*을 강제하지 못한다(공허/자명).
  - **c0022:** `isinstance(x,(int,float,np.floating,np.integer)) or pd.isna(x)==False` → 문자열·NaN 모두 통과
    (NaN은 float, 문자열은 not-NaN). "결측 0"·"전수 numeric" 미강제.
  - **c0121:** `not isinstance(x,(list,dict))` → melt 후 scalar면 자명 참. wide→long refined shape 미강제.
  - **c0023(부분):** `isinstance(x,numeric).all()` → ffill 후 leading NaN도 float라 통과(결측0 미강제).
- **실효 강제 위치:** 구현 guard(residual NaN→Q07, dup-id/count-mismatch→fail) + adversarial trap.
- **★ 함의(STOP 아님, 의도적·문서화):** c0022가 `fillna(median)`으로, c0121이 plain melt로 회귀해도
  `_check_postcond`(verbatim)는 **여전히 PASS**. 오직 adversarial trap만 검출한다:
  - `tests/test_adversarial.py :: TestC0022Adversarial.test_missing_wt_not_median_filled` (NaN≠75.0)
  - `... TestC0121Adversarial.test_value_column_named_by_base_not_cov_value` / `test_multi_covariate_not_mixed`
  → **이 3개 c의 안전망은 adversarial 스위트이며 load-bearing.**
- **disposition (Phase 9):** Phase 6/7은 이 c들의 노드 거동을 postcond로 추론 **금지**(verbatim 식이 거동을
  대표하지 않음). 해당 adversarial trap **약화·삭제 금지**. Hallucination 규칙 §1(토큰 불변) + Lock 3(trap) 정합.
- **관련:** GAP-19(verbatim STOP-check) / GAP-20(a) / GAP-21(A).

## [OBS-2] covariate 4개 가드/fallback 비대칭 → Phase 5 일괄 유예 명문화 (Phase 5)

- **현상:** baseline-cov 쌍(c0022/c0140)은 `_COVARIATE_COLS` df-fallback + `test_gap3_fallback_*`로
  빈-리스트 silent no-op을 조기 방어한다. tv-cov 쌍(c0023/c0141)은 **fallback/가드 없음** →
  `meta['tv_covariates']` 미선언/빈 리스트면 빈 순회 → `{success:True}` **silent no-op**(Lock 3 우려).
  - `src/c_units/c0023_*.py` `_resolve_tv_covariates` → `return []` (fallback 없음), c0141 동일.
  - (tv_covariates는 알려진 컬럼 사전이 없어 baseline식 fallback이 덜 자연스러움은 사실.)
- **disposition (Phase 5):** GAP-3가 4개 consumer(c0022/c0023/c0140/c0141)의 동 위험을 이미 기록·유예함.
  본 비대칭을 **Phase 5에서 4개 일괄 정산으로 명문화**(가드 통일 또는 일괄 유예 중 택1). 이번 세션 무수정.
- **관련:** GAP-3 (covariate 컬럼명 리스트 생산자 부재 / silent no-op).

## [OBS-3] 미커버 방어 가드 trap → Phase 9 adversarial 확장으로 이월 (Phase 9)

- **현상:** 1차 도메인 분기는 전수 커버되나, 다음 *방어 가드* fail 분기에 전용 trap fixture 없음:
  - **c0140** `src/c_units/c0140_*.py`: 키 둘 다 부재(subject_id·ID 모두 없음→Q07, L96-97),
    시간 둘 다 부재(TIME·time_value 모두 없음→Q07, L101-102). (기존 fallback 테스트는 항상 한 키 충족.)
  - **c0121** `src/c_units/c0121_*.py`: `duplicated(subset=id_cols)`→fail(L105), `n_after!=n_before`→fail(L119).
  - (c0023 ID-부재·c0141 subject_id-부재는 trap 보유 — 정상.)
- **disposition (Phase 9):** Phase 9 adversarial 확장 시 위 4개 가드에 falsifiable trap 추가. 저위험. 이번 세션 무수정.

---

## 비고

- **하드닝(OBS-2/3 실제 수정)은 본 세션 범위 밖 — 별도 cycle**(사용자 ★ 결정 2026-05-29).
- **다음 세션 권장:** Phase 5 진입 시 GAP-16(명목 vs 실효 detection: c0121 req_det=c0207 ↔ cov_layout←c0380/c0381) +
  producer 갭(GAP-3 / GAP-15 / GAP-17) 우선 reconcile.
- **축 점검 요약:** A(median override 일관) / B(PROPAGATE+cross-bleed trap) / C(defensive to_numeric) /
  D(입력계약 GAP 누락0) / E(detection 오지정 c0121 고립) / F(반환 계약 균일) — 전부 PASS.
