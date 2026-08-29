#!/usr/bin/env python3
"""
SIH26191 -- Step 5E: Derive Continuous Flood Exposure Proxy
==============================================================================
Derives a deterministic, continuous terrain-derived flood exposure proxy
from Topographic Wetness Index (TWI) using transparent, configuration-driven
scaling parameters.

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

SCIENTIFIC APPROACH & METHODOLOGY
---------------------------------
1. Physical Basis:
   - Topographic Wetness Index (TWI) integrates both cumulative upslope
     catchment drainage area (a) and local slope gradient (tan(beta)).
   - In rugged Himalayan terrain, high TWI highlights lower-gradient valley
     bottoms, active river corridors (Alaknanda, Mandakini), alluvial fans,
     and convergent drainage hollows where surface runoff naturally converges.
   - Low TWI reflects divergent, steep crests and mountain flanks where runoff
     immediately sheds.

2. Deterministic Monotonic Transformation:
   - Input: Topographic Wetness Index (TWI).
   - Output: Continuous flood exposure proxy score F in [0.0, 1.0].
   - Transformation formula:
         F(TWI) = clip((TWI - twi_min) / (twi_max - twi_min), 0.0, 1.0)
     where:
       twi_min = 3.5 (dry shedding ridges -> score = 0.0)
       twi_max = 13.5 (major channel corridors / confluences -> score = 1.0)
   - The transformation is strictly monotonic: higher TWI never produces
     a lower flood exposure score.
   - NoData pixels from the source DEM are preserved as NaN.

3. Explicit Non-Claims:
   - Score = 0.0 DOES NOT mean "flood safe".
   - Score = 1.0 DOES NOT mean "guaranteed flood inundation".
   - Output DOES NOT represent statistical probability or flood forecast.
   - Output is a relative terrain screening indicator for decision support.

OUTPUT
------
  data/processed/hazards/flood_exposure_proxy.tif

  CRS   : EPSG:32644 (WGS 84 / UTM Zone 44N)
  Unit  : dimensionless normalized screening score [0.0, 1.0]
  Dtype : float32
  NoData: NaN

USAGE
-----
    python processing/hydrology/derive_flood_exposure.py
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
_ROOT_DIR   = _SCRIPT_DIR.parent.parent


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

def load_config() -> dict:
    cfg_path = _ROOT_DIR / "configs" / "project.yaml"
    if not cfg_path.is_file():
        print(f"[FAIL] Config not found: {cfg_path}")
        sys.exit(1)
    with open(cfg_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    if not isinstance(cfg, dict):
        print("[FAIL] Configuration file parsed to non-dict object.")
        sys.exit(1)
    return cfg


# ---------------------------------------------------------------------------
# Core Derivation Logic
# ---------------------------------------------------------------------------

def derive_flood_exposure() -> bool:
    print(_sep("="))
    print("  SIH26191 -- STEP 5E: DERIVE CONTINUOUS FLOOD EXPOSURE PROXY")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    all_passed = True
    cfg = load_config()

    # Read configuration parameters
    hydro_cfg = cfg.get("hydrology", {})
    proxy_cfg = hydro_cfg.get("proxy", {})
    labels_cfg = hydro_cfg.get("labels", {})
    paths_cfg = cfg.get("paths", {})
    crs_cfg = cfg.get("crs", {})

    analysis_crs_str = crs_cfg.get("analysis_crs_metric", "EPSG:32644")
    target_crs = CRS.from_string(analysis_crs_str)

    twi_min = float(proxy_cfg.get("twi_min", 3.5))
    twi_max = float(proxy_cfg.get("twi_max", 13.5))
    transformation = proxy_cfg.get("transformation", "linear_clipped")

    twi_rel = hydro_cfg.get("derivatives", {}).get("topographic_wetness_index", {}).get(
        "output_path", "data/processed/hydrology/topographic_wetness_index.tif"
    )
    proxy_rel = proxy_cfg.get("output_path", "data/processed/hazards/flood_exposure_proxy.tif")

    twi_path = (_ROOT_DIR / twi_rel).resolve()
    output_path = (_ROOT_DIR / proxy_rel).resolve()

    _section("1. METHODOLOGY & CONFIGURATION")
    _field("Methodology Version", hydro_cfg.get("methodology_version", "1.0"))
    _field("Primary Input Derivative", "Topographic Wetness Index (TWI)")
    _field("TWI Min Threshold (twi_min)", f"{twi_min:.2f} -> score = 0.0")
    _field("TWI Max Threshold (twi_max)", f"{twi_max:.2f} -> score = 1.0 (saturation)")
    _field("Transformation Formula", f"score = clip((TWI - {twi_min:.2f}) / ({twi_max:.2f} - {twi_min:.2f}), 0.0, 1.0)")
    _field("Analysis Metric CRS", analysis_crs_str)

    # Verify input existence
    _section("2. READ TWI INPUT & GRID AUDIT")
    if not twi_path.is_file():
        print(f"[FAIL] TWI raster not found: {twi_path}")
        return False
    _field("TWI Input Path", str(twi_path))

    with rasterio.open(twi_path) as twi_src:
        twi_crs = twi_src.crs
        twi_transform = twi_src.transform
        twi_w, twi_h = twi_src.width, twi_src.height
        twi_profile = twi_src.profile.copy()
        twi_nodata = twi_src.nodata
        twi_data = twi_src.read(1)

    all_passed &= _result("TWI CRS matches analysis CRS", twi_crs == target_crs, f"{twi_crs}")

    # 3. Calculate continuous flood exposure proxy
    _section("3. CONTINUOUS PROXY CALCULATION")
    total_pixels = twi_data.size
    nan_mask = np.isnan(twi_data)
    nodata_mask = nan_mask if (twi_nodata is None or np.isnan(twi_nodata)) else (nan_mask | (twi_data == twi_nodata))
    valid_mask = ~nodata_mask
    valid_count = int(np.sum(valid_mask))
    nodata_count = int(np.sum(nodata_mask))

    _field("Total Raster Pixels", f"{total_pixels:,}")
    _field("Valid Terrain Pixels", f"{valid_count:,} ({valid_count/total_pixels*100:.2f}%)")
    _field("NoData Pixels", f"{nodata_count:,} ({nodata_count/total_pixels*100:.2f}%)")

    # Allocate output float32 array initialized to NaN
    proxy_data = np.full(twi_data.shape, np.nan, dtype=np.float32)

    # Compute monotonic normalized score on valid pixels
    valid_twi = twi_data[valid_mask]
    denominator = twi_max - twi_min
    if denominator <= 0:
        print("[FAIL] Invalid TWI threshold configuration: twi_max must be > twi_min")
        return False

    normalized_score = np.clip((valid_twi - twi_min) / denominator, 0.0, 1.0)
    proxy_data[valid_mask] = normalized_score.astype(np.float32)

    # Compute statistics on output proxy
    valid_proxy = proxy_data[valid_mask]
    p_min = float(np.min(valid_proxy))
    p_max = float(np.max(valid_proxy))
    p_mean = float(np.mean(valid_proxy))
    p_std = float(np.std(valid_proxy))

    _field("Calculated Score Range", f"[{p_min:.4f}, {p_max:.4f}]")
    _field("Mean Score", f"{p_mean:.4f}")
    _field("Std Dev Score", f"{p_std:.4f}")

    score_bounds_ok = (p_min >= 0.0) and (p_max <= 1.0)
    no_inf_ok = int(np.sum(np.isinf(proxy_data))) == 0
    all_passed &= _result("Score values strictly within [0.0, 1.0]", score_bounds_ok, f"min={p_min:.4f}, max={p_max:.4f}")
    all_passed &= _result("No infinite values in output", no_inf_ok)
    all_passed &= _result("Valid pixel count matches TWI input", int(np.sum(~np.isnan(proxy_data))) == valid_count)

    # 4. Save GeoTIFF output
    _section("4. WRITE GEOTIFF OUTPUT")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    _field("Output Destination", str(output_path))

    out_profile = twi_profile.copy()
    out_profile.update({
        "driver": "GTiff",
        "dtype": "float32",
        "nodata": np.nan,
        "width": twi_w,
        "height": twi_h,
        "count": 1,
        "crs": target_crs,
        "transform": twi_transform,
        "compress": "lzw",
        "tiled": False
    })

    try:
        with rasterio.open(output_path, "w", **out_profile) as dst:
            dst.write(proxy_data, 1)
            dst.set_band_description(1, "Terrain-Derived Flood Exposure Proxy (Normalized Score 0.0-1.0)")
            dst.update_tags(
                TITLE="Terrain-Derived Flood Exposure Proxy",
                PROJECT_ID="SIH26191",
                PILOT_DISTRICT="Rudraprayag",
                STATE="Uttarakhand",
                METHODOLOGY="Deterministic Monotonic TWI Normalization",
                TWI_MIN=str(twi_min),
                TWI_MAX=str(twi_max),
                TRANSFORMATION="linear_clipped",
                DISCLAIMER=labels_cfg.get("disclaimer", "Decision Support Layer Only")
            )
        all_passed &= _result("GeoTIFF written successfully", output_path.is_file(),
                              f"Size: {output_path.stat().st_size / (1024*1024):.2f} MB")
    except Exception as e:
        print(f"[FAIL] Failed to write GeoTIFF: {e}")
        all_passed = False

    # Summary
    print(f"\n{_sep('=')}")
    if all_passed:
        print("FLOOD EXPOSURE PROXY DERIVATION: PASS")
    else:
        print("FLOOD EXPOSURE PROXY DERIVATION: FAIL")
    print(_sep('='))

    return all_passed


if __name__ == "__main__":
    success = derive_flood_exposure()
    sys.exit(0 if success else 1)
