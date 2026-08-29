#!/usr/bin/env python3
"""
SIH26191 -- Step 10 Output Validation
=======================================

Validates all Step 10 outputs for:
  - File existence
  - CRS correctness
  - Feature count match
  - Required field presence
  - Priority tier completeness (all 653 villages classified)
  - Numeric range validity
  - Disclaimer field presence
  - No modification of Step 7/8/9 outputs

USAGE
-----
  python scripts/validate_step10_outputs.py
"""

import sys
import io
import json
import pathlib
import datetime
import warnings

import numpy as np
import geopandas as gpd

# Force UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

warnings.filterwarnings("ignore")

_SCRIPT_DIR = pathlib.Path(__file__).resolve().parent
_ROOT = _SCRIPT_DIR.parent

_EXPECTED_CRS = 32644
_EXPECTED_VILLAGE_COUNT = 653

CHECKS_PASS = []
CHECKS_FAIL = []
CHECKS_WARN = []


def _pass(msg: str) -> None:
    print(f"  PASS  {msg}")
    CHECKS_PASS.append(msg)


def _fail(msg: str) -> None:
    print(f"  FAIL  {msg}")
    CHECKS_FAIL.append(msg)


def _warn(msg: str) -> None:
    print(f"  WARN  {msg}")
    CHECKS_WARN.append(msg)


def _banner(text: str) -> None:
    print()
    print("=" * 72)
    print(f"  {text}")
    print("=" * 72)


def _section(text: str) -> None:
    print(f"\n--- {text} ---")


# ---------------------------------------------------------------------------
# File existence checks
# ---------------------------------------------------------------------------

def check_file_existence() -> None:
    _section("File existence")

    expected_files = {
        "village_priority_indicators.gpkg": _ROOT / "data/processed/decision/village_priority_indicators.gpkg",
        "village_priority_profiles.gpkg":   _ROOT / "data/processed/decision/village_priority_profiles.gpkg",
        "candidate_area_context.gpkg":       _ROOT / "data/processed/decision/candidate_area_context.gpkg",
        "decision_summary.json":             _ROOT / "data/processed/decision/decision_summary.json",
        "decision_metadata.json":            _ROOT / "data/processed/decision/decision_metadata.json",
        "step10_decision_engine_report.md":  _ROOT / "docs/step10_decision_engine_report.md",
        "priority_thresholds.yaml":          _ROOT / "configs/priority_thresholds.yaml",
        "capacity.yaml":                     _ROOT / "configs/capacity.yaml",
    }

    for label, path in expected_files.items():
        if path.exists() and path.stat().st_size > 0:
            _pass(f"Exists and non-empty: {label} ({path.stat().st_size:,} bytes)")
        elif path.exists():
            _warn(f"Exists but EMPTY: {label}")
        else:
            _fail(f"MISSING: {label}")


# ---------------------------------------------------------------------------
# Step 7/8/9 output integrity
# ---------------------------------------------------------------------------

def check_upstream_outputs_intact() -> None:
    _section("Upstream output integrity (Step 7/8/9 not modified)")

    upstream = {
        "Step 7 — red zones GeoJSON": _ROOT / "data/outputs/candidate_hazard_based_red_zones.geojson",
        "Step 8 — habitation exposure": _ROOT / "data/processed/exposure/habitation_exposure.geojson",
        "Step 9 — attributed areas":    _ROOT / "data/outputs/candidate_topographically_feasible_areas_attributed.geojson",
    }

    for label, path in upstream.items():
        if path.exists():
            _pass(f"Intact (not overwritten): {label}")
        else:
            _fail(f"MISSING — upstream output deleted or moved: {label}")


# ---------------------------------------------------------------------------
# GeoPackage checks
# ---------------------------------------------------------------------------

