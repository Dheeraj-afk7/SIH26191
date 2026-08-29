#!/usr/bin/env python3
"""
SIH26191 — Central Project Configuration Validation Script
==============================================================================
Validates configs/project.yaml for YAML syntax, required project parameters,
standardized terminology, and raw DEM dataset existence.
"""

import sys
from pathlib import Path
import yaml


def validate_config():
    root_dir = Path(__file__).resolve().parent.parent
    config_path = root_dir / "configs" / "project.yaml"

    print("==================================================================")
    print("         SIH26191 -- CENTRAL CONFIGURATION VALIDATOR               ")
    print("==================================================================")
    print(f"Target Config Path: {config_path.relative_to(root_dir)}\n")

    overall_pass = True

    # 1. File existence check
    if not config_path.is_file():
        print(f"[FAIL] Config file not found at: {config_path}")
        print("\n================================================")
        print("CONFIG VALIDATION: FAIL")
        print("================================================")
        sys.exit(1)
    
    print("[PASS] Config file exists.")

    # 2. YAML syntax & load check
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        print("[PASS] YAML syntax is valid and parsed successfully.\n")
    except Exception as e:
        print(f"[FAIL] Failed to parse YAML file: {e}")
        print("\n================================================")
        print("CONFIG VALIDATION: FAIL")
        print("================================================")
        sys.exit(1)

    # Helper function for checking nested fields
    def get_nested(d, keys):
        curr = d
        for k in keys:
            if not isinstance(curr, dict) or k not in curr:
                return None
            curr = curr[k]
        return curr

    fields_to_check = [
        ("project.id", ["project", "id"]),
        ("project.pilot_district", ["project", "pilot_district"]),
        ("project.state", ["project", "state"]),
        ("project.country", ["project", "country"]),
        ("crs.storage_crs", ["crs", "storage_crs"]),
        ("crs.analysis_crs_metric", ["crs", "analysis_crs_metric"]),
        ("paths.dem_raw", ["paths", "dem_raw"]),
        ("terminology.hazard_zone_label", ["terminology", "hazard_zone_label"]),
        ("terminology.relocation_site_label", ["terminology", "relocation_site_label"]),
        ("terminology.carrying_capacity_label", ["terminology", "carrying_capacity_label"]),
        ("multihazard.enabled", ["multihazard", "enabled"]),
        ("multihazard.weights.terrain_weight", ["multihazard", "weights", "terrain_weight"]),
        ("multihazard.weights.flood_weight", ["multihazard", "weights", "flood_weight"]),
        ("redzones.enabled", ["redzones", "enabled"]),
        ("redzones.segmentation.source_class", ["redzones", "segmentation", "source_class"]),
        ("redzones.filtering.minimum_zone_area_m2", ["redzones", "filtering", "minimum_zone_area_m2"]),
        ("redzones.outputs.output_vector", ["redzones", "outputs", "output_vector"]),
        ("redzones.outputs.output_geojson", ["redzones", "outputs", "output_geojson"]),
    ]

    print("--- 3. Extracted Project Configuration Values ---")
    extracted_values = {}
    for name, keys in fields_to_check:
        val = get_nested(cfg, keys)
        extracted_values[name] = val
        if val is not None and str(val).strip() != "":
            print(f"  * {name:<36}: {val}")
        else:
            print(f"  * {name:<36}: [MISSING / EMPTY]")
            overall_pass = False

    print("\n--- 4. Individual Field Validations ---")
    for name, val in extracted_values.items():
        if val is not None and str(val).strip() != "":
            print(f"[PASS] {name} is configured.")
        else:
            print(f"[FAIL] {name} is missing or empty.")
            overall_pass = False

    # 5. Raw DEM file existence check
    print("\n--- 5. Dataset File Existence Check ---")
    dem_rel_path = extracted_values.get("paths.dem_raw")
    if dem_rel_path:
        dem_full_path = root_dir / dem_rel_path

        if dem_full_path.exists() and dem_full_path.is_file():
            file_size_mb = dem_full_path.stat().st_size / (1024 * 1024)
            print(f"[PASS] DEM file exists: {dem_full_path.relative_to(root_dir)} ({file_size_mb:.2f} MB)")
        else:
            print(f"[FAIL] DEM file specified in paths.dem_raw DOES NOT EXIST at: {dem_full_path}")
            overall_pass = False
    else:
        print("[FAIL] Cannot check DEM existence because paths.dem_raw is missing.")
        overall_pass = False

    # Final summary output
    print("\n==================================================================")
    if overall_pass:
        print("CONFIG VALIDATION: PASS")
    else:
        print("CONFIG VALIDATION: FAIL")
    print("==================================================================")
    
    if not overall_pass:
        sys.exit(1)


if __name__ == "__main__":
    validate_config()
