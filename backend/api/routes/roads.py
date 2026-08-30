import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from backend.services.data_loader import data_store

router = APIRouter()

@router.get("/roads")
def get_roads(
    arterial_only: Optional[bool] = Query(True, description="Filter for primary arterial highway corridors"),
    limit: int = 500,
    offset: int = 0
):
    """
    Get GeoJSON of road network segments in Rudraprayag AOI.
    """
    df = data_store.roads
    if df.empty:
        raise HTTPException(status_code=404, detail="Road network dataset not loaded.")

    filtered = df.copy()
    if arterial_only and "is_arterial" in filtered.columns:
        filtered = filtered[filtered["is_arterial"] == True]

    subset = filtered.iloc[offset:offset+limit]
    return json.loads(subset.to_json())


@router.get("/roads/summary")
def get_road_summary():
    """
    Get summary statistics and mountain accessibility assumptions of road network.
    """
    if not data_store.road_summary:
        raise HTTPException(status_code=404, detail="Road network summary not loaded.")
    return data_store.road_summary
