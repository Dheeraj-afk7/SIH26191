#!/usr/bin/env python3
"""
SIH26191 -- Step 3E: Aspect Derivation
==============================================================================
Derives an aspect-in-degrees raster from the raw DEM.

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

ASPECT CONVENTION (documented here and preserved in output metadata)
---------------------------------------------------------------------
  0deg / 360deg = North  (slope faces toward the north)
  90deg        = East
  180deg       = South
  270deg       = West

  Flat / undefined terrain (gradient magnitude ~= 0):
    Represented as -1.0 (a sentinel value outside the 0-360 range).
    This is a deliberate, documented choice: using NaN for flat terrain
    would prevent distinguishing "no data" from "flat data" downstream.
    Any consumer of the output MUST treat -1.0 as "flat/undefined aspect".

SCIENTIFIC APPROACH
-------------------
  Same reprojection strategy as derive_slope.py:
  1. Open raw DEM (read-only).
  2. Reproject IN-MEMORY to configured metric CRS (EPSG:32644).
  3. Compute aspect from metric gradients using atan2.
  4. Write output with metric CRS embedded.

FORMULA
-------
  dz/dx, dz/dy = metric E-W and N-S elevation gradients (m/m)
  aspect_math  = atan2(-dz/dy, dz/dx)   [mathematical convention, from East]
  aspect_geo   = 90 - degrees(aspect_math)   [convert to geographic/compass]
  aspect_geo   = aspect_geo mod 360      [ensure [0, 360) range]
  Flat pixels  = -1.0

OUTPUT
------
  data/processed/terrain/aspect_degrees.tif

  CRS       : EPSG:32644 (WGS 84 / UTM Zone 44N)
  Unit      : degrees, compass bearing (0-360deg), -1 = flat/undefined
  Dtype     : float32
  NoData    : nan  (only for pixels with no elevation data)

USAGE
-----
    python processing/terrain/derive_aspect.py
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
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    from rasterio.crs import CRS
except ImportError as e:
    print(f"[ERROR] Required package not installed: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths -- this script lives at processing/terrain/derive_aspect.py
# Project root is two levels up.
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_ROOT_DIR   = _SCRIPT_DIR.parent.parent

# Sentinel value for flat / undefined terrain aspect
_FLAT_ASPECT_VALUE = -1.0

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _sep(char="=", width=66):
    return char * width

def _field(label, value, width=30):
    print(f"  {label:<{width}}: {value}")

# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config() -> dict:
    cfg_path = _ROOT_DIR / "configs" / "project.yaml"
    if not cfg_path.is_file():
        print(f"[FAIL] Config not found: {cfg_path}")
        sys.exit(1)
    with open(cfg_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)

# ---------------------------------------------------------------------------
# Core aspect derivation
# ---------------------------------------------------------------------------

def derive_aspect(cfg: dict) -> bool:
    """
    Read DEM -> reproject in-memory to metric CRS -> compute aspect -> write.
    Returns True on success.
    """

    # ------------------------------------------------------------------
    # 1. Read configuration
    # ------------------------------------------------------------------
    try:
        dem_rel          = cfg["paths"]["dem_raw"]
        analysis_crs_str = cfg["crs"]["analysis_crs_metric"]
        processed_dir    = cfg["paths"].get("processed_dir", "data/processed")
    except (KeyError, TypeError) as e:
        print(f"[FAIL] Missing config key: {e}")
        return False

    dem_path    = _ROOT_DIR / dem_rel
    output_dir  = _ROOT_DIR / processed_dir / "terrain"
    output_path = output_dir / "aspect_degrees.tif"

    print(f"\n{_sep('-')}")
    print("  INPUTS & CONFIGURATION")
    print(_sep('-'))
    _field("Raw DEM (read-only)", dem_path)
    _field("Analysis CRS",       analysis_crs_str)
    _field("Output path",        output_path)

    if not dem_path.is_file():
        print(f"\n[FAIL] DEM not found: {dem_path}")
        return False

    output_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 2. Reproject DEM in-memory to metric CRS
    #    Identical strategy to derive_slope.py -- see that script for the
    #    full scientific rationale.
    # ------------------------------------------------------------------
    print(f"\n{_sep('-')}")
    print("  STEP 1: REPROJECT DEM IN-MEMORY TO METRIC CRS")
    print(_sep('-'))

    dst_crs = CRS.from_string(analysis_crs_str)

    try:
        with rasterio.open(dem_path) as src:
            src_nodata = src.nodata

            print(f"  Source CRS   : {src.crs}")
            print(f"  Source nodata: {src_nodata}")
            print(f"  Target CRS   : {dst_crs}")

            dst_transform, dst_width, dst_height = calculate_default_transform(
                src.crs, dst_crs,
                src.width, src.height,
                *src.bounds,
            )
            print(f"  Reprojected dimensions: {dst_width} x {dst_height} px")
            print(f"  Reprojected pixel size: "
                  f"{abs(dst_transform.a):.2f} m x {abs(dst_transform.e):.2f} m")

            dst_array = np.full(
                (1, dst_height, dst_width),
                fill_value=np.nan,
                dtype=np.float32,
            )

            reproject(
                source           = rasterio.band(src, 1),
                destination      = dst_array,
                src_transform    = src.transform,
                src_crs          = src.crs,
                dst_transform    = dst_transform,
                dst_crs          = dst_crs,
                resampling       = Resampling.bilinear,
                src_nodata       = src_nodata,
                dst_nodata       = np.nan,
            )

    except Exception as e:
        print(f"\n[FAIL] Reprojection error: {e}")
        return False

    elev_metric = dst_array[0]
    print("  Reprojection complete.")

    # ------------------------------------------------------------------
    # 3. Calculate aspect in degrees (geographic / compass convention)
    #
    #    Step A: Compute metric elevation gradients via numpy.gradient.
    #      dz_dy = elevation change per metre in N-S direction (row axis)
    #      dz_dx = elevation change per metre in E-W direction (col axis)
    #
    #    Step B: atan2 in mathematical convention (angle from East,
    #      counter-clockwise positive):
    #      aspect_math = atan2(-dz_dy, dz_dx)
    #      The sign flip on dz_dy is because raster rows increase southward
    #      while geographic North is "up".
    #
    #    Step C: Convert to geographic/compass bearing (from North,
    #      clockwise positive):
    #      aspect_geo = 90deg - degrees(aspect_math)
    #      aspect_geo = aspect_geo mod 360   -> range [0, 360)
    #
    #    Step D: Flat terrain handling.
    #      Pixels where the gradient magnitude is effectively zero
    #      (< 1e-8 m/m) have undefined aspect.  They are assigned -1.0.
    #      This sentinel is documented in the output raster tags and README.
    #      NaN is reserved for "no elevation data" (NoData pixels).
    #
    #    NaN from NoData propagates through gradient -> atan2 -> NaN in output.
    #    NaN from NoData propagates through gradient -> atan2 -> NaN in output.
    # ------------------------------------------------------------------
    print(f"\n{_sep('-')}")
    print("  STEP 2: CALCULATE ASPECT IN DEGREES")
    print(_sep('-'))
    print("  Convention: 0/360=N, 90=E, 180=S, 270=W")
    print(f"  Flat/undefined terrain -> sentinel value: {_FLAT_ASPECT_VALUE}")

    pixel_size_x = abs(dst_transform.a)
    pixel_size_y = abs(dst_transform.e)

    # numpy.gradient: [d/drow, d/dcol] = [N-S, E-W] gradients
    dz_dy, dz_dx = np.gradient(elev_metric, pixel_size_y, pixel_size_x)

    # Gradient magnitude -- used to detect flat terrain
    grad_magnitude = np.sqrt(dz_dx**2 + dz_dy**2)

    # Mathematical aspect (from East, CCW positive)
    # Note: -dz_dy because row index increases southward
    aspect_math = np.arctan2(-dz_dy, dz_dx)

    # Convert to compass bearing (from North, CW positive), range [0, 360)
    aspect_geo = (90.0 - np.degrees(aspect_math)) % 360.0
    aspect_geo = aspect_geo.astype(np.float32)

    # Mark flat / undefined terrain with sentinel (-1.0)
    flat_mask   = grad_magnitude < 1e-8
    nodata_mask = np.isnan(elev_metric)   # pixels with no elevation data
    aspect_geo[flat_mask & ~nodata_mask] = _FLAT_ASPECT_VALUE

    # Propagate NoData: pixels where elevation was NaN -> NaN aspect
    aspect_geo[nodata_mask] = np.nan

    # ------------------------------------------------------------------
    # 4. Compute and print statistics
    # ------------------------------------------------------------------
    valid_mask    = ~np.isnan(aspect_geo)
    non_flat_mask = valid_mask & (aspect_geo >= 0)
    flat_count    = int(flat_mask.sum())
    nodata_count  = int(nodata_mask.sum())
    valid_count   = int(valid_mask.sum())

    print(f"\n  Total pixels       : {aspect_geo.size:,}")
    print(f"  Valid pixels       : {valid_count:,}")
    print(f"  NoData pixels      : {nodata_count:,}")
    print(f"  Flat/undef pixels  : {flat_count:,}  (sentinel = {_FLAT_ASPECT_VALUE})")

    non_flat_aspects = aspect_geo[non_flat_mask]
    if non_flat_aspects.size > 0:
        print(f"  Aspect range (non-flat): {non_flat_aspects.min():.2f}deg "
              f"-- {non_flat_aspects.max():.2f}deg")
    else:
        print("  No non-flat valid aspects found.")

    # ------------------------------------------------------------------
    # 5. Write aspect output
    # ------------------------------------------------------------------
    print(f"\n{_sep('-')}")
    print("  STEP 3: WRITE ASPECT OUTPUT")
    print(_sep('-'))

    try:
        with rasterio.open(
            output_path,
            mode      = "w",
            driver    = "GTiff",
            height    = dst_height,
            width     = dst_width,
            count     = 1,
            dtype     = np.float32,
            crs       = dst_crs,
            transform = dst_transform,
            nodata    = np.nan,
            compress  = "lzw",
        ) as dst:
            dst.write(aspect_geo, 1)
            dst.update_tags(
                TIFFTAG_IMAGEDESCRIPTION=(
                    "SIH26191 Aspect (degrees) -- Rudraprayag pilot. "
                    "Convention: 0/360=N, 90=E, 180=S, 270=W. "
                    f"Flat terrain sentinel = {_FLAT_ASPECT_VALUE}. "
                    "Decision-support terrain layer. Not engineering-certified."
                )
            )
    except Exception as e:
        print(f"\n[FAIL] Error writing aspect output: {e}")
        return False

    out_size_mb = output_path.stat().st_size / (1024 ** 2)
    _field("Output written", output_path)
    _field("Output size",    f"{out_size_mb:.2f} MB")
    _field("Output CRS",     dst_crs)
    _field("Valid aspect range", "0deg-360deg (non-flat pixels)")
    _field("Flat terrain handling", f"sentinel value = {_FLAT_ASPECT_VALUE}")

    return True

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print(_sep())
    print("  SIH26191 -- STEP 3E: ASPECT DERIVATION")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep())

    cfg = load_config()
    print("  [OK] Configuration loaded.")

    passed = derive_aspect(cfg)

    print(f"\n{_sep()}")
    print(f"  ASPECT DERIVATION: {'PASS' if passed else 'FAIL'}")
    print(_sep())

    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
