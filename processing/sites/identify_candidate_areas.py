#!/usr/bin/env python3
"""
SIH26191 -- Step 9: Candidate Topographically Feasible Area Identification
===========================================================================
Identifies Candidate Topographically Feasible Areas using deterministic
terrain-based screening of verified Step 3--7 raster outputs.

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

MANDATORY DISCLAIMER
--------------------
All outputs are PRELIMINARY DECISION-SUPPORT CANDIDATES REQUIRING FIELD
VERIFICATION. They do NOT constitute:
  - Official site authorizations
  - Engineering-certified safe locations
  - Government relocation approvals
  - Safety certifications of any kind
Geotechnical and infrastructure assessment is required before any relocation action.

PIPELINE STRUCTURE
------------------
Step 9A -- Topographic & Hazard Exclusion Masks
    D1 : Exclude Multi-Hazard Class 3 pixels           [DETERMINISTIC]
    D2 : Exclude Flood Exposure Class 3 pixels         [DETERMINISTIC]
    D3 : Exclude Step-7 Candidate Red Zone pixels      [DETERMINISTIC]
    D4 : Exclude NoData pixels                         [DETERMINISTIC]
    C1 : Slope maximum threshold exclusion             [CONFIGURABLE -- null=SKIP]
    C2 : Red zone buffer zone exclusion                [CONFIGURABLE -- null=SKIP]
    C3 : Moderate Flood Exposure Class 2 exclusion     [CONFIGURABLE -- null=SKIP]
    C4 : Moderate Multi-Hazard Class 2 exclusion       [CONFIGURABLE -- null=SKIP]
    C5 : Elevation maximum cap exclusion               [CONFIGURABLE -- null=SKIP]
    OUTPUT: combined_exclusion_mask.tif

Step 9B -- Candidate Area Extraction
    Connected component labeling (8-connectivity)
    Area calculation per cluster
    MMU filtering                                      [CONFIGURABLE -- null=SKIP]
    Vectorization (rasterio.features.shapes)
    Deterministic ID assignment (CA-0001, CA-0002, ...)
    OUTPUT: candidate_topographically_feasible_areas_base.gpkg/.geojson
            candidate_area_raster.tif
            candidate_areas_metadata.json

Step 9C -- Optional Context Attribution
    Habitation demographics pre-check (Census linkage verification)
    Zonal statistics (slope, terrain susceptibility, flood proxy, MH score)
    Proximity to nearest Candidate Hazard-Based Red Zone boundary
    Proximity to nearest habitation centroid + demographic context
    OUTPUT: candidate_topographically_feasible_areas_attributed.gpkg/.geojson
    NOTE: Step 9B base outputs are NEVER modified or overwritten.

USAGE
-----
    python processing/sites/identify_candidate_areas.py

All parameters are loaded from configs/project.yaml -- candidate_areas section.
"""

import sys
import io
import json
import math
import datetime
import pathlib
import warnings
from typing import Dict, Any, Optional, Tuple

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# ---------------------------------------------------------------------------
# Project root resolution
# ---------------------------------------------------------------------------
_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent          # processing/sites/
_ROOT = _SCRIPT_DIR.parent.parent                              # project root
_CONFIG_PATH = _ROOT / "configs" / "project.yaml"

# ---------------------------------------------------------------------------
# Dependency imports
# ---------------------------------------------------------------------------
try:
    import yaml
except ImportError:
    print("[FATAL] PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

try:
    import numpy as np
    import scipy.ndimage as ndi
    import rasterio
    import rasterio.features
    from rasterio.crs import CRS
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    import shapely.geometry as sg
    import geopandas as gpd
except ImportError as exc:
    print(f"[FATAL] Required geospatial package missing: {exc}")
    sys.exit(1)

try:
    import rasterstats
except ImportError:
    print("[FATAL] rasterstats not installed. Run: pip install rasterstats")
    sys.exit(1)

warnings.filterwarnings("ignore", category=UserWarning)

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
DISCLAIMER = (
    "Preliminary decision-support candidate requiring field verification. "
    "Not an official site authorization or safety certification. "
    "Geotechnical and infrastructure assessment required before any relocation action."
)

def _log(msg: str) -> None:
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)

def _skip(param: str) -> None:
    _log(f"[SKIP] {param}: NOT CONFIGURED -- screening step omitted.")

def _warn(msg: str) -> None:
    _log(f"[WARN] {msg}")

def _section(title: str) -> None:
    bar = "=" * 70
    print(f"\n{bar}\n  {title}\n{bar}", flush=True)

# ---------------------------------------------------------------------------
# Config loading
# ---------------------------------------------------------------------------
def load_config() -> Dict[str, Any]:
    if not _CONFIG_PATH.exists():
        print(f"[FATAL] Config not found: {_CONFIG_PATH}")
        sys.exit(1)
    with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    if "candidate_areas" not in cfg:
        print("[FATAL] 'candidate_areas' section missing from project.yaml")
        sys.exit(1)
    if not cfg["candidate_areas"].get("enabled", False):
        print("[FATAL] candidate_areas.enabled is false in project.yaml")
        sys.exit(1)
    return cfg

# ---------------------------------------------------------------------------
# Input validation
# ---------------------------------------------------------------------------
REQUIRED_INPUTS = {
    "multihazard_classes":         "data/processed/hazards/multihazard_classes.tif",
    "flood_exposure_classes":      "data/processed/hazards/flood_exposure_classes.tif",
    "candidate_redzone_raster":    "data/processed/hazards/candidate_redzone_raster.tif",
    "slope_degrees":               "data/processed/terrain/slope_degrees.tif",
    "multihazard_score":           "data/processed/hazards/multihazard_score.tif",
    "terrain_susceptibility_proxy":"data/processed/hazards/terrain_susceptibility_proxy.tif",
    "flood_exposure_proxy":        "data/processed/hazards/flood_exposure_proxy.tif",
}
OPTIONAL_INPUTS = {
    "dem_raw":              "data/raw/copernicus_glo30_rudraprayag.tif",
    "candidate_redzones":   "data/outputs/candidate_hazard_based_red_zones.gpkg",
    "habitation_exposure":  "data/processed/exposure/habitation_exposure.geojson",
}

def validate_inputs() -> Tuple[Dict[str, pathlib.Path], Dict[str, Optional[pathlib.Path]]]:
    _log("Validating required input files...")
    required = {}
    for name, rel in REQUIRED_INPUTS.items():
        p = _ROOT / rel
        if not p.exists():
            print(f"[FATAL] Required input missing: {p}")
            sys.exit(1)
        required[name] = p
        _log(f"  [OK] {name}: {rel}")

    optional = {}
    for name, rel in OPTIONAL_INPUTS.items():
        p = _ROOT / rel
        if p.exists():
            optional[name] = p
            _log(f"  [OK] {name}: {rel}")
        else:
            optional[name] = None
            _warn(f"Optional input not found: {rel} -- dependent step will be skipped.")
    return required, optional

