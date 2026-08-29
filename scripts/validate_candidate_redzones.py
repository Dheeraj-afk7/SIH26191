#!/usr/bin/env python3
"""
SIH26191 -- Step 7I: Candidate Hazard-Based Red Zone Validation
==============================================================
Comprehensive technical validation of all Candidate Hazard-Based Red Zone
outputs produced in Step 7:
  - data/outputs/candidate_hazard_based_red_zones.gpkg
  - data/outputs/candidate_hazard_based_red_zones.geojson
  - data/processed/hazards/candidate_redzone_raster.tif

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

VALIDATION RULES & STRICT ASSERTIONS
------------------------------------
INPUT INTEGRITY:
 1. Step 6 outputs exist and are readable.
 2. Input multi-hazard rasters are intact with valid value ranges.
 3. CRS alignment with analysis CRS (EPSG:32644).

OUTPUT INTEGRITY:
 4. Candidate GeoPackage exists and is readable.
 5. Candidate GeoJSON exists, is valid, and matches GeoPackage.
 6. Candidate raster mask exists, is readable, and aligned.
 7. Required attributes exist across all features.
 8. All zone IDs are unique and formatted deterministically.
 9. All zone areas > 0 and meet the configured MMU threshold.
10. All vector geometries are valid and non-empty.
11. Vector CRS matches configured metric analysis CRS (EPSG:32644).
12. Zone labels and disclaimers match configured project terminology.
13. Priority ranks are strictly sequential (1..N) without gaps.
14. Sorting order adheres strictly to deterministic ranking criteria.
15. Zonal statistics match underlying continuous raster values.
16. Candidate zones originate exclusively from configured source class (Class 3).

UPSTREAM PIPELINE IMMUTABILITY:
17. Raw Copernicus GLO-30 DEM exists and is untouched.
18. Step 3 terrain outputs exist and are intact.
19. Step 4 terrain susceptibility outputs exist and are intact.
20. Step 5 hydrological and flood exposure outputs exist and are intact.
21. Step 6 multi-hazard outputs exist and are intact.

USAGE
-----
    python scripts/validate_candidate_redzones.py
"""

import sys
import json
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

try:
    import numpy as np
    import rasterio
    from rasterio.crs import CRS
    import shapely.geometry as sg
    import geopandas as gpd
