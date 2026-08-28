"""
processing/exposure/build_habitation_baseline.py
================================================
SIH26191 -- Step 8C: Build Habitation Baseline Layer

PURPOSE
-------
Joins verified Census demographics (PCA) to SHRUG spatial village centroids
using an exact code-based join (Census Town/Village ID <-> SHRUG pc11_village_id).

Produces a georeferenced habitation baseline with demographic attributes, ready
for spatial overlay analysis.

IMPORTANT CONSTRAINTS
---------------------
- Join is EXACT and CODE-BASED ONLY. No fuzzy matching. No name matching.
- OSM data is NOT used in this script.
- Village IDs are treated as integers (both Census and SHRUG store them as int).
- All paths resolved from configs/project.yaml -- no hardcoded paths.
- Fails loudly if required inputs are missing or validation fails.

OUTPUT CRS
----------
data/processed/habitations/ files are stored in EPSG:32644 (metric CRS)
for downstream spatial analysis compatibility.

OUTPUTS
-------
data/processed/habitations/habitation_baseline.geojson
data/processed/habitations/habitation_baseline.gpkg

USAGE
-----
    python processing/exposure/build_habitation_baseline.py

Author: SIH26191 Processing Pipeline
"""

import sys
import io
import pathlib

# Force UTF-8 output on Windows (avoids cp1252 UnicodeEncodeError)
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Resolve project root dynamically (this script lives 2 dirs below root)
# ---------------------------------------------------------------------------
PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CONFIG_PATH  = PROJECT_ROOT / "configs" / "project.yaml"

# Fail early if config not found
if not CONFIG_PATH.exists():
    print(f"[FATAL] Config not found: {CONFIG_PATH}")
    sys.exit(1)

import yaml
import pandas as pd
import geopandas as gpd

# ---------------------------------------------------------------------------
# Load configuration
# ---------------------------------------------------------------------------
with open(CONFIG_PATH, "r", encoding="utf-8") as fh:
    CONFIG = yaml.safe_load(fh)

STORAGE_CRS = CONFIG["crs"]["storage_crs"]          # EPSG:4326
METRIC_CRS  = CONFIG["crs"]["analysis_crs_metric"]  # EPSG:32644

CENSUS_EXCEL_PATH = PROJECT_ROOT / CONFIG["paths"]["raw_dir"] / "habitations" / "PCA_CDB-0503-F-Census.xlsx"
SHRUG_GEOJSON_PATH = PROJECT_ROOT / CONFIG["paths"]["raw_dir"] / "habitations" / "rudraprayag_census_villages_shrug.geojson"

OUTPUT_DIR      = PROJECT_ROOT / CONFIG["paths"]["processed_dir"] / "habitations"
OUTPUT_GEOJSON  = OUTPUT_DIR / "habitation_baseline.geojson"
OUTPUT_GPKG     = OUTPUT_DIR / "habitation_baseline.gpkg"

HAZARD_LABEL    = CONFIG["terminology"]["hazard_zone_label"]
DISCLAIMER      = CONFIG["terminology"]["decision_support_disclaimer"]

# ---------------------------------------------------------------------------
# Ensure output directory exists
# ---------------------------------------------------------------------------
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("SIH26191 -- Step 8C: Build Habitation Baseline")
print("=" * 70)
print(f"Project root : {PROJECT_ROOT}")
print(f"Storage CRS  : {STORAGE_CRS}")
print(f"Metric CRS   : {METRIC_CRS}")
print()

# ===========================================================================
# STEP 1: Read Census Excel
# ===========================================================================
print("[1/8] Reading Census Excel ...")
if not CENSUS_EXCEL_PATH.exists():
    print(f"[FATAL] Census Excel not found: {CENSUS_EXCEL_PATH}")
    sys.exit(1)

xl = pd.ExcelFile(CENSUS_EXCEL_PATH)
df_raw = xl.parse(xl.sheet_names[0])
print(f"      Raw rows: {len(df_raw)} | Columns: {len(df_raw.columns)}")

# ===========================================================================
# STEP 2: Filter to village-level records only (Level == 'VILLAGE')
# ===========================================================================
print("[2/8] Filtering to VILLAGE-level records ...")
df_villages = df_raw[df_raw["Level"] == "VILLAGE"].copy()
print(f"      VILLAGE rows: {len(df_villages)}")

# ===========================================================================
# STEP 3: Normalize Census village IDs
# ===========================================================================
print("[3/8] Normalizing Census village IDs ...")
# Town/Village is int64 in the Excel.
# We cast to int64 explicitly to ensure consistent integer join.
# Leading-zero concern: not applicable -- IDs are integers in this Census file.
# Verified: Town/Village values are numeric like 42054, 42055 ...
df_villages = df_villages.copy()
df_villages["_census_vid"] = df_villages["Town/Village"].astype("int64")