# ---------------------------------------------------------------------------
# Habitation demographics pre-check (Step 9C prerequisite)
# ---------------------------------------------------------------------------
def check_habitation_demographics(exposure_path: Optional[pathlib.Path]) -> Tuple[bool, str]:
    """
    Verifies that population fields in habitation_exposure.geojson originate
    from the validated Census 2011 PCA dataset joined via exact integer code match.

    Returns (has_validated_demographics: bool, message: str)
    """
    _section("HABITATION DEMOGRAPHICS PRE-CHECK")
    if exposure_path is None:
        msg = "DEMOGRAPHIC_ATTRIBUTION_UNAVAILABLE: habitation_exposure.geojson not found."
        _log(msg)
        return False, msg

    try:
        gdf = gpd.read_file(str(exposure_path))
    except Exception as exc:
        msg = f"DEMOGRAPHIC_ATTRIBUTION_UNAVAILABLE: Could not read habitation_exposure: {exc}"
        _log(msg)
        return False, msg

    # Verify authoritative join method
    if "join_method" not in gdf.columns or "tot_pop" not in gdf.columns:
        msg = "DEMOGRAPHIC_ATTRIBUTION_UNAVAILABLE: Required fields (join_method, tot_pop) absent."
        _log(msg)
        return False, msg

    join_methods = gdf["join_method"].dropna().unique()
    if len(join_methods) == 0:
        msg = "DEMOGRAPHIC_ATTRIBUTION_UNAVAILABLE: join_method field is entirely null."
        _log(msg)
        return False, msg

    join_method = join_methods[0]
    _log(f"  join_method  : {join_method}")
    _log(f"  data_source  : {gdf['data_source'].iloc[0] if 'data_source' in gdf.columns else 'N/A'}")

    # Must be code-based (not fuzzy or name-based)
    is_code_based = "Exact code-based join" in join_method
    pop_nulls = int(gdf["tot_pop"].isnull().sum())
    pop_sum = int(gdf["tot_pop"].sum())
    census_total = 232360  # Verified in Step 8B.2 documentation

    _log(f"  tot_pop nulls: {pop_nulls}")
    _log(f"  tot_pop sum  : {pop_sum:,} (expected: {census_total:,})")
    _log(f"  Census match : {pop_sum == census_total}")

    if is_code_based and pop_nulls == 0 and pop_sum == census_total:
        msg = "DEMOGRAPHIC_ATTRIBUTION_AVAILABLE: Exact code-based Census 2011 PCA join confirmed."
        _log(f"  DECISION: {msg}")
        _log("  nearest_village_pop WILL BE INCLUDED in Step 9C attribution.")
        return True, msg
    else:
        reasons = []
        if not is_code_based:
            reasons.append("join is not code-based")
        if pop_nulls > 0:
            reasons.append(f"{pop_nulls} null population values")
        if pop_sum != census_total:
            reasons.append(f"sum mismatch ({pop_sum} vs {census_total})")
        msg = f"DEMOGRAPHIC_ATTRIBUTION_UNAVAILABLE: {'; '.join(reasons)}."
        _log(f"  DECISION: {msg}")
        _log("  nearest_village_pop will be null.")
        return False, msg

