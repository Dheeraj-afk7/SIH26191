import { API_ENDPOINTS } from '../config/api';
import { fetchJson } from './apiClient';
import { SystemHealth, ProjectMetadata } from '../types/api';

export const systemService = {
  getHealth: () => fetchJson<SystemHealth>(API_ENDPOINTS.HEALTH),
  getMetadata: () => fetchJson<ProjectMetadata>(API_ENDPOINTS.METADATA),
};
