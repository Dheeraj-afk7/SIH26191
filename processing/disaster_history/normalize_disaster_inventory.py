#!/usr/bin/env python3
"""
SIH26191 -- Phase 3: Historical Disaster Ingestion & Multi-Year Landslide Inventory Pipeline
===========================================================================================

Pilot Area: Rudraprayag District, Uttarakhand, India
CRS: Metric UTM Zone 44N (EPSG:32644) / WGS84 (EPSG:4326)

Record Classification: LITERATURE_CURATED_HISTORICAL_RECORD
Acquisition Method: MANUAL_RESEARCH_AND_CURATED_EXTRACTION
"""

import datetime
import io
import json
import os
import pathlib
import sys
import warnings
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely.geometry as sg
from scipy.spatial import cKDTree

# Force UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
warnings.filterwarnings("ignore")

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent

RAW_DIR = ROOT / "data" / "raw" / "disaster_history"
PROCESSED_DIR = ROOT / "data" / "processed" / "disaster_history"
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

ISRO_RAW_PATH = RAW_DIR / "isro_nrsc_landslide_inventory.json"
USDMA_RAW_PATH = RAW_DIR / "usdma_desinventar_historical_events.json"
PROVENANCE_PATH = RAW_DIR / "provenance_metadata.json"

OUT_GPKG = PROCESSED_DIR / "historical_disaster_inventory.gpkg"
OUT_GEOJSON = PROCESSED_DIR / "historical_disaster_inventory.geojson"
OUT_CSV_AUDIT = PROCESSED_DIR / "record_provenance_audit.csv"
OUT_SUMMARY = PROCESSED_DIR / "disaster_summary.json"

HAB_PATH = ROOT / "data" / "processed" / "exposure" / "habitation_exposure.geojson"
CAND_PATH = ROOT / "data" / "outputs" / "candidate_topographically_feasible_areas_attributed.geojson"

TARGET_CRS = "EPSG:32644"
SOURCE_CRS = "EPSG:4326"


def log(msg: str):
    ts = datetime.datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


def load_raw_datasets():
    log("1. Loading raw disaster records from literature curation source files...")
    
    with open(ISRO_RAW_PATH, "r", encoding="utf-8") as f:
        isro_data = json.load(f)
    with open(USDMA_RAW_PATH, "r", encoding="utf-8") as f:
        usdma_data = json.load(f)

    isro_recs = isro_data.get("records", [])
    usdma_recs = usdma_data.get("records", [])

    log(f"   Published Peer-Reviewed Literature records : {len(isro_recs)}")
    log(f"   Secondary Incident Compilation records     : {len(usdma_recs)}")

    combined = []
    for r in isro_recs:
        r_copy = dict(r)
        r_copy["raw_catalog"] = "PEER_REVIEWED_LITERATURE_INVENTORY"
        r_copy["orig_lat"] = r["latitude"]
        r_copy["orig_lon"] = r["longitude"]
        combined.append(r_copy)

    for r in usdma_recs:
        r_copy = dict(r)
        r_copy["raw_catalog"] = "SECONDARY_INCIDENT_COMPILATION"
        r_copy["orig_lat"] = r["latitude"]
        r_copy["orig_lon"] = r["longitude"]
        combined.append(r_copy)

    log(f"   Total curated records ingested: {len(combined)}")
    return combined