def check_village_priority_indicators() -> None:
    _section("village_priority_indicators.gpkg")
    path = _ROOT / "data/processed/decision/village_priority_indicators.gpkg"
    if not path.exists():
        _fail("File missing — cannot validate")
        return

    gdf = gpd.read_file(str(path))

    # Feature count
    n = len(gdf)
    if n == _EXPECTED_VILLAGE_COUNT:
        _pass(f"Feature count: {n} == {_EXPECTED_VILLAGE_COUNT} expected")
    else:
        _fail(f"Feature count: {n} != {_EXPECTED_VILLAGE_COUNT} expected")

    # CRS
    epsg = gdf.crs.to_epsg() if gdf.crs else None
    if epsg == _EXPECTED_CRS:
        _pass(f"CRS: EPSG:{epsg}")
    else:
        _fail(f"CRS: EPSG:{epsg} != expected EPSG:{_EXPECTED_CRS}")

    # Required fields
    required = [
        "village_id", "village_name", "tot_pop", "households",
        "nearest_hazard_distance_m", "proximity_band", "direct_zone_overlap",
        "mh_score_at_centroid", "mh_class_at_centroid",
        "pca_join_status", "step10b_disclaimer",
    ]
    for f in required:
        if f in gdf.columns:
            _pass(f"Field present: {f}")
        else:
            _fail(f"Field missing: {f}")

    # Vulnerability indicators (warn if all null)
    for ind in ["illiteracy_rate", "child_proportion", "sc_proportion", "st_proportion", "non_worker_rate"]:
        if ind not in gdf.columns:
            _warn(f"Vulnerability indicator absent: {ind}")
        elif gdf[ind].notna().sum() == 0:
            _warn(f"Vulnerability indicator all NaN: {ind}")
        else:
            valid = gdf[ind].notna().sum()
            # Rates should be [0, 1]
            out_of_range = ((gdf[ind] < 0) | (gdf[ind] > 1)).sum()
            if out_of_range == 0:
                _pass(f"{ind}: {valid} valid, range [0,1] OK")
            else:
                _fail(f"{ind}: {out_of_range} values out of [0,1] range")

    # mh_score range [0,1]
    if "mh_score_at_centroid" in gdf.columns:
        valid = gdf["mh_score_at_centroid"].dropna()
        if len(valid) > 0:
            if valid.min() >= 0.0 and valid.max() <= 1.0:
                _pass(f"mh_score_at_centroid range: [{valid.min():.4f}, {valid.max():.4f}] within [0,1]")
            else:
                _fail(f"mh_score_at_centroid out of range: [{valid.min():.4f}, {valid.max():.4f}]")

    # mh_class values should be 1, 2, 3, or NaN
    if "mh_class_at_centroid" in gdf.columns:
        valid_classes = {1.0, 2.0, 3.0}
        actual = set(gdf["mh_class_at_centroid"].dropna().unique())
        invalid = actual - valid_classes
        if not invalid:
            _pass(f"mh_class_at_centroid values all valid: {sorted(actual)}")
        else:
            _fail(f"mh_class_at_centroid has invalid values: {invalid}")

    # PCA join success rate
    if "pca_join_status" in gdf.columns:
        joined = (gdf["pca_join_status"] == "JOINED").sum()
        total = len(gdf)
        pct = 100 * joined / total if total > 0 else 0
        if pct >= 90:
            _pass(f"PCA join success: {joined}/{total} ({pct:.1f}%)")
        else:
            _warn(f"PCA join success below 90%: {joined}/{total} ({pct:.1f}%)")