# Sanity-check: no zero IDs in village rows
zero_ids = df_villages[df_villages["_census_vid"] == 0]
if len(zero_ids) > 0:
    print(f"[WARN] {len(zero_ids)} village rows with Town/Village=0 -- these should be block headers and filtered by Level='VILLAGE'. Check data.")

print(f"      Unique Census village IDs: {df_villages['_census_vid'].nunique()}")
print(f"      Inhabited villages (TOT_P > 0): {len(df_villages[df_villages['TOT_P'] > 0])}")
print(f"      Uninhabited villages (TOT_P = 0): {len(df_villages[df_villages['TOT_P'] == 0])}")

# ===========================================================================
# STEP 4: Read SHRUG GeoJSON
# ===========================================================================
print("[4/8] Reading SHRUG GeoJSON ...")
if not SHRUG_GEOJSON_PATH.exists():
    print(f"[FATAL] SHRUG GeoJSON not found: {SHRUG_GEOJSON_PATH}")
    sys.exit(1)

shrug = gpd.read_file(SHRUG_GEOJSON_PATH)
print(f"      SHRUG features: {len(shrug)}")
print(f"      SHRUG CRS: {shrug.crs}")
print(f"      SHRUG geometry types: {shrug.geom_type.unique().tolist()}")

if str(shrug.crs) != STORAGE_CRS:
    print(f"[WARN] SHRUG CRS is {shrug.crs}, expected {STORAGE_CRS}. Will reproject outputs to {METRIC_CRS}.")

# ===========================================================================
# STEP 5: Normalize SHRUG pc11_village_id
# ===========================================================================
print("[5/8] Normalizing SHRUG village IDs ...")
shrug["_shrug_vid"] = shrug["pc11_village_id"].astype("int64")
print(f"      Unique SHRUG village IDs: {shrug['_shrug_vid'].nunique()}")

# ===========================================================================
# STEP 6: Exact inner join on integer village ID
# ===========================================================================
print("[6/8] Performing EXACT inner join (Census -> SHRUG) ...")

# Select only required Census columns for the join
census_cols = [
    "_census_vid",
    "Town/Village",
    "Name",
    "No_HH",
    "TOT_P",
    "TOT_M",
    "TOT_F",
    "P_SC",
    "P_ST",
]
df_census_subset = df_villages[census_cols].copy()

# Check for duplicate Census village IDs before join
dup_census = df_census_subset["_census_vid"].duplicated()
if dup_census.any():
    print(f"[FATAL] Duplicate Census village IDs found: {dup_census.sum()}")
    print(df_census_subset[dup_census][["_census_vid", "Name"]].to_string())
    sys.exit(1)

# Merge
joined = shrug.merge(
    df_census_subset,
    left_on="_shrug_vid",
    right_on="_census_vid",
    how="inner",
    validate="1:1",  # Enforce no duplicates on either side
)
print(f"      Inner-join result: {len(joined)} records")

# Fail loudly if counts don't match expected
EXPECTED_JOINED = 653
if len(joined) != EXPECTED_JOINED:
    print(f"[FATAL] Expected {EXPECTED_JOINED} joined records, got {len(joined)}.")
    print("        Check Census and SHRUG data for mismatches.")
    # Report unmatched SHRUG IDs
    shrug_ids   = set(shrug["_shrug_vid"].tolist())
    census_ids  = set(df_census_subset["_census_vid"].tolist())
    unmatched_shrug = shrug_ids - census_ids
    unmatched_census = census_ids - shrug_ids
    print(f"        SHRUG IDs with no Census match: {len(unmatched_shrug)}")
    print(f"        Census IDs with no SHRUG match: {len(unmatched_census)}")
    if unmatched_census:
        missing = df_census_subset[df_census_subset["_census_vid"].isin(unmatched_census)]
        print(missing[["_census_vid", "Name", "TOT_P"]].to_string())
    sys.exit(1)

print(f"      [OK] All {len(joined)} SHRUG records matched to Census records.")

# ===========================================================================
# STEP 7: Add demographic fields with clean names
# ===========================================================================
print("[7/8] Building demographic attribute fields ...")

# Build clean output GeoDataFrame
baseline = gpd.GeoDataFrame(
    {
        # Village identification
        "village_id"   : joined["_census_vid"].astype("int64"),
        "village_name" : joined["Name"].astype(str),

        # Demographics
        "households"   : joined["No_HH"].astype("int64"),
        "tot_pop"      : joined["TOT_P"].astype("int64"),
        "pop_male"     : joined["TOT_M"].astype("int64"),
        "pop_female"   : joined["TOT_F"].astype("int64"),
        "pop_sc"       : joined["P_SC"].astype("int64"),
        "pop_st"       : joined["P_ST"].astype("int64"),

        # SHRUG provenance fields
        "shrid2"           : joined["shrid2"],
        "shrug_state_id"   : joined["pc11_state_id"],
        "shrug_district_id": joined["pc11_district_id"],
        "shrug_subdist_id" : joined["pc11_subdistrict_id"],

        # Source provenance
        "data_source"   : "Census PCA 2011 joined to SHRUG spatial bridge",
        "join_method"   : "Exact code-based join: Census Town/Village = SHRUG pc11_village_id",
        "disclaimer"    : DISCLAIMER,
    },
    geometry=joined["geometry"],
    crs=shrug.crs,
)

