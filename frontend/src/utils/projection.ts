/**
 * SIH26191 GIS Coordinate Reprojection Utility
 * 
 * Accurately transforms geospatial coordinates from projected metric CRS
 * EPSG:32644 (WGS 84 / UTM Zone 44N) to geographic CRS EPSG:4326 (WGS 84 Decimal Degrees)
 * for Leaflet rendering.
 */

import proj4 from 'proj4';

// Define UTM Zone 44N projection
proj4.defs(
  'EPSG:32644',
  '+proj=utm +zone=44 +datum=WGS84 +units=m +no_defs +type=crs'
);

/**
 * Transforms a single [x, y] / [lon, lat] coordinate pair.
 * If coordinates are in UTM (>180), reprojects from EPSG:32644 to EPSG:4326.
 * Returns [lon, lat] in EPSG:4326 decimal degrees.
 */
export function reprojectCoord(coord: [number, number]): [number, number] {
  const [x, y] = coord;
  // If coordinates are larger than 180, they are in metric UTM Zone 44N
  if (Math.abs(x) > 180 || Math.abs(y) > 90) {
    const [lon, lat] = proj4('EPSG:32644', 'EPSG:4326', [x, y]);
    return [lon, lat];
  }
  return [x, y];
}

/**
 * Returns [lat, lon] tuple for Leaflet center / marker positioning
 */
export function toLeafletLatLng(coord: [number, number]): [number, number] {
  const [lon, lat] = reprojectCoord(coord);
  return [lat, lon];
}

/**
 * Recursively projects coordinates array within any GeoJSON geometry type
 */
function projectGeometryCoordinates(coords: any, type: string): any {
  if (type === 'Point') {
    return reprojectCoord(coords);
  }
  if (type === 'LineString' || type === 'MultiPoint') {
    return coords.map((pt: [number, number]) => reprojectCoord(pt));
  }
  if (type === 'Polygon' || type === 'MultiLineString') {
    return coords.map((ring: [number, number][]) =>
      ring.map((pt: [number, number]) => reprojectCoord(pt))
    );
  }
  if (type === 'MultiPolygon') {
    return coords.map((poly: [number, number][][]) =>
      poly.map((ring: [number, number][]) =>
        ring.map((pt: [number, number]) => reprojectCoord(pt))
      )
    );
  }
  return coords;
}

/**
 * Deep-projects an entire GeoJSON FeatureCollection, Feature, or Geometry object to EPSG:4326
 */
export function reprojectGeoJson<T = any>(geojson: T): T {
  if (!geojson) return geojson;
  const clone = JSON.parse(JSON.stringify(geojson));

  const transformFeature = (feature: any) => {
    if (feature?.geometry?.coordinates) {
      feature.geometry.coordinates = projectGeometryCoordinates(
        feature.geometry.coordinates,
        feature.geometry.type
      );
    }
  };

  if ((clone as any).type === 'FeatureCollection' && Array.isArray((clone as any).features)) {
    (clone as any).features.forEach(transformFeature);
  } else if ((clone as any).type === 'Feature') {
    transformFeature(clone);
  } else if ((clone as any).coordinates && (clone as any).type) {
    (clone as any).coordinates = projectGeometryCoordinates((clone as any).coordinates, (clone as any).type);
  }

  return clone;
}
