"""structure_inspector — 실물 구조의 per-feature 감지 (= 엔진이 못 가진 "producing c").

wired DETECT c들은 raw 구조를 파싱하지 않고 meta descriptor를 읽는다(c0201 docstring:
"external boundary inputs, no producing c, GAP-6"). 본 inspector가 그 producing c 역할 —
구조 증거로부터 (a) wired+derivable feature(→ mess_profile 플래그 + 대응 wired c) 와
(b) unwired/not-accepted 구조(subject-wide·QA블록·inline-BLQ·sheet-JOIN·param-summary)를
**감지**한다. (b)는 라우팅하지 않고 기술만 한다([[GAP-37]], gap_annotator 소관).

각 detector는 구조 sample(read_workbook_structure 산출)을 스캔한다 — df=None(honest-stop)에서도
동작. df가 있으면(faithful tidy) 행-레코드 의존 감지(중복행)도 수행. 엔진/SSOT 무수정.
"""
import re
from dataclasses import dataclass, asdict

_BLQ_TOKEN = re.compile(r"(bql|blq|below\s*quant|<\s*\d|\bnd\b|\blod\b|이하|loq)", re.I)
_INLINE_BLQ = re.compile(r"\d.*\(\s*(bql|blq|below)\b", re.I)
_REANALYSIS = re.compile(r"(재산출|재분석|re-?anal|\(re\))", re.I)
_MEANSD = re.compile(r"^(mean|sd|std|평균|표준편차|cv%?)$", re.I)
_BW_SHEET = re.compile(r"(\bbw\b|body\s*weight|체중|weights?)", re.I)
_UNIT_HDR = re.compile(r"^(unit|units|단위)$", re.I)


@dataclass(frozen=True)
class Finding:
    feature: str
    what: str
    structural_evidence: str
    wired: bool
    target_c_id: str | None = None
    mess_dim: str | None = None
    derivable: bool = True

    def to_dict(self) -> dict:
        return asdict(self)


def _cells(structure):
    for name, s in structure["per_sheet"].items():
        for r, row in enumerate(s["sample"]):
            for c, val in enumerate(row):
                yield name, r, c, val


# ---- (a) wired + structurally-derivable ----------------------------------

def _detect_blq_token(structure):
    for name, r, c, val in _cells(structure):
        if val and _BLQ_TOKEN.search(val) and not _INLINE_BLQ.search(val):
            return Finding("blq-token",
                           "BLQ 토큰 변종 존재 (BQL/below quant/<LLOQ 등)",
                           f"sheet {name!r} r{r + 1}c{c + 1}: {val!r}",
                           wired=True, target_c_id="c0305", mess_dim="BLQ_TOKEN")
    return None


def _detect_encoding(structure):
    if structure.get("non_ascii_present"):
        return Finding("encoding",
                       "비-ASCII(한글/cp949 의심) 텍스트 존재",
                       f"non_ascii_present=True ({structure['encoding_hint']})",
                       wired=True, target_c_id="c0216", mess_dim="ENCODING")
    return None


def _detect_unit_column(structure):
    for name, s in structure["per_sheet"].items():
        if any(v and _UNIT_HDR.match(v.strip()) for row in s["sample"] for v in row):
            return Finding("unit-column",
                           "단위가 별도 'Unit' 열에 선언 (numeric 열별 meta['units'] 아님 → c0214 df-default=Q10)",
                           f"sheet {name!r}",
                           wired=True, target_c_id="c0214", mess_dim="UNIT_DECLARATION",
                           derivable=False)
    return None


def _detect_file_format(structure):
    merged = sum(s["n_merged"] for s in structure["per_sheet"].values())
    if structure["n_sheets"] > 1 or merged > 0:
        return Finding("file-format",
                       "다중시트/병합셀 semi-structured xlsx",
                       f"n_sheets={structure['n_sheets']}, merged_total={merged}",
                       wired=True, target_c_id="c0210", mess_dim=None)
    return None


def _detect_study_integration(structure):
    # 단일 CRO 파일 = single study (다중 study ID 미검출). 항상 1건 — file-property.
    return Finding("study-integration",
                   "단일 파일 = single study (다중 study ID 미검출)",
                   f"n_sheets={structure['n_sheets']}, 단일 파일",
                   wired=True, target_c_id="c0201", mess_dim=None)


