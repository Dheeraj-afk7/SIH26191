"""Step 8A.2 - Verify Actual Downloaded Habitation Files

Inspects the project filesystem for required Census PCA and spatial boundaries datasets.
Does not make assumptions, fabricate data, or proceed with join tests if files are missing.
"""

from datetime import datetime
import os
from pathlib import Path
import sys

def verify_actual_files() -> int:
    repo_root = Path(__file__).resolve().parent.parent
    
    target_files = [
        "data/raw/habitations/DDW_PCA0503_2011_MDDS with UI.xlsx",
        "data/raw/habitations/uttarakhand_villages_datameet_2011.geojson",
    ]
    
    print("=" * 60)
    print("PHASE 1 — FILE EXISTENCE VERIFICATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Working Directory: {repo_root}\n")
    
    all_exist = True
    for rel_path in target_files:
        full_path = repo_root / rel_path
        exists = full_path.exists()
        print(f"Filename: {Path(rel_path).name}")
        print(f"Relative Path: {rel_path}")
        print(f"Absolute Path: {full_path}")
        print(f"File Exists: {exists}")
        
        if exists:
            stat = full_path.stat()
            mod_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
            print(f"File Size: {stat.st_size} bytes")
            print(f"Last Modified: {mod_time}")
        else:
            print("File Size: N/A (file does not exist on disk)")
            print("Last Modified: N/A (file does not exist on disk)")
            all_exist = False
        print("-" * 60)
        
    if not all_exist:
        print("\n" + "=" * 60)
        print("FINAL STATUS: DATA NOT ACTUALLY ACQUIRED")
        print("STOPPING: Cannot proceed to Phase 2 (Census File Inspection),")
        print("Phase 3 (Spatial File Inspection), or Phase 4 (Strict Join Test).")
        print("=" * 60)
        return 1
        
    return 0

if __name__ == "__main__":
    sys.exit(verify_actual_files())
