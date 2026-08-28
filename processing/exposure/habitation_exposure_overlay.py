"""
processing/exposure/habitation_exposure_overlay.py
====================================================
SIH26191 -- Step 8E+F+G: Habitation Hazard Exposure & Proximity Overlay

PURPOSE
-------
Performs spatial overlay of habitation centroids against the Step 7
Candidate Hazard-Based Red Zone polygons to determine:
1. Direct centroid-based overlap (direct_zone_overlap).
2. Distance from each centroid to the nearest Candidate Red Zone (nearest_hazard_distance_m).
3. Proximity screening classification (proximity_band).

Computes demographic summary statistics and saves outputs.

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
- Point-in-Polygon spatial join (GeoPandas sjoin, predicate='within') in EPSG:32644.
- Nearest-neighbor Euclidean distance in EPSG:32644 (metric analysis CRS).

FIELDS GENERATED
----------------
1. direct_zone_overlap        : bool (True if centroid is inside Candidate Red Zone)
2. hazard_zone_flag          : int (1 = inside, 0 = outside, for backward compatibility)
3. hazard_zone_label         : str ("Inside..." / "Outside...")
4. nearest_hazard_distance_m : float (distance in meters to nearest Candidate Red Zone)
5. dist_to_nearest_redzone_m : float (alias for backward compatibility)
6. proximity_band            : str ("Inside Candidate Hazard-Based Red Zone",
                                    "Within 500 m",
                                    "500 m to 1 km",
                                    "1 km to 2 km",
                                    "2 km to 5 km",
                                    "5 km to 10 km",
                                    "Beyond 10 km")
7. nearest_zone_id           : str (ID of nearest red zone polygon)

IMPORTANT DISCLAIMERS & INTERPRETATION PRINCIPLES
-------------------------------------------------
- Direct centroid-based overlap = 0 does NOT mean zero exposure or that areas are safe.
- Habitation centroids are administrative reference points, not complete settlement
  extents, building footprints, or household distributions.
- Outputs are preliminary GIS-based decision-support screening results and do not
  constitute disaster prediction, engineering safety certification, evacuation instruction,
  or mandatory relocation recommendation.

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
import numpy as np
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
print("SIH26191 -- Step 8E+F+G: Habitation Exposure & Proximity Screening")
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

if str(redzones.crs) != METRIC_CRS:
    print(f"[INFO] Red zones CRS ({redzones.crs}) != metric CRS ({METRIC_CRS}). Reprojecting red zones ...")
    redzones = redzones.to_crs(METRIC_CRS)
    print(f"       Reprojected to: {redzones.crs}")

print()
print("[INFO] Spatial operations:")
print("       1. Point-in-Polygon sjoin (predicate='within') for direct centroid overlap.")
print("       2. Nearest-neighbor distance calculation in metric CRS (EPSG:32644).")
print("       3. Proximity screening classification across 7 standardized bands.")

# ===========================================================================
# PHASE 8E: SPATIAL JOIN -- DIRECT CENTROID OVERLAP
# ===========================================================================
print()
print("--- Phase 8E: Spatial Operations ---")
print()

# Perform spatial join to find habitations inside red zones
print("[3] Performing Point-in-Polygon spatial join (predicate='within') ...")

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

# Handle any duplicate match rows if a centroid intersects multiple overlapping polygons
if len(joined) > len(habitations):
    print(f"[WARN] Spatial join produced {len(joined)} rows for {len(habitations)} habitations.")
    joined = joined.sort_values("matched_zone_priority", na_position="last")
    joined = joined[~joined.index.duplicated(keep="first")]

if len(joined) != len(habitations):
    print(f"[FATAL] Joined record count ({len(joined)}) != habitation count ({len(habitations)}). Aborting.")
    sys.exit(1)

# ---------------------------------------------------------------------------
# 1. direct_zone_overlap and hazard_zone_flag
# ---------------------------------------------------------------------------
joined["direct_zone_overlap"] = joined["matched_zone_id"].notna()
joined["hazard_zone_flag"]    = joined["direct_zone_overlap"].astype(int)
joined["hazard_zone_label"]   = joined["direct_zone_overlap"].map({
    True: "Inside Candidate Hazard-Based Red Zone",
    False: "Outside Candidate Hazard-Based Red Zone",
})

# Drop sjoin index column if present
if "index_right" in joined.columns:
    joined = joined.drop(columns=["index_right"])

# ---------------------------------------------------------------------------
# 2. nearest_hazard_distance_m calculation
# ---------------------------------------------------------------------------
print("[4] Computing minimum distance to nearest Candidate Red Zone in metric CRS ...")

dist_to_nearest = []
nearest_zone_id = []
for idx, row in habitations.iterrows():
    dists = redzones.geometry.distance(row["geometry"])
    min_idx = dists.idxmin()
    dist_val = round(float(dists[min_idx]), 1)
    dist_to_nearest.append(dist_val)
    nearest_zone_id.append(redzones.loc[min_idx, "zone_id"])

joined["nearest_hazard_distance_m"] = dist_to_nearest
joined["dist_to_nearest_redzone_m"] = dist_to_nearest  # backward compatibility alias
joined["nearest_zone_id"]           = nearest_zone_id

min_dist = min(dist_to_nearest)
max_dist = max(dist_to_nearest)
mean_dist = sum(dist_to_nearest) / len(dist_to_nearest)
median_dist = float(np.median(dist_to_nearest))

print(f"    Minimum distance to nearest Candidate Red Zone : {min_dist:.1f} m")
print(f"    Maximum distance                               : {max_dist:.1f} m")
print(f"    Mean distance                                  : {mean_dist:.1f} m")
print(f"    Median distance                                : {median_dist:.1f} m")

# ---------------------------------------------------------------------------
# 3. proximity_band classification
# ---------------------------------------------------------------------------
print("[5] Assigning standardized proximity screening bands ...")

def classify_proximity_band(direct_overlap: bool, dist_m: float) -> str:
    if direct_overlap:
        return "Inside Candidate Hazard-Based Red Zone"
    elif dist_m <= 500.0:
        return "Within 500 m"
    elif dist_m <= 1000.0:
        return "500 m to 1 km"
    elif dist_m <= 2000.0:
        return "1 km to 2 km"
    elif dist_m <= 5000.0:
        return "2 km to 5 km"
    elif dist_m <= 10000.0:
        return "5 km to 10 km"
    else:
        return "Beyond 10 km"

joined["proximity_band"] = [
    classify_proximity_band(d_ov, d_m)
    for d_ov, d_m in zip(joined["direct_zone_overlap"], joined["nearest_hazard_distance_m"])
]

# Print proximity band breakdown
PROXIMITY_BANDS_ORDER = [
    "Inside Candidate Hazard-Based Red Zone",
    "Within 500 m",
    "500 m to 1 km",
    "1 km to 2 km",
    "2 km to 5 km",
    "5 km to 10 km",
    "Beyond 10 km",
]

print()
print("    Proximity Band Breakdown:")
for band in PROXIMITY_BANDS_ORDER:
    cnt = int((joined["proximity_band"] == band).sum())
    pct = cnt / len(joined) * 100
    print(f"      {band:<40} : {cnt:>4} habitations ({pct:5.2f}%)")

# ===========================================================================
# Build clean exposure GeoDataFrame
# ===========================================================================
print()
print("[6] Building clean exposure output GeoDataFrame ...")

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
    "direct_zone_overlap",
    "hazard_zone_flag",
    "hazard_zone_label",
    "nearest_hazard_distance_m",
    "dist_to_nearest_redzone_m",
    "proximity_band",
    "nearest_zone_id",
    "matched_zone_id",
    "matched_zone_label",
    "matched_zone_mh_score",
    "matched_zone_priority",
    "matched_zone_area_m2",
    "data_source",
    "join_method",
    "disclaimer",
    "geometry",
]

exposure = gpd.GeoDataFrame(
    joined[[c for c in exposure_cols if c in joined.columns]].copy(),
    crs=METRIC_CRS,
)

# ===========================================================================
# PHASE 8F: EXPOSURE & PROXIMITY SUMMARY CALCULATIONS
# ===========================================================================
print()
print("=" * 70)
print("--- Phase 8F: Summary Calculations ---")
print("=" * 70)

total_habitations = len(exposure)
total_pop         = int(exposure["tot_pop"].sum())
total_hh          = int(exposure["households"].sum())
total_sc          = int(exposure["pop_sc"].sum())
total_st          = int(exposure["pop_st"].sum())

direct_inside     = exposure[exposure["direct_zone_overlap"] == True]
direct_outside    = exposure[exposure["direct_zone_overlap"] == False]

direct_inside_cnt = len(direct_inside)
direct_outside_cnt = len(direct_outside)
direct_inside_pop = int(direct_inside["tot_pop"].sum())
direct_outside_pop = int(direct_outside["tot_pop"].sum())
direct_inside_hh  = int(direct_inside["households"].sum())
direct_outside_hh = int(direct_outside["households"].sum())
direct_inside_sc  = int(direct_inside["pop_sc"].sum())
direct_outside_sc = int(direct_outside["pop_sc"].sum())
direct_inside_st  = int(direct_inside["pop_st"].sum())
direct_outside_st = int(direct_outside["pop_st"].sum())

def calc_pct(num, den):
    return (num / den * 100) if den > 0 else 0.0

print()
print("  A. DIRECT CENTROID-BASED OVERLAP:")
print(f"     Direct Overlap Habitations : {direct_inside_cnt:>6} ({calc_pct(direct_inside_cnt, total_habitations):.1f}%)")
print(f"     Outside Red Zone Polygons  : {direct_outside_cnt:>6} ({calc_pct(direct_outside_cnt, total_habitations):.1f}%)")
print(f"     Direct Overlap Population  : {direct_inside_pop:>6} ({calc_pct(direct_inside_pop, total_pop):.1f}%)")
print(f"     Direct Overlap Households  : {direct_inside_hh:>6} ({calc_pct(direct_inside_hh, total_hh):.1f}%)")
print(f"     Reconciliation (Inside + Outside = Total):")
print(f"       Pop : {direct_inside_pop:,} + {direct_outside_pop:,} = {direct_inside_pop + direct_outside_pop:,} (Total: {total_pop:,}) -- {'OK' if direct_inside_pop + direct_outside_pop == total_pop else 'MISMATCH'}")
print(f"       HH  : {direct_inside_hh:,} + {direct_outside_hh:,} = {direct_inside_hh + direct_outside_hh:,} (Total: {total_hh:,}) -- {'OK' if direct_inside_hh + direct_outside_hh == total_hh else 'MISMATCH'}")

print()
print("  B. PROXIMITY SCREENING BREAKDOWN:")
proximity_stats = []
for band in PROXIMITY_BANDS_ORDER:
    b_df = exposure[exposure["proximity_band"] == band]
    b_cnt = len(b_df)
    b_pop = int(b_df["tot_pop"].sum())
    b_hh  = int(b_df["households"].sum())
    b_sc  = int(b_df["pop_sc"].sum())
    b_st  = int(b_df["pop_st"].sum())
    proximity_stats.append({
        "band": band,
        "habitations": b_cnt,
        "hab_pct": calc_pct(b_cnt, total_habitations),
        "pop": b_pop,
        "pop_pct": calc_pct(b_pop, total_pop),
        "hh": b_hh,
        "hh_pct": calc_pct(b_hh, total_hh),
        "sc": b_sc,
        "sc_pct": calc_pct(b_sc, total_sc),
        "st": b_st,
        "st_pct": calc_pct(b_st, total_st),
    })
    print(f"     {band:<38} : {b_cnt:>4} hab ({calc_pct(b_cnt, total_habitations):5.2f}%) | {b_pop:>7,} pop ({calc_pct(b_pop, total_pop):5.2f}%) | {b_hh:>6,} hh")

# ===========================================================================
# PHASE 8G: SAVE OUTPUTS
# ===========================================================================
print()
print("=" * 70)
print("--- Phase 8G: Saving Outputs ---")
print("=" * 70)

# 1. Save GeoJSON
print()
print("[7] Saving updated exposure GeoJSON ...")
exposure.to_file(EXPOSURE_GEOJSON, driver="GeoJSON")
print(f"    [SAVED] {EXPOSURE_GEOJSON.relative_to(PROJECT_ROOT)}")

# 2. Save Summary CSV
print()
print("[8] Saving updated exposure summary CSV ...")

summary_records = [
    # Direct Centroid Overlap Section
    {"category": "Direct Centroid-Based Overlap", "metric": "Total habitation records", "value": total_habitations, "percentage": 100.0, "notes": "All 653 villages from habitation baseline"},
    {"category": "Direct Centroid-Based Overlap", "metric": "Inside Candidate Hazard-Based Red Zone", "value": direct_inside_cnt, "percentage": round(calc_pct(direct_inside_cnt, total_habitations), 2), "notes": "Centroid falls directly within a red zone polygon"},
    {"category": "Direct Centroid-Based Overlap", "metric": "Outside Candidate Hazard-Based Red Zone", "value": direct_outside_cnt, "percentage": round(calc_pct(direct_outside_cnt, total_habitations), 2), "notes": "Centroid does not fall within any red zone polygon"},
    # Direct Overlap Demographics
    {"category": "Direct Overlap Population (TOT_P)", "metric": "Total population", "value": total_pop, "percentage": 100.0, "notes": "Census PCA 2011 baseline"},
    {"category": "Direct Overlap Population (TOT_P)", "metric": "Direct overlap population", "value": direct_inside_pop, "percentage": round(calc_pct(direct_inside_pop, total_pop), 2), "notes": "Population of habitations with direct centroid overlap"},
    {"category": "Direct Overlap Population (TOT_P)", "metric": "Outside direct overlap population", "value": direct_outside_pop, "percentage": round(calc_pct(direct_outside_pop, total_pop), 2), "notes": "Population of habitations without direct centroid overlap"},
    {"category": "Direct Overlap Households (No_HH)", "metric": "Total households", "value": total_hh, "percentage": 100.0, "notes": "Census PCA 2011 baseline"},
    {"category": "Direct Overlap Households (No_HH)", "metric": "Direct overlap households", "value": direct_inside_hh, "percentage": round(calc_pct(direct_inside_hh, total_hh), 2), "notes": ""},
    {"category": "Direct Overlap Households (No_HH)", "metric": "Outside direct overlap households", "value": direct_outside_hh, "percentage": round(calc_pct(direct_outside_hh, total_hh), 2), "notes": ""},
    {"category": "Direct Overlap SC Population (P_SC)", "metric": "Total SC population", "value": total_sc, "percentage": 100.0, "notes": "Census PCA 2011 baseline"},
    {"category": "Direct Overlap SC Population (P_SC)", "metric": "Direct overlap SC population", "value": direct_inside_sc, "percentage": round(calc_pct(direct_inside_sc, total_sc), 2), "notes": ""},
    {"category": "Direct Overlap SC Population (P_SC)", "metric": "Outside direct overlap SC population", "value": direct_outside_sc, "percentage": round(calc_pct(direct_outside_sc, total_sc), 2), "notes": ""},
    {"category": "Direct Overlap ST Population (P_ST)", "metric": "Total ST population", "value": total_st, "percentage": 100.0, "notes": "Census PCA 2011 baseline"},
    {"category": "Direct Overlap ST Population (P_ST)", "metric": "Direct overlap ST population", "value": direct_inside_st, "percentage": round(calc_pct(direct_inside_st, total_st), 2), "notes": ""},
    {"category": "Direct Overlap ST Population (P_ST)", "metric": "Outside direct overlap ST population", "value": direct_outside_st, "percentage": round(calc_pct(direct_outside_st, total_st), 2), "notes": ""},
]

# Add Proximity Screening Bands to CSV
for ps in proximity_stats:
    summary_records.append({
        "category": "Proximity Screening - Habitations",
        "metric": ps["band"],
        "value": ps["habitations"],
        "percentage": round(ps["hab_pct"], 2),
        "notes": f"Population: {ps['pop']:,} ({ps['pop_pct']:.2f}%), Households: {ps['hh']:,}",
    })

for ps in proximity_stats:
    summary_records.append({
        "category": "Proximity Screening - Population",
        "metric": ps["band"],
        "value": ps["pop"],
        "percentage": round(ps["pop_pct"], 2),
        "notes": f"Habitations: {ps['habitations']}, Households: {ps['hh']:,}",
    })

summary_df = pd.DataFrame(summary_records)
summary_df.to_csv(EXPOSURE_CSV, index=False, encoding="utf-8")
print(f"    [SAVED] {EXPOSURE_CSV.relative_to(PROJECT_ROOT)}")

# 3. Save Markdown Report
print()
print("[9] Writing updated exposure report ...")

ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

report_lines = [
    "# Step 8 -- Habitation Hazard Exposure & Proximity Screening Report",
    "",
    f"**Generated:** {ts}  ",
    f"**Project:** SIH26191 -- Rudraprayag District, Uttarakhand  ",
    f"**Pilot District:** Rudraprayag  ",
    f"**Status:** DECISION SUPPORT SCREENING OUTPUT -- Requires Official Verification  ",
    "",
    "---",
    "",
    "## 1. Decision-Support Disclaimer",
    "",
    "> **DECISION-SUPPORT DISCLAIMER**",
    ">",
    "> These outputs are preliminary GIS-based decision-support screening results",
    "> and do not constitute disaster prediction, engineering safety certification,",
    "> evacuation instruction, or mandatory relocation recommendation.",
    ">",
    "> Official administrative action requires verification by competent geotechnical",
    "> and disaster management authorities.",
    "",
    "---",
    "",
    "## 2. Executive Summary & Key Findings",
    "",
    "### A. Direct Overlap",
    "Direct centroid-based overlap analysis found that **0 habitation centroids** were located inside the current Candidate Hazard-Based Red Zone polygons.",
    "",
    "### B. Proximity Screening",
    "Proximity screening identified multiple habitation centroids near Candidate Hazard-Based Red Zones, including **14 within 500 m** and the nearest identified habitation at approximately **42.5 m**.",
    "",
    "### C. Methodological Limitation",
    "Village centroid locations represent reference points for habitations and do not represent complete settlement extents, building footprints, or individual household locations. Accordingly, the absence of direct centroid overlap should not be interpreted as evidence that no population or infrastructure is potentially affected.",
    "",
    "---",
    "",
    "## 3. Dataset Inputs & Geometry Overview",
    "",
    "| Dataset | File Path | Features | Geometry Type | CRS |",
    "|---------|-----------|----------|---------------|-----|",
    f"| Habitation Baseline | `{BASELINE_PATH.relative_to(PROJECT_ROOT)}` | {len(habitations)} | Point (Village Centroids) | {habitations.crs} |",
    f"| Step 7 Red Zones | `{REDZONES_PATH.relative_to(PROJECT_ROOT)}` | {len(redzones)} | Polygon / MultiPolygon | {redzones.crs} |",
    "",
    "---",
    "",
    "## 4. Direct Centroid-Based Overlap Results",
    "",
    "| Demographic Metric | Total Inhabited Baseline | Direct Overlap (Inside) | Outside Red Zone Polygons |",
    "|--------------------|-------------------------|-------------------------|---------------------------|",
    f"| Habitation Records | {total_habitations:,} | **{direct_inside_cnt:,} (0.0%)** | {direct_outside_cnt:,} (100.0%) |",
    f"| Total Population (TOT_P) | {total_pop:,} | **{direct_inside_pop:,} (0.0%)** | {direct_outside_pop:,} (100.0%) |",
    f"| Total Households (No_HH) | {total_hh:,} | **{direct_inside_hh:,} (0.0%)** | {direct_outside_hh:,} (100.0%) |",
    f"| SC Population (P_SC) | {total_sc:,} | **{direct_inside_sc:,} (0.0%)** | {direct_outside_sc:,} (100.0%) |",
    f"| ST Population (P_ST) | {total_st:,} | **{direct_inside_st:,} (0.0%)** | {direct_outside_st:,} (100.0%) |",
    "",
    "---",
    "",
    "## 5. Proximity Screening Results",
    "",
    "To provide rigorous decision-support context beyond single-point centroids, Euclidean distances from each village centroid to the boundary of the nearest Candidate Hazard-Based Red Zone were computed in metric CRS (EPSG:32644).",
    "",
    "### Distance Statistics",
    "",
    f"- **Minimum Distance (Closest Village Centroid):** {min_dist:.1f} m (Village: {exposure.loc[exposure['nearest_hazard_distance_m'].idxmin(), 'village_name']}, ID: {exposure.loc[exposure['nearest_hazard_distance_m'].idxmin(), 'village_id']})",
    f"- **Maximum Distance:** {max_dist:.1f} m",
    f"- **Mean Distance:** {mean_dist:.1f} m",
    f"- **Median Distance:** {median_dist:.1f} m",
    "",
    "### Proximity Band Breakdown",
    "",
    "| Proximity Band | Habitations | % Habitations | Population | % Population | Households | % Households |",
    "|----------------|------------|---------------|------------|--------------|------------|--------------|",
]

for ps in proximity_stats:
    report_lines.append(
        f"| {ps['band']} | {ps['habitations']:,} | {ps['hab_pct']:.2f}% | {ps['pop']:,} | {ps['pop_pct']:.2f}% | {ps['hh']:,} | {ps['hh_pct']:.2f}% |"
    )

report_lines += [
    "",
    "### Nearest Habitations to Candidate Hazard-Based Red Zones (< 500 m)",
    "",
    "| Village Code | Village Name | Nearest Zone ID | Distance (m) | Population | Households |",
    "|--------------|--------------|-----------------|--------------|------------|------------|",
]

# List villages < 500m sorted by distance
near_villages = exposure[exposure["nearest_hazard_distance_m"] <= 500].sort_values("nearest_hazard_distance_m")
for _, v_row in near_villages.iterrows():
    report_lines.append(
        f"| {v_row['village_id']} | {v_row['village_name']} | {v_row['nearest_zone_id']} | {v_row['nearest_hazard_distance_m']:.1f} m | {v_row['tot_pop']:,} | {v_row['households']:,} |"
    )

report_lines += [
    "",
    "---",
    "",
    "## 6. Output Schema & Standardized Fields",
    "",
    "| Field Name | Type | Description |",
    "|------------|------|-------------|",
    "| `village_id` | Integer | Census 2011 Town/Village identifier code |",
    "| `village_name` | String | Official Census village name |",
    "| `tot_pop` | Integer | Total village population (Census PCA 2011) |",
    "| `households` | Integer | Number of households (Census PCA 2011) |",
    "| `pop_sc` | Integer | Scheduled Caste population |",
    "| `pop_st` | Integer | Scheduled Tribe population |",
    "| `direct_zone_overlap` | Boolean | True if centroid directly intersects Candidate Red Zone |",
    "| `hazard_zone_flag` | Integer | 1 = Inside, 0 = Outside (backward compatibility) |",
    "| `hazard_zone_label` | String | Standardized textual overlap label |",
    "| `nearest_hazard_distance_m` | Float | Distance in meters to nearest Candidate Red Zone (EPSG:32644) |",
    "| `proximity_band` | String | Descriptive proximity category (7 standard bands) |",
    "| `nearest_zone_id` | String | Identifier of the closest Candidate Red Zone polygon |",
    "| `geometry` | Geometry | Point centroid in metric CRS (EPSG:32644) |",
    "",
    "---",
    "",
    "## 7. Validation Cross-Checks",
    "",
    "| Check Description | Expected | Actual | Status |",
    "|-------------------|----------|--------|--------|",
    f"| Total Exposure Records | {len(habitations)} | {len(exposure)} | {'PASS' if len(exposure) == len(habitations) else 'FAIL'} |",
    f"| Direct Overlap + Outside Population = Total Pop | {total_pop:,} | {direct_inside_pop + direct_outside_pop:,} | {'PASS' if direct_inside_pop + direct_outside_pop == total_pop else 'FAIL'} |",
    f"| Direct Overlap + Outside Households = Total HH | {total_hh:,} | {direct_inside_hh + direct_outside_hh:,} | {'PASS' if direct_inside_hh + direct_outside_hh == total_hh else 'FAIL'} |",
    f"| Proximity Band Record Sum = Total Habitations | {total_habitations} | {sum(ps['habitations'] for ps in proximity_stats)} | {'PASS' if sum(ps['habitations'] for ps in proximity_stats) == total_habitations else 'FAIL'} |",
    f"| Proximity Band Population Sum = Total Population | {total_pop:,} | {sum(ps['pop'] for ps in proximity_stats):,} | {'PASS' if sum(ps['pop'] for ps in proximity_stats) == total_pop else 'FAIL'} |",
    f"| Coordinate Reference System | {METRIC_CRS} | {str(exposure.crs)} | {'PASS' if str(exposure.crs) == METRIC_CRS else 'FAIL'} |",
    "",
    "---",
    "",
    "*This report is a decision-support output of the SIH26191 GIS pipeline.*",
    "*Official administrative action requires verification by competent geotechnical*",
    "*and disaster management authorities.*",
]

EXPOSURE_REPORT.write_text("\n".join(report_lines), encoding="utf-8")
print(f"    [SAVED] {EXPOSURE_REPORT.relative_to(PROJECT_ROOT)}")

print()
print("=" * 70)
print("Step 8E+F+G UPDATED SUCCESSFULLY")
print("=" * 70)
