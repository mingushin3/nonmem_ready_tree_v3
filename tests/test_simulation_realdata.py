"""고강도 실데이터 시뮬레이션 — raw_data_examples_1~3 + R/Python 스니펫 실행 검증.

★ report-only 검증: 정본(spec/c_units.json)·엔진 무수정. 실데이터/Rscript 부재 시 graceful skip.
  (1) 5개 실데이터 ingest() == 기대(faithful/honest-stop·c_sequence·gap·recipe WU) + wizard==ingest
  (2) 122개 python_snippet 전부 compile / r_snippet 전부 R parse(2개 frozen 정본 예외 문서화)
  (3) 대표 transform 을 python·R 로 실제 실행 → before→after 일치
  (4) faithful 실데이터가 디스패치하는 c 는 모두 EASY 카드 보유

발견(finding, 미수정 — frozen 정본): c0200 r_snippet=다중행 if/else 최상위 R parse 불가(의미는 정상),
  c0216 r_snippet=R 문자열에 \\x00 포함 불가([^\\x00-\\x7F]). 둘 다 python_snippet 은 정상. → KNOWN_R_NONPARSE.
"""
import glob
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "render"))

import build_html_v2 as V  # noqa: E402
from src.adapter import ingest  # noqa: E402
from src.adapter.xlsx_ingester import read_workbook_structure  # noqa: E402

_RAW = {e["c_id"]: e for e in json.loads((ROOT / "spec" / "c_units.json").read_text(encoding="utf-8"))}
_RSCRIPT = shutil.which("Rscript")

# frozen 정본 r_snippet 중 standalone R parse 불가(문서화된 finding, 본 세션 미수정)
KNOWN_R_NONPARSE = {"c0200", "c0216"}

# ── 실데이터 기대값(실측 확정) ────────────────────────────────────────────────
FAITHFUL_13 = ["c0201", "c0203", "c0205", "c0210", "c0211", "c0212", "c0214",
               "c0215", "c0216", "c0305", "c0310", "c0312", "c0314"]
REAL_EXPECT = {
    "raw_data_examples_1": dict(stop_at="navigable-band-complete", gap=None,
                                c_seq=FAITHFUL_13, wu=set()),
    "raw_data_examples_2": dict(stop_at="structure-recognition", gap="GAP-37",
                                c_seq=["c0201", "c0210"],
                                wu={"QA-strip", "pivot-wide-to-long", "dose-bw-join"}),
    "raw_data_examples_3/1. Mouse PK": dict(stop_at="structure-recognition", gap="GAP-37",
                                c_seq=["c0201", "c0210"],
                                wu={"QA-strip", "param-summary-reserve", "pivot-wide-to-long", "dose-bw-join"}),
    "raw_data_examples_3/2. Rat PK": dict(stop_at="structure-recognition", gap="GAP-37",
                                c_seq=["c0201", "c0210"],
                                wu={"QA-strip", "param-summary-reserve", "pivot-wide-to-long", "dose-bw-join"}),
    "raw_data_examples_3/3. Dog PK": dict(stop_at="structure-recognition", gap="GAP-37",
                                c_seq=["c0201", "c0210"],
                                wu={"QA-strip", "param-summary-reserve", "pivot-wide-to-long", "dose-bw-join"}),
}


def _pick_xlsx(rel):
    d = ROOT / rel
    if not d.is_dir():
        return None
    xs = [f for f in glob.glob(str(d / "*.xlsx")) if not os.path.basename(f).startswith("~$")]
    return max(xs, key=os.path.getsize) if xs else None


# ===== (1) 실데이터 decision tree/라우팅 ====================================

@pytest.mark.parametrize("rel", list(REAL_EXPECT))
def test_realdata_ingest_and_wizard_match(rel):
    f = _pick_xlsx(rel)
    if f is None:
        pytest.skip("실데이터 부재: " + rel)
    exp = REAL_EXPECT[rel]
    r = ingest(f)
    assert r["dispatched"]["c_sequence"] == exp["c_seq"], rel
    assert r["stop"]["at"] == exp["stop_at"], rel
    assert r["stop"].get("gap") == exp["gap"], rel
    wu = {w["name"] for w in r.get("recipe", {}).get("work_units", [])}
    assert wu == exp["wu"], (rel, wu)
    # 마법사(=정본 미러)가 동일 판정
    v = V.wizard_verdict_from_structure(read_workbook_structure(f))
    assert v["c_sequence"] == exp["c_seq"], rel
    assert v["stop_at"] == exp["stop_at"], rel
    assert v["gap"] == exp["gap"], rel


