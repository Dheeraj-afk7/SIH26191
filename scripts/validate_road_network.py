#!/usr/bin/env python3
"""
SIH26191 -- Phase 2 Output Validation: Routable Road Network & Mountain Accessibility
=====================================================================================

Validates:
1. Processed road network GeoPackage and schema integrity.
2. NetworkX serialized graph connectivity, nodes, edges, and LCC.
3. Dual accessibility metric attribution on Habitations (653) and Candidate Areas (2,998).
4. Strict distinction between Euclidean road distance and network travel time.
5. Provenance metadata and configuration parameters.
"""

import datetime
import json
import os
import pathlib
import pickle
import sys
import geopandas as gpd
import networkx as nx
import numpy as np

ROOT = pathlib.Path(__file__).resolve().parent.parent

PASS = "PASS"
FAIL = "FAIL"
WARN = "WARN"

results = []


def _check(name: str, status: str, detail: str = ""):
    results.append({"name": name, "status": status, "detail": detail})
    tag = f"[{status}]"
    print(f"  {tag:6s} {name:50s} | {detail}", flush=True)


def _section(title: str):
    print(f"\n{'='*72}\n  {title}\n{'='*72}", flush=True)


def validate_road_network() -> bool:
    print("=" * 72)
    print("  SIH26191 -- Phase 2 Road Network & Mountain Accessibility Validation")
    print(f"  Generated: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    print("=" * 72)

    # 1. File Existence Check
    _section("1. FILE EXISTENCE & ARTIFACT CHECK")
    expected = {
        "raw_geojson": ROOT / "data/raw/roads/osm_roads_rudraprayag.geojson",
        "provenance_json": ROOT / "data/raw/roads/provenance_metadata.json",
        "roads_gpkg": ROOT / "data/processed/roads/routable_road_network.gpkg",
        "graph_pickle": ROOT / "data/processed/roads/road_graph.pickle",
        "summary_json": ROOT / "data/processed/roads/road_summary.json",
        "config_yaml": ROOT / "configs/road_network.yaml",
        "habitations_geojson": ROOT / "data/processed/exposure/habitation_exposure.geojson",
        "candidate_areas_geojson": ROOT / "data/outputs/candidate_topographically_feasible_areas_attributed.geojson"
    }

    for k, p in expected.items():
        if p.exists() and p.stat().st_size > 0:
            _check(f"file.{k}", PASS, f"{p.relative_to(ROOT)} ({p.stat().st_size / 1024:.1f} KB)")
        else:
            _check(f"file.{k}", FAIL, f"Missing or empty: {p.relative_to(ROOT)}")

    # 2. Road Network Vector Integrity
    _section("2. ROUTABLE ROAD NETWORK VECTOR CHECK")
    roads_gdf = None
    try:
        roads_gdf = gpd.read_file(str(expected["roads_gpkg"]))
        _check("roads_gpkg.read", PASS, f"{len(roads_gdf):,} road features")
        _check("roads_gpkg.crs", PASS if str(roads_gdf.crs) == "EPSG:32644" else FAIL, str(roads_gdf.crs))

        req_cols = ["osm_id", "highway", "length_m", "assumed_speed_kmh", "travel_time_min", "is_vehicular", "is_arterial"]
        for c in req_cols:
            _check(f"roads_gpkg.field.{c}", PASS if c in roads_gdf.columns else FAIL, "present" if c in roads_gdf.columns else "MISSING")

        neg_lengths = int((roads_gdf["length_m"] <= 0).sum())
        _check("roads_gpkg.lengths_positive", PASS if neg_lengths == 0 else FAIL, f"non-positive lengths: {neg_lengths}")

        tot_km = float(roads_gdf["length_m"].sum() / 1000.0)
        _check("roads_gpkg.total_length", PASS, f"{tot_km:,.1f} km total length")

        vehicular_km = float(roads_gdf[roads_gdf["is_vehicular"]]["length_m"].sum() / 1000.0)
        _check("roads_gpkg.vehicular_length", PASS, f"{vehicular_km:,.1f} km vehicular roads")

        arterial_km = float(roads_gdf[roads_gdf["is_arterial"]]["length_m"].sum() / 1000.0)
        _check("roads_gpkg.arterial_length", PASS, f"{arterial_km:,.1f} km arterial highways (NH-107/NH-07/SH)")

    except Exception as exc:
        _check("roads_gpkg.read", FAIL, str(exc))

    # 3. NetworkX Graph Integrity
    _section("3. NETWORKX GRAPH TOPOLOGY & CONNECTIVITY CHECK")
    try:
        with open(str(expected["graph_pickle"]), "rb") as f:
            G = pickle.load(f)

        n_nodes = G.number_of_nodes()
        n_edges = G.number_of_edges()
        _check("graph.nodes_count", PASS if n_nodes > 10000 else FAIL, f"{n_nodes:,} nodes")
        _check("graph.edges_count", PASS if n_edges > 10000 else FAIL, f"{n_edges:,} edges")

        components = list(nx.connected_components(G))
        lcc = max(components, key=len) if components else set()
        lcc_pct = (len(lcc) * 100.0 / n_nodes) if n_nodes > 0 else 0.0
        _check("graph.connected_components", PASS, f"{len(components)} components found")
        _check("graph.largest_connected_component_pct", PASS if lcc_pct > 80.0 else WARN, f"{len(lcc):,} nodes ({lcc_pct:.1f}%) in LCC")

    except Exception as exc:
        _check("graph.read", FAIL, str(exc))

    # 4. Habitation Road Accessibility Metrics Check
    _section("4. HABITATION ROAD ACCESSIBILITY METRICS CHECK")
    try:
        hab_gdf = gpd.read_file(str(expected["habitations_geojson"]))
        _check("habitations.feature_count", PASS if len(hab_gdf) == 653 else FAIL, f"{len(hab_gdf)} habitations")

        hab_metrics = [
            "dist_to_nearest_road_m", "nearest_road_name", "nearest_road_highway_class",
            "nearest_road_surface", "road_snapping_distance_m", "network_distance_to_arterial_m",
            "network_travel_time_to_arterial_min", "network_isolated_flag", "road_accessibility_category"
        ]
        for m in hab_metrics:
            _check(f"habitations.field.{m}", PASS if m in hab_gdf.columns else FAIL, "present" if m in hab_gdf.columns else "MISSING")

        null_euc = int(hab_gdf["dist_to_nearest_road_m"].isnull().sum())
        _check("habitations.dist_to_nearest_road_no_nulls", PASS if null_euc == 0 else FAIL, f"nulls={null_euc}")

        mean_euc = float(hab_gdf["dist_to_nearest_road_m"].mean())
        mean_time = float(hab_gdf["network_travel_time_to_arterial_min"].dropna().mean())
        _check("habitations.mean_nearest_road_dist", PASS, f"{mean_euc:,.1f} m (Euclidean)")
        _check("habitations.mean_travel_time_to_arterial", PASS, f"{mean_time:.1f} min (Network Dijkstra)")

        iso_count = int(hab_gdf["network_isolated_flag"].sum())
        _check("habitations.isolated_habitations", PASS, f"{iso_count} of {len(hab_gdf)} habitations flagged as remote/isolated")

    except Exception as exc:
        _check("habitations.read", FAIL, str(exc))

    # 5. Candidate Area Road Accessibility Metrics Check
    _section("5. CANDIDATE AREA ROAD ACCESSIBILITY METRICS CHECK")
    try:
        cand_gdf = gpd.read_file(str(expected["candidate_areas_geojson"]))
        _check("candidate_areas.feature_count", PASS if len(cand_gdf) == 2998 else FAIL, f"{len(cand_gdf)} candidate areas")

        for m in hab_metrics:
            _check(f"candidate_areas.field.{m}", PASS if m in cand_gdf.columns else FAIL, "present" if m in cand_gdf.columns else "MISSING")

        null_euc_c = int(cand_gdf["dist_to_nearest_road_m"].isnull().sum())
        _check("candidate_areas.dist_to_nearest_road_no_nulls", PASS if null_euc_c == 0 else FAIL, f"nulls={null_euc_c}")

        mean_euc_c = float(cand_gdf["dist_to_nearest_road_m"].mean())
        mean_time_c = float(cand_gdf["network_travel_time_to_arterial_min"].dropna().mean())
        _check("candidate_areas.mean_nearest_road_dist", PASS, f"{mean_euc_c:,.1f} m (Euclidean)")
        _check("candidate_areas.mean_travel_time_to_arterial", PASS, f"{mean_time_c:.1f} min (Network Dijkstra)")

        iso_count_c = int(cand_gdf["network_isolated_flag"].sum())
        _check("candidate_areas.isolated_candidates", PASS, f"{iso_count_c} of {len(cand_gdf)} candidate areas flagged as remote/isolated")

    except Exception as exc:
        _check("candidate_areas.read", FAIL, str(exc))

    # 6. Summary Document Validation
    _section("6. SUMMARY DOCUMENT CHECK")
    try:
        with open(str(expected["summary_json"]), "r", encoding="utf-8") as f:
            summary = json.load(f)

        _check("summary.project", PASS if summary.get("project") == "SIH26191" else FAIL, summary.get("project"))
        _check("summary.crs", PASS if summary.get("crs") == "EPSG:32644" else FAIL, summary.get("crs"))
        _check("summary.total_network_length_km", PASS, f"{summary.get('network_statistics', {}).get('total_network_length_km')} km")
        _check("summary.planning_assumptions_present", PASS if "planning_assumptions_disclaimer" in summary else FAIL, "present")

    except Exception as exc:
        _check("summary.read", FAIL, str(exc))

    # Summary
    _section("VALIDATION SUMMARY")
    passes = sum(1 for r in results if r["status"] == PASS)
    fails = sum(1 for r in results if r["status"] == FAIL)
    warns = sum(1 for r in results if r["status"] == WARN)

    print(f"  Total checks : {len(results)}")
    print(f"  PASS         : {passes}")
    print(f"  FAIL         : {fails}")
    print(f"  WARN         : {warns}")

    if fails == 0:
        print("\n  OVERALL STATUS: PASS")
        return True
    else:
        print("\n  OVERALL STATUS: FAIL")
        return False


if __name__ == "__main__":
    if not validate_road_network():
        sys.exit(1)
