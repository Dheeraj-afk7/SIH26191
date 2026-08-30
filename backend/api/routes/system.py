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
            "candidate_areas": not data_store.candidate_areas.empty,
            "infrastructure": not data_store.infrastructure.empty,
            "disasters": not data_store.disasters.empty,
            "roads": not data_store.roads.empty,
        }
    }

@router.get("/metadata")
def get_metadata():
    return {
        "project_metadata": settings.project_config.get("project", {}),
        "crs": settings.project_config.get("crs", {}),
        "methodology_status": data_store.decision_metadata.get("methodology_status", "Decision engine applied deterministic rules."),
        "provenance_layers": {
            "phase1_lulc": "ESA WorldCover 10m 2021 v200 categorical reprojection to EPSG:32644",
            "phase2_roads": "OpenStreetMap 6,397.3 km routable graph with metric speeds in EPSG:32644",
            "phase3_disasters": "Literature Curated Historical Disaster Inventory (22 events 1998-2024, 6,913 fatalities)",
            "phase4_infrastructure": "OpenStreetMap Critical Infrastructure Directory (291 facilities with explicit emergency semantics)",
        },
        "decision_support_disclaimer": settings.project_config.get("terminology", {}).get(
            "decision_support_disclaimer", 
            "Decision Support — Requires Official Verification & Geotechnical Assessment"
        )
    }
