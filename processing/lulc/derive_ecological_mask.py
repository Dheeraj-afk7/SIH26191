#!/usr/bin/env python3
"""
SIH26191 -- Phase 1: LULC & Ecological Exclusion Mask Derivation
=================================================================

Pilot Area: Rudraprayag District, Uttarakhand, India
Project: SIH26191

Processes the raw 10m ESA WorldCover 2021 v200 raster and official Kedarnath
Wildlife Sanctuary boundary to produce aligned 30m metric GIS layers:

1. data/processed/lulc/rudraprayag_worldcover_30m.tif
   - 30m raster aligned exactly to terrain grid (EPSG:32644, shape 2458x1854)
   - Preserves discrete integer ESA WorldCover class codes:
       10: Tree cover
       20: Shrubland
       30: Grassland
       40: Cropland
       50: Built-up
       60: Bare / sparse vegetation
       70: Snow and ice
       80: Permanent water bodies
       90: Herbaceous wetland

2. data/processed/lulc/protected_areas_30m.tif
   - Binary raster (1 = Inside Kedarnath Wildlife Sanctuary, 0 = Outside)

3. data/processed/lulc/ecological_exclusion_mask.tif
   - Binary exclusion mask (1 = Excluded from Candidate Relocation Areas, 0 = Permissible)
   - Configured exclusions: Tree cover (10), Built-up (50), Snow/ice (70),
     Water bodies (80), Herbaceous wetland (90), Protected Sanctuary.
   - Permissible classes: Shrubland (20), Grassland (30), Bare soil/rock (60), Cropland (40).

4. data/processed/lulc/lulc_summary.json
   - Zonal pixel counts, hectare area breakdowns, and metadata provenance.
"""

import datetime
import io
import json
import os
import pathlib
import sys
import warnings

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.enums import Resampling
from rasterio.features import rasterize
from rasterio.warp import calculate_default_transform, reproject
import geopandas as gpd
import shapely.geometry as sg
import yaml

# Force UTF-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

warnings.filterwarnings("ignore", category=UserWarning)

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT / "configs" / "project.yaml"
RAW_LULC_DIR = ROOT / "data" / "raw" / "lulc"
PROCESSED_LULC_DIR = ROOT / "data" / "processed" / "lulc"
PROCESSED_LULC_DIR.mkdir(parents=True, exist_ok=True)

REF_SLOPE_PATH = ROOT / "data" / "processed" / "terrain" / "slope_degrees.tif"
RAW_WORLDCOVER_PATH = RAW_LULC_DIR / "ESA_WorldCover_10m_2021_v200_rudraprayag.tif"
if not RAW_WORLDCOVER_PATH.exists():
    RAW_WORLDCOVER_PATH = RAW_LULC_DIR / "ESA_WorldCover_10m_2021_v200_N30E078_Map.tif"
SANCTUARY_PATH = RAW_LULC_DIR / "protected_areas_unep_wcmc.geojson"
if not SANCTUARY_PATH.exists():
    SANCTUARY_PATH = RAW_LULC_DIR / "kedarnath_wildlife_sanctuary.geojson"

OUT_LULC_30M = PROCESSED_LULC_DIR / "rudraprayag_worldcover_30m.tif"
OUT_SANCTUARY_30M = PROCESSED_LULC_DIR / "protected_areas_30m.tif"
OUT_EXCLUSION_MASK = PROCESSED_LULC_DIR / "ecological_exclusion_mask.tif"
OUT_SUMMARY_JSON = PROCESSED_LULC_DIR / "lulc_summary.json"

WORLDCOVER_LEGEND = {
    10: "Tree cover",
    20: "Shrubland",
    30: "Grassland",
    40: "Cropland",
    50: "Built-up",
    60: "Bare / sparse vegetation",
    70: "Snow and ice",
    80: "Permanent water bodies",
    90: "Herbaceous wetland",
    95: "Mangroves",
    100: "Moss and lichen"
}


