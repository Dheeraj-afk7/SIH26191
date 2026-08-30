#!/usr/bin/env python3
"""
SIH26191 -- Phase 4 Critical Infrastructure Validation Suite
============================================================

Automated validation suite verifying:
1. Raw OSM infrastructure file presence, schema conformity, and provenance metadata.
2. Canonical facility inventory geometries, metric CRS (EPSG:32644), spatial bounds, and non-null constraints.
3. Category segregation (Hospitals vs CHCs vs PHCs vs Subcentres vs Schools vs Police vs Fire).
4. Emergency capability bounds (verified clinical/emergency tiers only; no name-only inference).
5. Segregation of Education accessibility from Healthcare/Emergency accessibility.
6. Graph network routing integration via Phase 2 road graph.
7. Habitation (653) and Candidate Area (2,998) accessibility enrichment.
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

RAW_JSON = ROOT / "data" / "raw" / "infrastructure" / "osm_critical_infrastructure_raw.json"
RAW_PROVENANCE = ROOT / "data" / "raw" / "infrastructure" / "provenance_metadata.json"

PROC_GPKG = ROOT / "data" / "processed" / "infrastructure" / "critical_infrastructure.gpkg"
PROC_GEOJSON = ROOT / "data" / "processed" / "infrastructure" / "critical_infrastructure.geojson"
PROC_CSV_AUDIT = ROOT / "data" / "processed" / "infrastructure" / "facility_provenance_audit.csv"
PROC_SUMMARY = ROOT / "data" / "processed" / "infrastructure" / "infrastructure_summary.json"

HAB_PATH = ROOT / "data" / "processed" / "exposure" / "habitation_exposure.geojson"
CAND_PATH = ROOT / "data" / "outputs" / "candidate_topographically_feasible_areas_attributed.geojson"

AOI_BBOX_WGS84 = [78.70, 30.10, 79.50, 30.90]


class InfrastructureValidationRunner:
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
        print(f"  {status_str} {name:<50} | {details}")

    def run_all_checks(self):
        print("=" * 80)
        print("  SIH26191 -- Phase 4 Critical Infrastructure Validation Suite")
        print(f"  Generated: {datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
        print("=" * 80)

        # 1. FILE EXISTENCE & PROVENANCE ARTIFACTS
        print("\n" + "=" * 80)
        print("  1. FILE EXISTENCE & PROVENANCE ARTIFACTS")
        print("=" * 80)
        self.check("file.raw_osm_json", RAW_JSON.exists(), f"{RAW_JSON.relative_to(ROOT)} ({RAW_JSON.stat().st_size / 1024:.1f} KB)" if RAW_JSON.exists() else "Missing")
        self.check("file.raw_provenance_json", RAW_PROVENANCE.exists(), f"{RAW_PROVENANCE.relative_to(ROOT)} ({RAW_PROVENANCE.stat().st_size / 1024:.1f} KB)" if RAW_PROVENANCE.exists() else "Missing")
        self.check("file.proc_gpkg", PROC_GPKG.exists(), f"{PROC_GPKG.relative_to(ROOT)} ({PROC_GPKG.stat().st_size / 1024:.1f} KB)" if PROC_GPKG.exists() else "Missing")
        self.check("file.proc_geojson", PROC_GEOJSON.exists(), f"{PROC_GEOJSON.relative_to(ROOT)} ({PROC_GEOJSON.stat().st_size / 1024:.1f} KB)" if PROC_GEOJSON.exists() else "Missing")
        self.check("file.proc_csv_audit", PROC_CSV_AUDIT.exists(), f"{PROC_CSV_AUDIT.relative_to(ROOT)} ({PROC_CSV_AUDIT.stat().st_size / 1024:.1f} KB)" if PROC_CSV_AUDIT.exists() else "Missing")
        self.check("file.proc_summary_json", PROC_SUMMARY.exists(), f"{PROC_SUMMARY.relative_to(ROOT)} ({PROC_SUMMARY.stat().st_size / 1024:.1f} KB)" if PROC_SUMMARY.exists() else "Missing")

        if not PROC_GPKG.exists() or not PROC_GEOJSON.exists() or not PROC_CSV_AUDIT.exists():
            print("\n[FATAL] Required processed infrastructure files missing. Aborting further checks.")
            return

        # 2. FACILITY INVENTORY GEOMETRY & BOUNDS
        print("\n" + "=" * 80)
        print("  2. FACILITY INVENTORY GEOMETRY & SPATIAL BOUNDS CHECK")
        print("=" * 80)
        gdf = gpd.read_file(str(PROC_GPKG))
        gdf_wgs84 = gpd.read_file(str(PROC_GEOJSON))

        self.check("facility.record_count", len(gdf) >= 250, f"{len(gdf)} critical facilities ingested")
        self.check("facility.crs_gpkg", gdf.crs.to_string() == "EPSG:32644", f"CRS: {gdf.crs}")
        self.check("facility.crs_geojson", gdf_wgs84.crs.to_string() == "EPSG:4326", f"CRS: {gdf_wgs84.crs}")
        self.check("facility.geom_all_points", all(gdf.geometry.geom_type == "Point"), "All geometries are Point features")
        self.check("facility.geom_all_valid", all(gdf.geometry.is_valid), "All geometries valid")

        # Bounds check
        minx, miny, maxx, maxy = gdf_wgs84.total_bounds
        in_bounds = (
            minx >= AOI_BBOX_WGS84[0] and miny >= AOI_BBOX_WGS84[1] and
            maxx <= AOI_BBOX_WGS84[2] and maxy <= AOI_BBOX_WGS84[3]
        )
        self.check("facility.spatial_within_aoi", in_bounds, f"BBox: [{minx:.4f}E, {miny:.4f}N] to [{maxx:.4f}E, {maxy:.4f}N]")

        # Unique IDs
        self.check("facility.id_unique", gdf["facility_id"].nunique() == len(gdf), f"{gdf['facility_id'].nunique()} unique IDs")
        self.check("facility.id_format", all(gdf["facility_id"].str.match(r"^FAC-RDP-\d{3}$")), "All follow FAC-RDP-NNN format")
        self.check("facility.osm_id_preserved", (gdf["osm_id"].str.len() > 3).all(), "Original OSM IDs preserved")
        self.check("facility.no_null_coordinates", not gdf.geometry.is_empty.any(), "0 null/empty coordinates")

        # 3. FACILITY CATEGORIZATION & SEPARATION
        print("\n" + "=" * 80)
        print("  3. FACILITY CATEGORIZATION & HEALTH/EDUCATION SEGREGATION")
        print("=" * 80)
        broad_types = set(gdf["facility_broad_type"].unique())
        self.check("category.broad_types_present", {"HEALTHCARE", "EDUCATION", "EMERGENCY", "CIVIC_ADMINISTRATIVE"}.issubset(broad_types), f"Broad types: {sorted(list(broad_types))}")

        # Healthcare breakdown
        hc_cats = set(gdf[gdf["facility_broad_type"] == "HEALTHCARE"]["facility_category"].unique())
        self.check("healthcare.categories_distinct", {"HEALTHCARE_HOSPITAL", "HEALTHCARE_CHC", "HEALTHCARE_PHC", "HEALTHCARE_SUBCENTRE"}.issubset(hc_cats), f"Healthcare categories: {sorted(list(hc_cats))}")

        # Education breakdown
        edu_cats = set(gdf[gdf["facility_broad_type"] == "EDUCATION"]["facility_category"].unique())
        self.check("education.categories_distinct", {"EDUCATION_SCHOOL", "EDUCATION_HIGHER"}.issubset(edu_cats), f"Education categories: {sorted(list(edu_cats))}")

        # Emergency capability semantics
        evidenced_count = int(gdf["explicitly_evidenced_emergency_capability"].sum())
        potential_count = int(gdf["potential_emergency_receiving_facility"].sum())
        self.check("emergency.explicitly_evidenced", evidenced_count == 4, f"{evidenced_count} explicitly evidenced emergency facilities (3 Police, 1 Fire Station, 0 hospitals with emergency=yes tag)")
        self.check("emergency.potential_clinical_receivers", potential_count == 42, f"{potential_count} potential emergency receiving facilities (24 Hospitals, 6 CHCs, 12 PHCs based on administrative tier)")

        # Classification triggers
        self.check("classification.triggers_present", "classification_trigger" in gdf.columns, "classification_trigger column present")

        # 4. RECORD-LEVEL AUDIT CSV CHECK
        print("\n" + "=" * 80)
        print("  4. RECORD-LEVEL FACILITY PROVENANCE AUDIT CHECK")
        print("=" * 80)
        audit_df = pd.read_csv(str(PROC_CSV_AUDIT))
        self.check("audit_csv.row_count_matches", len(audit_df) == len(gdf), f"{len(audit_df)} audit rows")
        self.check("audit_csv.source_provider_osm", (audit_df["source_provider"] == "OpenStreetMap Contributors").all(), "100% OpenStreetMap Contributors")
        self.check("audit_csv.osm_id_present", (audit_df["osm_id"].str.len() > 3).all(), "All records have valid OSM element IDs")
        self.check("audit_csv.explicit_emergency_col", "explicitly_evidenced_emergency_capability" in audit_df.columns, "explicitly_evidenced_emergency_capability in audit CSV")
        self.check("audit_csv.potential_emergency_col", "potential_emergency_receiving_facility" in audit_df.columns, "potential_emergency_receiving_facility in audit CSV")

        # 5. HABITATION ACCESSIBILITY ENRICHMENT CHECK (N = 653)
        print("\n" + "=" * 80)
        print("  5. HABITATION ACCESSIBILITY ENRICHMENT CHECK (N = 653)")
        print("=" * 80)
        hab_gdf = gpd.read_file(str(HAB_PATH))
        self.check("habitations.feature_count", len(hab_gdf) == 653, "653 habitations present")

        hab_req_fields = [
            "dist_to_nearest_health_facility_m", "nearest_health_facility_id", "nearest_health_facility_category",
            "dist_to_nearest_hospital_chc_m", "nearest_hospital_chc_id", "nearest_hospital_chc_name",
            "dist_to_nearest_phc_m", "nearest_phc_id", "nearest_phc_name",
            "dist_to_nearest_school_m", "nearest_school_id", "nearest_school_name",
            "dist_to_nearest_emergency_service_m", "nearest_emergency_service_id",
            "network_dist_to_health_facility_m", "network_time_to_health_facility_min", "health_facility_route_exists",
            "network_dist_to_hospital_chc_m", "network_time_to_hospital_chc_min", "hospital_chc_route_exists",
            "network_dist_to_school_m", "network_time_to_school_min", "school_route_exists",
            "has_health_within_5km_flag", "has_school_within_3km_flag", "hospital_chc_access_under_60min_flag",
            "infrastructure_status"
        ]
        for fld in hab_req_fields:
            self.check(f"habitations.field.{fld}", fld in hab_gdf.columns, "present")

        self.check("habitations.dist_health_no_nulls", hab_gdf["dist_to_nearest_health_facility_m"].isna().sum() == 0, "0 null distances")
        self.check("habitations.dist_school_no_nulls", hab_gdf["dist_to_nearest_school_m"].isna().sum() == 0, "0 null distances")
        self.check("habitations.mean_dist_health", hab_gdf["dist_to_nearest_health_facility_m"].mean() > 0, f"Mean health distance: {hab_gdf['dist_to_nearest_health_facility_m'].mean():.1f} m")
        self.check("habitations.mean_dist_school", hab_gdf["dist_to_nearest_school_m"].mean() > 0, f"Mean school distance: {hab_gdf['dist_to_nearest_school_m'].mean():.1f} m")

        # 6. CANDIDATE AREA ACCESSIBILITY ENRICHMENT CHECK (N = 2,998)
        print("\n" + "=" * 80)
        print("  6. CANDIDATE AREA ACCESSIBILITY ENRICHMENT CHECK (N = 2,998)")
        print("=" * 80)
        cand_gdf = gpd.read_file(str(CAND_PATH))
        self.check("candidate_areas.feature_count", len(cand_gdf) == 2998, "2,998 candidate areas present")

        cand_req_fields = [
            "dist_to_nearest_health_facility_m", "nearest_health_facility_id",
            "dist_to_nearest_hospital_chc_m", "nearest_hospital_chc_id",
            "dist_to_nearest_school_m", "nearest_school_id",
            "network_dist_to_health_facility_m", "network_time_to_health_facility_min", "health_facility_route_exists",
            "network_dist_to_hospital_chc_m", "network_time_to_hospital_chc_min", "hospital_chc_route_exists",
            "network_dist_to_school_m", "network_time_to_school_min", "school_route_exists",
            "has_health_within_5km_flag", "has_school_within_3km_flag", "hospital_chc_access_under_60min_flag",
            "infrastructure_status"
        ]
        for fld in cand_req_fields:
            self.check(f"candidate_areas.field.{fld}", fld in cand_gdf.columns, "present")

        self.check("candidate_areas.dist_health_no_nulls", cand_gdf["dist_to_nearest_health_facility_m"].isna().sum() == 0, "0 null distances")
        self.check("candidate_areas.dist_school_no_nulls", cand_gdf["dist_to_nearest_school_m"].isna().sum() == 0, "0 null distances")

        # SUMMARY
        print("\n" + "=" * 80)
        print("  VALIDATION SUMMARY")
        print("=" * 80)
        print(f"  Total checks : {self.passes + self.fails + self.warnings}")
        print(f"  PASS         : {self.passes}")
        print(f"  FAIL         : {self.fails}")
        print(f"  WARN         : {self.warnings}")
        print(f"\n  OVERALL STATUS: {'PASS' if self.fails == 0 else 'FAIL'}")


def main():
    runner = InfrastructureValidationRunner()
    runner.run_all_checks()
    return 0 if runner.fails == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
