import urllib.request
import urllib.parse
import json
import time
import pathlib

bbox = "30.10,78.70,30.90,79.50"
query = f"""[out:json][timeout:90];
(
  node["amenity"~"hospital|clinic|doctors|pharmacy|school|college|university|kindergarten|police|fire_station|community_centre|townhall"]({bbox});
  way["amenity"~"hospital|clinic|doctors|pharmacy|school|college|university|kindergarten|police|fire_station|community_centre|townhall"]({bbox});
  node["healthcare"]({bbox});
  way["healthcare"]({bbox});
  node["emergency"]({bbox});
  way["emergency"]({bbox});
);
out center tags;
"""

endpoints = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter"
]

data = None
for ep in endpoints:
    print(f"Querying Overpass endpoint: {ep}...")
    try:
        req = urllib.request.Request(
            ep,
            data=urllib.parse.urlencode({"data": query}).encode("utf-8"),
            headers={"User-Agent": "SIH26191-Rudraprayag-Infrastructure-Audit/1.0"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            print(f"Success! Elements fetched: {len(data.get('elements', []))}")
            break
    except Exception as e:
        print(f"Error from {ep}: {e}")
        time.sleep(2)

if data:
    elements = data.get("elements", [])
    print(f"\nTotal elements: {len(elements)}")
    
    amenities = {}
    healthcares = {}
    for el in elements:
        t = el.get("tags", {})
        am = t.get("amenity", "none")
        amenities[am] = amenities.get(am, 0) + 1
        hc = t.get("healthcare", "none")
        if hc != "none":
            healthcares[hc] = healthcares.get(hc, 0) + 1

    print("\nAmenity breakdown:")
    for k, v in sorted(amenities.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    print("\nHealthcare tag breakdown:")
    for k, v in sorted(healthcares.items(), key=lambda x: -x[1]):
        print(f"  {k}: {v}")

    # Inspect sample records
    print("\nSample records:")
    for el in elements[:10]:
        t = el.get("tags", {})
        lat = el.get("lat") or (el.get("center", {}).get("lat"))
        lon = el.get("lon") or (el.get("center", {}).get("lon"))
        print(f"  ID: {el.get('type')}/{el.get('id')} | Name: {t.get('name', 'Unnamed')} | Amenity: {t.get('amenity')} | Healthcare: {t.get('healthcare')} | Coords: ({lat}, {lon})")

    out_file = pathlib.Path("data/raw/infrastructure/osm_critical_infrastructure_raw.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    print(f"\nSaved raw data to {out_file} ({out_file.stat().st_size / 1024:.1f} KB)")
