"""Phase 3 verification script."""
import json
import pathlib
from collections import Counter

ROOT = pathlib.Path(__file__).parent

qc = json.loads((ROOT / "spec" / "q_codes.json").read_text("utf-8"))
sc = json.loads((ROOT / "spec" / "starting_conditions.json").read_text("utf-8"))
cu = json.loads((ROOT / "spec" / "c_units.json").read_text("utf-8"))
anchors = json.loads((ROOT / "anchors.json").read_text("utf-8"))

print("=== PHASE 3 VERIFICATION ===\n")

checks_passed = 0
checks_total = 0

def check(name, ok, detail=""):
    global checks_passed, checks_total
    checks_total += 1
    status = "PASS" if ok else "FAIL"
    if ok:
        checks_passed += 1
    msg = f"[{checks_total:02d}] {status}: {name}"
    if detail:
        msg += f" - {detail}"
    print(msg)

# 1. q_codes.json: 19 entries
check("q_codes.json has 19 entries", len(qc) == 19, f"got {len(qc)}")

# 2. All anchors.json Q-codes present
anchor_qs = set(anchors["q_codes"].keys())
qc_ids = set(q["q_id"] for q in qc)
missing_q = anchor_qs - qc_ids
check("All anchors Q-codes present", not missing_q, str(missing_q) if missing_q else "")

# 3. recover_to_c_id valid
cu_ids = set(c["c_id"] for c in cu)
invalid_recover = [q["q_id"] for q in qc if q["recover_to_c_id"] not in cu_ids]
check("recover_to_c_id all valid c_ids", not invalid_recover, str(invalid_recover) if invalid_recover else "")

# 4. starting_conditions count
check("starting_conditions.json has 5000 entries", len(sc) == 5000, f"got {len(sc)}")

# 5. Strata distribution
strata = Counter(s["stratum"] for s in sc)
strata_ok = strata["K0"] >= 95 and strata.get("K6+", 0) >= 95
check("Strata distribution reasonable", strata_ok, str(dict(sorted(strata.items()))))

# 6. All axis states from anchors.json
bad_states = []
for s in sc:
    for ax, st in s["v42_cell"].items():
        if ax in anchors["axes"] and st not in anchors["axes"][ax]:
            bad_states.append((s["sc_id"], ax, st))
check("All axis states from anchors.json", not bad_states,
      str(bad_states[:3]) if bad_states else "")

# 7. Incompatibility check (R1, R2, R3)
incompat = 0
for s in sc:
    c = s["v42_cell"]
    ddi0 = c["A0"] == "AIC-DDI"
    ddi2 = c["A2"] == "DDI"
    ddi8 = c["A8"] in ("DDI-VICTIM-ONLY", "DDI-VICTIM-PERPETRATOR")
    if ddi0 != ddi2 or ddi0 != ddi8:
        incompat += 1
    if c["A0"] == "AIC-PEDS" and c["A2"] != "PEDIATRIC":
        incompat += 1
    if c["A7"] == "PEDIATRIC-MATURATION" and c["A0"] != "AIC-PEDS":
        incompat += 1
check("No R1/R2/R3 violations", incompat == 0, f"{incompat} violations" if incompat else "")

# 8. Terminal validity
valid_terms = {"AUTO", "REPAIR", "QUARANTINE", "UNSUPPORTED", "INVALID"}
bad_term = [s["sc_id"] for s in sc if s["expected_terminal"] not in valid_terms]
check("expected_terminal all valid", not bad_term, str(bad_term[:5]) if bad_term else "")

# 9. q_code consistency (non-null iff QUARANTINE)
bad_qc = []
for s in sc:
    if s["expected_terminal"] == "QUARANTINE" and s.get("expected_q_code") is None:
        bad_qc.append(s["sc_id"])
    if s["expected_terminal"] != "QUARANTINE" and s["expected_q_code"] is not None:
        bad_qc.append(s["sc_id"])
check("expected_q_code <-> QUARANTINE consistency", not bad_qc,
      f"{len(bad_qc)} violations" if bad_qc else "")

