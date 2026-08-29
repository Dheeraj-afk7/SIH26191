#!/usr/bin/env python3
"""
SIH26191 -- Step 4E: Classify Terrain Susceptibility Proxy
==============================================================================
Classifies the continuous terrain-derived landslide susceptibility proxy into
transparent, explainable preliminary screening categories using configuration-driven
threshold intervals.

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

CLASSIFICATION SCHEME & RATIONALE
---------------------------------
1. Dynamic Configuration:
   - All interval thresholds, class codes, and labels are read dynamically from
     configs/project.yaml -> terrain_susceptibility.classification.

2. Standard Screening Categories (from project.yaml):
   - Class 1: Lower Terrain Susceptibility Indicator   (Score in [0.00, 0.35), Slope < 21.0 deg)
   - Class 2: Moderate Terrain Susceptibility Indicator(Score in [0.35, 0.65), Slope 21.0-39.0 deg)
   - Class 3: Higher Terrain Susceptibility Indicator  (Score in [0.65, 1.00], Slope >= 39.0 deg)
   - NoData (255): Unmapped / outside analysis extent / source DEM NoData

3. Explicit Non-Claims:
   - Categories represent preliminary terrain steepness screening indicators.
   - They DO NOT declare land as "Safe", "Unsafe", "Guaranteed Hazard", or "Landslide Zone".
   - They DO NOT constitute an official government hazard map or engineering certification.

OUTPUT
------
  data/processed/hazards/terrain_susceptibility_classes.tif

  CRS   : EPSG:32644 (WGS 84 / UTM Zone 44N)
  Dtype : uint8
  NoData: 255
  Classes: 1, 2, 3

USAGE
-----
    python processing/hazards/classify_terrain_susceptibility.py
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
# Core Classification Logic
# ---------------------------------------------------------------------------

def classify_terrain_susceptibility() -> bool:
    print(_sep("="))
    print("  SIH26191 -- STEP 4E: CLASSIFY TERRAIN SUSCEPTIBILITY PROXY")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    all_passed = True
    cfg = load_config()

    # Read configuration parameters
    suscept_cfg = cfg.get("terrain_susceptibility", {})
    class_cfg = suscept_cfg.get("classification", {})
    output_cfg = suscept_cfg.get("output", {})
    paths_cfg = cfg.get("paths", {})
    crs_cfg = cfg.get("crs", {})

    analysis_crs_str = crs_cfg.get("analysis_crs_metric", "EPSG:32644")
    target_crs = CRS.from_string(analysis_crs_str)

    proxy_rel = paths_cfg.get("terrain_susceptibility_proxy", "data/processed/hazards/terrain_susceptibility_proxy.tif")
    classes_rel = paths_cfg.get("terrain_susceptibility_classes", "data/processed/hazards/terrain_susceptibility_classes.tif")

    proxy_path = (_ROOT_DIR / proxy_rel).resolve()
    output_path = (_ROOT_DIR / classes_rel).resolve()

    classes_list = class_cfg.get("classes", [])
    nodata_val = int(class_cfg.get("nodata_value", 255))

    _section("1. CONFIGURATION & CLASSIFICATION SCHEME")
    _field("Classification method", class_cfg.get("method", "threshold_intervals"))
    _field("NoData value", str(nodata_val))
    _field("Configured classes count", str(len(classes_list)))

    for c in classes_list:
        code = c.get("code")
        label = c.get("label")
        s_min = c.get("score_min")
        s_max = c.get("score_max")
        s_range = c.get("slope_approx_range", "")
        _field(f"  Class {code}", f"{label} [Score: {s_min} - {s_max}, Slope: {s_range}]")

    # Verify input existence
    _section("2. READ CONTINUOUS PROXY INPUT")
    if not proxy_path.is_file():
        print(f"[FAIL] Continuous proxy raster not found: {proxy_path}")
        return False
    _field("Continuous proxy path", str(proxy_path))

    with rasterio.open(proxy_path) as src:
        proxy_crs = src.crs
        proxy_transform = src.transform
        proxy_w, proxy_h = src.width, src.height
        proxy_profile = src.profile.copy()
        proxy_nodata = src.nodata
        proxy_data = src.read(1)

    all_passed &= _result("Proxy CRS matches analysis CRS", proxy_crs == target_crs, f"{proxy_crs}")

    # 3. Classify raster
    _section("3. CLASSIFICATION PROCESSING")
    total_pixels = proxy_data.size
    nan_mask = np.isnan(proxy_data)
    nodata_mask = nan_mask if (proxy_nodata is None or np.isnan(proxy_nodata)) else (nan_mask | (proxy_data == proxy_nodata))
    valid_mask = ~nodata_mask
    valid_count = int(np.sum(valid_mask))
    nodata_count = int(np.sum(nodata_mask))

    _field("Total raster pixels", f"{total_pixels:,}")
    _field("Valid pixels to classify", f"{valid_count:,} ({valid_count/total_pixels*100:.2f}%)")
    _field("NoData pixels", f"{nodata_count:,} ({nodata_count/total_pixels*100:.2f}%)")

    # Allocate UInt8 array initialized to NoData (255)
    classified_data = np.full(proxy_data.shape, nodata_val, dtype=np.uint8)

    # Classify each interval deterministically
    class_stats = []
    total_assigned_valid = 0

    for i, c in enumerate(classes_list):
        code = int(c.get("code"))
        label = str(c.get("label"))
        s_min = float(c.get("score_min"))
        s_max = float(c.get("score_max"))

        # For the last class, include the upper boundary score_max (e.g. score <= 1.0)
        is_last = (i == len(classes_list) - 1)
        if is_last:
            mask = valid_mask & (proxy_data >= s_min) & (proxy_data <= s_max)
        else:
            mask = valid_mask & (proxy_data >= s_min) & (proxy_data < s_max)

        classified_data[mask] = code
        count = int(np.sum(mask))
        pct_valid = (count / valid_count * 100.0) if valid_count > 0 else 0.0
        pct_total = (count / total_pixels * 100.0)
        total_assigned_valid += count
        class_stats.append((code, label, count, pct_valid, pct_total))

    _section("4. CLASSIFICATION DISTRIBUTION")
    print(f"  {'Code':<6} {'Class Label':<44} {'Pixel Count':<14} {'% Valid':<10} {'% Total':<10}")
    print(f"  {'-'*6} {'-'*44} {'-'*14} {'-'*10} {'-'*10}")
    for code, label, count, pct_v, pct_t in class_stats:
        print(f"  {code:<6} {label:<44} {count:>12,} {pct_v:>8.2f}% {pct_t:>8.2f}%")
    print(f"  {nodata_val:<6} {'NoData / Out of Extent':<44} {nodata_count:>12,} {'---':>8} {nodata_count/total_pixels*100:>8.2f}%")

    all_assigned_ok = (total_assigned_valid == valid_count)
    all_passed &= _result("All valid pixels assigned to documented classes", all_assigned_ok,
                          f"assigned={total_assigned_valid:,}, valid={valid_count:,}")

    # Check for unexpected class values
    unique_vals = set(np.unique(classified_data).tolist())
    expected_vals = set([c["code"] for c in classes_list] + [nodata_val])
    unexpected = unique_vals - expected_vals
    all_passed &= _result("No unexpected class codes in output", len(unexpected) == 0,
                          f"unique={unique_vals}")

    # 4. Save GeoTIFF output
    _section("5. WRITE CLASSIFIED GEOTIFF OUTPUT")
    _field("Output destination", str(output_path))

    out_profile = proxy_profile.copy()
    out_profile.update({
        "driver": "GTiff",
        "dtype": "uint8",
        "nodata": nodata_val,
        "width": proxy_w,
        "height": proxy_h,
        "count": 1,
        "crs": target_crs,
        "transform": proxy_transform,
        "compress": "lzw",
        "tiled": False
    })

    try:
        with rasterio.open(output_path, "w", **out_profile) as dst:
            dst.write(classified_data, 1)
            dst.set_band_description(1, "Terrain-Derived Landslide Susceptibility Screening Classes (1=Lower, 2=Moderate, 3=Higher, 255=NoData)")
            dst.update_tags(
                TITLE="Terrain-Derived Landslide Susceptibility Screening Classes",
                PROJECT_ID="SIH26191",
                PILOT_DISTRICT="Rudraprayag",
                STATE="Uttarakhand",
                METHODOLOGY="Configuration-driven threshold intervals",
                CLASS_1="Lower Terrain Susceptibility Indicator (Score 0.0-0.35, Slope < 21 deg)",
                CLASS_2="Moderate Terrain Susceptibility Indicator (Score 0.35-0.65, Slope 21-39 deg)",
                CLASS_3="Higher Terrain Susceptibility Indicator (Score 0.65-1.00, Slope >= 39 deg)",
                NODATA_VALUE=str(nodata_val),
                DISCLAIMER=output_cfg.get("disclaimer", "Decision Support Layer Only")
            )
        all_passed &= _result("Classified GeoTIFF written successfully", output_path.is_file(),
                              f"Size: {output_path.stat().st_size / (1024*1024):.2f} MB")
    except Exception as e:
        print(f"[FAIL] Failed to write classified GeoTIFF: {e}")
        all_passed = False

    # Summary
    print(f"\n{_sep('=')}")
    if all_passed:
        print("TERRAIN SUSCEPTIBILITY CLASSIFICATION: PASS")
    else:
        print("TERRAIN SUSCEPTIBILITY CLASSIFICATION: FAIL")
    print(_sep('='))

    return all_passed


if __name__ == "__main__":
    success = classify_terrain_susceptibility()
    sys.exit(0 if success else 1)
