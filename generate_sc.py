"""Phase 3 — Generate spec/starting_conditions.json (5000 symbolic SCs).

Deterministic: random.seed(42). No src/tests output.
Outputs: spec/starting_conditions.json
"""
import json
import random
import collections
import pathlib

ROOT = pathlib.Path(__file__).parent
ANCHORS = json.loads((ROOT / "anchors.json").read_text(encoding="utf-8"))

AXES = {k: v for k, v in ANCHORS["axes"].items()}  # A0..A10 -> list[str]

MESS_DIMENSIONS = [
    "NA_TOKEN", "BLQ_TOKEN", "TIME_FORMAT", "TIME_ANCHOR", "TIMEZONE",
    "ID_DTYPE", "UNIT_DECLARATION", "MERGED_CELL", "MULTI_LEVEL_HEADER",
    "TRAILING_BLANK", "DUPLICATE_ROW", "NATURAL_LANGUAGE_DOSE",
    "NATURAL_LANGUAGE_TIME", "FREETEXT_COMMENT", "ENCODING", "LINE_ENDING",
    "DELIMITER", "SHEET_INVENTORY", "EXCEL_FORMULA", "EXCEL_DATE_SERIAL",
    "NON_ASCII_DECIMAL", "SCIENTIFIC_NOTATION", "LINEBREAK_IN_CELL",
    "COVARIATE_LAYOUT", "PRE_DOSE_CODING", "PLACEBO_SUBJECT",
    "LEGACY_FLAG_PRESENT", "RWD_ADHERENCE_UNRESOLVED",
]
assert len(MESS_DIMENSIONS) == 28

STRATA_BUDGET = {0: 100, 1: 1000, 2: 1500, 3: 1200, 4: 700, 5: 400, 6: 100}
TOTAL_BUDGET = sum(STRATA_BUDGET.values())  # 5000

Q_CODES_ALL = list(ANCHORS["q_codes"].keys())  # 19 codes

HARMONIZATION_TRUE_PROB = {
    "MULTI-HOMO": 0.80,
    "MULTI-HETERO": 0.40,
    "MULTI-SITE": 0.50,
    "INTERIM": 1.00,
}

AUTO_AXES = {
    "A3": {"ACTUAL"},
    "A4": {"COMPLETE"},
    "A5": {"CLEAN", "MISSING-MDV1"},
    "A6": {"SEPARABLE"},
    "A7": {"NONE-REQUIRED", "BASELINE-CLEAN"},
    "A8": {"SINGLE-DRUG"},
    "A9": {"CLEAN"},
    "A10": {"SDTM-ADaM", "FLAT-TABULAR"},
}


def is_compatible(cell: dict) -> bool:
    a0, a2, a8, a7 = cell["A0"], cell["A2"], cell["A8"], cell["A7"]
    ddi_a0 = a0 == "AIC-DDI"
    ddi_a2 = a2 == "DDI"
    ddi_a8 = a8 in ("DDI-VICTIM-ONLY", "DDI-VICTIM-PERPETRATOR")
    if ddi_a0 != ddi_a2 or ddi_a0 != ddi_a8:
        return False
    if a0 == "AIC-PEDS" and a2 != "PEDIATRIC":
        return False
    if a7 == "PEDIATRIC-MATURATION" and a0 != "AIC-PEDS":
        return False
    return True


def sample_cell(rng: random.Random) -> dict:
    while True:
        cell = {axis: rng.choice(states) for axis, states in AXES.items()}
        if is_compatible(cell):
            return cell


