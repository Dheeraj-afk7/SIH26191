"""Diagnose spatial alignment between habitations and red zones."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
import geopandas as gpd
import numpy as np

hab = gpd.read_file('data/processed/habitations/habitation_baseline.geojson')
rz  = gpd.read_file('data/outputs/candidate_hazard_based_red_zones.geojson')

print(f"Habitations CRS: {hab.crs}")
print(f"Red zones CRS  : {rz.crs}")
print()
print(f"Habitations bounds: {hab.total_bounds}")
print(f"Red zones bounds  : {rz.total_bounds}")
print()

# Check if extents overlap
hab_xmin, hab_ymin, hab_xmax, hab_ymax = hab.total_bounds
rz_xmin,  rz_ymin,  rz_xmax,  rz_ymax  = rz.total_bounds

overlap_x = hab_xmin < rz_xmax and hab_xmax > rz_xmin
overlap_y = hab_ymin < rz_ymax and hab_ymax > rz_ymin
print(f"X extents overlap: {overlap_x}")
print(f"Y extents overlap: {overlap_y}")
print()

# Try intersects instead of within
print("Testing with 'intersects' predicate ...")
joined_int = gpd.sjoin(hab, rz[['zone_id','geometry']], how='left', predicate='intersects')
print(f"Joined rows with intersects: {len(joined_int)}")
print(f"Matched (not null): {joined_int['zone_id'].notna().sum()}")
print()

# Try nearest distance
print("Computing minimum distance from each habitation to nearest red zone polygon ...")
# Sample 5 habitations
for idx, row in hab.head(5).iterrows():
    pt = row['geometry']
    dists = rz.geometry.distance(pt)
    min_dist = dists.min()
    nearest_rz = rz.iloc[dists.idxmin()]['zone_id']
    print(f"  Village {row['village_name']} ({row['village_id']}): min dist to red zone = {min_dist:.1f} m (nearest: {nearest_rz})")

print()
# Total habitations within 1000m of any red zone
dists_all = []
for idx, row in hab.iterrows():
    dists_all.append(rz.geometry.distance(row['geometry']).min())
dists_arr = np.array(dists_all)
print(f"Habitations within  100m of red zone: {(dists_arr < 100).sum()}")
print(f"Habitations within  500m of red zone: {(dists_arr < 500).sum()}")
print(f"Habitations within 1000m of red zone: {(dists_arr < 1000).sum()}")
print(f"Habitations within 2000m of red zone: {(dists_arr < 2000).sum()}")
print(f"Min distance overall: {dists_arr.min():.1f} m")
print(f"Max distance overall: {dists_arr.max():.1f} m")
print(f"Mean distance       : {dists_arr.mean():.1f} m")

# Are SHRUG points in UTM geographic space?
print()
print("Sample habitation coordinates (should be metric UTM):")
print(hab[['village_name','geometry']].head(5).to_string())
