#!/usr/bin/env python3
"""
SIH26191 -- Step 7A: Candidate Hazard-Based Red Zone Input Inspection
==============================================================================
Validates the availability, spatial reference, resolution, transform, spatial
bounds, NoData characteristics, class distribution, and score consistency of
the upstream Step 6 Multi-Hazard outputs:
  1. Multi-Hazard Screening Score (data/processed/hazards/multihazard_score.tif)
  2. Multi-Hazard Screening Classes (data/processed/hazards/multihazard_classes.tif)

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

MANDATORY RULES
---------------
1. Raw DEM and upstream Step 3-6 outputs are STRICTLY READ-ONLY.
2. Configuration is loaded dynamically from configs/project.yaml.
3. No processing artifacts are written during this inspection.
4. Output must terminate with 'RED ZONE INPUT INSPECTION: PASS / FAIL'.

USAGE
-----
    python scripts/inspect_redzone_inputs.py
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
# Main Inspection Logic
# ---------------------------------------------------------------------------

def inspect_redzone_inputs() -> bool:
    print(_sep("="))
    print("  SIH26191 -- STEP 7A: RED ZONE INPUT INSPECTION")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    all_passed = True
    cfg = load_config(_ROOT_DIR)

    # 1. Resolve paths dynamically
    paths_cfg = cfg.get("paths", {})
    multihazard_cfg = cfg.get("multihazard", {})
    mh_outputs = multihazard_cfg.get("outputs", {})

    score_rel = mh_outputs.get("multihazard_score", paths_cfg.get("multihazard_score", "data/processed/hazards/multihazard_score.tif"))
    class_rel = mh_outputs.get("multihazard_classes", paths_cfg.get("multihazard_classes", "data/processed/hazards/multihazard_classes.tif"))

    score_path = _ROOT_DIR / score_rel
    class_path = _ROOT_DIR / class_rel

    expected_crs_str = cfg.get("crs", {}).get("analysis_crs_metric", "EPSG:32644")

    # -----------------------------------------------------------------------
    _section("1. File Existence & Readability")
    # -----------------------------------------------------------------------
    ok_score_exists = score_path.is_file()
    ok_class_exists = class_path.is_file()

    all_passed &= _result("Multi-hazard score exists", ok_score_exists, str(score_path))
    all_passed &= _result("Multi-hazard class raster exists", ok_class_exists, str(class_path))

    if not (ok_score_exists and ok_class_exists):
        print("\n[ERROR] Required Step 6 multi-hazard raster inputs are missing. Stopping inspection.")
        print(f"\nRED ZONE INPUT INSPECTION: FAIL")
        return False

    # -----------------------------------------------------------------------
    _section("2. Dataset Opening & Spatial Alignment")
    # -----------------------------------------------------------------------
    try:
        ds_score = rasterio.open(score_path)
        ds_class = rasterio.open(class_path)
    except Exception as e:
        print(f"  [FAIL] Failed to open rasters with rasterio: {e}")
        print(f"\nRED ZONE INPUT INSPECTION: FAIL")
        return False

    with ds_score, ds_class:
        # Check CRS
        score_crs = ds_score.crs
        class_crs = ds_class.crs
        expected_crs = CRS.from_string(expected_crs_str)

        ok_crs_score = (score_crs == expected_crs)
        ok_crs_class = (class_crs == expected_crs)
        ok_crs_match = (score_crs == class_crs)

        all_passed &= _result(f"Score CRS matches configured analysis CRS ({expected_crs_str})", ok_crs_score, str(score_crs))
        all_passed &= _result(f"Class CRS matches configured analysis CRS ({expected_crs_str})", ok_crs_class, str(class_crs))
        all_passed &= _result("CRS alignment between score and class raster", ok_crs_match)

        # Check Dimensions
        shape_score = (ds_score.height, ds_score.width)
        shape_class = (ds_class.height, ds_class.width)
        ok_dims = (shape_score == shape_class)
        all_passed &= _result(f"Grid dimensions match: {shape_score[1]} x {shape_score[0]} px", ok_dims, f"Score={shape_score}, Class={shape_class}")

        # Check Transform
        transform_score = ds_score.transform
        transform_class = ds_class.transform
        ok_transform = (transform_score == transform_class)
        all_passed &= _result("Affine geotransform exact match", ok_transform)

        # Check Bounds
        bounds_score = ds_score.bounds
        bounds_class = ds_class.bounds
        ok_bounds = (bounds_score == bounds_class)
        all_passed &= _result("Spatial bounding coordinates match", ok_bounds)

        # Check Resolution
        res_score = (abs(ds_score.res[0]), abs(ds_score.res[1]))
        res_class = (abs(ds_class.res[0]), abs(ds_class.res[1]))
        ok_res = np.allclose(res_score, res_class, rtol=1e-5)
        all_passed &= _result(f"Spatial resolution: {res_score[0]:.4f} m x {res_score[1]:.4f} m", ok_res)

        # -------------------------------------------------------------------
        _section("3. Datatypes and NoData Settings")
        # -------------------------------------------------------------------
        score_dtype = ds_score.dtypes[0]
        class_dtype = ds_class.dtypes[0]
        score_nodata = ds_score.nodata
        class_nodata = ds_class.nodata

        ok_score_dtype = score_dtype in ("float32", "float64")
        ok_class_dtype = class_dtype in ("uint8", "int16", "uint16", "int32")
        all_passed &= _result(f"Score datatype: {score_dtype}", ok_score_dtype)
        all_passed &= _result(f"Class datatype: {class_dtype}", ok_class_dtype)
        all_passed &= _result(f"Score NoData value: {score_nodata}", np.isnan(score_nodata) if score_nodata is not None else False)
        all_passed &= _result(f"Class NoData value: {class_nodata}", class_nodata == 255.0 or class_nodata == 255)

        # -------------------------------------------------------------------
        _section("4. Array Analysis & Class Distribution")
        # -------------------------------------------------------------------
        score_arr = ds_score.read(1)
        class_arr = ds_class.read(1)

        total_pixels = score_arr.size
        _field("Total Raster Pixels", f"{total_pixels:,}")

        unique_classes, counts = np.unique(class_arr, return_counts=True)
        class_dict = dict(zip(unique_classes.tolist(), counts.tolist()))
        _field("Unique Class Values in Raster", sorted(list(unique_classes)))
        for c, cnt in sorted(class_dict.items()):
            pct = (cnt / total_pixels) * 100.0
            _field(f"  Class {c} Count", f"{cnt:,} ({pct:.2f}%)")

        # Documented classes check
        documented_classes = {1, 2, 3, 255}
        ok_classes = set(unique_classes).issubset(documented_classes)
        all_passed &= _result("Class raster contains only documented classes [1, 2, 3, 255]", ok_classes, str(unique_classes))

        # Check Class 3 exists
        class3_count = class_dict.get(3, 0)
        ok_class3_exists = class3_count > 0
        all_passed &= _result(f"Higher Multi-Hazard Indicator (Class 3) pixels exist", ok_class3_exists, f"{class3_count:,} pixels")

        # -------------------------------------------------------------------
        _section("5. Score Consistency with Classification")
        # -------------------------------------------------------------------
        valid_score_mask = ~np.isnan(score_arr)
        valid_class_mask = (class_arr != 255)

        ok_nodata_alignment = np.array_equal(valid_score_mask, valid_class_mask)
        all_passed &= _result("Valid pixel mask perfectly matches between score and class", ok_nodata_alignment)

        # Retrieve configured thresholds for Class 3
        classes_cfg = multihazard_cfg.get("classification", {}).get("classes", [])
        c3_cfg = next((c for c in classes_cfg if c.get("code") == 3), {})
        c3_min = float(c3_cfg.get("score_min", 0.65))
        c3_max = float(c3_cfg.get("score_max", 1.00))

        if ok_class3_exists:
            c3_mask = (class_arr == 3)
            c3_scores = score_arr[c3_mask]
            c3_score_min = float(np.nanmin(c3_scores))
            c3_score_max = float(np.nanmax(c3_scores))
            c3_score_mean = float(np.nanmean(c3_scores))

            _field("Class 3 Min Multi-Hazard Score", f"{c3_score_min:.6f}")
            _field("Class 3 Max Multi-Hazard Score", f"{c3_score_max:.6f}")
            _field("Class 3 Mean Multi-Hazard Score", f"{c3_score_mean:.6f}")

            # Every Class 3 pixel must satisfy score >= score_min and <= score_max
            ok_c3_range = (c3_score_min >= c3_min - 1e-5) and (c3_score_max <= c3_max + 1e-5)
            all_passed &= _result(
                f"Class 3 score consistency within [{c3_min:.2f}, {c3_max:.2f}]",
                ok_c3_range,
                f"Observed: [{c3_score_min:.4f}, {c3_score_max:.4f}]"
            )

    # -----------------------------------------------------------------------
    _section("Inspection Summary")
    # -----------------------------------------------------------------------
    status_str = "PASS" if all_passed else "FAIL"
    print(f"\nRED ZONE INPUT INSPECTION: {status_str}")
    return all_passed


if __name__ == "__main__":
    passed = inspect_redzone_inputs()
    sys.exit(0 if passed else 1)