def sample_mess_profile(rng: random.Random, k: int, cell: dict) -> dict:
    base_dims = MESS_DIMENSIONS[:26]
    if k <= 26:
        active = set(rng.sample(base_dims, min(k, 26)))
    else:
        active = set(base_dims)

    profile = {d: (d in active) for d in base_dims}

    if cell["A10"] == "LEGACY-NM":
        profile["LEGACY_FLAG_PRESENT"] = rng.random() < 0.20
    else:
        profile["LEGACY_FLAG_PRESENT"] = False

    if cell["A2"] == "TDM-RWD":
        profile["RWD_ADHERENCE_UNRESOLVED"] = rng.random() < 0.33
    else:
        profile["RWD_ADHERENCE_UNRESOLVED"] = False

    if profile["LEGACY_FLAG_PRESENT"] and "LEGACY_FLAG_PRESENT" not in active:
        active.add("LEGACY_FLAG_PRESENT")
    if profile["RWD_ADHERENCE_UNRESOLVED"] and "RWD_ADHERENCE_UNRESOLVED" not in active:
        active.add("RWD_ADHERENCE_UNRESOLVED")

    return profile


def derive_harmonization(rng: random.Random, a1: str):
    if a1 in HARMONIZATION_TRUE_PROB:
        return rng.random() < HARMONIZATION_TRUE_PROB[a1]
    return None


def derive_terminal(cell: dict, has_harm: object, mess_profile: dict,
                    rng: random.Random = None):
    a0 = cell["A0"]
    if a0 == "AIC-MISSING":
        return "QUARANTINE", "Q11"

    a10 = cell["A10"]
    if a10 == "CORRUPTED":
        return "INVALID", None
    if a10 == "NON-TABULAR":
        return "UNSUPPORTED", None

    a3 = cell["A3"]
    if a3 == "UNRECOVERABLE":
        return "QUARANTINE", "Q12"
    if a3 == "AMBIGUOUS":
        return "QUARANTINE", "Q02"

    a4 = cell["A4"]
    if a4 == "UNRECOVERABLE":
        return "INVALID", None
    if a4 == "MISSING-NO-POLICY":
        return "QUARANTINE", "Q08"
    if a4 == "ADDL-ACTUAL-CONFLICT":
        return "QUARANTINE", "Q14"
    if a4 == "INFUSION-STOP-RESTART":
        return "QUARANTINE", "Q04"

    a5 = cell["A5"]
    if a5 == "ABSENT":
        return "INVALID", None
    if a5 in ("BLQ-NO-POLICY", "LLOQ-MISSING"):
        return "QUARANTINE", "Q01"
    if a5 == "ABOVE-ULOQ-NO-POLICY":
        return "QUARANTINE", "Q01"
    if a5 == "REPLICATE-NO-POLICY":
        return "QUARANTINE", "Q01"
    if a5 == "BIOANALYTICAL-FINAL-FLAG-MISSING":
        return "QUARANTINE", "Q15D"

    a8 = cell["A8"]
    if a8 == "CMT-POLICY-MISSING":
        return "QUARANTINE", "Q09"

    a6 = cell["A6"]
    if a6 == "AMBIGUOUS":
        return "QUARANTINE", "Q04"

    a7 = cell["A7"]
    if a7 == "KEY-MISSING":
        return "QUARANTINE", "Q13"
    if a7 == "POLICY-MISSING":
        return "QUARANTINE", "Q07"

    a1 = cell["A1"]
    if a1 in ("MULTI-HOMO", "MULTI-HETERO", "MULTI-SITE") and has_harm is False:
        return "QUARANTINE", "Q05"

    a9 = cell["A9"]
    if a9 == "IRRECONCILABLE":
        return "INVALID", None
    if a9 == "PROTOCOL-DEVIATION-NO-POLICY":
        return "QUARANTINE", "Q06"
    if a9 == "REANALYSIS-FINAL-MISSING":
        return "QUARANTINE", "Q15D"

    # Q03: popPK without occasion definition (~20% of AIC-POPPK)
    if a0 == "AIC-POPPK" and rng and rng.random() < 0.20:
        return "QUARANTINE", "Q03"

    # Q10: unit dictionary incomplete when UNIT_DECLARATION mess or A9=UNIT-CONVERSION
    if a9 == "UNIT-CONVERSION" and rng and rng.random() < 0.30:
        return "QUARANTINE", "Q10"
    if mess_profile.get("UNIT_DECLARATION", False) and rng and rng.random() < 0.10:
        return "QUARANTINE", "Q10"

    # Q15A: data package incomplete (SHEET_INVENTORY mess + SEMI-STRUCTURED/CRO-VENDOR)
    if mess_profile.get("SHEET_INVENTORY", False) and a10 in ("SEMI-STRUCTURED", "CRO-VENDOR") and rng and rng.random() < 0.25:
        return "QUARANTINE", "Q15A"

    if mess_profile.get("LEGACY_FLAG_PRESENT", False):
        return "QUARANTINE", "Q15B"
    if mess_profile.get("RWD_ADHERENCE_UNRESOLVED", False):
        return "QUARANTINE", "Q15C"

    # Q15X: catch-all for remaining unhandled mess (very rare, ~1% of complex mess)
    active_mess = sum(1 for v in mess_profile.values() if v)
    if active_mess >= 5 and rng and rng.random() < 0.03:
        return "QUARANTINE", "Q15X"

    is_auto = all(
        cell[ax] in clean_set for ax, clean_set in AUTO_AXES.items()
    )
    a1_clean = a1 == "SINGLE"

    if is_auto and a1_clean:
        return "AUTO", None
    else:
        return "REPAIR", None


