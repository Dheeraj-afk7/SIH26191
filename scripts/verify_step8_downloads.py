"""Step 8A.1 - Download Verification Script

Performs filesystem and loadability checks on downloaded demographic and spatial files.
Does not inspect full schemas or execute joins.
"""

from datetime import datetime
import os
from pathlib import Path
import sys
import geopandas as gpd
import openpyxl
import pandas as pd

def verify_downloads():
    repo_root = Path(__file__).resolve().parent.parent
    habitations_dir = repo_root / "data" / "raw" / "habitations"
    
    print("=" * 70)
    print("PHASE 4 — DOWNLOAD VERIFICATION AUDIT")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Habitations Directory: {habitations_dir}\n")
    
    if not habitations_dir.exists():
        print(f"ERROR: Directory does not exist: {habitations_dir}")
        return 1
        
    target_files = [
        ("PCA_CDB-0503-F-Census.xlsx", "excel"),
        ("rudraprayag_settlements_osm.geojson", "spatial"),
    ]
    
    all_passed = True
    
    for filename, ftype in target_files:
        full_path = habitations_dir / filename
        rel_path = full_path.relative_to(repo_root)
        
        print(f"File Name: {filename}")
        print(f"Relative Path: {rel_path.as_posix()}")
        print(f"Absolute Path: {full_path}")
        print(f"File Extension: {full_path.suffix}")
        
        exists = full_path.exists()
        print(f"Physically Exists: {exists}")
        
        if not exists:
            print(f"Status: FAILED - File not found on disk\n{'-'*70}")
            all_passed = False
            continue
            
        stat = full_path.stat()
        mod_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
        print(f"File Size (bytes): {stat.st_size}")
        print(f"Last Modified: {mod_time}")
        
        if ftype == "excel":
            try:
                wb = openpyxl.load_workbook(full_path, read_only=True)
                sheets = wb.sheetnames
                wb.close()
                df_test = pd.read_excel(full_path, nrows=5)
                print(f"Open Status: SUCCESS (Workbook loaded, sheets: {sheets}, preview rows: {len(df_test)})")
            except Exception as e:
                print(f"Open Status: FAILED ({e})")
                all_passed = False
        elif ftype == "spatial":
            try:
                gdf_test = gpd.read_file(full_path)
                print(f"Open Status: SUCCESS (GeoDataFrame loaded, features: {len(gdf_test)}, CRS: {gdf_test.crs})")
            except Exception as e:
                print(f"Open Status: FAILED ({e})")
                all_passed = False
                
        print("-" * 70)
        
    print("\n" + "=" * 70)
    if all_passed:
        print("FINAL STATUS: PASS")
        print("Both demographic AND spatial datasets physically downloaded and successfully opened.")
    else:
        print("FINAL STATUS: FAIL")
    print("=" * 70)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(verify_downloads())