def test_faithful_dataset_dispatched_c_all_have_easy_cards():
    f = _pick_xlsx("raw_data_examples_1")
    if f is None:
        pytest.skip("실데이터 부재")
    for cid in ingest(f)["dispatched"]["c_sequence"]:
        assert cid in V.EASY, cid


# ===== (2) 122개 스니펫 구문 검증 ===========================================

def test_all_python_snippets_compile():
    bad = []
    for cid, e in _RAW.items():
        try:
            compile(e["python_snippet"], cid, "exec")
        except SyntaxError as ex:
            bad.append((cid, str(ex)))
    assert not bad, bad


def test_all_r_snippets_parse_except_known():
    if _RSCRIPT is None:
        pytest.skip("Rscript 미설치")
    td = tempfile.mkdtemp()
    for cid, e in _RAW.items():
        Path(td, cid + ".R").write_text(e["r_snippet"], encoding="utf-8")
    rcode = (
        'fs <- list.files("%s", pattern="[.]R$", full.names=TRUE)\n'
        'for (f in fs) { msg <- tryCatch({parse(file=f); ""}, error=function(e) conditionMessage(e));\n'
        '  if(nzchar(msg)) cat("FAIL", sub("[.]R$","",basename(f)), "\\n") }\n'
    ) % td
    out = subprocess.run([_RSCRIPT, "-e", rcode], capture_output=True, text=True)
    failed = {ln.split()[1] for ln in out.stdout.splitlines() if ln.startswith("FAIL")}
    # 새로 깨진 snippet 0 (frozen 정본 예외만 허용)
    assert failed <= KNOWN_R_NONPARSE, ("신규 R parse 실패", failed - KNOWN_R_NONPARSE)


# ===== (3) 대표 transform 실제 실행 (before→after) ==========================

def _run_py(cid, df):
    import pandas as pd
    import numpy as np
    ns = {"df": df.copy(), "pd": pd, "np": np}
    exec(_RAW[cid]["python_snippet"], ns)
    return ns["df"]


def test_python_transform_execution():
    pd = pytest.importorskip("pandas")
    import numpy as np
    d = _run_py("c0011", pd.DataFrame({"EVID": [1, 0, 0], "dv_value": [np.nan, 5.2, np.nan]}))
    assert list(d["MDV"]) == [1, 0, 1]                                   # ASSIGN MDV
    d = _run_py("c0341", pd.DataFrame({"ID": [1, np.nan, np.nan, 2]}))
    assert list(d["ID"]) == [1, 1, 1, 2]                                 # PROPAGATE MERGED_CELL
    d = _run_py("c0010", pd.DataFrame({"event_type": ["dose", "obs", "reset"]}))
    assert list(d["EVID"]) == [1, 0, 2]                                  # ASSIGN EVID
    d = _run_py("c0018", pd.DataFrame({"subject_id": ["PT-001", "PT-001", "PT-002"]}))
    assert list(d["ID"]) == [1, 1, 2]                                    # ASSIGN ID
    d = _run_py("c0017", pd.DataFrame({"EVID": [1, 0, 0], "MDV": [1, 0, 1],
                                       "dv_value": [np.nan, 5.2, np.nan]}))
    assert list(d["DV"]) == [0, 5.2, 0]                                  # ASSIGN DV


def _run_r(setup, cid):
    code = setup + "\n" + _RAW[cid]["r_snippet"] + '\ncat(RESULT)\n'
    out = subprocess.run([_RSCRIPT, "-e", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr[-300:]
    return out.stdout.strip()


def test_r_transform_execution():
    if _RSCRIPT is None:
        pytest.skip("Rscript 미설치")
    # c0011 MDV
    code = ("df <- data.frame(EVID=c(1L,0L,0L), dv_value=c(NA,5.2,NA))\n"
            + _RAW["c0011"]["r_snippet"] + '\ncat(df$MDV)\n')
    out = subprocess.run([_RSCRIPT, "-e", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr[-300:]
    assert out.stdout.split() == ["1", "0", "1"], out.stdout
    # c0341 fill
    code = ("suppressMessages(library(tidyr)); df <- data.frame(ID=c(1,NA,NA,2))\n"
            + _RAW["c0341"]["r_snippet"] + '\ncat(df$ID)\n')
    out = subprocess.run([_RSCRIPT, "-e", code], capture_output=True, text=True)
    assert out.returncode == 0, out.stderr[-300:]
    assert out.stdout.split() == ["1", "1", "1", "2"], out.stdout
