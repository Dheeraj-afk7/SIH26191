import { API_ENDPOINTS } from '../config/api';
import { fetchJson } from './apiClient';
import { VillageFeatureCollection } from '../types/api';
import { PriorityTierKey } from '../config/constants';

export interface GetVillagesParams {
  priority_tier?: PriorityTierKey;
  name?: string;
  limit?: number;
  offset?: number;
}

export const villageService = {
  getVillages: (params?: GetVillagesParams) => {
    const url = new URL(API_ENDPOINTS.VILLAGES);
    if (params?.priority_tier) url.searchParams.append('priority_tier', params.priority_tier);
    if (params?.name) url.searchParams.append('name', params.name);
    if (params?.limit !== undefined) url.searchParams.append('limit', params.limit.toString());
    if (params?.offset !== undefined) url.searchParams.append('offset', params.offset.toString());
    return fetchJson<VillageFeatureCollection>(url.toString());
  },
  getVillageById: (id: number | string) => {
    return fetchJson<VillageFeatureCollection>(API_ENDPOINTS.VILLAGE_BY_ID(id));
  },
};
