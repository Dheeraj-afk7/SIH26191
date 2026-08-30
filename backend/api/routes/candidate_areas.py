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
    limit: int = Query(20, description="Max number of candidate areas to return (default 20, max 500)"),
    offset: int = Query(0, description="Offset for pagination"),
    sort_by_area: bool = Query(True, description="Sort by area descending (largest first). Default True for decision-support use."),
    min_area_ha: Optional[float] = Query(None, description="Filter to areas >= this size in hectares"),
    max_area_ha: Optional[float] = Query(None, description="Filter to areas <= this size in hectares"),
    viable_only: bool = Query(False, description="If True, return only areas with PRELIMINARY_CAPACITY_SCENARIO status"),
):
    df = data_store.candidate_areas
    if df.empty:
        raise HTTPException(status_code=404, detail="Candidate Areas dataset not loaded.")

    total_count = len(df)

    if bbox:
        try:
            coords = [float(c) for c in bbox.split(",")]
            if len(coords) != 4:
                raise ValueError
            minx, miny, maxx, maxy = coords
        except Exception:
            raise HTTPException(status_code=422, detail="Invalid bbox format. Must be min_lon,min_lat,max_lon,max_lat")

        bbox_geom = box(minx, miny, maxx, maxy)
        bbox_gdf = gpd.GeoDataFrame({'geometry': [bbox_geom]}, crs="EPSG:4326")
        if df.crs and df.crs != "EPSG:4326":
            bbox_gdf = bbox_gdf.to_crs(df.crs)
        geom = bbox_gdf.iloc[0].geometry
        df = df.cx[geom.bounds[0]:geom.bounds[2], geom.bounds[1]:geom.bounds[3]]

    # Area filters
    if min_area_ha is not None and "area_hectares" in df.columns:
        df = df[df["area_hectares"] >= min_area_ha]
    if max_area_ha is not None and "area_hectares" in df.columns:
        df = df[df["area_hectares"] <= max_area_ha]

    # Viable-only filter (capacity estimated, not terrain-zone-scale)
    if viable_only and "capacity_status" in df.columns:
        df = df[df["capacity_status"] == "PRELIMINARY_CAPACITY_SCENARIO"]

    # Sort by area descending by default -- surfaces most relevant areas first
    if sort_by_area and "area_m2" in df.columns:
        df = df.sort_values("area_m2", ascending=False)

    # Cap limit
    limit = min(limit, 500)
    filtered_count = len(df)
    subset = df.iloc[offset:offset+limit]

    # Build response with screening metadata injected at top level
    features = json.loads(subset.to_json())
    response = {
        "type": "FeatureCollection",
        "screening_summary": {
            "total_polygons_identified": total_count,
            "displayed_count": len(subset),
            "filtered_count": filtered_count,
            "note": (
                f"{total_count} raw terrain polygons identified meeting slope "
                f"(<= 20 deg), hazard, and flood exclusion criteria. "
                f"Sorted by area descending (largest first). "
                f"All require field verification before any planning use."
            ),
            "disclaimer": (
                "PRELIMINARY DECISION-SUPPORT CANDIDATES -- Not official site authorizations. "
                "Geotechnical, land ownership, and legal clearances required."
            ),
        },
        "features": features.get("features", []),
    }
    return response


@router.get("/candidate-areas/{area_id}")
def get_candidate_area_by_id(area_id: str):
    df = data_store.candidate_areas
    if df.empty:
        raise HTTPException(status_code=404, detail="Candidate Areas dataset not loaded.")

    area = df[df['area_id'] == area_id]
    if area.empty:
        raise HTTPException(status_code=404, detail=f"Candidate Area with id {area_id} not found.")

    return json.loads(area.to_json())