# 10. has_harmonization_policy correctness
bad_harm = []
for s in sc:
    a1 = s["v42_cell"]["A1"]
    hp = s["has_harmonization_policy"]
    if a1 in ("MULTI-HOMO", "MULTI-HETERO", "MULTI-SITE", "INTERIM"):
        if hp is None:
            bad_harm.append(s["sc_id"])
    else:
        if hp is not None:
            bad_harm.append(s["sc_id"])
check("has_harmonization_policy populated correctly", not bad_harm,
      f"{len(bad_harm)} violations" if bad_harm else "")

# 11-13. Coverage
axis_cov = Counter()
q_cov = Counter()
mess_cov = Counter()
for s in sc:
    for ax, st in s["v42_cell"].items():
        axis_cov[(ax, st)] += 1
    if s["expected_q_code"]:
        q_cov[s["expected_q_code"]] += 1
    for d, v in s["mess_profile"].items():
        if v:
            mess_cov[d] += 1

all_states = set()
for ax, sts in anchors["axes"].items():
    for st in sts:
        all_states.add((ax, st))
uncov_axis = [(a, s) for (a, s) in sorted(all_states) if axis_cov[(a, s)] < 1]
check("All axis states >= 1 (marginal)", not uncov_axis,
      str(uncov_axis[:5]) if uncov_axis else f"{len(all_states)} states covered")

uncov_q = [q for q in sorted(anchor_qs) if q_cov[q] < 3]
check("All Q-codes >= 3", not uncov_q,
      str(uncov_q) if uncov_q else f"min={min(q_cov.values())}")

MESS_DIMS = [
    "NA_TOKEN", "BLQ_TOKEN", "TIME_FORMAT", "TIME_ANCHOR", "TIMEZONE",
    "ID_DTYPE", "UNIT_DECLARATION", "MERGED_CELL", "MULTI_LEVEL_HEADER",
    "TRAILING_BLANK", "DUPLICATE_ROW", "NATURAL_LANGUAGE_DOSE",
    "NATURAL_LANGUAGE_TIME", "FREETEXT_COMMENT", "ENCODING", "LINE_ENDING",
    "DELIMITER", "SHEET_INVENTORY", "EXCEL_FORMULA", "EXCEL_DATE_SERIAL",
    "NON_ASCII_DECIMAL", "SCIENTIFIC_NOTATION", "LINEBREAK_IN_CELL",
    "COVARIATE_LAYOUT", "PRE_DOSE_CODING", "PLACEBO_SUBJECT",
    "LEGACY_FLAG_PRESENT", "RWD_ADHERENCE_UNRESOLVED",
]
uncov_mess = [d for d in MESS_DIMS if mess_cov[d] < 5]
check("All 28 mess dims >= 5", not uncov_mess,
      str(uncov_mess) if uncov_mess else f"min={min(mess_cov[d] for d in MESS_DIMS)}")

# 14. Fixtures exist
fixtures = list((ROOT / "fixtures" / "starts").glob("*.csv"))
check("Coverage fixtures generated", len(fixtures) > 0, f"{len(fixtures)} files")

# 15. c_units.json updated (104 + 2 = 106)
check("c_units.json has 106 entries (104+2)", len(cu) == 106, f"got {len(cu)}")

# 16. New c-units exist
new_ids = {"c0394", "c0396"}
existing = set(c["c_id"] for c in cu)
check("c0394 and c0396 present", new_ids.issubset(existing),
      str(new_ids - existing) if not new_ids.issubset(existing) else "")

# Summary
print(f"\n=== SUMMARY: {checks_passed}/{checks_total} checks passed ===")
term_dist = Counter(s["expected_terminal"] for s in sc)
print(f"Terminal: {dict(sorted(term_dist.items()))}")
print(f"Q-code min/max: {min(q_cov.values())}/{max(q_cov.values())}")
print(f"Mess dim min/max: {min(mess_cov[d] for d in MESS_DIMS)}/{max(mess_cov[d] for d in MESS_DIMS)}")
print(f"Fixtures: {len(fixtures)}")