def deduplicate_records(raw_records: list) -> tuple:
    log("2. Performing conservative spatio-temporal deduplication across sources...")
    geoms = [sg.Point(r["longitude"], r["latitude"]) for r in raw_records]
    gdf = gpd.GeoDataFrame(raw_records, geometry=geoms, crs=SOURCE_CRS).to_crs(TARGET_CRS)

    gdf["easting"] = gdf.geometry.x
    gdf["northing"] = gdf.geometry.y
    gdf["date_dt"] = pd.to_datetime(gdf["date"], errors="coerce")

    merged_indices = set()
    canonical_list = []
    dedup_log = []

    for i in range(len(gdf)):
        if i in merged_indices:
            continue

        r1 = gdf.iloc[i]
        matched_peers = []

        for j in range(i + 1, len(gdf)):
            if j in merged_indices:
                continue

            r2 = gdf.iloc[j]

            # Match criteria: same event type, spatial distance <= 500m, time diff <= 3 days
            same_type = (r1["hazard_type"] == r2["hazard_type"])
            dist_m = r1.geometry.distance(r2.geometry)

            time_diff_days = None
            if pd.notna(r1["date_dt"]) and pd.notna(r2["date_dt"]):
                time_diff_days = abs((r1["date_dt"] - r2["date_dt"]).days)
            elif r1["year"] == r2["year"]:
                time_diff_days = 0

            if same_type and dist_m <= 500.0 and (time_diff_days is not None and time_diff_days <= 3):
                matched_peers.append((j, r2, dist_m, time_diff_days))
                merged_indices.add(j)

        # Build canonical record
        canon = dict(r1.drop(columns=["geometry", "date_dt"]))
        duplicate_refs = []
        spatial_offsets = []

        if matched_peers:
            providers = {r1["source_provider"]}
            for p_idx, p_row, p_dist, p_td in matched_peers:
                providers.add(p_row["source_provider"])
                duplicate_refs.append({
                    "source_provider": p_row["source_provider"],
                    "source_document_title": p_row.get("source_document_title", ""),
                    "spatial_offset_m": round(float(p_dist), 1),
                    "temporal_offset_days": int(p_td)
                })
                spatial_offsets.append(round(float(p_dist), 1))
                if pd.notna(p_row.get("fatalities")) and p_row.get("fatalities", 0) > canon.get("fatalities", 0):
                    canon["fatalities"] = int(p_row["fatalities"])

            canon["source_provider"] = " + ".join(sorted(providers))
            dedup_log.append({
                "canonical_location": canon["location_name"],
                "merged_records": duplicate_refs
            })

        canon["duplicate_source_refs"] = duplicate_refs
        canon["spatial_offset_m"] = spatial_offsets[0] if spatial_offsets else 0.0
        canon["easting_utm44n"] = round(float(r1["easting"]), 2)
        canon["northing_utm44n"] = round(float(r1["northing"]), 2)
        canon["geometry"] = r1.geometry
        canonical_list.append(canon)

    log(f"   Deduplication complete: {len(dedup_log)} cross-source duplicate pairs merged.")
    log(f"   Canonical discrete disaster events retained: {len(canonical_list)}")
    return canonical_list, dedup_log


def build_canonical_geodataframe(canonical_records: list) -> gpd.GeoDataFrame:
    log("3. Standardizing canonical schema and assigning stable project incident IDs...")
    
    canon_gdf = gpd.GeoDataFrame(canonical_records, crs=TARGET_CRS)
    canon_gdf = canon_gdf.sort_values(by=["year", "date"]).reset_index(drop=True)

    # Assign standardized project canonical ID: DIS-RDP-YYYY-NNN
    incident_ids = []
    year_counters = {}
    for idx, row in canon_gdf.iterrows():
        yr = int(row["year"])
        year_counters[yr] = year_counters.get(yr, 0) + 1
        inc_id = f"DIS-RDP-{yr}-{year_counters[yr]:03d}"
        incident_ids.append(inc_id)

    canon_gdf["incident_id"] = incident_ids
    canon_gdf["canonical_incident_id"] = incident_ids
    canon_gdf["source_native_id"] = "NULL"  # Strictly NULL as no native machine-readable ID was directly queried

    # Ensure required columns
    canon_gdf["fatalities"] = canon_gdf["fatalities"].fillna(0).astype(int)
    canon_gdf["injuries"] = canon_gdf["injuries"].fillna(0).astype(int)
    canon_gdf["households_affected"] = canon_gdf["households_affected"].fillna(0).astype(int)
    canon_gdf["coordinate_uncertainty_m"] = canon_gdf["coordinate_uncertainty_m"].fillna(100.0).astype(float)
    canon_gdf["duplicate_source_count"] = canon_gdf["duplicate_source_refs"].apply(len)
    canon_gdf["duplicate_refs_json"] = canon_gdf["duplicate_source_refs"].apply(json.dumps)
    
    # Strict 3-way separation of provenance dimensions
    canon_gdf["record_classification"] = "LITERATURE_CURATED_HISTORICAL_RECORD"
    canon_gdf["acquisition_method"] = "MANUAL_RESEARCH_AND_CURATED_EXTRACTION"

    # Define uncertainty band
    def get_uncertainty_band(u: float) -> str:
        if u <= 50.0:
            return "HIGH_PRECISION (≤ 50 m)"
        elif u <= 100.0:
            return "MODERATE_PRECISION (51–100 m)"
        elif u <= 200.0:
            return "VILLAGE_SCALE_PRECISION (101–200 m)"
        else:
            return "CORRIDOR_SCALE_PRECISION (> 200 m)"

    canon_gdf["uncertainty_band"] = canon_gdf["coordinate_uncertainty_m"].apply(get_uncertainty_band)

    ordered_cols = [
        "canonical_incident_id", "source_native_id", "source_provider", "hazard_type", "date", "year",
        "location_name", "latitude", "longitude", "easting_utm44n", "northing_utm44n",
        "coordinate_uncertainty_m", "uncertainty_band", "location_method", "uncertainty_basis",
        "fatalities", "injuries", "households_affected", "damage_description",
        "source_document_title", "source_document_url_or_identifier", "source_page_figure_table",
        "evidence_level", "source_access_status", "record_classification", "acquisition_method", "extraction_method",
        "duplicate_source_count", "duplicate_refs_json", "incident_id", "geometry"
    ]
    canon_gdf = canon_gdf[[c for c in ordered_cols if c in canon_gdf.columns]]
    return canon_gdf


