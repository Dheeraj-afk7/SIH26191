#!/usr/bin/env python3
"""
SIH26191 -- Step 6D & 6F: Derive Multi-Hazard Screening Score and Contribution Layers
====================================================================================
Combines the Terrain-Derived Landslide Susceptibility Proxy and Flood Exposure
Proxy into a transparent, deterministic Multi-Hazard Screening Score, and generates
spatial contribution / explainability layers using configuration-driven weights.

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

METHODOLOGY & FORMULATION
-------------------------
1. Linear Weighted Combination:
       M(x, y) = (w_terrain * T(x, y)) + (w_flood * F(x, y))
   where:
       M(x, y)   = Multi-Hazard Screening Score in [0.0, 1.0]
       T(x, y)   = Terrain Susceptibility Proxy in [0.0, 1.0]
       F(x, y)   = Flood Exposure Proxy in [0.0, 1.0]
       w_terrain = Configured weight for terrain susceptibility (0.5)
       w_flood   = Configured weight for flood exposure (0.5)

2. Component Contribution (Explainability) Layers:
       C_terrain(x, y) = w_terrain * T(x, y)
       C_flood(x, y)   = w_flood * F(x, y)
   such that:
       C_terrain(x, y) + C_flood(x, y) == M(x, y)  (within numerical float tolerance)

3. NoData Policy:
   - If either input is NaN (NoData), output M, C_terrain, C_flood are NaN.
   - Valid pixel count matches input mask exactly.

4. Explicit Non-Claims:
   - Intermediate screening indicator for decision support only.
   - NOT an official hazard zone, government red zone, disaster prediction,
     safety certification, evacuation order, or relocation authorization.

OUTPUTS
-------
  data/processed/hazards/multihazard_score.tif
  data/processed/hazards/terrain_contribution.tif
  data/processed/hazards/flood_contribution.tif

USAGE
-----
    python processing/multihazard/derive_multihazard_score.py
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
# Core Multi-Hazard Derivation Logic
# ---------------------------------------------------------------------------

def derive_multihazard_score() -> bool:
    print(_sep("="))
    print("  SIH26191 -- STEP 6D & 6F: DERIVE MULTI-HAZARD SCORE & CONTRIBUTIONS")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    all_passed = True
    cfg = load_config()

    # 1. Read Configuration
    _section("1. CONFIGURATION AUDIT")
    multihazard_cfg = cfg.get("multihazard", {})
    weights_cfg = multihazard_cfg.get("weights", {})
    inputs_cfg = multihazard_cfg.get("inputs", {})
    outputs_cfg = multihazard_cfg.get("outputs", {})
    crs_cfg = cfg.get("crs", {})
    paths_cfg = cfg.get("paths", {})

    analysis_crs_str = crs_cfg.get("analysis_crs_metric", "EPSG:32644")
    target_crs = CRS.from_string(analysis_crs_str)

    # Weights
    w_terrain = float(weights_cfg.get("terrain_weight", 0.5))
    w_flood = float(weights_cfg.get("flood_weight", 0.5))
    weight_sum = w_terrain + w_flood
    weight_rationale = weights_cfg.get("weight_rationale", "Initial equal-weight screening baseline")

    _field("Terrain Susceptibility Weight (w_t)", f"{w_terrain:.4f}")
    _field("Flood Exposure Weight (w_f)", f"{w_flood:.4f}")
    _field("Weight Sum (w_t + w_f)", f"{weight_sum:.6f}")
    _field("Weight Selection Rationale", weight_rationale)

    if not np.isclose(weight_sum, 1.0, atol=1e-5):
        print(f"[FAIL] Configured multi-hazard weights do not sum to 1.0: sum={weight_sum}")
        return False
    _result("Configured weights sum to 1.0", True, f"w_t={w_terrain}, w_f={w_flood}")

    # Paths
    terrain_proxy_rel = inputs_cfg.get(
        "terrain_susceptibility_proxy",
        paths_cfg.get("terrain_susceptibility_proxy", "data/processed/hazards/terrain_susceptibility_proxy.tif")
    )
    flood_proxy_rel = inputs_cfg.get(
        "flood_exposure_proxy",
        paths_cfg.get("flood_exposure_proxy", "data/processed/hazards/flood_exposure_proxy.tif")
    )

    score_out_rel = outputs_cfg.get(
        "multihazard_score",
        paths_cfg.get("multihazard_score", "data/processed/hazards/multihazard_score.tif")
    )
    terrain_contrib_rel = outputs_cfg.get(
        "terrain_contribution",
        paths_cfg.get("terrain_contribution", "data/processed/hazards/terrain_contribution.tif")
    )
    flood_contrib_rel = outputs_cfg.get(
        "flood_contribution",
        paths_cfg.get("flood_contribution", "data/processed/hazards/flood_contribution.tif")
    )

    terrain_proxy_path = (_ROOT_DIR / terrain_proxy_rel).resolve()
    flood_proxy_path = (_ROOT_DIR / flood_proxy_rel).resolve()
    score_out_path = (_ROOT_DIR / score_out_rel).resolve()
    terrain_contrib_path = (_ROOT_DIR / terrain_contrib_rel).resolve()
    flood_contrib_path = (_ROOT_DIR / flood_contrib_rel).resolve()

    _field("Input Terrain Proxy", str(terrain_proxy_path))
    _field("Input Flood Proxy", str(flood_proxy_path))
    _field("Output Multi-Hazard Score", str(score_out_path))
    _field("Output Terrain Contribution", str(terrain_contrib_path))
    _field("Output Flood Contribution", str(flood_contrib_path))

    # 2. Input Loading & Verification
    _section("2. INPUT LOADING & SPATIAL VERIFICATION")
    if not terrain_proxy_path.is_file():
        print(f"[FAIL] Terrain proxy not found: {terrain_proxy_path}")
        return False
    if not flood_proxy_path.is_file():
        print(f"[FAIL] Flood proxy not found: {flood_proxy_path}")
        return False

    with rasterio.open(terrain_proxy_path) as ds_t:
        arr_t = ds_t.read(1)
        profile_t = ds_t.profile.copy()
        crs_t = ds_t.crs
        transform_t = ds_t.transform
        shape_t = (ds_t.height, ds_t.width)

    with rasterio.open(flood_proxy_path) as ds_f:
        arr_f = ds_f.read(1)
        crs_f = ds_f.crs
        transform_f = ds_f.transform
        shape_f = (ds_f.height, ds_f.width)

    _result("Terrain Proxy CRS matches analysis CRS", crs_t == target_crs, str(crs_t))
    _result("Flood Proxy CRS matches analysis CRS", crs_f == target_crs, str(crs_f))
    _result("Grid shapes match", shape_t == shape_f, f"{shape_t}")
    _result("Geotransforms match", transform_t == transform_f)

    # 3. Derivation of Multi-Hazard Score & Contribution Layers
    _section("3. DERIVATION OF SCORE & CONTRIBUTIONS")
    
    # Identify valid and NoData pixels
    valid_t = ~np.isnan(arr_t)
    valid_f = ~np.isnan(arr_f)
    valid_mask = valid_t & valid_f

    total_px = arr_t.size
    valid_count = int(np.sum(valid_mask))
    nodata_count = total_px - valid_count

    _field("Total Pixels", f"{total_px:,}")
    _field("Valid Pixels (T & F)", f"{valid_count:,} ({valid_count/total_px*100:.2f}%)")
    _field("NoData Pixels", f"{nodata_count:,} ({nodata_count/total_px*100:.2f}%)")

    # Allocate outputs initialized with NaN
    score_arr = np.full(arr_t.shape, np.nan, dtype=np.float32)
    terrain_contrib_arr = np.full(arr_t.shape, np.nan, dtype=np.float32)
    flood_contrib_arr = np.full(arr_t.shape, np.nan, dtype=np.float32)

    # Calculate contributions and combined score on valid pixels
    t_valid = arr_t[valid_mask]
    f_valid = arr_f[valid_mask]

    c_t_valid = (w_terrain * t_valid).astype(np.float32)
    c_f_valid = (w_flood * f_valid).astype(np.float32)
    score_valid = c_t_valid + c_f_valid

    # Numerical safeguard: clamp to [0.0, 1.0]
    score_valid = np.clip(score_valid, 0.0, 1.0)

    terrain_contrib_arr[valid_mask] = c_t_valid
    flood_contrib_arr[valid_mask] = c_f_valid
    score_arr[valid_mask] = score_valid

    # 4. Numerical & Explainability Verification
    _section("4. NUMERICAL & EXPLAINABILITY AUDIT")
    
    # Check bounds
    m_min, m_max = float(np.nanmin(score_arr)), float(np.nanmax(score_arr))
    m_mean, m_std = float(np.nanmean(score_arr)), float(np.nanstd(score_arr))
    m_p25 = float(np.percentile(score_valid, 25))
    m_p50 = float(np.percentile(score_valid, 50))
    m_p75 = float(np.percentile(score_valid, 75))
    m_p90 = float(np.percentile(score_valid, 90))
    m_p99 = float(np.percentile(score_valid, 99))

    _field("Multi-Hazard Score Min", f"{m_min:.4f}")
    _field("Multi-Hazard Score Max", f"{m_max:.4f}")
    _field("Multi-Hazard Score Mean", f"{m_mean:.4f}")
    _field("Multi-Hazard Score Std Dev", f"{m_std:.4f}")
    _field("Multi-Hazard Score 25th %ile", f"{m_p25:.4f}")
    _field("Multi-Hazard Score Median (50th)", f"{m_p50:.4f}")
    _field("Multi-Hazard Score 75th %ile", f"{m_p75:.4f}")
    _field("Multi-Hazard Score 90th %ile", f"{m_p90:.4f}")
    _field("Multi-Hazard Score 99th %ile", f"{m_p99:.4f}")

    all_passed = _result("Score values bounded in [0.0, 1.0]", (m_min >= 0.0) and (m_max <= 1.0)) and all_passed

    # Check contributions
    ct_min, ct_max = float(np.nanmin(terrain_contrib_arr)), float(np.nanmax(terrain_contrib_arr))
    ct_mean = float(np.nanmean(terrain_contrib_arr))
    cf_min, cf_max = float(np.nanmin(flood_contrib_arr)), float(np.nanmax(flood_contrib_arr))
    cf_mean = float(np.nanmean(flood_contrib_arr))

    _field("Terrain Contribution Mean (w_t * T)", f"{ct_mean:.4f} (range: [{ct_min:.4f}, {ct_max:.4f}])")
    _field("Flood Contribution Mean (w_f * F)", f"{cf_mean:.4f} (range: [{cf_min:.4f}, {cf_max:.4f}])")

    all_passed = _result("Terrain contribution non-negative", ct_min >= 0.0) and all_passed
    all_passed = _result("Flood contribution non-negative", cf_min >= 0.0) and all_passed

    # Explainability additive check: C_t + C_f == M
    diff = np.abs((c_t_valid + c_f_valid) - score_valid)
    max_diff = float(np.max(diff))
    mean_diff = float(np.mean(diff))
    _field("Max Additive Residual (|C_t + C_f - M|)", f"{max_diff:.8e}")
    _field("Mean Additive Residual", f"{mean_diff:.8e}")

    additive_ok = max_diff < 1e-6
    all_passed = _result("Additive explainability holds strictly (C_t + C_f == M)", additive_ok, f"max_diff={max_diff:.2e}") and all_passed

    # 5. Write GeoTIFF Datasets
    _section("5. GEOTIFF WRITING")

    out_profile = profile_t.copy()
    out_profile.update({
        "driver": "GTiff",
        "height": arr_t.shape[0],
        "width": arr_t.shape[1],
        "count": 1,
        "dtype": "float32",
        "crs": target_crs,
        "transform": transform_t,
        "nodata": np.nan,
        "compress": "deflate",
        "predictor": 3,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    })

    # Ensure parent output directories exist
    score_out_path.parent.mkdir(parents=True, exist_ok=True)
    terrain_contrib_path.parent.mkdir(parents=True, exist_ok=True)
    flood_contrib_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"  Writing Multi-Hazard Score -> {score_out_path.relative_to(_ROOT_DIR)}")
    with rasterio.open(score_out_path, "w", **out_profile) as dst:
        dst.write(score_arr, 1)
        dst.set_band_description(1, "Multi-Hazard Screening Score [0.0 - 1.0]")
    _result("Multi-Hazard Score written successfully", score_out_path.is_file())

    print(f"  Writing Terrain Contribution -> {terrain_contrib_path.relative_to(_ROOT_DIR)}")
    with rasterio.open(terrain_contrib_path, "w", **out_profile) as dst:
        dst.write(terrain_contrib_arr, 1)
        dst.set_band_description(1, "Terrain Susceptibility Component Contribution")
    _result("Terrain Contribution layer written successfully", terrain_contrib_path.is_file())

    print(f"  Writing Flood Contribution -> {flood_contrib_path.relative_to(_ROOT_DIR)}")
    with rasterio.open(flood_contrib_path, "w", **out_profile) as dst:
        dst.write(flood_contrib_arr, 1)
        dst.set_band_description(1, "Flood Exposure Component Contribution")
    _result("Flood Contribution layer written successfully", flood_contrib_path.is_file())

    print(f"\n{_sep('=')}")
    if all_passed:
        print("MULTI-HAZARD SCORE DERIVATION: PASS")
    else:
        print("MULTI-HAZARD SCORE DERIVATION: FAIL")
    print(_sep('='))

    return all_passed


if __name__ == "__main__":
    success = derive_multihazard_score()
    sys.exit(0 if success else 1)
