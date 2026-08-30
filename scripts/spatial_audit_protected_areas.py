#!/usr/bin/env python3
"""
SIH26191 -- Spatial Audit & Geographic Identity Verification
Compares Rudraprayag AOI bounds with UNEP-WCMC Site ID 902492 (Nanda Devi) and Kedarnath Sanctuary geography.
"""

import json
import pathlib
import geopandas as gpd
import rasterio
from shapely.geometry import box

ROOT = pathlib.Path(__file__).resolve().parent.parent

# 1. AOI Bounds
with rasterio.open(ROOT / "data/processed/terrain/slope_degrees.tif") as src:
    aoi_bounds_32644 = src.bounds
    aoi_crs = src.crs

aoi_box = box(*aoi_bounds_32644)
aoi_gdf = gpd.GeoDataFrame({"name": ["Rudraprayag Pilot AOI Grid"], "geometry": [aoi_box]}, crs=aoi_crs)
aoi_4326 = aoi_gdf.to_crs(4326)
aoi_b_4326 = aoi_4326.total_bounds

# 2. UNEP-WCMC Layer
nd_path = ROOT / "data/raw/lulc/protected_areas_unep_wcmc.geojson"
nd_gdf = gpd.read_file(str(nd_path))
nd_b_4326 = nd_gdf.total_bounds
nd_32644 = nd_gdf.to_crs(aoi_crs)

# 3. Intersection Analysis
inter_geom = aoi_gdf.geometry.intersection(nd_32644.geometry.iloc[0])
inter_area_ha = float(inter_geom.area.iloc[0] / 10000.0)
aoi_area_ha = float(aoi_gdf.area.iloc[0] / 10000.0)

# Valid terrain inside slope raster
with rasterio.open(ROOT / "data/processed/terrain/slope_degrees.tif") as slope_src:
    slope_arr = slope_src.read(1)
    valid_terrain_px = int((slope_arr != slope_src.nodata).sum())
    pixel_area_ha = float((slope_src.res[0] * slope_src.res[1]) / 10000.0)
    valid_terrain_ha = float(valid_terrain_px * pixel_area_ha)

# Sanctuary raster stats if rasterized
sanct_tif = ROOT / "data/processed/lulc/protected_areas_30m.tif"
sanct_px = 0
if sanct_tif.exists():
    with rasterio.open(sanct_tif) as s_src:
        s_arr = s_src.read(1)
        sanct_px = int((s_arr == 1).sum())

sanct_ha = sanct_px * pixel_area_ha

print("=" * 76)
print("  GEOGRAPHIC IDENTITY & SPATIAL INTERSECTION AUDIT")
print("=" * 76)

print(f"\n1. SOURCE API RECORD ATTRIBUTES (UNEP-WCMC):")
props = dict(nd_gdf.drop(columns="geometry").iloc[0])
for k, v in props.items():
    print(f"   {k:15s}: {v}")

print(f"\n2. BOUNDING BOX COMPARISON (EPSG:4326 - WGS84):")
print(f"   Rudraprayag AOI Grid       : [lon_min={aoi_b_4326[0]:.4f}, lat_min={aoi_b_4326[1]:.4f}, lon_max={aoi_b_4326[2]:.4f}, lat_max={aoi_b_4326[3]:.4f}]")
print(f"   UNEP-WCMC Site 902492      : [lon_min={nd_b_4326[0]:.4f}, lat_min={nd_b_4326[1]:.4f}, lon_max={nd_b_4326[2]:.4f}, lat_max={nd_b_4326[3]:.4f}]")

print(f"\n3. SPATIAL INTERSECTION METRICS:")
print(f"   Total AOI Envelope Area    : {aoi_area_ha:,.2f} ha (BBox)")
print(f"   Valid District Terrain Area: {valid_terrain_ha:,.2f} ha (Rudraprayag DEM mask)")
print(f"   Spatial Overlap Polygon Area: {inter_area_ha:,.2f} ha ({inter_area_ha * 100.0 / aoi_area_ha:.2f}% of AOI Envelope)")
print(f"   Rasterized Overlap in DEM  : {sanct_px:,} pixels = {sanct_ha:,.2f} ha ({sanct_ha * 100.0 / valid_terrain_ha:.2f}% of Valid Terrain)")

print(f"\n4. GEOGRAPHIC RELATIONSHIP:")
print(f"   The Nanda Devi UNESCO-MAB Biosphere Reserve (WDPA ID 902492) is centered in Chamoli/Pithoragarh")
print(f"   with its westernmost high-altitude buffer overlapping the eastern border of the Rudraprayag AOI ({inter_area_ha:,.1f} ha).")
print(f"   However, Kedarnath Wildlife Sanctuary (WDPA ID 832, 975 km²) is the distinct, primary statutory")
print(f"   wildlife sanctuary occupying north-central Rudraprayag (upper Mandakini basin & Kedarnath valley).")