def generate_provenance_audit_table(canon_gdf: gpd.GeoDataFrame):
    log("4. Generating record-level provenance audit table (record_provenance_audit.csv)...")
    
    rows = []
    for idx, r in canon_gdf.iterrows():
        dup_refs = json.loads(r["duplicate_refs_json"])
        dup_ids = [str(d.get("source_provider")) for d in dup_refs]
        dup_str = ", ".join(dup_ids) if dup_ids else "NONE (Unique Record)"
        dedup_status = "MERGED_CROSS_SOURCE_DUPLICATE" if dup_refs else "UNIQUE_RECORD"
        offset_m = dup_refs[0]["spatial_offset_m"] if dup_refs else 0.0

        rows.append({
            "canonical_incident_id": r["canonical_incident_id"],
            "source_native_id": "NULL",
            "hazard_type": r["hazard_type"],
            "event_date": r["date"],
            "event_year": int(r["year"]),
            "location_name": r["location_name"],
            "source_provider": r["source_provider"],
            "deduplication_status": dedup_status,
            "spatial_offset_to_duplicate_m": offset_m,
            "merged_duplicate_source_info": dup_str,
            "record_classification": r["record_classification"],
            "acquisition_method": r["acquisition_method"],
            "extraction_method": r["extraction_method"],
            "source_access_status": r["source_access_status"],
            "evidence_level": r["evidence_level"],
            "latitude_wgs84": round(float(r["latitude"]), 5),
            "longitude_wgs84": round(float(r["longitude"]), 5),
            "easting_utm44n": round(float(r["easting_utm44n"]), 2),
            "northing_utm44n": round(float(r["northing_utm44n"]), 2),
            "location_method": r["location_method"],
            "coordinate_uncertainty_m": float(r["coordinate_uncertainty_m"]),
            "uncertainty_band": r["uncertainty_band"],
            "uncertainty_basis": r["uncertainty_basis"],
            "fatalities_documented": int(r["fatalities"]),
            "injuries_documented": int(r["injuries"]),
            "households_affected": int(r["households_affected"]),
            "source_document_title": r["source_document_title"],
            "source_document_url_or_identifier": r["source_document_url_or_identifier"],
            "source_page_figure_table": r["source_page_figure_table"]
        })

    audit_df = pd.DataFrame(rows)
    audit_df.to_csv(str(OUT_CSV_AUDIT), index=False, encoding="utf-8")
    log(f"   [OUTPUT] Written Provenance Audit Table to {OUT_CSV_AUDIT.relative_to(ROOT)} ({len(audit_df)} records)")


