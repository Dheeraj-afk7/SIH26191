import json
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from backend.services.data_loader import data_store
import geopandas as gpd
from shapely.geometry import box

router = APIRouter()

@router.get("/candidate-areas")
def get_candidate_areas(
    bbox: Optional[str] = Query(None, description="Bounding box in format min_lon,min_lat,max_lon,max_lat (EPSG:4326)"),
    limit: int = Query(50, description="Max number of candidate areas to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    df = data_store.candidate_areas
    if df.empty:
        raise HTTPException(status_code=404, detail="Candidate Areas dataset not loaded.")
        
    if bbox:
        try:
            coords = [float(c) for c in bbox.split(",")]
            if len(coords) != 4:
                raise ValueError
            minx, miny, maxx, maxy = coords
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid bbox format. Must be min_lon,min_lat,max_lon,max_lat")
            
        # Create a bounding box polygon in EPSG:4326
        bbox_geom = box(minx, miny, maxx, maxy)
        bbox_gdf = gpd.GeoDataFrame({'geometry': [bbox_geom]}, crs="EPSG:4326")
        
        # Project bbox to df CRS if they differ (GeoJSON standard is 4326, but sometimes it retains original CRS metadata)
        if df.crs and df.crs != "EPSG:4326":
            bbox_gdf = bbox_gdf.to_crs(df.crs)
            
        # Spatial filter using cx (bounding box intersection)
        geom = bbox_gdf.iloc[0].geometry
        df = df.cx[geom.bounds[0]:geom.bounds[2], geom.bounds[1]:geom.bounds[3]]

    # Ensure limit is reasonable
    limit = min(limit, 500)
    subset = df.iloc[offset:offset+limit]
    
    return json.loads(subset.to_json())

@router.get("/candidate-areas/{area_id}")
def get_candidate_area_by_id(area_id: str):
    df = data_store.candidate_areas
    if df.empty:
        raise HTTPException(status_code=404, detail="Candidate Areas dataset not loaded.")
        
    area = df[df['area_id'] == area_id]
    if area.empty:
        raise HTTPException(status_code=404, detail=f"Candidate Area with id {area_id} not found.")
        
    return json.loads(area.to_json())
