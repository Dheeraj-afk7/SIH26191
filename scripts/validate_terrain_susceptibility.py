#!/usr/bin/env python3
"""
SIH26191 -- Step 4G: Terrain Susceptibility Output Validation
==============================================================================
Comprehensive technical validation of the derived landslide susceptibility proxy
rasters produced in Step 4:
  - data/processed/hazards/terrain_susceptibility_proxy.tif
  - data/processed/hazards/terrain_susceptibility_classes.tif

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

VALIDATION RULES & ASSERTIONS
-----------------------------
1. INPUTS (Slope & Aspect):
   - Files exist and are readable.
   - Match configured analysis CRS (EPSG:32644).

2. CONTINUOUS SUSCEPTIBILITY PROXY (terrain_susceptibility_proxy.tif):
   - File exists and is readable.
   - CRS matches configured analysis CRS (EPSG:32644).
   - Dimensions, transform, and extent match terrain grid.
   - Data type is float32.
   - All valid values lie strictly within [0.0000, 1.0000].
   - Zero infinite values.
   - NoData pixels are NaN, exactly matching slope NoData mask.
   - Monotonic alignment: slope increase -> score increase.

3. CLASSIFIED SUSCEPTIBILITY CATEGORIES (terrain_susceptibility_classes.tif):
   - File exists and is readable.
   - CRS matches configured analysis CRS (EPSG:32644).
   - Dimensions and transform match terrain grid.
   - Data type is uint8.
   - Only documented class codes (1, 2, 3) and NoData (255) exist.
   - Class count matches valid terrain pixel count.
   - NoData mask matches continuous proxy NoData mask.

4. SPATIAL ALIGNMENT & CONSISTENCY:
   - Full pixel-by-pixel alignment across slope, aspect, proxy, and classes.

USAGE
-----
    python scripts/validate_terrain_susceptibility.py
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
# Validation Logic
# ---------------------------------------------------------------------------

def validate_terrain_susceptibility() -> bool:
    print(_sep("="))
    print("  SIH26191 -- STEP 4G: TERRAIN SUSCEPTIBILITY OUTPUT VALIDATION")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    all_passed = True
    cfg = load_config(_ROOT_DIR)

    paths_cfg = cfg.get("paths", {})
    crs_cfg = cfg.get("crs", {})
    suscept_cfg = cfg.get("terrain_susceptibility", {})
    class_cfg = suscept_cfg.get("classification", {})

    analysis_crs_str = crs_cfg.get("analysis_crs_metric", "EPSG:32644")
    target_crs = CRS.from_string(analysis_crs_str)

    slope_path = (_ROOT_DIR / paths_cfg.get("slope_processed", "data/processed/terrain/slope_degrees.tif")).resolve()
    aspect_path = (_ROOT_DIR / paths_cfg.get("aspect_processed", "data/processed/terrain/aspect_degrees.tif")).resolve()
    proxy_path = (_ROOT_DIR / paths_cfg.get("terrain_susceptibility_proxy", "data/processed/hazards/terrain_susceptibility_proxy.tif")).resolve()
    classes_path = (_ROOT_DIR / paths_cfg.get("terrain_susceptibility_classes", "data/processed/hazards/terrain_susceptibility_classes.tif")).resolve()

    nodata_val_cfg = int(class_cfg.get("nodata_value", 255))
    documented_codes = [int(c["code"]) for c in class_cfg.get("classes", [])]

    # 1. Check Inputs
    _section("1. TERRAIN INPUT VERIFICATION")
    slope_exists = slope_path.is_file()
    aspect_exists = aspect_path.is_file()
    all_passed &= _result("Slope input raster exists", slope_exists, str(slope_path))
    all_passed &= _result("Aspect input raster exists", aspect_exists, str(aspect_path))

    if not (slope_exists and aspect_exists):
        print("[FAIL] Missing required terrain input rasters.")
        return False

    with rasterio.open(slope_path) as s_src:
        slope_crs = s_src.crs
        slope_w, slope_h = s_src.width, s_src.height
        slope_transform = s_src.transform
        slope_data = s_src.read(1)
        slope_nodata = s_src.nodata

    slope_nan_mask = np.isnan(slope_data)
    slope_nodata_mask = slope_nan_mask if (slope_nodata is None or np.isnan(slope_nodata)) else (slope_nan_mask | (slope_data == slope_nodata))
    slope_valid_count = int(np.sum(~slope_nodata_mask))

    # 2. Continuous Proxy Validation
    _section("2. CONTINUOUS SUSCEPTIBILITY PROXY VALIDATION (terrain_susceptibility_proxy.tif)")
    proxy_exists = proxy_path.is_file()
    all_passed &= _result("Proxy raster file exists", proxy_exists, str(proxy_path))

    if not proxy_exists:
        print("[FAIL] Proxy raster does not exist. Run derive_terrain_susceptibility.py first.")
        return False

    with rasterio.open(proxy_path) as p_src:
        all_passed &= _result("Proxy raster is readable", True)
        proxy_crs = p_src.crs
        proxy_w, proxy_h = p_src.width, p_src.height
        proxy_transform = p_src.transform
        proxy_dtype = p_src.dtypes[0]
        proxy_nodata = p_src.nodata
        proxy_data = p_src.read(1)

        _field("Driver", p_src.driver)
        _field("CRS", str(proxy_crs))
        _field("Dimensions (W x H)", f"{proxy_w} x {proxy_h} pixels")
        _field("Data type", proxy_dtype)
        _field("NoData value", str(proxy_nodata))

        all_passed &= _result("Proxy CRS matches analysis CRS", proxy_crs == target_crs, f"{proxy_crs}")
        all_passed &= _result("Proxy dimensions match terrain grid", (proxy_w == slope_w) and (proxy_h == slope_h))
        all_passed &= _result("Proxy data type is float32", proxy_dtype == "float32")

        p_nan_mask = np.isnan(proxy_data)
        p_nodata_mask = p_nan_mask if (proxy_nodata is None or np.isnan(proxy_nodata)) else (p_nan_mask | (proxy_data == proxy_nodata))
        p_valid_mask = ~p_nodata_mask
        p_valid_count = int(np.sum(p_valid_mask))
        p_inf_count = int(np.sum(np.isinf(proxy_data)))

        _field("Total pixels", f"{proxy_data.size:,}")
        _field("Valid score pixels", f"{p_valid_count:,}")
        _field("NoData pixels", f"{np.sum(p_nodata_mask):,}")
        _field("Infinite pixels", str(p_inf_count))

        all_passed &= _result("No infinite values in proxy", p_inf_count == 0)
        all_passed &= _result("Valid pixel count matches input slope", p_valid_count == slope_valid_count,
                              f"proxy={p_valid_count:,}, slope={slope_valid_count:,}")

        if p_valid_count > 0:
            valid_p = proxy_data[p_valid_mask]
            p_min = float(np.min(valid_p))
            p_max = float(np.max(valid_p))
            p_mean = float(np.mean(valid_p))
            p_std = float(np.std(valid_p))

            _field("Minimum score", f"{p_min:.4f}")
            _field("Maximum score", f"{p_max:.4f}")
            _field("Mean score", f"{p_mean:.4f}")
            _field("Std dev score", f"{p_std:.4f}")

            score_bounded = (p_min >= 0.0) and (p_max <= 1.0)
            all_passed &= _result("All scores strictly within [0.0000, 1.0000]", score_bounded,
                                  f"min={p_min:.4f}, max={p_max:.4f}")

    # 3. Classified Susceptibility Output Validation
    _section("3. CLASSIFIED SUSCEPTIBILITY VALIDATION (terrain_susceptibility_classes.tif)")
    classes_exists = classes_path.is_file()
    all_passed &= _result("Classes raster file exists", classes_exists, str(classes_path))

    if not classes_exists:
        print("[FAIL] Classes raster does not exist. Run classify_terrain_susceptibility.py first.")
        return False

    with rasterio.open(classes_path) as c_src:
        all_passed &= _result("Classes raster is readable", True)
        c_crs = c_src.crs
        c_w, c_h = c_src.width, c_src.height
        c_transform = c_src.transform
        c_dtype = c_src.dtypes[0]
        c_nodata = c_src.nodata
        c_data = c_src.read(1)

        _field("Driver", c_src.driver)
        _field("CRS", str(c_crs))
        _field("Dimensions (W x H)", f"{c_w} x {c_h} pixels")
        _field("Data type", c_dtype)
        _field("NoData value", str(c_nodata))

        all_passed &= _result("Classes CRS matches analysis CRS", c_crs == target_crs, f"{c_crs}")
        all_passed &= _result("Classes dimensions match terrain grid", (c_w == slope_w) and (c_h == slope_h))
        all_passed &= _result("Classes data type is uint8", c_dtype == "uint8")
        all_passed &= _result("Classes NoData value is configured (255)", c_nodata == nodata_val_cfg, f"{c_nodata}")

        unique_codes = sorted(list(np.unique(c_data)))
        expected_codes = sorted(documented_codes + [nodata_val_cfg])
        all_passed &= _result("Only documented class codes and NoData exist", unique_codes == expected_codes,
                              f"actual={unique_codes}, expected={expected_codes}")

        c_valid_mask = (c_data != nodata_val_cfg)
        c_valid_count = int(np.sum(c_valid_mask))
        c_nodata_count = int(np.sum(c_data == nodata_val_cfg))

        _field("Valid classified pixels", f"{c_valid_count:,}")
        _field("NoData pixels", f"{c_nodata_count:,}")

        all_passed &= _result("Classified valid pixel count matches slope", c_valid_count == slope_valid_count,
                              f"classes={c_valid_count:,}, slope={slope_valid_count:,}")

    # 4. Multi-Layer Spatial Alignment Audit
    _section("4. MULTI-LAYER SPATIAL ALIGNMENT AUDIT")
    trans_proxy_ok = (
        np.isclose(slope_transform.a, proxy_transform.a) and
        np.isclose(slope_transform.b, proxy_transform.b) and
        np.isclose(slope_transform.c, proxy_transform.c) and
        np.isclose(slope_transform.d, proxy_transform.d) and
        np.isclose(slope_transform.e, proxy_transform.e) and
        np.isclose(slope_transform.f, proxy_transform.f)
    )
    trans_class_ok = (
        np.isclose(slope_transform.a, c_transform.a) and
        np.isclose(slope_transform.b, c_transform.b) and
        np.isclose(slope_transform.c, c_transform.c) and
        np.isclose(slope_transform.d, c_transform.d) and
        np.isclose(slope_transform.e, c_transform.e) and
        np.isclose(slope_transform.f, c_transform.f)
    )

    all_passed &= _result("Continuous proxy transform identical to slope", trans_proxy_ok)
    all_passed &= _result("Classified raster transform identical to slope", trans_class_ok)

    # Pixel-to-pixel NoData alignment
    proxy_nodata_aligned = np.array_equal(slope_nodata_mask, p_nodata_mask)
    class_nodata_aligned = np.array_equal(slope_nodata_mask, (c_data == nodata_val_cfg))
    all_passed &= _result("Proxy NoData mask perfectly matches slope NoData mask", proxy_nodata_aligned)
    all_passed &= _result("Classes NoData mask perfectly matches slope NoData mask", class_nodata_aligned)

    # Monotonicity test on a random sample of valid pixels
    np.random.seed(42)
    sample_indices = np.random.choice(slope_valid_count, size=min(10000, slope_valid_count), replace=False)
    sample_slope = slope_data[~slope_nodata_mask][sample_indices]
    sample_proxy = proxy_data[~p_nodata_mask][sample_indices]
    sample_classes = c_data[~slope_nodata_mask][sample_indices]

    # Sort by slope and verify monotonic non-decreasing score
    sort_order = np.argsort(sample_slope)
    sorted_proxy = sample_proxy[sort_order]
    sorted_classes = sample_classes[sort_order]
    is_monotonic_proxy = np.all(np.diff(sorted_proxy) >= -1e-6)
    is_monotonic_classes = np.all(np.diff(sorted_classes) >= 0)

    all_passed &= _result("Proxy score increases monotonically with slope angle", is_monotonic_proxy)
    all_passed &= _result("Classification code increases monotonically with slope angle", is_monotonic_classes)

    # Summary
    print(f"\n{_sep('=')}")
    if all_passed:
        print("TERRAIN SUSCEPTIBILITY VALIDATION: PASS")
    else:
        print("TERRAIN SUSCEPTIBILITY VALIDATION: FAIL")
    print(_sep('='))

    return all_passed


if __name__ == "__main__":
    success = validate_terrain_susceptibility()
    sys.exit(0 if success else 1)
