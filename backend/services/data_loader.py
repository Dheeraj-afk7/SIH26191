import json
import logging
import geopandas as gpd
import pandas as pd
from backend.core.config import settings

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(self):
        self.decision_summary = {}
        self.decision_metadata = {}
        self.villages = gpd.GeoDataFrame()
        self.red_zones = gpd.GeoDataFrame()
        self.candidate_areas = gpd.GeoDataFrame()
        
    def load_all(self):
        logger.info("Loading Decision Metadata...")
        try:
            with open("data/processed/decision/decision_metadata.json", "r", encoding="utf-8") as f:
                self.decision_metadata = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load decision metadata: {e}")

        logger.info("Loading Decision Summary...")
        try:
            with open("data/processed/decision/decision_summary.json", "r", encoding="utf-8") as f:
                self.decision_summary = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load decision summary: {e}")

        logger.info("Loading Village Profiles...")
        try:
            self.villages = gpd.read_file("data/processed/decision/village_priority_profiles.gpkg")
            # Create a spatial index for bbox queries
            self.villages.sindex
        except Exception as e:
            logger.error(f"Failed to load villages: {e}")

        logger.info("Loading Candidate Red Zones...")
        try:
            self.red_zones = gpd.read_file("data/outputs/candidate_hazard_based_red_zones.geojson")
            self.red_zones.sindex
        except Exception as e:
            logger.error(f"Failed to load red zones: {e}")

        logger.info("Loading Candidate Areas (approx 15MB)...")
        try:
            self.candidate_areas = gpd.read_file("data/outputs/candidate_topographically_feasible_areas_attributed.geojson")
            self.candidate_areas.sindex
        except Exception as e:
            logger.error(f"Failed to load candidate areas: {e}")
            
data_store = DataLoader()
