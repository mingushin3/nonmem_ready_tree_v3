"""descriptor_builder — wired+derivable finding → 엔진 meta descriptor 키.

wired DETECT c가 읽는 *경계 입력*(boundary input)만 채운다. Tier 0은 file-property
descriptor에 한정:
  - file_exists=True (c0210 precond 만족 — df 없이도 honest-stop 시 A10 평가)
  - file_format='semi-structured' (다중시트/병합 감지 시 → c0210 SEMI-STRUCTURED)
  - n_studies=1 (단일 파일 → c0201 SINGLE)
★ 외부 정책 경계 입력(blq_policy/uloq/units/harmonization_policy_present/time_policy 등)은
  **세팅하지 않는다** — 구조에서 도출 불가(GAP-6/30). 미세팅 시 해당 c는 df-fallback 또는
  undetermined로 남고 navigator가 precondition-gate한다(날조 0).
mess_profile은 여기서 만들지 않는다(symbolic 출력 — __init__이 finding에서 조립).
"""


def build_meta(findings, structure: dict) -> dict:
    feats = {f.feature for f in findings}
    meta = {"file_exists": True, "n_studies": 1}
    if "file-format" in feats:
        meta["file_format"] = "semi-structured"
    return meta
