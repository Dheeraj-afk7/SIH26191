import { useQuery } from '@tanstack/react-query';
import { systemService } from '../services/systemService';
import { decisionService } from '../services/decisionService';
import { villageService, GetVillagesParams } from '../services/villageService';
import { candidateAreaService, GetCandidateAreasParams } from '../services/candidateAreaService';
import { zoneService, hazardService } from '../services/hazardService';
import { infrastructureService, GetInfrastructureParams } from '../services/infrastructureService';
import { disasterService, GetDisasterParams } from '../services/disasterService';
import { roadService, GetRoadParams } from '../services/roadService';
import { lulcService } from '../services/lulcService';

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
  infrastructure: (params?: GetInfrastructureParams) => ['infrastructure', params] as const,
  infrastructureSummary: ['infrastructure', 'summary'] as const,
  disasters: (params?: GetDisasterParams) => ['disasters', params] as const,
  disasterSummary: ['disasters', 'summary'] as const,
  roads: (params?: GetRoadParams) => ['roads', params] as const,
  roadSummary: ['roads', 'summary'] as const,
  lulcSummary: ['lulc', 'summary'] as const,
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

export function useInfrastructure(params?: GetInfrastructureParams) {
  return useQuery({
    queryKey: QUERY_KEYS.infrastructure(params),
    queryFn: () => infrastructureService.getInfrastructure(params),
    staleTime: 10 * 60 * 1000,
  });
}

export function useInfrastructureSummary() {
  return useQuery({
    queryKey: QUERY_KEYS.infrastructureSummary,
    queryFn: infrastructureService.getSummary,
    staleTime: 10 * 60 * 1000,
  });
}

export function useDisasters(params?: GetDisasterParams) {
  return useQuery({
    queryKey: QUERY_KEYS.disasters(params),
    queryFn: () => disasterService.getDisasters(params),
    staleTime: 10 * 60 * 1000,
  });
}

export function useDisasterSummary() {
  return useQuery({
    queryKey: QUERY_KEYS.disasterSummary,
    queryFn: disasterService.getSummary,
    staleTime: 10 * 60 * 1000,
  });
}

export function useRoads(params?: GetRoadParams) {
  return useQuery({
    queryKey: QUERY_KEYS.roads(params),
    queryFn: () => roadService.getRoads(params),
    staleTime: 10 * 60 * 1000,
  });
}

export function useRoadSummary() {
  return useQuery({
    queryKey: QUERY_KEYS.roadSummary,
    queryFn: roadService.getSummary,
    staleTime: 10 * 60 * 1000,
  });
}

export function useLulcSummary() {
  return useQuery({
    queryKey: QUERY_KEYS.lulcSummary,
    queryFn: lulcService.getSummary,
    staleTime: 10 * 60 * 1000,
  });
}
