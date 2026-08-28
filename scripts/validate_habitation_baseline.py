"""
scripts/validate_habitation_baseline.py
========================================
SIH26191 -- Step 8D: Habitation Baseline Validation Script

PURPOSE
-------
Validates the output of Phase 8C (build_habitation_baseline.py) before
proceeding to Phase 8E (exposure overlay).

VALIDATION CHECKS
-----------------
1.  File exists
2.  CRS matches configured metric CRS
3.  Feature count = 653
4.  No duplicate village_id values
5.  No null geometries
6.  No null demographic fields
7.  No negative population values
8.  Population sum equals expected Census inhabited population
9.  Household sum is positive and reasonable
10. SC and ST population are within total population
11. Inhabited population coverage >= 100%

OUTPUTS
-------
docs/step8_habitation_baseline_validation.md  (validation report)

USAGE
-----
    python scripts/validate_habitation_baseline.py

Returns exit code 0 on PASS, 1 on FAIL.

Author: SIH26191 Processing Pipeline
"""

import sys
import io
import pathlib

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent
CONFIG_PATH  = PROJECT_ROOT / "configs" / "project.yaml"

if not CONFIG_PATH.exists():
    print(f"[FATAL] Config not found: {CONFIG_PATH}")
    sys.exit(1)

import yaml
import geopandas as gpd
import pandas as pd
from datetime import datetime

with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
    CONFIG = yaml.safe_load(fh)

METRIC_CRS = CONFIG["crs"]["analysis_crs_metric"]

BASELINE_GEOJSON = PROJECT_ROOT / CONFIG["paths"]["processed_dir"] / "habitations" / "habitation_baseline.geojson"
CENSUS_EXCEL     = PROJECT_ROOT / CONFIG["paths"]["raw_dir"] / "habitations" / "PCA_CDB-0503-F-Census.xlsx"
DOCS_DIR         = PROJECT_ROOT / "docs"
REPORT_PATH      = DOCS_DIR / "step8_habitation_baseline_validation.md"

DOCS_DIR.mkdir(parents=True, exist_ok=True)

EXPECTED_FEATURE_COUNT = 653

print("=" * 70)
print("SIH26191 -- Step 8D: Habitation Baseline Validation")
print("=" * 70)

checks = []   # list of (check_name, status, detail)
PASS = "PASS"
FAIL = "FAIL"
INFO = "INFO"

def add_check(name, passed, detail=""):
    status = PASS if passed else FAIL
    checks.append((name, status, detail))
    symbol = "[PASS]" if passed else "[FAIL]"
    print(f"  {symbol} {name}: {detail}")

# ---------------------------------------------------------------------------
# Load baseline
# ---------------------------------------------------------------------------
print()
print("[1] Loading habitation baseline ...")
if not BASELINE_GEOJSON.exists():
    print(f"[FATAL] Baseline file not found: {BASELINE_GEOJSON}")
    add_check("File exists", False, str(BASELINE_GEOJSON))
    # Write fail report and exit
    _write_report_and_exit(checks, REPORT_PATH, METRIC_CRS)

baseline = gpd.read_file(BASELINE_GEOJSON)
add_check("File exists", True, str(BASELINE_GEOJSON.relative_to(PROJECT_ROOT)))

print()
print("[2] Running validation checks ...")

# Check 2: CRS
crs_ok = str(baseline.crs).upper() == METRIC_CRS.upper()
add_check("CRS matches configured metric CRS", crs_ok,
          f"Actual: {baseline.crs} | Expected: {METRIC_CRS}")

# Check 3: Feature count
count_ok = len(baseline) == EXPECTED_FEATURE_COUNT
add_check("Feature count", count_ok,
          f"Actual: {len(baseline)} | Expected: {EXPECTED_FEATURE_COUNT}")

# Check 4: Duplicate village_id
dup_vids = baseline["village_id"].duplicated().sum()
add_check("No duplicate village_id", dup_vids == 0,
          f"Duplicate count: {dup_vids}")

# Check 5: Null geometries
null_geom = baseline.geometry.isnull().sum()
add_check("No null geometries", null_geom == 0,
          f"Null geometry count: {null_geom}")

# Check 6: No null demographic fields
demo_cols = ["households", "tot_pop", "pop_male", "pop_female", "pop_sc", "pop_st"]
demo_nulls = {col: baseline[col].isnull().sum() for col in demo_cols}
all_demo_ok = all(v == 0 for v in demo_nulls.values())
add_check("No null demographic fields", all_demo_ok,
          "Nulls: " + ", ".join(f"{k}={v}" for k, v in demo_nulls.items()))

# Check 7: No negative population
neg_pop = (baseline["tot_pop"] < 0).sum()
add_check("No negative tot_pop", neg_pop == 0,
          f"Negative population count: {neg_pop}")

# Check 8: Population sum cross-check against Census
print()
print("[3] Loading Census to cross-check population totals ...")
xl = pd.ExcelFile(CENSUS_EXCEL)
df_census = xl.parse(xl.sheet_names[0])
df_villages = df_census[df_census["Level"] == "VILLAGE"].copy()
census_inhabited_pop = int(df_villages[df_villages["TOT_P"] > 0]["TOT_P"].sum())
census_inhabited_hh  = int(df_villages[df_villages["TOT_P"] > 0]["No_HH"].sum())
census_inhabited_sc  = int(df_villages[df_villages["TOT_P"] > 0]["P_SC"].sum())
census_inhabited_st  = int(df_villages[df_villages["TOT_P"] > 0]["P_ST"].sum())
census_inhabited_villages = int((df_villages["TOT_P"] > 0).sum())

