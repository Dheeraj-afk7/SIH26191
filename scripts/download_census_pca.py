import os
from pathlib import Path
import urllib.request
import ssl

out_dir = Path("data/raw/habitations")
out_dir.mkdir(parents=True, exist_ok=True)

url = "https://censusindia.gov.in/nada/index.php/catalog/40739/download/44370/PCA_CDB-0503-F-Census.xlsx"
out_file = out_dir / "PCA_CDB-0503-F-Census.xlsx"

print(f"Downloading from: {url}")
print(f"Target: {out_file}")

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
}

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, context=ctx, timeout=60) as resp, open(out_file, "wb") as f:
        data = resp.read()
        f.write(data)
    print(f"Downloaded successfully: {len(data)} bytes")
    print(f"File exists: {out_file.exists()}")
    print(f"File size: {out_file.stat().st_size} bytes")
    
    # Try reading first few bytes or open with pandas/openpyxl
    with open(out_file, "rb") as f:
        header = f.read(16)
        print(f"Magic bytes: {header}")
except Exception as e:
    print(f"Error: {e}")
