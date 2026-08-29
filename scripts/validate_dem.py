#!/usr/bin/env python3
"""
SIH26191 -- Step 3B.4: Final DEM Validation Summary
==============================================================================
Consolidated end-to-end DEM validation covering:
  DATASET   : file existence, readability, driver, band count
  SPATIAL   : CRS validity, config match, analysis CRS strategy
  RESOLUTION: pixel resolution validity, approximate ground spacing
  QUALITY   : valid pixels, NoData, NaN, Inf, elevation statistics

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

IMPORTANT DISTINCTION
---------------------
A PASS from this script means:

  "Technically valid for pilot-scale terrain screening
   and decision-support analysis."

It does NOT mean:

  "Engineering-certified terrain assessment."
  "Guaranteed-safe site conditions."
  "Legally certified spatial accuracy."

All outputs from downstream processing using this DEM must carry the same
distinction in their documentation and user-facing reporting.

USAGE
-----
    python scripts/validate_dem.py
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
    import numpy as np
    import rasterio
except ImportError as e:
    print(f"[ERROR] Required package not installed: {e}")
    sys.exit(1)

try:
    from pyproj import CRS as ProjCRS
    _PYPROJ = True
except ImportError:
    _PYPROJ = False

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _sep(char="=", width=66):
    return char * width

def _section(title):
    print(f"\n{_sep('-')}")
    print(f"  {title}")
    print(_sep('-'))

def _field(label, value, width=32):
    print(f"  {label:<{width}}: {value}")

def _result(label, ok, detail=""):
    tag = "[PASS]" if ok else "[FAIL]"
    msg = f"  {tag}  {label}"
    if detail:
        msg += f"  ({detail})"
    print(msg)
    return ok

# ---------------------------------------------------------------------------
# Config helpers
# ---------------------------------------------------------------------------

def load_config(root_dir: Path) -> dict:
    cfg_path = root_dir / "configs" / "project.yaml"
    if not cfg_path.is_file():
        print(f"[FAIL] Config not found: {cfg_path}")
        sys.exit(1)
    with open(cfg_path, encoding="utf-8") as fh:
        return yaml.safe_load(fh)

def _get(cfg, *keys):
    node = cfg
    for k in keys:
        if not isinstance(node, dict) or k not in node:
            return None
        node = node[k]
    return node

# ---------------------------------------------------------------------------
# Ground-spacing helper (same formula as validate_dem_resolution.py)
# ---------------------------------------------------------------------------
_M_PER_DEG_LAT = 111_320.0

def _m_per_deg_lon(lat_deg):
    return _M_PER_DEG_LAT * math.cos(math.radians(lat_deg))

# ---------------------------------------------------------------------------
# Main validation
# ---------------------------------------------------------------------------

def run_validation(root_dir: Path, cfg: dict) -> bool:
    overall = True

    dem_rel          = _get(cfg, "paths", "dem_raw")
    storage_crs_str  = _get(cfg, "crs", "storage_crs")
    analysis_crs_str = _get(cfg, "crs", "analysis_crs_metric")

    if not dem_rel:
        print("[FAIL] paths.dem_raw missing from project.yaml")
        sys.exit(1)

    dem_path = root_dir / dem_rel

    # ==================================================================
    # SECTION A -- DATASET
    # ==================================================================
    _section("A. DATASET CHECKS")

    file_ok = dem_path.is_file()
    _field("DEM path", dem_path)
    overall &= _result("File exists", file_ok)
    if not file_ok:
        return False

    try:
        with rasterio.open(dem_path) as src:
            driver     = src.driver
            crs        = src.crs
            width      = src.width
            height     = src.height
            n_bands    = src.count
            transform  = src.transform
            bounds     = src.bounds
            nodata     = src.nodata
            dtype      = src.dtypes[0]
            band_data  = src.read(1).astype(np.float64)
        raster_ok = True
    except Exception as e:
        print(f"  [FAIL] Cannot open raster: {e}")
        return False

    overall &= _result("Raster readable by rasterio", raster_ok)
    overall &= _result("GeoTIFF driver", driver == "GTiff", f"driver={driver}")
    overall &= _result("Band count is 1", n_bands == 1, f"bands={n_bands}")

    _field("Driver",    driver)
    _field("Bands",     n_bands)
    _field("Dtype",     dtype)
    _field("Width px",  width)
    _field("Height px", height)

    # ==================================================================
    # SECTION B -- SPATIAL / CRS
    # ==================================================================
    _section("B. SPATIAL / CRS CHECKS")

    has_crs = crs is not None
    overall &= _result("DEM has embedded CRS", has_crs)

    if has_crs:
        actual_epsg = crs.to_epsg()
        actual_str  = f"EPSG:{actual_epsg}" if actual_epsg else str(crs)
        _field("Actual DEM CRS",      actual_str)
        _field("Config storage CRS",  storage_crs_str or "NOT SET")
        _field("Config analysis CRS", analysis_crs_str or "NOT SET")

        # Match actual vs configured storage CRS
        try:
            cfg_epsg = int(str(storage_crs_str).upper().replace("EPSG:", ""))
            match    = (actual_epsg == cfg_epsg)
        except Exception:
            match = str(actual_str).upper() == str(storage_crs_str).upper()
        overall &= _result(
            "DEM CRS matches configured storage CRS", match,
            f"actual={actual_str}, config={storage_crs_str}",
        )

        # Analysis CRS strategy validity
        if _PYPROJ and storage_crs_str and analysis_crs_str:
            try:
                ps = ProjCRS.from_user_input(storage_crs_str)
                pa = ProjCRS.from_user_input(analysis_crs_str)
                overall &= _result("Storage CRS is geographic", ps.is_geographic)
                overall &= _result("Analysis CRS is projected",  pa.is_projected)
                axes = pa.axis_info
                units = [ax.unit_name.lower() for ax in axes]
                is_metric = any("metre" in u or "meter" in u for u in units)
                overall &= _result(
                    "Analysis CRS uses metric units",
                    is_metric, f"units={units}",
                )
            except Exception as e:
                overall &= _result("CRS type analysis (pyproj)", False, str(e))
        elif not _PYPROJ:
            print("  [SKIP] pyproj not installed -- CRS type checks skipped.")

    # ==================================================================
    # SECTION C -- RESOLUTION
    # ==================================================================
    _section("C. RESOLUTION CHECKS")

    res_x = abs(transform.a)
    res_y = abs(transform.e)
    _field("X pixel (deg)", f"{res_x:.8f}")
    _field("Y pixel (deg)", f"{res_y:.8f}")

    res_ok = (res_x > 0) and (res_y > 0)
    overall &= _result("Pixel resolution non-zero", res_ok)

    if res_x > 0 and res_y > 0:
        ratio = res_x / res_y
        overall &= _result("Square pixels (X ~= Y)", abs(ratio - 1.0) < 0.001,
                           f"ratio={ratio:.6f}")

        centre_lat = (bounds.bottom + bounds.top) / 2.0
        sp_ns = res_y * _M_PER_DEG_LAT
        sp_ew = res_x * _m_per_deg_lon(centre_lat)
        _field("Approx N-S spacing", f"{sp_ns:.1f} m  (at centre lat {centre_lat:.2f}deg)")
        _field("Approx E-W spacing", f"{sp_ew:.1f} m  (at centre lat {centre_lat:.2f}deg)")
        print("  NOTE: Spacing varies across scene -- not uniform 30 m everywhere.")

    # ==================================================================
    # SECTION D -- DATA QUALITY
    # ==================================================================
    _section("D. DATA QUALITY CHECKS")

    nan_mask    = np.isnan(band_data)
    inf_mask    = np.isinf(band_data)
    if nodata is not None and not np.isnan(float(nodata if nodata is not None else 0)):
        nodata_mask = (band_data == float(nodata))
    else:
        nodata_mask = nan_mask.copy() if (nodata is not None and np.isnan(nodata)) \
                      else np.zeros_like(band_data, dtype=bool)

    invalid_mask = nodata_mask | nan_mask | inf_mask
    valid_mask   = ~invalid_mask
    valid_px     = band_data[valid_mask]

    n_total  = band_data.size
    n_valid  = int(valid_mask.sum())
    n_nodata = int(nodata_mask.sum())
    n_nan    = int(nan_mask.sum())
    n_inf    = int(inf_mask.sum())

    _field("Total pixels",  f"{n_total:,}")
    _field("Valid pixels",  f"{n_valid:,}")
    _field("NoData pixels", f"{n_nodata:,}")
    _field("NaN pixels",    f"{n_nan:,}")
    _field("Inf pixels",    f"{n_inf:,}")

    overall &= _result("Has valid pixels", n_valid > 0)
    overall &= _result("No NaN values",    n_nan == 0, f"count={n_nan}" if n_nan else "")
    overall &= _result("No Inf values",    n_inf == 0, f"count={n_inf}" if n_inf else "")

    if n_valid > 0:
        _field("Min elevation", f"{valid_px.min():.2f} m")
        _field("Max elevation", f"{valid_px.max():.2f} m")
        _field("Mean elevation",f"{valid_px.mean():.2f} m")

    # ==================================================================
    # SECTION E -- SUITABILITY STATEMENT
    # ==================================================================
    _section("E. SUITABILITY STATEMENT")

    print("  A PASS from this validation means:")
    print()
    print("    'Technically valid for pilot-scale terrain screening")
    print("     and decision-support analysis.'")
    print()
    print("  It does NOT mean:")
    print()
    print("    'Engineering-certified or guaranteed-safe terrain assessment.'")
    print("    'Legally certified spatial accuracy.'")
    print("    'Sufficient for parcel-level infrastructure design.'")
    print()
    print("  All downstream terrain products derived from this DEM must carry")
    print("  the same qualification in documentation and user-facing output.")

    return overall

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    root_dir = Path(__file__).resolve().parent.parent

    print(_sep())
    print("  SIH26191 -- STEP 3B.4: FINAL DEM VALIDATION SUMMARY")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep())

    print("\n  Config : configs/project.yaml")
    cfg = load_config(root_dir)
    print("  [OK]    Configuration loaded.")

    passed = run_validation(root_dir, cfg)

    print(f"\n{_sep()}")
    if passed:
        print("  DEM VALIDATION: PASS")
        print("  (Technically valid for pilot-scale terrain screening)")
    else:
        print("  DEM VALIDATION: FAIL")
    print(_sep())

    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
