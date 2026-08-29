import json
from pathlib import Path
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point

habitations_dir = Path("data/raw/habitations")
pc11_key_file = habitations_dir / "pc11r_shrid_key.csv"
spatial_stats_file = habitations_dir / "shrid2_spatial_stats.csv"
loc_names_file = habitations_dir / "shrid_loc_names.csv"
census_excel_file = habitations_dir / "PCA_CDB-0503-F-Census.xlsx"
out_geojson = habitations_dir / "rudraprayag_census_villages_shrug.geojson"

print("Loading SHRUG PC11 keys...")
df_keys = pd.read_csv(pc11_key_file)
# Filter for State=5 (Uttarakhand), District=58 (Rudraprayag)
rudra_keys = df_keys[(df_keys['pc11_state_id'] == 5) & (df_keys['pc11_district_id'] == 58)].copy()
print(f"Total Rudraprayag PC11 village keys: {len(rudra_keys)}")

print("Loading SHRUG spatial statistics...")
df_spatial = pd.read_csv(spatial_stats_file)

print("Merging PC11 keys with spatial coordinates on shrid2...")
merged = rudra_keys.merge(df_spatial[['shrid2', 'latitude', 'longitude', 'area_laea', 'high_quality', 'polysource']], on='shrid2', how='left')

# Load location names if available
if loc_names_file.exists():
    df_names = pd.read_csv(loc_names_file)
    merged = merged.merge(df_names[['shrid2', 'state_name', 'district_name', 'subdistrict_name', 'village_name', 'place_name']], on='shrid2', how='left')

print(f"Total merged records: {len(merged)}")
print(f"Null latitudes: {merged['latitude'].isnull().sum()}")
print(f"Null longitudes: {merged['longitude'].isnull().sum()}")

# Create GeoDataFrame with Point geometry
valid_spatial = merged.dropna(subset=['latitude', 'longitude']).copy()
geometry = [Point(xy) for xy in zip(valid_spatial['longitude'], valid_spatial['latitude'])]
gdf_shrug = gpd.GeoDataFrame(valid_spatial, geometry=geometry, crs="EPSG:4326")

# Save as standard GeoJSON
gdf_shrug.to_file(out_geojson, driver="GeoJSON")
print(f"Saved spatial GeoJSON: {out_geojson} ({out_geojson.stat().st_size} bytes)")

# Test reading back with GeoPandas
gdf_test = gpd.read_file(out_geojson)
print(f"Loaded with GeoPandas: {len(gdf_test)} features, CRS: {gdf_test.crs}")
print(f"Columns: {gdf_test.columns.tolist()}")
print("\nFirst 5 records:")
print(gdf_test[['pc11_village_id', 'shrid2', 'village_name', 'latitude', 'longitude']].head(5).to_string())

# Diagnostic Join Test
print("\n" + "=" * 70)
print("DIAGNOSTIC JOIN TEST: CENSUS PCA EXCEL VS SHRUG SPATIAL BRIDGE")
print("=" * 70)
df_census = pd.read_excel(census_excel_file)
df_census_villages = df_census[df_census['Level'] == 'VILLAGE'].copy()
census_village_codes = set(df_census_villages['Town/Village'].astype(int))

spatial_village_codes = set(gdf_test['pc11_village_id'].astype(int))

matched_codes = census_village_codes.intersection(spatial_village_codes)
unmatched_census = census_village_codes - spatial_village_codes
unmatched_spatial = spatial_village_codes - census_village_codes

print(f"Census village codes in Excel: {len(census_village_codes)}")
print(f"Spatial village records in SHRUG: {len(spatial_village_codes)}")
print(f"Matching Census-Spatial village codes: {len(matched_codes)} ({len(matched_codes)/len(census_village_codes)*100:.2f}%)")
print(f"Unmatched Census village codes: {len(unmatched_census)} ({len(unmatched_census)/len(census_village_codes)*100:.2f}%)")
print(f"Unmatched Spatial village codes: {len(unmatched_spatial)}")
print(f"Duplicate spatial village codes: {len(gdf_test) - gdf_test['pc11_village_id'].nunique()}")

if len(unmatched_census) > 0:
    print(f"Sample unmatched Census codes (first 10): {sorted(list(unmatched_census))[:10]}")
    # Inspect some unmatched census villages
    unmatched_df = df_census_villages[df_census_villages['Town/Village'].isin(unmatched_census)]
    print("\nSample Unmatched Census Villages (Name, Population):")
    print(unmatched_df[['Town/Village', 'Name', 'TOT_P', 'No_HH']].head(10).to_string())
