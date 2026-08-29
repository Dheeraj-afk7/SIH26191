import json
import os
from pathlib import Path
import sys
import urllib.parse
import urllib.request
import geopandas as gpd

def acquire_osm_settlements():
    out_dir = Path("data/raw/habitations")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_geojson = out_dir / "rudraprayag_settlements_osm.geojson"

    # Bounding box covering Rudraprayag District (aligned with Copernicus DEM AOI: [78.7847, 30.1878, 79.3789, 30.8211])
    query = """[out:json][timeout:90];
(
  node["place"~"village|town|hamlet|isolated_dwelling|suburb|locality"](30.1878,78.7847,30.8211,79.3789);
  way["place"~"village|town|hamlet|isolated_dwelling|suburb|locality"](30.1878,78.7847,30.8211,79.3789);
  relation["place"~"village|town|hamlet|isolated_dwelling|suburb|locality"](30.1878,78.7847,30.8211,79.3789);
);
out body;
>;
out skel qt;"""

    url = "https://overpass-api.de/api/interpreter"
    data = urllib.parse.urlencode({"data": query}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"User-Agent": "SIH26191-Geospatial-Acquisition/1.0"})

    print(f"Querying official Overpass API: {url}...")
    with urllib.request.urlopen(req, timeout=90) as resp:
        raw_json = json.loads(resp.read().decode("utf-8"))

    elements = raw_json.get("elements", [])
    print(f"Retrieved {len(elements)} raw elements from OSM.")

    features = []
    nodes = {e["id"]: (e["lon"], e["lat"]) for e in elements if e["type"] == "node" and "lon" in e and "lat" in e}

    for el in elements:
        tags = el.get("tags", {})
        if "place" not in tags:
            continue
        
        geom = None
        if el["type"] == "node":
            geom = {
                "type": "Point",
                "coordinates": [el["lon"], el["lat"]]
            }
        elif el["type"] == "way" and "nodes" in el:
            coords = [nodes[nid] for nid in el["nodes"] if nid in nodes]
            if len(coords) >= 3 and coords[0] == coords[-1]:
                geom = {"type": "Polygon", "coordinates": [coords]}
            elif len(coords) >= 2:
                geom = {"type": "LineString", "coordinates": coords}
                
        if geom:
            props = dict(tags)
            props["osm_id"] = el["id"]
            props["osm_type"] = el["type"]
            features.append({
                "type": "Feature",
                "geometry": geom,
                "properties": props
            })

    fc = {
        "type": "FeatureCollection",
        "name": "rudraprayag_settlements_osm",
        "crs": {
            "type": "name",
            "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}
        },
        "features": features
    }

    with open(out_geojson, "w", encoding="utf-8") as f:
        json.dump(fc, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(features)} settlement features to: {out_geojson}")
    print(f"File size: {out_geojson.stat().st_size} bytes")

    # Test opening with GeoPandas
    gdf = gpd.read_file(out_geojson)
    print(f"GeoPandas successfully loaded: {len(gdf)} records, CRS: {gdf.crs}")
    print("Geometry types:")
    print(gdf.geometry.geom_type.value_counts().to_string())
    print("Place categories:")
    print(gdf["place"].value_counts().to_string())
    print("Spatial acquisition successful.")

if __name__ == "__main__":
    acquire_osm_settlements()
