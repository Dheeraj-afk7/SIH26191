import sys
import os
import requests
import time
import subprocess
import json

def test_endpoints():
    base_url = "http://localhost:8000/api"
    errors = []
    
    # Wait for server to be up
    time.sleep(10)
    
    endpoints = [
        "/health",
        "/metadata",
        "/decision/summary",
        "/decision/metadata",
        "/villages?limit=5",
        "/villages?priority_tier=Tier1_AttentionPriority&limit=1",
        "/red-zones",
        "/candidate-areas?limit=2",
        "/candidate-areas?bbox=78.8,30.4,79.2,30.7",
        "/hazards"
    ]
    
    print("Running Validation Tests...\n")
    
    for ep in endpoints:
        url = f"{base_url}{ep}"
        try:
            resp = requests.get(url)
            if resp.status_code == 200:
                print(f"[PASS] {ep}")
            else:
                print(f"[FAIL] {ep} returned {resp.status_code}")
                errors.append((ep, resp.status_code))
        except Exception as e:
            print(f"[FAIL] {ep} generated exception: {e}")
            errors.append((ep, str(e)))

    # Test 404
    try:
        resp = requests.get(f"{base_url}/villages/999999")
        if resp.status_code == 404:
            print(f"[PASS] /villages/999999 (404 expected)")
        else:
            print(f"[FAIL] /villages/999999 returned {resp.status_code} instead of 404")
            errors.append(("/villages/999999", resp.status_code))
    except Exception as e:
        print(f"[FAIL] 404 test generated exception: {e}")

    # Test Validation Error
    try:
        resp = requests.get(f"{base_url}/villages?priority_tier=InvalidTier")
        if resp.status_code == 422:
            print(f"[PASS] Invalid priority_tier (422 expected)")
        else:
            print(f"[FAIL] Invalid priority_tier returned {resp.status_code} instead of 422")
            errors.append(("Invalid priority_tier", resp.status_code))
    except Exception as e:
        print(f"[FAIL] 422 test generated exception: {e}")

    if errors:
        print("\nValidation completed with ERRORS:")
        for ep, err in errors:
            print(f" - {ep}: {err}")
        return False
    else:
        print("\nAll API endpoints validated successfully!")
        return True

if __name__ == "__main__":
    print("Starting API Server in background...")
    proc = subprocess.Popen(["python", "-m", "backend.main"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    
    try:
        success = test_endpoints()
    finally:
        print("Stopping API Server...")
        proc.terminate()
        proc.wait()
    
    if not success:
        sys.exit(1)
