import { API_ENDPOINTS } from '../config/api';
import { fetchJson } from './apiClient';
import { FeatureCollection, Point } from 'geojson';

export interface DisasterProperties {
  canonical_incident_id: string;
  source_native_id: string | null;
  source_provider: string;
  hazard_type: string;
  date: string;
  year: number;
  location_name: string;
  fatalities: number;
  injuries: number;
  households_affected: number;
  damage_description: string;
  coordinate_uncertainty_m: number;
  uncertainty_band: string;
  evidence_level: string;
  source_document_title: string;
}

export type DisasterFeatureCollection = FeatureCollection<Point, DisasterProperties>;

export interface DisasterSummary {
  project: string;
  total_canonical_events: number;
  total_fatalities_recorded: number;
  total_households_affected: number;
  temporal_range: string;
  hazard_type_breakdown: Record<string, number>;
  source_provider_breakdown: Record<string, number>;
  methodological_disclaimer: string;
}

export interface GetDisasterParams {
  hazard_type?: string;
  year_min?: number;
  year_max?: number;
  limit?: number;
  offset?: number;
}

export const disasterService = {
  getDisasters: (params?: GetDisasterParams): Promise<DisasterFeatureCollection> => {
    const url = new URL(API_ENDPOINTS.DISASTERS);
    if (params?.hazard_type) url.searchParams.append('hazard_type', params.hazard_type);
    if (params?.year_min !== undefined) url.searchParams.append('year_min', params.year_min.toString());
    if (params?.year_max !== undefined) url.searchParams.append('year_max', params.year_max.toString());
    if (params?.limit !== undefined) url.searchParams.append('limit', params.limit.toString());
    if (params?.offset !== undefined) url.searchParams.append('offset', params.offset.toString());
    return fetchJson<DisasterFeatureCollection>(url.toString());
  },

  getSummary: (): Promise<DisasterSummary> => {
    return fetchJson<DisasterSummary>(API_ENDPOINTS.DISASTER_SUMMARY);
  },
};
