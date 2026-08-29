#!/usr/bin/env python3
"""
SIH26191 -- Step 3D: Slope Derivation
==============================================================================
Derives a slope-in-degrees raster from the raw DEM.

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

SCIENTIFIC APPROACH
-------------------
The raw DEM is stored in EPSG:4326 (decimal degrees). Calculating slope by
treating 0.000278deg pixel spacing as if it were metres would be INCORRECT --
it would produce slope values that are orders of magnitude wrong because the
unit mismatch is never accounted for.

Correct procedure (used here):
  1. Open the raw DEM (read-only, never modified).
  2. Reproject it IN-MEMORY to the configured metric analysis CRS
     (EPSG:32644 -- UTM Zone 44N, units: metres).
  3. Calculate slope from the metric pixel spacing using the standard
     gradient-magnitude formula:
         slope = arctan( sqrt( (dz/dx)² + (dz/dy)² ) )
     where dz/dx and dz/dy are elevation differences per metre.
  4. Write the slope output with the metric CRS embedded.

The raw DEM file is NEVER modified.
No terrain data is written to data/raw/.

OUTPUT
------
  data/processed/terrain/slope_degrees.tif

  CRS   : EPSG:32644 (WGS 84 / UTM Zone 44N)
  Unit  : degrees (0deg = flat, 90deg = vertical)
  Dtype : float32

SUITABILITY
-----------
  Suitable for: pilot-scale terrain screening and decision-support.
  NOT for: geotechnical certification or guaranteed site-safety assessment.

USAGE
-----
    python processing/terrain/derive_slope.py
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
# Paths -- this script lives at processing/terrain/derive_slope.py
# Project root is two levels up.
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_ROOT_DIR   = _SCRIPT_DIR.parent.parent

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
# Core slope derivation
# ---------------------------------------------------------------------------

def derive_slope(cfg: dict) -> bool:
    """
    Read DEM -> reproject in-memory to metric CRS -> compute slope -> write.
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
    output_path = output_dir / "slope_degrees.tif"

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
    #    (EPSG:32644 -- WGS 84 / UTM Zone 44N, units: metres)
    #
    #    WHY: Gradient calculations need pixel spacing in metres.
    #         EPSG:4326 pixels are in degrees -- treating them as metres
    #         would produce scientifically invalid slope values.
    # ------------------------------------------------------------------
    print(f"\n{_sep('-')}")
    print("  STEP 1: REPROJECT DEM IN-MEMORY TO METRIC CRS")
    print(_sep('-'))

    dst_crs = CRS.from_string(analysis_crs_str)

    try:
        with rasterio.open(dem_path) as src:
            src_crs    = src.crs
            src_nodata = src.nodata
            src_dtype  = src.dtypes[0]

            print(f"  Source CRS   : {src_crs}")
            print(f"  Source nodata: {src_nodata}")
            print(f"  Source dtype : {src_dtype}")
            print(f"  Target CRS   : {dst_crs}")

            # Calculate the optimal transform and dimensions for the target CRS
            dst_transform, dst_width, dst_height = calculate_default_transform(
                src.crs, dst_crs,
                src.width, src.height,
                *src.bounds,
            )
            print(f"  Reprojected dimensions: {dst_width} x {dst_height} px")
            print(f"  Reprojected pixel size: "
                  f"{abs(dst_transform.a):.2f} m x {abs(dst_transform.e):.2f} m")

            # Allocate in-memory array for reprojected elevation
            # Use float32 -- sufficient precision for elevation, memory-efficient
            dst_array = np.full(
                (1, dst_height, dst_width),
                fill_value=np.nan,
                dtype=np.float32,
            )

            # Nodata handling: use np.nan internally for safe masking
            reproject(
                source      = rasterio.band(src, 1),
                destination = dst_array,
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

    elev_metric = dst_array[0]   # 2-D elevation array in metric CRS (metres)
    print("  Reprojection complete.")

    # ------------------------------------------------------------------
    # 3. Calculate slope in degrees
    #
    #    Using numpy.gradient on the metric-space elevation array.
    #    numpy.gradient returns finite differences; with uniform pixel
    #    spacing dx and dy in metres, this gives dz/dx and dz/dy in m/m.
    #
    #    slope_radians = arctan( sqrt( (dz/dy)² + (dz/dx)² ) )
    #    slope_degrees = slope_radians x (180 / π)
    #
    #    NaN pixels (NoData) propagate naturally through gradient and
    #    arctan, producing NaN in the output -- correct behaviour.
    # ------------------------------------------------------------------
    print(f"\n{_sep('-')}")
    print("  STEP 2: CALCULATE SLOPE IN DEGREES")
    print(_sep('-'))
    print("  Method: arctan(sqrt((dz/dy)^2 + (dz/dx)^2))")
    print("  Units : degrees (0deg = flat, 90deg = vertical)")

    # Metric pixel spacing in metres (absolute values)
    pixel_size_x = abs(dst_transform.a)   # E-W spacing in metres
    pixel_size_y = abs(dst_transform.e)   # N-S spacing in metres

    print(f"  Pixel spacing X: {pixel_size_x:.4f} m")
    print(f"  Pixel spacing Y: {pixel_size_y:.4f} m")

    # numpy.gradient on 2D array: returns [d/drow, d/dcol]
    # d/drow corresponds to N-S direction (dy), d/dcol to E-W (dx)
    dz_dy, dz_dx = np.gradient(elev_metric, pixel_size_y, pixel_size_x)

    # Gradient magnitude -> slope angle
    slope_radians = np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))
    slope_degrees = np.degrees(slope_radians).astype(np.float32)

    # Build a valid-pixel mask (NaN = NoData from reprojection)
    valid_mask    = ~np.isnan(slope_degrees)
    valid_slopes  = slope_degrees[valid_mask]

    if valid_slopes.size == 0:
        print("\n[FAIL] No valid slope values computed.")
        return False

    slope_min  = float(valid_slopes.min())
    slope_max  = float(valid_slopes.max())
    slope_mean = float(valid_slopes.mean())

    print(f"  Valid slope pixels : {valid_slopes.size:,}")
    print(f"  Minimum slope      : {slope_min:.2f}deg")
    print(f"  Maximum slope      : {slope_max:.2f}deg")
    print(f"  Mean slope         : {slope_mean:.2f}deg")

    # Physical sanity check: slope must be in [0, 90] degrees
    if slope_max > 90.0 or slope_min < 0.0:
        print(f"\n[FAIL] Slope values outside physical range [0, 90]: "
              f"min={slope_min:.2f}deg, max={slope_max:.2f}deg")
        return False

    # ------------------------------------------------------------------
    # 4. Write slope output
    #    CRS   : analysis CRS (EPSG:32644)
    #    Dtype : float32
    #    NoData: nan
    # ------------------------------------------------------------------
    print(f"\n{_sep('-')}")
    print("  STEP 3: WRITE SLOPE OUTPUT")
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
            compress  = "lzw",   # lossless compression -- reduces file size
        ) as dst:
            dst.write(slope_degrees, 1)
            dst.update_tags(
                TIFFTAG_IMAGEDESCRIPTION=(
                    "SIH26191 Slope (degrees) -- Rudraprayag pilot. "
                    "Decision-support terrain layer. "
                    "Not engineering-certified."
                )
            )
    except Exception as e:
        print(f"\n[FAIL] Error writing slope output: {e}")
        return False

    out_size_mb = output_path.stat().st_size / (1024 ** 2)
    print(f"  Output written    : {output_path}")
    print(f"  Output size       : {out_size_mb:.2f} MB")
    print(f"  Output CRS        : {dst_crs}")

    return True

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    print(_sep())
    print("  SIH26191 -- STEP 3D: SLOPE DERIVATION")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep())

    cfg = load_config()
    print("  [OK] Configuration loaded.")

    passed = derive_slope(cfg)

    print(f"\n{_sep()}")
    print(f"  SLOPE DERIVATION: {'PASS' if passed else 'FAIL'}")
    print(_sep())

    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
