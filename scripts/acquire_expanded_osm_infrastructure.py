import urllib.request
import urllib.parse
import json
import pathlib

bbox = "30.10,78.70,30.90,79.50"
query = f"""[out:json][timeout:120];
(
  node["amenity"~"hospital|clinic|doctors|pharmacy|school|college|university|kindergarten|police|fire_station|community_centre|townhall|courthouse|post_office"]({bbox});
  way["amenity"~"hospital|clinic|doctors|pharmacy|school|college|university|kindergarten|police|fire_station|community_centre|townhall|courthouse|post_office"]({bbox});
  node["healthcare"]({bbox});
  way["healthcare"]({bbox});
  node["building"~"school|hospital|kindergarten|university|college"]({bbox});
  way["building"~"school|hospital|kindergarten|university|college"]({bbox});
  node["emergency"]({bbox});
  way["emergency"]({bbox});
  node["office"~"government|administrative"]({bbox});
  way["office"~"government|administrative"]({bbox});
);
out center tags;
"""

print("Querying Overpass with expanded facility tags...")
req = urllib.request.Request(
    "https://overpass-api.de/api/interpreter",
    data=urllib.parse.urlencode({"data": query}).encode("utf-8"),
    headers={"User-Agent": "SIH26191-Rudraprayag-Expanded-Facility-Audit/1.0"}
)

with urllib.request.urlopen(req, timeout=90) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    elements = data.get("elements", [])
    print(f"Expanded elements fetched: {len(elements)}")

# Deduplicate by (type, id)
unique_elements = {}
for el in elements:
    k = (el.get("type"), el.get("id"))
    unique_elements[k] = el

print(f"Unique OSM objects: {len(unique_elements)}")

out_file = pathlib.Path("data/raw/infrastructure/osm_critical_infrastructure_raw.json")
out_file.parent.mkdir(parents=True, exist_ok=True)
with open(out_file, "w", encoding="utf-8") as f:
    json.dump({"elements": list(unique_elements.values())}, f, indent=2)

print(f"Saved {len(unique_elements)} raw infrastructure records to {out_file} ({out_file.stat().st_size / 1024:.1f} KB)")
