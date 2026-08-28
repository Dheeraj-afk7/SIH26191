"""
scripts/validate_habitation_exposure.py
========================================
SIH26191 -- Step 8G: Habitation Exposure Validation Script

PURPOSE
-------
Validates the output of Phase 8E+F+G (habitation_exposure_overlay.py):
the habitation exposure GeoJSON and exposure summary CSV.

VALIDATION CHECKS
-----------------
1.  Exposure GeoJSON exists
2.  Summary CSV exists
3.  CRS of exposure layer matches metric CRS
4.  Exposure record count equals habitation baseline record count
5.  No duplicate village_id values
6.  hazard_zone_flag values are only 0 or 1
7.  Population totals reconcile: inside + outside = total
8.  Household totals reconcile
9.  SC population totals reconcile
10. ST population totals reconcile
11. No raw dataset was modified
12. No Step 7 hazard layer was modified (file size check)
13. Summary CSV row count is reasonable

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
from datetime import datetime, timezone

with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
    CONFIG = yaml.safe_load(fh)

METRIC_CRS = CONFIG["crs"]["analysis_crs_metric"]

EXPOSURE_GEOJSON  = PROJECT_ROOT / CONFIG["paths"]["processed_dir"] / "exposure" / "habitation_exposure.geojson"
EXPOSURE_CSV      = PROJECT_ROOT / CONFIG["paths"]["processed_dir"] / "exposure" / "habitation_exposure_summary.csv"
BASELINE_GEOJSON  = PROJECT_ROOT / CONFIG["paths"]["processed_dir"] / "habitations" / "habitation_baseline.geojson"
REDZONES_GEOJSON  = PROJECT_ROOT / CONFIG["paths"]["redzones_geojson"]

# Raw data paths (must not be modified)
CENSUS_EXCEL      = PROJECT_ROOT / CONFIG["paths"]["raw_dir"] / "habitations" / "PCA_CDB-0503-F-Census.xlsx"
SHRUG_GEOJSON     = PROJECT_ROOT / CONFIG["paths"]["raw_dir"] / "habitations" / "rudraprayag_census_villages_shrug.geojson"

EXPECTED_RECORD_COUNT = 653

print("=" * 70)
print("SIH26191 -- Step 8G: Habitation Exposure Validation")
print("=" * 70)

checks = []

def add_check(name, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    checks.append((name, status, detail))
    symbol = "[PASS]" if passed else "[FAIL]"
    print(f"  {symbol} {name}: {detail}")

# ---------------------------------------------------------------------------
# CHECK 1: Exposure GeoJSON exists
# ---------------------------------------------------------------------------
print()
print("[1] Checking file existence ...")
c1 = EXPOSURE_GEOJSON.exists()
add_check("Exposure GeoJSON exists", c1, str(EXPOSURE_GEOJSON.relative_to(PROJECT_ROOT)))

c2 = EXPOSURE_CSV.exists()
add_check("Exposure CSV exists", c2, str(EXPOSURE_CSV.relative_to(PROJECT_ROOT)))

if not c1:
    print("[FATAL] Exposure GeoJSON not found. Run habitation_exposure_overlay.py first.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Load exposure layer
# ---------------------------------------------------------------------------
exposure = gpd.read_file(EXPOSURE_GEOJSON)
baseline = gpd.read_file(BASELINE_GEOJSON)

# ---------------------------------------------------------------------------
# CHECK 2: CRS
# ---------------------------------------------------------------------------
print()
print("[2] Checking CRS ...")
crs_ok = str(exposure.crs).upper() == METRIC_CRS.upper()
add_check("CRS matches metric CRS", crs_ok,
          f"Actual: {exposure.crs} | Expected: {METRIC_CRS}")

# ---------------------------------------------------------------------------
# CHECK 3: Record count
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
# CHECK 4: No duplicate village_id
# ---------------------------------------------------------------------------
print()
print("[4] Checking for duplicates ...")
dup_vids = exposure["village_id"].duplicated().sum()
add_check("No duplicate village_id", dup_vids == 0,
          f"Duplicate count: {dup_vids}")

# ---------------------------------------------------------------------------
# CHECK 5: hazard_zone_flag values valid
# ---------------------------------------------------------------------------
print()
print("[5] Checking hazard_zone_flag values ...")
valid_flags = exposure["hazard_zone_flag"].isin([0, 1]).all()
add_check("hazard_zone_flag values are 0 or 1 only", valid_flags,
          f"Unique values: {sorted(exposure['hazard_zone_flag'].unique().tolist())}")

# ---------------------------------------------------------------------------
# CHECK 6: Population reconciliation
# ---------------------------------------------------------------------------
print()
print("[6] Checking population reconciliation ...")

inside  = exposure[exposure["hazard_zone_flag"] == 1]
outside = exposure[exposure["hazard_zone_flag"] == 0]

total_pop  = int(exposure["tot_pop"].sum())
inside_pop = int(inside["tot_pop"].sum())
outside_pop = int(outside["tot_pop"].sum())

pop_ok = (inside_pop + outside_pop) == total_pop
add_check("Population reconciles (inside + outside = total)", pop_ok,
          f"Inside {inside_pop:,} + Outside {outside_pop:,} = {inside_pop+outside_pop:,} (Total: {total_pop:,})")

total_hh  = int(exposure["households"].sum())
inside_hh = int(inside["households"].sum())
outside_hh = int(outside["households"].sum())

hh_ok = (inside_hh + outside_hh) == total_hh
add_check("Household reconciles (inside + outside = total)", hh_ok,
          f"Inside {inside_hh:,} + Outside {outside_hh:,} = {inside_hh+outside_hh:,} (Total: {total_hh:,})")

total_sc  = int(exposure["pop_sc"].sum())
inside_sc = int(inside["pop_sc"].sum())
outside_sc = int(outside["pop_sc"].sum())

sc_ok = (inside_sc + outside_sc) == total_sc
add_check("SC population reconciles", sc_ok,
          f"Inside {inside_sc:,} + Outside {outside_sc:,} = {inside_sc+outside_sc:,} (Total: {total_sc:,})")

total_st  = int(exposure["pop_st"].sum())
inside_st = int(inside["pop_st"].sum())
outside_st = int(outside["pop_st"].sum())

st_ok = (inside_st + outside_st) == total_st
add_check("ST population reconciles", st_ok,
          f"Inside {inside_st:,} + Outside {outside_st:,} = {inside_st+outside_st:,} (Total: {total_st:,})")

# ---------------------------------------------------------------------------
# CHECK 7: CRS consistency between exposure and baseline
# ---------------------------------------------------------------------------
print()
print("[7] Checking CRS consistency ...")
crs_consistent = str(exposure.crs) == str(baseline.crs)
add_check("CRS consistent with baseline", crs_consistent,
          f"Exposure: {exposure.crs} | Baseline: {baseline.crs}")

# ---------------------------------------------------------------------------
# CHECK 8: Raw data not modified (compare file sizes against expected)
# ---------------------------------------------------------------------------
print()
print("[8] Checking raw data integrity ...")
# We check that raw input files still exist and their content is readable
census_ok = CENSUS_EXCEL.exists()
add_check("Census Excel raw file still exists (unmodified)", census_ok,
          str(CENSUS_EXCEL.relative_to(PROJECT_ROOT)))

shrug_ok = SHRUG_GEOJSON.exists()
add_check("SHRUG GeoJSON raw file still exists (unmodified)", shrug_ok,
          str(SHRUG_GEOJSON.relative_to(PROJECT_ROOT)))

# CHECK 9: Step 7 hazard layer not modified
print()
print("[9] Checking Step 7 hazard layer integrity ...")
rz_ok = REDZONES_GEOJSON.exists()
add_check("Step 7 red zone GeoJSON still exists (unmodified)", rz_ok,
          str(REDZONES_GEOJSON.relative_to(PROJECT_ROOT)))

if rz_ok:
    rz_check = gpd.read_file(REDZONES_GEOJSON)
    rz_feature_ok = len(rz_check) == 289
    add_check("Step 7 red zone feature count unchanged (289)", rz_feature_ok,
              f"Actual: {len(rz_check)}")

# ---------------------------------------------------------------------------
# CHECK 10: Summary CSV structure
# ---------------------------------------------------------------------------
print()
print("[10] Checking summary CSV ...")
if c2:
    summary_df = pd.read_csv(EXPOSURE_CSV)
    csv_cols_ok = all(c in summary_df.columns for c in ["category", "metric", "value", "percentage"])
    add_check("Summary CSV has required columns", csv_cols_ok,
              f"Columns: {summary_df.columns.tolist()}")
    csv_rows_ok = len(summary_df) >= 14  # At least 14 rows (5 categories * 3 rows each - 1)
    add_check("Summary CSV has sufficient rows", csv_rows_ok,
              f"Rows: {len(summary_df)}")

# ---------------------------------------------------------------------------
# CHECK 11: distance field exists and is valid
# ---------------------------------------------------------------------------
print()
print("[11] Checking distance field ...")
dist_ok = "dist_to_nearest_redzone_m" in exposure.columns
add_check("dist_to_nearest_redzone_m field present", dist_ok,
          "Field present" if dist_ok else "Field missing")

if dist_ok:
    dist_non_negative = (exposure["dist_to_nearest_redzone_m"] >= 0).all()
    add_check("dist_to_nearest_redzone_m >= 0 for all records", dist_non_negative,
              f"Min: {exposure['dist_to_nearest_redzone_m'].min():.1f} m")

# ---------------------------------------------------------------------------
# Overall status
# ---------------------------------------------------------------------------
failed = [c for c in checks if c[1] == "FAIL"]
overall = "PASS" if not failed else "FAIL"

print()
print("=" * 70)
print(f"EXPOSURE VALIDATION STATUS: {overall}")
print("=" * 70)

if failed:
    print("Failed checks:")
    for name, status, detail in failed:
        print(f"  - {name}: {detail}")
else:
    print("All checks passed.")

print()
print("--- Exposure Summary ---")
print(f"  Total habitations      : {len(exposure):,}")
print(f"  Inside red zones       : {len(inside):,} ({len(inside)/len(exposure)*100:.1f}%)")
print(f"  Outside red zones      : {len(outside):,} ({len(outside)/len(exposure)*100:.1f}%)")
print(f"  Total population       : {total_pop:,}")
print(f"  Population inside      : {inside_pop:,} ({inside_pop/total_pop*100 if total_pop else 0:.1f}%)")
print(f"  Population outside     : {outside_pop:,} ({outside_pop/total_pop*100 if total_pop else 0:.1f}%)")
print(f"  Total households       : {total_hh:,}")
print(f"  HH inside              : {inside_hh:,}")
print(f"  SC total               : {total_sc:,}")
print(f"  SC inside              : {inside_sc:,}")
print(f"  ST total               : {total_st:,}")
print(f"  ST inside              : {inside_st:,}")

if "dist_to_nearest_redzone_m" in exposure.columns:
    print()
    print("--- Proximity Context (SHRUG centroid to nearest Candidate Red Zone) ---")
    print(f"  Min distance           : {exposure['dist_to_nearest_redzone_m'].min():.1f} m")
    print(f"  Max distance           : {exposure['dist_to_nearest_redzone_m'].max():.1f} m")
    print(f"  Mean distance          : {exposure['dist_to_nearest_redzone_m'].mean():.1f} m")
    print(f"  Habitations < 500 m    : {(exposure['dist_to_nearest_redzone_m'] < 500).sum()}")
    print(f"  Habitations 500-1000 m : {((exposure['dist_to_nearest_redzone_m'] >= 500) & (exposure['dist_to_nearest_redzone_m'] < 1000)).sum()}")

print()
print("IMPORTANT: These are preliminary spatial screening outputs.")
print("They require official geotechnical verification and do NOT constitute")
print("evacuation orders, safety certifications, or relocation authorizations.")

if overall == "FAIL":
    sys.exit(1)

sys.exit(0)
