import json
import pathlib
import pandas as pd
import geopandas as gpd
import shapely.geometry as sg

raw_file = pathlib.Path("data/raw/infrastructure/osm_critical_infrastructure_raw.json")
with open(raw_file, "r", encoding="utf-8") as f:
    data = json.load(f)

elements = data.get("elements", [])
rows = []
for el in elements:
    t = el.get("tags", {})
    lat = el.get("lat") if "lat" in el else el.get("center", {}).get("lat")
    lon = el.get("lon") if "lon" in el else el.get("center", {}).get("lon")
    
    rows.append({
        "osm_id": f"{el.get('type')}/{el.get('id')}",
        "osm_type": el.get("type"),
        "id_num": el.get("id"),
        "latitude": lat,
        "longitude": lon,
        "name": t.get("name", ""),
        "name_en": t.get("name:en", ""),
        "amenity": t.get("amenity", ""),
        "healthcare": t.get("healthcare", ""),
        "healthcare_speciality": t.get("healthcare:speciality", ""),
        "emergency": t.get("emergency", ""),
        "operator": t.get("operator", ""),
        "operator_type": t.get("operator:type", ""),
        "building": t.get("building", ""),
        "raw_tags": json.dumps(t)
    })

df = pd.DataFrame(rows)
print(f"Total elements: {len(df)}")
print(f"Null coords: {df['latitude'].isna().sum()}")

# Geospatial bounds check against Rudraprayag AOI [78.70, 30.10, 79.50, 30.90]
in_aoi = (
    (df["longitude"] >= 78.70) & (df["longitude"] <= 79.50) &
    (df["latitude"] >= 30.10) & (df["latitude"] <= 30.90)
)
print(f"Features strictly within pilot bounding box: {in_aoi.sum()} / {len(df)}")

# Categorize facilities
# Healthcare: Hospital, Community Health Centre (CHC), Primary Health Centre (PHC), Subcentre, Clinic, Pharmacy
# Education: School, College, University, Kindergarten
# Emergency/Admin: Police, Fire Station, Town Hall, Community Centre

def categorize(row):
    am = str(row["amenity"]).lower()
    hc = str(row["healthcare"]).lower()
    name = str(row["name"]).lower()
    em = str(row["emergency"]).lower()
    
    # 1. Healthcare
    if "hospital" in am or "hospital" in hc or "hospital" in name:
        return "HEALTHCARE_HOSPITAL"
    elif "chc" in name or "community health" in name:
        return "HEALTHCARE_CHC"
    elif "phc" in name or "primary health" in name or "aphc" in name:
        return "HEALTHCARE_PHC"
    elif "subcentre" in name or "sub-centre" in name or "sub centre" in name:
        return "HEALTHCARE_SUBCENTRE"
    elif "clinic" in am or "clinic" in hc or "doctors" in am or "dispensary" in name or hc == "centre":
        return "HEALTHCARE_CLINIC_OR_CENTRE"
    elif "pharmacy" in am:
        return "HEALTHCARE_PHARMACY"
    
    # 2. Education
    elif am == "school" or "school" in name or "vidyalaya" in name or "inter college" in name:
        return "EDUCATION_SCHOOL"
    elif am == "college" or "college" in name or "polytechnic" in name or "iti" in name:
        return "EDUCATION_HIGHER"
    elif am == "university" or "university" in name:
        return "EDUCATION_UNIVERSITY"
    elif am == "kindergarten" or "anganwadi" in name:
        return "EDUCATION_KINDERGARTEN"
    
    # 3. Emergency / Civic Administration
    elif am == "police" or "police" in name or "thana" in name or "chowki" in name:
        return "EMERGENCY_POLICE"
    elif am == "fire_station" or "fire" in name:
        return "EMERGENCY_FIRE_STATION"
    elif am == "townhall" or am == "community_centre" or "panchayat" in name or "milan kendra" in name:
        return "CIVIC_COMMUNITY_CENTRE"
    else:
        return "OTHER_CIVIC_FACILITY"

df["facility_category"] = df.apply(categorize, axis=1)

print("\nFacility Category Breakdown:")
print(df["facility_category"].value_counts())

print("\nSample facilities per category:")
for cat, grp in df.groupby("facility_category"):
    print(f"\n--- {cat} ({len(grp)}) ---")
    for idx, r in grp.head(3).iterrows():
        print(f"  {r['osm_id']} | Name: {r['name']} | Coords: ({r['latitude']:.4f}, {r['longitude']:.4f})")
