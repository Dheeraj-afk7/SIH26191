from fastapi import APIRouter
import os
from backend.core.config import settings

router = APIRouter()

@router.get("/hazards")
def get_hazards():
    """
    Returns metadata about hazard layers, distinguishing between what is 
    configured in project.yaml and what is actually available in the outputs directory.
    """
    hazards_dir = "data/processed/hazards"
    available_files = set()
    if os.path.exists(hazards_dir):
        available_files = set(os.listdir(hazards_dir))
        
    # Build a metadata response incorporating config and actual files
    terrain_cfg = settings.project_config.get("terrain_susceptibility", {})
    hydro_cfg = settings.project_config.get("hydrology", {})
    mh_cfg = settings.project_config.get("multihazard", {})
    
    def check_status(filename):
        if not filename:
            return "NOT_CONFIGURED"
        basename = os.path.basename(filename)
        if basename in available_files:
            return "AVAILABLE"
        return "CONFIGURED_BUT_MISSING"

    return {
        "metadata": {
            "disclaimer": "Do NOT expose huge rasters directly. For visualization, rely on map servers like GeoServer or Mapbox.",
            "crs": settings.project_config.get("crs", {}).get("analysis_crs_metric", "EPSG:32644")
        },
        "layers": {
            "terrain_susceptibility_proxy": {
                "name": terrain_cfg.get("output", {}).get("proxy_name", "Terrain-Derived Landslide Susceptibility Proxy"),
                "status": check_status(settings.project_config.get("paths", {}).get("terrain_susceptibility_proxy")),
                "file": "terrain_susceptibility_proxy.tif",
                "description": terrain_cfg.get("description", "")
            },
            "terrain_susceptibility_classes": {
                "name": terrain_cfg.get("output", {}).get("classes_name", "Terrain-Derived Landslide Susceptibility Screening Classes"),
                "status": check_status(settings.project_config.get("paths", {}).get("terrain_susceptibility_classes")),
                "file": "terrain_susceptibility_classes.tif"
            },
            "flood_exposure_proxy": {
                "name": hydro_cfg.get("labels", {}).get("proxy_name", "Terrain-Derived Flood Exposure Proxy"),
                "status": check_status(settings.project_config.get("paths", {}).get("flood_exposure_proxy")),
                "file": "flood_exposure_proxy.tif",
                "description": hydro_cfg.get("description", "")
            },
            "flood_exposure_classes": {
                "name": hydro_cfg.get("labels", {}).get("classes_name", "Terrain-Derived Flood Exposure Screening Classes"),
                "status": check_status(settings.project_config.get("paths", {}).get("flood_exposure_classes")),
                "file": "flood_exposure_classes.tif"
            },
            "multihazard_score": {
                "name": mh_cfg.get("labels", {}).get("indicator_name", "Multi-Hazard Screening Score"),
                "status": check_status(settings.project_config.get("paths", {}).get("multihazard_score")),
                "file": "multihazard_score.tif",
                "description": mh_cfg.get("description", "")
            },
            "multihazard_classes": {
                "name": mh_cfg.get("labels", {}).get("classes_name", "Multi-Hazard Screening Classes"),
                "status": check_status(settings.project_config.get("paths", {}).get("multihazard_classes")),
                "file": "multihazard_classes.tif"
            },
            "candidate_redzone_raster": {
                "name": "Candidate Hazard-Based Red Zone Raster",
                "status": check_status(settings.project_config.get("paths", {}).get("redzones_raster")),
                "file": "candidate_redzone_raster.tif"
            }
        },
        "available_files_in_directory": list(available_files)
    }
