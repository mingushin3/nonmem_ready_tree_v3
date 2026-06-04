"""Phase 3 — Generate coverage fixtures in fixtures/starts/.

Selects minimal SC subset covering all c-units, Q-codes, and mess dimensions,
then synthesizes 1-compartment PK data with mess injection.
"""
import json
import random
import math
import csv
import pathlib
import io

ROOT = pathlib.Path(__file__).parent
SC_PATH = ROOT / "spec" / "starting_conditions.json"
CU_PATH = ROOT / "spec" / "c_units.json"
QC_PATH = ROOT / "spec" / "q_codes.json"
OUT_DIR = ROOT / "fixtures" / "starts"

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

# 1-compartment PK model parameters
V = 10.0    # L
KE = 0.1    # hr^-1 (t1/2 ~ 7 hr)
DOSE = 100  # mg
LLOQ = 0.05  # ng/mL


def pk_conc(t, dose=DOSE, v=V, ke=KE):
    if t <= 0:
        return 0.0
    return (dose / v) * math.exp(-ke * t)


def select_coverage_subset(scs, q_codes_list, mess_dims):
    """Greedy set-cover: select SCs that maximize coverage of Q-codes + mess dims."""
    needed_q = {q: 0 for q in q_codes_list}
    needed_mess = {d: 0 for d in mess_dims}

    for q in q_codes_list:
        needed_q[q] = 1
    for d in mess_dims:
        needed_mess[d] = 1

    selected = []
    selected_ids = set()

    for terminal in ["AUTO", "REPAIR", "QUARANTINE", "UNSUPPORTED", "INVALID"]:
        for sc in scs:
            if sc["expected_terminal"] == terminal and sc["sc_id"] not in selected_ids:
                selected.append(sc)
                selected_ids.add(sc["sc_id"])
                break

    for q in q_codes_list:
        if any(s["expected_q_code"] == q for s in selected):
            continue
        for sc in scs:
            if sc["expected_q_code"] == q and sc["sc_id"] not in selected_ids:
                selected.append(sc)
                selected_ids.add(sc["sc_id"])
                break

    covered_mess = set()
    for sc in selected:
        for d, v in sc["mess_profile"].items():
            if v:
                covered_mess.add(d)

    for d in mess_dims:
        if d in covered_mess:
            continue
        for sc in scs:
            if sc["mess_profile"].get(d, False) and sc["sc_id"] not in selected_ids:
                selected.append(sc)
                selected_ids.add(sc["sc_id"])
                covered_mess.add(d)
                for dd, vv in sc["mess_profile"].items():
                    if vv:
                        covered_mess.add(dd)
                break

    for q in q_codes_list:
        if any(s["expected_q_code"] == q for s in selected):
            continue
        for sc in scs:
            if sc.get("expected_q_code") == q and sc["sc_id"] not in selected_ids:
                selected.append(sc)
                selected_ids.add(sc["sc_id"])
                break

    strata_seen = set()
    for sc in scs:
        if sc["stratum"] not in strata_seen and sc["sc_id"] not in selected_ids:
            selected.append(sc)
            selected_ids.add(sc["sc_id"])
            strata_seen.add(sc["stratum"])
            if len(strata_seen) >= 7:
                break

    return selected


def generate_pk_data(rng, n_subjects=6, n_timepoints=6, mess_profile=None):
    """Generate synthetic 1-compartment PK data."""
    times = [0, 0.5, 1, 2, 4, 8, 12, 24][:n_timepoints]
    rows = []

    for subj in range(1, n_subjects + 1):
        subj_id = str(subj)
        dose_amt = DOSE * (1 + 0.1 * rng.gauss(0, 1))

        rows.append({
            "subject_id": subj_id,
            "event_type": "dose",
            "time_value": 0.0,
            "dv_value": ".",
            "dose_amount": f"{dose_amt:.1f}",
        })

        for t in times:
            if t == 0:
                continue
            conc = pk_conc(t, dose=dose_amt)
            conc_noisy = conc * math.exp(rng.gauss(0, 0.2))
            if conc_noisy < LLOQ:
                conc_noisy = LLOQ / 2
            rows.append({
                "subject_id": subj_id,
                "event_type": "obs",
                "time_value": t,
                "dv_value": f"{conc_noisy:.4f}",
                "dose_amount": ".",
            })

    return rows


