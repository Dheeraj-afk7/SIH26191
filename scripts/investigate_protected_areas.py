#!/usr/bin/env python3
"""
Deep investigation into authoritative boundary datasets for Kedarnath Wildlife Sanctuary (KWLS).
"""

import json
import urllib.parse
import urllib.request
import geopandas as gpd
import rasterio

# Check Rudraprayag DEM / slope bounds
with rasterio.open("data/processed/terrain/slope_degrees.tif") as src:
    print(f"Reference Grid: {src.shape}, Bounds: {src.bounds}, CRS: {src.crs}")
    ref_bounds = src.bounds

# Query 1: Check Protected Planet API directly for WDPA 832
url_wdpa = "https://api.protectedplanet.net/v3/protected_areas/832"
print(f"\nChecking Protected Planet endpoint for 832...")

# Query 2: Search UNEP-WCMC FeatureServer Layer 0 (Points) and Layer 1 (Polygons) with wildcard searches
base_fs = "https://data-gis.unep-wcmc.org/server/rest/services/ProtectedPlanet/WDPCA/FeatureServer"

for layer in [0, 1]:
    q_url = f"{base_fs}/{layer}/query?where=1%3D1&geometry=78.80%2C30.15%2C79.40%2C30.85&geometryType=esriGeometryEnvelope&inSR=4326&spatialRel=esriSpatialRelIntersects&outFields=*&f=json"
    req = urllib.request.Request(q_url, headers={"User-Agent": "SIH26191/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            feats = data.get("features", [])
            print(f"UNEP-WCMC Layer {layer} returned {len(feats)} features intersecting Rudraprayag BBox:")
            for f in feats:
                attrs = f.get("attributes", {})
                print(f"  Layer {layer} | Site ID: {attrs.get('site_id')} | Name: {attrs.get('name_eng')} ({attrs.get('name')}) | Desig: {attrs.get('desig_eng')} | GIS Area: {attrs.get('gis_area')}")
    except Exception as ex:
        print(f"Layer {layer} query failed: {ex}")

# Query 3: Search Overpass OSM with different mirrors for Kedarnath sanctuary relations/ways
osm_query = """[out:json][timeout:30];
(
  relation["name"~"Kedarnath",i];
  way["name"~"Kedarnath",i];
  relation["boundary"="protected_area"](30.15,78.80,30.85,79.40);
  relation["leisure"="nature_reserve"](30.15,78.80,30.85,79.40);
);
out tags;"""

mirrors = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
]

print("\nQuerying OSM Overpass mirrors for Kedarnath / Protected Areas in BBox...")
for m in mirrors:
    try:
        u = m + "?data=" + urllib.parse.quote(osm_query)
        req = urllib.request.Request(u, headers={"User-Agent": "SIH26191/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            d = json.loads(resp.read().decode("utf-8"))
            els = d.get("elements", [])
            print(f"  Mirror {m} returned {len(els)} elements:")
            for e in els:
                t = e.get("tags", {})
                print(f"    {e['type']} {e['id']} | name: {t.get('name')} | boundary: {t.get('boundary')} | leisure: {t.get('leisure')} | protect_class: {t.get('protect_class')}")
            break
    except Exception as ex:
        print(f"  Mirror {m} failed: {ex}")