def compute_spatial_exposure(points_gdf: gpd.GeoDataFrame, disaster_gdf: gpd.GeoDataFrame, id_col: str) -> gpd.GeoDataFrame:
    res = points_gdf.copy().reset_index(drop=True)
    if res.crs != TARGET_CRS:
        res = res.to_crs(TARGET_CRS)

    centroids = res.geometry.centroid if res.geometry.iloc[0].geom_type != "Point" else res.geometry
    pts = np.column_stack([centroids.x, centroids.y])

    d_coords = np.column_stack([disaster_gdf.geometry.x, disaster_gdf.geometry.y])
    kdtree_disaster = cKDTree(d_coords)

    near_dists, near_indices = kdtree_disaster.query(pts)
    res["dist_to_nearest_disaster_m"] = np.round(near_dists, 1)
    res["nearest_disaster_id"] = disaster_gdf["canonical_incident_id"].iloc[near_indices].values
    res["nearest_disaster_hazard_type"] = disaster_gdf["hazard_type"].iloc[near_indices].values
    res["nearest_disaster_year"] = disaster_gdf["year"].iloc[near_indices].values.astype(int)

    indices_1km = kdtree_disaster.query_ball_point(pts, r=1000.0)
    indices_2km = kdtree_disaster.query_ball_point(pts, r=2000.0)

    count_1km = [len(idxs) for idxs in indices_1km]
    count_2km = [len(idxs) for idxs in indices_2km]

    mass_movement_types = {"LANDSLIDE", "DEBRIS_FLOW", "ROCKFALL"}
    flood_types = {"CLOUDBURST", "FLASH_FLOOD", "RIVERINE_FLOOD"}

    landslide_count_2km = []
    flood_count_2km = []

    for idxs in indices_2km:
        sub_types = disaster_gdf["hazard_type"].iloc[idxs].values
        ls_c = sum(1 for t in sub_types if t in mass_movement_types)
        fl_c = sum(1 for t in sub_types if t in flood_types)
        landslide_count_2km.append(ls_c)
        flood_count_2km.append(fl_c)

    res["disaster_events_within_1km_count"] = count_1km
    res["disaster_events_within_2km_count"] = count_2km
    res["landslide_events_within_2km_count"] = landslide_count_2km
    res["cloudburst_flood_events_within_2km_count"] = flood_count_2km
    res["has_historical_disaster_1km_flag"] = [c > 0 for c in count_1km]
    res["chronic_disaster_exposure_2km_flag"] = [c >= 2 for c in count_2km]
    res["disaster_history_status"] = "HISTORICAL_RECORDS_INGESTED"

    return res


