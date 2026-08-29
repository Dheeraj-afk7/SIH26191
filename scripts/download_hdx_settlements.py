import os
from pathlib import Path
import urllib.request
import zipfile

out_dir = Path("data/raw/habitations")
out_dir.mkdir(parents=True, exist_ok=True)

url = "https://production-raw-data-api.s3.amazonaws.com/ISO3/IND/populated_places/hotosm_ind_populated_places_osm_geojson.zip"
zip_path = out_dir / "hotosm_ind_populated_places_osm_geojson.zip"

print(f"Downloading {url} to {zip_path}...")
headers = {"User-Agent": "Mozilla/5.0"}
req = urllib.request.Request(url, headers=headers)

with urllib.request.urlopen(req, timeout=120) as resp, open(zip_path, "wb") as f:
    total_downloaded = 0
    chunk_size = 1024 * 1024
    while True:
        chunk = resp.read(chunk_size)
        if not chunk:
            break
        f.write(chunk)
        total_downloaded += len(chunk)
        if total_downloaded % (10 * 1024 * 1024) < chunk_size:
            print(f"Downloaded {total_downloaded / (1024*1024):.1f} MB...")

print(f"Finished download. File size: {zip_path.stat().st_size} bytes")

print("Extracting zip contents...")
with zipfile.ZipFile(zip_path, 'r') as z:
    for name in z.namelist():
        print(f"Found in zip: {name}")
    z.extractall(out_dir)

print("Extraction complete.")
