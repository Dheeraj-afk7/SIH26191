#!/usr/bin/env python3
"""
SIH26191 -- Step 4A: Inspect Terrain Inputs
==============================================================================
Programmatic inspection and spatial alignment verification of processed terrain
layers (slope and aspect) prior to landslide susceptibility proxy calculation.

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

PURPOSE
-------
Inspects and validates the processed terrain derivatives produced in Step 3:
  - data/processed/terrain/slope_degrees.tif
  - data/processed/terrain/aspect_degrees.tif

REQUIREMENTS & CHECKS
---------------------
1. Dynamically load configuration from configs/project.yaml.
2. Dynamically locate slope and aspect rasters.
3. Validate SLOPE:
   - File exists and is readable
   - CRS matches configured analysis CRS (EPSG:32644)
   - Valid dimensions and transform
   - Valid values: 0deg <= slope <= 90deg
   - Statistics: minimum, maximum, mean
4. Validate ASPECT:
   - File exists and is readable
   - CRS matches configured analysis CRS (EPSG:32644)
   - Valid dimensions and transform
   - Valid values: 0deg <= aspect <= 360deg, flat sentinel = -1.0, NoData = NaN
5. Spatial Grid Alignment:
   - Matching CRS
   - Matching pixel dimensions (width x height)
   - Matching geotransform / pixel resolution
   - Identical spatial extent / bounding box
6. Read-only operation: No input file is modified.

USAGE
-----
    python scripts/inspect_terrain_inputs.py
"""

import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Third-party imports
# ---------------------------------------------------------------------------
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

_FLAT_ASPECT_SENTINEL = -1.0


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
# Inspection logic
# ---------------------------------------------------------------------------

