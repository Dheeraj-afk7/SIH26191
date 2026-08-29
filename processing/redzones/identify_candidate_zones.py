#!/usr/bin/env python3
"""
SIH26191 -- Step 7: Candidate Hazard-Based Red Zone Generation
==============================================================
Transforms discrete Higher Multi-Hazard Indicator raster cells (Class 3) into
spatially coherent, contiguous, and attributed Candidate Hazard-Based Red Zones.

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

WORKFLOW & METHODOLOGY
----------------------
1. Dynamic Configuration:
   - Reads inputs, outputs, thresholds, connectivity, and labels from configs/project.yaml.
2. Source Selection:
   - Identifies raster cells matching configured source class (Class 3: Higher Multi-Hazard Indicator).
3. Connected Components Labeling:
   - Evaluates spatial contiguity using configured morphological connectivity (8-neighbour default).
4. Minimum Mapping Unit (MMU) Filtering:
   - Calculates geographic area of each contiguous cluster in metric units (m2) based on
     projected CRS resolution.
   - Filters out isolated micro-pixel clusters below configured minimum area threshold.
5. Geometry Extraction:
   - Vectorizes retained raster clusters into valid OGC Polygon/MultiPolygon geometries.
6. Zonal Multi-Hazard Statistics & Attribution:
   - Derives exact zonal statistics from underlying continuous score and contribution rasters:
     • mean_multihazard_score, max_multihazard_score, min_multihazard_score
     • terrain_contribution_mean, flood_contribution_mean
     • pixel_count, area_m2, area_hectares
7. Deterministic Priority Ranking:
   - Ranks candidate zones deterministically by Mean Multi-Hazard Score, then Max Score, then Area.
   - Assigns sequential candidate_priority_rank (1..N) and deterministic zone_id (RZ-001..RZ-NNN).
8. Vector & Raster Export:
   - GeoPackage: data/outputs/candidate_hazard_based_red_zones.gpkg
   - GeoJSON   : data/outputs/candidate_hazard_based_red_zones.geojson
   - Raster    : data/processed/hazards/candidate_redzone_raster.tif

DISCLAIMER
----------
Outputs are preliminary screening and decision-support layers.
They DO NOT constitute official government Red Zones, legal declarations,
evacuation orders, relocation authorizations, or engineering certifications.

USAGE
-----
    python processing/redzones/identify_candidate_zones.py
"""

import sys
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple

try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

try:
    import numpy as np
    import scipy.ndimage as ndi
    import rasterio
    import rasterio.features
    from rasterio.crs import CRS
    from rasterio.transform import Affine
    import shapely.geometry as sg
    import shapely.ops as so
    import geopandas as gpd