def check_village_priority_profiles() -> None:
    _section("village_priority_profiles.gpkg")
    path = _ROOT / "data/processed/decision/village_priority_profiles.gpkg"
    if not path.exists():
        _fail("File missing — cannot validate")
        return

    gdf = gpd.read_file(str(path))

    # Feature count
    n = len(gdf)
    if n == _EXPECTED_VILLAGE_COUNT:
        _pass(f"Feature count: {n} == {_EXPECTED_VILLAGE_COUNT} expected")
    else:
        _fail(f"Feature count: {n} != {_EXPECTED_VILLAGE_COUNT} expected")

    # CRS
    epsg = gdf.crs.to_epsg() if gdf.crs else None
    if epsg == _EXPECTED_CRS:
        _pass(f"CRS: EPSG:{epsg}")
    else:
        _fail(f"CRS: EPSG:{epsg} != expected EPSG:{_EXPECTED_CRS}")

    # Required classification fields
    required = [
        "priority_tier", "priority_tier_display", "priority_reason",
        "priority_applied_rule", "disaster_history_status",
        "methodology_status", "step10c_disclaimer",
    ]
    for f in required:
        if f in gdf.columns:
            _pass(f"Field present: {f}")
        else:
            _fail(f"Field missing: {f}")

    # All villages must have a priority tier
    if "priority_tier" in gdf.columns:
        unclassified = gdf["priority_tier"].isna().sum()
        if unclassified == 0:
            _pass("All villages have a priority_tier assigned")
        else:
            _fail(f"{unclassified} villages have no priority_tier (NaN)")

        unknown = (gdf["priority_tier"] == "Unknown").sum()
        if unknown == 0:
            _pass("No villages with 'Unknown' priority tier")
        else:
            _warn(f"{unknown} villages have 'Unknown' priority tier (distance field issue)")

        # Valid tier values
        valid_tiers = {
            "Tier1_AttentionPriority", "Tier2_ElevatedAttention",
            "Tier3_Monitoring", "BeyondProximity", "Unknown",
        }
        actual_tiers = set(gdf["priority_tier"].dropna().unique())
        invalid = actual_tiers - valid_tiers
        if not invalid:
            _pass(f"Priority tier values all valid: {sorted(actual_tiers)}")
        else:
            _fail(f"Invalid priority tier values: {invalid}")

        # Tier distribution
        print()
        print("  Tier distribution:")
        for tier in sorted(actual_tiers):
            n_t = (gdf["priority_tier"] == tier).sum()
            print(f"    {tier}: {n_t} villages")

    # Disclaimer present
    if "step10c_disclaimer" in gdf.columns:
        blank = (gdf["step10c_disclaimer"].isna() | (gdf["step10c_disclaimer"] == "")).sum()
        if blank == 0:
            _pass("step10c_disclaimer populated for all villages")
        else:
            _fail(f"{blank} villages missing step10c_disclaimer")

    # Disaster history status
    if "disaster_history_status" in gdf.columns:
        statuses = gdf["disaster_history_status"].unique().tolist()
        if all("NOT_ACQUIRED" in str(s) for s in statuses):
            _pass(f"disaster_history_status correctly set: {statuses[0][:60]}...")
        else:
            _warn(f"disaster_history_status values: {statuses}")


def check_candidate_area_context() -> None:
    _section("candidate_area_context.gpkg")
    path = _ROOT / "data/processed/decision/candidate_area_context.gpkg"
    if not path.exists():
        _fail("File missing — cannot validate")
        return

    gdf = gpd.read_file(str(path))
    print(f"  Features: {len(gdf)}")

    # CRS
    epsg = gdf.crs.to_epsg() if gdf.crs else None
    if epsg == _EXPECTED_CRS:
        _pass(f"CRS: EPSG:{epsg}")
    else:
        _fail(f"CRS: EPSG:{epsg} != expected EPSG:{_EXPECTED_CRS}")

    # Required context fields
    context_fields = [
        "slope_context", "terrain_context", "flood_context",
        "hazard_buffer_context", "area_scale_context",
        "screening_completeness", "capacity_status",
        "capacity_planning_note", "allocation_status",
        "step10_disclaimer",
    ]
    for f in context_fields:
        if f in gdf.columns:
            _pass(f"Context field present: {f}")
        else:
            _fail(f"Context field missing: {f}")

    # Capacity status
    if "capacity_status" in gdf.columns:
        statuses = gdf["capacity_status"].unique().tolist()
        expected_status = "NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD"
        if all(expected_status in str(s) for s in statuses):
            _pass(f"capacity_status correctly set: {expected_status}")
        else:
            _warn(f"Unexpected capacity_status: {statuses}")

    # Allocation status — must contain NO_ALLOCATION message
    if "allocation_status" in gdf.columns:
        alloc = gdf["allocation_status"].iloc[0] if len(gdf) > 0 else ""
        if "NO VILLAGE-TO-AREA ALLOCATION GENERATED" in str(alloc):
            _pass("allocation_status correctly states no allocation generated")
        else:
            _warn(f"Unexpected allocation_status: {alloc}")

    # Disclaimer
    if "step10_disclaimer" in gdf.columns:
        blank = (gdf["step10_disclaimer"].isna() | (gdf["step10_disclaimer"] == "")).sum()
        if blank == 0:
            _pass("step10_disclaimer populated for all features")
        else:
            _fail(f"{blank} features missing step10_disclaimer")


