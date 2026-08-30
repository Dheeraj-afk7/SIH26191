import { API_ENDPOINTS } from '../config/api';
import { fetchJson } from './apiClient';
import { FeatureCollection, Point } from 'geojson';

export interface InfrastructureProperties {
  facility_id: string;
  osm_id: string;
  name: string;
  facility_broad_type: 'HEALTHCARE' | 'EDUCATION' | 'EMERGENCY' | 'CIVIC_ADMINISTRATIVE';
  facility_category: string;
  explicitly_evidenced_emergency_capability: boolean;
  potential_emergency_receiving_facility: boolean;
  classification_trigger: string;
  amenity_tag: string;
  healthcare_tag: string;
  building_tag: string;
  office_tag: string;
  source_provider: string;
  acquisition_date: string;
  latitude_wgs84: number;
  longitude_wgs84: number;
}

export type InfrastructureFeatureCollection = FeatureCollection<Point, InfrastructureProperties>;

export interface InfrastructureSummary {
  project: string;
  pipeline_phase: string;
  source_provider: string;
  total_critical_facilities: number;
  emergency_capability_breakdown: {
    explicitly_evidenced_emergency_facilities: number;
    potential_emergency_receiving_clinical_facilities: number;
    routine_healthcare_and_civic_facilities: number;
  };
  facility_broad_type_breakdown: Record<string, number>;
  facility_category_breakdown: Record<string, number>;
  habitation_accessibility_summary: {
    total_habitations: number;
    mean_dist_to_health_facility_m: number;
    mean_dist_to_hospital_chc_m: number;
    mean_dist_to_school_m: number;
    habitations_with_health_under_5km: number;
    habitations_with_school_under_3km: number;
    habitations_with_hospital_chc_under_60min: number;
  };
  education_completeness_statement: string;
  methodological_safeguard: string;
}

export interface GetInfrastructureParams {
  broad_type?: string;
  category?: string;
  emergency_only?: boolean;
  limit?: number;
  offset?: number;
}

export const infrastructureService = {
  getInfrastructure: (params?: GetInfrastructureParams): Promise<InfrastructureFeatureCollection> => {
    const url = new URL(API_ENDPOINTS.INFRASTRUCTURE);
    if (params?.broad_type) url.searchParams.append('broad_type', params.broad_type);
    if (params?.category) url.searchParams.append('category', params.category);
    if (params?.emergency_only) url.searchParams.append('emergency_only', 'true');
    if (params?.limit !== undefined) url.searchParams.append('limit', params.limit.toString());
    if (params?.offset !== undefined) url.searchParams.append('offset', params.offset.toString());
    return fetchJson<InfrastructureFeatureCollection>(url.toString());
  },

  getSummary: (): Promise<InfrastructureSummary> => {
    return fetchJson<InfrastructureSummary>(API_ENDPOINTS.INFRASTRUCTURE_SUMMARY);
  },
};