def inspect_terrain_inputs() -> bool:
    print(_sep("="))
    print("  SIH26191 -- STEP 4A: TERRAIN INPUT INSPECTION")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    all_passed = True
    cfg = load_config(_ROOT_DIR)

    # 1. Config paths & parameters
    analysis_crs_str = cfg.get("crs", {}).get("analysis_crs_metric", "EPSG:32644")
    target_crs = CRS.from_string(analysis_crs_str)

    paths_cfg = cfg.get("paths", {})
    slope_rel = paths_cfg.get("slope_processed", "data/processed/terrain/slope_degrees.tif")
    aspect_rel = paths_cfg.get("aspect_processed", "data/processed/terrain/aspect_degrees.tif")

    slope_path = (_ROOT_DIR / slope_rel).resolve()
    aspect_path = (_ROOT_DIR / aspect_rel).resolve()

    _section("1. CONFIGURATION & LOCATIONS")
    _field("Config file", "configs/project.yaml")
    _field("Configured analysis CRS", analysis_crs_str)
    _field("Slope input path", str(slope_path))
    _field("Aspect input path", str(aspect_path))

    # 2. Inspect Slope Raster
    _section("2. SLOPE RASTER AUDIT (slope_degrees.tif)")
    slope_exists = slope_path.is_file()
    all_passed &= _result("Slope file exists", slope_exists, str(slope_path))
    if not slope_exists:
        print("[FAIL] Slope raster does not exist. Run Step 3 pipeline first.")
        print(f"\n{_sep('=')}")
        print("TERRAIN INPUT INSPECTION: FAIL")
        print(_sep('='))
        return False

    try:
        with rasterio.open(slope_path) as slope_src:
            slope_readable = True
            all_passed &= _result("Slope raster is readable", True)
            
            slope_crs = slope_src.crs
            slope_w, slope_h = slope_src.width, slope_src.height
            slope_transform = slope_src.transform
            slope_bounds = slope_src.bounds
            slope_nodata = slope_src.nodata
            slope_dtype = slope_src.dtypes[0]

            _field("Driver", slope_src.driver)
            _field("CRS", str(slope_crs))
            _field("Dimensions (W x H)", f"{slope_w} x {slope_h} pixels")
            _field("Data type", slope_dtype)
            _field("NoData value", str(slope_nodata))
            _field("Bounds (Left, Bottom, Right, Top)", 
                   f"({slope_bounds.left:.2f}, {slope_bounds.bottom:.2f}, {slope_bounds.right:.2f}, {slope_bounds.top:.2f})")
            _field("Pixel Resolution (X, Y)", f"{slope_transform.a:.4f} m, {abs(slope_transform.e):.4f} m")

            crs_match = (slope_crs == target_crs)
            all_passed &= _result("CRS matches analysis CRS", crs_match, f"expected={target_crs}, actual={slope_crs}")

            slope_data = slope_src.read(1)
            total_px = slope_data.size
            nan_mask = np.isnan(slope_data)
            nodata_mask = nan_mask if (slope_nodata is None or np.isnan(slope_nodata)) else (nan_mask | (slope_data == slope_nodata))
            valid_mask = ~nodata_mask

            valid_count = int(np.sum(valid_mask))
            nodata_count = int(np.sum(nodata_mask))
            inf_count = int(np.sum(np.isinf(slope_data)))

            _field("Total pixels", f"{total_px:,}")
            _field("Valid terrain pixels", f"{valid_count:,} ({valid_count/total_px*100:.2f}%)")
            _field("NoData pixels", f"{nodata_count:,} ({nodata_count/total_px*100:.2f}%)")
            _field("Infinite pixels", str(inf_count))

            all_passed &= _result("No infinite values", inf_count == 0)
            all_passed &= _result("Has valid pixels", valid_count > 0)

            if valid_count > 0:
                valid_slope = slope_data[valid_mask]
                s_min = float(np.min(valid_slope))
                s_max = float(np.max(valid_slope))
                s_mean = float(np.mean(valid_slope))
                s_std = float(np.std(valid_slope))

                _field("Minimum slope", f"{s_min:.2f} deg")
                _field("Maximum slope", f"{s_max:.2f} deg")
                _field("Mean slope", f"{s_mean:.2f} deg")
                _field("Std dev slope", f"{s_std:.2f} deg")

                valid_range = (s_min >= 0.0) and (s_max <= 90.0)
                all_passed &= _result("Slope values within physical range [0 deg, 90 deg]", valid_range,
                                      f"min={s_min:.2f} deg, max={s_max:.2f} deg")
    except Exception as e:
        print(f"[FAIL] Error reading slope raster: {e}")
        all_passed = False

    # 3. Inspect Aspect Raster
    _section("3. ASPECT RASTER AUDIT (aspect_degrees.tif)")
    aspect_exists = aspect_path.is_file()
    all_passed &= _result("Aspect file exists", aspect_exists, str(aspect_path))
    if not aspect_exists:
        print("[FAIL] Aspect raster does not exist. Run Step 3 pipeline first.")
        print(f"\n{_sep('=')}")
        print("TERRAIN INPUT INSPECTION: FAIL")
        print(_sep('='))
        return False

    try:
        with rasterio.open(aspect_path) as aspect_src:
            all_passed &= _result("Aspect raster is readable", True)
            
            aspect_crs = aspect_src.crs
            aspect_w, aspect_h = aspect_src.width, aspect_src.height
            aspect_transform = aspect_src.transform
            aspect_bounds = aspect_src.bounds
            aspect_nodata = aspect_src.nodata
            aspect_dtype = aspect_src.dtypes[0]

            _field("Driver", aspect_src.driver)
            _field("CRS", str(aspect_crs))
            _field("Dimensions (W x H)", f"{aspect_w} x {aspect_h} pixels")
            _field("Data type", aspect_dtype)
            _field("NoData value", str(aspect_nodata))
            _field("Bounds (Left, Bottom, Right, Top)", 
                   f"({aspect_bounds.left:.2f}, {aspect_bounds.bottom:.2f}, {aspect_bounds.right:.2f}, {aspect_bounds.top:.2f})")
            _field("Pixel Resolution (X, Y)", f"{aspect_transform.a:.4f} m, {abs(aspect_transform.e):.4f} m")

            crs_match_asp = (aspect_crs == target_crs)
            all_passed &= _result("CRS matches analysis CRS", crs_match_asp, f"expected={target_crs}, actual={aspect_crs}")

            aspect_data = aspect_src.read(1)
            total_px_asp = aspect_data.size
            nan_mask_asp = np.isnan(aspect_data)
            nodata_mask_asp = nan_mask_asp if (aspect_nodata is None or np.isnan(aspect_nodata)) else (nan_mask_asp | (aspect_data == aspect_nodata))
            valid_mask_asp = ~nodata_mask_asp

            valid_count_asp = int(np.sum(valid_mask_asp))
            nodata_count_asp = int(np.sum(nodata_mask_asp))
            inf_count_asp = int(np.sum(np.isinf(aspect_data)))

            flat_mask = (aspect_data == _FLAT_ASPECT_SENTINEL) & valid_mask_asp
            flat_count = int(np.sum(flat_mask))
            directional_mask = valid_mask_asp & ~flat_mask
            directional_count = int(np.sum(directional_mask))

            _field("Total pixels", f"{total_px_asp:,}")
            _field("Valid pixels", f"{valid_count_asp:,} ({valid_count_asp/total_px_asp*100:.2f}%)")
            _field("NoData pixels", f"{nodata_count_asp:,} ({nodata_count_asp/total_px_asp*100:.2f}%)")
            _field("Flat terrain pixels (sentinel=-1.0)", f"{flat_count:,}")
            _field("Directional aspect pixels", f"{directional_count:,}")

            all_passed &= _result("No infinite values", inf_count_asp == 0)
            all_passed &= _result("Has valid pixels", valid_count_asp > 0)

            if directional_count > 0:
                dir_aspect = aspect_data[directional_mask]
                a_min = float(np.min(dir_aspect))
                a_max = float(np.max(dir_aspect))
                a_mean = float(np.mean(dir_aspect))

                _field("Directional aspect min", f"{a_min:.2f} deg")
                _field("Directional aspect max", f"{a_max:.2f} deg")
                _field("Directional aspect mean", f"{a_mean:.2f} deg")

                valid_aspect_range = (a_min >= 0.0) and (a_max <= 360.0)
                all_passed &= _result("Directional aspect in range [0 deg, 360 deg]", valid_aspect_range,
                                      f"min={a_min:.2f} deg, max={a_max:.2f} deg")
                all_passed &= _result("Flat terrain sentinel convention verified (-1.0)", True)
    except Exception as e:
        print(f"[FAIL] Error reading aspect raster: {e}")
        all_passed = False

    # 4. Spatial Grid Alignment Check
    _section("4. SPATIAL GRID ALIGNMENT & COMPATIBILITY CHECK")
    if slope_exists and aspect_exists:
        try:
            with rasterio.open(slope_path) as s_src, rasterio.open(aspect_path) as a_src:
                crs_identical = (s_src.crs == a_src.crs)
                dim_identical = (s_src.width == a_src.width) and (s_src.height == a_src.height)
                
                # Compare transforms with high float precision
                t_s = s_src.transform
                t_a = a_src.transform
                trans_identical = (
                    np.isclose(t_s.a, t_a.a) and
                    np.isclose(t_s.b, t_a.b) and
                    np.isclose(t_s.c, t_a.c) and
                    np.isclose(t_s.d, t_a.d) and
                    np.isclose(t_s.e, t_a.e) and
                    np.isclose(t_s.f, t_a.f)
                )

                bounds_identical = (
                    np.isclose(s_src.bounds.left, a_src.bounds.left) and
                    np.isclose(s_src.bounds.bottom, a_src.bounds.bottom) and
                    np.isclose(s_src.bounds.right, a_src.bounds.right) and
                    np.isclose(s_src.bounds.top, a_src.bounds.top)
                )

                all_passed &= _result("CRS identical across slope and aspect", crs_identical, f"{s_src.crs}")
                all_passed &= _result("Dimensions identical (width & height)", dim_identical, f"{s_src.width} x {s_src.height}")
                all_passed &= _result("Affine transform / pixel grid identical", trans_identical)
                all_passed &= _result("Spatial extent / bounding box identical", bounds_identical)

                # NoData mask alignment
                s_nodata_mask = np.isnan(s_src.read(1))
                a_nodata_mask = np.isnan(a_src.read(1))
                nodata_aligned = np.array_equal(s_nodata_mask, a_nodata_mask)
                all_passed &= _result("NoData masks perfectly aligned", nodata_aligned,
                                      f"{np.sum(s_nodata_mask):,} NoData pixels")
        except Exception as e:
            print(f"[FAIL] Error checking alignment: {e}")
            all_passed = False

    # Summary
    print(f"\n{_sep('=')}")
    if all_passed:
        print("TERRAIN INPUT INSPECTION: PASS")
    else:
        print("TERRAIN INPUT INSPECTION: FAIL")
    print(_sep('='))

    return all_passed


if __name__ == "__main__":
    success = inspect_terrain_inputs()
    sys.exit(0 if success else 1)
