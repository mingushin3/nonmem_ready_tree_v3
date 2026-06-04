"""reason_binder — feature에 사람가독 사유 부착 (Direction B ripple M5 single-source).

wired feature의 reason = 대응 DETECT/VERIFY c의 spec/c_units.json 항목에서
  verify_visualization['criterion_predicate_ko'] (사람가독 기준) + ['ref'] (provenance)을
  그대로 재사용한다(단일 출처). unwired feature는 reason_binder가 아니라 gap_annotator가
  구조 증거 + [[GAP-37]]로 기술한다(라우팅 아님).

read-only: spec/c_units.json을 읽기만 한다(orchestrator.py:118 동형 로드, 무수정).
어떤 SSOT/엔진도 수정하지 않는다.
"""
from pathlib import Path
import json

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_CUNITS_PATH = _PROJECT_ROOT / "spec" / "c_units.json"
_CUNITS = {c["c_id"]: c for c in json.loads(_CUNITS_PATH.read_text(encoding="utf-8"))}


def bind_wired(c_id: str) -> dict:
    """wired c의 criterion_predicate_ko + ref를 반환.

    결손(spec에 c_id 없음, 또는 criterion_ko 미기재)이면 None으로 정직 표기 — 날조 금지.
    """
    entry = _CUNITS.get(c_id)
    if entry is None:
        return {"c_id": c_id, "criterion_ko": None, "ref": None,
                "note": "c_id가 spec/c_units.json에 없음"}
    vv = entry.get("verify_visualization") or {}
    return {
        "c_id": c_id,
        "criterion_ko": vv.get("criterion_predicate_ko"),
        "ref": entry.get("ref"),
    }