baseline_pop = int(baseline["tot_pop"].sum())
baseline_hh  = int(baseline["households"].sum())
baseline_sc  = int(baseline["pop_sc"].sum())
baseline_st  = int(baseline["pop_st"].sum())

pop_match = baseline_pop == census_inhabited_pop
add_check("Population sum matches Census inhabited total", pop_match,
          f"Baseline: {baseline_pop:,} | Census inhabited: {census_inhabited_pop:,}")

hh_match = baseline_hh == census_inhabited_hh
add_check("Household sum matches Census inhabited total", hh_match,
          f"Baseline: {baseline_hh:,} | Census inhabited: {census_inhabited_hh:,}")

sc_match = baseline_sc == census_inhabited_sc
add_check("SC population matches Census", sc_match,
          f"Baseline: {baseline_sc:,} | Census: {census_inhabited_sc:,}")

st_match = baseline_st == census_inhabited_st
add_check("ST population matches Census", st_match,
          f"Baseline: {baseline_st:,} | Census: {census_inhabited_st:,}")

# Check 9: Population coverage >= 100%
coverage_pct = (baseline_pop / census_inhabited_pop * 100) if census_inhabited_pop > 0 else 0.0
add_check("Population coverage >= 100%", coverage_pct >= 100.0,
          f"{coverage_pct:.2f}%")

# Check 10: SC/ST within bounds
sc_within = (baseline["pop_sc"] <= baseline["tot_pop"]).all()
add_check("SC population within total population", sc_within, "")
st_within = (baseline["pop_st"] <= baseline["tot_pop"]).all()
add_check("ST population within total population", st_within, "")

# ---------------------------------------------------------------------------
# Overall status
# ---------------------------------------------------------------------------
failed = [c for c in checks if c[1] == FAIL]
overall = "PASS" if not failed else "FAIL"

print()
print("=" * 70)
print(f"VALIDATION STATUS: {overall}")
print("=" * 70)
if failed:
    print("Failed checks:")
    for name, status, detail in failed:
        print(f"  - {name}: {detail}")
else:
    print("All checks passed.")

# ---------------------------------------------------------------------------
# Write markdown report
# ---------------------------------------------------------------------------
ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
lines = [
    "# Step 8D -- Habitation Baseline Validation Report",
    "",
    f"**Generated:** {ts}  ",
    f"**Project:** SIH26191 -- Rudraprayag District, Uttarakhand  ",
    f"**File validated:** `{BASELINE_GEOJSON.relative_to(PROJECT_ROOT)}`  ",
    "",
    "---",
    "",
    "## Summary Statistics",
    "",
    f"| Metric | Value |",
    f"|--------|-------|",
    f"| Feature count | {len(baseline):,} |",
    f"| CRS | {baseline.crs} |",
    f"| Total population | {baseline_pop:,} |",
    f"| Total households | {baseline_hh:,} |",
    f"| SC population | {baseline_sc:,} |",
    f"| ST population | {baseline_st:,} |",
    f"| Population coverage vs Census inhabited | {coverage_pct:.2f}% |",
    "",
    "---",
    "",
    "## Validation Checks",
    "",
    "| # | Check | Status | Detail |",
    "|---|-------|--------|--------|",
]
for i, (name, status, detail) in enumerate(checks, 1):
    icon = "PASS" if status == PASS else "**FAIL**"
    lines.append(f"| {i} | {name} | {icon} | {detail} |")

lines += [
    "",
    "---",
    "",
    f"## Overall Status: **{overall}**",
    "",
]

if overall == "PASS":
    lines += [
        "> All validation checks passed.",
        "> Proceed to Phase 8E: Hazard Exposure Overlay.",
        "",
    ]
else:
    lines += [
        "> **VALIDATION FAILED.** Do not proceed to Phase 8E.",
        "> Resolve all FAIL checks above before continuing.",
        "",
    ]

lines += [
    "---",
    "",
    "## Reference: Census Cross-Check Totals",
    "",
    f"| Metric | Census (inhabited) | Baseline |",
    f"|--------|-------------------|----------|",
    f"| Inhabited village records | {census_inhabited_villages} | {len(baseline)} |",
    f"| Total population | {census_inhabited_pop:,} | {baseline_pop:,} |",
    f"| Total households | {census_inhabited_hh:,} | {baseline_hh:,} |",
    f"| SC population | {census_inhabited_sc:,} | {baseline_sc:,} |",
    f"| ST population | {census_inhabited_st:,} | {baseline_st:,} |",
    "",
    "---",
    "",
    "*This document is a decision-support output of the SIH26191 pipeline.*",
    "*It does not constitute an official hazard zone declaration, evacuation order,*",
    "*safety certification, or relocation authorization.*",
]

report_text = "\n".join(lines)
REPORT_PATH.write_text(report_text, encoding="utf-8")
print()
print(f"[REPORT] Validation report written to: {REPORT_PATH.relative_to(PROJECT_ROOT)}")

if overall == "FAIL":
    sys.exit(1)

print()
print("Proceed to Phase 8E: Hazard Exposure Overlay.")
sys.exit(0)
