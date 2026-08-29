#!/usr/bin/env python3
"""
SIH26191 -- Step 4D: Derive Continuous Terrain Susceptibility Proxy
==============================================================================
Derives a deterministic, continuous terrain-derived landslide susceptibility proxy
from metric slope angle using transparent, configuration-driven parameters.

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

SCIENTIFIC APPROACH & METHODOLOGY
---------------------------------
1. Physical Basis:
   - Topographic slope angle is the primary physical predisposing terrain factor
     governing gravitational shear stress on hillside slopes.
   - Steeper slopes experience higher gravitational driving forces, increasing
     predisposition to mass wasting and slope failure.
   - Aspect is tracked contextually without arbitrary hazard weighting.

2. Deterministic Monotonic Transformation:
   - Input: Slope angle in degrees theta in [0deg, 90deg].
   - Output: Continuous terrain susceptibility proxy S in [0.0, 1.0].
   - Transformation formula:
         S(theta) = clip((theta - theta_min) / (theta_max - theta_min), 0.0, 1.0)
     where:
       theta_min = 0.0 deg (baseline flat terrain -> S = 0.0)
       theta_max = 60.0 deg (saturation angle -> S = 1.0)
   - The transformation is strictly monotonic: higher slope never produces
     a lower susceptibility score.
   - NoData pixels from the source DEM are preserved as NaN.

3. Explicit Non-Claims:
   - Score = 0.0 DOES NOT mean "safe terrain".
   - Score = 1.0 DOES NOT mean "certain landslide".
   - Output DOES NOT represent statistical probability or landslide prediction.
   - Output is a relative terrain screening indicator for decision support.

OUTPUT
------
  data/processed/hazards/terrain_susceptibility_proxy.tif

  CRS   : EPSG:32644 (WGS 84 / UTM Zone 44N)
  Unit  : dimensionless normalized screening score [0.0, 1.0]
  Dtype : float32
  NoData: NaN

USAGE
-----
    python processing/hazards/derive_terrain_susceptibility.py
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

def derive_terrain_susceptibility() -> bool:
    print(_sep("="))
    print("  SIH26191 -- STEP 4D: DERIVE CONTINUOUS TERRAIN SUSCEPTIBILITY PROXY")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    all_passed = True
    cfg = load_config()

    # Read configuration parameters
    suscept_cfg = cfg.get("terrain_susceptibility", {})
    slope_cfg = suscept_cfg.get("slope", {})
    aspect_cfg = suscept_cfg.get("aspect", {})
    output_cfg = suscept_cfg.get("output", {})
    paths_cfg = cfg.get("paths", {})
    crs_cfg = cfg.get("crs", {})

    analysis_crs_str = crs_cfg.get("analysis_crs_metric", "EPSG:32644")
    target_crs = CRS.from_string(analysis_crs_str)

    min_slope_deg = float(slope_cfg.get("min_slope_deg", 0.0))
    max_slope_deg = float(slope_cfg.get("max_slope_deg", 60.0))
    transformation = slope_cfg.get("transformation", "linear_clipped")
    aspect_role = aspect_cfg.get("role", "contextual")
    aspect_weight = float(aspect_cfg.get("weight", 0.0))

    slope_rel = paths_cfg.get("slope_processed", "data/processed/terrain/slope_degrees.tif")
    aspect_rel = paths_cfg.get("aspect_processed", "data/processed/terrain/aspect_degrees.tif")
    hazards_dir_rel = paths_cfg.get("hazards_dir", "data/processed/hazards")
    proxy_rel = paths_cfg.get("terrain_susceptibility_proxy", "data/processed/hazards/terrain_susceptibility_proxy.tif")

    slope_path = (_ROOT_DIR / slope_rel).resolve()
    aspect_path = (_ROOT_DIR / aspect_rel).resolve()
    hazards_dir = (_ROOT_DIR / hazards_dir_rel).resolve()
    output_path = (_ROOT_DIR / proxy_rel).resolve()

    _section("1. METHODOLOGY & CONFIGURATION")
    _field("Methodology version", suscept_cfg.get("methodology_version", "1.0"))
    _field("Primary factor", f"Slope angle (role: {slope_cfg.get('role', 'primary')})")
    _field("Slope min threshold (theta_min)", f"{min_slope_deg:.1f} deg -> score = 0.0")
    _field("Slope max threshold (theta_max)", f"{max_slope_deg:.1f} deg -> score = 1.0 (saturation)")
    _field("Transformation formula", f"score = clip((slope - {min_slope_deg:.1f}) / ({max_slope_deg:.1f} - {min_slope_deg:.1f}), 0.0, 1.0)")
    _field("Secondary factor", f"Aspect (role: {aspect_role}, weight: {aspect_weight})")
    _field("Analysis CRS", analysis_crs_str)

    # Verify input existence
    _section("2. INPUT DATASETS & ALIGNMENT VERIFICATION")
    if not slope_path.is_file():
        print(f"[FAIL] Slope raster not found: {slope_path}")
        return False
    _field("Slope input path", str(slope_path))

    if not aspect_path.is_file():
        print(f"[FAIL] Aspect raster not found: {aspect_path}")
        return False
    _field("Aspect input path", str(aspect_path))

    # Read slope raster
    with rasterio.open(slope_path) as slope_src:
        slope_crs = slope_src.crs
        slope_transform = slope_src.transform
        slope_w, slope_h = slope_src.width, slope_src.height
        slope_profile = slope_src.profile.copy()
        slope_nodata = slope_src.nodata
        slope_data = slope_src.read(1)

    # Read aspect raster for alignment verification
    with rasterio.open(aspect_path) as aspect_src:
        aspect_crs = aspect_src.crs
        aspect_transform = aspect_src.transform
        aspect_w, aspect_h = aspect_src.width, aspect_src.height

    # Validate alignment
    crs_ok = (slope_crs == target_crs) and (aspect_crs == target_crs)
    dim_ok = (slope_w == aspect_w) and (slope_h == aspect_h)
    trans_ok = (
        np.isclose(slope_transform.a, aspect_transform.a) and
        np.isclose(slope_transform.b, aspect_transform.b) and
        np.isclose(slope_transform.c, aspect_transform.c) and
        np.isclose(slope_transform.d, aspect_transform.d) and
        np.isclose(slope_transform.e, aspect_transform.e) and
        np.isclose(slope_transform.f, aspect_transform.f)
    )

    all_passed &= _result("Slope CRS matches analysis CRS", slope_crs == target_crs, f"{slope_crs}")
    all_passed &= _result("Aspect CRS matches analysis CRS", aspect_crs == target_crs, f"{aspect_crs}")
    all_passed &= _result("Spatial grid alignment verified", dim_ok and trans_ok, f"{slope_w} x {slope_h} px")

    if not (crs_ok and dim_ok and trans_ok):
        print("[FAIL] Spatial alignment check failed.")
        return False

    # 3. Calculate continuous susceptibility proxy
    _section("3. CONTINUOUS PROXY CALCULATION")
    total_pixels = slope_data.size
    nan_mask = np.isnan(slope_data)
    nodata_mask = nan_mask if (slope_nodata is None or np.isnan(slope_nodata)) else (nan_mask | (slope_data == slope_nodata))
    valid_mask = ~nodata_mask
    valid_count = int(np.sum(valid_mask))
    nodata_count = int(np.sum(nodata_mask))

    _field("Total raster pixels", f"{total_pixels:,}")
    _field("Valid terrain pixels", f"{valid_count:,} ({valid_count/total_pixels*100:.2f}%)")
    _field("NoData pixels", f"{nodata_count:,} ({nodata_count/total_pixels*100:.2f}%)")

    # Allocate output float32 array initialized to NaN
    proxy_data = np.full(slope_data.shape, np.nan, dtype=np.float32)

    # Compute monotonic normalized score on valid pixels
    valid_slope = slope_data[valid_mask]
    denominator = max_slope_deg - min_slope_deg
    if denominator <= 0:
        print("[FAIL] Invalid slope threshold configuration: max_slope_deg must be > min_slope_deg")
        return False

    normalized_score = np.clip((valid_slope - min_slope_deg) / denominator, 0.0, 1.0)
    proxy_data[valid_mask] = normalized_score.astype(np.float32)

    # Compute statistics on output proxy
    valid_proxy = proxy_data[valid_mask]
    p_min = float(np.min(valid_proxy))
    p_max = float(np.max(valid_proxy))
    p_mean = float(np.mean(valid_proxy))
    p_std = float(np.std(valid_proxy))

    _field("Calculated score range", f"[{p_min:.4f}, {p_max:.4f}]")
    _field("Mean score", f"{p_mean:.4f}")
    _field("Std dev score", f"{p_std:.4f}")

    score_bounds_ok = (p_min >= 0.0) and (p_max <= 1.0)
    no_inf_ok = int(np.sum(np.isinf(proxy_data))) == 0
    all_passed &= _result("Score values strictly within [0.0, 1.0]", score_bounds_ok, f"min={p_min:.4f}, max={p_max:.4f}")
    all_passed &= _result("No infinite values in output", no_inf_ok)
    all_passed &= _result("Valid pixel count matches slope input", int(np.sum(~np.isnan(proxy_data))) == valid_count)

    # 4. Save GeoTIFF output
    _section("4. WRITE GEOTIFF OUTPUT")
    hazards_dir.mkdir(parents=True, exist_ok=True)
    _field("Output destination", str(output_path))

    out_profile = slope_profile.copy()
    out_profile.update({
        "driver": "GTiff",
        "dtype": "float32",
        "nodata": np.nan,
        "width": slope_w,
        "height": slope_h,
        "count": 1,
        "crs": target_crs,
        "transform": slope_transform,
        "compress": "lzw",
        "tiled": False
    })

    try:
        with rasterio.open(output_path, "w", **out_profile) as dst:
            dst.write(proxy_data, 1)
            dst.set_band_description(1, "Terrain-Derived Landslide Susceptibility Proxy (Normalized Score 0.0-1.0)")
            dst.update_tags(
                TITLE="Terrain-Derived Landslide Susceptibility Proxy",
                PROJECT_ID="SIH26191",
                PILOT_DISTRICT="Rudraprayag",
                STATE="Uttarakhand",
                METHODOLOGY="Deterministic Monotonic Slope Normalization",
                MIN_SLOPE_DEG=str(min_slope_deg),
                MAX_SLOPE_DEG=str(max_slope_deg),
                TRANSFORMATION="linear_clipped",
                ASPECT_ROLE="contextual",
                DISCLAIMER=output_cfg.get("disclaimer", "Decision Support Layer Only")
            )
        all_passed &= _result("GeoTIFF written successfully", output_path.is_file(),
                              f"Size: {output_path.stat().st_size / (1024*1024):.2f} MB")
    except Exception as e:
        print(f"[FAIL] Failed to write GeoTIFF: {e}")
        all_passed = False

    # Summary
    print(f"\n{_sep('=')}")
    if all_passed:
        print("TERRAIN SUSCEPTIBILITY DERIVATION: PASS")
    else:
        print("TERRAIN SUSCEPTIBILITY DERIVATION: FAIL")
    print(_sep('='))

    return all_passed


if __name__ == "__main__":
    success = derive_terrain_susceptibility()
    sys.exit(0 if success else 1)
