from fastapi import APIRouter, HTTPException
from backend.services.data_loader import data_store

router = APIRouter()

@router.get("/summary")
def get_decision_summary():
    if not data_store.decision_summary:
        raise HTTPException(status_code=404, detail="Decision summary not found.")
    return data_store.decision_summary

@router.get("/metadata")
def get_decision_metadata():
    if not data_store.decision_metadata:
        raise HTTPException(status_code=404, detail="Decision metadata not found.")
    return data_store.decision_metadata
