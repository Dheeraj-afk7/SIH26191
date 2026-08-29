import json
from fastapi import APIRouter, HTTPException
from backend.services.data_loader import data_store

router = APIRouter()

@router.get("/red-zones")
def get_red_zones():
    df = data_store.red_zones
    if df.empty:
        raise HTTPException(status_code=404, detail="Candidate Hazard-Based Red Zones dataset not loaded.")
    
    return json.loads(df.to_json())