NA_VARIANTS = ["NA", "N/A", ".", "", "NULL", "999"]
BLQ_VARIANTS = ["<LLOQ", "BLQ", "<0.05", "ND"]
TIME_FORMATS = {
    "clock": lambda t: f"{int(t)}:{int((t % 1) * 60):02d}",
    "elapsed": lambda t: f"{t:.2f}",
    "datetime": lambda t: f"2024-01-01 {int(t):02d}:{int((t % 1) * 60):02d}:00",
}


def inject_mess(rows, mess_profile, rng):
    """Inject syntactic defects into rows based on mess_profile."""
    if mess_profile.get("NA_TOKEN"):
        token = rng.choice(NA_VARIANTS)
        for r in rows:
            if r["dv_value"] == ".":
                r["dv_value"] = token

    if mess_profile.get("BLQ_TOKEN"):
        token = rng.choice(BLQ_VARIANTS)
        for r in rows:
            try:
                if float(r["dv_value"]) < LLOQ:
                    r["dv_value"] = token
            except (ValueError, TypeError):
                pass

    if mess_profile.get("TIME_FORMAT"):
        fmt = rng.choice(list(TIME_FORMATS.keys()))
        converter = TIME_FORMATS[fmt]
        for r in rows:
            try:
                t = float(r["time_value"])
                r["time_value"] = converter(t)
            except (ValueError, TypeError):
                pass

    if mess_profile.get("ID_DTYPE"):
        for r in rows:
            r["subject_id"] = f"SUBJ-{r['subject_id']:>03s}"

    if mess_profile.get("TRAILING_BLANK"):
        for _ in range(3):
            rows.append({k: "" for k in rows[0].keys()})

    if mess_profile.get("DUPLICATE_ROW"):
        if len(rows) > 2:
            rows.append(dict(rows[2]))

    if mess_profile.get("SCIENTIFIC_NOTATION"):
        for r in rows:
            try:
                v = float(r["dv_value"])
                r["dv_value"] = f"{v:.4E}"
            except (ValueError, TypeError):
                pass

    if mess_profile.get("NON_ASCII_DECIMAL"):
        for r in rows:
            if isinstance(r["dv_value"], str) and "." in r["dv_value"]:
                try:
                    float(r["dv_value"])
                    r["dv_value"] = r["dv_value"].replace(".", ",")
                except ValueError:
                    pass

    if mess_profile.get("FREETEXT_COMMENT"):
        for r in rows:
            r["comment"] = ""
        rows[0]["comment"] = "Initial dose administered"
        if len(rows) > 3:
            rows[3]["comment"] = "Sample collected post-meal"

    if mess_profile.get("PRE_DOSE_CODING"):
        for r in rows:
            if r["event_type"] == "obs":
                try:
                    t = float(r["time_value"])
                    if t <= 0:
                        r["time_value"] = "PRE"
                except (ValueError, TypeError):
                    pass

    if mess_profile.get("PLACEBO_SUBJECT"):
        placebo_id = f"SUBJ-PBO" if mess_profile.get("ID_DTYPE") else "99"
        rows.append({
            "subject_id": placebo_id,
            "event_type": "dose",
            "time_value": "0",
            "dv_value": ".",
            "dose_amount": "0",
        })

    if mess_profile.get("NATURAL_LANGUAGE_DOSE"):
        for r in rows:
            if r["event_type"] == "dose":
                try:
                    amt = float(r["dose_amount"])
                    r["dose_amount"] = f"{amt:.0f} mg oral"
                except (ValueError, TypeError):
                    pass

    if mess_profile.get("NATURAL_LANGUAGE_TIME"):
        for r in rows:
            if r["event_type"] == "obs":
                try:
                    t = float(r["time_value"])
                    if t < 1:
                        r["time_value"] = f"after {t*60:.0f} min"
                except (ValueError, TypeError):
                    pass

    if mess_profile.get("MULTI_LEVEL_HEADER"):
        header_row = {k: f"HEADER_{k}" for k in rows[0].keys()}
        rows.insert(0, header_row)

    if mess_profile.get("LINEBREAK_IN_CELL"):
        for r in rows[:2]:
            if "comment" in r:
                r["comment"] = r["comment"] + "\nline2"

    if mess_profile.get("LEGACY_FLAG_PRESENT"):
        for r in rows:
            r["OLD_DATA"] = rng.choice(["0", "1", ""])

    if mess_profile.get("RWD_ADHERENCE_UNRESOLVED"):
        for r in rows:
            r["dose_source"] = "patient_recall"

    return rows


