import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from backend.services.data_loader import data_store

router = APIRouter()

@router.get("/infrastructure")
def get_infrastructure(
    broad_type: Optional[str] = Query(None, description="Filter by broad type (HEALTHCARE, EDUCATION, EMERGENCY, CIVIC_ADMINISTRATIVE)"),
    category: Optional[str] = Query(None, description="Filter by specific category (e.g. HEALTHCARE_HOSPITAL, HEALTHCARE_PHC, EDUCATION_SCHOOL)"),
    emergency_only: Optional[bool] = Query(False, description="Filter for emergency capable/potential receiving facilities"),
    limit: int = 350,
    offset: int = 0
):
    """
    Get GeoJSON of critical infrastructure facilities within Rudraprayag pilot AOI.
    Preserves native OSM IDs, coordinates, facility categories, and emergency capability semantics.
    """
    df = data_store.infrastructure
    if df.empty:
        raise HTTPException(status_code=404, detail="Critical infrastructure dataset not loaded.")

    filtered = df.copy()

    if broad_type:
        filtered = filtered[filtered["facility_broad_type"].str.upper() == broad_type.upper()]

    if category:
        filtered = filtered[filtered["facility_category"].str.upper() == category.upper()]

    if emergency_only:
        filtered = filtered[
            (filtered["explicitly_evidenced_emergency_capability"] == True) |
            (filtered["potential_emergency_receiving_facility"] == True)
        ]

    subset = filtered.iloc[offset:offset+limit].copy()
    for col in subset.select_dtypes(include=['datetime64', 'datetimetz']).columns:
        subset[col] = subset[col].astype(str)
    if "acquisition_date" in subset.columns:
        subset["acquisition_date"] = subset["acquisition_date"].astype(str)

    return json.loads(subset.to_json(default=str))


@router.get("/infrastructure/summary")
def get_infrastructure_summary():
    """
    Get summary statistics and category breakdown of critical infrastructure.
    """
    if not data_store.infrastructure_summary:
        raise HTTPException(status_code=404, detail="Infrastructure summary not loaded.")
    return data_store.infrastructure_summary