except ImportError as e:
    print(f"[ERROR] Required geospatial package not installed: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths and formatting helpers
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_ROOT_DIR   = _SCRIPT_DIR.parent.parent


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

def load_config() -> dict:
    cfg_path = _ROOT_DIR / "configs" / "project.yaml"
    if not cfg_path.is_file():
        print(f"[FAIL] Configuration file not found: {cfg_path}")
        sys.exit(1)
    with open(cfg_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if not isinstance(cfg, dict):
        print("[FAIL] Configuration file parsed to non-dict object.")
        sys.exit(1)
    return cfg


# ---------------------------------------------------------------------------
# Main Candidate Red Zone Identification Routine
# ---------------------------------------------------------------------------

def identify_candidate_red_zones() -> bool:
    print(_sep("="))
    print("  SIH26191 -- STEP 7: CANDIDATE HAZARD-BASED RED ZONE GENERATION")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    all_passed = True
    cfg = load_config()

    # Retrieve configuration sections
    redzones_cfg   = cfg.get("redzones", {})
    multihazard_cfg= cfg.get("multihazard", {})
    paths_cfg      = cfg.get("paths", {})
    terminology_cfg= cfg.get("terminology", {})
    crs_cfg        = cfg.get("crs", {})

    expected_crs_str = crs_cfg.get("analysis_crs_metric", "EPSG:32644")

    # 1. Resolve Input Paths
    inputs_cfg = redzones_cfg.get("inputs", {})
    class_rel  = inputs_cfg.get("multihazard_classes", paths_cfg.get("multihazard_classes", "data/processed/hazards/multihazard_classes.tif"))
    score_rel  = inputs_cfg.get("multihazard_score", paths_cfg.get("multihazard_score", "data/processed/hazards/multihazard_score.tif"))
    terr_rel   = inputs_cfg.get("terrain_contribution", paths_cfg.get("terrain_contribution", "data/processed/hazards/terrain_contribution.tif"))
    flood_rel  = inputs_cfg.get("flood_contribution", paths_cfg.get("flood_contribution", "data/processed/hazards/flood_contribution.tif"))

    class_path = _ROOT_DIR / class_rel
    score_path = _ROOT_DIR / score_rel
    terr_path  = _ROOT_DIR / terr_rel
    flood_path = _ROOT_DIR / flood_rel

    # 2. Resolve Output Paths
    outputs_cfg = redzones_cfg.get("outputs", {})
    gpkg_rel    = outputs_cfg.get("output_vector", paths_cfg.get("redzones_gpkg", "data/outputs/candidate_hazard_based_red_zones.gpkg"))
    geojson_rel = outputs_cfg.get("output_geojson", paths_cfg.get("redzones_geojson", "data/outputs/candidate_hazard_based_red_zones.geojson"))
    raster_rel  = outputs_cfg.get("output_raster", paths_cfg.get("redzones_raster", "data/processed/hazards/candidate_redzone_raster.tif"))

    gpkg_path    = _ROOT_DIR / gpkg_rel
    geojson_path = _ROOT_DIR / geojson_rel
    raster_path  = _ROOT_DIR / raster_rel

    # Ensure output parent directories exist
    gpkg_path.parent.mkdir(parents=True, exist_ok=True)
    geojson_path.parent.mkdir(parents=True, exist_ok=True)
    raster_path.parent.mkdir(parents=True, exist_ok=True)

    # 3. Parameters
    seg_cfg      = redzones_cfg.get("segmentation", {})
    source_class = int(seg_cfg.get("source_class", 3))
    connectivity = int(seg_cfg.get("connectivity", 8))
    id_format    = seg_cfg.get("id_format", "RZ-{:03d}")

    filt_cfg     = redzones_cfg.get("filtering", {})
    min_area_m2  = float(filt_cfg.get("minimum_zone_area_m2", 5000.0))

    labels_cfg   = redzones_cfg.get("labels", {})
    zone_label   = labels_cfg.get("zone_label", terminology_cfg.get("hazard_zone_label", "Candidate Hazard-Based Red Zone"))
    src_indicator= labels_cfg.get("source_indicator", "Higher Multi-Hazard Indicator")
    methodology  = labels_cfg.get("methodology", "Deterministic terrain and hydrology screening")
    disclaimer   = labels_cfg.get("disclaimer", terminology_cfg.get("decision_support_disclaimer", "Decision Support — Requires Official Verification & Geotechnical Assessment"))

    rank_cfg     = redzones_cfg.get("priority_ranking", {})
    priority_basis = rank_cfg.get("basis_description", "Mean multi-hazard score, then maximum score, then area")

    _section("1. Configuration Summary")
    _field("Source Class Code", f"{source_class} ({src_indicator})")
    _field("Connectivity Method", f"{connectivity}-neighbour")
    _field("Minimum Mapping Unit (MMU)", f"{min_area_m2:,.1f} m2 ({min_area_m2 / 10000.0:.2f} ha)")
    _field("Output GeoPackage", str(gpkg_rel))
    _field("Output GeoJSON", str(geojson_rel))
    _field("Output Raster Mask", str(raster_rel))
    _field("Target Analysis CRS", expected_crs_str)

    # -----------------------------------------------------------------------
    _section("2. Input Datasets Loading & Verification")
    # -----------------------------------------------------------------------
    for name, p in [("Multi-hazard classes", class_path),
                    ("Multi-hazard score", score_path),
                    ("Terrain contribution", terr_path),
                    ("Flood contribution", flood_path)]:
        ok_exists = p.is_file()
        all_passed &= _result(f"Input file exists: {name}", ok_exists, str(p))
        if not ok_exists:
            print(f"[FAIL] Missing critical input: {p}")
            return False

    with rasterio.open(class_path) as ds_class, \
         rasterio.open(score_path) as ds_score, \
         rasterio.open(terr_path)  as ds_terr,  \
         rasterio.open(flood_path) as ds_flood:

        profile   = ds_class.profile
        transform = ds_class.transform
        crs       = ds_class.crs
        res_x     = abs(transform.a)
        res_y     = abs(transform.e)
        px_area   = res_x * res_y

        class_arr = ds_class.read(1)
        score_arr = ds_score.read(1)
        terr_arr  = ds_terr.read(1)
        flood_arr = ds_flood.read(1)

        _field("Grid Dimensions", f"{class_arr.shape[1]} x {class_arr.shape[0]} px")
        _field("Pixel Resolution", f"{res_x:.4f} m x {res_y:.4f} m")
        _field("Unit Pixel Area", f"{px_area:.4f} m2")
        _field("Analysis CRS", str(crs))

        # -------------------------------------------------------------------
        _section("3. Binary Mask & Connected Components Labeling")
        # -------------------------------------------------------------------
        source_mask = (class_arr == source_class)
        total_source_pixels = int(np.count_nonzero(source_mask))
        _field(f"Total Source Pixels (Class {source_class})", f"{total_source_pixels:,}")

        if total_source_pixels == 0:
            print(f"[FAIL] No pixels found matching source class {source_class}!")
            return False

        # Structuring element for connectivity
        if connectivity == 8:
            structure = np.ones((3, 3), dtype=int)
        elif connectivity == 4:
            structure = np.array([[0, 1, 0],
                                  [1, 1, 1],
                                  [0, 1, 0]], dtype=int)
        else:
            raise ValueError(f"Unsupported connectivity: {connectivity}. Must be 4 or 8.")

        labeled_arr, num_initial_regions = ndi.label(source_mask, structure=structure)
        _field("Initial Contiguous Regions Count", f"{num_initial_regions:,}")

        # -------------------------------------------------------------------
        _section("4. Minimum Mapping Unit (MMU) Filtering")
        # -------------------------------------------------------------------
        # Compute size (pixel count) of each component 1..num_initial_regions
        component_sizes = ndi.sum(source_mask, labeled_arr, range(1, num_initial_regions + 1))
        component_areas_m2 = component_sizes * px_area

        # Find components meeting MMU threshold
        retained_comp_ids = np.where(component_areas_m2 >= min_area_m2)[0] + 1  # 1-based IDs
        retained_set = set(retained_comp_ids)
        retained_count = len(retained_comp_ids)
        removed_count  = num_initial_regions - retained_count

        total_source_area_ha   = (total_source_pixels * px_area) / 10000.0
        retained_source_area_ha= float(np.sum(component_areas_m2[component_areas_m2 >= min_area_m2])) / 10000.0
        removed_source_area_ha = total_source_area_ha - retained_source_area_ha

        _field("Initial Contiguous Regions", f"{num_initial_regions:,}")
        _field("Filtered (Removed) Small Regions", f"{removed_count:,} ({removed_source_area_ha:.2f} ha)")
        _field("Retained Candidate Red Zones", f"{retained_count:,} ({retained_source_area_ha:.2f} ha)")

        all_passed &= _result("Candidate zones retained after MMU filtering", retained_count > 0, f"{retained_count} zones")

        # -------------------------------------------------------------------
        _section("5. Zonal Attribution & Polygon Extraction")
        # -------------------------------------------------------------------
        print(f"  Vectorizing and calculating zonal statistics for {retained_count} candidate zones...")

        # Create retained labeled raster for single-pass vectorization
        retained_mask = np.isin(labeled_arr, retained_comp_ids)
        retained_labeled = np.where(retained_mask, labeled_arr, 0).astype(np.int32)

        # Single-pass shape extraction
        shapes_gen = rasterio.features.shapes(retained_labeled, mask=retained_mask, transform=transform)
        geoms_by_id = {}
        for shape_geom, shape_val in shapes_gen:
            cid = int(shape_val)
            poly = sg.shape(shape_geom)
            if not poly.is_valid:
                poly = poly.buffer(0)
            if cid not in geoms_by_id:
                geoms_by_id[cid] = []
            geoms_by_id[cid].append(poly)

        # Bounding box slices for fast per-component statistics
        obj_slices = ndi.find_objects(labeled_arr)

        zone_records = []
        for comp_id in retained_comp_ids:
            cid = int(comp_id)
            comp_slice = obj_slices[cid - 1]
            sub_labeled = labeled_arr[comp_slice]
            sub_mask = (sub_labeled == cid)

            comp_px_count = int(np.count_nonzero(sub_mask))
            comp_area_m2  = float(comp_px_count * px_area)
            comp_area_ha  = float(comp_area_m2 / 10000.0)

            # Sub-array raster values
            comp_scores = score_arr[comp_slice][sub_mask]
            comp_terr   = terr_arr[comp_slice][sub_mask]
            comp_flood  = flood_arr[comp_slice][sub_mask]

            mean_score = float(np.nanmean(comp_scores))
            max_score  = float(np.nanmax(comp_scores))
            min_score  = float(np.nanmin(comp_scores))

            mean_terr  = float(np.nanmean(comp_terr))
            mean_flood = float(np.nanmean(comp_flood))

            # Assemble polygon geometry
            comp_geoms = geoms_by_id.get(cid, [])
            if len(comp_geoms) == 1:
                final_geom = comp_geoms[0]
            elif len(comp_geoms) > 1:
                final_geom = so.unary_union(comp_geoms)
            else:
                print(f"[WARN] No polygon geometry found for component {cid}")
                continue

            if not final_geom.is_valid:
                final_geom = final_geom.buffer(0)

            zone_records.append({
                "orig_comp_id": cid,
                "geometry": final_geom,
                "pixel_count": comp_px_count,
                "area_m2": round(comp_area_m2, 2),
                "area_hectares": round(comp_area_ha, 4),
                "mean_multihazard_score": round(mean_score, 6),
                "max_multihazard_score": round(max_score, 6),
                "min_multihazard_score": round(min_score, 6),
                "terrain_contribution_mean": round(mean_terr, 6),
                "flood_contribution_mean": round(mean_flood, 6),
                "source_class": source_class,
                "source_indicator": src_indicator,
                "zone_label": zone_label,
                "methodology": methodology,
                "disclaimer": disclaimer,
            })

        # -------------------------------------------------------------------
        _section("6. Deterministic Priority Ranking")
        # -------------------------------------------------------------------
        # Sort records deterministically:
        # 1. mean_multihazard_score DESCENDING
        # 2. max_multihazard_score DESCENDING
        # 3. area_m2 DESCENDING
        # 4. orig_comp_id ASCENDING (deterministic tie-breaker)
        zone_records.sort(
            key=lambda r: (
                -r["mean_multihazard_score"],
                -r["max_multihazard_score"],
                -r["area_m2"],
                r["orig_comp_id"]
            )
        )

        filtered_raster = np.zeros_like(labeled_arr, dtype=np.uint16)

        for rank_idx, record in enumerate(zone_records, start=1):
            record["candidate_priority_rank"] = rank_idx
            record["zone_id"] = id_format.format(rank_idx)
            record["candidate_priority_basis"] = priority_basis

            # Paint rank on filtered raster output
            comp_id = record["orig_comp_id"]
            comp_slice = obj_slices[comp_id - 1]
            sub_labeled = labeled_arr[comp_slice]
            sub_filt = filtered_raster[comp_slice]
            sub_filt[sub_labeled == comp_id] = rank_idx

        _field("Deterministic Priority Ranks Assigned", f"1 to {len(zone_records)}")
        _field("Priority Ranking Basis", priority_basis)

        # -------------------------------------------------------------------
        _section("7. Vector Creation & GeoPackage / GeoJSON Export")
        # -------------------------------------------------------------------
        # Build GeoDataFrame
        gdf = gpd.GeoDataFrame(zone_records, crs=crs, geometry="geometry")

        # Drop internal temporary column
        if "orig_comp_id" in gdf.columns:
            gdf = gdf.drop(columns=["orig_comp_id"])

        # Reorder columns logically
        ordered_cols = [
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
        gdf = gdf[ordered_cols]

        # Write GeoPackage
        print(f"  Writing GeoPackage to: {gpkg_path.relative_to(_ROOT_DIR)}...")
        gdf.to_file(gpkg_path, layer="candidate_hazard_based_red_zones", driver="GPKG")
        ok_gpkg = gpkg_path.is_file() and gpkg_path.stat().st_size > 0
        all_passed &= _result(f"GeoPackage exported successfully ({gpkg_path.stat().st_size / 1024:.1f} KB)", ok_gpkg)

        # Write GeoJSON
        print(f"  Writing GeoJSON to: {geojson_path.relative_to(_ROOT_DIR)}...")
        gdf.to_file(geojson_path, driver="GeoJSON")
        ok_geojson = geojson_path.is_file() and geojson_path.stat().st_size > 0
        all_passed &= _result(f"GeoJSON exported successfully ({geojson_path.stat().st_size / 1024:.1f} KB)", ok_geojson)

        # -------------------------------------------------------------------
        _section("8. Filtered Candidate Zone Raster Mask Export")
        # -------------------------------------------------------------------
        print(f"  Writing raster mask to: {raster_path.relative_to(_ROOT_DIR)}...")
        raster_profile = profile.copy()
        raster_profile.update({
            "dtype": "uint16",
            "nodata": 0,
            "count": 1,
            "compress": "lzw"
        })
        with rasterio.open(raster_path, "w", **raster_profile) as dst:
            dst.write(filtered_raster, 1)

        ok_raster = raster_path.is_file() and raster_path.stat().st_size > 0
        all_passed &= _result(f"Candidate Red Zone raster exported ({raster_path.stat().st_size / 1024:.1f} KB)", ok_raster)

        # -------------------------------------------------------------------
        _section("9. Candidate Red Zone Statistical Overview")
        # -------------------------------------------------------------------
        top_zone = zone_records[0]
        smallest_zone = min(zone_records, key=lambda r: r["area_m2"])
        largest_zone  = max(zone_records, key=lambda r: r["area_m2"])
        mean_area_m2  = float(np.mean([r["area_m2"] for r in zone_records]))
        mean_area_ha  = float(mean_area_m2 / 10000.0)

        _field("Total Candidate Zones Generated", f"{len(zone_records):,}")
        _field("Total Candidate Zone Area", f"{retained_source_area_ha:.2f} ha ({retained_source_area_ha * 10000.0:,.0f} m2)")
        _field("Mean Candidate Zone Area", f"{mean_area_ha:.2f} ha ({mean_area_m2:,.1f} m2)")
        _field("Largest Candidate Zone", f"{largest_zone['zone_id']} ({largest_zone['area_hectares']:.2f} ha, Mean Score: {largest_zone['mean_multihazard_score']:.4f})")
        _field("Smallest Retained Candidate Zone", f"{smallest_zone['zone_id']} ({smallest_zone['area_hectares']:.2f} ha, {smallest_zone['area_m2']:,.0f} m2)")
        _field("Highest Priority Candidate Zone", f"{top_zone['zone_id']} (Rank #{top_zone['candidate_priority_rank']}, Mean Score: {top_zone['mean_multihazard_score']:.4f}, Max: {top_zone['max_multihazard_score']:.4f})")

    # -----------------------------------------------------------------------
    _section("Execution Result")
    # -----------------------------------------------------------------------
    status_str = "PASS" if all_passed else "FAIL"
    print(f"\nCANDIDATE HAZARD-BASED RED ZONE GENERATION: {status_str}")
    return all_passed


if __name__ == "__main__":
    success = identify_candidate_red_zones()
    sys.exit(0 if success else 1)
