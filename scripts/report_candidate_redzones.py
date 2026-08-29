#!/usr/bin/env python3
"""
SIH26191 -- Step 7H: Candidate Hazard-Based Red Zone Explainability Report
==========================================================================
Generates a detailed, transparent explainability report for Candidate
Hazard-Based Red Zones in Rudraprayag District, detailing how each zone's
geometry, multi-hazard score, component contributions (terrain vs flood),
and priority ranking were derived.

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

EXPLAINABILITY FRAMEWORK
------------------------
For each candidate zone:
  1. Zone ID & Label
  2. Spatial Geometry & Footprint (Area in m2 / ha, Pixel count)
  3. Continuous Multi-Hazard Screening Score (Mean, Max, Min)
  4. Component Breakdown:
       Mean Terrain Contribution (Slope steepness proxy * 0.5)
       Mean Flood Contribution   (TWI convergence proxy * 0.5)
       Relative Balance          (% terrain vs % flood)
  5. Deterministic Priority Rank & Ranking Basis
  6. Transparent Retention Rationale (Contiguity + MMU threshold)
  7. Strict Decision-Support Disclaimers & Non-Claims

USAGE
-----
    python scripts/report_candidate_redzones.py [--limit N]
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any, List

try:
    import yaml
except ImportError:
    print("[ERROR] PyYAML not installed. Run: pip install pyyaml")
    sys.exit(1)

try:
    import numpy as np
    import geopandas as gpd
except ImportError as e:
    print(f"[ERROR] Required geospatial package not installed: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Paths and formatting helpers
# ---------------------------------------------------------------------------
_SCRIPT_DIR = Path(__file__).resolve().parent
_ROOT_DIR   = _SCRIPT_DIR.parent


def _sep(char: str = "=", width: int = 72) -> str:
    return char * width


def _section(title: str) -> None:
    print(f"\n{_sep('-')}")
    print(f"  {title}")
    print(_sep('-'))


def _field(label: str, value, width: int = 36) -> None:
    print(f"  {label:<{width}}: {value}")


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

def load_config() -> dict:
    cfg_path = _ROOT_DIR / "configs" / "project.yaml"
    if not cfg_path.is_file():
        print(f"[FAIL] Configuration file not found: {cfg_path}")
        sys.exit(1)
    with open(cfg_path, "r", encoding="utf-8") as fh:
        cfg = yaml.safe_load(fh)
    return cfg


# ---------------------------------------------------------------------------
# Main Explainability Report Generator
# ---------------------------------------------------------------------------

def generate_explainability_report(limit: int = 10) -> bool:
    print(_sep("="))
    print("  SIH26191 -- STEP 7H: CANDIDATE RED ZONE EXPLAINABILITY REPORT")
    print("  Pilot: Rudraprayag, Uttarakhand, India")
    print(_sep("="))

    cfg = load_config()
    redzones_cfg = cfg.get("redzones", {})
    paths_cfg    = cfg.get("paths", {})

    gpkg_rel = redzones_cfg.get("outputs", {}).get("output_vector", paths_cfg.get("redzones_gpkg", "data/outputs/candidate_hazard_based_red_zones.gpkg"))
    gpkg_path = _ROOT_DIR / gpkg_rel

    if not gpkg_path.is_file():
        print(f"[FAIL] Candidate red zone GeoPackage not found at: {gpkg_path}")
        print("Please run 'python processing/redzones/identify_candidate_zones.py' first.")
        return False

    gdf = gpd.read_file(gpkg_path)
    total_zones = len(gdf)

    min_area_m2 = float(redzones_cfg.get("filtering", {}).get("minimum_zone_area_m2", 5000.0))
    min_area_ha = min_area_m2 / 10000.0

    _section("1. Dataset & Methodology Summary")
    _field("Source Dataset", str(gpkg_rel))
    _field("CRS", str(gdf.crs))
    _field("Total Retained Candidate Zones", f"{total_zones:,}")
    _field("Minimum Mapping Unit (MMU)", f"{min_area_m2:,.1f} m2 ({min_area_ha:.2f} ha)")
    _field("Source Screening Class", "Class 3 (Higher Multi-Hazard Indicator)")
    _field("Ranking Basis", redzones_cfg.get("priority_ranking", {}).get("basis_description", "Mean multi-hazard score, then max score, then area"))

    # Summary Statistics
    total_area_ha = gdf["area_hectares"].sum()
    mean_score = gdf["mean_multihazard_score"].mean()
    mean_terr  = gdf["terrain_contribution_mean"].mean()
    mean_flood = gdf["flood_contribution_mean"].mean()

    _field("Total Candidate Zone Area", f"{total_area_ha:.2f} ha ({total_area_ha * 10000.0:,.0f} m2)")
    _field("Average Zone Mean Score", f"{mean_score:.4f}")
    _field("Average Terrain Contribution", f"{mean_terr:.4f} ({(mean_terr/mean_score)*100:.1f}%)")
    _field("Average Flood Contribution", f"{mean_flood:.4f} ({(mean_flood/mean_score)*100:.1f}%)")

    display_count = min(limit, total_zones) if limit > 0 else total_zones
    _section(f"2. Detailed Explainability Breakdown (Top {display_count} Ranked Zones)")

    for idx, row in gdf.iloc[:display_count].iterrows():
        zid    = row["zone_id"]
        rank   = row["candidate_priority_rank"]
        area_m2= row["area_m2"]
        area_ha= row["area_hectares"]
        px_cnt = row["pixel_count"]
        m_score= row["mean_multihazard_score"]
        mx_score=row["max_multihazard_score"]
        mn_score=row["min_multihazard_score"]
        c_terr = row["terrain_contribution_mean"]
        c_flood= row["flood_contribution_mean"]

        terr_pct  = (c_terr / m_score) * 100.0 if m_score > 0 else 50.0
        flood_pct = (c_flood / m_score) * 100.0 if m_score > 0 else 50.0

        if terr_pct >= 65.0:
            driver_str = "Terrain Susceptibility Dominated (Steep Flanks)"
        elif flood_pct >= 65.0:
            driver_str = "Hydrological Convergence Dominated (Channel Corridor / Terraces)"
        else:
            driver_str = "Dual Predisposition (Steep Gully / Convergence Flanks)"

        print(f"\n  ------------------------------------------------------------------")
        print(f"  ZONE ID: {zid}  |  PRIORITY RANK: #{rank}  |  STATUS: Candidate Zone")
        print(f"  ------------------------------------------------------------------")
        _field("  Spatial Footprint", f"{area_ha:.2f} ha ({area_m2:,.1f} m2, {px_cnt} cells)")
        _field("  Multi-Hazard Score (Mean)", f"{m_score:.4f}  [Min: {mn_score:.4f}, Max: {mx_score:.4f}]")
        _field("  Terrain Contribution (Slope)", f"{c_terr:.4f} ({terr_pct:.1f}% of score)")
        _field("  Flood Contribution (TWI)", f"{c_flood:.4f} ({flood_pct:.1f}% of score)")
        _field("  Predominant Hazard Driver", driver_str)
        print(f"  Retention Rationale:")
        print(f"    - Zone {zid} was retained because it forms a contiguous spatial cluster")
        print(f"      of Higher Multi-Hazard Indicator pixels (Class 3) and satisfies the")
        print(f"      configured minimum mapping unit of {min_area_m2:,.0f} m2 ({area_m2:,.0f} m2 >= {min_area_m2:,.0f} m2).")
        print(f"  Transparent Score Decomposition:")
        print(f"    - Mean Multi-Hazard Score = (Terrain Contribution) + (Flood Contribution)")
        print(f"                              = {c_terr:.4f} + {c_flood:.4f} = {m_score:.4f}")
        print(f"  Decision-Support Guidance:")
        print(f"    - Screening Indicator only. Requires mandatory geotechnical site")
        print(f"      survey and administrative verification by disaster management authorities.")

    if total_zones > display_count:
        print(f"\n  [NOTE] {total_zones - display_count} additional candidate zones are recorded in the GeoPackage and GeoJSON outputs.")

    _section("3. Scientific Limitations & Legal Notice")
    print("  * Screening Nature: Topographic and hydrological proxies identify predisposing")
    print("    terrain patterns; they DO NOT constitute landslide or flood event predictions.")
    print("  * Field Ground-Truthing: Boundaries must be validated through geological field")
    print("    mapping, soil mechanics testing, and municipal hazard boundary demarcations.")
    print("  * Non-Executive Output: Software provides decision support and NEVER authorizes")
    print("    evacuation, habitation relocation, or structural demolition.")

    print(f"\n{_sep('=')}")
    print("  CANDIDATE RED ZONE EXPLAINABILITY REPORT: COMPLETE")
    print(_sep('='))
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Candidate Red Zone Explainability Report.")
    parser.add_argument("--limit", type=int, default=10, help="Number of top candidate zones to report in detail (default: 10).")
    args = parser.parse_args()

    ok = generate_explainability_report(limit=args.limit)
    sys.exit(0 if ok else 1)
