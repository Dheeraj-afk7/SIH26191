#!/usr/bin/env python3
"""
SIH26191 -- Phase 2 Routing Sanity & Graph Topology Audit
=========================================================
"""

import json
import pathlib
import pickle
import geopandas as gpd
import networkx as nx
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent

HAB_PATH = ROOT / "data" / "processed" / "exposure" / "habitation_exposure.geojson"
CAND_PATH = ROOT / "data" / "outputs" / "candidate_topographically_feasible_areas_attributed.geojson"
GRAPH_PATH = ROOT / "data" / "processed" / "roads" / "road_graph.pickle"
ROADS_PATH = ROOT / "data" / "processed" / "roads" / "routable_road_network.gpkg"


def run_sanity_audit():
    print("=" * 76)
    print("  SIH26191: Phase 2 Topological & Routing Sanity Audit")
    print("=" * 76)

    hab_gdf = gpd.read_file(str(HAB_PATH))
    cand_gdf = gpd.read_file(str(CAND_PATH))
    roads_gdf = gpd.read_file(str(ROADS_PATH))

    with open(str(GRAPH_PATH), "rb") as f:
        G = pickle.load(f)

    # 1. Representative Cases across Tiers
    categories = [
        "HIGHLY_ACCESSIBLE",
        "MODERATELY_ACCESSIBLE",
        "REMOTE",
        "SEVERELY_REMOTE",
        "ISOLATED_GRAPH_DISCONNECTED"
    ]

    print("\n" + "=" * 76)
    print("  REPRESENTATIVE HABITATION ROUTING TEST CASES")
    print("=" * 76)

    for cat in categories:
        sub = hab_gdf[hab_gdf["road_accessibility_category"] == cat]
        if len(sub) == 0:
            continue
        v = sub.iloc[0]
        print(f"\n--- Category: {cat} (Total villages in category: {len(sub)}) ---")
        print(f"  Village Name         : {v['village_name']} (ID: {v['village_id']})")
        print(f"  Population / HH      : {v['tot_pop']:,} persons / {v['households']:,} households")
        print(f"  Nearest Road Name    : {v['nearest_road_name']} (Ref: {v['nearest_road_ref']})")
        print(f"  Highway Class        : {v['nearest_road_highway_class']} (Surface: {v['nearest_road_surface']})")
        print(f"  Euclidean Road Dist  : {v['dist_to_nearest_road_m']:.1f} m")
        print(f"  Graph Snapping Dist  : {v['road_snapping_distance_m']:.1f} m")
        print(f"  Network Route Exists : {v['network_route_exists']}")
        if v['network_route_exists']:
            print(f"  Network Road Dist    : {v['network_distance_to_arterial_m']:.1f} m")
            print(f"  Travel Time to NH/SH : {v['network_travel_time_to_arterial_min']:.1f} min")
        else:
            print(f"  Network Road Dist    : N/A (Graph Disconnected)")
            print(f"  Travel Time to NH/SH : N/A (Graph Disconnected)")

    print("\n" + "=" * 76)
    print("  REPRESENTATIVE CANDIDATE RELOCATION AREA TEST CASES")
    print("=" * 76)

    for cat in ["HIGHLY_ACCESSIBLE", "REMOTE", "ISOLATED_GRAPH_DISCONNECTED"]:
        sub_c = cand_gdf[cand_gdf["road_accessibility_category"] == cat]
        if len(sub_c) == 0:
            continue
        c = sub_c.iloc[0]
        print(f"\n--- Category: {cat} (Total candidates in category: {len(sub_c)}) ---")
        print(f"  Candidate Area ID    : {c['area_id']} ({c['area_hectares']:.2f} ha, slope: {c['mean_slope']:.1f}°)")
        print(f"  Nearest Village      : {c['nearest_village_name']} (ID: {c['nearest_village_id']})")
        print(f"  Nearest Road Name    : {c['nearest_road_name']} (Ref: {c['nearest_road_ref']}, Class: {c['nearest_road_highway_class']})")
        print(f"  Euclidean Road Dist  : {c['dist_to_nearest_road_m']:.1f} m")
        print(f"  Graph Snapping Dist  : {c['road_snapping_distance_m']:.1f} m")
        print(f"  Network Route Exists : {c['network_route_exists']}")
        if c['network_route_exists']:
            print(f"  Network Road Dist    : {c['network_distance_to_arterial_m']:.1f} m")
            print(f"  Travel Time to NH/SH : {c['network_travel_time_to_arterial_min']:.1f} min")
        else:
            print(f"  Network Road Dist    : N/A (Graph Disconnected)")
            print(f"  Travel Time to NH/SH : N/A (Graph Disconnected)")

    # 4. Major Junction Routability Verification
    print("\n" + "=" * 76)
    print("  MAJOR HIGHWAY JUNCTION ROUTABILITY & TOPOLOGY CHECK")
    print("=" * 76)

    nh107 = roads_gdf[roads_gdf["ref"].str.contains("NH107", case=False, na=False)]
    nh7 = roads_gdf[roads_gdf["ref"].str.contains("NH7", case=False, na=False)]
    print(f"  NH-107 Segments: {len(nh107)} | NH-7 Segments: {len(nh7)}")

    p_start = (round(nh107.geometry.iloc[0].coords[0][0], 1), round(nh107.geometry.iloc[0].coords[0][1], 1))
    p_end = (round(nh7.geometry.iloc[0].coords[0][0], 1), round(nh7.geometry.iloc[0].coords[0][1], 1))

    has_path = nx.has_path(G, p_start, p_end)
    path_len = nx.shortest_path_length(G, p_start, p_end, weight="length_m") if has_path else None
    path_time = nx.shortest_path_length(G, p_start, p_end, weight="travel_time_min") if has_path else None

    print(f"  Topological Route Exists between NH-107 and NH-07: {has_path}")
    if has_path:
        print(f"  Shortest Path Distance between sample endpoints  : {path_len:,.1f} m ({path_len/1000.0:.2f} km)")
        print(f"  Shortest Path Travel Time                        : {path_time:.1f} min")


if __name__ == "__main__":
    run_sanity_audit()
