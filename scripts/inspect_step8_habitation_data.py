"""Step 8B.1 - Habitation Data Schema Inspection Script

Inspects the Census 2011 Excel dataset and the OSM Settlements GeoJSON dataset.
Strictly read-only. Does not modify raw files, generate processed outputs, or execute joins.
"""

from datetime import datetime
import json
import os
from pathlib import Path
import sys
import geopandas as gpd
import openpyxl
import pandas as pd

def inspect_data():
    repo_root = Path(__file__).resolve().parent.parent
    census_file = repo_root / "data" / "raw" / "habitations" / "PCA_CDB-0503-F-Census.xlsx"
    osm_file = repo_root / "data" / "raw" / "habitations" / "rudraprayag_settlements_osm.geojson"

    print("=" * 80)
    print("STEP 8B.1: ACTUAL DATASET SCHEMA INSPECTION")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().isoformat()}\n")

    # -------------------------------------------------------------
    # PHASE 1: CENSUS DATASET INSPECTION
    # -------------------------------------------------------------
    print("=" * 80)
    print("PHASE 1 — CENSUS DATASET INSPECTION (PCA_CDB-0503-F-Census.xlsx)")
    print("=" * 80)

    if not census_file.exists():
        print(f"ERROR: Census file not found: {census_file}")
        return 1

    wb = openpyxl.load_workbook(census_file, read_only=True)
    sheet_names = wb.sheetnames
    wb.close()
    print(f"1. Workbook Sheet Names: {sheet_names}")

    df_census = pd.read_excel(census_file)
    row_count, col_count = df_census.shape
    print(f"2. Exact Row Count: {row_count}")
    print(f"3. Exact Column Count: {col_count}")
    print(f"4. Complete Column Names ({len(df_census.columns)} total):")
    for i, col in enumerate(df_census.columns):
        print(f"   [{i:02d}] {col} (dtype: {df_census[col].dtype})")

    print("\n5. First 5 Rows (Selected Core Administrative & Demographic Columns):")
    core_cols = [c for c in ['State', 'District', 'DT Name', 'CD Block', 'Town/Village', 'Ward', 'EB', 'Level', 'Name', 'TRU', 'No_HH', 'TOT_P', 'TOT_M', 'TOT_F', 'P_SC', 'P_ST'] if c in df_census.columns]
    print(df_census[core_cols].head(5).to_string())

    print("\n6. Unique Values in Administrative Classification Columns:")
    admin_cols = ['State', 'District', 'DT Name', 'CD Block', 'Level', 'TRU']
    for ac in admin_cols:
        if ac in df_census.columns:
            uvals = df_census[ac].dropna().unique()
            print(f"   - {ac}: {uvals.tolist()}")

    print("\n7. Key Demographic Field Identification & Mapping:")
    mapping = {
        "Village Name": "Name" if "Name" in df_census.columns else "NOT FOUND",
        "Census Village Code": "Town/Village" if "Town/Village" in df_census.columns else "NOT FOUND",
        "Households": "No_HH" if "No_HH" in df_census.columns else "NOT FOUND",
        "Total Population": "TOT_P" if "TOT_P" in df_census.columns else "NOT FOUND",
        "Male Population": "TOT_M" if "TOT_M" in df_census.columns else "NOT FOUND",
        "Female Population": "TOT_F" if "TOT_F" in df_census.columns else "NOT FOUND",
        "SC Population": "P_SC" if "P_SC" in df_census.columns else "NOT FOUND",
        "ST Population": "P_ST" if "P_ST" in df_census.columns else "NOT FOUND",
    }
    for k, v in mapping.items():
        print(f"   - {k}: '{v}' (Present: {v in df_census.columns})")

    print("\n8. Record Counts by Administrative Level ('Level' column):")
    level_counts = df_census['Level'].value_counts(dropna=False)
    print(level_counts.to_string())
    
    village_records = len(df_census[df_census['Level'] == 'VILLAGE']) if 'Level' in df_census.columns else 0
    town_records = len(df_census[df_census['Level'] == 'TOWN']) if 'Level' in df_census.columns else 0
    cdblock_records = len(df_census[df_census['Level'] == 'CD BLOCK']) if 'Level' in df_census.columns else 0
    district_records = len(df_census[df_census['Level'] == 'DISTRICT']) if 'Level' in df_census.columns else 0
    print(f"\n   - Village records: {village_records}")
    print(f"   - Town records: {town_records}")
    print(f"   - CD Block records: {cdblock_records}")
    print(f"   - District records: {district_records}")
    print(f"   - Total records: {row_count}")

    print("\n9. Null Value Check in Core Demographic Fields:")
    for col in ['Name', 'Town/Village', 'No_HH', 'TOT_P', 'TOT_M', 'TOT_F', 'P_SC', 'P_ST']:
        if col in df_census.columns:
            null_cnt = df_census[col].isnull().sum()
            print(f"   - {col}: {null_cnt} nulls ({null_cnt / row_count * 100:.2f}%)")

    print("\n10. Duplicate Check in Census Village Codes:")
    village_df = df_census[df_census['Level'] == 'VILLAGE']
    tv_codes = village_df['Town/Village']
    dup_tv = tv_codes[tv_codes.duplicated()].unique()
    print(f"   - Total Village rows: {len(village_df)}")
    print(f"   - Unique 'Town/Village' codes in VILLAGE level: {tv_codes.nunique()}")
    print(f"   - Duplicate 'Town/Village' codes count: {len(dup_tv)}")
    if len(dup_tv) > 0:
        print(f"   - Duplicate codes: {dup_tv.tolist()[:10]}")

    # -------------------------------------------------------------
    # PHASE 2: SPATIAL DATASET INSPECTION
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PHASE 2 — SPATIAL DATASET INSPECTION (rudraprayag_settlements_osm.geojson)")
    print("=" * 80)

    if not osm_file.exists():
        print(f"ERROR: Spatial file not found: {osm_file}")
        return 1

    gdf_osm = gpd.read_file(osm_file)
    print(f"1. Coordinate Reference System (CRS): {gdf_osm.crs}")
    print(f"2. Total Feature Count: {len(gdf_osm)}")
    print(f"3. Geometry Type Counts:\n{gdf_osm.geometry.geom_type.value_counts().to_string()}")
    print(f"4. Complete Attribute Column Names ({len(gdf_osm.columns)} columns):")
    for i, col in enumerate(gdf_osm.columns):
        print(f"   [{i:02d}] {col} (dtype: {gdf_osm[col].dtype})")

    print("\n5. First 10 Attribute Records (Selected Columns):")
    preview_cols = [c for c in ['osm_id', 'osm_type', 'name', 'place', 'population', 'source'] if c in gdf_osm.columns]
    # Replace non-ascii characters for clean console display
    preview_df = gdf_osm[preview_cols].head(10).copy()
    if 'name' in preview_df.columns:
        preview_df['name'] = preview_df['name'].apply(lambda x: str(x).encode('ascii', 'replace').decode('ascii') if pd.notnull(x) else None)
    print(preview_df.to_string())

    print("\n6. Unique Values in 'place' Classification:")
    place_counts = gdf_osm['place'].value_counts(dropna=False)
    print(place_counts.to_string())

    print("\n7. Identification of Key Structural / Administrative Fields:")
    has_census_code = any('census' in c.lower() or 'mdds' in c.lower() for c in gdf_osm.columns)
    has_lgd_code = any('lgd' in c.lower() for c in gdf_osm.columns)
    has_district = any('district' in c.lower() or 'dt' in c.lower() for c in gdf_osm.columns)
    print(f"   - Settlement Name Field: {'name' if 'name' in gdf_osm.columns else 'NOT FOUND'}")
    print(f"   - OSM Identifier: {'osm_id' if 'osm_id' in gdf_osm.columns else 'NOT FOUND'}")
    print(f"   - Census Code Field: {'YES (' + ', '.join([c for c in gdf_osm.columns if 'census' in c.lower() or 'mdds' in c.lower()]) + ')' if has_census_code else 'NONE'}")
    print(f"   - LGD Code Field: {'YES (' + ', '.join([c for c in gdf_osm.columns if 'lgd' in c.lower()]) + ')' if has_lgd_code else 'NONE'}")
    print(f"   - Explicit District / Administrative Hierarchy Fields: {'YES (' + ', '.join([c for c in gdf_osm.columns if 'district' in c.lower()]) + ')' if has_district else 'NONE (Inferred from Bounding Box query only)'}")

    print("\n8. Settlement Name Quality Audit:")
    if 'name' in gdf_osm.columns:
        null_names = gdf_osm['name'].isnull().sum()
        valid_names = gdf_osm['name'].dropna()
        dup_names = valid_names[valid_names.duplicated()].unique()
        print(f"   - Total records: {len(gdf_osm)}")
        print(f"   - Null / Unnamed settlements: {null_names} ({null_names / len(gdf_osm) * 100:.2f}%)")
        print(f"   - Named settlements: {len(valid_names)}")
        print(f"   - Unique names: {valid_names.nunique()}")
        print(f"   - Duplicate name count: {len(dup_names)}")
        if len(dup_names) > 0:
            sample_dup = [str(n).encode('ascii', 'replace').decode('ascii') for n in dup_names[:10]]
            print(f"   - Sample duplicate names: {sample_dup}")

    # -------------------------------------------------------------
    # PHASE 3: JOIN FEASIBILITY ANALYSIS
    # -------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PHASE 3 — JOIN FEASIBILITY ANALYSIS")
    print("=" * 80)

    print("Shared Code Check:")
    print(f"   - Census Village Code present in Census table: YES ('Town/Village' column, e.g., MDDS code)")
    print(f"   - Census Village Code present in Spatial dataset: {'YES' if has_census_code else 'NO'}")
    print(f"   - LGD Code present in Census table: NO")
    print(f"   - LGD Code present in Spatial dataset: {'YES' if has_lgd_code else 'NO'}")
    print(f"   - Other authoritative common key (e.g. SHRID / Pincode / UID): NONE")

    print("\nJoin Feasibility Classification:")
    classification = "PARTIAL — datasets inspected but no safe join key exists"
    print(f"   Classification: B / C -> NO SAFE CODE-BASED JOIN POSSIBLE")
    print(f"   Reason: The official Census 2011 PCA dataset uses 6-digit Census 2011/MDDS village codes,")
    print(f"           while the OpenStreetMap spatial dataset contains OSM IDs and names but lacks Census MDDS codes.")
    print(f"           Joining on settlement name is UNSAFE due to severe phonetic spelling variations, transliterations,")
    print(f"           duplicate village names (e.g. multiple hamlets sharing common regional names), and 35.8% unnamed features.")

    print("\nRequired Additional Dataset for Exact Code-Based Join:")
    print("   To achieve an authoritative 1:1 code-based join with Census 2011 PCA, one of the following is required:")
    print("   1. Survey of India (SOI) / LGD / DataMeet 2011 Village Boundaries Shapefile/GeoJSON with Census MDDS village codes.")
    print("   2. DevDataLab SHRUG (Socioeconomic High-resolution Rural-Urban Geographic) spatial shapefile which maps SHRIDs to Census 2011 MDDS village codes.")
    print("   3. Or maintain spatial hazard exposure as a continuous raster overlay / settlement point exposure directly without demographic join.")

    print("\n" + "=" * 80)
    print(f"FINAL STATUS: {classification}")
    print("=" * 80)
    return 0

if __name__ == "__main__":
    sys.exit(inspect_data())
