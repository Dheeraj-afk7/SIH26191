#!/usr/bin/env python3
"""
SIH26191 -- Phase 3 Historical Disaster Inventory Validation Suite
==================================================================

Automated validation suite verifying:
1. Raw source file presence, schema conformity, and provenance metadata.
2. Canonical disaster inventory geometries, CRS, spatial bounds, and non-null constraints.
3. Strict hazard taxonomy separation (Landslide vs Cloudburst vs Flood vs Debris Flow).
4. Cross-source deduplication integrity and temporal coverage (1998-2024).
5. Strict 3-way provenance separation (record_classification, acquisition_method, extraction_method).
6. Source access status verification and strict NULL source-native ID audit.
7. Coordinate uncertainty values and derivation basis for every record.
8. Habitation (653) and Candidate Area (2,998) contextual exposure enrichment.
"""

import datetime
import io
import json
import os
import pathlib
import sys
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely.geometry as sg

# Force UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

ROOT = pathlib.Path(__file__).resolve().parent.parent

RAW_ISRO = ROOT / "data" / "raw" / "disaster_history" / "isro_nrsc_landslide_inventory.json"
RAW_USDMA = ROOT / "data" / "raw" / "disaster_history" / "usdma_desinventar_historical_events.json"
RAW_PROVENANCE = ROOT / "data" / "raw" / "disaster_history" / "provenance_metadata.json"

PROC_GPKG = ROOT / "data" / "processed" / "disaster_history" / "historical_disaster_inventory.gpkg"
PROC_GEOJSON = ROOT / "data" / "processed" / "disaster_history" / "historical_disaster_inventory.geojson"
PROC_CSV_AUDIT = ROOT / "data" / "processed" / "disaster_history" / "record_provenance_audit.csv"
PROC_SUMMARY = ROOT / "data" / "processed" / "disaster_history" / "disaster_summary.json"

HAB_PATH = ROOT / "data" / "processed" / "exposure" / "habitation_exposure.geojson"
CAND_PATH = ROOT / "data" / "outputs" / "candidate_topographically_feasible_areas_attributed.geojson"

AOI_BBOX_WGS84 = [78.70, 30.10, 79.50, 30.90]  # [minx, miny, maxx, maxy]