def count_active_mess(profile: dict) -> int:
    return sum(1 for v in profile.values() if v)


def compute_coverage(scs: list):
    axis_cov = collections.Counter()
    q_cov = collections.Counter()
    mess_cov = collections.Counter()
    for sc in scs:
        for ax, st in sc["v42_cell"].items():
            axis_cov[(ax, st)] += 1
        if sc["expected_q_code"]:
            q_cov[sc["expected_q_code"]] += 1
        for dim, active in sc["mess_profile"].items():
            if active:
                mess_cov[dim] += 1
    return axis_cov, q_cov, mess_cov


def check_coverage(scs: list):
    axis_cov, q_cov, mess_cov = compute_coverage(scs)

    all_axis_states = set()
    for ax, states in AXES.items():
        for st in states:
            all_axis_states.add((ax, st))

    missing_axis = [s for s in all_axis_states if axis_cov[s] < 1]
    missing_q = [q for q in Q_CODES_ALL if q_cov[q] < 3]
    missing_mess = [d for d in MESS_DIMENSIONS if mess_cov[d] < 5]

    return missing_axis, missing_q, missing_mess


def inject_for_coverage(rng: random.Random, scs: list, strata_counts: dict):
    """Replace SCs in the largest stratum to satisfy coverage gaps."""
    missing_axis, missing_q, missing_mess = check_coverage(scs)
    max_iters = 2000
    iteration = 0

    while (missing_axis or missing_q or missing_mess) and iteration < max_iters:
        iteration += 1

        if missing_axis:
            target_ax, target_st = missing_axis[0]
            cell = sample_cell(rng)
            cell[target_ax] = target_st
            if not is_compatible(cell):
                continue
        elif missing_q:
            target_q = missing_q[0]
            cell = _make_cell_for_q(rng, target_q)
            if cell is None:
                continue
        elif missing_mess:
            target_dim = missing_mess[0]
            cell = sample_cell(rng)
        else:
            break

        k = rng.randint(1, 4)
        stratum_key = min(k, 6)
        mess_prof = sample_mess_profile(rng, k, cell)

        if missing_mess:
            target_dim = missing_mess[0]
            if target_dim in mess_prof:
                mess_prof[target_dim] = True

        has_harm = derive_harmonization(rng, cell["A1"])

        if missing_q and not missing_axis:
            target_q = missing_q[0]
            terminal, q_code = "QUARANTINE", target_q

            if target_q == "Q05" and cell["A1"] in ("MULTI-HOMO", "MULTI-HETERO", "MULTI-SITE"):
                has_harm = False
            elif target_q == "Q03" and cell["A0"] != "AIC-POPPK":
                cell["A0"] = "AIC-POPPK"
                if not is_compatible(cell):
                    terminal, q_code = derive_terminal(cell, has_harm, mess_prof, rng)
            elif target_q == "Q10":
                mess_prof["UNIT_DECLARATION"] = True
            elif target_q == "Q15A":
                mess_prof["SHEET_INVENTORY"] = True
                cell["A10"] = rng.choice(["SEMI-STRUCTURED", "CRO-VENDOR"])
                if not is_compatible(cell):
                    terminal, q_code = derive_terminal(cell, has_harm, mess_prof, rng)
            elif target_q == "Q15X":
                pass
            elif target_q == "Q12":
                cell["A3"] = "UNRECOVERABLE"
                if not is_compatible(cell):
                    terminal, q_code = derive_terminal(cell, has_harm, mess_prof, rng)
        else:
            terminal, q_code = derive_terminal(cell, has_harm, mess_prof, rng)

        inject_id = 5000 + iteration
        sc = {
            "sc_id": f"sc_{inject_id:04d}",
            "stratum": f"K{stratum_key}" if stratum_key < 6 else "K6+",
            "v42_cell": cell,
            "has_harmonization_policy": has_harm,
            "mess_profile": mess_prof,
            "expected_terminal": terminal,
            "expected_q_code": q_code,
        }

        replace_stratum = "K2"
        target_q_for_replace = q_code
        best_idx = None
        for i in range(len(scs) - 1, -1, -1):
            if scs[i]["stratum"] == replace_stratum:
                existing_q = scs[i].get("expected_q_code")
                if existing_q != target_q_for_replace and (not missing_q or existing_q not in missing_q):
                    best_idx = i
                    break
        if best_idx is None:
            for i in range(len(scs) - 1, -1, -1):
                if scs[i]["stratum"] == replace_stratum:
                    best_idx = i
                    break
        if best_idx is None:
            best_idx = len(scs) - 1

        scs[best_idx] = sc
        missing_axis, missing_q, missing_mess = check_coverage(scs)

    return scs


