#!/usr/bin/env python3
"""
SIH26191 -- Phase 2: Routable Road Network & Mountain Accessibility Pipeline
=============================================================================

Pilot Area: Rudraprayag District, Uttarakhand, India
CRS: EPSG:32644 (UTM Zone 44N)

Processing Steps:
1. Ingest raw OSM road GeoJSON with all original attributes preserved.
2. Filter valid highway classes and reproject to metric EPSG:32644.
3. Compute metric segment lengths, assign assumed mountain speeds, and calculate edge traversal times.
4. Construct a NetworkX topological graph and analyze connectivity (connected components, LCC).
5. Compute dual accessibility metrics for Habitations (653) and Candidate Areas (2,998):
   - Euclidean straight-line nearest road distance and road attributes
   - Network shortest-path distance (m) and travel time (min) to main arterial corridor (NH-107/NH-07/SH)
   - Mountain road accessibility classification and isolation flags
6. Export clean GeoPackage, graph pickle, summary JSON, and enriched datasets.
"""

import datetime
import io
import json
import os
import pathlib
import pickle
import sys
import warnings
import geopandas as gpd
import networkx as nx
import numpy as np
import shapely.geometry as sg
from scipy.spatial import cKDTree
import yaml

# Force UTF-8 on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CONFIG_PATH = ROOT / "configs" / "road_network.yaml"

PROCESSED_ROADS_DIR = ROOT / "data" / "processed" / "roads"
PROCESSED_ROADS_DIR.mkdir(parents=True, exist_ok=True)