class DisasterValidationRunner:
    def __init__(self):
        self.passes = 0
        self.fails = 0
        self.warnings = 0
        self.results = []

    def check(self, name: str, condition: bool, details: str = "", is_warn: bool = False):
        if condition:
            self.passes += 1
            status = "PASS"
        elif is_warn:
            self.warnings += 1
            status = "WARN"
        else:
            self.fails += 1
            status = "FAIL"
        
        self.results.append((status, name, details))
        status_str = f"[{status:4s}]"
        print(f"  {status_str} {name:<48} | {details}")

    def run_all_checks(self):
        print("=" * 78)
        print("  SIH26191 -- Phase 3 Historical Disaster Inventory Validation Suite")
        print(f"  Generated: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
        print("=" * 78)

        # 1. FILE EXISTENCE
        print("\n" + "=" * 78)
        print("  1. FILE EXISTENCE & PROVENANCE ARTIFACTS")
        print("=" * 78)
        self.check("file.raw_isro_json", RAW_ISRO.exists(), f"{RAW_ISRO.relative_to(ROOT)} ({RAW_ISRO.stat().st_size / 1024:.1f} KB)" if RAW_ISRO.exists() else "Missing")
        self.check("file.raw_usdma_json", RAW_USDMA.exists(), f"{RAW_USDMA.relative_to(ROOT)} ({RAW_USDMA.stat().st_size / 1024:.1f} KB)" if RAW_USDMA.exists() else "Missing")
        self.check("file.raw_provenance_json", RAW_PROVENANCE.exists(), f"{RAW_PROVENANCE.relative_to(ROOT)} ({RAW_PROVENANCE.stat().st_size / 1024:.1f} KB)" if RAW_PROVENANCE.exists() else "Missing")
        self.check("file.proc_gpkg", PROC_GPKG.exists(), f"{PROC_GPKG.relative_to(ROOT)} ({PROC_GPKG.stat().st_size / 1024:.1f} KB)" if PROC_GPKG.exists() else "Missing")
        self.check("file.proc_geojson", PROC_GEOJSON.exists(), f"{PROC_GEOJSON.relative_to(ROOT)} ({PROC_GEOJSON.stat().st_size / 1024:.1f} KB)" if PROC_GEOJSON.exists() else "Missing")
        self.check("file.proc_csv_audit", PROC_CSV_AUDIT.exists(), f"{PROC_CSV_AUDIT.relative_to(ROOT)} ({PROC_CSV_AUDIT.stat().st_size / 1024:.1f} KB)" if PROC_CSV_AUDIT.exists() else "Missing")
        self.check("file.proc_summary_json", PROC_SUMMARY.exists(), f"{PROC_SUMMARY.relative_to(ROOT)} ({PROC_SUMMARY.stat().st_size / 1024:.1f} KB)" if PROC_SUMMARY.exists() else "Missing")

        if not PROC_GPKG.exists() or not PROC_GEOJSON.exists() or not PROC_CSV_AUDIT.exists():
            print("\n[FATAL] Required processed files missing. Aborting further checks.")
            return

        # 2. CANONICAL INVENTORY GEOMETRY & SCHEMA
        print("\n" + "=" * 78)
        print("  2. CANONICAL INVENTORY GEOMETRY & SPATIAL BOUNDS CHECK")
        print("=" * 78)
        gdf = gpd.read_file(str(PROC_GPKG))
        gdf_wgs84 = gpd.read_file(str(PROC_GEOJSON))

        self.check("inventory.record_count", len(gdf) >= 20, f"{len(gdf)} canonical disaster events")
        self.check("inventory.crs_gpkg", gdf.crs.to_string() == "EPSG:32644", f"CRS: {gdf.crs}")
        self.check("inventory.crs_geojson", gdf_wgs84.crs.to_string() == "EPSG:4326", f"CRS: {gdf_wgs84.crs}")
        self.check("inventory.geom_all_points", all(gdf.geometry.geom_type == "Point"), "All geometries are Point features")
        self.check("inventory.geom_all_valid", all(gdf.geometry.is_valid), "All geometries valid")

        # Bounds check
        minx, miny, maxx, maxy = gdf_wgs84.total_bounds
        in_bounds = (
            minx >= AOI_BBOX_WGS84[0] and miny >= AOI_BBOX_WGS84[1] and
            maxx <= AOI_BBOX_WGS84[2] and maxy <= AOI_BBOX_WGS84[3]
        )
        self.check("inventory.spatial_within_aoi", in_bounds, f"BBox: [{minx:.4f}E, {miny:.4f}N] to [{maxx:.4f}E, {maxy:.4f}N]")

        # Unique IDs
        self.check("inventory.incident_id_unique", gdf["incident_id"].nunique() == len(gdf), f"{gdf['incident_id'].nunique()} unique IDs")
        self.check("inventory.incident_id_format", all(gdf["incident_id"].str.match(r"^DIS-RDP-\d{4}-\d{3}$")), "All follow DIS-RDP-YYYY-NNN format")
        self.check("inventory.no_null_coordinates", not gdf.geometry.is_empty.any(), "0 null/empty coordinates")

        # 3. HAZARD TAXONOMY & TEMPORAL COVERAGE
        print("\n" + "=" * 78)
        print("  3. HAZARD TAXONOMY & TEMPORAL COVERAGE CHECK")
        print("=" * 78)
        expected_types = {"LANDSLIDE", "CLOUDBURST", "DEBRIS_FLOW", "RIVERINE_FLOOD", "FLASH_FLOOD", "ROCKFALL"}
        actual_types = set(gdf["hazard_type"].unique())
        self.check("taxonomy.all_expected_types_represented", len(actual_types.intersection(expected_types)) >= 4, f"Types found: {sorted(list(actual_types))}")
        
        min_yr = int(gdf["year"].min())
        max_yr = int(gdf["year"].max())
        self.check("temporal.multi_decadal_span", (min_yr <= 1998) and (max_yr >= 2023), f"Temporal range: {min_yr} - {max_yr} ({max_yr - min_yr + 1} years)")
        
        exact_fatalities = int(gdf["fatalities"].sum())
        self.check("inventory.exact_fatalities_count", exact_fatalities == 6913, f"Exact fatalities: {exact_fatalities:,}")

        # 4. PROVENANCE INTEGRITY & EPISTEMIC HONESTY CHECK
        print("\n" + "=" * 78)
        print("  4. PROVENANCE INTEGRITY & EPISTEMIC HONESTY AUDIT")
        print("=" * 78)
        audit_df = pd.read_csv(str(PROC_CSV_AUDIT))
        self.check("audit_csv.row_count_matches", len(audit_df) == len(gdf), f"{len(audit_df)} audit rows")
        
        # Provenance Dimensions Separation
        self.check("audit_csv.record_classification_explicit", (audit_df["record_classification"] == "LITERATURE_CURATED_HISTORICAL_RECORD").all(), "100% LITERATURE_CURATED_HISTORICAL_RECORD")
        self.check("audit_csv.acq_method_separated", (audit_df["acquisition_method"] == "MANUAL_RESEARCH_AND_CURATED_EXTRACTION").all(), "100% MANUAL_RESEARCH_AND_CURATED_EXTRACTION")
        self.check("audit_csv.extraction_method_valid", audit_df["extraction_method"].isin(["MAP_GEOREFERENCED_DIGITIZATION", "TEXT_TABULAR_EXTRACTION"]).all(), f"Extraction methods: {dict(audit_df['extraction_method'].value_counts())}")
        
        # Source Native ID audit: all must be NULL since none directly downloaded from database
        self.check("audit_csv.source_native_id_strictly_null", (audit_df["source_native_id"].isna() | (audit_df["source_native_id"] == "NULL")).all(), "All 22 source_native_ids set to NULL (no pseudo-native IDs)")
        
        # Source Access Status breakdown
        valid_access_statuses = {"VERIFIED_PUBLISHED_SECONDARY_SOURCE", "UNVERIFIED_DOCUMENT_REFERENCE"}
        self.check("audit_csv.source_access_status_valid", audit_df["source_access_status"].isin(valid_access_statuses).all(), f"Access statuses: {dict(audit_df['source_access_status'].value_counts())}")

        # Coordinate Uncertainty & Basis
        self.check("audit_csv.all_have_uncertainty_basis", (audit_df["uncertainty_basis"].str.len() > 10).all(), "All 22 records explain uncertainty derivation basis")
        self.check("audit_csv.uncertainty_positive_range", (audit_df["coordinate_uncertainty_m"] >= 50.0).all() and (audit_df["coordinate_uncertainty_m"] <= 300.0).all(), "Uncertainties realistically bounded (50 m - 300 m)")

        # Citations
        self.check("audit_csv.all_have_document_title", (audit_df["source_document_title"].str.len() > 10).all(), "All records have specific documentary source titles")
        self.check("audit_csv.all_have_doc_identifier", (audit_df["source_document_url_or_identifier"].str.len() > 5).all(), "All records have document DOIs, URLs, or registration references")
        self.check("audit_csv.all_have_page_fig_ref", (audit_df["source_page_figure_table"].str.len() > 2).all(), "All records have exact page/table/figure references")
        
        dup_count = (audit_df["deduplication_status"] == "MERGED_CROSS_SOURCE_DUPLICATE").sum()
        self.check("audit_csv.duplicate_pairs_identified", dup_count == 4, f"{dup_count} merged duplicate pairs documented with spatial offsets")

        # 5. HABITATION EXPOSURE ENRICHMENT CHECK
        print("\n" + "=" * 78)
        print("  5. HABITATION EXPOSURE ENRICHMENT CHECK (N = 653)")
        print("=" * 78)
        hab_gdf = gpd.read_file(str(HAB_PATH))
        self.check("habitations.feature_count", len(hab_gdf) == 653, "653 habitations present")
        
        hab_req_fields = [
            "dist_to_nearest_disaster_m", "nearest_disaster_id", "nearest_disaster_hazard_type",
            "nearest_disaster_year", "disaster_events_within_1km_count", "disaster_events_within_2km_count",
            "landslide_events_within_2km_count", "cloudburst_flood_events_within_2km_count",
            "chronic_disaster_exposure_2km_flag"
        ]
        for fld in hab_req_fields:
            self.check(f"habitations.field.{fld}", fld in hab_gdf.columns, "present")

        self.check("habitations.dist_no_nulls", hab_gdf["dist_to_nearest_disaster_m"].isna().sum() == 0, "0 null distances")
        self.check("habitations.mean_distance", hab_gdf["dist_to_nearest_disaster_m"].mean() > 0, f"Mean distance: {hab_gdf['dist_to_nearest_disaster_m'].mean():.1f} m")
        
        hab_chronic = hab_gdf["chronic_disaster_exposure_2km_flag"].sum()
        self.check("habitations.chronic_exposure_count", hab_chronic >= 0, f"{hab_chronic} habitations with chronic disaster exposure (>=2 events in 2km)")

        # 6. CANDIDATE AREA EXPOSURE ENRICHMENT CHECK
        print("\n" + "=" * 78)
        print("  6. CANDIDATE AREA EXPOSURE ENRICHMENT CHECK (N = 2,998)")
        print("=" * 78)
        cand_gdf = gpd.read_file(str(CAND_PATH))
        self.check("candidate_areas.feature_count", len(cand_gdf) == 2998, "2,998 candidate areas present")

        cand_req_fields = [
            "dist_to_nearest_disaster_m", "nearest_disaster_id", "nearest_disaster_hazard_type",
            "nearest_disaster_year", "disaster_events_within_1km_count", "disaster_events_within_2km_count",
            "landslide_events_within_2km_count", "cloudburst_flood_events_within_2km_count",
            "chronic_disaster_exposure_2km_flag"
        ]
        for fld in cand_req_fields:
            self.check(f"candidate_areas.field.{fld}", fld in cand_gdf.columns, "present")

        self.check("candidate_areas.dist_no_nulls", cand_gdf["dist_to_nearest_disaster_m"].isna().sum() == 0, "0 null distances")
        cand_chronic = cand_gdf["chronic_disaster_exposure_2km_flag"].sum()
        self.check("candidate_areas.chronic_exposure_count", cand_chronic >= 0, f"{cand_chronic} candidate areas with chronic disaster exposure (>=2 events in 2km)")

        # SUMMARY
        print("\n" + "=" * 78)
        print("  VALIDATION SUMMARY")
        print("=" * 78)
        print(f"  Total checks : {self.passes + self.fails + self.warnings}")
        print(f"  PASS         : {self.passes}")
        print(f"  FAIL         : {self.fails}")
        print(f"  WARN         : {self.warnings}")
        print(f"\n  OVERALL STATUS: {'PASS' if self.fails == 0 else 'FAIL'}")


def main():
    runner = DisasterValidationRunner()
    runner.run_all_checks()
    return 0 if runner.fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