def run_pipeline():
    print("=" * 76)
    print("  SIH26191: Phase 3 Historical Disaster Ingestion & Exposure Alignment")
    print("=" * 76)

    raw_records = load_raw_datasets()
    canonical_records, dedup_log = deduplicate_records(raw_records)
    disaster_gdf = build_canonical_geodataframe(canonical_records)

    # 4. Generate Provenance Audit Table
    generate_provenance_audit_table(disaster_gdf)

    # 5. Spatial Exposure Attribution on Habitations & Candidates
    log("5. Computing spatial proximity & analytical exposure buffers (1 km, 2 km)...")
    
    if HAB_PATH.exists():
        log(f"   Evaluating exposure for 653 habitations from {HAB_PATH.name}...")
        hab_gdf = gpd.read_file(str(HAB_PATH))
        hab_enriched = compute_spatial_exposure(hab_gdf, disaster_gdf, "village_id")
        hab_enriched.to_file(str(HAB_PATH), driver="GeoJSON")
        log(f"   [SUCCESS] Updated {HAB_PATH.name} with historical disaster exposure attributes.")

    if CAND_PATH.exists():
        log(f"   Evaluating exposure for {len(gpd.read_file(str(CAND_PATH))):,} candidate areas from {CAND_PATH.name}...")
        cand_gdf = gpd.read_file(str(CAND_PATH))
        cand_enriched = compute_spatial_exposure(cand_gdf, disaster_gdf, "area_id")
        cand_enriched.to_file(str(CAND_PATH), driver="GeoJSON")
        log(f"   [SUCCESS] Updated {CAND_PATH.name} with historical disaster exposure attributes.")

    # 6. Export Processed Inventory Files
    log("6. Exporting processed canonical disaster inventory...")
    disaster_gdf.to_file(str(OUT_GPKG), layer="historical_disasters", driver="GPKG")
    log(f"   [OUTPUT] Written GeoPackage to {OUT_GPKG.relative_to(ROOT)} ({OUT_GPKG.stat().st_size / 1024:.1f} KB)")

    disaster_wgs84 = disaster_gdf.to_crs(SOURCE_CRS)
    disaster_wgs84.to_file(str(OUT_GEOJSON), driver="GeoJSON")
    log(f"   [OUTPUT] Written GeoJSON to {OUT_GEOJSON.relative_to(ROOT)} ({OUT_GEOJSON.stat().st_size / 1024:.1f} KB)")

    # 7. Generate Summary Breakdown
    source_access_counts = {str(k): int(v) for k, v in disaster_gdf["source_access_status"].value_counts().items()}
    acq_method_counts = {str(k): int(v) for k, v in disaster_gdf["acquisition_method"].value_counts().items()}
    extraction_counts = {str(k): int(v) for k, v in disaster_gdf["extraction_method"].value_counts().items()}
    evidence_counts = {str(k): int(v) for k, v in disaster_gdf["evidence_level"].value_counts().items()}
    uncertainty_counts = {str(k): int(v) for k, v in disaster_gdf["uncertainty_band"].value_counts().items()}
    provider_counts = {str(k): int(v) for k, v in disaster_gdf["source_provider"].value_counts().items()}
    type_counts = {str(k): int(v) for k, v in disaster_gdf["hazard_type"].value_counts().items()}
    year_counts = {str(k): int(v) for k, v in disaster_gdf["year"].value_counts().sort_index().items()}
    total_fatalities = int(disaster_gdf["fatalities"].sum())

    summary = {
        "project": "SIH26191",
        "pipeline_phase": "Phase 3: Historical Disaster Ingestion & Multi-Year Landslide Inventory Alignment",
        "record_classification": "LITERATURE_CURATED_HISTORICAL_RECORD",
        "acquisition_method": "MANUAL_RESEARCH_AND_CURATED_EXTRACTION",
        "processed_timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "crs": TARGET_CRS,
        "total_canonical_events": len(disaster_gdf),
        "total_fatalities_recorded": total_fatalities,
        "total_households_affected": int(disaster_gdf["households_affected"].sum()),
        "temporal_range": [int(disaster_gdf["year"].min()), int(disaster_gdf["year"].max())],
        "hazard_type_breakdown": type_counts,
        "source_access_status_breakdown": source_access_counts,
        "acquisition_method_breakdown": acq_method_counts,
        "extraction_method_breakdown": extraction_counts,
        "source_native_id_status": {
            "verified_native_ids_count": 0,
            "null_unassigned_ids_count": len(disaster_gdf)
        },
        "evidence_level_breakdown": evidence_counts,
        "coordinate_uncertainty_breakdown": uncertainty_counts,
        "source_provider_breakdown": provider_counts,
        "annual_event_distribution": year_counts,
        "deduplication_summary": {
            "raw_records_ingested": len(raw_records),
            "duplicate_pairs_merged": len(dedup_log),
            "canonical_events_retained": len(disaster_gdf),
            "dedup_log": dedup_log
        },
        "habitation_exposure_summary": {
            "total_habitations": len(hab_enriched) if 'hab_enriched' in locals() else 0,
            "habitations_within_1km_count": int((hab_enriched["disaster_events_within_1km_count"] > 0).sum()) if 'hab_enriched' in locals() else 0,
            "habitations_within_2km_count": int((hab_enriched["disaster_events_within_2km_count"] > 0).sum()) if 'hab_enriched' in locals() else 0,
            "chronic_exposure_habitations_count": int(hab_enriched["chronic_disaster_exposure_2km_flag"].sum()) if 'hab_enriched' in locals() else 0,
            "mean_dist_to_nearest_disaster_m": round(float(hab_enriched["dist_to_nearest_disaster_m"].mean()), 1) if 'hab_enriched' in locals() else 0
        },
        "candidate_area_exposure_summary": {
            "total_candidate_areas": len(cand_enriched) if 'cand_enriched' in locals() else 0,
            "candidates_within_1km_count": int((cand_enriched["disaster_events_within_1km_count"] > 0).sum()) if 'cand_enriched' in locals() else 0,
            "candidates_within_2km_count": int((cand_enriched["disaster_events_within_2km_count"] > 0).sum()) if 'cand_enriched' in locals() else 0,
            "chronic_exposure_candidates_count": int(cand_enriched["chronic_disaster_exposure_2km_flag"].sum()) if 'cand_enriched' in locals() else 0,
            "mean_dist_to_nearest_disaster_m": round(float(cand_enriched["dist_to_nearest_disaster_m"].mean()), 1) if 'cand_enriched' in locals() else 0
        },
        "methodological_disclaimer": (
            "CONTEXTUAL DISASTER HISTORY INFORMATION ONLY. Historical event counts and 1km/2km buffers "
            "are analytical exposure perimeters to provide situational context for planners. They do not alter "
            "the core deterministic hazard classification rules without official administrative review."
        )
    }

    with open(OUT_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    log(f"[OUTPUT] Written Disaster Summary to {OUT_SUMMARY.relative_to(ROOT)} (Total Fatalities: {total_fatalities:,})")
    print("\n[SUCCESS] Phase 3 Historical Disaster Ingestion Complete.")


if __name__ == "__main__":
    run_pipeline()
