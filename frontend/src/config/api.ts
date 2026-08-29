/**
 * SIH26191 Backend API Configuration
 * 
 * Default backend port is 8000.
 * In development, requests can target http://localhost:8000 directly.
 */

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export const API_ENDPOINTS = {
  HEALTH: `${API_BASE_URL}/api/health`,
  METADATA: `${API_BASE_URL}/api/metadata`,
  DECISION_SUMMARY: `${API_BASE_URL}/api/decision/summary`,
  DECISION_METADATA: `${API_BASE_URL}/api/decision/metadata`,
  VILLAGES: `${API_BASE_URL}/api/villages`,
  VILLAGE_BY_ID: (id: number | string) => `${API_BASE_URL}/api/villages/${id}`,
  RED_ZONES: `${API_BASE_URL}/api/red-zones`,
  CANDIDATE_AREAS: `${API_BASE_URL}/api/candidate-areas`,
  CANDIDATE_AREA_BY_ID: (id: string) => `${API_BASE_URL}/api/candidate-areas/${id}`,
  HAZARDS: `${API_BASE_URL}/api/hazards`,
} as const;