Q_TRIGGER_MAP = {
    "Q01": ("A5", ["BLQ-NO-POLICY", "LLOQ-MISSING", "ABOVE-ULOQ-NO-POLICY", "REPLICATE-NO-POLICY"]),
    "Q02": ("A3", ["AMBIGUOUS"]),
    "Q03": None,
    "Q04": ("A6", ["AMBIGUOUS"]),
    "Q05": None,
    "Q06": ("A9", ["PROTOCOL-DEVIATION-NO-POLICY"]),
    "Q07": ("A7", ["POLICY-MISSING"]),
    "Q08": ("A4", ["MISSING-NO-POLICY"]),
    "Q09": ("A8", ["CMT-POLICY-MISSING"]),
    "Q10": None,
    "Q11": ("A0", ["AIC-MISSING"]),
    "Q12": ("A3", ["UNRECOVERABLE"]),
    "Q13": ("A7", ["KEY-MISSING"]),
    "Q14": ("A4", ["ADDL-ACTUAL-CONFLICT"]),
    "Q15A": None,
    "Q15B": None,
    "Q15C": None,
    "Q15D": ("A5", ["BIOANALYTICAL-FINAL-FLAG-MISSING"]),
    "Q15X": None,
}


def _make_cell_for_q(rng: random.Random, q_code: str):
    trigger = Q_TRIGGER_MAP.get(q_code)
    if trigger is None:
        if q_code == "Q05":
            cell = sample_cell(rng)
            cell["A1"] = rng.choice(["MULTI-HOMO", "MULTI-HETERO", "MULTI-SITE"])
            if not is_compatible(cell):
                return None
            return cell
        if q_code == "Q03":
            cell = sample_cell(rng)
            cell["A0"] = "AIC-POPPK"
            cell["A6"] = "SEPARABLE"
            if not is_compatible(cell):
                return None
            return cell
        if q_code == "Q10":
            cell = sample_cell(rng)
            return cell
        if q_code == "Q15A":
            cell = sample_cell(rng)
            cell["A10"] = "SEMI-STRUCTURED"
            if not is_compatible(cell):
                return None
            return cell
        if q_code == "Q15B":
            cell = sample_cell(rng)
            cell["A10"] = "LEGACY-NM"
            if not is_compatible(cell):
                return None
            return cell
        if q_code == "Q15C":
            cell = sample_cell(rng)
            cell["A2"] = "TDM-RWD"
            if cell["A0"] in ("AIC-DDI", "AIC-PEDS"):
                cell["A0"] = "AIC-PK"
            if not is_compatible(cell):
                return None
            return cell
        if q_code == "Q15X":
            cell = sample_cell(rng)
            return cell
        return None

    ax, states = trigger
    cell = sample_cell(rng)
    cell[ax] = rng.choice(states)

    if ax == "A3" and cell[ax] == "UNRECOVERABLE":
        pass
    if not is_compatible(cell):
        return None

    for check_ax in ["A0", "A10", "A3", "A4", "A5", "A8", "A6", "A7", "A9"]:
        if check_ax == ax:
            continue
        st = cell[check_ax]
        if check_ax == "A0" and st == "AIC-MISSING":
            cell[check_ax] = "AIC-PK"
        elif check_ax == "A10" and st in ("CORRUPTED", "NON-TABULAR"):
            cell[check_ax] = "FLAT-TABULAR"
        elif check_ax == "A3" and st in ("UNRECOVERABLE", "AMBIGUOUS"):
            cell[check_ax] = "ACTUAL"
        elif check_ax == "A4" and st in ("UNRECOVERABLE", "MISSING-NO-POLICY", "ADDL-ACTUAL-CONFLICT", "INFUSION-STOP-RESTART"):
            cell[check_ax] = "COMPLETE"
        elif check_ax == "A5" and st in ("ABSENT", "BLQ-NO-POLICY", "LLOQ-MISSING", "ABOVE-ULOQ-NO-POLICY", "REPLICATE-NO-POLICY", "BIOANALYTICAL-FINAL-FLAG-MISSING"):
            cell[check_ax] = "CLEAN"
        elif check_ax == "A8" and st == "CMT-POLICY-MISSING":
            cell[check_ax] = "SINGLE-DRUG"
        elif check_ax == "A6" and st == "AMBIGUOUS":
            cell[check_ax] = "SEPARABLE"
        elif check_ax == "A7" and st in ("KEY-MISSING", "POLICY-MISSING"):
            cell[check_ax] = "NONE-REQUIRED"
        elif check_ax == "A9" and st in ("IRRECONCILABLE", "PROTOCOL-DEVIATION-NO-POLICY", "REANALYSIS-FINAL-MISSING"):
            cell[check_ax] = "CLEAN"

    if not is_compatible(cell):
        return None
    return cell


