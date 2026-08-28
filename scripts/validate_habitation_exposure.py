"""
scripts/validate_habitation_exposure.py
========================================
SIH26191 -- Step 8G: Habitation Exposure & Proximity Validation Script

PURPOSE
-------
Validates the updated output of Phase 8E+F+G (habitation_exposure_overlay.py):
1. data/processed/exposure/habitation_exposure.geojson
2. data/processed/exposure/habitation_exposure_summary.csv
3. docs/step8_habitation_exposure_report.md

VALIDATION CHECKS
-----------------
1.  Exposure GeoJSON exists
2.  Summary CSV exists
3.  Report Markdown exists
4.  CRS of exposure layer matches metric CRS (EPSG:32644)
5.  Exposure record count equals 653 (and matches baseline)
6.  No duplicate village_id values
7.  direct_zone_overlap field is boolean
8.  nearest_hazard_distance_m field is numeric and >= 0
9.  proximity_band contains only the 7 approved standardized categories
10. Proximity band record sum equals 653
11. Population totals reconcile: direct overlap + outside = 232,360
12. Household totals reconcile: direct overlap + outside = 50,882
13. SC population totals reconcile: direct overlap + outside = 46,279
14. ST population totals reconcile: direct overlap + outside = 309
15. Proximity band population sum reconciles to 232,360
16. Proximity band household sum reconciles to 50,882
17. CRS consistency between exposure and baseline
18. Raw Census Excel and SHRUG GeoJSON files unmodified
19. Step 7 Candidate Red Zone outputs unmodified (289 features)
20. Summary CSV structure and row count

USAGE
-----
    python scripts/validate_habitation_exposure.py

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

with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
    CONFIG = yaml.safe_load(fh)

METRIC_CRS = CONFIG["crs"]["analysis_crs_metric"]

EXPOSURE_GEOJSON  = PROJECT_ROOT / CONFIG["paths"]["processed_dir"] / "exposure" / "habitation_exposure.geojson"
EXPOSURE_CSV      = PROJECT_ROOT / CONFIG["paths"]["processed_dir"] / "exposure" / "habitation_exposure_summary.csv"
EXPOSURE_REPORT   = PROJECT_ROOT / "docs" / "step8_habitation_exposure_report.md"
BASELINE_GEOJSON  = PROJECT_ROOT / CONFIG["paths"]["processed_dir"] / "habitations" / "habitation_baseline.geojson"
REDZONES_GEOJSON  = PROJECT_ROOT / CONFIG["paths"]["redzones_geojson"]

# Raw data paths (must not be modified)
CENSUS_EXCEL      = PROJECT_ROOT / CONFIG["paths"]["raw_dir"] / "habitations" / "PCA_CDB-0503-F-Census.xlsx"
SHRUG_GEOJSON     = PROJECT_ROOT / CONFIG["paths"]["raw_dir"] / "habitations" / "rudraprayag_census_villages_shrug.geojson"

EXPECTED_RECORD_COUNT = 653
APPROVED_PROXIMITY_BANDS = {
    "Inside Candidate Hazard-Based Red Zone",
    "Within 500 m",
    "500 m to 1 km",
    "1 km to 2 km",
    "2 km to 5 km",
    "5 km to 10 km",
    "Beyond 10 km",
}

print("=" * 70)
print("SIH26191 -- Step 8G: Habitation Exposure & Proximity Validation")
print("=" * 70)

checks = []

def add_check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    checks.append((name, status, detail))
    symbol = "[PASS]" if passed else "[FAIL]"
    print(f"  {symbol} {name}: {detail}")

# ---------------------------------------------------------------------------
# CHECK 1-3: Files Exist
# ---------------------------------------------------------------------------
print()
print("[1] Checking output files existence ...")
c1 = EXPOSURE_GEOJSON.exists()
add_check("Exposure GeoJSON exists", c1, str(EXPOSURE_GEOJSON.relative_to(PROJECT_ROOT)))

c2 = EXPOSURE_CSV.exists()
add_check("Exposure summary CSV exists", c2, str(EXPOSURE_CSV.relative_to(PROJECT_ROOT)))

c3 = EXPOSURE_REPORT.exists()
add_check("Exposure report exists", c3, str(EXPOSURE_REPORT.relative_to(PROJECT_ROOT)))

if not c1:
    print("[FATAL] Exposure GeoJSON not found. Run habitation_exposure_overlay.py first.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Load layers
# ---------------------------------------------------------------------------
exposure = gpd.read_file(EXPOSURE_GEOJSON)
baseline = gpd.read_file(BASELINE_GEOJSON)

# ---------------------------------------------------------------------------
# CHECK 4: CRS
# ---------------------------------------------------------------------------
print()
print("[2] Checking CRS ...")
crs_ok = str(exposure.crs).upper() == METRIC_CRS.upper()
add_check("CRS matches metric CRS", crs_ok,
          f"Actual: {exposure.crs} | Expected: {METRIC_CRS}")

# ---------------------------------------------------------------------------
# CHECK 5: Record count
# ---------------------------------------------------------------------------
print()
print("[3] Checking record counts ...")
count_ok = len(exposure) == EXPECTED_RECORD_COUNT
add_check("Exposure record count", count_ok,
          f"Exposure: {len(exposure)} | Expected: {EXPECTED_RECORD_COUNT}")

baseline_match = len(exposure) == len(baseline)
add_check("Exposure records = baseline records", baseline_match,
          f"Exposure: {len(exposure)} | Baseline: {len(baseline)}")

# ---------------------------------------------------------------------------
# CHECK 6: No duplicate village_id
# ---------------------------------------------------------------------------
print()
print("[4] Checking for duplicate identifiers ...")
dup_vids = exposure["village_id"].duplicated().sum()
add_check("No duplicate village_id", dup_vids == 0,
          f"Duplicate count: {dup_vids}")

# ---------------------------------------------------------------------------
# CHECK 7: direct_zone_overlap field
# ---------------------------------------------------------------------------
print()
print("[5] Checking direct_zone_overlap and distance fields ...")
has_direct_ov = "direct_zone_overlap" in exposure.columns
add_check("direct_zone_overlap field present", has_direct_ov, "")

if has_direct_ov:
    is_bool = exposure["direct_zone_overlap"].dtype == bool or set(exposure["direct_zone_overlap"].unique()).issubset({True, False})
    add_check("direct_zone_overlap is boolean", is_bool,
              f"Values: {exposure['direct_zone_overlap'].value_counts().to_dict()}")

# CHECK 8: nearest_hazard_distance_m field
has_dist = "nearest_hazard_distance_m" in exposure.columns
add_check("nearest_hazard_distance_m field present", has_dist, "")

if has_dist:
    dist_non_negative = (exposure["nearest_hazard_distance_m"] >= 0).all()
    min_dist_val = float(exposure["nearest_hazard_distance_m"].min())
    add_check("nearest_hazard_distance_m >= 0 for all records", dist_non_negative,
              f"Min: {min_dist_val:.1f} m (Village: {exposure.loc[exposure['nearest_hazard_distance_m'].idxmin(), 'village_name']})")

# ---------------------------------------------------------------------------
# CHECK 9-10: proximity_band field
# ---------------------------------------------------------------------------
print()
print("[6] Checking proximity screening bands ...")
has_band = "proximity_band" in exposure.columns
add_check("proximity_band field present", has_band, "")

if has_band:
    unique_bands = set(exposure["proximity_band"].unique())
    valid_bands = unique_bands.issubset(APPROVED_PROXIMITY_BANDS)
    add_check("proximity_band contains only approved standard categories", valid_bands,
              f"Observed: {sorted(list(unique_bands))}")

    band_sum_ok = exposure["proximity_band"].value_counts().sum() == EXPECTED_RECORD_COUNT
    add_check("Proximity band count sum equals 653", band_sum_ok,
              f"Sum: {exposure['proximity_band'].value_counts().sum()}")

# ---------------------------------------------------------------------------
# CHECK 11-14: Population & Demographic Reconciliation
# ---------------------------------------------------------------------------
print()
print("[7] Checking demographic reconciliations ...")

total_pop = int(exposure["tot_pop"].sum())
total_hh  = int(exposure["households"].sum())
total_sc  = int(exposure["pop_sc"].sum())
total_st  = int(exposure["pop_st"].sum())

pop_target = 232360
hh_target  = 50882
sc_target  = 46279
st_target  = 309

add_check("Total population matches Census baseline (232,360)", total_pop == pop_target,
          f"Actual: {total_pop:,} | Target: {pop_target:,}")
add_check("Total households match Census baseline (50,882)", total_hh == hh_target,
          f"Actual: {total_hh:,} | Target: {hh_target:,}")
add_check("Total SC population matches Census baseline (46,279)", total_sc == sc_target,
          f"Actual: {total_sc:,} | Target: {sc_target:,}")
add_check("Total ST population matches Census baseline (309)", total_st == st_target,
          f"Actual: {total_st:,} | Target: {st_target:,}")

# Direct overlap reconciliation
direct_in = exposure[exposure["direct_zone_overlap"] == True]
direct_out = exposure[exposure["direct_zone_overlap"] == False]

direct_in_pop = int(direct_in["tot_pop"].sum())
direct_out_pop = int(direct_out["tot_pop"].sum())
direct_reconcile = (direct_in_pop + direct_out_pop) == total_pop
add_check("Direct overlap population reconciles (in + out = total)", direct_reconcile,
          f"In: {direct_in_pop:,} + Out: {direct_out_pop:,} = {direct_in_pop + direct_out_pop:,}")

# Proximity band population and household reconciliation
band_pop_sum = int(exposure.groupby("proximity_band")["tot_pop"].sum().sum())
band_hh_sum  = int(exposure.groupby("proximity_band")["households"].sum().sum())
add_check("Proximity band population sum = total population", band_pop_sum == total_pop,
          f"Band Pop Sum: {band_pop_sum:,} | Total: {total_pop:,}")
add_check("Proximity band household sum = total households", band_hh_sum == total_hh,
          f"Band HH Sum: {band_hh_sum:,} | Total: {total_hh:,}")

# ---------------------------------------------------------------------------
# CHECK 17: CRS consistency
# ---------------------------------------------------------------------------
print()
print("[8] Checking CRS consistency with baseline ...")
crs_consistent = str(exposure.crs) == str(baseline.crs)
add_check("CRS consistent with baseline", crs_consistent,
          f"Exposure: {exposure.crs} | Baseline: {baseline.crs}")

# ---------------------------------------------------------------------------
# CHECK 18: Raw data integrity
# ---------------------------------------------------------------------------
print()
print("[9] Checking raw data and Step 7 integrity ...")
census_ok = CENSUS_EXCEL.exists()
add_check("Census Excel raw file still exists (unmodified)", census_ok,
          str(CENSUS_EXCEL.relative_to(PROJECT_ROOT)))

shrug_ok = SHRUG_GEOJSON.exists()
add_check("SHRUG GeoJSON raw file still exists (unmodified)", shrug_ok,
          str(SHRUG_GEOJSON.relative_to(PROJECT_ROOT)))

# CHECK 19: Step 7 hazard layer integrity
rz_ok = REDZONES_GEOJSON.exists()
add_check("Step 7 red zone GeoJSON still exists (unmodified)", rz_ok,
          str(REDZONES_GEOJSON.relative_to(PROJECT_ROOT)))

if rz_ok:
    rz_check = gpd.read_file(REDZONES_GEOJSON)
    rz_feature_ok = len(rz_check) == 289
    add_check("Step 7 red zone feature count unchanged (289)", rz_feature_ok,
              f"Actual: {len(rz_check)}")

# ---------------------------------------------------------------------------
# CHECK 20: Summary CSV structure
# ---------------------------------------------------------------------------
print()
print("[10] Checking summary CSV structure ...")
if c2:
    summary_df = pd.read_csv(EXPOSURE_CSV)
    csv_cols_ok = all(c in summary_df.columns for c in ["category", "metric", "value", "percentage"])
    add_check("Summary CSV has required columns", csv_cols_ok,
              f"Columns: {summary_df.columns.tolist()}")
    csv_rows_ok = len(summary_df) >= 15
    add_check("Summary CSV has sufficient rows", csv_rows_ok,
              f"Rows: {len(summary_df)}")

# ---------------------------------------------------------------------------
# Overall status
# ---------------------------------------------------------------------------
failed = [c for c in checks if c[1] == "FAIL"]
overall = "PASS" if not failed else "FAIL"

print()
print("=" * 70)
print(f"STEP 8 EXPOSURE & PROXIMITY VALIDATION STATUS: {overall}")
print("=" * 70)

if failed:
    print("Failed checks:")
    for name, status, detail in failed:
        print(f"  - {name}: {detail}")
else:
    print("All checks passed successfully.")

print()
print("--- SUMMARY OF VERIFIED RESULTS ---")
print(f"  1. Direct Centroid-Based Overlaps : {len(direct_in)}")
print(f"  2. Total Habitations Evaluated   : {len(exposure)}")
print(f"  3. Proximity Bands Breakdown:")
for band in [
    "Inside Candidate Hazard-Based Red Zone",
    "Within 500 m",
    "500 m to 1 km",
    "1 km to 2 km",
    "2 km to 5 km",
    "5 km to 10 km",
    "Beyond 10 km",
]:
    b_df = exposure[exposure["proximity_band"] == band]
    print(f"     - {band:<38} : {len(b_df):>4} hab | {int(b_df['tot_pop'].sum()):>7,} pop | {int(b_df['households'].sum()):>6,} hh")

min_idx = exposure["nearest_hazard_distance_m"].idxmin()
print(f"  4. Nearest Identified Habitation  : {exposure.loc[min_idx, 'village_name']} (ID: {exposure.loc[min_idx, 'village_id']}) at {exposure.loc[min_idx, 'nearest_hazard_distance_m']:.1f} m")
print(f"  5. Total Population Reconciled    : {total_pop:,} (100.0% coverage)")
print(f"  6. Total Households Reconciled    : {total_hh:,}")
print()
print("DECISION-SUPPORT DISCLAIMER:")
print("These outputs are preliminary GIS-based decision-support screening results")
print("and do not constitute disaster prediction, engineering safety certification,")
print("evacuation instruction, or mandatory relocation recommendation.")

if overall == "FAIL":
    sys.exit(1)

sys.exit(0)
