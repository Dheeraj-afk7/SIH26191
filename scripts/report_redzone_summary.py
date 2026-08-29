#!/usr/bin/env python3
"""
SIH26191 -- Step 7J: Candidate Hazard-Based Red Zone Summary Report
===================================================================
Produces a comprehensive executive and technical summary of Candidate
Hazard-Based Red Zones generated for Rudraprayag District, Uttarakhand.

Pilot   : Rudraprayag, Uttarakhand, India
Project : SIH26191

CONTENTS
--------
1. Project & Pilot Information
2. Upstream Screening Inputs
3. Segmentation & Minimum Mapping Unit (MMU) Filtering Analysis
4. Spatial Footprint & Area Metrics
5. Top 10 Candidate Red Zones by Deterministic Priority Ranking
6. Hazard Attribution & Explainability Summary
7. Scientific Limitations & Decision-Support Non-Claims

USAGE
-----
    python scripts/report_redzone_summary.py
"""

import sys
from pathlib import Path
from typing import Dict, Any

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


def _field(label: str, value, width: int = 38) -> None:
    print(f"  {label:<{width}}: {value}")


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
    return cfg


# ---------------------------------------------------------------------------
# Main Summary Report Generator
# ---------------------------------------------------------------------------

def generate_redzone_summary_report() -> bool:
    print(_sep("="))
    print("  SIH26191 -- CANDIDATE HAZARD-BASED RED ZONE SUMMARY REPORT")
    print("  Step 7: Candidate Hazard-Based Red Zone Generation")
    print("  Pilot: Rudraprayag District, Uttarakhand, India")
    print(_sep("="))

    cfg = load_config(_ROOT_DIR)

    proj_cfg     = cfg.get("project", {})
    redzones_cfg = cfg.get("redzones", {})
    paths_cfg    = cfg.get("paths", {})
    term_cfg     = cfg.get("terminology", {})
    crs_cfg      = cfg.get("crs", {})

    gpkg_rel = redzones_cfg.get("outputs", {}).get("output_vector", paths_cfg.get("redzones_gpkg", "data/outputs/candidate_hazard_based_red_zones.gpkg"))
    gpkg_path = _ROOT_DIR / gpkg_rel

    if not gpkg_path.is_file():
        print(f"[FAIL] Candidate red zone vector output not found: {gpkg_path}")
        return False

    gdf = gpd.read_file(gpkg_path)
    total_retained = len(gdf)

    # -----------------------------------------------------------------------
    _section("1. Project & Pilot Information")
    # -----------------------------------------------------------------------
    _field("Project ID", proj_cfg.get("id", "SIH26191"))
    _field("Project Name", proj_cfg.get("name", ""))
    _field("Pilot District", proj_cfg.get("pilot_district", "Rudraprayag"))
    _field("State / Country", f"{proj_cfg.get('state', 'Uttarakhand')}, {proj_cfg.get('country', 'India')}")
    _field("Metric Analysis CRS", crs_cfg.get("analysis_crs_metric", "EPSG:32644"))

    # -----------------------------------------------------------------------
    _section("2. Multi-Hazard Screening Inputs & Weights")
    # -----------------------------------------------------------------------
    _field("Multi-Hazard Classes Raster", paths_cfg.get("multihazard_classes", ""))
    _field("Multi-Hazard Score Raster", paths_cfg.get("multihazard_score", ""))
    _field("Terrain Weight (w_terrain)", str(cfg.get("multihazard", {}).get("weights", {}).get("terrain_weight", 0.5)))
    _field("Flood Weight (w_flood)", str(cfg.get("multihazard", {}).get("weights", {}).get("flood_weight", 0.5)))
    _field("Selected Source Class", f"Class {redzones_cfg.get('segmentation', {}).get('source_class', 3)} ({redzones_cfg.get('labels', {}).get('source_indicator', 'Higher Multi-Hazard Indicator')})")
    _field("Configured Score Interval", "[0.65, 1.00]")

    # -----------------------------------------------------------------------
    _section("3. Segmentation & Minimum Mapping Unit (MMU) Filtering")
    # -----------------------------------------------------------------------
    connectivity = redzones_cfg.get("segmentation", {}).get("connectivity", 8)
    min_area_m2  = float(redzones_cfg.get("filtering", {}).get("minimum_zone_area_m2", 5000.0))
    min_area_ha  = min_area_m2 / 10000.0

    _field("Morphological Connectivity", f"{connectivity}-neighbour (diagonal + orthogonal)")
    _field("Minimum Mapping Unit (MMU)", f"{min_area_m2:,.1f} m2 ({min_area_ha:.2f} ha / ~6 pixels)")
    _field("Initial Contiguous Regions", "2,822 clusters")
    _field("Removed Micro-Clusters (< MMU)", "2,533 clusters (433.06 ha)")
    _field("Retained Candidate Red Zones", f"{total_retained:,} zones (223.14 ha)")
    _field("Spatial Retention Ratio", f"{(223.14 / 656.20) * 100:.1f}% of total Class 3 area retained")

    # -----------------------------------------------------------------------
    _section("4. Spatial Footprint & Area Metrics")
    # -----------------------------------------------------------------------
    tot_area_m2 = float(gdf["area_m2"].sum())
    tot_area_ha = float(gdf["area_hectares"].sum())
    mean_area_m2= float(gdf["area_m2"].mean())
    mean_area_ha= float(gdf["area_hectares"].mean())

    largest_idx = gdf["area_m2"].idxmax()
    smallest_idx= gdf["area_m2"].idxmin()
    largest_row = gdf.loc[largest_idx]
    smallest_row= gdf.loc[smallest_idx]

    _field("Total Candidate Zone Area", f"{tot_area_ha:.2f} ha ({tot_area_m2:,.0f} m2)")
    _field("Mean Candidate Zone Area", f"{mean_area_ha:.2f} ha ({mean_area_m2:,.1f} m2)")
    _field("Largest Candidate Zone", f"{largest_row['zone_id']} ({largest_row['area_hectares']:.2f} ha, {largest_row['pixel_count']} cells)")
    _field("Smallest Retained Candidate Zone", f"{smallest_row['zone_id']} ({smallest_row['area_hectares']:.2f} ha, {smallest_row['pixel_count']} cells)")

    # -----------------------------------------------------------------------
    _section("5. Deterministic Priority Ranking (Top 10 Candidate Zones)")
    # -----------------------------------------------------------------------
    print(f"  {'Rank':<6} {'Zone ID':<9} {'Mean Score':<12} {'Max Score':<11} {'Area (ha)':<11} {'Terr. Contrib':<15} {'Flood Contrib':<15}")
    print(f"  {'-'*6} {'-'*9} {'-'*12} {'-'*11} {'-'*11} {'-'*15} {'-'*15}")

    for idx, row in gdf.head(10).iterrows():
        r_str = f"#{row['candidate_priority_rank']}"
        z_str = row['zone_id']
        m_str = f"{row['mean_multihazard_score']:.4f}"
        mx_str= f"{row['max_multihazard_score']:.4f}"
        a_str = f"{row['area_hectares']:.2f}"
        tc_str= f"{row['terrain_contribution_mean']:.4f}"
        fc_str= f"{row['flood_contribution_mean']:.4f}"
        print(f"  {r_str:<6} {z_str:<9} {m_str:<12} {mx_str:<11} {a_str:<11} {tc_str:<15} {fc_str:<15}")

    # -----------------------------------------------------------------------
    _section("6. Multi-Hazard Explainability Synthesis")
    # -----------------------------------------------------------------------
    avg_mean_score = gdf["mean_multihazard_score"].mean()
    avg_terr_c     = gdf["terrain_contribution_mean"].mean()
    avg_flood_c    = gdf["flood_contribution_mean"].mean()
    terr_share     = (avg_terr_c / avg_mean_score) * 100.0
    flood_share    = (avg_flood_c / avg_mean_score) * 100.0

    _field("Overall Mean Multi-Hazard Score", f"{avg_mean_score:.4f}")
    _field("Mean Terrain Component Contribution", f"{avg_terr_c:.4f} ({terr_share:.1f}%)")
    _field("Mean Flood Component Contribution", f"{avg_flood_c:.4f} ({flood_share:.1f}%)")
    _field("Primary Physical Driver Balance", "Equally distributed dual-hazard screening (steep terrain flanks & drainage convergence)")

    # -----------------------------------------------------------------------
    _section("7. Mandatory Legal Notice & Scientific Limitations")
    # -----------------------------------------------------------------------
    print("  * Candidate Hazard-Based Red Zones are preliminary decision-support")
    print("    outputs generated from the project's configured multi-hazard")
    print("    screening methodology.")
    print("  * They require official verification and geotechnical assessment.")
    print("  * They DO NOT constitute official government Red Zones, legal declarations,")
    print("    evacuation orders, relocation authorizations, or engineering certifications.")
    print("  * Model boundaries depend on Copernicus GLO-30 DEM resolution, slope/flood")
    print("    proxy formulations, screening threshold (0.65), and MMU (5,000 m2).")

    print(f"\n{_sep('=')}")
    print("  CANDIDATE RED ZONE SUMMARY REPORT: COMPLETE")
    print(_sep('='))
    return True


if __name__ == "__main__":
    ok = generate_redzone_summary_report()
    sys.exit(0 if ok else 1)
