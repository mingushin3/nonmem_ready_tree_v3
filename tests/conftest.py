import sys
from pathlib import Path
import json

import pandas as pd
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

FIXTURES_DIR = PROJECT_ROOT / "fixtures" / "intermediate"


@pytest.fixture
def load_fixture():
    """Load a c-unit fixture pair (input CSV + expected JSON)."""
    def _load(c_id: str, case: str) -> tuple[pd.DataFrame, dict]:
        fixture_dir = FIXTURES_DIR / c_id
        df = pd.read_csv(fixture_dir / f"{case}_input.csv")
        with open(fixture_dir / f"{case}_expected.json", encoding="utf-8") as f:
            expected = json.load(f)
        return df, expected
    return _load


@pytest.fixture
def load_fixture_with_meta():
    """Load a c-unit fixture triple (input CSV + input meta JSON + expected JSON)."""
    def _load(c_id: str, case: str) -> tuple[pd.DataFrame, dict, dict]:
        fixture_dir = FIXTURES_DIR / c_id
        df = pd.read_csv(fixture_dir / f"{case}_input.csv")
        meta_path = fixture_dir / f"{case}_meta.json"
        if meta_path.exists():
            with open(meta_path, encoding="utf-8") as f:
                meta = json.load(f)
        else:
            meta = {}
        with open(fixture_dir / f"{case}_expected.json", encoding="utf-8") as f:
            expected = json.load(f)
        return df, meta, expected
    return _load
