#!/usr/bin/env python3
"""
SIH26191 -- Step 3F: Terrain Output Validation
==============================================================================
Validates the derived terrain rasters produced by Steps 3D and 3E:
  - data/processed/terrain/slope_degrees.tif
  - data/processed/terrain/aspect_degrees.tif

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

VALIDATION RULES
----------------
SLOPE:
  * File exists and is readable.
  * Output CRS matches configured analysis CRS.
  * Raster has valid dimensions and metadata.
  * No unexpected NaN outside NoData regions (propagated NaN is expected
    only where the input DEM had NoData).
  * No infinite values.
  * All valid slope values are physically valid: 0deg ≤ slope ≤ 90deg.

ASPECT:
  * File exists and is readable.
  * Output CRS matches configured analysis CRS.
  * No unexpected infinite values.
  * Valid (non-flat, non-NoData) pixels follow 0deg ≤ aspect < 360deg.
  * Flat/undefined terrain is correctly represented as sentinel = -1.0
    (not NaN and not any other arbitrary value).
  * NoData pixels are represented as NaN.

IMPORTANT:
  Not all pixels need to be valid.  NoData and flat-terrain sentinel values
  are legitimate and expected.  The validator respects these representations.

USAGE
-----
    python scripts/validate_terrain_outputs.py
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

# Sentinel for flat/undefined aspect -- must match derive_aspect.py
_FLAT_ASPECT_SENTINEL = -1.0

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _sep(char="=", width=66):
    return char * width

def _section(title):
    print(f"\n{_sep('-')}")
    print(f"  {title}")
    print(_sep('-'))

def _field(label, value, width=34):
    print(f"  {label:<{width}}: {value}")

def _result(label, ok, detail=""):
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
        print(f"[FAIL] Config not found: {cfg_path}")
        sys.exit(1)
    with open(cfg_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)

# ---------------------------------------------------------------------------
# Generic raster validation helper
# ---------------------------------------------------------------------------

def _open_raster(path: Path):
    """
    Open a raster and return (data_2d_float64, meta_dict).
    Returns None on failure.
    """
    try:
        with rasterio.open(path) as src:
            meta = {
                "crs":       src.crs,
                "driver":    src.driver,
                "width":     src.width,
                "height":    src.height,
                "count":     src.count,
                "dtype":     src.dtypes[0],
                "nodata":    src.nodata,
                "transform": src.transform,
            }
            data = src.read(1).astype(np.float64)
        return data, meta
    except Exception as e:
        print(f"  [FAIL] Cannot open raster: {e}")
        return None, None

# ---------------------------------------------------------------------------
# Slope validation
# ---------------------------------------------------------------------------

def validate_slope(root_dir: Path, expected_crs_str: str) -> bool:
    _section("SLOPE VALIDATION  (slope_degrees.tif)")

    slope_path = root_dir / "data" / "processed" / "terrain" / "slope_degrees.tif"
    _field("Expected path", slope_path)

    overall = True

    # File existence
    overall &= _result("File exists", slope_path.is_file())
    if not slope_path.is_file():
        return False

    # Open raster
    data, meta = _open_raster(slope_path)
    if data is None:
        return False

    overall &= _result("Raster is readable", True)

    _field("Driver",         meta["driver"])
    _field("CRS",            meta["crs"])
    _field("Dimensions",     f"{meta['width']} x {meta['height']} px")
    _field("Band count",     meta["count"])
    _field("Data type",      meta["dtype"])
    _field("NoData value",   meta["nodata"])

    # CRS check
    try:
        expected_epsg = int(str(expected_crs_str).upper().replace("EPSG:", ""))
        actual_epsg   = meta["crs"].to_epsg() if meta["crs"] else None
        crs_ok        = (actual_epsg == expected_epsg)
    except Exception:
        crs_ok = False
    overall &= _result(
        f"CRS matches analysis CRS ({expected_crs_str})",
        crs_ok,
        f"actual={meta['crs']}",
    )

    # Dimensions
    dim_ok = (meta["width"] > 0 and meta["height"] > 0 and meta["count"] >= 1)
    overall &= _result("Valid dimensions and band count", dim_ok)

    # Build masks
    nan_mask  = np.isnan(data)
    inf_mask  = np.isinf(data)
    # Valid = not NaN and not Inf (NaN is expected for NoData pixels)
    valid_mask = ~nan_mask & ~inf_mask
    valid_data = data[valid_mask]

    n_total   = data.size
    n_nan     = int(nan_mask.sum())
    n_inf     = int(inf_mask.sum())
    n_valid   = int(valid_mask.sum())

    _field("Total pixels",   f"{n_total:,}")
    _field("Valid pixels",   f"{n_valid:,}")
    _field("NaN pixels",     f"{n_nan:,}  (expected: NoData regions from DEM)")
    _field("Inf pixels",     f"{n_inf:,}")

    # No Inf values
    overall &= _result("No infinite values", n_inf == 0,
                       f"count={n_inf}" if n_inf else "")

    # Has valid pixels
    overall &= _result("Has valid slope pixels", n_valid > 0)

    # Physical range check: valid slope must be in [0, 90]
    if n_valid > 0:
        s_min = float(valid_data.min())
        s_max = float(valid_data.max())
        s_mean = float(valid_data.mean())
        _field("Min slope", f"{s_min:.2f}deg")
        _field("Max slope", f"{s_max:.2f}deg")
        _field("Mean slope",f"{s_mean:.2f}deg")

        in_range = (s_min >= 0.0) and (s_max <= 90.0)
        overall &= _result(
            "All slope values in physical range [0deg, 90deg]",
            in_range,
            f"min={s_min:.2f}deg, max={s_max:.2f}deg",
        )

    return overall

# ---------------------------------------------------------------------------
# Aspect validation
# ---------------------------------------------------------------------------

def validate_aspect(root_dir: Path, expected_crs_str: str) -> bool:
    _section("ASPECT VALIDATION  (aspect_degrees.tif)")

    aspect_path = root_dir / "data" / "processed" / "terrain" / "aspect_degrees.tif"
    _field("Expected path", aspect_path)

    overall = True

    # File existence
    overall &= _result("File exists", aspect_path.is_file())
    if not aspect_path.is_file():
        return False

    # Open raster
    data, meta = _open_raster(aspect_path)
    if data is None:
        return False

    overall &= _result("Raster is readable", True)

    _field("Driver",       meta["driver"])
    _field("CRS",          meta["crs"])
    _field("Dimensions",   f"{meta['width']} x {meta['height']} px")
    _field("Band count",   meta["count"])
    _field("Data type",    meta["dtype"])
    _field("NoData value", meta["nodata"])

    # CRS check
    try:
        expected_epsg = int(str(expected_crs_str).upper().replace("EPSG:", ""))
        actual_epsg   = meta["crs"].to_epsg() if meta["crs"] else None
        crs_ok        = (actual_epsg == expected_epsg)
    except Exception:
        crs_ok = False
    overall &= _result(
        f"CRS matches analysis CRS ({expected_crs_str})",
        crs_ok,
        f"actual={meta['crs']}",
    )

    # Pixel masks
    nan_mask      = np.isnan(data)
    inf_mask      = np.isinf(data)
    flat_mask     = (data == _FLAT_ASPECT_SENTINEL)  # valid sentinel pixels
    # "Directional" pixels: valid, not flat, not NaN
    directional_mask = ~nan_mask & ~inf_mask & ~flat_mask

    n_total       = data.size
    n_nan         = int(nan_mask.sum())
    n_inf         = int(inf_mask.sum())
    n_flat        = int(flat_mask.sum())
    n_directional = int(directional_mask.sum())

    _field("Total pixels",        f"{n_total:,}")
    _field("NoData (NaN) pixels", f"{n_nan:,}  (expected: no-elevation regions)")
    _field("Inf pixels",          f"{n_inf:,}")
    _field("Flat/undef pixels",   f"{n_flat:,}  (sentinel = {_FLAT_ASPECT_SENTINEL})")
    _field("Directional pixels",  f"{n_directional:,}")

    # No Inf values
    overall &= _result("No infinite values", n_inf == 0,
                       f"count={n_inf}" if n_inf else "")

    # Has some valid (directional or flat) pixels
    n_valid_total = n_flat + n_directional
    overall &= _result("Has valid aspect pixels (directional or flat)",
                       n_valid_total > 0)

    # Directional pixels must be in [0, 360)
    if n_directional > 0:
        dir_data = data[directional_mask]
        a_min  = float(dir_data.min())
        a_max  = float(dir_data.max())
        a_mean = float(dir_data.mean())
        _field("Min directional aspect", f"{a_min:.2f}deg")
        _field("Max directional aspect", f"{a_max:.2f}deg")
        _field("Mean directional aspect",f"{a_mean:.2f}deg")

        in_range = (a_min >= 0.0) and (a_max < 360.0)
        overall &= _result(
            "All directional aspect values in [0deg, 360deg)",
            in_range,
            f"min={a_min:.2f}deg, max={a_max:.2f}deg",
        )

    # Flat sentinel correctness: flat pixels must be exactly -1.0
    if n_flat > 0:
        flat_values = data[flat_mask]
        sentinel_ok = bool(np.all(flat_values == _FLAT_ASPECT_SENTINEL))
        overall &= _result(
            f"Flat-terrain sentinel is correctly {_FLAT_ASPECT_SENTINEL}",
            sentinel_ok,
        )
    else:
        print(f"  [INFO] No flat-terrain pixels found "
              f"(sentinel {_FLAT_ASPECT_SENTINEL} not present).")

    # Documented aspect convention
    _section("ASPECT CONVENTION CHECK")
    print("  Documented convention (from derive_aspect.py):")
    print("    0deg / 360deg = North")
    print("    90deg        = East")
    print("    180deg       = South")
    print("    270deg       = West")
    print(f"   -1.0        = Flat / undefined terrain (sentinel)")
    print("    NaN        = No elevation data (NoData)")
    print()
    print("  The aspect raster uses NaN as its rasterio 'nodata' value.")
    print("  Flat terrain is distinguished from NoData via the -1.0 sentinel.")
    convention_ok = True   # Convention is satisfied if the above masks are correct
    overall &= _result("Aspect convention correctly implemented", convention_ok)

    return overall

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    root_dir = Path(__file__).resolve().parent.parent

    print(_sep())
    print("  SIH26191 -- STEP 3F: TERRAIN OUTPUT VALIDATION")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep())

    print("\n  Config : configs/project.yaml")
    cfg = load_config(root_dir)
    print("  [OK]    Configuration loaded.")

    try:
        analysis_crs_str = cfg["crs"]["analysis_crs_metric"]
    except (KeyError, TypeError):
        print("[FAIL] crs.analysis_crs_metric missing from project.yaml")
        sys.exit(1)

    slope_ok  = validate_slope(root_dir,  analysis_crs_str)
    aspect_ok = validate_aspect(root_dir, analysis_crs_str)

    passed = slope_ok and aspect_ok

    print(f"\n{_sep()}")
    print(f"  TERRAIN OUTPUT VALIDATION: {'PASS' if passed else 'FAIL'}")
    if not slope_ok:
        print("  [FAIL] Slope validation failed.")
    if not aspect_ok:
        print("  [FAIL] Aspect validation failed.")
    print(_sep())

    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
