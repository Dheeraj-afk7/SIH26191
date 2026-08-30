#!/usr/bin/env python3
"""
SIH26191 -- Phase 4: Critical Infrastructure Ingestion & Lifeline Accessibility Pipeline
========================================================================================

Pilot Area: Rudraprayag District, Uttarakhand, India
CRS: Metric UTM Zone 44N (EPSG:32644) / WGS84 (EPSG:4326)

Acquires, standardizes, validates, and routes critical facilities:
- Healthcare: Hospitals, CHCs, PHCs, Subcentres, Clinics, Pharmacies
- Education: Schools, Colleges, Universities
- Emergency & Civic: Police Stations, Fire Stations, Community Centres, Administrative Offices

Computes both Euclidean proximity and Network Graph shortest paths via Phase 2 road network.
Distinguishes evidenced emergency capability from structural potential emergency receiving facilities.
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
import pandas as pd
import shapely.geometry as sg
from scipy.spatial import cKDTree

# Force UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

RAW_DIR = ROOT / "data" / "raw" / "infrastructure"
PROCESSED_DIR = ROOT / "data" / "processed" / "infrastructure"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

RAW_JSON_PATH = RAW_DIR / "osm_critical_infrastructure_raw.json"
PROVENANCE_PATH = RAW_DIR / "provenance_metadata.json"

ROAD_GRAPH_PATH = ROOT / "data" / "processed" / "roads" / "road_graph.pickle"
ROAD_NETWORK_PATH = ROOT / "data" / "processed" / "roads" / "routable_road_network.gpkg"

OUT_GPKG = PROCESSED_DIR / "critical_infrastructure.gpkg"
OUT_GEOJSON = PROCESSED_DIR / "critical_infrastructure.geojson"
OUT_CSV_AUDIT = PROCESSED_DIR / "facility_provenance_audit.csv"
OUT_SUMMARY = PROCESSED_DIR / "infrastructure_summary.json"

HAB_PATH = ROOT / "data" / "processed" / "exposure" / "habitation_exposure.geojson"
CAND_PATH = ROOT / "data" / "outputs" / "candidate_topographically_feasible_areas_attributed.geojson"

TARGET_CRS = "EPSG:32644"
SOURCE_CRS = "EPSG:4326"
AOI_BBOX_WGS84 = [78.70, 30.10, 79.50, 30.90]


def log(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def categorize_osm_facility(tags: dict) -> tuple:
    """
    Deterministic rule-based classification of OSM infrastructure.
    Returns: (broad_type, specific_category, is_evidenced_emergency, is_potential_emergency_receiver, classification_trigger)
    """
    am = str(tags.get("amenity", "")).lower()
    hc = str(tags.get("healthcare", "")).lower()
    off = str(tags.get("office", "")).lower()
    bld = str(tags.get("building", "")).lower()
    name = str(tags.get("name", "")).lower()
    em_tag = str(tags.get("emergency", "")).lower()

    # 1. Healthcare
    if "hospital" in am or "hospital" in hc or "hospital" in name or bld == "hospital":
        trigger = "TAG_HOSPITAL" if ("hospital" in am or "hospital" in hc or bld == "hospital") else "HEURISTIC_NAME_HOSPITAL"
        is_evidenced = (em_tag in ["yes", "designated"])
        return "HEALTHCARE", "HEALTHCARE_HOSPITAL", is_evidenced, True, trigger
    elif "chc" in name or "community health" in name:
        return "HEALTHCARE", "HEALTHCARE_CHC", False, True, "HEURISTIC_NAME_CHC"
    elif "phc" in name or "primary health" in name or "aphc" in name:
        return "HEALTHCARE", "HEALTHCARE_PHC", False, True, "HEURISTIC_NAME_PHC"
    elif "subcentre" in name or "sub-centre" in name or "sub centre" in name:
        return "HEALTHCARE", "HEALTHCARE_SUBCENTRE", False, False, "HEURISTIC_NAME_SUBCENTRE"
    elif "clinic" in am or "clinic" in hc or "doctors" in am or "dispensary" in name or hc in ["centre", "clinic"]:
        trigger = "TAG_CLINIC_CENTRE" if ("clinic" in am or "clinic" in hc or "doctors" in am or hc in ["centre", "clinic"]) else "HEURISTIC_NAME_DISPENSARY"
        return "HEALTHCARE", "HEALTHCARE_CLINIC", False, False, trigger
    elif "pharmacy" in am or "chemist" in am or "medical store" in name:
        return "HEALTHCARE", "HEALTHCARE_PHARMACY", False, False, "TAG_OR_NAME_PHARMACY"

    # 2. Education
    elif am == "school" or bld == "school" or "school" in name or "vidyalaya" in name or "inter college" in name:
        trigger = "TAG_SCHOOL" if (am == "school" or bld == "school") else "HEURISTIC_NAME_SCHOOL"
        return "EDUCATION", "EDUCATION_SCHOOL", False, False, trigger
    elif am == "college" or bld == "college" or "college" in name or "polytechnic" in name or "iti" in name:
        trigger = "TAG_COLLEGE" if (am == "college" or bld == "college") else "HEURISTIC_NAME_COLLEGE"
        return "EDUCATION", "EDUCATION_HIGHER", False, False, trigger
    elif am == "university" or bld == "university" or "university" in name or "hnbgu" in name:
        trigger = "TAG_UNIVERSITY" if (am == "university" or bld == "university") else "HEURISTIC_NAME_UNIVERSITY"
        return "EDUCATION", "EDUCATION_UNIVERSITY", False, False, trigger
    elif am == "kindergarten" or bld == "kindergarten" or "anganwadi" in name:
        return "EDUCATION", "EDUCATION_KINDERGARTEN", False, False, "TAG_OR_NAME_KINDERGARTEN"

    # 3. Emergency Lifeline
    elif am == "police" or "police" in name or "thana" in name or "chowki" in name:
        return "EMERGENCY", "EMERGENCY_POLICE", True, False, "TAG_OR_NAME_POLICE"
    elif am == "fire_station" or "fire" in name:
        return "EMERGENCY", "EMERGENCY_FIRE_STATION", True, False, "TAG_OR_NAME_FIRE_STATION"

    # 4. Civic & Administrative
    elif am == "townhall" or am == "community_centre" or "panchayat" in name or "milan kendra" in name:
        return "CIVIC_ADMINISTRATIVE", "CIVIC_COMMUNITY_CENTRE", False, False, "TAG_OR_NAME_COMMUNITY_CENTRE"
    elif am == "post_office" or "post office" in name or "dak ghar" in name:
        return "CIVIC_ADMINISTRATIVE", "CIVIC_POST_OFFICE", False, False, "TAG_OR_NAME_POST_OFFICE"
    elif am == "courthouse" or "court" in name:
        return "CIVIC_ADMINISTRATIVE", "CIVIC_COURTHOUSE", False, False, "TAG_OR_NAME_COURTHOUSE"
    elif off in ["government", "administrative"] or "office" in name or "bhavan" in name:
        return "CIVIC_ADMINISTRATIVE", "CIVIC_GOVERNMENT_OFFICE", False, False, "TAG_OR_NAME_GOVERNMENT_OFFICE"
    else:
        return "CIVIC_ADMINISTRATIVE", "OTHER_CIVIC_FACILITY", False, False, "OTHER_GENERIC_POI"


def load_and_standardize_facilities() -> gpd.GeoDataFrame:
    log("1. Loading raw OSM infrastructure records...")
    with open(RAW_JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    elements = data.get("elements", [])
    log(f"   Raw OSM features loaded: {len(elements)}")

    rows = []
    for idx, el in enumerate(elements):
        t = el.get("tags", {})
        lat = el.get("lat") if "lat" in el else el.get("center", {}).get("lat")
        lon = el.get("lon") if "lon" in el else el.get("center", {}).get("lon")

        if lat is None or lon is None:
            continue

        broad_type, specific_cat, is_evidenced, is_potential, trigger = categorize_osm_facility(t)
        name_clean = t.get("name") or t.get("name:en") or f"Unnamed {specific_cat.replace('_', ' ').title()}"

        rows.append({
            "osm_id": f"{el.get('type')}/{el.get('id')}",
            "osm_element_type": el.get("type"),
            "osm_native_id": el.get("id"),
            "name": name_clean,
            "facility_broad_type": broad_type,
            "facility_category": specific_cat,
            "explicitly_evidenced_emergency_capability": is_evidenced,
            "potential_emergency_receiving_facility": is_potential,
            "classification_trigger": trigger,
            "amenity_tag": t.get("amenity", ""),
            "healthcare_tag": t.get("healthcare", ""),
            "building_tag": t.get("building", ""),
            "office_tag": t.get("office", ""),
            "emergency_tag": t.get("emergency", ""),
            "operator_type": t.get("operator:type", ""),
            "source_provider": "OpenStreetMap Contributors",
            "acquisition_date": "2026-08-30",
            "latitude_wgs84": round(float(lat), 6),
            "longitude_wgs84": round(float(lon), 6),
            "geometry": sg.Point(float(lon), float(lat))
        })

    gdf_wgs84 = gpd.GeoDataFrame(rows, crs=SOURCE_CRS)
    log(f"   Converted to GeoDataFrame: {len(gdf_wgs84)} valid point geometries.")

    # Spatial bounds filter
    in_aoi = (
        (gdf_wgs84["longitude_wgs84"] >= AOI_BBOX_WGS84[0]) & (gdf_wgs84["longitude_wgs84"] <= AOI_BBOX_WGS84[2]) &
        (gdf_wgs84["latitude_wgs84"] >= AOI_BBOX_WGS84[1]) & (gdf_wgs84["latitude_wgs84"] <= AOI_BBOX_WGS84[3])
    )
    gdf_wgs84 = gdf_wgs84[in_aoi].reset_index(drop=True)
    log(f"   Features strictly within Rudraprayag AOI: {len(gdf_wgs84)}")

    # Reproject to metric EPSG:32644
    gdf_utm = gdf_wgs84.to_crs(TARGET_CRS)
    gdf_utm["easting_utm44n"] = np.round(gdf_utm.geometry.x, 2)
    gdf_utm["northing_utm44n"] = np.round(gdf_utm.geometry.y, 2)

    # Assign sequential project IDs: FAC-RDP-NNN
    gdf_utm = gdf_utm.sort_values(by=["facility_broad_type", "facility_category", "name"]).reset_index(drop=True)
    gdf_utm["facility_id"] = [f"FAC-RDP-{i+1:03d}" for i in range(len(gdf_utm))]

    ordered_cols = [
        "facility_id", "osm_id", "name", "facility_broad_type", "facility_category",
        "explicitly_evidenced_emergency_capability", "potential_emergency_receiving_facility", "classification_trigger",
        "amenity_tag", "healthcare_tag", "building_tag", "office_tag", "emergency_tag", "operator_type",
        "source_provider", "acquisition_date", "latitude_wgs84", "longitude_wgs84",
        "easting_utm44n", "northing_utm44n", "geometry"
    ]
    gdf_utm = gdf_utm[ordered_cols]
    return gdf_utm


def build_facility_spatial_index(fac_gdf: gpd.GeoDataFrame):
    """Builds KDTree indices for various facility subsets."""
    coords = np.column_stack([fac_gdf.geometry.x, fac_gdf.geometry.y])
    tree_all = cKDTree(coords)

    # Subsets
    hc_mask = fac_gdf["facility_broad_type"] == "HEALTHCARE"
    hc_indices = np.where(hc_mask)[0]
    tree_hc = cKDTree(coords[hc_indices]) if len(hc_indices) > 0 else None

    hosp_chc_mask = fac_gdf["facility_category"].isin(["HEALTHCARE_HOSPITAL", "HEALTHCARE_CHC"])
    hosp_chc_indices = np.where(hosp_chc_mask)[0]
    tree_hosp_chc = cKDTree(coords[hosp_chc_indices]) if len(hosp_chc_indices) > 0 else None

    phc_mask = fac_gdf["facility_category"] == "HEALTHCARE_PHC"
    phc_indices = np.where(phc_mask)[0]
    tree_phc = cKDTree(coords[phc_indices]) if len(phc_indices) > 0 else None

    edu_mask = fac_gdf["facility_broad_type"] == "EDUCATION"
    edu_indices = np.where(edu_mask)[0]
    tree_edu = cKDTree(coords[edu_indices]) if len(edu_indices) > 0 else None

    emerg_mask = fac_gdf["facility_broad_type"] == "EMERGENCY"
    emerg_indices = np.where(emerg_mask)[0]
    tree_emerg = cKDTree(coords[emerg_indices]) if len(emerg_indices) > 0 else None

    return {
        "fac_gdf": fac_gdf,
        "tree_all": tree_all,
        "tree_hc": tree_hc, "hc_indices": hc_indices,
        "tree_hosp_chc": tree_hosp_chc, "hosp_chc_indices": hosp_chc_indices,
        "tree_phc": tree_phc, "phc_indices": phc_indices,
        "tree_edu": tree_edu, "edu_indices": edu_indices,
        "tree_emerg": tree_emerg, "emerg_indices": emerg_indices
    }


def load_road_network_graph():
    log("2. Loading Phase 2 validated road network graph...")
    if not ROAD_GRAPH_PATH.exists():
        raise FileNotFoundError(f"Road graph not found at {ROAD_GRAPH_PATH}")

    with open(ROAD_GRAPH_PATH, "rb") as f:
        G = pickle.load(f)

    log(f"   Graph loaded: {G.number_of_nodes():,} nodes, {G.number_of_edges():,} edges.")
    
    # In Phase 2, nodes are (x, y) coordinate tuples in EPSG:32644
    node_coords = np.array(list(G.nodes()))
    node_tree = cKDTree(node_coords)
    
    return G, node_coords, node_tree


def precompute_facility_network_routing(G, node_coords, node_tree, fac_gdf: gpd.GeoDataFrame):
    """
    Precomputes multi-source Dijkstra from snapped facility nodes for instant graph lookups.
    """
    log("   Precomputing multi-source shortest paths from critical facility nodes...")
    
    def get_snapped_nodes(subset_indices):
        sub_pts = np.column_stack([fac_gdf.geometry.iloc[subset_indices].x, fac_gdf.geometry.iloc[subset_indices].y])
        dists, idxs = node_tree.query(sub_pts)
        snapped_nodes = set()
        for idx in idxs:
            snapped_nodes.add((node_coords[idx][0], node_coords[idx][1]))
        return snapped_nodes

    # Healthcare nodes
    hc_mask = np.where(fac_gdf["facility_broad_type"] == "HEALTHCARE")[0]
    hc_nodes = get_snapped_nodes(hc_mask)
    dist_to_hc = nx.multi_source_dijkstra_path_length(G, hc_nodes, weight="length_m")
    time_to_hc = nx.multi_source_dijkstra_path_length(G, hc_nodes, weight="travel_time_min")

    # Hospital / CHC nodes
    hosp_mask = np.where(fac_gdf["facility_category"].isin(["HEALTHCARE_HOSPITAL", "HEALTHCARE_CHC"]))[0]
    hosp_nodes = get_snapped_nodes(hosp_mask)
    dist_to_hosp = nx.multi_source_dijkstra_path_length(G, hosp_nodes, weight="length_m")
    time_to_hosp = nx.multi_source_dijkstra_path_length(G, hosp_nodes, weight="travel_time_min")

    # School nodes
    edu_mask = np.where(fac_gdf["facility_broad_type"] == "EDUCATION")[0]
    edu_nodes = get_snapped_nodes(edu_mask)
    dist_to_edu = nx.multi_source_dijkstra_path_length(G, edu_nodes, weight="length_m")
    time_to_edu = nx.multi_source_dijkstra_path_length(G, edu_nodes, weight="travel_time_min")

    return {
        "dist_to_hc": dist_to_hc, "time_to_hc": time_to_hc,
        "dist_to_hosp": dist_to_hosp, "time_to_hosp": time_to_hosp,
        "dist_to_edu": dist_to_edu, "time_to_edu": time_to_edu
    }


def enrich_points_with_infrastructure(points_gdf: gpd.GeoDataFrame, fac_index: dict, node_coords, node_tree, routing_dicts: dict) -> gpd.GeoDataFrame:
    """
    Computes Euclidean proximity and graph network travel times for habitations and candidate areas.
    """
    res = points_gdf.copy().reset_index(drop=True)
    if res.crs != TARGET_CRS:
        res = res.to_crs(TARGET_CRS)

    centroids = res.geometry.centroid if res.geometry.iloc[0].geom_type != "Point" else res.geometry
    pts = np.column_stack([centroids.x, centroids.y])
    n_pts = len(pts)

    fac_gdf = fac_index["fac_gdf"]

    # 1. Nearest Healthcare Facility (All Tiers)
    hc_dists, hc_idx_in_subset = fac_index["tree_hc"].query(pts)
    hc_global_indices = fac_index["hc_indices"][hc_idx_in_subset]
    res["dist_to_nearest_health_facility_m"] = np.round(hc_dists, 1)
    res["nearest_health_facility_id"] = fac_gdf["facility_id"].iloc[hc_global_indices].values
    res["nearest_health_facility_name"] = fac_gdf["name"].iloc[hc_global_indices].values
    res["nearest_health_facility_category"] = fac_gdf["facility_category"].iloc[hc_global_indices].values

    # 2. Nearest Hospital / CHC (Secondary/Tertiary Lifeline)
    hosp_dists, hosp_idx_in_subset = fac_index["tree_hosp_chc"].query(pts)
    hosp_global_indices = fac_index["hosp_chc_indices"][hosp_idx_in_subset]
    res["dist_to_nearest_hospital_chc_m"] = np.round(hosp_dists, 1)
    res["nearest_hospital_chc_id"] = fac_gdf["facility_id"].iloc[hosp_global_indices].values
    res["nearest_hospital_chc_name"] = fac_gdf["name"].iloc[hosp_global_indices].values
    res["nearest_hospital_chc_category"] = fac_gdf["facility_category"].iloc[hosp_global_indices].values

    # 3. Nearest Primary Health Centre (PHC)
    phc_dists, phc_idx_in_subset = fac_index["tree_phc"].query(pts)
    phc_global_indices = fac_index["phc_indices"][phc_idx_in_subset]
    res["dist_to_nearest_phc_m"] = np.round(phc_dists, 1)
    res["nearest_phc_id"] = fac_gdf["facility_id"].iloc[phc_global_indices].values
    res["nearest_phc_name"] = fac_gdf["name"].iloc[phc_global_indices].values

    # 4. Nearest School / Educational Facility (Separate from Healthcare)
    edu_dists, edu_idx_in_subset = fac_index["tree_edu"].query(pts)
    edu_global_indices = fac_index["edu_indices"][edu_idx_in_subset]
    res["dist_to_nearest_school_m"] = np.round(edu_dists, 1)
    res["nearest_school_id"] = fac_gdf["facility_id"].iloc[edu_global_indices].values
    res["nearest_school_name"] = fac_gdf["name"].iloc[edu_global_indices].values
    res["nearest_school_category"] = fac_gdf["facility_category"].iloc[edu_global_indices].values

    # 5. Nearest Emergency Service (Police / Fire)
    emerg_dists, emerg_idx_in_subset = fac_index["tree_emerg"].query(pts)
    emerg_global_indices = fac_index["emerg_indices"][emerg_idx_in_subset]
    res["dist_to_nearest_emergency_service_m"] = np.round(emerg_dists, 1)
    res["nearest_emergency_service_id"] = fac_gdf["facility_id"].iloc[emerg_global_indices].values
    res["nearest_emergency_service_name"] = fac_gdf["name"].iloc[emerg_global_indices].values
    res["nearest_emergency_service_category"] = fac_gdf["facility_category"].iloc[emerg_global_indices].values

    # 6. Network Routing via Road Graph
    snap_dists, snap_indices = node_tree.query(pts)

    net_dist_health = []
    net_time_health = []
    route_exists_health = []

    net_dist_hosp = []
    net_time_hosp = []
    route_exists_hosp = []

    net_dist_school = []
    net_time_school = []
    route_exists_school = []

    dist_to_hc = routing_dicts["dist_to_hc"]
    time_to_hc = routing_dicts["time_to_hc"]
    dist_to_hosp = routing_dicts["dist_to_hosp"]
    time_to_hosp = routing_dicts["time_to_hosp"]
    dist_to_edu = routing_dicts["dist_to_edu"]
    time_to_edu = routing_dicts["time_to_edu"]

    for i in range(n_pts):
        snap_d = float(snap_dists[i])
        snap_node = (node_coords[snap_indices[i]][0], node_coords[snap_indices[i]][1])
        walk_time_min = (snap_d / 1000.0) / 4.0 * 60.0

        # Health routing
        if snap_d <= 3000.0 and snap_node in dist_to_hc:
            net_dist_health.append(round(float(dist_to_hc[snap_node] + snap_d), 1))
            net_time_health.append(round(float(time_to_hc[snap_node] + walk_time_min), 1))
            route_exists_health.append(True)
        else:
            net_dist_health.append(None)
            net_time_health.append(None)
            route_exists_health.append(False)

        # Hospital/CHC routing (mapped facilities)
        if snap_d <= 3000.0 and snap_node in dist_to_hosp:
            net_dist_hosp.append(round(float(dist_to_hosp[snap_node] + snap_d), 1))
            net_time_hosp.append(round(float(time_to_hosp[snap_node] + walk_time_min), 1))
            route_exists_hosp.append(True)
        else:
            net_dist_hosp.append(None)
            net_time_hosp.append(None)
            route_exists_hosp.append(False)

        # School routing
        if snap_d <= 3000.0 and snap_node in dist_to_edu:
            net_dist_school.append(round(float(dist_to_edu[snap_node] + snap_d), 1))
            net_time_school.append(round(float(time_to_edu[snap_node] + walk_time_min), 1))
            route_exists_school.append(True)
        else:
            net_dist_school.append(None)
            net_time_school.append(None)
            route_exists_school.append(False)

    res["network_dist_to_health_facility_m"] = net_dist_health
    res["network_time_to_health_facility_min"] = net_time_health
    res["health_facility_route_exists"] = route_exists_health

    res["network_dist_to_hospital_chc_m"] = net_dist_hosp
    res["network_time_to_hospital_chc_min"] = net_time_hosp
    res["hospital_chc_route_exists"] = route_exists_hosp

    res["network_dist_to_school_m"] = net_dist_school
    res["network_time_to_school_min"] = net_time_school
    res["school_route_exists"] = route_exists_school

    # Lifeline Deficit Analytical Flags
    res["has_health_within_5km_flag"] = res["dist_to_nearest_health_facility_m"] <= 5000.0
    res["has_school_within_3km_flag"] = res["dist_to_nearest_school_m"] <= 3000.0
    res["hospital_chc_access_under_60min_flag"] = [bool(t is not None and t <= 60.0) for t in net_time_hosp]
    res["infrastructure_status"] = "INFRASTRUCTURE_METRICS_INGESTED"

    return res


def export_audit_csv(fac_gdf: gpd.GeoDataFrame):
    log("4. Exporting record-level facility provenance audit table (facility_provenance_audit.csv)...")
    audit_df = pd.DataFrame({
        "facility_id": fac_gdf["facility_id"],
        "osm_id": fac_gdf["osm_id"],
        "facility_name": fac_gdf["name"],
        "facility_broad_type": fac_gdf["facility_broad_type"],
        "facility_category": fac_gdf["facility_category"],
        "explicitly_evidenced_emergency_capability": fac_gdf["explicitly_evidenced_emergency_capability"],
        "potential_emergency_receiving_facility": fac_gdf["potential_emergency_receiving_facility"],
        "classification_trigger": fac_gdf["classification_trigger"],
        "amenity_tag": fac_gdf["amenity_tag"],
        "healthcare_tag": fac_gdf["healthcare_tag"],
        "building_tag": fac_gdf["building_tag"],
        "office_tag": fac_gdf["office_tag"],
        "source_provider": fac_gdf["source_provider"],
        "acquisition_date": fac_gdf["acquisition_date"],
        "latitude_wgs84": fac_gdf["latitude_wgs84"],
        "longitude_wgs84": fac_gdf["longitude_wgs84"],
        "easting_utm44n": fac_gdf["easting_utm44n"],
        "northing_utm44n": fac_gdf["northing_utm44n"]
    })
    audit_df.to_csv(str(OUT_CSV_AUDIT), index=False, encoding="utf-8")
    log(f"   [OUTPUT] Written Facility Audit Table to {OUT_CSV_AUDIT.relative_to(ROOT)} ({len(audit_df)} records)")


def run_pipeline():
    print("=" * 76)
    print("  SIH26191: Phase 4 Critical Infrastructure Ingestion & Routing Pipeline")
    print("=" * 76)

    fac_gdf = load_and_standardize_facilities()
    fac_index = build_facility_spatial_index(fac_gdf)
    G, node_coords, node_tree = load_road_network_graph()
    routing_dicts = precompute_facility_network_routing(G, node_coords, node_tree, fac_gdf)

    # Export audit table
    export_audit_csv(fac_gdf)

    # Export Processed Infrastructure layers
    log("3. Exporting processed critical infrastructure layers...")
    fac_gdf.to_file(str(OUT_GPKG), layer="facilities", driver="GPKG")
    log(f"   [OUTPUT] Written GeoPackage to {OUT_GPKG.relative_to(ROOT)} ({OUT_GPKG.stat().st_size / 1024:.1f} KB)")

    fac_wgs84 = fac_gdf.to_crs(SOURCE_CRS)
    fac_wgs84.to_file(str(OUT_GEOJSON), driver="GeoJSON")
    log(f"   [OUTPUT] Written GeoJSON to {OUT_GEOJSON.relative_to(ROOT)} ({OUT_GEOJSON.stat().st_size / 1024:.1f} KB)")

    # Enrich habitations
    if HAB_PATH.exists():
        log(f"   Evaluating infrastructure accessibility for 653 habitations from {HAB_PATH.name}...")
        hab_gdf = gpd.read_file(str(HAB_PATH))
        hab_enriched = enrich_points_with_infrastructure(hab_gdf, fac_index, node_coords, node_tree, routing_dicts)
        hab_enriched.to_file(str(HAB_PATH), driver="GeoJSON")
        log(f"   [SUCCESS] Updated {HAB_PATH.name} with infrastructure proximity & network metrics.")

    # Enrich candidate areas
    if CAND_PATH.exists():
        log(f"   Evaluating infrastructure accessibility for 2,998 candidate areas from {CAND_PATH.name}...")
        cand_gdf = gpd.read_file(str(CAND_PATH))
        cand_enriched = enrich_points_with_infrastructure(cand_gdf, fac_index, node_coords, node_tree, routing_dicts)
        cand_enriched.to_file(str(CAND_PATH), driver="GeoJSON")
        log(f"   [SUCCESS] Updated {CAND_PATH.name} with infrastructure proximity & network metrics.")

    # Generate Summary Breakdown
    broad_type_counts = {str(k): int(v) for k, v in fac_gdf["facility_broad_type"].value_counts().items()}
    category_counts = {str(k): int(v) for k, v in fac_gdf["facility_category"].value_counts().items()}
    evidenced_emergency_count = int(fac_gdf["explicitly_evidenced_emergency_capability"].sum())
    potential_emergency_receiver_count = int(fac_gdf["potential_emergency_receiving_facility"].sum())

    summary = {
        "project": "SIH26191",
        "pipeline_phase": "Phase 4: Critical Infrastructure (Health, Education & Emergency Facilities)",
        "source_provider": "OpenStreetMap Contributors",
        "source_license": "ODbL 1.0",
        "acquisition_date": "2026-08-30",
        "processed_timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "crs": TARGET_CRS,
        "total_critical_facilities": len(fac_gdf),
        "emergency_capability_breakdown": {
            "explicitly_evidenced_emergency_facilities": evidenced_emergency_count,
            "potential_emergency_receiving_clinical_facilities": potential_emergency_receiver_count,
            "routine_healthcare_and_civic_facilities": len(fac_gdf) - (evidenced_emergency_count + potential_emergency_receiver_count)
        },
        "facility_broad_type_breakdown": broad_type_counts,
        "facility_category_breakdown": category_counts,
        "habitation_accessibility_summary": {
            "total_habitations": len(hab_enriched) if 'hab_enriched' in locals() else 0,
            "mean_dist_to_health_facility_m": round(float(hab_enriched["dist_to_nearest_health_facility_m"].mean()), 1) if 'hab_enriched' in locals() else 0,
            "mean_dist_to_hospital_chc_m": round(float(hab_enriched["dist_to_nearest_hospital_chc_m"].mean()), 1) if 'hab_enriched' in locals() else 0,
            "mean_dist_to_school_m": round(float(hab_enriched["dist_to_nearest_school_m"].mean()), 1) if 'hab_enriched' in locals() else 0,
            "habitations_with_health_under_5km": int((hab_enriched["has_health_within_5km_flag"]).sum()) if 'hab_enriched' in locals() else 0,
            "habitations_with_school_under_3km": int((hab_enriched["has_school_within_3km_flag"]).sum()) if 'hab_enriched' in locals() else 0,
            "habitations_with_hospital_chc_under_60min": int((hab_enriched["hospital_chc_access_under_60min_flag"]).sum()) if 'hab_enriched' in locals() else 0
        },
        "candidate_area_accessibility_summary": {
            "total_candidate_areas": len(cand_enriched) if 'cand_enriched' in locals() else 0,
            "mean_dist_to_health_facility_m": round(float(cand_enriched["dist_to_nearest_health_facility_m"].mean()), 1) if 'cand_enriched' in locals() else 0,
            "mean_dist_to_hospital_chc_m": round(float(cand_enriched["dist_to_nearest_hospital_chc_m"].mean()), 1) if 'cand_enriched' in locals() else 0,
            "mean_dist_to_school_m": round(float(cand_enriched["dist_to_nearest_school_m"].mean()), 1) if 'cand_enriched' in locals() else 0,
            "candidates_with_health_under_5km": int((cand_enriched["has_health_within_5km_flag"]).sum()) if 'cand_enriched' in locals() else 0,
            "candidates_with_school_under_3km": int((cand_enriched["has_school_within_3km_flag"]).sum()) if 'cand_enriched' in locals() else 0,
            "candidates_with_hospital_chc_under_60min": int((cand_enriched["hospital_chc_access_under_60min_flag"]).sum()) if 'cand_enriched' in locals() else 0
        },
        "education_completeness_statement": (
            "OSM MAPPED EDUCATION INDICATOR ONLY. Mapped schools (N=70) reflect open community-contributed "
            "geospatial features. They do not constitute an exhaustive administrative census of all rural primary "
            "and upper-primary school institutions across all 653 revenue villages."
        ),
        "methodological_safeguard": (
            "CRITICAL INFRASTRUCTURE ACCESSIBILITY METRICS ARE CONTEXTUAL LIFELINE INDICATORS ONLY. "
            "They quantify isolation from healthcare and educational services to assist planners in evaluating "
            "community vulnerability. They do not alter the deterministic core priority classification engine."
        )
    }

    with open(OUT_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    log(f"[OUTPUT] Written Infrastructure Summary to {OUT_SUMMARY.relative_to(ROOT)}")
    print("\n[SUCCESS] Phase 4 Critical Infrastructure Pipeline Complete.")


if __name__ == "__main__":
    run_pipeline()
