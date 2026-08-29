from fastapi import APIRouter
from backend.services.data_loader import data_store
from backend.core.config import settings
import json

router = APIRouter()

@router.get("/health")
def get_health():
    return {
        "status": "ok",
        "api_version": settings.api_version,
        "datasets_loaded": {
            "decision_metadata": bool(data_store.decision_metadata),
            "decision_summary": bool(data_store.decision_summary),
            "villages": not data_store.villages.empty,
            "red_zones": not data_store.red_zones.empty,
            "candidate_areas": not data_store.candidate_areas.empty
        }
    }

@router.get("/metadata")
def get_metadata():
    return {
        "project_metadata": settings.project_config.get("project", {}),
        "crs": settings.project_config.get("crs", {}),
        "methodology_status": data_store.decision_metadata.get("methodology_status", "Decision engine applied deterministic rules."),
        "major_limitations": "Does not account for detailed geotechnical studies or real-time hazards. Historical disaster integration pending.",
        "decision_support_disclaimer": settings.project_config.get("terminology", {}).get(
            "decision_support_disclaimer", 
            "Decision Support \u2014 Requires Official Verification & Geotechnical Assessment"
        )
    }
