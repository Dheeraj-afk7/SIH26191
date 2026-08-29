#!/usr/bin/env python3
"""
SIH26191 -- Step 6E: Classify Multi-Hazard Screening Score
==============================================================================
Classifies the continuous Multi-Hazard Screening Score into transparent,
explainable preliminary screening categories using configuration-driven
threshold intervals.

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

CLASSIFICATION SCHEME & RATIONALE
---------------------------------
1. Dynamic Configuration:
   - All interval thresholds, class codes, and labels are read dynamically from
     configs/project.yaml -> multihazard.classification.

2. Standard Screening Categories (from project.yaml):
   - Class 1: Lower Multi-Hazard Indicator   (Score in [0.00, 0.35))
   - Class 2: Moderate Multi-Hazard Indicator(Score in [0.35, 0.65))
   - Class 3: Higher Multi-Hazard Indicator  (Score in [0.65, 1.00])
   - NoData (255): Unmapped / outside analysis extent / source DEM NoData

3. Explicit Non-Claims:
   - Categories represent preliminary multi-hazard screening indicators.
   - They DO NOT declare land as "Safe", "Unsafe", "Guaranteed Hazard", "Official Hazard Zone",
     or "Candidate Hazard-Based Red Zone".
   - They DO NOT constitute an official government hazard map or relocation authorization.

OUTPUT
------
  data/processed/hazards/multihazard_classes.tif

  CRS   : EPSG:32644 (WGS 84 / UTM Zone 44N)
  Dtype : uint8
  NoData: 255
  Classes: 1, 2, 3

USAGE
-----
    python processing/multihazard/classify_multihazard.py
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
# Core Classification Logic
# ---------------------------------------------------------------------------

def classify_multihazard() -> bool:
    print(_sep("="))
    print("  SIH26191 -- STEP 6E: CLASSIFY MULTI-HAZARD SCREENING SCORE")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    all_passed = True
    cfg = load_config()

    # Read configuration parameters
    multihazard_cfg = cfg.get("multihazard", {})
    class_cfg = multihazard_cfg.get("classification", {})
    outputs_cfg = multihazard_cfg.get("outputs", {})
    paths_cfg = cfg.get("paths", {})
    crs_cfg = cfg.get("crs", {})

    analysis_crs_str = crs_cfg.get("analysis_crs_metric", "EPSG:32644")
    target_crs = CRS.from_string(analysis_crs_str)

    score_rel = outputs_cfg.get(
        "multihazard_score",
        paths_cfg.get("multihazard_score", "data/processed/hazards/multihazard_score.tif")
    )
    classes_rel = outputs_cfg.get(
        "multihazard_classes",
        paths_cfg.get("multihazard_classes", "data/processed/hazards/multihazard_classes.tif")
    )

    score_path = (_ROOT_DIR / score_rel).resolve()
    output_path = (_ROOT_DIR / classes_rel).resolve()

    classes_list = class_cfg.get("classes", [])
    nodata_val = int(class_cfg.get("nodata_value", 255))

    _section("1. CONFIGURATION & CLASSIFICATION SCHEME")
    _field("Configured Analysis Metric CRS", analysis_crs_str)
    _field("Input Multi-Hazard Score Path", str(score_path))
    _field("Output Classified Raster Path", str(output_path))
    _field("NoData Class Code", str(nodata_val))
    _field("Configured Class Count", len(classes_list))

    print("\n  Configured Classification Intervals:")
    for i, cls_info in enumerate(classes_list):
        code = cls_info.get("code")
        label = cls_info.get("label")
        s_min = cls_info.get("score_min")
        s_max = cls_info.get("score_max")
        close_bracket = "]" if (i == len(classes_list) - 1 or int(code) == 3) else ")"
        print(f"    Class {code}: [{s_min:.2f}, {s_max:.2f}{close_bracket} -> {label}")

    if not classes_list:
        print("[FAIL] No classification classes defined in configuration.")
        return False

    # 2. Input Raster Verification
    _section("2. INPUT RASTER LOADING")
    if not score_path.is_file():
        print(f"[FAIL] Multi-hazard score raster not found: {score_path}")
        return False

    with rasterio.open(score_path) as ds:
        arr_score = ds.read(1)
        profile = ds.profile.copy()
        crs_in = ds.crs
        res_in = ds.res
        transform_in = ds.transform
        shape_in = arr_score.shape

    _field("Input CRS", str(crs_in))
    _field("Input Dimensions (W x H)", f"{shape_in[1]} x {shape_in[0]} px")
    _field("Input Pixel Resolution", f"{res_in[0]:.4f} m x {res_in[1]:.4f} m")

    _result("Input CRS matches analysis metric CRS", crs_in == target_crs, str(crs_in))

    # 3. Array Classification
    _section("3. DISCRETIZATION & CLASSIFICATION")

    valid_mask = ~np.isnan(arr_score)
    total_px = arr_score.size
    valid_count = int(np.sum(valid_mask))
    nodata_count = total_px - valid_count

    # Initialize output array with NoData value
    arr_classes = np.full(shape_in, nodata_val, dtype=np.uint8)

    # Apply interval rules
    # Classes are evaluated in order; last class includes the upper bound (1.00)
    for i, cls_info in enumerate(classes_list):
        code = int(cls_info["code"])
        s_min = float(cls_info["score_min"])
        s_max = float(cls_info["score_max"])

        if i == len(classes_list) - 1:
            # Last class: inclusive upper bound [s_min, s_max]
            cls_mask = valid_mask & (arr_score >= s_min) & (arr_score <= s_max)
        else:
            # Intermediate classes: half-open interval [s_min, s_max)
            cls_mask = valid_mask & (arr_score >= s_min) & (arr_score < s_max)

        arr_classes[cls_mask] = np.uint8(code)

    # 4. Class Distribution & Spatial Statistics
    _section("4. CLASSIFICATION DISTRIBUTION AUDIT")

    # Cell area in sq km and hectares (from metric resolution)
    pixel_area_m2 = res_in[0] * res_in[1]
    pixel_area_ha = pixel_area_m2 / 10000.0
    pixel_area_km2 = pixel_area_m2 / 1000000.0

    _field("Pixel Ground Area", f"{pixel_area_m2:.2f} m2 ({pixel_area_ha:.4f} ha)")

    print(f"\n  {'Code':<6} {'Screening Level':<38} {'Pixels':<12} {'Area (ha)':<14} {'Area (km2)':<12} {'Valid %':<10}")
    print(f"  {'-'*6} {'-'*38} {'-'*12} {'-'*14} {'-'*12} {'-'*10}")

    total_classified_valid = 0
    for cls_info in classes_list:
        code = int(cls_info["code"])
        label = cls_info["label"]
        cnt = int(np.sum(arr_classes == code))
        total_classified_valid += cnt
        ha = cnt * pixel_area_ha
        km2 = cnt * pixel_area_km2
        pct = (cnt / valid_count * 100.0) if valid_count > 0 else 0.0
        print(f"  {code:<6} {label:<38} {cnt:<12,} {ha:<14.2f} {km2:<12.2f} {pct:<9.2f}%")

    nodata_actual = int(np.sum(arr_classes == nodata_val))
    print(f"  {nodata_val:<6} {'NoData / Outside Analysis Grid':<38} {nodata_actual:<12,} {nodata_actual*pixel_area_ha:<14.2f} {nodata_actual*pixel_area_km2:<12.2f} {'--':<10}")

    # Check that all valid pixels received a valid class code (1, 2, or 3)
    unassigned_count = valid_count - total_classified_valid
    all_passed = _result(
        "All valid score pixels assigned to a class",
        unassigned_count == 0,
        f"unassigned={unassigned_count}"
    ) and all_passed

    all_passed = _result(
        "NoData pixel count exactly matches input score",
        nodata_actual == nodata_count,
        f"actual={nodata_actual:,}, expected={nodata_count:,}"
    ) and all_passed

    # 5. GeoTIFF Output Writing
    _section("5. GEOTIFF EXPORT")

    out_profile = profile.copy()
    out_profile.update({
        "driver": "GTiff",
        "height": shape_in[0],
        "width": shape_in[1],
        "count": 1,
        "dtype": "uint8",
        "crs": target_crs,
        "transform": transform_in,
        "nodata": nodata_val,
        "compress": "deflate",
        "predictor": 1,
        "tiled": True,
        "blockxsize": 256,
        "blockysize": 256,
    })

    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"  Writing Classified Multi-Hazard GeoTIFF -> {output_path.relative_to(_ROOT_DIR)}")
    with rasterio.open(output_path, "w", **out_profile) as dst:
        dst.write(arr_classes, 1)
        dst.set_band_description(1, "Multi-Hazard Screening Classes (1=Lower, 2=Moderate, 3=Higher, 255=NoData)")

    all_passed = _result("Classified GeoTIFF exists and is written", output_path.is_file()) and all_passed

    print(f"\n{_sep('=')}")
    if all_passed:
        print("MULTI-HAZARD CLASSIFICATION: PASS")
    else:
        print("MULTI-HAZARD CLASSIFICATION: FAIL")
    print(_sep('='))

    return all_passed


if __name__ == "__main__":
    success = classify_multihazard()
    sys.exit(0 if success else 1)
