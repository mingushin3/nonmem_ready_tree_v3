"""gap_annotator — unwired 구조를 [[GAP-37]] 사유로 기술 + 모호-wide 2옵션 제시(D-G2).

unwired finding은 라우팅하지 않는다(현 57-wired 백본에 대응 transform/route 없음).
"감지했으나 미배선([[GAP-37]])"으로 구조 증거만 기술한다.
subject-as-column wide의 *종류*(동일군 재측정 vs 별개 arm)가 구조만으로 불확정이면
silent 선택을 금하고(D-G2) 두 해석을 모두 surface한다 — 사용자 결정 대상.

★ 교정(검토 §3): param-summary 시트의 `재산출` 컬럼은 arm-vs-replicate 결정이 아니라
  "파생 재적합(derived-parameter re-fit)" = **비결정(non-decision)** 이다(단말 NCA 재적합일 뿐).
  따라서 surface_ambiguous_wide는 param-summary 시트를 skip하고, classify_non_decisions가
  비결정으로 분류한다. (Dog 전용 'RLD vs 시험'을 Mouse 결정문에 끌어오던 오분류 제거.)
"""
import re

_REANALYSIS = re.compile(r"(재산출|재분석|re-?anal|\(re\))", re.I)


def annotate_unwired(findings) -> list:
    """unwired finding → GAP-37 사유 엔트리."""
    return [{"feature": f.feature, "what": f.what,
             "structural_evidence": f.structural_evidence, "gap": "GAP-37"}
            for f in findings if not f.wired]


def surface_ambiguous_wide(structure: dict) -> list:
    """재산출/재분석 마커가 붙은 wide 컬럼 = 종류 불확정 → 두 해석 제시(D-G2).

    구조만으로 자동 판정하지 않는다 — interpretation_A/B를 모두 반환하고 선택은 사용자.
    """
    out = []
    for name, s in structure["per_sheet"].items():
        if s["shape_class"] == "param-summary":
            continue  # 파생 param-summary의 재산출 = 비결정(파생 재적합) → classify_non_decisions 소관(검토 §3)
        markers = []
        for row in s["sample"]:
            for v in row:
                if v and _REANALYSIS.search(v):
                    markers.append(v.strip())
        if markers:
            out.append({
                "feature": "wide-type",
                "sheet": name,
                "evidence": markers[:4],
                "interpretation_A": "동일 그룹의 재산출/재측정(replicate·reanalysis) → reconcile/dedupe 후 단일 시계열",
                "interpretation_B": "별개 arm/그룹(설계상 분리된 처리군) → 분리 유지 + subject-wide→long PIVOT 개별 처리",
                "why": "재측정 vs 별개군이 구조만으로 불확정 — 자동 선택 시 silent 오류(D-G2). 사용자 결정 필요.",
            })
    return out


def classify_non_decisions(structure: dict) -> list:
    """param-summary 시트의 `재산출` 마커 = '파생 재적합' 비결정(non-decision)으로 분류(검토 §3).

    동일 농도-시간 데이터를 단말 NCA λz 적합구간만 달리해 재적합한 것(초기지표 동일·단말만 상이) →
    신규 arm도 replicate도 아님 → raw conc 데이터셋엔 무의미. arm-vs-replicate 결정으로 라우팅하지
    않는다(surface_ambiguous_wide가 param-summary를 skip하는 짝). 1.Data를 SKIP하면 ambiguity 미발생.
    """
    out = []
    for name, s in structure["per_sheet"].items():
        if s["shape_class"] != "param-summary":
            continue
        markers = []
        for r, row in enumerate(s["sample"]):
            for c, v in enumerate(row):
                if v and _REANALYSIS.search(v):
                    markers.append(f"{name} r{r + 1}c{c + 1}: {v.strip()!r}")
        if markers:
            out.append({
                "kind": "derived-parameter-refit",
                "sheet": name,
                "classification": "non-decision",
                "evidence": markers[:4],
                "rationale": "동일 농도-시간 데이터의 단말 NCA λz 재적합(초기지표 동일·단말지표만 상이) — "
                             "신규 arm/replicate 아님. raw conc 데이터셋엔 무의미하므로 1.Data를 SKIP하면 "
                             "ambiguity 애초에 미발생.",
                "supersedes": "arm-vs-replicate 2옵션(param-summary는 surface_ambiguous_wide에서 skip)",
                "ref": "검토의견 §3 (단말 NCA 재적합); G2 vs G2재산출 초기지표 동일·단말만 상이",
            })
    return out
