import json
import logging
import pathlib
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
        self.infrastructure = gpd.GeoDataFrame()
        self.infrastructure_summary = {}
        self.disasters = gpd.GeoDataFrame()
        self.disaster_summary = {}
        self.roads = gpd.GeoDataFrame()
        self.road_summary = {}
        self.lulc_summary = {}
        
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

        logger.info("Loading Village Priority Profiles...")
        try:
            self.villages = gpd.read_file("data/processed/decision/village_priority_profiles.gpkg")
            # If CRS is metric, reproject a copy to WGS84 for GeoJSON serialization
            self.villages.sindex
            logger.info(f"Loaded {len(self.villages)} village priority profiles.")
        except Exception as e:
            logger.error(f"Failed to load villages: {e}")

        logger.info("Loading Candidate Red Zones...")
        try:
            self.red_zones = gpd.read_file("data/outputs/candidate_hazard_based_red_zones.geojson")
            self.red_zones.sindex
            logger.info(f"Loaded {len(self.red_zones)} candidate red zones.")
        except Exception as e:
            logger.error(f"Failed to load red zones: {e}")

        logger.info("Loading Candidate Areas (Phase D context-enriched)...")
        try:
            context_path = pathlib.Path("data/processed/decision/candidate_area_context.gpkg")
            attributed_path = pathlib.Path("data/outputs/candidate_topographically_feasible_areas_attributed.geojson")
            if context_path.exists():
                self.candidate_areas = gpd.read_file(str(context_path))
                logger.info(f"Loaded Phase D candidate_area_context.gpkg ({len(self.candidate_areas)} features)")
            else:
                self.candidate_areas = gpd.read_file(str(attributed_path))
                logger.warning("Phase D context file not found -- loaded Step 9C attributed file")
            self.candidate_areas.sindex
        except Exception as e:
            logger.error(f"Failed to load candidate areas: {e}")

        logger.info("Loading Critical Infrastructure Layer...")
        try:
            infra_path = pathlib.Path("data/processed/infrastructure/critical_infrastructure.geojson")
            if infra_path.exists():
                self.infrastructure = gpd.read_file(str(infra_path))
                self.infrastructure.sindex
                logger.info(f"Loaded {len(self.infrastructure)} critical infrastructure facilities.")
            infra_sum_path = pathlib.Path("data/processed/infrastructure/infrastructure_summary.json")
            if infra_sum_path.exists():
                with open(infra_sum_path, "r", encoding="utf-8") as f:
                    self.infrastructure_summary = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load infrastructure: {e}")

        logger.info("Loading Historical Disaster Layer...")
        try:
            dis_path = pathlib.Path("data/processed/disaster_history/historical_disaster_inventory.geojson")
            if dis_path.exists():
                self.disasters = gpd.read_file(str(dis_path))
                self.disasters.sindex
                logger.info(f"Loaded {len(self.disasters)} canonical historical disaster records.")
            dis_sum_path = pathlib.Path("data/processed/disaster_history/disaster_summary.json")
            if dis_sum_path.exists():
                with open(dis_sum_path, "r", encoding="utf-8") as f:
                    self.disaster_summary = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load disasters: {e}")

        logger.info("Loading Road Network Layer...")
        try:
            roads_path = pathlib.Path("data/processed/roads/arterial_roads.geojson")
            if roads_path.exists():
                self.roads = gpd.read_file(str(roads_path))
                self.roads.sindex
                logger.info(f"Loaded {len(self.roads)} arterial road segments.")
            road_sum_path = pathlib.Path("data/processed/roads/road_summary.json")
            if road_sum_path.exists():
                with open(road_sum_path, "r", encoding="utf-8") as f:
                    self.road_summary = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load road network: {e}")

        logger.info("Loading LULC Summary...")
        try:
            lulc_sum_path = pathlib.Path("data/processed/lulc/lulc_summary.json")
            if lulc_sum_path.exists():
                with open(lulc_sum_path, "r", encoding="utf-8") as f:
                    self.lulc_summary = json.load(f)
                logger.info("Loaded LULC exclusion summary.")
        except Exception as e:
            logger.error(f"Failed to load LULC summary: {e}")

data_store = DataLoader()
