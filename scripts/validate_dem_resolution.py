#!/usr/bin/env python3
"""
SIH26191 -- Step 3B.2: DEM Resolution Validation
==============================================================================
Validates the raw DEM's pixel resolution and documents approximate ground
spacing, accounting for the geographic CRS (EPSG:4326) in which the DEM
is stored.

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

PURPOSE
-------
Pixel resolution in EPSG:4326 is expressed in decimal degrees, not metres.
One degree of latitude is approximately 111,320 m everywhere, but one degree
of longitude shrinks with increasing latitude (cos(lat) factor).  This script:

  1. Reports the native resolution in degrees.
  2. Estimates approximate ground spacing in metres at the raster's centre
     latitude -- separately for the latitude (N-S) and longitude (E-W)
     directions.
  3. States explicitly that this estimate is NOT exact uniform 30 m coverage.
  4. Documents suitability ONLY for pilot-scale terrain screening.
  5. States clearly what this DEM is NOT sufficient for.

SCOPE
-----
  * Read-only inspection -- the DEM is not modified in any way.
  * All paths read from configs/project.yaml.

USAGE
-----
    python scripts/validate_dem_resolution.py
"""

import sys
import math
from pathlib import Path

try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

try:
    import rasterio
except ImportError:
    print("[ERROR] rasterio not installed. Run: pip install rasterio")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _sep(char="=", width=66):
    return char * width

def _section(title):
    print(f"\n{_sep('-')}")
    print(f"  {title}")
    print(_sep('-'))

def _field(label, value, width=36):
    print(f"  {label:<{width}}: {value}")

def _result(label, ok, detail=""):
    tag = "[PASS]" if ok else "[FAIL]"
    line = f"  {tag}  {label}"
    if detail:
        line += f"  ({detail})"
    print(line)
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
        cfg = yaml.safe_load(fh)
    return cfg

# ---------------------------------------------------------------------------
# Ground-spacing estimation (EPSG:4326 -> metres)
# ---------------------------------------------------------------------------

# WGS-84 mean values used for ground-spacing approximation only.
# These are well-established geodetic constants; they are NOT used for
# coordinate transformation -- that is handled by pyproj/rasterio elsewhere.
_METRES_PER_DEGREE_LAT = 111_320.0   # approximately constant everywhere

def _metres_per_degree_lon(lat_deg: float) -> float:
    """
    Approximate metres per degree of longitude at a given latitude.
    Formula: 111,320 x cos(latitude_in_radians)
    This is a standard geographic approximation, not a rigorous projection.
    """
    return _METRES_PER_DEGREE_LAT * math.cos(math.radians(lat_deg))

# ---------------------------------------------------------------------------
# Core validation
# ---------------------------------------------------------------------------