# ---------------------------------------------------------------------------
# Step 9A: Topographic & Hazard Exclusion Masks
# ---------------------------------------------------------------------------
def run_9a_exclusion_masks(
    cfg: Dict[str, Any],
    required: Dict[str, pathlib.Path],
    optional: Dict[str, Optional[pathlib.Path]],
) -> Tuple[np.ndarray, np.ndarray, Any, Any, Dict[str, Any], Dict[str, str]]:
    """
    Builds the combined exclusion mask from deterministic + configurable criteria.

    Returns
    -------
    combined_exclusion_mask : ndarray bool  (True = excluded)
    candidate_mask          : ndarray bool  (True = candidate terrain)
    transform               : rasterio Affine
    crs                     : rasterio CRS
    meta                    : dict (rasterio metadata for writing)
    param_log               : dict mapping parameter names to 'APPLIED' / 'NOT_CONFIGURED'
    """
    _section("STEP 9A: TOPOGRAPHIC + HAZARD EXCLUSION MASKS")
    ca_cfg = cfg["candidate_areas"]
    det = ca_cfg["deterministic_exclusions"]
    cscr = ca_cfg["configurable_screening"]
    param_log: Dict[str, str] = {}

    # Open the reference raster (slope) for grid metadata
    with rasterio.open(str(required["slope_degrees"])) as src:
        ref_transform = src.transform
        ref_crs = src.crs
        ref_shape = src.shape
        ref_meta = src.meta.copy()
        slope = src.read(1)
        slope_nodata = src.nodata  # NaN for float32

    pixel_size_m = abs(ref_transform[0])  # 29.1058 m
    pixel_area_m2 = pixel_size_m ** 2
    _log(f"Reference grid: {ref_shape} | CRS: {ref_crs} | pixel: {pixel_size_m:.4f} m | area: {pixel_area_m2:.2f} m2")

    # ------------------------------------------------------------------
    # Load classification rasters
    # ------------------------------------------------------------------
    with rasterio.open(str(required["multihazard_classes"])) as src:
        mh_classes = src.read(1)        # uint8: 1/2/3/255
        mh_nodata = src.nodata          # 255

    with rasterio.open(str(required["flood_exposure_classes"])) as src:
        flood_classes = src.read(1)     # uint8: 1/2/3/255
        flood_nodata = src.nodata       # 255

    with rasterio.open(str(required["candidate_redzone_raster"])) as src:
        redzone_raster = src.read(1)    # uint16: 0=background, 1..N=zone_id

    # ------------------------------------------------------------------
    # D1: MH Class 3 exclusion [DETERMINISTIC]
    # ------------------------------------------------------------------
    if det.get("exclude_mh_class_3", True):
        mask_mh3 = (mh_classes == 3)
        px = int(mask_mh3.sum())
        _log(f"  [D1] MH Class 3 excluded : {px:,} px ({px * pixel_area_m2 / 10000:.1f} ha) [DETERMINISTIC]")
        param_log["exclude_mh_class_3"] = f"APPLIED: {px} pixels excluded"
    else:
        mask_mh3 = np.zeros(ref_shape, dtype=bool)
        param_log["exclude_mh_class_3"] = "DISABLED in config (unusual)"

    # ------------------------------------------------------------------
    # D2: Flood Class 3 exclusion [DETERMINISTIC]
    # ------------------------------------------------------------------
    if det.get("exclude_flood_class_3", True):
        mask_flood3 = (flood_classes == 3)
        px = int(mask_flood3.sum())
        _log(f"  [D2] Flood Class 3 excluded: {px:,} px ({px * pixel_area_m2 / 10000:.1f} ha) [DETERMINISTIC]")
        param_log["exclude_flood_class_3"] = f"APPLIED: {px} pixels excluded"
    else:
        mask_flood3 = np.zeros(ref_shape, dtype=bool)
        param_log["exclude_flood_class_3"] = "DISABLED in config (unusual)"

    # ------------------------------------------------------------------
    # D3: Red zone pixel exclusion [DETERMINISTIC]
    # ------------------------------------------------------------------
    if det.get("exclude_redzone_pixels", True):
        mask_rz = (redzone_raster != 0)
        px = int(mask_rz.sum())
        _log(f"  [D3] Red zone pixels excluded: {px:,} px ({px * pixel_area_m2 / 10000:.1f} ha) [DETERMINISTIC]")
        param_log["exclude_redzone_pixels"] = f"APPLIED: {px} pixels excluded"
    else:
        mask_rz = np.zeros(ref_shape, dtype=bool)
        param_log["exclude_redzone_pixels"] = "DISABLED in config (unusual)"

    # ------------------------------------------------------------------
    # D4: NoData exclusion [DETERMINISTIC]
    # ------------------------------------------------------------------
    if det.get("exclude_nodata", True):
        nodata_slope = ~np.isfinite(slope)
        nodata_mh = (mh_classes == 255) if mh_nodata is not None else np.zeros(ref_shape, dtype=bool)
        nodata_flood = (flood_classes == 255) if flood_nodata is not None else np.zeros(ref_shape, dtype=bool)
        mask_nodata = nodata_slope | nodata_mh | nodata_flood
        px = int(mask_nodata.sum())
        _log(f"  [D4] NoData excluded: {px:,} px [DETERMINISTIC]")
        param_log["exclude_nodata"] = f"APPLIED: {px} pixels excluded"
    else:
        mask_nodata = np.zeros(ref_shape, dtype=bool)
        param_log["exclude_nodata"] = "DISABLED in config (unusual)"

    # ------------------------------------------------------------------
    # C1: Slope maximum threshold [CONFIGURABLE]
    # ------------------------------------------------------------------
    slope_max = cscr.get("slope_max_deg", None)
    if slope_max is None:
        _skip("slope_max_deg")
        mask_slope = np.zeros(ref_shape, dtype=bool)
        param_log["slope_max_deg"] = "NOT_CONFIGURED"
    else:
        slope_max = float(slope_max)
        mask_slope = np.isfinite(slope) & (slope > slope_max)
        px = int(mask_slope.sum())
        _log(f"  [C1] Slope > {slope_max} deg excluded: {px:,} px ({px * pixel_area_m2 / 10000:.1f} ha) [APPLIED]")
        param_log["slope_max_deg"] = f"APPLIED: {slope_max} deg, {px} pixels excluded"

    # ------------------------------------------------------------------
    # C2: Red zone buffer [CONFIGURABLE]
    # ------------------------------------------------------------------
    buffer_m = cscr.get("redzone_buffer_m", None)
    if buffer_m is None:
        _skip("redzone_buffer_m")
        mask_rz_buffer = np.zeros(ref_shape, dtype=bool)
        param_log["redzone_buffer_m"] = "NOT_CONFIGURED"
    else:
        buffer_m = float(buffer_m)
        pixel_radius = int(math.ceil(buffer_m / pixel_size_m))
        _log(f"  [C2] Red zone buffer: {buffer_m} m -> {pixel_radius} pixel radius [APPLIED]")
        struct = ndi.generate_binary_structure(2, 1)  # 4-connectivity for dilation
        dilated = ndi.binary_dilation(mask_rz, structure=struct, iterations=pixel_radius)
        mask_rz_buffer = dilated & ~mask_rz  # Only the additional buffer pixels
        px = int(mask_rz_buffer.sum())
        _log(f"       Additional {px:,} px ({px * pixel_area_m2 / 10000:.1f} ha) from buffer")
        param_log["redzone_buffer_m"] = f"APPLIED: {buffer_m} m, {px} additional pixels excluded"

    # ------------------------------------------------------------------
    # C3: Flood Class 2 exclusion [CONFIGURABLE]
    # ------------------------------------------------------------------
    excl_flood2 = cscr.get("exclude_flood_class_2", None)
    if excl_flood2 is None:
        _skip("exclude_flood_class_2")
        mask_flood2 = np.zeros(ref_shape, dtype=bool)
        param_log["exclude_flood_class_2"] = "NOT_CONFIGURED"
    elif excl_flood2 is True:
        mask_flood2 = (flood_classes == 2)
        px = int(mask_flood2.sum())
        _log(f"  [C3] Flood Class 2 excluded: {px:,} px ({px * pixel_area_m2 / 10000:.1f} ha) [APPLIED]")
        param_log["exclude_flood_class_2"] = f"APPLIED: {px} pixels excluded"
    else:
        mask_flood2 = np.zeros(ref_shape, dtype=bool)
        param_log["exclude_flood_class_2"] = "CONFIGURED_FALSE"

    # ------------------------------------------------------------------
    # C4: MH Class 2 exclusion [CONFIGURABLE]
    # ------------------------------------------------------------------
    excl_mh2 = cscr.get("exclude_mh_class_2", None)
    if excl_mh2 is None:
        _skip("exclude_mh_class_2")
        mask_mh2 = np.zeros(ref_shape, dtype=bool)
        param_log["exclude_mh_class_2"] = "NOT_CONFIGURED"
    elif excl_mh2 is True:
        mask_mh2 = (mh_classes == 2)
        px = int(mask_mh2.sum())
        _log(f"  [C4] MH Class 2 excluded: {px:,} px ({px * pixel_area_m2 / 10000:.1f} ha) [APPLIED]")
        param_log["exclude_mh_class_2"] = f"APPLIED: {px} pixels excluded"
    else:
        mask_mh2 = np.zeros(ref_shape, dtype=bool)
        param_log["exclude_mh_class_2"] = "CONFIGURED_FALSE"

    # ------------------------------------------------------------------
    # C5: Elevation cap [CONFIGURABLE]
    # ------------------------------------------------------------------
    elev_max = cscr.get("elevation_max_m", None)
    if elev_max is None:
        _skip("elevation_max_m")
        mask_elev = np.zeros(ref_shape, dtype=bool)
        param_log["elevation_max_m"] = "NOT_CONFIGURED"
    else:
        elev_max = float(elev_max)
        dem_path = optional.get("dem_raw")
        if dem_path is None:
            _warn("elevation_max_m configured but DEM raw file not found. Elevation exclusion skipped.")
            mask_elev = np.zeros(ref_shape, dtype=bool)
            param_log["elevation_max_m"] = f"NOT_APPLIED: DEM raw file missing"
        else:
            _log(f"  [C5] Elevation cap: {elev_max} m -- reprojecting DEM in-memory...")
            with rasterio.open(str(dem_path)) as dem_src:
                new_transform, new_width, new_height = calculate_default_transform(
                    dem_src.crs, ref_crs, dem_src.width, dem_src.height, *dem_src.bounds
                )
                dem_reproj = np.zeros(ref_shape, dtype=np.float32)
                reproject(
                    source=rasterio.band(dem_src, 1),
                    destination=dem_reproj,
                    src_transform=dem_src.transform,
                    src_crs=dem_src.crs,
                    dst_transform=ref_transform,
                    dst_crs=ref_crs,
                    resampling=Resampling.bilinear,
                )
            mask_elev = np.isfinite(dem_reproj) & (dem_reproj > elev_max)
            px = int(mask_elev.sum())
            _log(f"       Elevation > {elev_max} m excluded: {px:,} px ({px * pixel_area_m2 / 10000:.1f} ha) [APPLIED]")
            param_log["elevation_max_m"] = f"APPLIED: {elev_max} m, {px} pixels excluded"

    # ------------------------------------------------------------------
    # Combined mask
    # ------------------------------------------------------------------
    combined_exclusion = (
        mask_mh3 | mask_flood3 | mask_rz | mask_nodata |
        mask_slope | mask_rz_buffer | mask_flood2 | mask_mh2 | mask_elev
    )
    candidate_mask = ~combined_exclusion

    total_px = int(np.prod(ref_shape))
    excl_px = int(combined_exclusion.sum())
    cand_px = int(candidate_mask.sum())
    cand_ha = cand_px * pixel_area_m2 / 10000

    _log(f"\n  Combined exclusion summary:")
    _log(f"    Total pixels    : {total_px:,}")
    _log(f"    Excluded pixels : {excl_px:,} ({100.0 * excl_px / total_px:.1f}%)")
    _log(f"    Candidate pixels: {cand_px:,} ({100.0 * cand_px / total_px:.1f}%) = {cand_ha:,.0f} ha")

    # ------------------------------------------------------------------
    # Write combined_exclusion_mask.tif
    # ------------------------------------------------------------------
    excl_out = _ROOT / cfg["candidate_areas"]["outputs"]["exclusion_mask"]
    excl_out.parent.mkdir(parents=True, exist_ok=True)

    excl_meta = ref_meta.copy()
    excl_meta.update({"dtype": "uint8", "nodata": 255, "count": 1, "compress": "lzw"})
    excl_arr = combined_exclusion.astype(np.uint8)
    excl_arr[mask_nodata] = 255  # Mark original NoData cells as 255

    with rasterio.open(str(excl_out), "w", **excl_meta) as dst:
        dst.write(excl_arr, 1)
    _log(f"\n  [9A OUTPUT] {excl_out.relative_to(_ROOT)}")

    return (
        combined_exclusion,
        candidate_mask,
        ref_transform,
        ref_crs,
        ref_meta,
        pixel_area_m2,
        param_log,
    )

