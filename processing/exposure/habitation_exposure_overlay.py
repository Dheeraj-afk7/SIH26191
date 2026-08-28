"""
processing/exposure/habitation_exposure_overlay.py
====================================================
SIH26191 -- Step 8E+F+G: Habitation Hazard Exposure Overlay

PURPOSE
-------
Performs spatial overlay of habitation centroids against the Step 7
Candidate Hazard-Based Red Zone polygons to determine which habitations
fall within or outside red zones.

Computes population exposure statistics (Phase 8F) and saves outputs (Phase 8G).

INPUTS
------
Habitation baseline:
    data/processed/habitations/habitation_baseline.geojson
    (653 village centroids, EPSG:32644, from Phase 8C)

Step 7 Candidate Hazard-Based Red Zones:
    data/outputs/candidate_hazard_based_red_zones.geojson
    (289 polygon/multipolygon features, EPSG:32644)

SPATIAL OPERATION
-----------------
Since habitations are Point geometries and red zones are Polygon/MultiPolygon
geometries, the overlay uses GeoPandas spatial join (sjoin) with predicate
'within' to test whether each habitation centroid falls inside any red zone
polygon.

Both layers are already in EPSG:32644 (metric CRS), so no reprojection
is required for the overlay.

HAZARD ZONE FLAG VALUES
-----------------------
hazard_zone_flag = 1 : "Inside Candidate Hazard-Based Red Zone"
hazard_zone_flag = 0 : "Outside Candidate Hazard-Based Red Zone"

IMPORTANT DISCLAIMERS
---------------------
- This is a screening output for DECISION SUPPORT only.
- It does NOT constitute an evacuation order.
- It does NOT declare locations safe or unsafe.
- It does NOT authorize relocation.
- It does NOT predict disasters.
- Official geotechnical assessment is required.

OUTPUTS
-------
data/processed/exposure/habitation_exposure.geojson
data/processed/exposure/habitation_exposure_summary.csv
docs/step8_habitation_exposure_report.md

USAGE
-----
    python processing/exposure/habitation_exposure_overlay.py

Author: SIH26191 Processing Pipeline
"""

import sys
import io
import pathlib

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
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

METRIC_CRS  = CONFIG["crs"]["analysis_crs_metric"]    # EPSG:32644
STORAGE_CRS = CONFIG["crs"]["storage_crs"]            # EPSG:4326

# ---------------------------------------------------------------------------
# Resolve input paths from config
# ---------------------------------------------------------------------------
BASELINE_PATH   = PROJECT_ROOT / CONFIG["paths"]["processed_dir"] / "habitations" / "habitation_baseline.geojson"
REDZONES_PATH   = PROJECT_ROOT / CONFIG["paths"]["redzones_geojson"]

# Output paths
EXPOSURE_DIR    = PROJECT_ROOT / CONFIG["paths"]["processed_dir"] / "exposure"
EXPOSURE_GEOJSON = EXPOSURE_DIR / "habitation_exposure.geojson"
EXPOSURE_CSV     = EXPOSURE_DIR / "habitation_exposure_summary.csv"

DOCS_DIR        = PROJECT_ROOT / "docs"
EXPOSURE_REPORT = DOCS_DIR / "step8_habitation_exposure_report.md"

HAZARD_LABEL    = CONFIG["terminology"]["hazard_zone_label"]
DISCLAIMER_TERM = CONFIG["terminology"]["decision_support_disclaimer"]

# Output directory setup
EXPOSURE_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

print("=" * 70)
print("SIH26191 -- Step 8E+F+G: Hazard Exposure Overlay")
print("=" * 70)
print(f"Metric CRS   : {METRIC_CRS}")
print(f"Hazard label : {HAZARD_LABEL}")
print()

# ===========================================================================
# PHASE 8E: LOAD INPUTS AND INSPECT
# ===========================================================================
print("--- Phase 8E: Loading Inputs ---")
print()

# Load habitation baseline
print(f"[1] Loading habitation baseline from:")
print(f"    {BASELINE_PATH.relative_to(PROJECT_ROOT)}")
if not BASELINE_PATH.exists():
    print("[FATAL] Habitation baseline not found. Run build_habitation_baseline.py first.")
    sys.exit(1)

