#!/usr/bin/env python3
"""
SIH26191 -- Phase 2 Acquisition: OpenStreetMap Road Network Extract
===================================================================

Pilot Area: Rudraprayag District, Uttarakhand, India
Bounding Box: Longitude [78.70°E, 79.50°E], Latitude [30.10°N, 30.90°N] (Buffered to prevent boundary clipping)

Acquires complete road network from OpenStreetMap via Overpass API with retry mirrors:
- Highways: motorways, trunk (NH-107, NH-07), primary, secondary, tertiary, unclassified, residential, track, service, path, footway
- Attributes: highway, surface, maxspeed, access, motor_vehicle, bridge, tunnel, name, ref, oneway, smoothness, tracktype
"""

import datetime
import hashlib
import json
import os
import pathlib
import sys
import time
import urllib.parse
import urllib.request
import geopandas as gpd
import shapely.geometry as sg

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW_ROADS_DIR = ROOT / "data" / "raw" / "roads"
RAW_ROADS_DIR.mkdir(parents=True, exist_ok=True)

RAW_JSON_PATH = RAW_ROADS_DIR / "osm_roads_rudraprayag_raw.json"
GEOJSON_PATH = RAW_ROADS_DIR / "osm_roads_rudraprayag.geojson"
PROVENANCE_PATH = RAW_ROADS_DIR / "provenance_metadata.json"

OVERPASS_MIRRORS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
]

# Overpass QL Query for complete road/path network in buffered Rudraprayag BBox
OVERPASS_QUERY = """[out:json][timeout:120];
(
  way["highway"](30.10,78.70,30.90,79.50);
);
out body geom;"""


def acquire_osm_roads(force: bool = False) -> bool:
    print("=" * 76)
    print("  SIH26191: Phase 2 Road Network Acquisition (OpenStreetMap)")
    print("=" * 76)
    print(f"Bounding Box: [78.70°E, 30.10°N] to [79.50°E, 30.90°N] (Buffered)")

    if not force and GEOJSON_PATH.exists() and GEOJSON_PATH.stat().st_size > 6_000_000:
        print(f"[EXISTS] Valid OSM road GeoJSON already present ({GEOJSON_PATH.stat().st_size / (1024*1024):.2f} MB).")
        return True

    data = None
    used_mirror = None
    query_encoded = urllib.parse.quote(OVERPASS_QUERY)

    for mirror in OVERPASS_MIRRORS:
        url = mirror + "?data=" + query_encoded
        print(f"\nAttempting query on Overpass mirror: {mirror}...")
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "SIH26191-GIS-DecisionSupport/1.0 (rudraprayag-disaster-resilience)"}
            )
            with urllib.request.urlopen(req, timeout=75) as resp:
                raw_bytes = resp.read()
                data = json.loads(raw_bytes.decode("utf-8"))
                used_mirror = mirror
                print(f"  [OK] Received response ({len(raw_bytes) / (1024*1024):.2f} MB)")
                
                # Save raw JSON for strict provenance
                with open(RAW_JSON_PATH, "wb") as f:
                    f.write(raw_bytes)
                break
        except Exception as exc:
            print(f"  [WARN] Mirror {mirror} failed: {exc}")
            time.sleep(2)

    if data is None or "elements" not in data:
        print("[ERROR] All Overpass mirrors failed.")
        return False

    elements = data["elements"]
    print(f"\nProcessing {len(elements):,} OSM elements into LineString features...")

    features = []
    for el in elements:
        if el.get("type") != "way":
            continue
        geom_points = el.get("geometry", [])
        if len(geom_points) < 2:
            continue

        coords = [(pt["lon"], pt["lat"]) for pt in geom_points]
        line = sg.LineString(coords)
        tags = el.get("tags", {})

        feat = {
            "type": "Feature",
            "properties": {
                "osm_id": el["id"],
                "highway": tags.get("highway", "unclassified"),
                "name": tags.get("name"),
                "name_en": tags.get("name:en"),
                "ref": tags.get("ref"),
                "surface": tags.get("surface", "unknown"),
                "maxspeed": tags.get("maxspeed"),
                "oneway": tags.get("oneway", "no"),
                "access": tags.get("access", "yes"),
                "motor_vehicle": tags.get("motor_vehicle"),
                "bridge": tags.get("bridge", "no"),
                "tunnel": tags.get("tunnel", "no"),
                "smoothness": tags.get("smoothness"),
                "tracktype": tags.get("tracktype"),
                "lanes": tags.get("lanes"),
                "layer": tags.get("layer", "0")
            },
            "geometry": sg.mapping(line)
        }
        features.append(feat)

    fc = {
        "type": "FeatureCollection",
        "name": "osm_roads_rudraprayag",
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features
    }

    with open(GEOJSON_PATH, "w", encoding="utf-8") as f:
        json.dump(fc, f)

    print(f"[SUCCESS] Written {len(features):,} road line segments to {GEOJSON_PATH.name} ({GEOJSON_PATH.stat().st_size / (1024*1024):.2f} MB)")

    # Provenance metadata
    h = hashlib.sha256()
    with open(GEOJSON_PATH, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    sha256 = h.hexdigest()

    prov = {
        "dataset_name": "OpenStreetMap Road Network (Rudraprayag BBox)",
        "source": "OpenStreetMap Contributors via Overpass API",
        "source_mirror": used_mirror,
        "query": OVERPASS_QUERY,
        "acquisition_timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "license": "Open Database License (ODbL) 1.0",
        "attribution": "© OpenStreetMap contributors",
        "raw_json_file": RAW_JSON_PATH.name,
        "geojson_file": GEOJSON_PATH.name,
        "file_size_bytes": GEOJSON_PATH.stat().st_size,
        "sha256_hash": sha256,
        "feature_count": len(features),
        "source_crs": "EPSG:4326 (WGS84)",
        "bounding_box": [78.70, 30.10, 79.50, 30.90],
        "original_attributes_preserved": [
            "osm_id", "highway", "name", "name_en", "ref", "surface",
            "maxspeed", "oneway", "access", "motor_vehicle", "bridge",
            "tunnel", "smoothness", "tracktype", "lanes", "layer"
        ]
    }

    with open(PROVENANCE_PATH, "w", encoding="utf-8") as f:
        json.dump(prov, f, indent=2)

    print(f"[PROVENANCE] Written provenance metadata to {PROVENANCE_PATH.name}")
    return True


if __name__ == "__main__":
    force_run = "--force" in sys.argv or True
    if not acquire_osm_roads(force=force_run):
        sys.exit(1)
