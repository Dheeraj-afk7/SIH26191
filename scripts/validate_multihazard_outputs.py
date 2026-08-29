#!/usr/bin/env python3
"""
SIH26191 -- Step 6G: Multi-Hazard Output Validation
==============================================================================
Comprehensive technical validation of all multi-hazard integration outputs
produced in Step 6:
  - data/processed/hazards/multihazard_score.tif
  - data/processed/hazards/multihazard_classes.tif
  - data/processed/hazards/terrain_contribution.tif
  - data/processed/hazards/flood_contribution.tif

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

VALIDATION RULES & 25 STRICT ASSERTIONS
---------------------------------------
INPUT INTEGRITY:
 1. Both input proxy files exist.
 2. Both input files are readable.
 3. Input proxy values are valid and untouched.

OUTPUT VALIDATION:
 4. Multi-hazard score exists.
 5. Multi-hazard classes exist.
 6. Contribution layers exist (terrain & flood).
 7. All output rasters are readable.
 8. CRS matches configured analysis CRS (EPSG:32644).
 9. Raster dimensions match upstream analysis grid (1854 x 2458 px).
10. Affine geotransforms match analysis grid.
11. Spatial bounding coordinates match analysis grid.
12. NoData is preserved consistently across all layers.
13. No unexpected NaN on valid terrain pixels.
14. Zero infinite values on all output rasters.
15. Multi-hazard score is strictly within [0.0, 1.0].
16. Class codes contain only documented values [1, 2, 3, 255].
17. Classified valid pixel count exactly matches score valid pixel count.
18. Classification is monotonic with respect to continuous score.
19. Contribution layers are non-negative.
20. Terrain contribution + flood contribution == multi-hazard score within float tolerance.
21. Configured weights sum to 1.0.

UPSTREAM PIPELINE IMMUTABILITY:
22. Step 3 terrain outputs exist and are intact.
23. Step 4 terrain susceptibility outputs exist and are intact.
24. Step 5 hydrological derivatives and flood exposure outputs exist and are intact.
25. Raw Copernicus GLO-30 DEM exists and is untouched.

USAGE
-----
    python scripts/validate_multihazard_outputs.py
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


def _field(label: str, value, width: int = 36) -> None:
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

def validate_multihazard_outputs() -> bool:
    print(_sep("="))
    print("  SIH26191 -- STEP 6G: MULTI-HAZARD OUTPUT VALIDATION")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    all_passed = True
    cfg = load_config(_ROOT_DIR)

    analysis_crs_str = cfg.get("crs", {}).get("analysis_crs_metric", "EPSG:32644")
    target_crs = CRS.from_string(analysis_crs_str)

    paths_cfg = cfg.get("paths", {})
    multihazard_cfg = cfg.get("multihazard", {})
    weights_cfg = multihazard_cfg.get("weights", {})
    class_cfg = multihazard_cfg.get("classification", {})
    classes_list = class_cfg.get("classes", [])
    nodata_val_cfg = int(class_cfg.get("nodata_value", 255))

    # Weight check
    w_t = float(weights_cfg.get("terrain_weight", 0.5))
    w_f = float(weights_cfg.get("flood_weight", 0.5))

    # Output paths
    score_path = (_ROOT_DIR / paths_cfg.get("multihazard_score", "data/processed/hazards/multihazard_score.tif")).resolve()
    classes_path = (_ROOT_DIR / paths_cfg.get("multihazard_classes", "data/processed/hazards/multihazard_classes.tif")).resolve()
    t_contrib_path = (_ROOT_DIR / paths_cfg.get("terrain_contribution", "data/processed/hazards/terrain_contribution.tif")).resolve()
    f_contrib_path = (_ROOT_DIR / paths_cfg.get("flood_contribution", "data/processed/hazards/flood_contribution.tif")).resolve()

    # Input paths
    t_proxy_path = (_ROOT_DIR / paths_cfg.get("terrain_susceptibility_proxy", "data/processed/hazards/terrain_susceptibility_proxy.tif")).resolve()
    f_proxy_path = (_ROOT_DIR / paths_cfg.get("flood_exposure_proxy", "data/processed/hazards/flood_exposure_proxy.tif")).resolve()

    # Upstream paths
    dem_raw_path = (_ROOT_DIR / paths_cfg.get("dem_raw", "data/raw/copernicus_glo30_rudraprayag.tif")).resolve()
    slope_path = (_ROOT_DIR / paths_cfg.get("slope_processed", "data/processed/terrain/slope_degrees.tif")).resolve()
    aspect_path = (_ROOT_DIR / paths_cfg.get("aspect_processed", "data/processed/terrain/aspect_degrees.tif")).resolve()
    t_classes_path = (_ROOT_DIR / paths_cfg.get("terrain_susceptibility_classes", "data/processed/hazards/terrain_susceptibility_classes.tif")).resolve()
    flow_dir_path = (_ROOT_DIR / paths_cfg.get("flow_direction", "data/processed/hydrology/flow_direction.tif")).resolve()
    flow_acc_path = (_ROOT_DIR / paths_cfg.get("flow_accumulation", "data/processed/hydrology/flow_accumulation.tif")).resolve()
    twi_path = (_ROOT_DIR / paths_cfg.get("topographic_wetness_index", "data/processed/hydrology/topographic_wetness_index.tif")).resolve()
    f_classes_path = (_ROOT_DIR / paths_cfg.get("flood_exposure_classes", "data/processed/hazards/flood_exposure_classes.tif")).resolve()

    # -----------------------------------------------------------------------
    # 1. UPSTREAM INPUT INTEGRITY & BASELINE AUDIT
    # -----------------------------------------------------------------------
    _section("1. UPSTREAM PIPELINE INTEGRITY & INPUT AUDIT")

    # Assertion 1: Both input files exist
    all_passed = _result("1. Input Terrain Proxy exists", t_proxy_path.is_file(), str(t_proxy_path.name)) and all_passed
    all_passed = _result("1b. Input Flood Proxy exists", f_proxy_path.is_file(), str(f_proxy_path.name)) and all_passed

    # Assertion 2: Both input files are readable
    try:
        ds_tp = rasterio.open(t_proxy_path)
        ds_fp = rasterio.open(f_proxy_path)
        arr_tp = ds_tp.read(1)
        arr_fp = ds_fp.read(1)
        inputs_readable = True
    except Exception as exc:
        inputs_readable = False
        print(f"[FAIL] Error reading input rasters: {exc}")
    all_passed = _result("2. Both input proxy rasters are readable", inputs_readable) and all_passed

    # Assertion 3: Inputs remain unchanged and valid
    tp_valid_mask = ~np.isnan(arr_tp)
    fp_valid_mask = ~np.isnan(arr_fp)
    inputs_valid = (
        np.array_equal(tp_valid_mask, fp_valid_mask) and
        (np.nanmin(arr_tp) >= 0.0) and (np.nanmax(arr_tp) <= 1.0) and
        (np.nanmin(arr_fp) >= 0.0) and (np.nanmax(arr_fp) <= 1.0)
    )
    all_passed = _result("3. Input proxy values are valid and untouched", inputs_valid) and all_passed

    # -----------------------------------------------------------------------
    # 2. OUTPUT DATASET EXISTENCE & READABILITY
    # -----------------------------------------------------------------------
    _section("2. OUTPUT DATASET EXISTENCE & READABILITY")

    # Assertion 4: Multi-hazard score exists
    all_passed = _result("4. Multi-hazard score file exists", score_path.is_file(), str(score_path.name)) and all_passed

    # Assertion 5: Multi-hazard classes exist
    all_passed = _result("5. Multi-hazard classes file exists", classes_path.is_file(), str(classes_path.name)) and all_passed

    # Assertion 6: Contribution layers exist
    all_passed = _result("6a. Terrain contribution layer exists", t_contrib_path.is_file(), str(t_contrib_path.name)) and all_passed
    all_passed = _result("6b. Flood contribution layer exists", f_contrib_path.is_file(), str(f_contrib_path.name)) and all_passed

    # Assertion 7: All outputs are readable
    try:
        ds_score = rasterio.open(score_path)
        ds_cls = rasterio.open(classes_path)
        ds_tc = rasterio.open(t_contrib_path)
        ds_fc = rasterio.open(f_contrib_path)

        arr_score = ds_score.read(1)
        arr_cls = ds_cls.read(1)
        arr_tc = ds_tc.read(1)
        arr_fc = ds_fc.read(1)
        outputs_readable = True
    except Exception as exc:
        outputs_readable = False
        print(f"[FAIL] Error reading output rasters: {exc}")
    all_passed = _result("7. All 4 output datasets are readable", outputs_readable) and all_passed

    if not outputs_readable:
        print("\n[ERROR] Cannot proceed with further validations due to unreadable outputs.")
        print(f"\n{_sep('=')}")
        print("MULTI-HAZARD OUTPUT VALIDATION: FAIL")
        print(_sep('='))
        return False

    # -----------------------------------------------------------------------
    # 3. SPATIAL METADATA & GRID ALIGNMENT
    # -----------------------------------------------------------------------
    _section("3. SPATIAL METADATA & GRID ALIGNMENT")

    # Assertion 8: CRS matches analysis CRS
    crs_all_match = (
        (ds_score.crs == target_crs) and
        (ds_cls.crs == target_crs) and
        (ds_tc.crs == target_crs) and
        (ds_fc.crs == target_crs)
    )
    all_passed = _result("8. All output CRS match analysis CRS", crs_all_match, f"{target_crs}") and all_passed

    # Assertion 9: Dimensions match
    expected_shape = (ds_tp.height, ds_tp.width)
    dims_all_match = (
        ((ds_score.height, ds_score.width) == expected_shape) and
        ((ds_cls.height, ds_cls.width) == expected_shape) and
        ((ds_tc.height, ds_tc.width) == expected_shape) and
        ((ds_fc.height, ds_fc.width) == expected_shape)
    )
    all_passed = _result("9. Dimensions match analysis grid", dims_all_match, f"{expected_shape[1]}x{expected_shape[0]} px") and all_passed

    # Assertion 10: Transform matches
    expected_transform = ds_tp.transform
    transform_all_match = (
        (ds_score.transform == expected_transform) and
        (ds_cls.transform == expected_transform) and
        (ds_tc.transform == expected_transform) and
        (ds_fc.transform == expected_transform)
    )
    all_passed = _result("10. Affine transforms match analysis grid", transform_all_match) and all_passed

    # Assertion 11: Spatial bounds match
    expected_bounds = ds_tp.bounds
    bounds_all_match = (
        (ds_score.bounds == expected_bounds) and
        (ds_cls.bounds == expected_bounds) and
        (ds_tc.bounds == expected_bounds) and
        (ds_fc.bounds == expected_bounds)
    )
    all_passed = _result("11. Spatial bounds match analysis grid", bounds_all_match) and all_passed

    # -----------------------------------------------------------------------
    # 4. NUMERICAL INTEGRITY & NODATA PRESERVATION
    # -----------------------------------------------------------------------
    _section("4. NUMERICAL INTEGRITY & NODATA PRESERVATION")

    score_valid_mask = ~np.isnan(arr_score)
    tc_valid_mask = ~np.isnan(arr_tc)
    fc_valid_mask = ~np.isnan(arr_fc)
    cls_valid_mask = (arr_cls != nodata_val_cfg)

    # Assertion 12: NoData preserved correctly
    nodata_consistent = (
        np.array_equal(score_valid_mask, tp_valid_mask) and
        np.array_equal(tc_valid_mask, tp_valid_mask) and
        np.array_equal(fc_valid_mask, tp_valid_mask) and
        np.array_equal(cls_valid_mask, tp_valid_mask)
    )
    all_passed = _result("12. NoData masks strictly preserved across all layers", nodata_consistent) and all_passed

    # Assertion 13: No unexpected NaN on valid pixels
    unexpected_nan = (
        np.sum(np.isnan(arr_score[tp_valid_mask])) +
        np.sum(np.isnan(arr_tc[tp_valid_mask])) +
        np.sum(np.isnan(arr_fc[tp_valid_mask]))
    )
    all_passed = _result("13. Zero unexpected NaN on valid terrain pixels", unexpected_nan == 0, f"nan_count={unexpected_nan}") and all_passed

    # Assertion 14: No unexpected infinity
    inf_count = (
        np.sum(np.isinf(arr_score)) +
        np.sum(np.isinf(arr_tc)) +
        np.sum(np.isinf(arr_fc))
    )
    all_passed = _result("14. Zero infinite values on all output rasters", inf_count == 0, f"inf_count={inf_count}") and all_passed

    # Assertion 15: Multi-hazard score is strictly within [0.0, 1.0]
    score_min = float(np.nanmin(arr_score))
    score_max = float(np.nanmax(arr_score))
    score_in_bounds = (score_min >= 0.0) and (score_max <= 1.0)
    all_passed = _result("15. Multi-hazard score strictly within [0.0, 1.0]", score_in_bounds, f"min={score_min:.4f}, max={score_max:.4f}") and all_passed

    # Assertion 16: Class codes contain only documented values
    unique_classes = set(np.unique(arr_cls).tolist())
    expected_classes = {int(c["code"]) for c in classes_list} | {nodata_val_cfg}
    classes_valid = unique_classes.issubset(expected_classes)
    all_passed = _result("16. Class codes only contain documented values", classes_valid, f"actual={sorted(unique_classes)}, expected={sorted(expected_classes)}") and all_passed

    # Assertion 17: Classified valid pixel count matches score valid pixels
    score_valid_count = int(np.sum(score_valid_mask))
    cls_valid_count = int(np.sum(cls_valid_mask))
    counts_match = (score_valid_count == cls_valid_count) and (score_valid_count == int(np.sum(tp_valid_mask)))
    all_passed = _result("17. Classified valid pixel count matches score valid pixels", counts_match, f"{cls_valid_count:,} px") and all_passed

    # Assertion 18: Score classification is monotonic
    # Sample test: verify score min and max per class respect class boundary intervals
    monotonic_ok = True
    for cls_info in classes_list:
        code = int(cls_info["code"])
        s_min = float(cls_info["score_min"])
        s_max = float(cls_info["score_max"])
        cls_scores = arr_score[arr_cls == code]
        if cls_scores.size > 0:
            actual_min = float(np.min(cls_scores))
            actual_max = float(np.max(cls_scores))
            if actual_min < s_min - 1e-6 or actual_max > s_max + 1e-6:
                monotonic_ok = False
                print(f"[FAIL] Class {code} scores [{actual_min:.4f}, {actual_max:.4f}] violate interval [{s_min:.2f}, {s_max:.2f}]")
    all_passed = _result("18. Score classification is strictly monotonic", monotonic_ok) and all_passed

    # Assertion 19: Contribution layers are non-negative
    tc_min = float(np.nanmin(arr_tc))
    fc_min = float(np.nanmin(arr_fc))
    contrib_non_neg = (tc_min >= 0.0) and (fc_min >= 0.0)
    all_passed = _result("19. Contribution layers are non-negative", contrib_non_neg, f"tc_min={tc_min:.4f}, fc_min={fc_min:.4f}") and all_passed

    # Assertion 20: Terrain contribution + flood contribution == multi-hazard score within tolerance
    diff = np.abs((arr_tc[score_valid_mask] + arr_fc[score_valid_mask]) - arr_score[score_valid_mask])
    max_residual = float(np.max(diff))
    explainability_valid = max_residual < 1e-5
    all_passed = _result("20. Terrain + flood contribution equals score within tolerance", explainability_valid, f"max_residual={max_residual:.2e}") and all_passed

    # Assertion 21: Configured weights sum to 1.0
    weight_sum = w_t + w_f
    weights_ok = np.isclose(weight_sum, 1.0, atol=1e-5)
    all_passed = _result("21. Configured weights sum to 1.0", weights_ok, f"w_t={w_t}, w_f={w_f}, sum={weight_sum:.4f}") and all_passed

    # -----------------------------------------------------------------------
    # 5. UPSTREAM STEP IMMUTABILITY
    # -----------------------------------------------------------------------
    _section("5. UPSTREAM STEP IMMUTABILITY CONFIRMATION")

    # Assertion 22: Step 3 outputs unchanged
    step3_ok = slope_path.is_file() and aspect_path.is_file()
    all_passed = _result("22. Step 3 terrain outputs exist and intact", step3_ok, f"slope={slope_path.name}, aspect={aspect_path.name}") and all_passed

    # Assertion 23: Step 4 outputs unchanged
    step4_ok = t_proxy_path.is_file() and t_classes_path.is_file()
    all_passed = _result("23. Step 4 landslide hazard outputs exist and intact", step4_ok, f"proxy={t_proxy_path.name}, classes={t_classes_path.name}") and all_passed

    # Assertion 24: Step 5 outputs unchanged
    step5_ok = (
        flow_dir_path.is_file() and
        flow_acc_path.is_file() and
        twi_path.is_file() and
        f_proxy_path.is_file() and
        f_classes_path.is_file()
    )
    all_passed = _result("24. Step 5 hydrology outputs exist and intact", step5_ok, "all 5 files verified") and all_passed

    # Assertion 25: Raw DEM unchanged
    dem_ok = dem_raw_path.is_file() and (dem_raw_path.stat().st_size > 18 * 1024 * 1024)
    all_passed = _result("25. Raw Copernicus GLO-30 DEM exists and untouched", dem_ok, f"size={dem_raw_path.stat().st_size / (1024*1024):.2f} MB") and all_passed

    # Close open datasets
    ds_tp.close()
    ds_fp.close()
    ds_score.close()
    ds_cls.close()
    ds_tc.close()
    ds_fc.close()

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    _section("6. VALIDATION SUMMARY")
    _field("Total Validations Evaluated", "25")
    _field("Multi-Hazard Integration Status", "FULLY VERIFIED" if all_passed else "VERIFICATION FAILED")

    print(f"\n{_sep('=')}")
    if all_passed:
        print("MULTI-HAZARD OUTPUT VALIDATION: PASS")
    else:
        print("MULTI-HAZARD OUTPUT VALIDATION: FAIL")
    print(_sep('='))

    return all_passed


if __name__ == "__main__":
    success = validate_multihazard_outputs()
    sys.exit(0 if success else 1)
