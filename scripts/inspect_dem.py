#!/usr/bin/env python3
"""
SIH26191 — Step 3A: DEM Technical Inspection
==============================================================================
Programmatic technical inspection of the raw DEM raster.

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

PURPOSE
-------
This script performs a READ-ONLY technical audit of the DEM file defined in
configs/project.yaml (paths.dem_raw).  It prints raster metadata and basic
elevation statistics so that the pipeline team can confirm the DEM is usable
before any terrain-derivative calculations begin.

SCOPE
-----
  * Inspection ONLY — no raster is written, modified, or reprojected.
  * DEM path is read dynamically from project.yaml; nothing is hardcoded.
  * NoData pixels are excluded from the statistical calculations.

USAGE
-----
    python scripts/inspect_dem.py
"""

import sys
import numpy as np
from pathlib import Path

# ---------------------------------------------------------------------------
# Third-party imports — fail early with a clear message if missing
# ---------------------------------------------------------------------------
try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML is not installed.  Run:  pip install pyyaml")
    sys.exit(1)

try:
    import rasterio
except ImportError:
    print("[ERROR] rasterio is not installed.  Run:  pip install rasterio")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------

def _separator(char: str = "=", width: int = 66) -> str:
    """Return a horizontal separator line."""
    return char * width


def _section(title: str) -> None:
    """Print a clearly delimited section header."""
    print(f"\n{_separator('-')}")
    print(f"  {title}")
    print(_separator('-'))


def _field(label: str, value, width: int = 28) -> None:
    """Print a labelled field in a consistent format."""
    print(f"  {label:<{width}}: {value}")


# ---------------------------------------------------------------------------
# Core inspection logic
# ---------------------------------------------------------------------------

