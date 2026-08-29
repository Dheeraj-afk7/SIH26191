import { API_ENDPOINTS } from '../config/api';
import { fetchJson } from './apiClient';
import { HazardsResponse, RedZoneFeatureCollection } from '../types/api';

export const hazardService = {
  getHazards: () => fetchJson<HazardsResponse>(API_ENDPOINTS.HAZARDS),
};

export const zoneService = {
  getRedZones: () => fetchJson<RedZoneFeatureCollection>(API_ENDPOINTS.RED_ZONES),
};