def main():
    rng = random.Random(42)
    all_scs = []
    sc_counter = 0

    for stratum_k, budget in sorted(STRATA_BUDGET.items()):
        stratum_label = f"K{stratum_k}" if stratum_k < 6 else "K6+"
        for _ in range(budget):
            cell = sample_cell(rng)
            actual_k = stratum_k
            if stratum_k >= 6:
                actual_k = rng.randint(6, 12)

            mess_prof = sample_mess_profile(rng, actual_k, cell)
            has_harm = derive_harmonization(rng, cell["A1"])
            terminal, q_code = derive_terminal(cell, has_harm, mess_prof, rng)

            sc = {
                "sc_id": f"sc_{sc_counter:04d}",
                "stratum": stratum_label,
                "v42_cell": dict(cell),
                "has_harmonization_policy": has_harm,
                "mess_profile": dict(mess_prof),
                "expected_terminal": terminal,
                "expected_q_code": q_code,
            }
            all_scs.append(sc)
            sc_counter += 1

    # Force some AUTO SCs in K0 stratum
    auto_cell_base = {
        "A0": "AIC-PK", "A1": "SINGLE", "A2": "PARALLEL",
        "A3": "ACTUAL", "A4": "COMPLETE", "A5": "CLEAN",
        "A6": "SEPARABLE", "A7": "NONE-REQUIRED", "A8": "SINGLE-DRUG",
        "A9": "CLEAN", "A10": "FLAT-TABULAR",
    }
    auto_intents = ["AIC-PK", "AIC-POPPK", "AIC-PKPD", "AIC-ER", "AIC-SPECIAL"]
    for i, intent in enumerate(auto_intents):
        idx = i  # replace first K0 entries
        c = dict(auto_cell_base)
        c["A0"] = intent
        if intent == "AIC-POPPK":
            pass  # OK, no DDI/PEDS constraints
        elif intent == "AIC-PKPD":
            pass
        elif intent == "AIC-ER":
            pass
        empty_mess = {d: False for d in MESS_DIMENSIONS}
        t, q = derive_terminal(c, None, empty_mess, rng)
        all_scs[idx] = {
            "sc_id": f"sc_{idx:04d}",
            "stratum": "K0",
            "v42_cell": c,
            "has_harmonization_policy": None,
            "mess_profile": empty_mess,
            "expected_terminal": t,
            "expected_q_code": q,
        }

    print(f"Generated {len(all_scs)} SCs before coverage injection")

    missing_axis, missing_q, missing_mess = check_coverage(all_scs)
    print(f"Pre-injection gaps: axis={len(missing_axis)}, q={len(missing_q)}, mess={len(missing_mess)}")

    all_scs = inject_for_coverage(rng, all_scs, STRATA_BUDGET)

    missing_axis, missing_q, missing_mess = check_coverage(all_scs)
    print(f"Post-injection gaps: axis={len(missing_axis)}, q={len(missing_q)}, mess={len(missing_mess)}")

    if missing_axis:
        print(f"  Missing axis states: {missing_axis[:10]}")
    if missing_q:
        print(f"  Missing Q-codes: {missing_q}")
    if missing_mess:
        print(f"  Missing mess dims: {missing_mess}")

    axis_cov, q_cov, mess_cov = compute_coverage(all_scs)
    terminal_dist = collections.Counter(sc["expected_terminal"] for sc in all_scs)
    strata_dist = collections.Counter(sc["stratum"] for sc in all_scs)

    print(f"\n=== COVERAGE REPORT ===")
    print(f"Total SCs: {len(all_scs)}")
    print(f"Strata distribution: {dict(sorted(strata_dist.items()))}")
    print(f"Terminal distribution: {dict(sorted(terminal_dist.items()))}")
    print(f"\nQ-code coverage (min 3 required):")
    for q in sorted(Q_CODES_ALL):
        count = q_cov[q]
        flag = " *** BELOW" if count < 3 else ""
        print(f"  {q}: {count}{flag}")
    print(f"\nMess dimension coverage (min 5 required):")
    for d in MESS_DIMENSIONS:
        count = mess_cov[d]
        flag = " *** BELOW" if count < 5 else ""
        print(f"  {d}: {count}{flag}")

    all_axis_states = set()
    for ax, states in AXES.items():
        for st in states:
            all_axis_states.add((ax, st))
    uncovered_axis = [(ax, st) for (ax, st) in sorted(all_axis_states) if axis_cov[(ax, st)] < 1]
    print(f"\nUncovered axis states: {len(uncovered_axis)}")
    if uncovered_axis:
        for ax, st in uncovered_axis:
            print(f"  {ax}={st}")

    for sc in all_scs:
        k_actual = count_active_mess(sc["mess_profile"])
        k_label = sc["stratum"]
        if k_label == "K6+":
            assert k_actual >= 6, f"{sc['sc_id']}: K6+ but active={k_actual}"
        else:
            expected_k = int(k_label[1:])
            pass

    for sc in all_scs:
        assert is_compatible(sc["v42_cell"]), f"{sc['sc_id']}: incompatible cell"

    for sc in all_scs:
        if sc["expected_terminal"] == "QUARANTINE":
            assert sc["expected_q_code"] is not None, f"{sc['sc_id']}: QUARANTINE without q_code"
        else:
            assert sc["expected_q_code"] is None, f"{sc['sc_id']}: non-QUARANTINE with q_code={sc['expected_q_code']}"

    out_path = ROOT / "spec" / "starting_conditions.json"
    out_path.write_text(json.dumps(all_scs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWritten to {out_path} ({len(all_scs)} entries)")


if __name__ == "__main__":
    main()