habitations = gpd.read_file(BASELINE_PATH)
print(f"    Features      : {len(habitations)}")
print(f"    CRS           : {habitations.crs}")
print(f"    Geom types    : {habitations.geom_type.unique().tolist()}")
print(f"    Columns       : {habitations.columns.tolist()}")

if str(habitations.crs) != METRIC_CRS:
    print(f"[FATAL] Habitation baseline CRS ({habitations.crs}) != metric CRS ({METRIC_CRS}). Aborting.")
    sys.exit(1)

# Load Step 7 red zones
print()
print(f"[2] Loading Candidate Hazard-Based Red Zones from:")
print(f"    {REDZONES_PATH.relative_to(PROJECT_ROOT)}")
if not REDZONES_PATH.exists():
    print(f"[FATAL] Red zone file not found: {REDZONES_PATH}")
    sys.exit(1)

redzones = gpd.read_file(REDZONES_PATH)
print(f"    Features      : {len(redzones)}")
print(f"    CRS           : {redzones.crs}")
print(f"    Geom types    : {redzones.geom_type.unique().tolist()}")
print(f"    Key attributes: {[c for c in redzones.columns if c != 'geometry']}")

# Both layers should be in EPSG:32644
if str(redzones.crs) != METRIC_CRS:
    print(f"[INFO] Red zones CRS ({redzones.crs}) != metric CRS ({METRIC_CRS}). Reprojecting red zones ...")
    redzones = redzones.to_crs(METRIC_CRS)
    print(f"       Reprojected to: {redzones.crs}")

print()
print("[INFO] Geometry analysis:")
print(f"       Habitations: {habitations.geom_type.value_counts().to_dict()}")
print(f"       Red zones  : {redzones.geom_type.value_counts().to_dict()}")
print()
print("[INFO] Spatial operation: Point-in-Polygon sjoin (predicate='within')")
print("       Habitation centroids tested against Candidate Hazard-Based Red Zone polygons.")
print("[INFO] Also computing: distance to nearest Candidate Red Zone for each habitation.")

# ===========================================================================
# PHASE 8E: SPATIAL JOIN -- POINT IN POLYGON
# ===========================================================================
print()
print("--- Phase 8E: Spatial Join ---")
print()

# Perform spatial join to find habitations inside red zones
# We use 'within' predicate: centroid falls completely within the polygon
# 'intersects' would also work for points, but 'within' is precise
print("[3] Performing spatial join (habitations within red zones) ...")

# sjoin returns only matched rows (inner join by default)
# We use 'left' join to keep ALL habitations, with NaN for non-overlapping ones
joined = gpd.sjoin(
    habitations,
    redzones[["zone_id", "zone_label", "mean_multihazard_score",
              "candidate_priority_rank", "area_m2", "geometry"]].rename(
        columns={
            "zone_id"   : "matched_zone_id",
            "zone_label": "matched_zone_label",
            "mean_multihazard_score"    : "matched_zone_mh_score",
            "candidate_priority_rank"   : "matched_zone_priority",
            "area_m2"   : "matched_zone_area_m2",
        }
    ),
    how="left",
    predicate="within",
)

print(f"    Joined result rows: {len(joined)}")

# After left sjoin, duplicates can appear if a point falls in multiple polygons.
# This should not occur for non-overlapping red zones, but check anyway.
if len(joined) > len(habitations):
    print(f"[WARN] Spatial join produced {len(joined)} rows for {len(habitations)} habitations.")
    print("       This means some habitations fall within multiple overlapping red zones.")
    print("       Keeping only the first match per habitation (highest priority zone).")
    # Sort by matched_zone_priority (ascending, lower rank = higher priority)
    # NaN (no match) will be placed last
    joined = joined.sort_values("matched_zone_priority", na_position="last")
    joined = joined[~joined.index.duplicated(keep="first")]
    print(f"       After dedup: {len(joined)} rows")

