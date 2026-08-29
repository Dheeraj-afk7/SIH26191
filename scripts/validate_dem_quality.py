#!/usr/bin/env python3
"""
SIH26191 -- Step 3B.3: DEM Data Quality Validation
==============================================================================
Inspects the raw DEM raster for data integrity issues:
  - Pixel counts (total, valid, NoData, NaN, infinite)
  - Elevation statistics (min, max, mean)
  - Detection of clearly invalid numeric values

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

DESIGN PRINCIPLES
-----------------
  * No arbitrary "acceptable elevation limits" are invented.
  * Suspicious values are REPORTED as observations, not silently failed against
    hardcoded thresholds.  Himalayan terrain legitimately spans a very wide
    elevation range; the script does not assume a narrow band is "valid".
  * PASS/FAIL is based on data integrity only:
      - Can the file be opened?
      - Does it contain at least one valid pixel?
      - Are there structurally invalid values (NaN / Inf) that would break
        downstream calculations?
  * The DEM is opened in read-only mode.  Nothing is written.

USAGE
-----
    python scripts/validate_dem_quality.py
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
except ImportError as e:
    print(f"[ERROR] Required package not installed: {e}")
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

def _field(label, value, width=34):
    print(f"  {label:<{width}}: {value}")

def _result(label, ok, detail=""):
    tag = "[PASS]" if ok else "[FAIL]"
    line = f"  {tag}  {label}"
    if detail:
        line += f"  ({detail})"
    print(line)
    return ok

def _obs(label, value, width=34):
    """Print an observation (non-pass/fail informational line)."""
    print(f"  [OBS]  {label:<{width}}: {value}")

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
# Core quality validation
# ---------------------------------------------------------------------------

def validate_quality(root_dir: Path, cfg: dict) -> bool:
    overall = True

    try:
        dem_rel = cfg["paths"]["dem_raw"]
    except (KeyError, TypeError):
        print("[FAIL] paths.dem_raw missing from project.yaml")
        sys.exit(1)

    dem_path = root_dir / dem_rel

    # ------------------------------------------------------------------
    # Section 1 -- File accessibility
    # ------------------------------------------------------------------
    _section("1. FILE ACCESSIBILITY")

    file_ok = dem_path.is_file()
    _field("DEM path", dem_path)
    overall &= _result("DEM file exists on disk", file_ok)
    if not file_ok:
        return False

    # ------------------------------------------------------------------
    # Section 2 -- Raster read & band data
    # ------------------------------------------------------------------
    _section("2. RASTER READ  (read-only, band 1)")

    try:
        with rasterio.open(dem_path) as src:
            nodata    = src.nodata
            dtype     = src.dtypes[0]
            n_bands   = src.count
            width     = src.width
            height    = src.height
            band_data = src.read(1).astype(np.float64)  # cast for safe NaN/math ops
    except Exception as e:
        print(f"  [FAIL] Cannot open DEM: {e}")
        return False

    overall &= _result("DEM opened successfully with rasterio", True)

    _field("Data type (raw)",  dtype)
    _field("Band count",       n_bands)
    _field("Raster dimensions",f"{width} x {height} px")
    _field("NoData value",     nodata if nodata is not None else "Not set")

    # ------------------------------------------------------------------
    # Section 3 -- Pixel counts
    # ------------------------------------------------------------------
    _section("3. PIXEL COUNT ANALYSIS")

    total_pixels = band_data.size

    # Build masks for each pixel category
    nan_mask  = np.isnan(band_data)
    inf_mask  = np.isinf(band_data)

    # NoData mask -- handles both set and unset NoData
    if nodata is not None:
        if np.isnan(nodata):
            nodata_mask = nan_mask.copy()
        else:
            nodata_mask = (band_data == float(nodata))
    else:
        nodata_mask = np.zeros_like(band_data, dtype=bool)

    # "Valid" = not NoData AND not NaN AND not Inf
    invalid_mask  = nodata_mask | nan_mask | inf_mask
    valid_mask    = ~invalid_mask
    valid_pixels  = band_data[valid_mask]

    n_total   = total_pixels
    n_valid   = int(valid_mask.sum())
    n_nodata  = int(nodata_mask.sum())
    n_nan     = int(nan_mask.sum())
    n_inf     = int(inf_mask.sum())
    n_invalid = int(invalid_mask.sum())

    _field("Total pixels",         f"{n_total:,}")
    _field("Valid pixels",         f"{n_valid:,}")
    _field("NoData pixels",        f"{n_nodata:,}")
    _field("NaN pixels",           f"{n_nan:,}")
    _field("Infinite value pixels",f"{n_inf:,}")

    valid_pct = (n_valid / n_total * 100) if n_total > 0 else 0.0
    _field("Valid pixel coverage", f"{valid_pct:.2f} %")

    # Integrity checks
    has_valid = n_valid > 0
    overall &= _result("At least one valid pixel exists", has_valid)

    no_nan = n_nan == 0
    overall &= _result(
        "No NaN values in pixel data",
        no_nan,
        f"NaN count={n_nan}" if not no_nan else "",
    )

    no_inf = n_inf == 0
    overall &= _result(
        "No infinite values in pixel data",
        no_inf,
        f"Inf count={n_inf}" if not no_inf else "",
    )

    # ------------------------------------------------------------------
    # Section 4 -- Elevation statistics (valid pixels only)
    # ------------------------------------------------------------------
    _section("4. ELEVATION STATISTICS  (valid pixels only)")

    if n_valid == 0:
        print("  [SKIP] No valid pixels -- statistics cannot be computed.")
    else:
        elev_min  = float(valid_pixels.min())
        elev_max  = float(valid_pixels.max())
        elev_mean = float(valid_pixels.mean())
        elev_std  = float(valid_pixels.std())

        _field("Minimum elevation", f"{elev_min:.2f} m")
        _field("Maximum elevation", f"{elev_max:.2f} m")
        _field("Mean elevation",    f"{elev_mean:.2f} m")
        _field("Std dev elevation", f"{elev_std:.2f} m")
        _field("Elevation range",   f"{elev_max - elev_min:.2f} m")

        # ------------------------------------------------------------------
        # Observations (no arbitrary pass/fail thresholds)
        # ------------------------------------------------------------------
        _section("5. OBSERVATIONS  (informational -- not pass/fail thresholds)")

        print("  NOTE: Himalayan terrain spans extreme elevation ranges.")
        print("  No arbitrary upper/lower elevation limits are applied.")
        print("  The observations below are reported for review only.")
        print()

        # Negative elevations -- unusual for Himalayan terrain; worth noting
        n_negative = int((valid_pixels < 0).sum())
        if n_negative > 0:
            _obs("Pixels below 0 m (sea level)", f"{n_negative:,}  ← OBSERVATION: review if expected")
        else:
            _obs("Pixels below 0 m (sea level)", "0  (none)")

        # Unusually high values -- GLO-30 top of world ~8849 m (Everest)
        # Rudraprayag region max peaks around 6500-7000 m
        # Reported as observation, not hard fail
        n_above_9000 = int((valid_pixels > 9000).sum())
        if n_above_9000 > 0:
            _obs("Pixels > 9000 m", f"{n_above_9000:,}  ← OBSERVATION: exceeds Earth max; review")
        else:
            _obs("Pixels > 9000 m", "0  (none above Earth maximum)")

        # Observed elevation context note
        print()
        print("  Rudraprayag district context for reference:")
        print("  Expected approximate range: ~500 m (valleys) to ~7000 m (high peaks).")
        print("  Values outside this range are observations, not automatic failures.")
        print(f"  Observed range: {elev_min:.1f} m -- {elev_max:.1f} m  (see above).")

    return overall

# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    root_dir = Path(__file__).resolve().parent.parent

    print(_sep())
    print("  SIH26191 -- STEP 3B.3: DEM DATA QUALITY VALIDATION")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep())

    print("\n  Config : configs/project.yaml")
    cfg = load_config(root_dir)
    print("  [OK]    Configuration loaded.")

    passed = validate_quality(root_dir, cfg)

    print(f"\n{_sep()}")
    print(f"  DATA QUALITY VALIDATION: {'PASS' if passed else 'FAIL'}")
    print(_sep())

    if not passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