# ---------------------------------------------------------------------------
# Step 9B: Candidate Area Extraction
# ---------------------------------------------------------------------------
def run_9b_candidate_extraction(
    cfg: Dict[str, Any],
    candidate_mask: np.ndarray,
    transform: Any,
    crs: Any,
    ref_meta: Dict,
    pixel_area_m2: float,
    param_log: Dict[str, str],
) -> Tuple[gpd.GeoDataFrame, int]:
    """
    Extracts contiguous candidate areas, assigns IDs, and writes base outputs.

    Returns (candidate_gdf, num_retained_features)
    """
    _section("STEP 9B: CANDIDATE AREA EXTRACTION")
    ca_cfg = cfg["candidate_areas"]
    seg = ca_cfg["segmentation"]
    id_fmt = seg.get("id_format", "CA-{:04d}")
    connectivity = seg.get("connectivity", 8)
    mmu = ca_cfg["filtering"].get("minimum_area_m2", None)

    # ------------------------------------------------------------------
    # Connected component labeling
    # ------------------------------------------------------------------
    _log(f"Running connected component labeling ({connectivity}-connectivity)...")
    if connectivity == 8:
        struct = np.ones((3, 3), dtype=np.int32)
    else:
        struct = ndi.generate_binary_structure(2, 1)

    labeled_array, num_features = ndi.label(candidate_mask, structure=struct)
    _log(f"  Raw clusters found: {num_features:,}")

    if num_features == 0:
        _warn("No candidate terrain found after exclusion. Check exclusion parameters.")
        return gpd.GeoDataFrame(geometry=[], crs=crs), 0

    # ------------------------------------------------------------------
    # Area per cluster
    # ------------------------------------------------------------------
    _log("Computing area per cluster...")
    label_vals, counts = np.unique(labeled_array[labeled_array > 0], return_counts=True)
    areas_m2 = counts.astype(np.float64) * pixel_area_m2

    # ------------------------------------------------------------------
    # MMU filtering [CONFIGURABLE]
    # ------------------------------------------------------------------
    if mmu is None:
        _skip("minimum_area_m2")
        param_log["minimum_area_m2"] = "NOT_CONFIGURED"
        retained_labels = label_vals
        retained_areas = areas_m2
        retained_counts = counts
        _log(f"  Clusters retained (no MMU filter): {len(retained_labels):,}")
    else:
        mmu = float(mmu)
        keep_mask = areas_m2 >= mmu
        retained_labels = label_vals[keep_mask]
        retained_areas = areas_m2[keep_mask]
        retained_counts = counts[keep_mask]
        dropped = int((~keep_mask).sum())
        _log(f"  MMU filter: {mmu:,.0f} m2 -> dropped {dropped:,} clusters, retained {len(retained_labels):,}")
        param_log["minimum_area_m2"] = f"APPLIED: {mmu} m2, {dropped} clusters dropped"

        # Update labeled array: set dropped labels to 0
        drop_set = set(label_vals[~keep_mask].tolist())
        if drop_set:
            drop_mask = np.isin(labeled_array, list(drop_set))
            labeled_array[drop_mask] = 0

    num_retained = len(retained_labels)
    _log(f"  Retained candidate areas: {num_retained:,}")

    if num_retained == 0:
        _warn("All clusters dropped by MMU filter. Lower minimum_area_m2 or set to null.")
        return gpd.GeoDataFrame(geometry=[], crs=crs), 0

    if num_retained > 5000:
        _warn(f"Large number of clusters ({num_retained:,}). Without MMU filtering, many tiny "
              f"pixel-level clusters are included. Consider setting minimum_area_m2.")

    # ------------------------------------------------------------------
    # Sort by area descending (largest candidate areas first)
    # ------------------------------------------------------------------
    sort_idx = np.argsort(-retained_areas)
    retained_labels = retained_labels[sort_idx]
    retained_areas = retained_areas[sort_idx]
    retained_counts = retained_counts[sort_idx]

    # Build lookup: old_label -> (new_id, area, pixel_count)
    label_to_info: Dict[int, Dict] = {}
    for rank, (lbl, area, pc) in enumerate(zip(retained_labels, retained_areas, retained_counts), start=1):
        label_to_info[int(lbl)] = {
            "area_id":       id_fmt.format(rank),
            "area_m2":       float(area),
            "area_hectares": float(area / 10000.0),
            "pixel_count":   int(pc),
            "rank":          rank,
        }

    # ------------------------------------------------------------------
    # Vectorization: rasterio.features.shapes on the labeled array
    # ------------------------------------------------------------------
    # NOTE: rasterio.features.shapes emits individual polygon RINGS for each
    # contiguous sub-region of the same pixel value, including separate rings for
    # holes (excluded pixels interior to a cluster). For large candidate terrain
    # with many internal holes, one cluster label may produce hundreds of rings.
    # Approach: collect ALL ring geometries per label, then unary_union per label
    # to form one correct (Multi)Polygon. Area is taken from pixel counts
    # (already computed), NOT from polygon geometry, to avoid double-counting.
    # ------------------------------------------------------------------
    _log("Vectorizing candidate areas (collecting rings per cluster, then unioning)...")
    try:
        from shapely.ops import unary_union
    except ImportError:
        from shapely.ops import cascaded_union as unary_union  # shapely <2.0 fallback

    valid_label_set = set(retained_labels.tolist())
    candidate_uint8 = candidate_mask.astype(np.uint8)
    labeled_int32 = labeled_array.astype(np.int32)

    # Pass 1: collect all ring geometries per label
    label_geoms: Dict[int, list] = {int(lbl): [] for lbl in retained_labels}
    ring_total = 0
    for geom_dict, value in rasterio.features.shapes(
        labeled_int32,
        mask=candidate_uint8,
        transform=transform
    ):
        lbl_val = int(value)
        if lbl_val not in valid_label_set:
            continue
        label_geoms[lbl_val].append(sg.shape(geom_dict))
        ring_total += 1
    _log(f"  Collected {ring_total} ring geometries for {len(label_geoms)} clusters. Unioning...")

    # Pass 2: union per cluster into one (Multi)Polygon
    records = []
    for lbl_val in retained_labels:
        rings = label_geoms.get(int(lbl_val), [])
        if not rings:
            _warn(f"  Cluster {lbl_val}: no geometries collected -- skipped.")
            continue
        merged = rings[0] if len(rings) == 1 else unary_union(rings)
        info = label_to_info[int(lbl_val)]
        records.append({
            "area_id":       info["area_id"],
            "area_label":    ca_cfg["labels"]["area_label"],
            # Pixel-count-derived area is authoritative; polygon area is NOT used.
            "area_m2":       info["area_m2"],
            "area_hectares": info["area_hectares"],
            "pixel_count":   info["pixel_count"],
            "geometry":      merged,
        })

    if not records:
        _warn("Vectorization produced no records. This is unexpected.")
        return gpd.GeoDataFrame(geometry=[], crs=crs), 0

    # ------------------------------------------------------------------
    # Build GeoDataFrame
    # ------------------------------------------------------------------
    _log(f"Building GeoDataFrame from {len(records):,} vectorized features...")
    gdf = gpd.GeoDataFrame(records, crs=crs)

    # Build screening_basis string
    det = cfg["candidate_areas"]["deterministic_exclusions"]
    basis_parts = [
        f"exclude_mh_class_3={det.get('exclude_mh_class_3', True)}",
        f"exclude_flood_class_3={det.get('exclude_flood_class_3', True)}",
        f"exclude_redzone_pixels={det.get('exclude_redzone_pixels', True)}",
        f"exclude_nodata={det.get('exclude_nodata', True)}",
        f"slope_max_deg={param_log.get('slope_max_deg','NOT_CONFIGURED')}",
        f"redzone_buffer_m={param_log.get('redzone_buffer_m','NOT_CONFIGURED')}",
        f"exclude_flood_class_2={param_log.get('exclude_flood_class_2','NOT_CONFIGURED')}",
        f"exclude_mh_class_2={param_log.get('exclude_mh_class_2','NOT_CONFIGURED')}",
        f"elevation_max_m={param_log.get('elevation_max_m','NOT_CONFIGURED')}",
        f"minimum_area_m2={param_log.get('minimum_area_m2','NOT_CONFIGURED')}",
    ]
    screening_basis = "; ".join(basis_parts)
    gdf["screening_basis"] = screening_basis
    gdf["methodology"] = ca_cfg["labels"]["methodology"]
    gdf["disclaimer"] = ca_cfg["labels"]["disclaimer"]

    total_ha = float(gdf["area_hectares"].sum())
    _log(f"\n  STEP 9B SUMMARY:")
    _log(f"    Features retained : {len(gdf):,}")
    _log(f"    Total area        : {total_ha:,.1f} ha")
    _log(f"    Largest area      : {float(gdf['area_m2'].max()):,.0f} m2 ({float(gdf['area_hectares'].max()):,.1f} ha)")
    _log(f"    Smallest area     : {float(gdf['area_m2'].min()):,.0f} m2")

    # ------------------------------------------------------------------
    # Write candidate_area_raster.tif
    # ------------------------------------------------------------------
    raster_out = _ROOT / ca_cfg["outputs"]["area_raster"]
    raster_out.parent.mkdir(parents=True, exist_ok=True)
    raster_meta = ref_meta.copy()
    raster_meta.update({"dtype": "uint32", "nodata": 0, "count": 1, "compress": "lzw"})
    with rasterio.open(str(raster_out), "w", **raster_meta) as dst:
        dst.write(labeled_array.astype(np.uint32), 1)
    _log(f"\n  [9B OUTPUT] {raster_out.relative_to(_ROOT)}")

    # ------------------------------------------------------------------
    # Write base vector outputs (GeoPackage + GeoJSON)
    # ------------------------------------------------------------------
    base_gpkg = _ROOT / ca_cfg["outputs"]["base_gpkg"]
    base_gpkg.parent.mkdir(parents=True, exist_ok=True)
    base_geojson = _ROOT / ca_cfg["outputs"]["base_geojson"]

    # GeoPackage
    gdf.to_file(str(base_gpkg), driver="GPKG", layer="candidate_topographically_feasible_areas")
    _log(f"  [9B OUTPUT] {base_gpkg.relative_to(_ROOT)}")

    # GeoJSON (reproject to EPSG:4326 for storage CRS compliance if needed — keep EPSG:32644 per project convention)
    gdf.to_file(str(base_geojson), driver="GeoJSON")
    _log(f"  [9B OUTPUT] {base_geojson.relative_to(_ROOT)}")

    return gdf, num_retained

