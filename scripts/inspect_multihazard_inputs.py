#!/usr/bin/env python3
"""
SIH26191 -- Step 6A: Multi-Hazard Input Inspection
==============================================================================
Validates the availability, spatial reference, resolution, transform, spatial
bounds, NoData characteristics, and value ranges of the two upstream hazard
screening proxies:
  1. Terrain Susceptibility Proxy (Step 4)
  2. Flood Exposure Proxy (Step 5)

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

MANDATORY RULES
---------------
1. Raw DEM and upstream outputs are STRICTLY READ-ONLY.
2. Configuration is loaded dynamically from configs/project.yaml.
3. No processing artifacts are written during this inspection.
4. Output must terminate with 'MULTI-HAZARD INPUT INSPECTION: PASS / FAIL'.

USAGE
-----
    python scripts/inspect_multihazard_inputs.py
"""

import sys
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
except ImportError as e:
    print(f"[ERROR] Required package not installed: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths and formatting helpers
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_ROOT_DIR   = _SCRIPT_DIR.parent


def _sep(char: str = "=", width: int = 68) -> str:
    return char * width


def _section(title: str) -> None:
    print(f"\n{_sep('-')}")
    print(f"  {title}")
    print(_sep('-'))


def _field(label: str, value, width: int = 34) -> None:
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
    if not isinstance(cfg, dict):
        print("[FAIL] Configuration file parsed to non-dict object.")
        sys.exit(1)
    return cfg


# ---------------------------------------------------------------------------
# Main Inspection Logic
# ---------------------------------------------------------------------------

def inspect_multihazard_inputs() -> bool:
    print(_sep("="))
    print("  SIH26191 -- STEP 6A: MULTI-HAZARD INPUT INSPECTION")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    all_passed = True
    cfg = load_config(_ROOT_DIR)

    # 1. Project & CRS Configuration
    _section("1. CONFIGURATION PARAMETERS")
    project_id = cfg.get("project", {}).get("id", "SIH26191")
    pilot_district = cfg.get("project", {}).get("pilot_district", "Rudraprayag")
    state = cfg.get("project", {}).get("state", "Uttarakhand")

    analysis_crs_str = cfg.get("crs", {}).get("analysis_crs_metric", "EPSG:32644")
    paths_cfg = cfg.get("paths", {})

    terrain_proxy_rel = paths_cfg.get(
        "terrain_susceptibility_proxy",
        "data/processed/hazards/terrain_susceptibility_proxy.tif"
    )
    flood_proxy_rel = paths_cfg.get(
        "flood_exposure_proxy",
        "data/processed/hazards/flood_exposure_proxy.tif"
    )

    terrain_proxy_path = (_ROOT_DIR / terrain_proxy_rel).resolve()
    flood_proxy_path = (_ROOT_DIR / flood_proxy_rel).resolve()

    _field("Project ID", project_id)
    _field("Pilot Region", f"{pilot_district}, {state}")
    _field("Configured Analysis Metric CRS", analysis_crs_str)
    _field("Terrain Susceptibility Proxy Path", str(terrain_proxy_path))
    _field("Flood Exposure Proxy Path", str(flood_proxy_path))

    expected_analysis_crs = CRS.from_string(analysis_crs_str)

    # 2. File Existence & Readability Checks
    _section("2. FILE EXISTENCE & READABILITY")
    
    terrain_exists = terrain_proxy_path.is_file()
    all_passed = _result("Terrain Susceptibility Proxy exists", terrain_exists, str(terrain_proxy_path)) and all_passed

    flood_exists = flood_proxy_path.is_file()
    all_passed = _result("Flood Exposure Proxy exists", flood_exists, str(flood_proxy_path)) and all_passed

    if not (terrain_exists and flood_exists):
        print("\n[ERROR] One or more required multi-hazard input rasters are missing.")
        print("Integration cannot proceed.")
        print(f"\n{_sep('=')}")
        print("MULTI-HAZARD INPUT INSPECTION: FAIL")
        print(_sep('='))
        return False

    # 3. Raster Metadata Inspection
    _section("3. RASTER METADATA INSPECTION")

    try:
        ds_terrain = rasterio.open(terrain_proxy_path)
        ds_flood = rasterio.open(flood_proxy_path)
    except Exception as exc:
        print(f"[FAIL] Error opening input raster datasets: {exc}")
        print(f"\n{_sep('=')}")
        print("MULTI-HAZARD INPUT INSPECTION: FAIL")
        print(_sep('='))
        return False

    # Terrain metadata
    print("\n  --- Terrain Susceptibility Proxy (Step 4) ---")
    _field("Driver", ds_terrain.driver)
    _field("CRS", str(ds_terrain.crs))
    _field("Dimensions (W x H)", f"{ds_terrain.width} x {ds_terrain.height} px")
    _field("Pixel Resolution (X, Y)", f"{ds_terrain.res[0]:.6f} m, {ds_terrain.res[1]:.6f} m")
    _field("Data Type", ds_terrain.dtypes[0])
    _field("NoData Value", str(ds_terrain.nodata))
    _field("Bounding Box Left", f"{ds_terrain.bounds.left:.4f}")
    _field("Bounding Box Bottom", f"{ds_terrain.bounds.bottom:.4f}")
    _field("Bounding Box Right", f"{ds_terrain.bounds.right:.4f}")
    _field("Bounding Box Top", f"{ds_terrain.bounds.top:.4f}")

    # Flood metadata
    print("\n  --- Flood Exposure Proxy (Step 5) ---")
    _field("Driver", ds_flood.driver)
    _field("CRS", str(ds_flood.crs))
    _field("Dimensions (W x H)", f"{ds_flood.width} x {ds_flood.height} px")
    _field("Pixel Resolution (X, Y)", f"{ds_flood.res[0]:.6f} m, {ds_flood.res[1]:.6f} m")
    _field("Data Type", ds_flood.dtypes[0])
    _field("NoData Value", str(ds_flood.nodata))
    _field("Bounding Box Left", f"{ds_flood.bounds.left:.4f}")
    _field("Bounding Box Bottom", f"{ds_flood.bounds.bottom:.4f}")
    _field("Bounding Box Right", f"{ds_flood.bounds.right:.4f}")
    _field("Bounding Box Top", f"{ds_flood.bounds.top:.4f}")

    # 4. Spatial Compatibility Checks
    _section("4. SPATIAL COMPATIBILITY CHECKS")

    # CRS checks
    crs_match_analysis = (ds_terrain.crs == expected_analysis_crs) and (ds_flood.crs == expected_analysis_crs)
    all_passed = _result(
        "Both rasters match configured analysis CRS",
        crs_match_analysis,
        f"Terrain: {ds_terrain.crs}, Flood: {ds_flood.crs}, Target: {expected_analysis_crs}"
    ) and all_passed

    crs_match_each_other = (ds_terrain.crs == ds_flood.crs)
    all_passed = _result(
        "CRS of both input rasters are identical",
        crs_match_each_other,
        f"{ds_terrain.crs} == {ds_flood.crs}"
    ) and all_passed

    # Dimensions check
    dims_match = (ds_terrain.width == ds_flood.width) and (ds_terrain.height == ds_flood.height)
    all_passed = _result(
        "Raster grid dimensions match exactly",
        dims_match,
        f"{ds_terrain.width}x{ds_terrain.height} vs {ds_flood.width}x{ds_flood.height}"
    ) and all_passed

    # Resolution check
    res_match = (
        np.isclose(ds_terrain.res[0], ds_flood.res[0], atol=1e-5) and
        np.isclose(ds_terrain.res[1], ds_flood.res[1], atol=1e-5)
    )
    all_passed = _result(
        "Pixel resolutions match exactly",
        res_match,
        f"({ds_terrain.res[0]:.6f}, {ds_terrain.res[1]:.6f})"
    ) and all_passed

    # Transform check
    transform_match = (ds_terrain.transform == ds_flood.transform)
    all_passed = _result(
        "Affine geotransforms match exactly",
        transform_match,
        f"Terrain={tuple(ds_terrain.transform)[:6]} vs Flood={tuple(ds_flood.transform)[:6]}"
    ) and all_passed

    # Bounds check
    bounds_match = (
        np.isclose(ds_terrain.bounds.left, ds_flood.bounds.left, atol=1e-3) and
        np.isclose(ds_terrain.bounds.bottom, ds_flood.bounds.bottom, atol=1e-3) and
        np.isclose(ds_terrain.bounds.right, ds_flood.bounds.right, atol=1e-3) and
        np.isclose(ds_terrain.bounds.top, ds_flood.bounds.top, atol=1e-3)
    )
    all_passed = _result(
        "Spatial bounding coordinates match exactly",
        bounds_match
    ) and all_passed

    # 5. Data Quality, Mask Compatibility & Value Range Audit
    _section("5. DATA QUALITY, MASK COMPATIBILITY & VALUE RANGES")

    arr_terrain = ds_terrain.read(1)
    arr_flood = ds_flood.read(1)

    ds_terrain.close()
    ds_flood.close()

    total_pixels = arr_terrain.size
    _field("Total Grid Pixels", f"{total_pixels:,}")

    # NoData / Valid Mask Check
    valid_terrain_mask = ~np.isnan(arr_terrain)
    valid_flood_mask = ~np.isnan(arr_flood)

    valid_terrain_count = int(np.sum(valid_terrain_mask))
    valid_flood_count = int(np.sum(valid_flood_mask))

    _field("Valid Terrain Pixels", f"{valid_terrain_count:,} ({valid_terrain_count / total_pixels * 100:.2f}%)")
    _field("Valid Flood Pixels", f"{valid_flood_count:,} ({valid_flood_count / total_pixels * 100:.2f}%)")

    masks_identical = np.array_equal(valid_terrain_mask, valid_flood_mask)
    all_passed = _result(
        "Valid pixel masks are 100% identical",
        masks_identical,
        f"Valid count = {valid_terrain_count:,}"
    ) and all_passed

    # Infinite value check
    inf_terrain_count = int(np.sum(np.isinf(arr_terrain)))
    inf_flood_count = int(np.sum(np.isinf(arr_flood)))
    all_passed = _result(
        "Terrain proxy has zero infinite values",
        inf_terrain_count == 0,
        f"inf_count = {inf_terrain_count}"
    ) and all_passed
    all_passed = _result(
        "Flood proxy has zero infinite values",
        inf_flood_count == 0,
        f"inf_count = {inf_flood_count}"
    ) and all_passed

    # Value Range Checks
    t_min = float(np.nanmin(arr_terrain))
    t_max = float(np.nanmax(arr_terrain))
    t_mean = float(np.nanmean(arr_terrain))
    t_std = float(np.nanstd(arr_terrain))

    f_min = float(np.nanmin(arr_flood))
    f_max = float(np.nanmax(arr_flood))
    f_mean = float(np.nanmean(arr_flood))
    f_std = float(np.nanstd(arr_flood))

    print("\n  --- Value Range Statistics ---")
    _field("Terrain Proxy Min", f"{t_min:.4f}")
    _field("Terrain Proxy Max", f"{t_max:.4f}")
    _field("Terrain Proxy Mean", f"{t_mean:.4f}")
    _field("Terrain Proxy Std Dev", f"{t_std:.4f}")
    _field("Flood Proxy Min", f"{f_min:.4f}")
    _field("Flood Proxy Max", f"{f_max:.4f}")
    _field("Flood Proxy Mean", f"{f_mean:.4f}")
    _field("Flood Proxy Std Dev", f"{f_std:.4f}")

    t_in_range = (t_min >= 0.0) and (t_max <= 1.0)
    all_passed = _result(
        "Terrain proxy strictly bounded within [0.0, 1.0]",
        t_in_range,
        f"min={t_min:.4f}, max={t_max:.4f}"
    ) and all_passed

    f_in_range = (f_min >= 0.0) and (f_max <= 1.0)
    all_passed = _result(
        "Flood proxy strictly bounded within [0.0, 1.0]",
        f_in_range,
        f"min={f_min:.4f}, max={f_max:.4f}"
    ) and all_passed

    # 6. Summary Verdict
    _section("6. SUMMARY VERDICT")
    _field("Spatial Compatibility", "CONFIRMED ALIGNED" if dims_match and res_match and transform_match and bounds_match and masks_identical else "INCOMPATIBLE")
    _field("Numerical Validity", "CONFIRMED VALID" if t_in_range and f_in_range and inf_terrain_count == 0 and inf_flood_count == 0 else "INVALID")
    _field("Integration Readiness", "READY FOR STEP 6 INTEGRATION" if all_passed else "BLOCKED")

    print(f"\n{_sep('=')}")
    if all_passed:
        print("MULTI-HAZARD INPUT INSPECTION: PASS")
    else:
        print("MULTI-HAZARD INPUT INSPECTION: FAIL")
    print(_sep('='))

    return all_passed


if __name__ == "__main__":
    success = inspect_multihazard_inputs()
    sys.exit(0 if success else 1)
