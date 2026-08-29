import { API_ENDPOINTS } from '../config/api';
import { fetchJson } from './apiClient';
import { CandidateAreaFeatureCollection } from '../types/api';

export interface GetCandidateAreasParams {
  bbox?: string; // min_lon,min_lat,max_lon,max_lat (EPSG:4326)
  limit?: number;
  offset?: number;
}

export const candidateAreaService = {
  getCandidateAreas: (params?: GetCandidateAreasParams) => {
    const url = new URL(API_ENDPOINTS.CANDIDATE_AREAS);
    if (params?.bbox) url.searchParams.append('bbox', params.bbox);
    if (params?.limit !== undefined) url.searchParams.append('limit', params.limit.toString());
    if (params?.offset !== undefined) url.searchParams.append('offset', params.offset.toString());
    return fetchJson<CandidateAreaFeatureCollection>(url.toString());
  },
  getCandidateAreaById: (id: string) => {
    return fetchJson<CandidateAreaFeatureCollection>(API_ENDPOINTS.CANDIDATE_AREA_BY_ID(id));
  },
};