def _detect_duplicate_rows(structure, df):
    if df is not None and len(df) > 0 and bool(df.duplicated().any()):
        return Finding("duplicate-row",
                       "완전 중복 행 존재",
                       f"{int(df.duplicated().sum())} duplicated rows in chosen tidy sheet",
                       wired=True, target_c_id="c0215", mess_dim="DUPLICATE_ROW")
    return None


# ---- (b) unwired / not-accepted (기술만, GAP-37) ---------------------------

def _detect_inline_blq(structure):
    for name, r, c, val in _cells(structure):
        if val and _INLINE_BLQ.search(val):
            return Finding("inline-blq",
                           "값+플래그 결합셀 BLQ (예: '0.09 (BQL)') — 값 보존 미보장, wired c0305 토큰 regex 미포착",
                           f"sheet {name!r} r{r + 1}c{c + 1}: {val!r}",
                           wired=False)
    return None


def _detect_qa_block(structure):
    qa = [n for n, s in structure["per_sheet"].items() if s["shape_class"] == "qa-contaminated"]
    if qa:
        return Finding("intra-sheet-qa-block",
                       "intra-sheet QA블록(Standard/DBLK/BLK/QC/Calibration)이 실샘플과 동일시트 혼재",
                       f"sheets: {qa}", wired=False)
    return None


def _detect_param_summary(structure):
    ps = [n for n, s in structure["per_sheet"].items() if s["shape_class"] == "param-summary"]
    if ps:
        return Finding("param-summary",
                       "파생 NCA 파라미터 요약 시트(Parameters×Unit×Mean) — raw conc 아님",
                       f"sheets: {ps}", wired=False)
    return None


def _detect_subject_wide(structure):
    sw = [n for n, s in structure["per_sheet"].items() if s["shape_class"] == "subject-wide"]
    if sw:
        ev = "; ".join(f"{n}: header={structure['per_sheet'][n]['header_row'][:6]}" for n in sw)
        return Finding("subject-wide-conc",
                       "subject-as-column wide conc (시간=행, 개체=열) — wide→long PIVOT 미배선(c0120은 analyte-wide만)",
                       ev, wired=False)
    return None


def _detect_mean_sd(structure):
    for name, s in structure["per_sheet"].items():
        if any(v and _MEANSD.match(v.strip()) for row in s["sample"] for v in row):
            return Finding("mean-sd-aggregate",
                           "Mean/SD 집계열 (개별 관측 아님)",
                           f"sheet {name!r}", wired=False)
    return None


def _detect_reanalysis(structure):
    for name, r, c, val in _cells(structure):
        if val and _REANALYSIS.search(val):
            return Finding("reanalysis-duplicate",
                           "재산출/재분석 중복 그룹 (예: 'G2 (재산출)')",
                           f"sheet {name!r} r{r + 1}c{c + 1}: {val!r}", wired=False)
    return None


def _detect_dose_bw_join(structure):
    bw = [n for n in structure["sheet_names"] if _BW_SHEET.search(n)]
    if bw and structure["n_sheets"] > 1:
        return Finding("dose-bw-sheet-join",
                       "체중(BW)/용량이 별도 시트 — event table로 JOIN 필요(c0110/c0111 미배선)",
                       f"BW-like sheets: {bw}", wired=False)
    return None


_DETECTORS = [
    _detect_blq_token, _detect_encoding, _detect_unit_column, _detect_file_format,
    _detect_study_integration, _detect_inline_blq, _detect_qa_block,
    _detect_param_summary, _detect_subject_wide, _detect_mean_sd,
    _detect_reanalysis, _detect_dose_bw_join,
]


def inspect(structure: dict, df=None, raw_cols=None) -> list:
    """구조 + (옵션) tidy df → Finding 리스트(non-None만)."""
    findings = [f for f in (d(structure) for d in _DETECTORS) if f is not None]
    dup = _detect_duplicate_rows(structure, df)
    if dup is not None:
        findings.append(dup)
    return findings