def validate_resolution(root_dir: Path, cfg: dict) -> bool:
    overall = True

    # Read dem path from config
    try:
        dem_rel = cfg["paths"]["dem_raw"]
    except (KeyError, TypeError):
        print("[FAIL] paths.dem_raw missing from project.yaml")
        sys.exit(1)

    dem_path = root_dir / dem_rel

    # ------------------------------------------------------------------
    # Section 1 -- Open DEM, extract metadata
    # ------------------------------------------------------------------
    _section("1. DEM FILE & METADATA")

    if not dem_path.is_file():
        print(f"  [FAIL] DEM not found: {dem_path}")
        return False

    _field("DEM path", dem_path)

    try:
        with rasterio.open(dem_path) as src:
            transform  = src.transform
            crs        = src.crs
            width      = src.width
            height     = src.height
            bounds     = src.bounds
    except Exception as e:
        print(f"  [FAIL] rasterio error: {e}")
        return False

    # Pixel sizes -- use absolute values (handles south-up convention)
    res_x_deg = abs(transform.a)   # longitude direction
    res_y_deg = abs(transform.e)   # latitude direction

    _field("CRS",             crs)
    _field("Width (px)",      width)
    _field("Height (px)",     height)
    _field("West bound (deg)",  f"{bounds.left:.6f}")
    _field("East bound (deg)",  f"{bounds.right:.6f}")
    _field("South bound (deg)", f"{bounds.bottom:.6f}")
    _field("North bound (deg)", f"{bounds.top:.6f}")

    # ------------------------------------------------------------------
    # Section 2 -- Resolution in degrees
    # ------------------------------------------------------------------
    _section("2. NATIVE PIXEL RESOLUTION  (EPSG:4326 -- degrees)")

    _field("X pixel size (longitude)", f"{res_x_deg:.8f} deg")
    _field("Y pixel size (latitude)",  f"{res_y_deg:.8f} deg")
    print()
    print("  NOTE: Because the DEM is stored in EPSG:4326 (geographic coordinates),")
    print("        pixel dimensions are expressed in decimal degrees, not metres.")
    print("        Ground spacing in metres varies with latitude.")

    # Validation: resolution must be non-zero and positive
    res_valid = (res_x_deg > 0) and (res_y_deg > 0)
    overall &= _result("Pixel resolution is non-zero and positive", res_valid)

    # X/Y consistency -- within 0.1% tolerance (GLO-30 is square pixels)
    if res_x_deg > 0 and res_y_deg > 0:
        ratio = res_x_deg / res_y_deg
        consistent = abs(ratio - 1.0) < 0.001
        overall &= _result(
            "X and Y pixel sizes are consistent (square pixels)",
            consistent,
            f"ratio={ratio:.6f}",
        )

    # ------------------------------------------------------------------
    # Section 3 -- Approximate ground spacing at centre latitude
    # ------------------------------------------------------------------
    _section("3. APPROXIMATE GROUND SPACING IN METRES  (centre-latitude estimate)")

    centre_lat = (bounds.bottom + bounds.top) / 2.0
    centre_lon = (bounds.left  + bounds.right) / 2.0

    m_per_deg_lat = _METRES_PER_DEGREE_LAT
    m_per_deg_lon = _metres_per_degree_lon(centre_lat)

    spacing_ns_m = res_y_deg * m_per_deg_lat    # N-S (latitude direction)
    spacing_ew_m = res_x_deg * m_per_deg_lon    # E-W (longitude direction)

    _field("Raster centre latitude",           f"{centre_lat:.4f} degN")
    _field("Raster centre longitude",          f"{centre_lon:.4f} degE")
    _field("m per degree latitude (approx)",   f"{m_per_deg_lat:.1f} m/deg")
    _field("m per degree longitude (approx)",  f"{m_per_deg_lon:.1f} m/deg  "
           f"[= 111320 x cos({centre_lat:.4f}deg)]")
    print()
    _field("N-S ground spacing (approx)",      f"{spacing_ns_m:.1f} m")
    _field("E-W ground spacing (approx)",      f"{spacing_ew_m:.1f} m")
    print()
    print("  IMPORTANT: These are APPROXIMATIONS at the raster's centre latitude.")
    print("  Actual ground spacing varies across the scene because EPSG:4326")
    print("  is not an equal-area or equidistant projection.")
    print("  Resolution is NOT a uniform 30 m everywhere.")
    print("  Terrain derivatives requiring metric accuracy will use the configured")
    print("  projected analysis CRS (EPSG:32644) -- not the raw degree spacing.")

    # ------------------------------------------------------------------
    # Section 4 -- Suitability statement
    # ------------------------------------------------------------------
    _section("4. SUITABILITY ASSESSMENT")

    print("  SUITABLE FOR:")
    print("    * Pilot-scale terrain screening and decision-support analysis.")
    print("    * Regional identification of candidate hazard-prone terrain zones.")
    print("    * Preliminary slope, aspect, and drainage pattern characterisation.")
    print()
    print("  NOT SUFFICIENT FOR:")
    print("    * Parcel-level engineering design.")
    print("    * Geotechnical site investigation or certification.")
    print("    * Guaranteed site safety determination.")
    print("    * Any use that requires legally certified terrain accuracy.")
    print()
    print("  This DEM provides decision-support terrain input only.")
    print("  Official geotechnical assessment by qualified engineers is")
    print("  required before any infrastructure or relocation decisions.")

    return overall

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    root_dir = Path(__file__).resolve().parent.parent

    print(_sep())
    print("  SIH26191 -- STEP 3B.2: DEM RESOLUTION VALIDATION")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep())

    print(f"\n  Config : configs/project.yaml")
    cfg = load_config(root_dir)
    print("  [OK]    Configuration loaded.")

    passed = validate_resolution(root_dir, cfg)

    print(f"\n{_sep()}")
    print(f"  RESOLUTION VALIDATION: {'PASS' if passed else 'FAIL'}")
    print(_sep())

    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
