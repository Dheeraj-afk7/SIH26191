import json
from fastapi import APIRouter, HTTPException
from backend.services.data_loader import data_store

router = APIRouter()

@router.get("/lulc/summary")
def get_lulc_summary():
    """
    Get ESA WorldCover LULC exclusion statistics and breakdown.
    """
    if not data_store.lulc_summary:
        raise HTTPException(status_code=404, detail="LULC summary not loaded.")
    return data_store.lulc_summary
