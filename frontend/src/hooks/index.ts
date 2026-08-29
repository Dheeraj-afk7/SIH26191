import { useQuery } from '@tanstack/react-query';
import { systemService } from '../services/systemService';
import { decisionService } from '../services/decisionService';
import { villageService, GetVillagesParams } from '../services/villageService';
import { candidateAreaService, GetCandidateAreasParams } from '../services/candidateAreaService';
import { zoneService, hazardService } from '../services/hazardService';

export const QUERY_KEYS = {
  health: ['health'] as const,
  metadata: ['metadata'] as const,
  decisionSummary: ['decision', 'summary'] as const,
  decisionMetadata: ['decision', 'metadata'] as const,
  villages: (params?: GetVillagesParams) => ['villages', params] as const,
  village: (id: number | string) => ['village', id] as const,
  redZones: ['red-zones'] as const,
  candidateAreas: (params?: GetCandidateAreasParams) => ['candidate-areas', params] as const,
  candidateArea: (id: string) => ['candidate-area', id] as const,
  hazards: ['hazards'] as const,
};

export function useHealth() {
  return useQuery({
    queryKey: QUERY_KEYS.health,
    queryFn: systemService.getHealth,
    staleTime: 60 * 1000,
  });
}

export function useMetadata() {
  return useQuery({
    queryKey: QUERY_KEYS.metadata,
    queryFn: systemService.getMetadata,
    staleTime: 5 * 60 * 1000,
  });
}

export function useDecisionSummary() {
  return useQuery({
    queryKey: QUERY_KEYS.decisionSummary,
    queryFn: decisionService.getSummary,
    staleTime: 5 * 60 * 1000,
  });
}

export function useDecisionMetadata() {
  return useQuery({
    queryKey: QUERY_KEYS.decisionMetadata,
    queryFn: decisionService.getMetadata,
    staleTime: 5 * 60 * 1000,
  });
}

export function useVillages(params?: GetVillagesParams) {
  return useQuery({
    queryKey: QUERY_KEYS.villages(params),
    queryFn: () => villageService.getVillages(params),
    staleTime: 5 * 60 * 1000,
  });
}

export function useVillage(id: number | string) {
  return useQuery({
    queryKey: QUERY_KEYS.village(id),
    queryFn: () => villageService.getVillageById(id),
    enabled: Boolean(id),
  });
}

export function useRedZones() {
  return useQuery({
    queryKey: QUERY_KEYS.redZones,
    queryFn: zoneService.getRedZones,
    staleTime: 10 * 60 * 1000,
  });
}

export function useCandidateAreas(params?: GetCandidateAreasParams) {
  return useQuery({
    queryKey: QUERY_KEYS.candidateAreas(params),
    queryFn: () => candidateAreaService.getCandidateAreas(params),
    staleTime: 10 * 60 * 1000,
  });
}

export function useHazards() {
  return useQuery({
    queryKey: QUERY_KEYS.hazards,
    queryFn: hazardService.getHazards,
    staleTime: 5 * 60 * 1000,
  });
}
