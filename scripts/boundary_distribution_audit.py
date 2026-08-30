#!/usr/bin/env python3
"""
SIH26191 -- Phase 2 Candidate Area Boundary Distribution Audit
==============================================================

Inspects candidate areas around threshold boundaries:
- snapping distance: 1,400 - 1,600 m
- snapping distance: 2,900 - 3,100 m
- travel time: 85 - 95 min
- Explains SEVERELY_REMOTE vs ISOLATED_GRAPH_DISCONNECTED distribution
"""

import json
import pathlib
import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAND_PATH = ROOT / "data" / "outputs" / "candidate_topographically_feasible_areas_attributed.geojson"
HAB_PATH = ROOT / "data" / "processed" / "exposure" / "habitation_exposure.geojson"


def audit_candidate_boundaries():
    cand_gdf = gpd.read_file(str(CAND_PATH))
    hab_gdf = gpd.read_file(str(HAB_PATH))

    print("=" * 76)
    print("  CANDIDATE AREA THRESHOLD BOUNDARY DISTRIBUTION AUDIT (N = 2,998)")
    print("=" * 76)

    # Snapping distance stats
    snap = cand_gdf["road_snapping_distance_m"]
    tt = cand_gdf["network_travel_time_to_arterial_min"]

    print("\n--- OVERALL CANDIDATE AREA METRIC DISTRIBUTIONS ---")
    print(f"Snapping Distance (m): min={snap.min():.1f}, 25%={snap.quantile(0.25):.1f}, median={snap.median():.1f}, 75%={snap.quantile(0.75):.1f}, max={snap.max():.1f}")
    print(f"Snapping Distance <= 500m   : {(snap <= 500).sum():,} ({(snap <= 500).mean()*100:.1f}%)")
    print(f"Snapping Distance 500-1000m : {((snap > 500) & (snap <= 1000)).sum():,} ({((snap > 500) & (snap <= 1000)).mean()*100:.1f}%)")
    print(f"Snapping Distance 1000-1500m: {((snap > 1000) & (snap <= 1500)).sum():,} ({((snap > 1000) & (snap <= 1500)).mean()*100:.1f}%)")
    print(f"Snapping Distance 1500-3000m: {((snap > 1500) & (snap <= 3000)).sum():,} ({((snap > 1500) & (snap <= 3000)).mean()*100:.1f}%)")
    print(f"Snapping Distance > 3000m   : {(snap > 3000).sum():,} ({(snap > 3000).mean()*100:.1f}%)")

    print("\nTravel Time to NH/SH (min) [Non-null]:")
    tt_valid = tt.dropna()
    print(f"Valid route count          : {len(tt_valid):,} of {len(cand_gdf):,}")
    print(f"Travel Time (min): min={tt_valid.min():.1f}, 25%={tt_valid.quantile(0.25):.1f}, median={tt_valid.median():.1f}, 75%={tt_valid.quantile(0.75):.1f}, max={tt_valid.max():.1f}")
    print(f"Travel Time <= 15 min      : {(tt_valid <= 15).sum():,} ({(tt_valid <= 15).mean()*100:.1f}%)")
    print(f"Travel Time 15 - 45 min    : {((tt_valid > 15) & (tt_valid <= 45)).sum():,} ({((tt_valid > 15) & (tt_valid <= 45)).mean()*100:.1f}%)")
    print(f"Travel Time 45 - 90 min    : {((tt_valid > 45) & (tt_valid <= 90)).sum():,} ({((tt_valid > 45) & (tt_valid <= 90)).mean()*100:.1f}%)")
    print(f"Travel Time > 90 min       : {(tt_valid > 90).sum():,} ({(tt_valid > 90).mean()*100:.1f}%)")

    # 1. Boundary Band: Snapping distance 1,400 - 1,600 m
    print("\n" + "=" * 76)
    print("  1. BOUNDARY BAND: Snapping Distance [1,400 m – 1,600 m]")
    print("=" * 76)
    b1 = cand_gdf[(cand_gdf["road_snapping_distance_m"] >= 1400.0) & (cand_gdf["road_snapping_distance_m"] <= 1600.0)]
    print(f"Count in [1,400 m – 1,600 m]: {len(b1)}")
    if len(b1) > 0:
        print("\nCategory breakdown in band:")
        print(b1["road_accessibility_category"].value_counts().to_string())
        print("\nSample records in band:")
        for idx, row in b1.head(3).iterrows():
            print(f"  ID: {row['area_id']} | Snap: {row['road_snapping_distance_m']:.1f}m | Route: {row['network_route_exists']} | TT: {row['network_travel_time_to_arterial_min']} min | Cat: {row['road_accessibility_category']}")

    # 2. Boundary Band: Snapping distance 2,900 - 3,100 m
    print("\n" + "=" * 76)
    print("  2. BOUNDARY BAND: Snapping Distance [2,900 m – 3,100 m]")
    print("=" * 76)
    b2 = cand_gdf[(cand_gdf["road_snapping_distance_m"] >= 2900.0) & (cand_gdf["road_snapping_distance_m"] <= 3100.0)]
    print(f"Count in [2,900 m – 3,100 m]: {len(b2)}")
    if len(b2) > 0:
        print("\nCategory breakdown in band:")
        print(b2["road_accessibility_category"].value_counts().to_string())
        print("\nSample records in band:")
        for idx, row in b2.head(3).iterrows():
            print(f"  ID: {row['area_id']} | Snap: {row['road_snapping_distance_m']:.1f}m | Route: {row['network_route_exists']} | TT: {row['network_travel_time_to_arterial_min']} min | Cat: {row['road_accessibility_category']}")

    # 3. Boundary Band: Travel Time 85 - 95 min
    print("\n" + "=" * 76)
    print("  3. BOUNDARY BAND: Network Travel Time [85.0 min – 95.0 min]")
    print("=" * 76)
    b3 = cand_gdf[(cand_gdf["network_travel_time_to_arterial_min"] >= 85.0) & (cand_gdf["network_travel_time_to_arterial_min"] <= 95.0)]
    print(f"Count in [85.0 min – 95.0 min]: {len(b3)}")
    if len(b3) > 0:
        print("\nCategory breakdown in band:")
        print(b3["road_accessibility_category"].value_counts().to_string())
        print("\nSample records in band:")
        for idx, row in b3.head(3).iterrows():
            print(f"  ID: {row['area_id']} | Snap: {row['road_snapping_distance_m']:.1f}m | Route: {row['network_route_exists']} | TT: {row['network_travel_time_to_arterial_min']} min | Cat: {row['road_accessibility_category']}")

    # 4. Check SEVERELY_REMOTE evaluation for candidate areas
    print("\n" + "=" * 76)
    print("  4. SEVERELY_REMOTE LOGIC AUDIT FOR CANDIDATES")
    print("=" * 76)
    # Check candidates with snap > 1500 and snap <= 3000 and valid route
    sev_snap = cand_gdf[(cand_gdf["road_snapping_distance_m"] > 1500.0) & (cand_gdf["road_snapping_distance_m"] <= 3000.0)]
    print(f"Candidates with 1500m < Snap <= 3000m: {len(sev_snap)}")
    sev_tt = cand_gdf[cand_gdf["network_travel_time_to_arterial_min"] > 90.0]
    print(f"Candidates with Travel Time > 90 min : {len(sev_tt)}")


if __name__ == "__main__":
    audit_candidate_boundaries()