def log(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def derive_lulc_and_masks():
    print("=" * 72)
    print("  SIH26191: LULC & Ecological Exclusion Mask Processing")
    print("=" * 72)

    # 1. Inspect Reference Raster
    if not REF_SLOPE_PATH.exists():
        log(f"[FATAL] Reference slope raster not found: {REF_SLOPE_PATH}")
        sys.exit(1)

    with rasterio.open(str(REF_SLOPE_PATH)) as ref:
        target_meta = ref.meta.copy()
        target_crs = ref.crs
        target_transform = ref.transform
        target_shape = ref.shape  # (height, width)
        ref_slope = ref.read(1)

    pixel_size_m = abs(target_transform[0])
    pixel_area_m2 = pixel_size_m * pixel_size_m
    pixel_area_ha = pixel_area_m2 / 10000.0
    total_pixels = target_shape[0] * target_shape[1]
    valid_terrain_mask = np.isfinite(ref_slope)
    valid_terrain_pixels = int(valid_terrain_mask.sum())

    log(f"Reference Grid: {target_shape} | CRS: {target_crs} | Pixel: {pixel_size_m:.4f} m ({pixel_area_ha:.4f} ha)")
    log(f"Valid District Terrain Pixels: {valid_terrain_pixels:,} ({valid_terrain_pixels * pixel_area_ha:,.1f} ha)")

    # 2. Ingest and Reproject ESA WorldCover 10m
    if not RAW_WORLDCOVER_PATH.exists():
        log(f"[FATAL] Raw WorldCover TIF missing at {RAW_WORLDCOVER_PATH}")
        sys.exit(1)

    log(f"Reprojecting and resampling ESA WorldCover 10m to 30m target grid (Nearest Neighbour)...")
    with rasterio.open(str(RAW_WORLDCOVER_PATH)) as src:
        log(f"  Source WorldCover Shape: {src.shape} | CRS: {src.crs} | Res: {src.res}")
        lulc_30m = np.zeros(target_shape, dtype=np.uint8)
        reproject(
            source=rasterio.band(src, 1),
            destination=lulc_30m,
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=target_transform,
            dst_crs=target_crs,
            resampling=Resampling.nearest
        )

    # Mask out pixels outside district DEM extent with 0 (NoData)
    lulc_30m[~valid_terrain_mask] = 0

    # Write 30m LULC GeoTIFF
    target_meta.update({
        "driver": "GTiff",
        "dtype": "uint8",
        "nodata": 0,
        "count": 1,
        "compress": "lzw"
    })

    with rasterio.open(str(OUT_LULC_30M), "w", **target_meta) as dst:
        dst.write(lulc_30m, 1)
    log(f"[OUTPUT] Written 30m LULC to {OUT_LULC_30M.name}")

    # 3. Protected Area Layer Handling (Pending Official UKFD Cadastre Release)
    log(f"Evaluating Protected Area Layer...")
    sanctuary_mask = np.zeros(target_shape, dtype=np.uint8)
    sanctuary_status = "PENDING_AUTHORITATIVE_CADASTRE_RELEASE"
    sanctuary_name = "Kedarnath Wildlife Sanctuary (WDPA ID 832)"

    # If an official verified UKFD / WII vector dataset is supplied in the future, rasterize it:
    if SANCTUARY_PATH.exists() and "protected_areas_unep_wcmc" not in str(SANCTUARY_PATH):
        try:
            gdf_sanctuary = gpd.read_file(str(SANCTUARY_PATH))
            if not gdf_sanctuary.empty:
                gdf_sanctuary_proj = gdf_sanctuary.to_crs(target_crs)
                shapes = [(geom, 1) for geom in gdf_sanctuary_proj.geometry if geom is not None and not geom.is_empty]
                if shapes:
                    sanctuary_mask = rasterize(
                        shapes=shapes,
                        out_shape=target_shape,
                        transform=target_transform,
                        fill=0,
                        dtype=np.uint8
                    )
                    sanctuary_status = "APPLIED_FROM_LOCAL_VECTOR"
                    log(f"  Rasterized {len(shapes)} sanctuary polygon(s).")
        except Exception as exc:
            log(f"  [WARN] Failed to rasterize sanctuary: {exc}")
    else:
        log(f"  [STATUS] Protected Area ({sanctuary_name}): {sanctuary_status}")
        log(f"           Nanda Devi Biosphere Reserve was not substituted to preserve strict geographic identity.")

    sanctuary_mask[~valid_terrain_mask] = 0
    sanctuary_pixels = int(sanctuary_mask.sum())
    log(f"  Sanctuary coverage: {sanctuary_pixels:,} px ({sanctuary_pixels * pixel_area_ha:,.1f} ha) [{sanctuary_status}]")

    with rasterio.open(str(OUT_SANCTUARY_30M), "w", **target_meta) as dst:
        dst.write(sanctuary_mask, 1)
    log(f"[OUTPUT] Written Protected Area raster to {OUT_SANCTUARY_30M.name}")

    # 4. Generate Combined Empirical Ecological Exclusion Mask
    # Excluded Classes: Tree Cover (10), Built-up (50), Snow/ice (70), Permanent water bodies (80), Herbaceous wetland (90)
    # Plus Protected Areas if an authoritative cadastre is active.
    log("Building Combined Ecological Exclusion Mask (ESA WorldCover 10m Empirical Base)...")
    mask_tree_cover = (lulc_30m == 10)
    mask_built_up = (lulc_30m == 50)
    mask_snow_ice = (lulc_30m == 70)
    mask_water = (lulc_30m == 80)
    mask_wetland = (lulc_30m == 90)
    mask_sanctuary = (sanctuary_mask == 1)

    combined_exclusion = (
        mask_tree_cover |
        mask_built_up |
        mask_snow_ice |
        mask_water |
        mask_wetland |
        mask_sanctuary
    )
    # Maintain 0 outside district boundary
    combined_exclusion[~valid_terrain_mask] = False

    exclusion_uint8 = np.zeros(target_shape, dtype=np.uint8)
    exclusion_uint8[combined_exclusion] = 1

    with rasterio.open(str(OUT_EXCLUSION_MASK), "w", **target_meta) as dst:
        dst.write(exclusion_uint8, 1)
    log(f"[OUTPUT] Written Ecological Exclusion Mask to {OUT_EXCLUSION_MASK.name}")

    # 5. Class Statistics and Summaries
    log("\nComputing LULC Class Distribution across Rudraprayag District:")
    class_stats = {}
    for code, label in WORLDCOVER_LEGEND.items():
        px_count = int((lulc_30m == code).sum())
        ha_area = float(px_count * pixel_area_ha)
        pct = float(px_count * 100.0 / valid_terrain_pixels) if valid_terrain_pixels > 0 else 0.0
        class_stats[str(code)] = {
            "code": code,
            "label": label,
            "pixel_count": px_count,
            "area_hectares": round(ha_area, 2),
            "percentage_of_district": round(pct, 2),
            "screening_policy": "EXCLUDED" if code in [10, 50, 70, 80, 90] else "PERMISSIBLE"
        }
        if px_count > 0:
            log(f"  Class {code:2d} ({label:26s}): {px_count:7,d} px | {ha_area:10,.2f} ha ({pct:5.2f}%) -> {class_stats[str(code)]['screening_policy']}")

    total_excl_px = int(combined_exclusion.sum())
    total_excl_ha = float(total_excl_px * pixel_area_ha)
    total_excl_pct = float(total_excl_px * 100.0 / valid_terrain_pixels) if valid_terrain_pixels > 0 else 0.0

    permissible_px = valid_terrain_pixels - total_excl_px
    permissible_ha = float(permissible_px * pixel_area_ha)
    permissible_pct = float(permissible_px * 100.0 / valid_terrain_pixels) if valid_terrain_pixels > 0 else 0.0

    log(f"\nSummary Ecological Exclusion:")
    log(f"  Total District Valid Terrain: {valid_terrain_pixels:,} px ({valid_terrain_pixels * pixel_area_ha:,.1f} ha)")
    log(f"  Ecologically Excluded Terrain: {total_excl_px:,} px ({total_excl_ha:,.1f} ha, {total_excl_pct:.2f}%)")
    log(f"  Ecologically Permissible Terrain: {permissible_px:,} px ({permissible_ha:,.1f} ha, {permissible_pct:.2f}%)")

    summary_doc = {
        "project": "SIH26191",
        "pilot_district": "Rudraprayag, Uttarakhand, India",
        "processed_timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "crs": "EPSG:32644 (UTM Zone 44N)",
        "grid_resolution_m": round(pixel_size_m, 4),
        "source_dataset": "ESA WorldCover 10m 2021 v200 (Tile N30E078)",
        "protected_area_layer_status": sanctuary_status,
        "protected_area_intended_target": "Kedarnath Wildlife Sanctuary (WDPA ID 832, 975 km2)",
        "protected_area_status_note": "UNEP-WCMC WDPCA India feature 902492 (Nanda Devi) excluded from substitution to preserve strict geographic identity. Statutory sanctuary boundary remains a pending cadastre layer until official UKFD release.",
        "total_district_area_ha": round(valid_terrain_pixels * pixel_area_ha, 2),
        "ecological_exclusion_ha": round(total_excl_ha, 2),
        "ecological_exclusion_pct": round(total_excl_pct, 2),
        "ecological_permissible_ha": round(permissible_ha, 2),
        "ecological_permissible_pct": round(permissible_pct, 2),
        "classes": class_stats,
        "exclusion_breakdown": {
            "tree_cover_ha": round(int(mask_tree_cover.sum()) * pixel_area_ha, 2),
            "built_up_ha": round(int(mask_built_up.sum()) * pixel_area_ha, 2),
            "snow_ice_ha": round(int(mask_snow_ice.sum()) * pixel_area_ha, 2),
            "water_bodies_ha": round(int(mask_water.sum()) * pixel_area_ha, 2),
            "sanctuary_ha": round(int(mask_sanctuary.sum()) * pixel_area_ha, 2)
        }
    }

    with open(OUT_SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary_doc, f, indent=2)
    log(f"[OUTPUT] Written LULC Summary to {OUT_SUMMARY_JSON.name}")

    print("\n[SUCCESS] LULC & Ecological Exclusion Processing Complete.")


if __name__ == "__main__":
    derive_lulc_and_masks()
