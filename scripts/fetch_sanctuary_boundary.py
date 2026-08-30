#!/usr/bin/env python3
"""
Fetch official Kedarnath Wildlife Sanctuary protected area boundary from Overpass API / OSM.
"""

import json
import urllib.parse
import urllib.request

queries = [
    '[out:json][timeout:60];(nwr["name"~"Kedarnath",i]["boundary"="protected_area"];nwr["name"~"Kedarnath",i]["leisure"="nature_reserve"];nwr["name"~"Kedarnath",i]["protect_class"];nwr["name"~"Kedarnath Musk Deer",i];);out geom;',
    '[out:json][timeout:60];relation["boundary"="protected_area"](30.15,78.80,30.85,79.40);out geom;'
]

for i, q in enumerate(queries):
    url = "https://overpass-api.de/api/interpreter?data=" + urllib.parse.quote(q)
    print(f"Executing Query {i+1}...")
    req = urllib.request.Request(url, headers={"User-Agent": "SIH26191-GIS-Pipeline/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            elements = data.get("elements", [])
            print(f"Query {i+1} returned {len(elements)} element(s):")
            for el in elements:
                tags = el.get("tags", {})
                print(f"  Type: {el['type']}, ID: {el['id']}")
                print(f"  Tags: {tags}")
                if "members" in el:
                    print(f"  Members: {len(el['members'])}")
                if "geometry" in el:
                    print(f"  Geometry points: {len(el['geometry'])}")
    except Exception as exc:
        print(f"Query {i+1} failed: {exc}")