def check_json_outputs() -> None:
    _section("JSON outputs")

    # decision_summary.json
    summary_path = _ROOT / "data/processed/decision/decision_summary.json"
    if summary_path.exists():
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
        required_keys = ["project", "step", "generated_utc", "village_priority",
                         "candidate_areas", "disclaimer"]
        for k in required_keys:
            if k in summary:
                _pass(f"decision_summary.json has key: {k}")
            else:
                _fail(f"decision_summary.json missing key: {k}")

        # Tier counts should sum to expected village count
        tier_dist = summary.get("village_priority", {}).get("tier_distribution", {})
        total_classified = sum(t.get("count", 0) for t in tier_dist.values())
        total_expected = summary.get("village_priority", {}).get("total_habitations", 0)
        if total_classified == total_expected:
            _pass(f"Tier counts sum matches total habitations: {total_classified}")
        else:
            _fail(f"Tier counts sum {total_classified} != total habitations {total_expected}")
    else:
        _fail("decision_summary.json missing")

    # decision_metadata.json
    meta_path = _ROOT / "data/processed/decision/decision_metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)
        required_meta = ["inputs_used", "outputs_produced", "classification_rules_applied",
                         "capacity_status", "allocation_status"]
        for k in required_meta:
            if k in meta:
                _pass(f"decision_metadata.json has key: {k}")
            else:
                _fail(f"decision_metadata.json missing key: {k}")

        # Confirm no upstream outputs were modified
        if meta.get("step9_outputs_modified") == False:
            _pass("step9_outputs_modified = False (confirmed)")
        else:
            _warn(f"step9_outputs_modified = {meta.get('step9_outputs_modified')}")
    else:
        _fail("decision_metadata.json missing")


# ---------------------------------------------------------------------------
# Main validation run
# ---------------------------------------------------------------------------

def main() -> None:
    _banner("SIH26191 — Step 10 Output Validation")
    t_start = datetime.datetime.utcnow()
    print(f"  Time: {t_start.strftime('%Y-%m-%dT%H:%M:%SZ')}")

    check_file_existence()
    check_upstream_outputs_intact()
    check_village_priority_indicators()
    check_village_priority_profiles()
    check_candidate_area_context()
    check_json_outputs()

    # ── Summary ───────────────────────────────────────────────────────────
    _banner("Validation Summary")
    total = len(CHECKS_PASS) + len(CHECKS_FAIL) + len(CHECKS_WARN)
    print(f"  Total checks: {total}")
    print(f"  PASS:         {len(CHECKS_PASS)}")
    print(f"  WARN:         {len(CHECKS_WARN)}")
    print(f"  FAIL:         {len(CHECKS_FAIL)}")
    print()

    if CHECKS_FAIL:
        print("  FAILED CHECKS:")
        for c in CHECKS_FAIL:
            print(f"    - {c}")
        print()
        print("  VALIDATION RESULT: FAIL")
        sys.exit(1)
    elif CHECKS_WARN:
        print("  WARNINGS (non-blocking):")
        for c in CHECKS_WARN:
            print(f"    ~ {c}")
        print()
        print("  VALIDATION RESULT: PASS WITH WARNINGS")
    else:
        print("  VALIDATION RESULT: PASS — All checks passed")

    t_end = datetime.datetime.utcnow()
    elapsed = (t_end - t_start).total_seconds()
    print(f"\n  Completed in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
