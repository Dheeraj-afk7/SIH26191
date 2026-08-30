import json
import pathlib
import sys
import io
import pandas as pd

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

raw_path = pathlib.Path("data/raw/infrastructure/osm_critical_infrastructure_raw.json")
with open(raw_path, "r", encoding="utf-8") as f:
    data = json.load(f)

elements = data.get("elements", [])
print(f"Total raw elements: {len(elements)}")

rows = []
for el in elements:
    t = el.get("tags", {})
    lat = el.get("lat") if "lat" in el else el.get("center", {}).get("lat")
    lon = el.get("lon") if "lon" in el else el.get("center", {}).get("lon")
    
    rows.append({
        "osm_id": f"{el.get('type')}/{el.get('id')}",
        "osm_type": el.get("type"),
        "osm_num_id": el.get("id"),
        "name": t.get("name", ""),
        "amenity": t.get("amenity", ""),
        "healthcare": t.get("healthcare", ""),
        "building": t.get("building", ""),
        "office": t.get("office", ""),
        "emergency": t.get("emergency", ""),
        "lat": lat,
        "lon": lon,
        "tags": t
    })

df = pd.DataFrame(rows)

print("\n--- Education Tag Analysis ---")
edu_mask = (
    df["amenity"].isin(["school", "college", "university", "kindergarten"]) |
    df["building"].isin(["school", "college", "university", "kindergarten"]) |
    df["name"].str.lower().str.contains("school|vidyalaya|college|university|iti|polytechnic|campus", regex=True)
)
edu_df = df[edu_mask].copy()
print(f"Total education elements matched: {len(edu_df)}")
print("\nAmenity tags in education:")
print(edu_df["amenity"].value_counts(dropna=False))
print("\nBuilding tags in education:")
print(edu_df["building"].value_counts(dropna=False))
print(f"Named education facilities: {(edu_df['name'] != '').sum()}")
print(f"Unnamed education facilities: {(edu_df['name'] == '').sum()}")
print("\nEducation facility names sample:")
for idx, r in edu_df.head(15).iterrows():
    print(f"  {r['osm_id']} | Amenity: '{r['amenity']}' | Building: '{r['building']}' | Name: '{r['name']}'")

print("\n--- Emergency Tag Analysis ---")
print("Emergency tag values across all 291 elements:")
print(df["emergency"].value_counts(dropna=False))

print("\n--- Healthcare Analysis ---")
hc_mask = (
    df["amenity"].isin(["hospital", "clinic", "doctors", "pharmacy"]) |
    df["healthcare"].isin(["hospital", "centre", "clinic", "subcentre", "dispensary", "yes"]) |
    df["name"].str.lower().str.contains("hospital|chc|phc|subcentre|dispensary|clinic|chemist", regex=True)
)
hc_df = df[hc_mask].copy()
print(f"Total healthcare elements matched: {len(hc_df)}")
print("\nHealthcare tag distribution:")
print(hc_df["healthcare"].value_counts(dropna=False))
print("\nHealthcare amenity tag distribution:")
print(hc_df["amenity"].value_counts(dropna=False))
