import { API_ENDPOINTS } from '../config/api';
import { fetchJson } from './apiClient';
import { DecisionSummary, DecisionMetadata } from '../types/api';

export const decisionService = {
  getSummary: () => fetchJson<DecisionSummary>(API_ENDPOINTS.DECISION_SUMMARY),
  getMetadata: () => fetchJson<DecisionMetadata>(API_ENDPOINTS.DECISION_METADATA),
};