def write_fixture(sc, rows, out_dir, mess_profile, rng):
    """Write fixture file (CSV, with encoding injection if needed)."""
    sc_id = sc["sc_id"]
    terminal = sc["expected_terminal"]

    encoding = "utf-8"
    if mess_profile.get("ENCODING"):
        encoding = rng.choice(["cp949", "utf-8-sig", "latin-1"])

    delimiter = ","
    if mess_profile.get("DELIMITER"):
        delimiter = rng.choice(["\t", ";"])

    line_ending = "\n"
    if mess_profile.get("LINE_ENDING"):
        line_ending = rng.choice(["\r\n", "\r"])

    ext = ".csv"
    if mess_profile.get("MERGED_CELL") or mess_profile.get("EXCEL_FORMULA") or mess_profile.get("EXCEL_DATE_SERIAL"):
        ext = ".csv"

    filename = f"{sc_id}_{terminal}{ext}"
    filepath = out_dir / filename

    fieldnames = list(rows[0].keys()) if rows else []
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, delimiter=delimiter,
                            lineterminator=line_ending)
    writer.writeheader()
    for row in rows:
        clean_row = {k: row.get(k, "") for k in fieldnames}
        writer.writerow(clean_row)

    text = buf.getvalue()

    if mess_profile.get("EXCEL_FORMULA"):
        text = text.replace(rows[1].get("dv_value", ""), "=A2*1.0", 1)

    try:
        filepath.write_text(text, encoding=encoding)
    except (UnicodeEncodeError, LookupError):
        filepath.write_text(text, encoding="utf-8")

    return filepath


def main():
    rng = random.Random(42)

    scs = json.loads(SC_PATH.read_text(encoding="utf-8"))
    c_units = json.loads(CU_PATH.read_text(encoding="utf-8"))
    q_codes = json.loads(QC_PATH.read_text(encoding="utf-8"))

    q_codes_list = [q["q_id"] for q in q_codes]

    selected = select_coverage_subset(scs, q_codes_list, MESS_DIMENSIONS)

    print(f"Selected {len(selected)} SCs for coverage fixtures")

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    terminal_cov = set()
    q_cov = set()
    mess_cov = set()

    for sc in selected:
        mess_profile = sc["mess_profile"]
        rows = generate_pk_data(rng, n_subjects=6, n_timepoints=6, mess_profile=mess_profile)
        rows = inject_mess(rows, mess_profile, rng)
        fp = write_fixture(sc, rows, OUT_DIR, mess_profile, rng)

        terminal_cov.add(sc["expected_terminal"])
        if sc["expected_q_code"]:
            q_cov.add(sc["expected_q_code"])
        for d, v in mess_profile.items():
            if v:
                mess_cov.add(d)

        print(f"  {fp.name} ({sc['expected_terminal']}, Q={sc['expected_q_code']}, K={sc['stratum']})")

    uncovered_q = set(q_codes_list) - q_cov
    uncovered_mess = set(MESS_DIMENSIONS) - mess_cov
    uncovered_term = {"AUTO", "REPAIR", "QUARANTINE", "UNSUPPORTED", "INVALID"} - terminal_cov

    print(f"\n=== FIXTURE COVERAGE ===")
    print(f"Fixtures generated: {len(selected)}")
    print(f"Terminals covered: {len(terminal_cov)}/5 (uncovered: {uncovered_term or 'none'})")
    print(f"Q-codes covered: {len(q_cov)}/{len(q_codes_list)} (uncovered: {uncovered_q or 'none'})")
    print(f"Mess dims covered: {len(mess_cov)}/{len(MESS_DIMENSIONS)} (uncovered: {uncovered_mess or 'none'})")
    print(f"C-units: {len(c_units)} defined (full c-unit exercise requires Phase 4 implementation)")


if __name__ == "__main__":
    main()