# ---------------------------------------------------------------------------
# Step 9C: Optional Context Attribution
# ---------------------------------------------------------------------------
def run_9c_attribution(
    cfg: Dict[str, Any],
    base_gdf: gpd.GeoDataFrame,
    required: Dict[str, pathlib.Path],
    optional: Dict[str, Optional[pathlib.Path]],
    has_demographics: bool,
    demog_message: str,
) -> Optional[gpd.GeoDataFrame]:
    """
    Appends zonal statistics and proximity attribution to base candidate areas.
    Writes to SEPARATE attributed output files (never overwrites 9B base).

    Returns attributed_gdf or None if attribution not possible.
    """
    _section("STEP 9C: OPTIONAL CONTEXT ATTRIBUTION")
    ca_cfg = cfg["candidate_areas"]

    if base_gdf is None or len(base_gdf) == 0:
        _warn("Step 9B produced no candidate areas. Step 9C skipped.")
        return None

    # Deep copy to ensure base_gdf is never mutated
    att_gdf = base_gdf.copy()

    # ------------------------------------------------------------------
    # 9C-1: Zonal statistics (rasterstats)
    # ------------------------------------------------------------------
    _log("9C-1: Computing zonal statistics per candidate area...")
    zonal_rasters = {
        "slope":                   required["slope_degrees"],
        "terrain_susceptibility":  required["terrain_susceptibility_proxy"],
        "flood_exposure_proxy":    required["flood_exposure_proxy"],
        "multihazard_score":       required["multihazard_score"],
    }
    for field_prefix, raster_path in zonal_rasters.items():
        try:
            stats = rasterstats.zonal_stats(
                vectors=att_gdf.geometry,
                raster=str(raster_path),
                stats=["mean", "max", "min"],
                nodata=float("nan"),
            )
            att_gdf[f"mean_{field_prefix}"] = [
                round(s["mean"], 4) if s["mean"] is not None else None for s in stats
            ]
            att_gdf[f"max_{field_prefix}"] = [
                round(s["max"], 4) if s["max"] is not None else None for s in stats
            ]
            att_gdf[f"min_{field_prefix}"] = [
                round(s["min"], 4) if s["min"] is not None else None for s in stats
            ]
            _log(f"  [OK] {field_prefix}: mean/max/min computed for {len(att_gdf)} features")
        except Exception as exc:
            _warn(f"Zonal stats failed for {field_prefix}: {exc}")
            for suffix in ("mean", "max", "min"):
                att_gdf[f"{suffix}_{field_prefix}"] = None

    # ------------------------------------------------------------------
    # 9C-2: Proximity to nearest Candidate Red Zone
    # ------------------------------------------------------------------
    _log("9C-2: Computing proximity to nearest Candidate Hazard-Based Red Zone...")
    rz_path = optional.get("candidate_redzones")
    if rz_path is None:
        _warn("Candidate red zones file not found. dist_to_nearest_redzone_m = null.")
        att_gdf["dist_to_nearest_redzone_m"] = None
        att_gdf["nearest_redzone_id"] = None
    else:
        try:
            rz_gdf = gpd.read_file(str(rz_path))
            if rz_gdf.crs != att_gdf.crs:
                rz_gdf = rz_gdf.to_crs(att_gdf.crs)

            # Compute centroid of each candidate area for distance calc
            cand_centroids = att_gdf.copy()
            cand_centroids["geometry"] = att_gdf.geometry.centroid

            # sjoin_nearest: returns distance from centroid to nearest rz polygon boundary
            joined = gpd.sjoin_nearest(
                cand_centroids[["area_id", "geometry"]],
                rz_gdf[["zone_id", "geometry"]],
                how="left",
                distance_col="dist_to_nearest_redzone_m",
            )
            # Handle possible duplicates from sjoin_nearest
            joined = joined.drop_duplicates(subset=["area_id"], keep="first")
            joined = joined.set_index("area_id")

            att_gdf["dist_to_nearest_redzone_m"] = att_gdf["area_id"].map(
                joined["dist_to_nearest_redzone_m"]
            ).round(1)
            att_gdf["nearest_redzone_id"] = att_gdf["area_id"].map(
                joined["zone_id"]
            )
            valid_dists = att_gdf["dist_to_nearest_redzone_m"].dropna()
            _log(f"  [OK] Red zone proximity: min={float(valid_dists.min()):.1f} m, "
                 f"max={float(valid_dists.max()):.1f} m, mean={float(valid_dists.mean()):.1f} m")
        except Exception as exc:
            _warn(f"Red zone proximity failed: {exc}")
            att_gdf["dist_to_nearest_redzone_m"] = None
            att_gdf["nearest_redzone_id"] = None

    # ------------------------------------------------------------------
    # 9C-3: Proximity to habitation centroids
    # ------------------------------------------------------------------
    _log("9C-3: Computing proximity to habitation centroids...")
    hab_path = optional.get("habitation_exposure")
    if hab_path is None:
        _warn("habitation_exposure.geojson not found. Habitation proximity skipped.")
        att_gdf["nearest_habitation_m"] = None
        att_gdf["nearest_village_name"] = None
        att_gdf["nearest_village_id"] = None
        att_gdf["nearest_village_pop"] = None
    else:
        try:
            hab_gdf = gpd.read_file(str(hab_path))
            if hab_gdf.crs != att_gdf.crs:
                hab_gdf = hab_gdf.to_crs(att_gdf.crs)

            cand_centroids = att_gdf.copy()
            cand_centroids["geometry"] = att_gdf.geometry.centroid

            # Columns to carry from habitation dataset
            hab_cols = ["village_id", "village_name", "geometry"]
            if has_demographics and "tot_pop" in hab_gdf.columns:
                hab_cols.append("tot_pop")

            joined_hab = gpd.sjoin_nearest(
                cand_centroids[["area_id", "geometry"]],
                hab_gdf[hab_cols],
                how="left",
                distance_col="nearest_habitation_m",
            )
            joined_hab = joined_hab.drop_duplicates(subset=["area_id"], keep="first")
            joined_hab = joined_hab.set_index("area_id")

            att_gdf["nearest_habitation_m"] = att_gdf["area_id"].map(
                joined_hab["nearest_habitation_m"]
            ).round(1)
            att_gdf["nearest_village_name"] = att_gdf["area_id"].map(
                joined_hab["village_name"]
            )
            att_gdf["nearest_village_id"] = att_gdf["area_id"].map(
                joined_hab["village_id"]
            )

            if has_demographics and "tot_pop" in joined_hab.columns:
                att_gdf["nearest_village_pop"] = att_gdf["area_id"].map(
                    joined_hab["tot_pop"]
                ).astype("Int64")
                _log(f"  [OK] nearest_village_pop INCLUDED (Census PCA 2011 - authoritative)")
            else:
                att_gdf["nearest_village_pop"] = None
                _log(f"  [SKIP] nearest_village_pop = null. Reason: {demog_message}")

            valid_dists = att_gdf["nearest_habitation_m"].dropna()
            _log(f"  [OK] Habitation proximity: min={float(valid_dists.min()):.1f} m, "
                 f"max={float(valid_dists.max()):.1f} m, mean={float(valid_dists.mean()):.1f} m")
        except Exception as exc:
            _warn(f"Habitation proximity failed: {exc}")
            att_gdf["nearest_habitation_m"] = None
            att_gdf["nearest_village_name"] = None
            att_gdf["nearest_village_id"] = None
            att_gdf["nearest_village_pop"] = None

    # ------------------------------------------------------------------
    # Write attributed outputs (SEPARATE from 9B base)
    # ------------------------------------------------------------------
    att_gpkg = _ROOT / ca_cfg["outputs"]["attributed_gpkg"]
    att_geojson = _ROOT / ca_cfg["outputs"]["attributed_geojson"]
    att_gpkg.parent.mkdir(parents=True, exist_ok=True)

    att_gdf.to_file(str(att_gpkg), driver="GPKG", layer="candidate_topographically_feasible_areas_attributed")
    _log(f"\n  [9C OUTPUT] {att_gpkg.relative_to(_ROOT)}")

    att_gdf.to_file(str(att_geojson), driver="GeoJSON")
    _log(f"  [9C OUTPUT] {att_geojson.relative_to(_ROOT)}")

    return att_gdf