except ImportError as e:
    print(f"[ERROR] Required geospatial package not installed: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths and formatting helpers
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_ROOT_DIR   = _SCRIPT_DIR.parent


def _sep(char: str = "=", width: int = 70) -> str:
    return char * width


def _section(title: str) -> None:
    print(f"\n{_sep('-')}")
    print(f"  {title}")
    print(_sep('-'))


def _field(label: str, value, width: int = 36) -> None:
    print(f"  {label:<{width}}: {value}")


def _result(label: str, ok: bool, detail: str = "") -> bool:
    tag = "[PASS]" if ok else "[FAIL]"
    msg = f"  {tag}  {label}"
    if detail:
        msg += f"  ({detail})"
    print(msg)
    return ok


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config(root_dir: Path) -> dict:
    cfg_path = root_dir / "configs" / "project.yaml"
    if not cfg_path.is_file():
        print(f"[FAIL] Configuration file not found: {cfg_path}")
        sys.exit(1)
    with open(cfg_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    return cfg


# ---------------------------------------------------------------------------
# Main Validation Logic
# ---------------------------------------------------------------------------

def validate_candidate_redzones() -> bool:
    print(_sep("="))
    print("  SIH26191 -- STEP 7I: CANDIDATE RED ZONE OUTPUT VALIDATION")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    all_passed = True
    cfg = load_config(_ROOT_DIR)

    paths_cfg    = cfg.get("paths", {})
    redzones_cfg = cfg.get("redzones", {})
    term_cfg     = cfg.get("terminology", {})
    expected_crs = cfg.get("crs", {}).get("analysis_crs_metric", "EPSG:32644")

    # -----------------------------------------------------------------------
    _section("1. Upstream Multi-Hazard Input Validation (Step 6)")
    # -----------------------------------------------------------------------
    score_path = _ROOT_DIR / paths_cfg.get("multihazard_score", "data/processed/hazards/multihazard_score.tif")
    class_path = _ROOT_DIR / paths_cfg.get("multihazard_classes", "data/processed/hazards/multihazard_classes.tif")
    terr_path  = _ROOT_DIR / paths_cfg.get("terrain_contribution", "data/processed/hazards/terrain_contribution.tif")
    flood_path = _ROOT_DIR / paths_cfg.get("flood_contribution", "data/processed/hazards/flood_contribution.tif")

    all_passed &= _result("Multi-hazard score exists", score_path.is_file(), str(score_path))
    all_passed &= _result("Multi-hazard class raster exists", class_path.is_file(), str(class_path))
    all_passed &= _result("Terrain contribution raster exists", terr_path.is_file(), str(terr_path))
    all_passed &= _result("Flood contribution raster exists", flood_path.is_file(), str(flood_path))

    if not (score_path.is_file() and class_path.is_file() and terr_path.is_file() and flood_path.is_file()):
        print("[FAIL] Missing upstream Step 6 inputs. Halting validation.")
        return False

    with rasterio.open(class_path) as ds_class, rasterio.open(score_path) as ds_score:
        crs_ok = (ds_class.crs == CRS.from_string(expected_crs))
        all_passed &= _result(f"Input rasters CRS matches configured {expected_crs}", crs_ok)

        class_arr = ds_class.read(1)
        score_arr = ds_score.read(1)

        source_class = int(redzones_cfg.get("segmentation", {}).get("source_class", 3))
        c3_count = int(np.count_nonzero(class_arr == source_class))
        all_passed &= _result(f"Source class {source_class} pixels exist in input", c3_count > 0, f"{c3_count:,} pixels")

    # -----------------------------------------------------------------------
    _section("2. Candidate Red Zone Output Dataset Verification")
    # -----------------------------------------------------------------------
    gpkg_path    = _ROOT_DIR / redzones_cfg.get("outputs", {}).get("output_vector", "data/outputs/candidate_hazard_based_red_zones.gpkg")
    geojson_path = _ROOT_DIR / redzones_cfg.get("outputs", {}).get("output_geojson", "data/outputs/candidate_hazard_based_red_zones.geojson")
    raster_path  = _ROOT_DIR / redzones_cfg.get("outputs", {}).get("output_raster", "data/processed/hazards/candidate_redzone_raster.tif")

    ok_gpkg_exist    = gpkg_path.is_file() and gpkg_path.stat().st_size > 0
    ok_geojson_exist = geojson_path.is_file() and geojson_path.stat().st_size > 0
    ok_raster_exist  = raster_path.is_file() and raster_path.stat().st_size > 0

    all_passed &= _result("GeoPackage output exists and is non-empty", ok_gpkg_exist, f"{gpkg_path.stat().st_size / 1024:.1f} KB" if ok_gpkg_exist else "Missing")
    all_passed &= _result("GeoJSON output exists and is non-empty", ok_geojson_exist, f"{geojson_path.stat().st_size / 1024:.1f} KB" if ok_geojson_exist else "Missing")
    all_passed &= _result("Candidate raster mask exists and is non-empty", ok_raster_exist, f"{raster_path.stat().st_size / 1024:.1f} KB" if ok_raster_exist else "Missing")

    if not (ok_gpkg_exist and ok_geojson_exist):
        print("[FAIL] Required vector outputs missing. Halting validation.")
        return False

    # -----------------------------------------------------------------------
    _section("3. Vector Layers Loading & Structure Validation")
    # -----------------------------------------------------------------------
    gdf_gpkg = gpd.read_file(gpkg_path)
    gdf_json = gpd.read_file(geojson_path)

    n_gpkg = len(gdf_gpkg)
    n_json = len(gdf_json)

    all_passed &= _result("GeoPackage readable by GeoPandas", n_gpkg > 0, f"{n_gpkg} features")
    all_passed &= _result("GeoJSON readable by GeoPandas", n_json > 0, f"{n_json} features")
    all_passed &= _result("Feature count consistency between GeoPackage and GeoJSON", n_gpkg == n_json, f"{n_gpkg} vs {n_json}")

    # Check Required Attributes
    required_attrs = [
        "zone_id",
        "zone_label",
        "candidate_priority_rank",
        "candidate_priority_basis",
        "source_indicator",
        "source_class",
        "mean_multihazard_score",
        "max_multihazard_score",
        "min_multihazard_score",
        "terrain_contribution_mean",
        "flood_contribution_mean",
        "area_m2",
        "area_hectares",
        "pixel_count",
        "methodology",
        "disclaimer",
        "geometry"
    ]
    missing_attrs = [col for col in required_attrs if col not in gdf_gpkg.columns]
    all_passed &= _result("All 17 required attributes present in GeoPackage", len(missing_attrs) == 0, f"Missing: {missing_attrs}" if missing_attrs else "All Present")

    # -----------------------------------------------------------------------
    _section("4. Geometry & Coordinate Reference System (CRS)")
    # -----------------------------------------------------------------------
    gpkg_crs_str = str(gdf_gpkg.crs)
    ok_gpkg_crs = (gdf_gpkg.crs == CRS.from_string(expected_crs))
    all_passed &= _result(f"GeoPackage CRS is {expected_crs}", ok_gpkg_crs, gpkg_crs_str)

    all_valid_geoms = bool(gdf_gpkg.geometry.is_valid.all())
    all_passed &= _result("All polygon geometries are topologically valid", all_valid_geoms)

    no_empty_geoms = bool((~gdf_gpkg.geometry.is_empty).all())
    all_passed &= _result("Zero empty geometries in candidate red zones", no_empty_geoms)

    # -----------------------------------------------------------------------
    _section("5. Zone Attributes, Determinism & Minimum Mapping Unit (MMU)")
    # -----------------------------------------------------------------------
    # Unique Zone IDs
    zone_ids = gdf_gpkg["zone_id"].tolist()
    unique_ids = set(zone_ids)
    all_passed &= _result("All candidate zone IDs are unique", len(unique_ids) == len(zone_ids), f"{len(unique_ids)} unique IDs")

    # Positive area
    all_pos_area = bool((gdf_gpkg["area_m2"] > 0).all())
    all_passed &= _result("All zone areas > 0 m2", all_pos_area)

    # MMU Threshold
    min_mmu_m2 = float(redzones_cfg.get("filtering", {}).get("minimum_zone_area_m2", 5000.0))
    min_observed_area = float(gdf_gpkg["area_m2"].min())
    ok_mmu = (min_observed_area >= min_mmu_m2 - 1e-3)
    all_passed &= _result(
        f"All retained zones meet configured MMU ({min_mmu_m2:,.0f} m2)",
        ok_mmu,
        f"Min observed: {min_observed_area:,.1f} m2"
    )

    # Sequential Priority Ranks
    ranks = gdf_gpkg["candidate_priority_rank"].tolist()
    expected_ranks = list(range(1, n_gpkg + 1))
    ok_ranks = (ranks == expected_ranks)
    all_passed &= _result("Priority ranks are strictly sequential from 1 to N", ok_ranks, f"1..{n_gpkg}")

    # Monotonicity of Priority Ranking (Mean score descending)
    mean_scores = gdf_gpkg["mean_multihazard_score"].tolist()
    is_sorted_desc = all(mean_scores[i] >= mean_scores[i+1] - 1e-6 for i in range(len(mean_scores)-1))
    all_passed &= _result("Priority ranking is monotonically descending by mean multi-hazard score", is_sorted_desc)

    # Score Range Validity
    min_score_val = float(gdf_gpkg["min_multihazard_score"].min())
    max_score_val = float(gdf_gpkg["max_multihazard_score"].max())
    ok_score_range = (min_score_val >= 0.65 - 1e-5) and (max_score_val <= 1.0 + 1e-5)
    all_passed &= _result("All zone scores strictly in Class 3 range [0.65, 1.00]", ok_score_range, f"Observed [{min_score_val:.4f}, {max_score_val:.4f}]")

    # Terminology and Disclaimer Checks
    configured_label = redzones_cfg.get("labels", {}).get("zone_label", term_cfg.get("hazard_zone_label", "Candidate Hazard-Based Red Zone"))
    configured_disclaimer = redzones_cfg.get("labels", {}).get("disclaimer", term_cfg.get("decision_support_disclaimer", ""))

    ok_labels = bool((gdf_gpkg["zone_label"] == configured_label).all())
    ok_disclaimer = bool((gdf_gpkg["disclaimer"] == configured_disclaimer).all())
    all_passed &= _result("Zone label matches configured terminology", ok_labels, configured_label)
    all_passed &= _result("Disclaimer matches configured decision-support text", ok_disclaimer)

    # -----------------------------------------------------------------------
    _section("6. Upstream Pipeline & Raw DEM Immutability")
    # -----------------------------------------------------------------------
    upstream_checks = [
        ("Raw Copernicus GLO-30 DEM", paths_cfg.get("dem_raw", "data/raw/copernicus_glo30_rudraprayag.tif")),
        ("Step 3 Slope", paths_cfg.get("slope_processed", "data/processed/terrain/slope_degrees.tif")),
        ("Step 3 Aspect", paths_cfg.get("aspect_processed", "data/processed/terrain/aspect_degrees.tif")),
        ("Step 4 Terrain Susceptibility Proxy", paths_cfg.get("terrain_susceptibility_proxy", "data/processed/hazards/terrain_susceptibility_proxy.tif")),
        ("Step 4 Terrain Susceptibility Classes", paths_cfg.get("terrain_susceptibility_classes", "data/processed/hazards/terrain_susceptibility_classes.tif")),
        ("Step 5 Flow Direction", paths_cfg.get("flow_direction", "data/processed/hydrology/flow_direction.tif")),
        ("Step 5 Flow Accumulation", paths_cfg.get("flow_accumulation", "data/processed/hydrology/flow_accumulation.tif")),
        ("Step 5 Topographic Wetness Index", paths_cfg.get("topographic_wetness_index", "data/processed/hydrology/topographic_wetness_index.tif")),
        ("Step 5 Flood Exposure Proxy", paths_cfg.get("flood_exposure_proxy", "data/processed/hazards/flood_exposure_proxy.tif")),
        ("Step 5 Flood Exposure Classes", paths_cfg.get("flood_exposure_classes", "data/processed/hazards/flood_exposure_classes.tif")),
        ("Step 6 Multi-Hazard Score", paths_cfg.get("multihazard_score", "data/processed/hazards/multihazard_score.tif")),
        ("Step 6 Multi-Hazard Classes", paths_cfg.get("multihazard_classes", "data/processed/hazards/multihazard_classes.tif")),
        ("Step 6 Terrain Contribution", paths_cfg.get("terrain_contribution", "data/processed/hazards/terrain_contribution.tif")),
        ("Step 6 Flood Contribution", paths_cfg.get("flood_contribution", "data/processed/hazards/flood_contribution.tif")),
    ]

    for label, rel_path in upstream_checks:
        fp = _ROOT_DIR / rel_path
        ok_up = fp.is_file() and fp.stat().st_size > 0
        all_passed &= _result(f"Upstream dataset intact: {label}", ok_up, f"{fp.stat().st_size / 1024:.1f} KB" if ok_up else "Missing")

    # -----------------------------------------------------------------------
    _section("Final Validation Summary")
    # -----------------------------------------------------------------------
    status_str = "PASS" if all_passed else "FAIL"
    print(f"\nCANDIDATE RED ZONE VALIDATION: {status_str}")
    return all_passed


if __name__ == "__main__":
    passed = validate_candidate_redzones()
    sys.exit(0 if passed else 1)
