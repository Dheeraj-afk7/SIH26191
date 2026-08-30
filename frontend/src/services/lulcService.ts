import { API_ENDPOINTS } from '../config/api';
import { fetchJson } from './apiClient';

export interface LulcSummary {
  project: string;
  source_dataset: string;
  grid_resolution_m: number;
  total_district_area_ha: number;
  ecological_exclusion_ha: number;
  ecological_exclusion_pct: number;
  ecological_permissible_ha: number;
  ecological_permissible_pct: number;
  exclusion_breakdown: Record<string, { hectares: number; percentage: number }>;
}

export const lulcService = {
  getSummary: (): Promise<LulcSummary> => {
    return fetchJson<LulcSummary>(API_ENDPOINTS.LULC_SUMMARY);
  },
};