# ---------------------------------------------------------------------------
# Metadata JSON
# ---------------------------------------------------------------------------
def write_metadata(
    cfg: Dict[str, Any],
    param_log: Dict[str, str],
    base_gdf: gpd.GeoDataFrame,
    att_gdf: Optional[gpd.GeoDataFrame],
    has_demographics: bool,
    demog_message: str,
    pixel_area_m2: float,
    elapsed_s: float,
) -> None:
    ca_cfg = cfg["candidate_areas"]
    meta_path = _ROOT / ca_cfg["outputs"]["metadata_json"]
    meta_path.parent.mkdir(parents=True, exist_ok=True)

    base_count = len(base_gdf) if base_gdf is not None else 0
    base_area_ha = float(base_gdf["area_hectares"].sum()) if base_count > 0 else 0.0

    metadata = {
        "project": "SIH26191",
        "step": "Step 9 -- Candidate Topographically Feasible Area Identification",
        "pilot_district": "Rudraprayag, Uttarakhand, India",
        "generated_utc": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "methodology_version": ca_cfg.get("methodology_version", "1.0"),
        "crs": "EPSG:32644",
        "pixel_area_m2": round(pixel_area_m2, 4),
        "pipeline_phases": {
            "9A_exclusion_masks": "completed",
            "9B_candidate_extraction": "completed" if base_count > 0 else "no_features",
            "9C_attribution": "completed" if att_gdf is not None else "skipped_or_no_features",
        },
        "applied_parameters": param_log,
        "habitation_demographics": {
            "status": "AVAILABLE" if has_demographics else "UNAVAILABLE",
            "message": demog_message,
            "nearest_village_pop_included": has_demographics,
        },
        "outputs": {
            "base_features": base_count,
            "base_total_area_ha": round(base_area_ha, 2),
            "attributed_features": len(att_gdf) if att_gdf is not None else 0,
            "files": {
                "exclusion_mask":    str((_ROOT / ca_cfg["outputs"]["exclusion_mask"]).relative_to(_ROOT)),
                "area_raster":       str((_ROOT / ca_cfg["outputs"]["area_raster"]).relative_to(_ROOT)),
                "base_gpkg":         str((_ROOT / ca_cfg["outputs"]["base_gpkg"]).relative_to(_ROOT)),
                "base_geojson":      str((_ROOT / ca_cfg["outputs"]["base_geojson"]).relative_to(_ROOT)),
                "attributed_gpkg":   str((_ROOT / ca_cfg["outputs"]["attributed_gpkg"]).relative_to(_ROOT)),
                "attributed_geojson":str((_ROOT / ca_cfg["outputs"]["attributed_geojson"]).relative_to(_ROOT)),
            },
        },
        "inputs_used": {k: v for k, v in REQUIRED_INPUTS.items()},
        "disclaimer": ca_cfg["labels"]["disclaimer"],
        "processing_time_seconds": round(elapsed_s, 2),
    }

    with open(str(meta_path), "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    _log(f"  [META] {meta_path.relative_to(_ROOT)}")

# ---------------------------------------------------------------------------
# Step 9 Report
# ---------------------------------------------------------------------------
def generate_report(
    cfg: Dict[str, Any],
    param_log: Dict[str, str],
    base_gdf: gpd.GeoDataFrame,
    att_gdf: Optional[gpd.GeoDataFrame],
    has_demographics: bool,
    demog_message: str,
    pixel_area_m2: float,
) -> None:
    _section("GENERATING STEP 9 REPORT")
    report_path = _ROOT / "docs" / "step9_candidate_areas_report.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)

    ca_cfg = cfg["candidate_areas"]
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    base_count = len(base_gdf) if base_gdf is not None else 0
    base_ha = float(base_gdf["area_hectares"].sum()) if base_count > 0 else 0.0
    max_ha = float(base_gdf["area_hectares"].max()) if base_count > 0 else 0.0
    min_m2 = float(base_gdf["area_m2"].min()) if base_count > 0 else 0.0

    # Build parameter table rows
    param_rows = ""
    for k, v in param_log.items():
        status = "NOT_CONFIGURED" if v == "NOT_CONFIGURED" else ("APPLIED" if "APPLIED" in v else v)
        param_rows += f"| `{k}` | {v} | {status} |\n"

    lines = [
        "# Step 9 \u2014 Candidate Topographically Feasible Area Identification Report",
        "",
        f"**Generated (UTC):** {timestamp}  ",
        f"**Project:** SIH26191 \u2014 Rudraprayag District, Uttarakhand  ",
        f"**Pipeline Version:** {ca_cfg.get('methodology_version', '1.0')}  ",
        f"**Status:** DECISION SUPPORT SCREENING OUTPUT \u2014 Requires Official Verification",
        "",
        "---",
        "",
        "## 1. Mandatory Decision-Support Disclaimer",
        "",
        "> **MANDATORY DISCLAIMER**",
        ">",
        "> " + ca_cfg["labels"]["disclaimer"].replace("\n", " "),
        "",
        "---",
        "",
        "## 2. Executive Summary",
        "",
        f"Step 9 applied a deterministic terrain-based screening pipeline to identify",
        f"**Candidate Topographically Feasible Areas** across Rudraprayag District.",
        f"All configurable screening parameters were set to `null` (NOT CONFIGURED) and",
        f"were explicitly skipped. Only deterministic exclusions based on the verified",
        f"Step 4\u20137 pipeline outputs were applied.",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Candidate area features (9B base) | **{base_count:,}** |",
        f"| Total candidate terrain area | **{base_ha:,.1f} ha** |",
        f"| Largest single candidate area | **{max_ha:,.1f} ha** |",
        f"| Smallest single candidate area | **{min_m2:,.0f} m\u00b2** |",
        f"| Pixel area | {pixel_area_m2:.2f} m\u00b2 (29.11 m \u00d7 29.11 m) |",
        f"| CRS | EPSG:32644 (WGS 84 / UTM Zone 44N) |",
        f"| Step 9C attribution | {'Completed' if att_gdf is not None else 'Not run'} |",
        f"| Demographic attribution | {'AVAILABLE (Census PCA 2011)' if has_demographics else 'UNAVAILABLE'} |",
        "",
        "---",
        "",
        "## 3. Applied vs Skipped Screening Parameters",
        "",
        "| Parameter | Value / Status | Classification |",
        "|-----------|---------------|----------------|",
        param_rows.rstrip(),
        "",
        "---",
        "",
        "## 4. Deterministic Exclusions Applied",
        "",
        "The following exclusions were always applied regardless of configurable parameters:",
        "",
        "| Exclusion | Basis | Source Layer |",
        "|-----------|-------|-------------|",
        "| Multi-Hazard Class 3 (Higher) | Internally consistent with Step 7 red zone generation | `multihazard_classes.tif` |",
        "| Flood Exposure Class 3 (Higher) | TWI \u2265 10.0 (valley bottoms, drainage confluences) | `flood_exposure_classes.tif` |",
        "| Step 7 Candidate Red Zone pixels | Pixels already in candidate hazard-based red zones | `candidate_redzone_raster.tif` |",
        "| NoData pixels | Any pixel where required inputs have NoData | All required rasters |",
        "",
        "---",
        "",
        "## 5. Habitation Demographics Check",
        "",
        f"**Status:** `{demog_message}`  ",
        f"**nearest_village_pop included:** {'Yes' if has_demographics else 'No (null)'}  ",
        "",
        "The habitation dataset (`habitation_exposure.geojson`) was inspected before Step 9C.",
        "Geometry source: SHRUG v2.2 spatial centroids (Development Data Lab).",
        "Join method: Exact integer code match (Census Town/Village = SHRUG pc11_village_id).",
        "Village centroid points represent administrative reference locations, NOT building footprints.",
        "Proximity calculations are centroid-to-centroid Euclidean distances in EPSG:32644.",
        "",
        "---",
        "",
        "## 6. Output Files",
        "",
        "| File | Step | Purpose |",
        "|------|------|---------|",
        f"| `data/processed/sites/combined_exclusion_mask.tif` | 9A | Combined exclusion mask (0=candidate, 1=excluded, 255=NoData) |",
        f"| `data/processed/sites/candidate_area_raster.tif` | 9B | Labeled cluster raster (cluster_id per pixel, 0=background) |",
        f"| `data/outputs/candidate_topographically_feasible_areas_base.gpkg` | 9B | Base vector output (no attribution) |",
        f"| `data/outputs/candidate_topographically_feasible_areas_base.geojson` | 9B | Base GeoJSON |",
        f"| `data/outputs/candidate_topographically_feasible_areas_attributed.gpkg` | 9C | Attributed vector (zonal stats + proximity) |",
        f"| `data/outputs/candidate_topographically_feasible_areas_attributed.geojson` | 9C | Attributed GeoJSON |",
        f"| `data/outputs/candidate_areas_metadata.json` | 9A-9C | Processing metadata and parameter log |",
        f"| `docs/step9_candidate_areas_report.md` | 9A-9C | This report |",
        "",
        "---",
        "",
        "## 7. Major Limitations",
        "",
        "1. **No slope screening applied** (`slope_max_deg = null`). All slope gradients that are not excluded by MH/Flood Class 3 remain as candidate terrain. Field surveys must assess actual slope suitability.",
        "2. **No road accessibility screening** (roads dataset not acquired). Candidate areas may be topographically suitable but logistically inaccessible.",
        "3. **No LULC / forest exclusion** (dataset not acquired). Candidate areas may include forest land, protected areas, or agricultural land.",
        "4. **No river buffer exclusion** (river network dataset not acquired). TWI-based flood Class 3 exclusion is a partial proxy only.",
        "5. **No minimum mapping unit filter** (`minimum_area_m2 = null`). All contiguous clusters are retained including very small areas potentially unsuitable for habitation.",
        "6. **30 m DEM resolution** limits spatial precision. Candidate area boundaries are indicative at approximately 30 m scale.",
        "7. **Village centroids are administrative reference points**, not building footprints. Proximity distances are Euclidean, not routable path distances.",
        "8. **This output does NOT replace field surveys**, geotechnical assessment, legal land-use review, or government authorization.",
        "",
        "---",
        "",
        "*This report is a decision-support output of the SIH26191 GIS pipeline.*",
        "*Official administrative action requires verification by competent geotechnical*",
        "*and disaster management authorities.*",
    ]

    with open(str(report_path), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    _log(f"  [REPORT] {report_path.relative_to(_ROOT)}")

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    t0 = datetime.datetime.now()
    _section("SIH26191 -- STEP 9: CANDIDATE TOPOGRAPHICALLY FEASIBLE AREA IDENTIFICATION")
    _log("MANDATORY DISCLAIMER: All outputs are preliminary decision-support candidates")
    _log("requiring field verification. Not official authorizations or safety certifications.")

    # 1. Load config and validate inputs
    cfg = load_config()
    required, optional = validate_inputs()

    # 2. Habitation demographics pre-check (for Step 9C)
    has_demographics, demog_message = check_habitation_demographics(
        optional.get("habitation_exposure")
    )

    # 3. Step 9A: Build exclusion masks
    (
        combined_exclusion,
        candidate_mask,
        transform,
        crs,
        ref_meta,
        pixel_area_m2,
        param_log,
    ) = run_9a_exclusion_masks(cfg, required, optional)

    # 4. Step 9B: Extract candidate areas (base outputs)
    base_gdf, num_retained = run_9b_candidate_extraction(
        cfg, candidate_mask, transform, crs, ref_meta, pixel_area_m2, param_log
    )

    # 5. Step 9C: Attribution (attributed outputs — never overwrites 9B)
    att_gdf = None
    if num_retained > 0:
        att_gdf = run_9c_attribution(
            cfg, base_gdf, required, optional, has_demographics, demog_message
        )
    else:
        _warn("Step 9C skipped: no candidate areas produced by Step 9B.")

    # 6. Metadata JSON
    elapsed = (datetime.datetime.now() - t0).total_seconds()
    write_metadata(
        cfg, param_log, base_gdf, att_gdf,
        has_demographics, demog_message, pixel_area_m2, elapsed
    )

    # 7. Report
    generate_report(
        cfg, param_log, base_gdf, att_gdf,
        has_demographics, demog_message, pixel_area_m2
    )

    # 8. Final summary
    _section("STEP 9 COMPLETE")
    base_count = len(base_gdf) if base_gdf is not None else 0
    base_ha = float(base_gdf["area_hectares"].sum()) if base_count > 0 else 0.0
    _log(f"Candidate areas (9B base): {base_count:,}")
    _log(f"Total candidate terrain  : {base_ha:,.1f} ha")
    _log(f"Step 9C attribution      : {'completed' if att_gdf is not None else 'skipped'}")
    _log(f"Processing time          : {elapsed:.1f} s")
    _log(f"\nAll outputs are PRELIMINARY DECISION-SUPPORT CANDIDATES.")
    _log(f"DISCLAIMER: {DISCLAIMER}")


if __name__ == "__main__":
    main()