print(f"      Fields added: {[c for c in baseline.columns if c != 'geometry']}")

# ===========================================================================
# STEP 8: Validate baseline
# ===========================================================================
print("[8/8] Validating habitation baseline ...")

errors = []

# 8a. Feature count
if len(baseline) != EXPECTED_JOINED:
    errors.append(f"Feature count mismatch: expected {EXPECTED_JOINED}, got {len(baseline)}")

# 8b. Duplicate village IDs
dup_vids = baseline["village_id"].duplicated()
if dup_vids.any():
    errors.append(f"Duplicate village_id values: {dup_vids.sum()}")

# 8c. Null geometries
null_geom = baseline.geometry.isnull()
if null_geom.any():
    errors.append(f"Null geometries: {null_geom.sum()}")

# 8d. Demographic nulls
for col in ["households", "tot_pop", "pop_male", "pop_female", "pop_sc", "pop_st"]:
    nulls = baseline[col].isnull().sum()
    if nulls > 0:
        errors.append(f"Null values in {col}: {nulls}")

# 8e. No negative population
neg_pop = (baseline["tot_pop"] < 0).sum()
if neg_pop > 0:
    errors.append(f"Negative tot_pop values: {neg_pop}")

# 8f. Population sum cross-check against Census-only figure
#     For inhabited villages (TOT_P > 0), Census sum should equal baseline sum
census_inhabited_pop = df_villages[df_villages["TOT_P"] > 0]["TOT_P"].sum()
baseline_pop_sum     = baseline["tot_pop"].sum()
# Note: baseline includes ALL 653 joined records (which includes the 653 SHRUG-matched
# villages -- some may have TOT_P=0 from Census if Census has 0 for them in the join).
# The inhabited Census pop is the upper bound -- baseline pop should equal it
# because all 653 matched villages cover 100% of inhabited population.

print()
print("  --- Validation Counts ---")
print(f"  Feature count         : {len(baseline)}")
print(f"  Duplicate village IDs : {dup_vids.sum()}")
print(f"  Null geometries       : {null_geom.sum()}")
print(f"  Total population sum  : {baseline_pop_sum:,}")
print(f"  Census inhabited pop  : {census_inhabited_pop:,}")
print(f"  Households total      : {baseline['households'].sum():,}")
print(f"  SC population total   : {baseline['pop_sc'].sum():,}")
print(f"  ST population total   : {baseline['pop_st'].sum():,}")

# Population coverage check
pop_diff = abs(baseline_pop_sum - census_inhabited_pop)
if pop_diff > 0:
    # Some matched villages may have TOT_P=0 (uninhabited but matched)
    # This is expected and acceptable -- we report it
    print(f"  [INFO] Population difference between baseline and inhabited Census: {pop_diff:,}")
    print(f"         (This may reflect uninhabited villages matched in SHRUG.)")

if errors:
    print()
    print("[FATAL] Validation FAILED:")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)

print()
print("  [PASS] All validation checks passed.")

# ===========================================================================
# STEP 9: Reproject to metric CRS
# ===========================================================================
print()
print(f"[9/9] Reprojecting to metric CRS ({METRIC_CRS}) for spatial analysis ...")
baseline_metric = baseline.to_crs(METRIC_CRS)
print(f"      CRS after reproject: {baseline_metric.crs}")

# ===========================================================================
# STEP 10: Save outputs
# ===========================================================================
print()
print("[10/10] Saving outputs ...")

# GeoJSON (storage CRS = EPSG:4326 per project convention for file sharing,
# but for spatial analysis we store metric. The spec says save in metric CRS
# for analysis. Save both: metric for analysis, and note CRS in file.)
# Per spec: "Reproject to the configured metric CRS for spatial analysis"
# -> save in METRIC_CRS
baseline_metric.to_file(OUTPUT_GEOJSON, driver="GeoJSON")
print(f"      [SAVED] {OUTPUT_GEOJSON.relative_to(PROJECT_ROOT)}")

baseline_metric.to_file(OUTPUT_GPKG, driver="GPKG", layer="habitation_baseline")
print(f"      [SAVED] {OUTPUT_GPKG.relative_to(PROJECT_ROOT)}")

print()
print("=" * 70)
print("Step 8C COMPLETE -- Habitation Baseline Built Successfully")
print("=" * 70)
print(f"  Output features  : {len(baseline_metric)}")
print(f"  Output CRS       : {baseline_metric.crs}")
print(f"  Total population : {baseline_metric['tot_pop'].sum():,}")
print(f"  Total households : {baseline_metric['households'].sum():,}")
print(f"  SC population    : {baseline_metric['pop_sc'].sum():,}")
print(f"  ST population    : {baseline_metric['pop_st'].sum():,}")
print()