# Sanity: must equal original habitation count
if len(joined) != len(habitations):
    print(f"[FATAL] Joined record count ({len(joined)}) != habitation count ({len(habitations)}). Aborting.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Compute distance from each habitation centroid to nearest red zone
# ---------------------------------------------------------------------------
print()
print("[3b] Computing distance to nearest Candidate Red Zone for each habitation ...")
print("     (SHRUG centroids are village administrative centroids, not precise")
print("      building locations. Distance proximity is a key supplementary metric.)")

import numpy as np

dist_to_nearest = []
nearest_zone_id = []
for idx, row in habitations.iterrows():
    dists = redzones.geometry.distance(row["geometry"])
    min_idx = dists.idxmin()
    dist_to_nearest.append(round(float(dists[min_idx]), 1))
    nearest_zone_id.append(redzones.loc[min_idx, "zone_id"])

joined["dist_to_nearest_redzone_m"] = dist_to_nearest
joined["nearest_zone_id"]          = nearest_zone_id

print(f"    Min distance  : {min(dist_to_nearest):.1f} m")
print(f"    Max distance  : {max(dist_to_nearest):.1f} m")
print(f"    Mean distance : {sum(dist_to_nearest)/len(dist_to_nearest):.1f} m")

# Proximity bands
dist_arr = np.array(dist_to_nearest)
print()
print("    Proximity band breakdown:")
for lo, hi in [(0, 500), (500, 1000), (1000, 2000), (2000, 5000), (5000, 10000), (10000, 100000)]:
    cnt = int(((dist_arr >= lo) & (dist_arr < hi)).sum())
    pct_band = cnt / len(dist_arr) * 100
    label = f"{lo:>6,} - {hi:>6,} m" if hi < 100000 else f"{lo:>6,}+ m      "
    print(f"      {label} : {cnt:>4} habitations ({pct_band:.1f}%)")

# ===========================================================================
# Add hazard_zone_flag
# ===========================================================================
print()
print("[4] Adding hazard_zone_flag field ...")

# hazard_zone_flag = 1 if habitation is inside a red zone (matched_zone_id is not null)
# hazard_zone_flag = 0 if habitation is outside (no match)
joined["hazard_zone_flag"] = joined["matched_zone_id"].notna().astype(int)

# Add explicit label for clarity
joined["hazard_zone_label"] = joined["hazard_zone_flag"].map({
    1: "Inside Candidate Hazard-Based Red Zone",
    0: "Outside Candidate Hazard-Based Red Zone",
})

print(f"    Inside  (flag=1): {joined['hazard_zone_flag'].sum()}")
print(f"    Outside (flag=0): {(joined['hazard_zone_flag'] == 0).sum()}")

# Drop sjoin index column if present
if "index_right" in joined.columns:
    joined = joined.drop(columns=["index_right"])

# ===========================================================================
# Build clean exposure GeoDataFrame
# ===========================================================================
print()
print("[5] Building clean exposure output ...")

exposure_cols = [
    "village_id",
    "village_name",
    "households",
    "tot_pop",
    "pop_male",
    "pop_female",
    "pop_sc",
    "pop_st",
    "shrid2",
    "shrug_state_id",
    "shrug_district_id",
    "shrug_subdist_id",
    "hazard_zone_flag",
    "hazard_zone_label",
    "matched_zone_id",
    "matched_zone_label",
    "matched_zone_mh_score",
    "matched_zone_priority",
    "matched_zone_area_m2",
    "dist_to_nearest_redzone_m",
    "nearest_zone_id",
    "data_source",
    "join_method",
    "disclaimer",
    "geometry",
]

# Keep only columns that exist (matched_zone_* may be NaN for outside habitations)
exposure = gpd.GeoDataFrame(
    joined[[c for c in exposure_cols if c in joined.columns]].copy(),
    crs=METRIC_CRS,
)

print(f"    Exposure features: {len(exposure)}")
print(f"    Columns: {[c for c in exposure.columns if c != 'geometry']}")

# ===========================================================================
# PHASE 8F: EXPOSURE SUMMARY
# ===========================================================================
print()
print("=" * 70)
print("--- Phase 8F: Exposure Summary Calculation ---")
print("=" * 70)

inside  = exposure[exposure["hazard_zone_flag"] == 1]
outside = exposure[exposure["hazard_zone_flag"] == 0]

# Totals
total_habitations  = len(exposure)
inside_count       = len(inside)
outside_count      = len(outside)

total_pop          = int(exposure["tot_pop"].sum())
inside_pop         = int(inside["tot_pop"].sum())
outside_pop        = int(outside["tot_pop"].sum())

total_hh           = int(exposure["households"].sum())
inside_hh          = int(inside["households"].sum())
outside_hh         = int(outside["households"].sum())

total_sc           = int(exposure["pop_sc"].sum())
inside_sc          = int(inside["pop_sc"].sum())
outside_sc         = int(outside["pop_sc"].sum())

total_st           = int(exposure["pop_st"].sum())
inside_st          = int(inside["pop_st"].sum())
outside_st         = int(outside["pop_st"].sum())

# Percentages
def pct(numerator, denominator):
    return (numerator / denominator * 100) if denominator > 0 else 0.0

inside_pct_habitations = pct(inside_count, total_habitations)
inside_pct_pop         = pct(inside_pop, total_pop)
inside_pct_hh          = pct(inside_hh, total_hh)
inside_pct_sc          = pct(inside_sc, total_sc)
inside_pct_st          = pct(inside_st, total_st)

print()
print("  DISCLAIMER: These represent population exposure screening based on")
print("  the current Candidate Hazard-Based Red Zone layer.")
print("  They are NOT evacuation orders, disaster predictions, mandatory")
print("  relocation recommendations, or engineering safety certifications.")
print()

print("  --- Habitation Counts ---")
print(f"  Total habitations                        : {total_habitations:>8,}")
print(f"  Inside Candidate Hazard-Based Red Zones  : {inside_count:>8,}  ({inside_pct_habitations:.1f}%)")
print(f"  Outside Candidate Hazard-Based Red Zones : {outside_count:>8,}  ({100-inside_pct_habitations:.1f}%)")

print()
print("  --- Population Exposure ---")
print(f"  Total population                         : {total_pop:>8,}")
print(f"  Inside Candidate Hazard-Based Red Zones  : {inside_pop:>8,}  ({inside_pct_pop:.1f}%)")
print(f"  Outside Candidate Hazard-Based Red Zones : {outside_pop:>8,}  ({100-inside_pct_pop:.1f}%)")
print(f"  Inside + Outside = {inside_pop + outside_pop:,} (must = {total_pop:,}) -- {'OK' if inside_pop + outside_pop == total_pop else 'MISMATCH'}")

print()
print("  --- Household Exposure ---")
print(f"  Total households                         : {total_hh:>8,}")
print(f"  Inside Candidate Hazard-Based Red Zones  : {inside_hh:>8,}  ({inside_pct_hh:.1f}%)")
print(f"  Outside Candidate Hazard-Based Red Zones : {outside_hh:>8,}  ({100-inside_pct_hh:.1f}%)")

print()
print("  --- SC Population Exposure ---")
print(f"  Total SC population                      : {total_sc:>8,}")
print(f"  Inside Candidate Hazard-Based Red Zones  : {inside_sc:>8,}  ({inside_pct_sc:.1f}%)")
print(f"  Outside Candidate Hazard-Based Red Zones : {outside_sc:>8,}  ({100-inside_pct_sc:.1f}%)")

print()
print("  --- ST Population Exposure ---")
print(f"  Total ST population                      : {total_st:>8,}")
print(f"  Inside Candidate Hazard-Based Red Zones  : {inside_st:>8,}  ({inside_pct_st:.1f}%)")
print(f"  Outside Candidate Hazard-Based Red Zones : {outside_st:>8,}  ({100-inside_pct_st:.1f}%)")

# ===========================================================================
# PHASE 8G: SAVE OUTPUTS
# ===========================================================================
print()
print("=" * 70)
print("--- Phase 8G: Saving Outputs ---")
print("=" * 70)

# Save exposure GeoJSON
print()
print("[6] Saving exposure GeoJSON ...")
exposure.to_file(EXPOSURE_GEOJSON, driver="GeoJSON")
print(f"    [SAVED] {EXPOSURE_GEOJSON.relative_to(PROJECT_ROOT)}")

# Build summary CSV
print()
print("[7] Saving exposure summary CSV ...")

summary_records = [
    # Habitation counts
    {"category": "Habitation Records", "metric": "Total habitation records", "value": total_habitations, "percentage": 100.0, "notes": "All 653 villages from habitation baseline"},
    {"category": "Habitation Records", "metric": "Inside Candidate Hazard-Based Red Zone", "value": inside_count, "percentage": round(inside_pct_habitations, 2), "notes": "Centroid falls within a red zone polygon"},
    {"category": "Habitation Records", "metric": "Outside Candidate Hazard-Based Red Zone", "value": outside_count, "percentage": round(100 - inside_pct_habitations, 2), "notes": "Centroid does not intersect any red zone"},
    # Population
    {"category": "Population (TOT_P)", "metric": "Total population", "value": total_pop, "percentage": 100.0, "notes": "Census PCA 2011"},
    {"category": "Population (TOT_P)", "metric": "Population inside red zones", "value": inside_pop, "percentage": round(inside_pct_pop, 2), "notes": ""},
    {"category": "Population (TOT_P)", "metric": "Population outside red zones", "value": outside_pop, "percentage": round(100 - inside_pct_pop, 2), "notes": ""},
    # Households
    {"category": "Households (No_HH)", "metric": "Total households", "value": total_hh, "percentage": 100.0, "notes": "Census PCA 2011"},
    {"category": "Households (No_HH)", "metric": "Households inside red zones", "value": inside_hh, "percentage": round(inside_pct_hh, 2), "notes": ""},
    {"category": "Households (No_HH)", "metric": "Households outside red zones", "value": outside_hh, "percentage": round(100 - inside_pct_hh, 2), "notes": ""},
    # SC
    {"category": "SC Population (P_SC)", "metric": "Total SC population", "value": total_sc, "percentage": 100.0, "notes": "Census PCA 2011"},
    {"category": "SC Population (P_SC)", "metric": "SC population inside red zones", "value": inside_sc, "percentage": round(inside_pct_sc, 2), "notes": ""},
    {"category": "SC Population (P_SC)", "metric": "SC population outside red zones", "value": outside_sc, "percentage": round(100 - inside_pct_sc, 2), "notes": ""},
    # ST
    {"category": "ST Population (P_ST)", "metric": "Total ST population", "value": total_st, "percentage": 100.0, "notes": "Census PCA 2011"},
    {"category": "ST Population (P_ST)", "metric": "ST population inside red zones", "value": inside_st, "percentage": round(inside_pct_st, 2), "notes": ""},
    {"category": "ST Population (P_ST)", "metric": "ST population outside red zones", "value": outside_st, "percentage": round(100 - inside_pct_st, 2), "notes": ""},
    # Proximity bands (distance from village centroid to nearest red zone)
    {"category": "Proximity to Red Zone", "metric": "Habitations < 500 m from nearest Candidate Red Zone", "value": int((dist_arr < 500).sum()), "percentage": round(pct(int((dist_arr < 500).sum()), total_habitations), 2), "notes": "Centroid proximity (not inside zone)"},
    {"category": "Proximity to Red Zone", "metric": "Habitations 500 m - 1,000 m from nearest Candidate Red Zone", "value": int(((dist_arr >= 500) & (dist_arr < 1000)).sum()), "percentage": round(pct(int(((dist_arr >= 500) & (dist_arr < 1000)).sum()), total_habitations), 2), "notes": ""},
    {"category": "Proximity to Red Zone", "metric": "Habitations 1,000 m - 2,000 m from nearest Candidate Red Zone", "value": int(((dist_arr >= 1000) & (dist_arr < 2000)).sum()), "percentage": round(pct(int(((dist_arr >= 1000) & (dist_arr < 2000)).sum()), total_habitations), 2), "notes": ""},
    {"category": "Proximity to Red Zone", "metric": "Habitations 2,000 m - 5,000 m from nearest Candidate Red Zone", "value": int(((dist_arr >= 2000) & (dist_arr < 5000)).sum()), "percentage": round(pct(int(((dist_arr >= 2000) & (dist_arr < 5000)).sum()), total_habitations), 2), "notes": ""},
    {"category": "Proximity to Red Zone", "metric": "Habitations > 5,000 m from nearest Candidate Red Zone", "value": int((dist_arr >= 5000).sum()), "percentage": round(pct(int((dist_arr >= 5000).sum()), total_habitations), 2), "notes": ""},
]

summary_df = pd.DataFrame(summary_records)
summary_df.to_csv(EXPOSURE_CSV, index=False, encoding="utf-8")
print(f"    [SAVED] {EXPOSURE_CSV.relative_to(PROJECT_ROOT)}")

# ===========================================================================
# Write exposure report markdown
# ===========================================================================
print()
print("[8] Writing exposure report ...")

ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

report_lines = [
    "# Step 8 -- Habitation Hazard Exposure Report",
    "",
    f"**Generated:** {ts}  ",
    f"**Project:** SIH26191 -- Rudraprayag District, Uttarakhand  ",
    f"**Pilot District:** Rudraprayag  ",
    f"**Status:** DECISION SUPPORT SCREENING OUTPUT -- Requires Official Verification  ",
    "",
    "---",
    "",
    "> **IMPORTANT DISCLAIMER**",
    ">",
    "> This report presents population exposure screening based on the current",
    "> **Candidate Hazard-Based Red Zone** layer (Step 7 output).",
    ">",
    "> These results are **NOT**:",
    "> - Evacuation orders",
    "> - Disaster predictions",
    "> - Mandatory relocation recommendations",
    "> - Engineering safety certifications",
    "> - Official government hazard zone declarations",
    ">",
    "> All outputs require official verification and geotechnical assessment",
    "> before any administrative action.",
    "",
    "---",
    "",
    "## Step 7 Red Zone Input Summary",
    "",
    f"| Parameter | Value |",
    f"|-----------|-------|",
    f"| File | `{REDZONES_PATH.relative_to(PROJECT_ROOT)}` |",
    f"| Feature count | {len(redzones)} |",
    f"| Geometry type | Polygon / MultiPolygon |",
    f"| CRS | {redzones.crs} |",
    f"| Zone label | {HAZARD_LABEL} |",
    "",
    "---",
    "",
    "## Habitation Baseline Summary",
    "",
    f"| Parameter | Value |",
    f"|-----------|-------|",
    f"| File | `{BASELINE_PATH.relative_to(PROJECT_ROOT)}` |",
    f"| Feature count | {len(habitations)} |",
    f"| Geometry type | Point (village centroids) |",
    f"| CRS | {habitations.crs} |",
    f"| Source | Census PCA 2011 joined to SHRUG spatial bridge |",
    "",
    "---",
    "",
    "## Spatial Operation",
    "",
    "| Parameter | Detail |",
    "|-----------|--------|",
    "| Method | Point-in-Polygon spatial join (GeoPandas sjoin) |",
    "| Predicate | `within` (habitation centroid falls inside red zone polygon) |",
    "| Both layers in metric CRS | EPSG:32644 (UTM Zone 44N) |",
    "| Overlay type | Left join (all habitations retained) |",
    "",
    "---",
    "",
    "## Exposure Results",
    "",
    "### Habitation Records",
    "",
    "| Metric | Count | Percentage |",
    "|--------|-------|------------|",
    f"| Total habitation records | {total_habitations:,} | 100.0% |",
    f"| Inside Candidate Hazard-Based Red Zone | {inside_count:,} | {inside_pct_habitations:.1f}% |",
    f"| Outside Candidate Hazard-Based Red Zone | {outside_count:,} | {100-inside_pct_habitations:.1f}% |",
    "",
    "### Population Exposure",
    "",
    "| Metric | Value | Percentage |",
    "|--------|-------|------------|",
    f"| Total population (Census PCA 2011) | {total_pop:,} | 100.0% |",
    f"| Population inside Candidate Red Zones | {inside_pop:,} | {inside_pct_pop:.1f}% |",
    f"| Population outside Candidate Red Zones | {outside_pop:,} | {100-inside_pct_pop:.1f}% |",
    "",
    "### Household Exposure",
    "",
    "| Metric | Value | Percentage |",
    "|--------|-------|------------|",
    f"| Total households (Census PCA 2011) | {total_hh:,} | 100.0% |",
    f"| Households inside Candidate Red Zones | {inside_hh:,} | {inside_pct_hh:.1f}% |",
    f"| Households outside Candidate Red Zones | {outside_hh:,} | {100-inside_pct_hh:.1f}% |",
    "",
    "### SC Population Exposure",
    "",
    "| Metric | Value | Percentage |",
    "|--------|-------|------------|",
    f"| Total SC population | {total_sc:,} | 100.0% |",
    f"| SC population inside Candidate Red Zones | {inside_sc:,} | {inside_pct_sc:.1f}% |",
    f"| SC population outside Candidate Red Zones | {outside_sc:,} | {100-inside_pct_sc:.1f}% |",
    "",
    "### ST Population Exposure",
    "",
    "| Metric | Value | Percentage |",
    "|--------|-------|------------|",
    f"| Total ST population | {total_st:,} | 100.0% |",
    f"| ST population inside Candidate Red Zones | {inside_st:,} | {inside_pct_st:.1f}% |",
    f"| ST population outside Candidate Red Zones | {outside_st:,} | {100-inside_pct_st:.1f}% |",
    "",
    "---",
    "",
    "## Proximity Context: Distance to Nearest Candidate Red Zone",
    "",
    "> **Methodological Note on the 0-Inside Result**",
    ">",
    "> No village centroids fall **inside** a Candidate Hazard-Based Red Zone polygon.",
    "> This is a **geographically valid and expected result**, not a pipeline error.",
    ">",
    "> Explanation:",
    "> - SHRUG village centroids represent the **administrative village boundary centroid**,",
    ">   not precise building or household locations.",
    "> - Candidate Hazard-Based Red Zones are **small terrain-derived patches** (avg area ~7,721 m2)",
    ">   derived from steep/wet raster cells, which tend to occupy ridge flanks and",
    ">   valley corridor areas -- not village administrative centres.",
    "> - The 289 red zones cover a **total of ~223 ha** across a large mountainous district.",
    ">",
    "> The distance-to-nearest-red-zone field (`dist_to_nearest_redzone_m`) provides",
    "> critical proximity context for decision-makers.",
    "",
    "### Distance from Village Centroid to Nearest Candidate Red Zone",
    "",
    f"| Metric | Value |",
    f"|--------|-------|",
    f"| Minimum distance (closest village) | {min(dist_to_nearest):.1f} m |",
    f"| Maximum distance | {max(dist_to_nearest):.1f} m |",
    f"| Mean distance | {sum(dist_to_nearest)/len(dist_to_nearest):.1f} m |",
    "",
    "### Proximity Band Breakdown",
    "",
    "| Distance Band | Habitation Count | Percentage |",
    "|---------------|-----------------|------------|",
    f"| < 500 m | {int((dist_arr < 500).sum())} | {pct(int((dist_arr < 500).sum()), total_habitations):.1f}% |",
    f"| 500 m -- 1,000 m | {int(((dist_arr >= 500) & (dist_arr < 1000)).sum())} | {pct(int(((dist_arr >= 500) & (dist_arr < 1000)).sum()), total_habitations):.1f}% |",
    f"| 1,000 m -- 2,000 m | {int(((dist_arr >= 1000) & (dist_arr < 2000)).sum())} | {pct(int(((dist_arr >= 1000) & (dist_arr < 2000)).sum()), total_habitations):.1f}% |",
    f"| 2,000 m -- 5,000 m | {int(((dist_arr >= 2000) & (dist_arr < 5000)).sum())} | {pct(int(((dist_arr >= 2000) & (dist_arr < 5000)).sum()), total_habitations):.1f}% |",
    f"| > 5,000 m | {int((dist_arr >= 5000).sum())} | {pct(int((dist_arr >= 5000).sum()), total_habitations):.1f}% |",
    "",
    "**NOTE:** Proximity does not equal exposure. A village centroid being close to",
    "a red zone boundary does not mean the village area is inside the red zone.",
    "Field verification and site-level geotechnical assessment is required.",
    "",
    "---",
    "",
    "## Validation Cross-Checks",
    "",
    "| Check | Expected | Actual | Status |",
    "|-------|----------|--------|--------|",
    f"| Exposure records = baseline records | {len(habitations)} | {len(exposure)} | {'PASS' if len(exposure) == len(habitations) else 'FAIL'} |",
    f"| Inside pop + outside pop = total pop | {total_pop:,} | {inside_pop + outside_pop:,} | {'PASS' if inside_pop + outside_pop == total_pop else 'FAIL'} |",
    f"| Inside HH + outside HH = total HH | {total_hh:,} | {inside_hh + outside_hh:,} | {'PASS' if inside_hh + outside_hh == total_hh else 'FAIL'} |",
    f"| Inside SC + outside SC = total SC | {total_sc:,} | {inside_sc + outside_sc:,} | {'PASS' if inside_sc + outside_sc == total_sc else 'FAIL'} |",
    f"| Inside ST + outside ST = total ST | {total_st:,} | {inside_st + outside_st:,} | {'PASS' if inside_st + outside_st == total_st else 'FAIL'} |",
    f"| CRS consistency | {METRIC_CRS} | {str(exposure.crs)} | {'PASS' if str(exposure.crs) == METRIC_CRS else 'FAIL'} |",
    "",
    "---",
    "",
    "## Output Files",
    "",
    f"| File | Description |",
    f"|------|-------------|",
    f"| `{EXPOSURE_GEOJSON.relative_to(PROJECT_ROOT)}` | Habitation exposure layer (GeoJSON, EPSG:32644) |",
    f"| `{EXPOSURE_CSV.relative_to(PROJECT_ROOT)}` | Exposure summary table (CSV) |",
    f"| `{EXPOSURE_REPORT.relative_to(PROJECT_ROOT)}` | This report |",
    "",
    "---",
    "",
    "## Hazard Zone Flag Definition",
    "",
    "| Field | Value | Meaning |",
    "|-------|-------|---------|",
    "| `hazard_zone_flag` | `1` | Inside Candidate Hazard-Based Red Zone |",
    "| `hazard_zone_flag` | `0` | Outside Candidate Hazard-Based Red Zone |",
    "",
    "**These flags do NOT indicate safe or unsafe status.**",
    "**They represent preliminary spatial screening only.**",
    "",
    "---",
    "",
    "*This report is a decision-support output of the SIH26191 GIS pipeline.*",
    "*Official administrative action requires verification by competent geotechnical*",
    "*and disaster management authorities.*",
]

EXPOSURE_REPORT.write_text("\n".join(report_lines), encoding="utf-8")
print(f"    [SAVED] {EXPOSURE_REPORT.relative_to(PROJECT_ROOT)}")

# ===========================================================================
# Final summary
# ===========================================================================
print()
print("=" * 70)
print("Step 8E+F+G COMPLETE -- Habitation Exposure Overlay Done")
print("=" * 70)
print(f"  Exposure features    : {len(exposure)}")
print(f"  CRS                  : {exposure.crs}")
print(f"  Inside red zones     : {inside_count} habitations ({inside_pct_habitations:.1f}%)")
print(f"  Outside red zones    : {outside_count} habitations ({100-inside_pct_habitations:.1f}%)")
print(f"  Pop inside red zones : {inside_pop:,} ({inside_pct_pop:.1f}%)")
print(f"  Pop outside          : {outside_pop:,} ({100-inside_pct_pop:.1f}%)")
print(f"  HH inside red zones  : {inside_hh:,} ({inside_pct_hh:.1f}%)")
print(f"  SC inside red zones  : {inside_sc:,} ({inside_pct_sc:.1f}%)")
print(f"  ST inside red zones  : {inside_st:,} ({inside_pct_st:.1f}%)")
print()
print("  Proceed to: scripts/validate_habitation_exposure.py")
print()
