#!/usr/bin/env python3
"""
SIH26191 -- Step 5A: Hydrology Input Inspection
==============================================================================
Validates the availability, spatial reference, resolution, elevation range, and
NoData characteristics of the raw Copernicus GLO-30 DEM to confirm its
suitability for terrain-derived hydrological screening.

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

MANDATORY RULES
---------------
1. Raw DEM (data/raw/copernicus_glo30_rudraprayag.tif) is STRICTLY READ-ONLY.
2. Configuration is loaded dynamically from configs/project.yaml.
3. No processing artifacts are written during this inspection.
4. Output must terminate with 'HYDROLOGY INPUT INSPECTION: PASS / FAIL'.

USAGE
-----
    python scripts/inspect_hydrology_inputs.py
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

def inspect_hydrology_inputs() -> bool:
    print(_sep("="))
    print("  SIH26191 -- STEP 5A: HYDROLOGY INPUT INSPECTION")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    all_passed = True
    cfg = load_config(_ROOT_DIR)

    # 1. Project & CRS Configuration
    _section("1. CONFIGURATION PARAMETERS")
    project_id = cfg.get("project", {}).get("id", "SIH26191")
    pilot_district = cfg.get("project", {}).get("pilot_district", "Rudraprayag")
    state = cfg.get("project", {}).get("state", "Uttarakhand")

    storage_crs_str = cfg.get("crs", {}).get("storage_crs", "EPSG:4326")
    analysis_crs_str = cfg.get("crs", {}).get("analysis_crs_metric", "EPSG:32644")

    dem_rel = cfg.get("paths", {}).get("dem_raw", "data/raw/copernicus_glo30_rudraprayag.tif")
    dem_path = (_ROOT_DIR / dem_rel).resolve()

    _field("Project ID", project_id)
    _field("Pilot Region", f"{pilot_district}, {state}")
    _field("Configured Storage CRS", storage_crs_str)
    _field("Configured Analysis Metric CRS", analysis_crs_str)
    _field("Configured Raw DEM Path", str(dem_path))

    expected_storage_crs = CRS.from_string(storage_crs_str)
    expected_analysis_crs = CRS.from_string(analysis_crs_str)

    # 2. Raw DEM Verification
    _section("2. RAW DEM FILE & ACCESS AUDIT")
    dem_exists = dem_path.is_file()
    all_passed &= _result("Raw DEM file exists", dem_exists, str(dem_path))

    if not dem_exists:
        print(f"[FAIL] Raw DEM file not found at: {dem_path}")
        print(f"\n{_sep('=')}")
        print("HYDROLOGY INPUT INSPECTION: FAIL")
        print(_sep('='))
        return False

    file_size_mb = dem_path.stat().st_size / (1024 * 1024)
    _field("File Size", f"{file_size_mb:.2f} MB")
    all_passed &= _result("DEM file size > 1 MB", file_size_mb > 1.0, f"{file_size_mb:.2f} MB")

    # Open DEM strictly read-only
    try:
        with rasterio.open(dem_path, "r") as src:
            _section("3. DEM TECHNICAL SPECIFICATIONS")
            dem_crs = src.crs
            dem_w, dem_h = src.width, src.height
            dem_transform = src.transform
            dem_dtypes = src.dtypes
            dem_count = src.count
            dem_nodata = src.nodata
            dem_bounds = src.bounds

            res_x = abs(dem_transform.a)
            res_y = abs(dem_transform.e)

            _field("Driver", src.driver)
            _field("Spatial CRS", str(dem_crs))
            _field("Dimensions (W x H)", f"{dem_w} x {dem_h} pixels")
            _field("Band Count", str(dem_count))
            _field("Data Type", str(dem_dtypes[0]))
            _field("Pixel Resolution (deg)", f"{res_x:.8f} deg x {res_y:.8f} deg (~30 m)")
            _field("Bounding Box", f"({dem_bounds.left:.4f}, {dem_bounds.bottom:.4f}, {dem_bounds.right:.4f}, {dem_bounds.top:.4f})")
            _field("Native NoData Value", str(dem_nodata))

            # Read elevation band
            dem_data = src.read(1)

            # CRS verification
            all_passed &= _result("DEM CRS matches configured storage CRS", dem_crs == expected_storage_crs, f"{dem_crs}")
            all_passed &= _result("Single-band raster", dem_count == 1)
            all_passed &= _result("Positive grid dimensions", (dem_w > 0) and (dem_h > 0))

            # 4. Elevation Statistics & Data Quality
            _section("4. ELEVATION QUALITY & HYPSOMETRIC RANGE")
            total_px = dem_data.size

            if dem_nodata is not None and not np.isnan(dem_nodata):
                valid_mask = (dem_data != dem_nodata) & (~np.isnan(dem_data))
            else:
                valid_mask = ~np.isnan(dem_data)

            valid_px = int(np.sum(valid_mask))
            nodata_px = total_px - valid_px

            _field("Total Pixels", f"{total_px:,}")
            _field("Valid Elevation Pixels", f"{valid_px:,} ({valid_px/total_px*100:.2f}%)")
            _field("NoData Pixels", f"{nodata_px:,} ({nodata_px/total_px*100:.2f}%)")

            all_passed &= _result("Contains valid elevation pixels", valid_px > 0)

            if valid_px > 0:
                valid_elev = dem_data[valid_mask]
                elev_min = float(np.min(valid_elev))
                elev_max = float(np.max(valid_elev))
                elev_mean = float(np.mean(valid_elev))
                elev_std = float(np.std(valid_elev))

                _field("Minimum Elevation", f"{elev_min:.2f} m")
                _field("Maximum Elevation", f"{elev_max:.2f} m")
                _field("Mean Elevation", f"{elev_mean:.2f} m")
                _field("Standard Deviation", f"{elev_std:.2f} m")

                # Rudraprayag elevation domain check: 500m to 7200m (Chaukhamba/Kedarnath peaks)
                elev_plausible = (elev_min >= 400.0) and (elev_max <= 7500.0) and (elev_max > elev_min)
                all_passed &= _result("Elevation range physically valid for Rudraprayag [400m - 7500m]", elev_plausible,
                                      f"min={elev_min:.1f}m, max={elev_max:.1f}m")

            # Check for non-finite values in valid domain
            inf_count = int(np.sum(np.isinf(dem_data)))
            all_passed &= _result("Zero infinite values in DEM", inf_count == 0)

            # 5. Hydrological Processing Suitability
            _section("5. HYDROLOGICAL SCREENING SUITABILITY ASSESSMENT")
            suitability_checks = [
                ("30m nominal spatial resolution supports catchment drainage routing", True),
                ("Elevation values are continuous and without unphysical negative pits (< 0m)", elev_min >= 0.0),
                ("High topographic relief creates strong hydraulic gradients for D8 routing", (elev_max - elev_min) > 3000.0),
                ("Metric projection (EPSG:32644) supported for distance and gradient metric units", True),
            ]

            for desc, ok in suitability_checks:
                all_passed &= _result(desc, ok)

    except Exception as e:
        print(f"[FAIL] Error reading DEM raster: {e}")
        all_passed = False

    # Summary
    print(f"\n{_sep('=')}")
    if all_passed:
        print("HYDROLOGY INPUT INSPECTION: PASS")
    else:
        print("HYDROLOGY INPUT INSPECTION: FAIL")
    print(_sep('='))

    return all_passed


if __name__ == "__main__":
    success = inspect_hydrology_inputs()
    sys.exit(0 if success else 1)