def load_config(root_dir: Path) -> dict:
    """Load and parse configs/project.yaml relative to the project root."""
    config_path = root_dir / "configs" / "project.yaml"
    if not config_path.is_file():
        print(f"[FAIL] Configuration file not found: {config_path}")
        sys.exit(1)
    with open(config_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if not isinstance(cfg, dict):
        print("[FAIL] Configuration file parsed to a non-dict object.")
        sys.exit(1)
    return cfg


def get_dem_path(cfg: dict, root_dir: Path) -> Path:
    """Extract paths.dem_raw from the config and resolve it to an absolute path."""
    try:
        dem_rel = cfg["paths"]["dem_raw"]
    except (KeyError, TypeError):
        print("[FAIL] 'paths.dem_raw' is missing from configs/project.yaml.")
        sys.exit(1)

    if not dem_rel or str(dem_rel).strip() == "":
        print("[FAIL] 'paths.dem_raw' is empty in configs/project.yaml.")
        sys.exit(1)

    return root_dir / dem_rel


def inspect_dem(dem_path: Path) -> bool:
    """
    Open the DEM with rasterio and print a full technical inspection report.

    Returns
    -------
    bool
        True  -> inspection passed (DEM is readable and has valid data).
        False -> inspection failed.
    """
    passed = True

    # ------------------------------------------------------------------
    # Section 1 — File-level checks
    # ------------------------------------------------------------------
    _section("1. FILE INFORMATION")

    _field("DEM file path", dem_path)
    file_exists = dem_path.exists() and dem_path.is_file()
    _field("File exists", file_exists)

    if not file_exists:
        print(f"\n[FAIL] DEM file does not exist: {dem_path}")
        return False

    file_size_mb = dem_path.stat().st_size / (1024 ** 2)
    _field("File size", f"{file_size_mb:.2f} MB")

    # ------------------------------------------------------------------
    # Section 2 — Rasterio metadata inspection
    # ------------------------------------------------------------------
    _section("2. RASTER METADATA")

    try:
        with rasterio.open(dem_path) as src:
            driver     = src.driver
            crs        = src.crs
            width      = src.width
            height     = src.height
            band_count = src.count
            dtype      = src.dtypes[0]          # dtype of band 1
            transform  = src.transform
            bounds     = src.bounds
            nodata     = src.nodata

            # Pixel resolution (absolute value handles south-up rasters)
            res_x = abs(transform.a)
            res_y = abs(transform.e)

            _field("Raster driver",   driver)
            _field("CRS",             crs)
            _field("Width (pixels)",  width)
            _field("Height (pixels)", height)
            _field("Number of bands", band_count)
            _field("Data type",       dtype)
            _field("Pixel resolution",
                   f"X={res_x:.6f}, Y={res_y:.6f}  (CRS units)")
            _field("West bound",  f"{bounds.left:.6f}")
            _field("East bound",  f"{bounds.right:.6f}")
            _field("South bound", f"{bounds.bottom:.6f}")
            _field("North bound", f"{bounds.top:.6f}")
            _field("NoData value", nodata if nodata is not None else "Not set")

            # ------------------------------------------------------------------
            # Basic sanity checks on metadata
            # ------------------------------------------------------------------
            if crs is None:
                print("\n  [WARN] No CRS is defined in the raster file.")
                passed = False
            if width <= 0 or height <= 0:
                print("\n  [FAIL] Invalid raster dimensions.")
                passed = False
            if band_count < 1:
                print("\n  [FAIL] Raster has no bands.")
                passed = False

            # ------------------------------------------------------------------
            # Section 3 — Elevation statistics (band 1, valid pixels only)
            # ------------------------------------------------------------------
            _section("3. ELEVATION STATISTICS  (Band 1 — valid pixels only)")

            band_data = src.read(1).astype(np.float64)   # read as float for math

            # Mask NoData pixels safely
            if nodata is not None:
                if np.isnan(nodata):
                    valid_mask = ~np.isnan(band_data)
                else:
                    valid_mask = band_data != nodata
            else:
                # No NoData defined — treat NaN as invalid just in case
                valid_mask = ~np.isnan(band_data)

            valid_pixels = band_data[valid_mask]

            if valid_pixels.size == 0:
                print("\n  [FAIL] No valid (non-NoData) pixels found in the DEM.")
                passed = False
            else:
                total_pixels = band_data.size
                valid_count  = valid_pixels.size
                nodata_count = total_pixels - valid_count

                _field("Total pixels",       f"{total_pixels:,}")
                _field("Valid pixels",        f"{valid_count:,}")
                _field("NoData pixels",       f"{nodata_count:,}")
                _field("Minimum elevation",   f"{valid_pixels.min():.2f} m")
                _field("Maximum elevation",   f"{valid_pixels.max():.2f} m")
                _field("Mean elevation",      f"{valid_pixels.mean():.2f} m")

    except rasterio.errors.RasterioIOError as e:
        print(f"\n[FAIL] rasterio could not open the DEM: {e}")
        return False
    except Exception as e:
        print(f"\n[FAIL] Unexpected error during DEM inspection: {e}")
        return False

    return passed


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    # Derive the project root from this script's location
    # (scripts/ is one level below the project root)
    root_dir = Path(__file__).resolve().parent.parent

    print(_separator("="))
    print("  SIH26191 — STEP 3A: DEM TECHNICAL INSPECTION")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_separator("="))

    # 1. Load project config
    print(f"\n  Config : configs/project.yaml")
    cfg = load_config(root_dir)
    print("  [OK]    Configuration loaded successfully.")

    # 2. Resolve the DEM path from config
    dem_path = get_dem_path(cfg, root_dir)
    print(f"  [OK]    DEM path resolved from paths.dem_raw.")

    # 3. Run the full inspection
    passed = inspect_dem(dem_path)

    # ------------------------------------------------------------------
    # Final verdict
    # ------------------------------------------------------------------
    print(f"\n{_separator('=')}")
    if passed:
        print("  DEM INSPECTION: PASS")
    else:
        print("  DEM INSPECTION: FAIL")
    print(_separator("="))

    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
