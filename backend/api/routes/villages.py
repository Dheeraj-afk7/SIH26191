import json
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.services.data_loader import data_store
import geopandas as gpd
from shapely.geometry import box

router = APIRouter()

@router.get("")
def get_villages(
    priority_tier: Optional[str] = Query(None, description="Filter by priority tier (e.g. Tier1_AttentionPriority)"),
    name: Optional[str] = Query(None, description="Search by village name"),
    limit: int = 100,
    offset: int = 0
):
    df = data_store.villages
    if df.empty:
        raise HTTPException(status_code=404, detail="Villages dataset not loaded.")
        
    if priority_tier:
        valid_tiers = ['Tier1_AttentionPriority', 'Tier2_ElevatedAttention', 'Tier3_Monitoring', 'BeyondProximity']
        if priority_tier not in valid_tiers:
            raise HTTPException(status_code=422, detail=f"Invalid priority_tier. Must be one of {valid_tiers}")
        df = df[df['priority_tier'] == priority_tier]
        
    if name:
        df = df[df['village_name'].str.contains(name, case=False, na=False)]
        
    subset = df.iloc[offset:offset+limit]
    
    # Return as GeoJSON
    return json.loads(subset.to_json())

@router.get("/{village_id}")
def get_village_by_id(village_id: int):
    df = data_store.villages
    if df.empty:
        raise HTTPException(status_code=404, detail="Villages dataset not loaded.")
        
    village = df[df['village_id'] == village_id]
    if village.empty:
        raise HTTPException(status_code=404, detail=f"Village with id {village_id} not found.")
        
    return json.loads(village.to_json())
