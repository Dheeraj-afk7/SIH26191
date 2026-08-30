import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from backend.services.data_loader import data_store

router = APIRouter()

@router.get("/disasters")
def get_historical_disasters(
    hazard_type: Optional[str] = Query(None, description="Filter by hazard type (LANDSLIDE, FLASH_FLOOD_CLOUDBURST)"),
    year_min: Optional[int] = Query(None, description="Minimum event year"),
    year_max: Optional[int] = Query(None, description="Maximum event year"),
    limit: int = 50,
    offset: int = 0
):
    """
    Get GeoJSON of canonical historical disaster events (1998-2024) in Rudraprayag AOI.
    Preserves exact provenance dimensions, fatalities, coordinate uncertainty, and literature citations.
    """
    df = data_store.disasters
    if df.empty:
        raise HTTPException(status_code=404, detail="Historical disaster dataset not loaded.")

    filtered = df.copy()

    if hazard_type:
        filtered = filtered[filtered["hazard_type"].str.upper() == hazard_type.upper()]

    if year_min is not None:
        filtered = filtered[filtered["year"] >= year_min]

    if year_max is not None:
        filtered = filtered[filtered["year"] <= year_max]

    subset = filtered.iloc[offset:offset+limit].copy()
    for col in subset.select_dtypes(include=['datetime64', 'datetimetz']).columns:
        subset[col] = subset[col].astype(str)
    if "date" in subset.columns:
        subset["date"] = subset["date"].astype(str)

    return json.loads(subset.to_json(default=str))


@router.get("/disasters/summary")
def get_disaster_summary():
    """
    Get statistical summary of canonical historical disaster events.
    """
    if not data_store.disaster_summary:
        raise HTTPException(status_code=404, detail="Disaster summary not loaded.")
    return data_store.disaster_summary
