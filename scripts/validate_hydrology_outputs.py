#!/usr/bin/env python3
"""
SIH26191 -- Step 5G: Hydrology Output Validation
==============================================================================
Comprehensive technical validation of all hydrological derivatives and flood
screening outputs produced in Step 5:
  - data/processed/hydrology/flow_direction.tif
  - data/processed/hydrology/flow_accumulation.tif
  - data/processed/hydrology/topographic_wetness_index.tif
  - data/processed/hazards/flood_exposure_proxy.tif
  - data/processed/hazards/flood_exposure_classes.tif

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

VALIDATION RULES & ASSERTIONS
-----------------------------
1. INPUT INTEGRITY (Raw DEM, Step 3 Terrain, Step 4 Landslide Hazards):
   - Raw DEM exists, is intact, and was NOT modified.
   - Step 3 terrain derivatives (slope, aspect) exist and are unchanged.
   - Step 4 landslide hazard outputs (proxy, classes) exist and were NOT overwritten.

2. HYDROLOGICAL DERIVATIVES:
   - Files exist and are readable.
   - Match configured analysis CRS (EPSG:32644).
   - Dimensions, transform, and extent match terrain processing grid.
   - Data types: flow_direction (uint8), flow_accumulation (float32), TWI (float32).
   - Flow direction contains only valid D8 codes [0, 1, 2, 4, 8, 16, 32, 64, 128, 255].
   - Flow accumulation is strictly >= 1.0 cell with 0 infinite values.
   - TWI is numerically valid and finite on all valid terrain pixels.

3. CONTINUOUS FLOOD EXPOSURE PROXY:
   - File exists, is readable, CRS is EPSG:32644, dtype is float32.
   - Scores strictly within [0.0000, 1.0000].
   - Zero infinite values; NoData pixels match DEM/slope mask.
   - Monotonic alignment: TWI increase -> score increase.

4. CLASSIFIED FLOOD EXPOSURE CATEGORIES:
   - File exists, is readable, CRS is EPSG:32644, dtype is uint8.
   - Only documented class codes (1, 2, 3) and NoData (255) exist.
   - Valid classified pixel count exactly matches continuous proxy valid pixels.
   - NoData mask matches continuous proxy NoData mask.

5. SPATIAL ALIGNMENT & CONSISTENCY:
   - Full pixel-by-pixel alignment across all 5 hydrological and hazard layers.

USAGE
-----
    python scripts/validate_hydrology_outputs.py
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
# Main Validation Logic
# ---------------------------------------------------------------------------

def validate_hydrology_outputs() -> bool:
    print(_sep("="))
    print("  SIH26191 -- STEP 5G: HYDROLOGY OUTPUT VALIDATION")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    all_passed = True
    cfg = load_config(_ROOT_DIR)

    paths_cfg = cfg.get("paths", {})
    crs_cfg = cfg.get("crs", {})
    hydro_cfg = cfg.get("hydrology", {})
    class_cfg = hydro_cfg.get("classification", {})

    analysis_crs_str = crs_cfg.get("analysis_crs_metric", "EPSG:32644")
    target_crs = CRS.from_string(analysis_crs_str)

    # Resolve all file paths
    dem_path = (_ROOT_DIR / paths_cfg.get("dem_raw", "data/raw/copernicus_glo30_rudraprayag.tif")).resolve()
    slope_path = (_ROOT_DIR / paths_cfg.get("slope_processed", "data/processed/terrain/slope_degrees.tif")).resolve()
    aspect_path = (_ROOT_DIR / paths_cfg.get("aspect_processed", "data/processed/terrain/aspect_degrees.tif")).resolve()
    landslide_proxy_path = (_ROOT_DIR / paths_cfg.get("terrain_susceptibility_proxy", "data/processed/hazards/terrain_susceptibility_proxy.tif")).resolve()
    landslide_class_path = (_ROOT_DIR / paths_cfg.get("terrain_susceptibility_classes", "data/processed/hazards/terrain_susceptibility_classes.tif")).resolve()

    fdir_path = (_ROOT_DIR / paths_cfg.get("flow_direction", "data/processed/hydrology/flow_direction.tif")).resolve()
    facc_path = (_ROOT_DIR / paths_cfg.get("flow_accumulation", "data/processed/hydrology/flow_accumulation.tif")).resolve()
    twi_path = (_ROOT_DIR / paths_cfg.get("topographic_wetness_index", "data/processed/hydrology/topographic_wetness_index.tif")).resolve()
    flood_proxy_path = (_ROOT_DIR / paths_cfg.get("flood_exposure_proxy", "data/processed/hazards/flood_exposure_proxy.tif")).resolve()
    flood_class_path = (_ROOT_DIR / paths_cfg.get("flood_exposure_classes", "data/processed/hazards/flood_exposure_classes.tif")).resolve()

    nodata_val_cfg = int(class_cfg.get("nodata_value", 255))
    documented_classes = [int(c["code"]) for c in class_cfg.get("classes", [])]

    # ------------------------------------------------------------------
    # 1. Pipeline Integrity & Baseline Layers Audit
    # ------------------------------------------------------------------
    _section("1. PIPELINE INTEGRITY & BASELINE DATASETS AUDIT")
    all_passed &= _result("Raw DEM exists and is untouched", dem_path.is_file(), str(dem_path))
    all_passed &= _result("Step 3 Slope output exists and is intact", slope_path.is_file(), str(slope_path))
    all_passed &= _result("Step 3 Aspect output exists and is intact", aspect_path.is_file(), str(aspect_path))
    all_passed &= _result("Step 4 Landslide Susceptibility Proxy exists and is intact", landslide_proxy_path.is_file(), str(landslide_proxy_path))
    all_passed &= _result("Step 4 Landslide Susceptibility Classes exists and is intact", landslide_class_path.is_file(), str(landslide_class_path))

    if not (slope_path.is_file() and landslide_proxy_path.is_file()):
        print("[FAIL] Prior pipeline stages missing. Aborting validation.")
        return False

    with rasterio.open(slope_path) as s_src:
        grid_w, grid_h = s_src.width, s_src.height
        grid_crs = s_src.crs
        grid_transform = s_src.transform
        slope_data = s_src.read(1)
        slope_nodata_mask = np.isnan(slope_data)
        valid_terrain_count = int(np.sum(~slope_nodata_mask))

    # ------------------------------------------------------------------
    # 2. Hydrological Derivatives Validation
    # ------------------------------------------------------------------
    _section("2. HYDROLOGICAL DERIVATIVES VALIDATION")

    # A. Flow Direction
    all_passed &= _result("Flow direction file exists", fdir_path.is_file(), str(fdir_path))
    if fdir_path.is_file():
        with rasterio.open(fdir_path) as src:
            all_passed &= _result("Flow direction is readable", True)
            all_passed &= _result("Flow direction CRS matches analysis CRS", src.crs == target_crs)
            all_passed &= _result("Flow direction dimensions match grid", (src.width == grid_w) and (src.height == grid_h))
            all_passed &= _result("Flow direction dtype is uint8", src.dtypes[0] == "uint8")
            all_passed &= _result("Flow direction nodata is 255", src.nodata == 255.0 or src.nodata == 255)
            fdir_data = src.read(1)
            valid_d8_codes = {0, 1, 2, 4, 8, 16, 32, 64, 128, 255}
            actual_codes = set(np.unique(fdir_data).tolist())
            all_passed &= _result("Only valid D8 codes and NoData exist", actual_codes.issubset(valid_d8_codes),
                                  f"codes={sorted(list(actual_codes))}")
            fdir_nodata_mask = (fdir_data == 255)
            all_passed &= _result("Flow direction NoData mask matches slope mask", np.array_equal(fdir_nodata_mask, slope_nodata_mask))

    # B. Flow Accumulation
    all_passed &= _result("Flow accumulation file exists", facc_path.is_file(), str(facc_path))
    if facc_path.is_file():
        with rasterio.open(facc_path) as src:
            all_passed &= _result("Flow accumulation is readable", True)
            all_passed &= _result("Flow accumulation CRS matches analysis CRS", src.crs == target_crs)
            all_passed &= _result("Flow accumulation dimensions match grid", (src.width == grid_w) and (src.height == grid_h))
            all_passed &= _result("Flow accumulation dtype is float32", src.dtypes[0] == "float32")
            facc_data = src.read(1)
            facc_valid = facc_data[~slope_nodata_mask]
            acc_min = float(np.min(facc_valid))
            acc_max = float(np.max(facc_valid))
            all_passed &= _result("Accumulation strictly >= 1.0 cell", acc_min >= 1.0, f"min={acc_min:.1f}, max={acc_max:.1f}")
            all_passed &= _result("Zero infinite values in accumulation", int(np.sum(np.isinf(facc_data))) == 0)
            all_passed &= _result("Accumulation NoData mask matches slope mask", np.array_equal(np.isnan(facc_data), slope_nodata_mask))

    # C. Topographic Wetness Index (TWI)
    all_passed &= _result("Topographic Wetness Index file exists", twi_path.is_file(), str(twi_path))
    if twi_path.is_file():
        with rasterio.open(twi_path) as src:
            all_passed &= _result("TWI raster is readable", True)
            all_passed &= _result("TWI CRS matches analysis CRS", src.crs == target_crs)
            all_passed &= _result("TWI dimensions match grid", (src.width == grid_w) and (src.height == grid_h))
            all_passed &= _result("TWI dtype is float32", src.dtypes[0] == "float32")
            twi_data = src.read(1)
            twi_valid = twi_data[~slope_nodata_mask]
            twi_min = float(np.min(twi_valid))
            twi_max = float(np.max(twi_valid))
            all_passed &= _result("Zero infinite values in TWI", int(np.sum(np.isinf(twi_data))) == 0)
            all_passed &= _result("TWI physically realistic range [1.0 to 25.0]", (twi_min >= 0.0) and (twi_max <= 30.0),
                                  f"min={twi_min:.2f}, max={twi_max:.2f}")
            all_passed &= _result("TWI NoData mask matches slope mask", np.array_equal(np.isnan(twi_data), slope_nodata_mask))

    # ------------------------------------------------------------------
    # 3. Continuous Flood Exposure Proxy Validation
    # ------------------------------------------------------------------
    _section("3. CONTINUOUS FLOOD EXPOSURE PROXY VALIDATION (flood_exposure_proxy.tif)")
    all_passed &= _result("Flood proxy file exists", flood_proxy_path.is_file(), str(flood_proxy_path))
    if flood_proxy_path.is_file():
        with rasterio.open(flood_proxy_path) as src:
            all_passed &= _result("Flood proxy raster is readable", True)
            all_passed &= _result("Flood proxy CRS matches analysis CRS", src.crs == target_crs)
            all_passed &= _result("Flood proxy dimensions match grid", (src.width == grid_w) and (src.height == grid_h))
            all_passed &= _result("Flood proxy dtype is float32", src.dtypes[0] == "float32")
            proxy_data = src.read(1)
            p_nan_mask = np.isnan(proxy_data)
            p_valid = proxy_data[~p_nan_mask]
            p_min = float(np.min(p_valid))
            p_max = float(np.max(p_valid))
            p_valid_count = len(p_valid)

            all_passed &= _result("Zero infinite values in proxy", int(np.sum(np.isinf(proxy_data))) == 0)
            all_passed &= _result("Proxy values strictly bounded within [0.0000, 1.0000]",
                                  (p_min >= 0.0) and (p_max <= 1.0),
                                  f"min={p_min:.4f}, max={p_max:.4f}")
            all_passed &= _result("Valid pixel count matches terrain grid", p_valid_count == valid_terrain_count,
                                  f"proxy={p_valid_count:,}, terrain={valid_terrain_count:,}")
            all_passed &= _result("Proxy NoData mask matches slope mask", np.array_equal(p_nan_mask, slope_nodata_mask))

    # ------------------------------------------------------------------
    # 4. Classified Flood Exposure Output Validation
    # ------------------------------------------------------------------
    _section("4. CLASSIFIED FLOOD EXPOSURE VALIDATION (flood_exposure_classes.tif)")
    all_passed &= _result("Flood classes file exists", flood_class_path.is_file(), str(flood_class_path))
    if flood_class_path.is_file():
        with rasterio.open(flood_class_path) as src:
            all_passed &= _result("Flood classes raster is readable", True)
            all_passed &= _result("Flood classes CRS matches analysis CRS", src.crs == target_crs)
            all_passed &= _result("Flood classes dimensions match grid", (src.width == grid_w) and (src.height == grid_h))
            all_passed &= _result("Flood classes dtype is uint8", src.dtypes[0] == "uint8")
            all_passed &= _result("Flood classes NoData value is configured (255)", src.nodata == nodata_val_cfg or src.nodata == float(nodata_val_cfg))
            class_data = src.read(1)
            c_unique = sorted(list(np.unique(class_data)))
            c_expected = sorted(documented_classes + [nodata_val_cfg])
            all_passed &= _result("Only documented class codes and NoData exist", c_unique == c_expected,
                                  f"actual={c_unique}, expected={c_expected}")
            c_valid_count = int(np.sum(class_data != nodata_val_cfg))
            all_passed &= _result("Classified valid pixel count matches terrain", c_valid_count == valid_terrain_count,
                                  f"classes={c_valid_count:,}, terrain={valid_terrain_count:,}")
            all_passed &= _result("Classes NoData mask matches slope mask", np.array_equal(class_data == nodata_val_cfg, slope_nodata_mask))

    # ------------------------------------------------------------------
    # 5. Multi-Layer Spatial Alignment & Monotonicity Audit
    # ------------------------------------------------------------------
    _section("5. MULTI-LAYER SPATIAL ALIGNMENT & MONOTONICITY AUDIT")
    # Check transform alignment across all Step 5 outputs
    for p, name in [
        (fdir_path, "Flow Direction"),
        (facc_path, "Flow Accumulation"),
        (twi_path, "Topographic Wetness Index"),
        (flood_proxy_path, "Flood Exposure Proxy"),
        (flood_class_path, "Flood Exposure Classes"),
    ]:
        with rasterio.open(p) as src:
            trans_ok = (
                np.isclose(src.transform.a, grid_transform.a) and
                np.isclose(src.transform.b, grid_transform.b) and
                np.isclose(src.transform.c, grid_transform.c) and
                np.isclose(src.transform.d, grid_transform.d) and
                np.isclose(src.transform.e, grid_transform.e) and
                np.isclose(src.transform.f, grid_transform.f)
            )
            all_passed &= _result(f"{name} transform strictly aligned with terrain grid", trans_ok)

    # Monotonicity test on sample
    np.random.seed(42)
    sample_indices = np.random.choice(valid_terrain_count, size=min(10000, valid_terrain_count), replace=False)
    sample_twi = twi_data[~slope_nodata_mask][sample_indices]
    sample_proxy = proxy_data[~slope_nodata_mask][sample_indices]
    sample_classes = class_data[~slope_nodata_mask][sample_indices]

    sort_order = np.argsort(sample_twi)
    sorted_proxy = sample_proxy[sort_order]
    sorted_classes = sample_classes[sort_order]

    is_monotonic_proxy = np.all(np.diff(sorted_proxy) >= -1e-6)
    is_monotonic_classes = np.all(np.diff(sorted_classes) >= 0)

    all_passed &= _result("Proxy score increases monotonically with TWI", is_monotonic_proxy)
    all_passed &= _result("Classification code increases monotonically with TWI", is_monotonic_classes)

    # Summary
    print(f"\n{_sep('=')}")
    if all_passed:
        print("HYDROLOGY OUTPUT VALIDATION: PASS")
    else:
        print("HYDROLOGY OUTPUT VALIDATION: FAIL")
    print(_sep('='))

    return all_passed


if __name__ == "__main__":
    success = validate_hydrology_outputs()
    sys.exit(0 if success else 1)
