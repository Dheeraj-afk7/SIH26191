import json
from pathlib import Path
import time
import urllib.request
import zipfile

out_dir = Path("data/raw/habitations")
out_dir.mkdir(parents=True, exist_ok=True)

# Fetch latest presigned URLs
catalog_url = "http://www.devdatalab.org/shrug_download/data"
req = urllib.request.Request(catalog_url, headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as resp:
    catalog = json.loads(resp.read().decode("utf-8"))

target_items = [
    ("Population Census keys", "shrug-pc-keys-csv.zip"),
    ("Shrug Location Names and Additional Keys", "shrug-shrid-keys-csv.zip")
]

for table_name, filename in target_items:
    url = None
    for item in catalog:
        if item.get("table_short_label") == table_name:
            url = item.get("secondary_download")
            break
            
    if not url:
        print(f"URL for {table_name} not found in catalog.")
        continue
        
    dest = out_dir / filename
    print(f"\n--- Downloading {filename} ({table_name}) ---", flush=True)
    g_req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    
    start_time = time.time()
    try:
        with urllib.request.urlopen(g_req, timeout=60) as resp, open(dest, "wb") as f:
            total_size = int(resp.headers.get("Content-Length", 0))
            print(f"Total size: {total_size / (1024*1024):.2f} MB ({total_size} bytes)", flush=True)
            downloaded = 0
            while True:
                chunk = resp.read(128 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                downloaded += len(chunk)
                if downloaded % (2 * 1024 * 1024) < 128 * 1024:
                    elapsed = time.time() - start_time
                    speed = downloaded / (1024 * 1024 * elapsed) if elapsed > 0 else 0
                    print(f"Downloaded: {downloaded / (1024*1024):.2f} MB / {total_size / (1024*1024):.2f} MB ({downloaded/total_size*100:.1f}%) @ {speed:.2f} MB/s", flush=True)
        print(f"Finished {filename}. Total bytes: {dest.stat().st_size}", flush=True)
        
        print(f"Extracting {filename}...", flush=True)
        with zipfile.ZipFile(dest, "r") as z:
            for member in z.namelist():
                print(f"  - Extracted: {member}", flush=True)
            z.extractall(out_dir)
    except Exception as e:
        print(f"Error downloading {filename}: {e}", flush=True)

print("\nAll downloads processed.", flush=True)