def log(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_config() -> dict:
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    return {}


def build_road_network():
    print("=" * 76)
    print("  SIH26191: Phase 2 Routable Road Network & Mountain Accessibility")
    print("=" * 76)

    cfg = load_config()
    target_crs = cfg.get("target_crs", "EPSG:32644")
    raw_path = ROOT / cfg.get("paths", {}).get("raw_roads_geojson", "data/raw/roads/osm_roads_rudraprayag.geojson")
    out_gpkg = ROOT / cfg.get("paths", {}).get("processed_roads_gpkg", "data/processed/roads/routable_road_network.gpkg")
    out_graph = ROOT / cfg.get("paths", {}).get("graph_pickle", "data/processed/roads/road_graph.pickle")
    out_summary = ROOT / cfg.get("paths", {}).get("summary_json", "data/processed/roads/road_summary.json")

    # 1. Ingest and Validate Raw Road Layer
    log(f"1. Loading raw OSM road network from {raw_path.relative_to(ROOT)}...")
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw road file not found at {raw_path}")

    gdf_raw = gpd.read_file(str(raw_path))
    log(f"   Loaded {len(gdf_raw):,} raw road segments. Source CRS: {gdf_raw.crs}")

    # 2. Filter & Reproject to Metric CRS (EPSG:32644)
    log(f"2. Filtering and reprojecting road network to {target_crs}...")
    excluded_classes = set(cfg.get("highway_filtering", {}).get("excluded_classes", ["construction", "proposed", "abandoned"]))
    vehicular_classes = set(cfg.get("highway_filtering", {}).get("vehicular_classes", []))
    arterial_classes = {"trunk", "trunk_link", "primary", "primary_link"}

    gdf = gdf_raw[~gdf_raw["highway"].isin(excluded_classes)].copy()
    if gdf.crs != target_crs:
        gdf = gdf.to_crs(target_crs)

    # 3. Compute Segment Lengths and Travel Time Impedance
    log("3. Computing metric segment lengths and mountain travel time impedance...")
    gdf["length_m"] = gdf.geometry.length.round(2)
    gdf = gdf[gdf["length_m"] > 0].copy()

    speeds = cfg.get("assumed_speeds_kmh", {})
    default_spd = speeds.get("default_speed", 15.0)

    gdf["assumed_speed_kmh"] = gdf["highway"].map(lambda h: float(speeds.get(h, default_spd)))
    gdf["travel_time_min"] = ((gdf["length_m"] / 1000.0) / gdf["assumed_speed_kmh"] * 60.0).round(4)
    gdf["is_vehicular"] = gdf["highway"].isin(vehicular_classes)
    gdf["is_arterial"] = gdf["highway"].isin(arterial_classes)

    total_len_km = float(gdf["length_m"].sum() / 1000.0)
    vehicular_len_km = float(gdf[gdf["is_vehicular"]]["length_m"].sum() / 1000.0)
    arterial_len_km = float(gdf[gdf["is_arterial"]]["length_m"].sum() / 1000.0)

    log(f"   Total Network Length    : {total_len_km:,.1f} km ({len(gdf):,} segments)")
    log(f"   Vehicular Road Length   : {vehicular_len_km:,.1f} km ({int(gdf['is_vehicular'].sum()):,} segments)")
    log(f"   Arterial Highway Length : {arterial_len_km:,.1f} km ({int(gdf['is_arterial'].sum()):,} segments)")

    # 4. Construct Topological Graph (NetworkX)
    log("4. Building NetworkX topological graph from road geometry...")
    G = nx.Graph()
    G_vehicular = nx.Graph()

    for idx, row in gdf.iterrows():
        geom = row.geometry
        if geom.geom_type == "LineString":
            lines = [geom]
        elif geom.geom_type == "MultiLineString":
            lines = list(geom.geoms)
        else:
            continue

        for line in lines:
            coords = list(line.coords)
            for i in range(len(coords) - 1):
                p1 = (round(coords[i][0], 1), round(coords[i][1], 1))
                p2 = (round(coords[i+1][0], 1), round(coords[i+1][1], 1))
                if p1 == p2:
                    continue

                sub_len = float(sg.LineString([coords[i], coords[i+1]]).length)
                sub_time = float((sub_len / 1000.0) / row["assumed_speed_kmh"] * 60.0)

                attr = {
                    "length_m": round(sub_len, 2),
                    "travel_time_min": round(sub_time, 4),
                    "highway": row["highway"],
                    "name": row.get("name"),
                    "ref": row.get("ref"),
                    "surface": row.get("surface"),
                    "is_vehicular": row["is_vehicular"],
                    "is_arterial": row["is_arterial"],
                    "osm_id": row.get("osm_id")
                }

                G.add_edge(p1, p2, **attr)
                if row["is_vehicular"]:
                    G_vehicular.add_edge(p1, p2, **attr)

    log(f"   Full Graph Nodes: {G.number_of_nodes():,} | Edges: {G.number_of_edges():,}")
    log(f"   Vehicular Graph Nodes: {G_vehicular.number_of_nodes():,} | Edges: {G_vehicular.number_of_edges():,}")

    # Connected Components Analysis
    components = list(nx.connected_components(G_vehicular))
    num_components = len(components)
    largest_cc = max(components, key=len) if components else set()
    lcc_size = len(largest_cc)
    lcc_pct = (lcc_size * 100.0 / G_vehicular.number_of_nodes()) if G_vehicular.number_of_nodes() > 0 else 0.0

    log(f"   Vehicular Connected Components: {num_components}")
    log(f"   Largest Connected Component (LCC): {lcc_size:,} nodes ({lcc_pct:.1f}% of network)")

    # Identify Arterial Nodes for Destination Routing
    arterial_nodes = set()
    for u, v, data in G_vehicular.edges(data=True):
        if data.get("is_arterial"):
            arterial_nodes.add(u)
            arterial_nodes.add(v)
    log(f"   Arterial Target Highway Nodes (NH-107/NH-07/SH): {len(arterial_nodes):,}")

    # Precompute multi-source Dijkstra from all arterial nodes across vehicular graph
    log("   Precomputing shortest path distances & times to arterial highway network...")
    dist_to_arterial = {}
    time_to_arterial = {}

    if arterial_nodes:
        dist_to_arterial = nx.multi_source_dijkstra_path_length(G_vehicular, arterial_nodes, weight="length_m")
        time_to_arterial = nx.multi_source_dijkstra_path_length(G_vehicular, arterial_nodes, weight="travel_time_min")

    # Build KDTree of Vehicular Graph Nodes for Snapping
    node_coords = np.array(list(G_vehicular.nodes()))
    kdtree_nodes = cKDTree(node_coords)

    # 5. Dual Accessibility Computation for Habitations & Candidate Areas
    log("5. Computing dual accessibility metrics (Euclidean proximity + Network travel time)...")

    def evaluate_accessibility(points_gdf: gpd.GeoDataFrame, name_col: str = "village_name") -> gpd.GeoDataFrame:
        res = points_gdf.copy().reset_index(drop=True)
        if res.crs != target_crs:
            res = res.to_crs(target_crs)

        # A. Euclidean Nearest Road Proximity via sjoin_nearest
        # Carry nearest road attributes: name, ref, highway, surface, is_vehicular
        temp_pts = res[[res.geometry.name]].copy()
        temp_pts["_temp_id"] = np.arange(len(temp_pts))

        joined = gpd.sjoin_nearest(
            temp_pts,
            gdf[["osm_id", "name", "ref", "highway", "surface", "is_vehicular", "geometry"]],
            how="left",
            distance_col="dist_to_nearest_road_m"
        )
        joined = joined.drop_duplicates(subset=["_temp_id"], keep="first").sort_values("_temp_id")

        res["dist_to_nearest_road_m"] = joined["dist_to_nearest_road_m"].round(1).values
        res["nearest_road_name"] = joined["name"].fillna("Unnamed Road").values
        res["nearest_road_ref"] = joined["ref"].fillna("None").values
        res["nearest_road_highway_class"] = joined["highway"].fillna("unknown").values
        res["nearest_road_surface"] = joined["surface"].fillna("unknown").values
        res["nearest_road_is_vehicular"] = joined["is_vehicular"].fillna(False).values

        # B. Network-Based Routing to Arterial Highway
        centroids = res.geometry.centroid if res.geometry.iloc[0].geom_type != "Point" else res.geometry
        pts = np.column_stack([centroids.x, centroids.y])

        snap_dists, snap_indices = kdtree_nodes.query(pts)

        net_dists = []
        net_times = []
        isolated_flags = []
        route_exists = []
        categories = []

        max_snap = float(cfg.get("thresholds", {}).get("max_snapping_radius_m", 3000.0))

        for i in range(len(res)):
            snap_d = float(snap_dists[i])
            node_tuple = (node_coords[snap_indices[i]][0], node_coords[snap_indices[i]][1])

            # Precedence Tier 1: ISOLATED_GRAPH_DISCONNECTED
            if snap_d > max_snap or node_tuple not in dist_to_arterial:
                net_dists.append(None)
                net_times.append(None)
                route_exists.append(False)
                isolated_flags.append(True)
                categories.append("ISOLATED_GRAPH_DISCONNECTED")
            else:
                d_art = round(float(dist_to_arterial[node_tuple]), 1)
                t_art = round(float(time_to_arterial[node_tuple]), 1)
                net_dists.append(d_art)
                net_times.append(t_art)
                route_exists.append(True)

                # Precedence Tier 2: SEVERELY_REMOTE (connected, but >90 min or snapping 1.5 - 3 km)
                if t_art > 90.0 or snap_d > 1500.0:
                    categories.append("SEVERELY_REMOTE")
                    isolated_flags.append(True)
                # Precedence Tier 3: REMOTE (45 - 90 min, snapping <= 1.5 km)
                elif t_art > 45.0:
                    categories.append("REMOTE")
                    isolated_flags.append(False)
                # Precedence Tier 4: MODERATELY_ACCESSIBLE (15 - 45 min, snapping <= 1.0 km)
                elif t_art > 15.0 or snap_d > 500.0:
                    categories.append("MODERATELY_ACCESSIBLE")
                    isolated_flags.append(False)
                # Precedence Tier 5: HIGHLY_ACCESSIBLE (<= 15 min, snapping <= 500 m)
                else:
                    categories.append("HIGHLY_ACCESSIBLE")
                    isolated_flags.append(False)

        res["road_snapping_distance_m"] = np.round(snap_dists, 1)
        res["network_route_exists"] = route_exists
        res["network_distance_to_arterial_m"] = net_dists
        res["network_travel_time_to_arterial_min"] = net_times
        res["network_isolated_flag"] = isolated_flags
        res["road_accessibility_category"] = categories
        res["road_accessibility_status"] = "ROUTABLE_NETWORK_EVALUATED"

        return res

    # 5A. Evaluate Habitations (653 villages)
    hab_path = ROOT / cfg.get("paths", {}).get("habitations_geojson", "data/processed/exposure/habitation_exposure.geojson")
    if hab_path.exists():
        log(f"   Evaluating accessibility for 653 habitations from {hab_path.name}...")
        hab_gdf = gpd.read_file(str(hab_path))
        hab_enriched = evaluate_accessibility(hab_gdf, "village_name")
        hab_enriched.to_file(str(hab_path), driver="GeoJSON")
        log(f"   [SUCCESS] Updated {hab_path.name} with road accessibility metrics.")

    # 5B. Evaluate Candidate Areas (2,998)
    cand_path = ROOT / cfg.get("paths", {}).get("candidate_areas_geojson", "data/outputs/candidate_topographically_feasible_areas_attributed.geojson")
    if cand_path.exists():
        log(f"   Evaluating accessibility for {len(gpd.read_file(str(cand_path))):,} candidate areas from {cand_path.name}...")
        cand_gdf = gpd.read_file(str(cand_path))
        cand_enriched = evaluate_accessibility(cand_gdf, "area_id")
        cand_enriched.to_file(str(cand_path), driver="GeoJSON")
        log(f"   [SUCCESS] Updated {cand_path.name} with road accessibility metrics.")

    # 6. Save Processed Artifacts
    log("6. Saving processed road network and serialized graph...")
    gdf.to_file(str(out_gpkg), layer="routable_roads", driver="GPKG")
    log(f"   [OUTPUT] Written {len(gdf):,} road features to {out_gpkg.relative_to(ROOT)}")

    with open(out_graph, "wb") as f:
        pickle.dump(G, f, protocol=pickle.HIGHEST_PROTOCOL)
    log(f"   [OUTPUT] Saved NetworkX graph to {out_graph.relative_to(ROOT)}")

    # Class Breakdown Summary
    class_summary = {}
    for hw, group in gdf.groupby("highway"):
        class_summary[hw] = {
            "segments": len(group),
            "length_km": round(float(group["length_m"].sum() / 1000.0), 2),
            "assumed_speed_kmh": float(group["assumed_speed_kmh"].iloc[0]),
            "is_vehicular": bool(group["is_vehicular"].iloc[0]),
            "is_arterial": bool(group["is_arterial"].iloc[0])
        }

    summary_doc = {
        "project": "SIH26191",
        "pipeline_phase": "Phase 2: Routable Road Network & Mountain Accessibility",
        "processed_timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "crs": target_crs,
        "source_dataset": "OpenStreetMap Contributors (ODbL 1.0)",
        "network_statistics": {
            "total_segments": len(gdf),
            "total_network_length_km": round(total_len_km, 2),
            "vehicular_network_length_km": round(vehicular_len_km, 2),
            "arterial_network_length_km": round(arterial_len_km, 2),
            "total_graph_nodes": G.number_of_nodes(),
            "total_graph_edges": G.number_of_edges(),
            "vehicular_graph_nodes": G_vehicular.number_of_nodes(),
            "vehicular_graph_edges": G_vehicular.number_of_edges(),
            "connected_components_count": num_components,
            "largest_connected_component_nodes": lcc_size,
            "largest_connected_component_pct": round(lcc_pct, 2),
            "arterial_highway_nodes": len(arterial_nodes)
        },
        "highway_classes": class_summary,
        "habitation_accessibility_summary": {
            "total_habitations": int(len(hab_enriched)) if 'hab_enriched' in locals() else 0,
            "category_distribution": {str(k): int(v) for k, v in hab_enriched["road_accessibility_category"].value_counts().items()} if 'hab_enriched' in locals() else {},
            "mean_dist_to_nearest_road_m": round(float(hab_enriched["dist_to_nearest_road_m"].mean()), 1) if 'hab_enriched' in locals() else 0,
            "mean_travel_time_to_arterial_min": round(float(hab_enriched["network_travel_time_to_arterial_min"].dropna().mean()), 1) if 'hab_enriched' in locals() else 0,
            "isolated_habitations_count": int(hab_enriched["network_isolated_flag"].sum()) if 'hab_enriched' in locals() else 0
        },
        "candidate_area_accessibility_summary": {
            "total_candidate_areas": int(len(cand_enriched)) if 'cand_enriched' in locals() else 0,
            "category_distribution": {str(k): int(v) for k, v in cand_enriched["road_accessibility_category"].value_counts().items()} if 'cand_enriched' in locals() else {},
            "mean_dist_to_nearest_road_m": round(float(cand_enriched["dist_to_nearest_road_m"].mean()), 1) if 'cand_enriched' in locals() else 0,
            "mean_travel_time_to_arterial_min": round(float(cand_enriched["network_travel_time_to_arterial_min"].dropna().mean()), 1) if 'cand_enriched' in locals() else 0,
            "isolated_candidates_count": int(cand_enriched["network_isolated_flag"].sum()) if 'cand_enriched' in locals() else 0
        },
        "planning_assumptions_disclaimer": (
            "ANALYTICAL PLANNING ASSUMPTIONS ONLY. Assumed speeds (trunk: 35 km/h, secondary: 25 km/h, "
            "tertiary/PMGSY: 20 km/h, track: 10 km/h) represent realistic mountain travel speed models for rugged "
            "Himalayan terrain. OSM highway attributes are preserved without assuming all-weather passability. "
            "Actual travel accessibility requires field verification and seasonal landslide monitoring."
        )
    }

    with open(out_summary, "w", encoding="utf-8") as f:
        json.dump(summary_doc, f, indent=2)

    log(f"[OUTPUT] Written Road Network Summary to {out_summary.relative_to(ROOT)}")
    print("\n[SUCCESS] Phase 2 Road Network & Mountain Accessibility Processing Complete.")


if __name__ == "__main__":
    build_road_network()
