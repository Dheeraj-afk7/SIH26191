import { API_ENDPOINTS } from '../config/api';
import { fetchJson } from './apiClient';
import { FeatureCollection, LineString, MultiLineString } from 'geojson';

export interface RoadProperties {
  osm_id: string;
  highway: string;
  name: string;
  ref: string;
  surface: string;
  is_arterial: boolean;
  length_m: number;
  assumed_speed_kmh: number;
}

export type RoadFeatureCollection = FeatureCollection<LineString | MultiLineString, RoadProperties>;

export interface RoadSummary {
  project: string;
  total_network_length_km: number;
  arterial_length_km: number;
  assumed_mountain_speeds: Record<string, number>;
  accessibility_tier_thresholds: Record<string, string>;
}

export interface GetRoadParams {
  arterial_only?: boolean;
  limit?: number;
  offset?: number;
}

export const roadService = {
  getRoads: (params?: GetRoadParams): Promise<RoadFeatureCollection> => {
    const url = new URL(API_ENDPOINTS.ROADS);
    if (params?.arterial_only) url.searchParams.append('arterial_only', 'true');
    if (params?.limit !== undefined) url.searchParams.append('limit', params.limit.toString());
    if (params?.offset !== undefined) url.searchParams.append('offset', params.offset.toString());
    return fetchJson<RoadFeatureCollection>(url.toString());
  },

  getSummary: (): Promise<RoadSummary> => {
    return fetchJson<RoadSummary>(API_ENDPOINTS.ROADS_SUMMARY);
  },
};
