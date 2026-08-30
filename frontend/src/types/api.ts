/**
 * SIH26191 TypeScript Interfaces
 * 
 * Accurately mapped to FastAPI routes and Step 10/11 output JSON schemas.
 */

import { PriorityTierKey } from '../config/constants';

// --- System & Metadata Types ---

export interface SystemHealth {
  status: 'ok' | 'error';
  api_version: string;
  datasets_loaded: {
    decision_metadata: boolean;
    decision_summary: boolean;
    villages: boolean;
    red_zones: boolean;
    candidate_areas: boolean;
  };
}

export interface ProjectMetadata {
  project_metadata: {
    id: string;
    name: string;
    short_title: string;
    pilot_district: string;
    state: string;
    country: string;
  };
  crs: {
    storage_crs: string;
    analysis_crs_metric: string;
  };
  methodology_status: string;
  major_limitations: string;
  decision_support_disclaimer: string;
}

// --- Decision Summary Types ---

export interface TierStats {
  display_label: string;
  count: number;
  percentage: number;
  population: number;
  households: number;
}

export interface ProximityBandStats {
  count: number;
  population: number;
}

export interface TopAttentionVillage {
  village_id: number;
  village_name: string;
  tot_pop: number;
  households: number;
  nearest_hazard_distance_m: number;
  nearest_zone_id: string;
  mh_class_at_centroid: number;
  priority_reason: string;
}

export interface VulnerabilityIndicatorStat {
  mean: number;
  median: number;
  min: number;
  max: number;
  valid_count: number;
}

export interface CandidateAreaSummaryItem {
  area_id: string;
  area_hectares: number;
  mean_slope: number;
  slope_context: string;
  terrain_context: string;
  flood_context: string;
  hazard_buffer_context: string;
  area_scale_context: string;
  dist_to_nearest_redzone_m: number;
  nearest_village_name: string;
  nearest_village_pop: number;
  capacity_status: string;
}

export interface DecisionSummary {
  project: string;
  step: string;
  pilot_district: string;
  generated_utc: string;
  methodology_version: string;
  classification_method: string;
  village_priority: {
    total_habitations: number;
    total_population: number;
    total_households: number;
    tier_distribution: Record<PriorityTierKey, TierStats>;
    proximity_band_distribution: Record<string, ProximityBandStats>;
    mh_class_at_centroid_distribution: {
      Class_1: number;
      Class_2: number;
      Class_3: number;
      NoData: number;
    };
    top_attention_priority_villages: TopAttentionVillage[];
    vulnerability_indicator_stats: {
      illiteracy_rate: VulnerabilityIndicatorStat;
      child_proportion: VulnerabilityIndicatorStat;
      sc_proportion: VulnerabilityIndicatorStat;
      st_proportion: VulnerabilityIndicatorStat;
      non_worker_rate: VulnerabilityIndicatorStat;
    };
    vulnerability_note: string;
  };
  candidate_areas: {
    total_features: number;
    total_area_ha: number;
    capacity_status: string;
    allocation_status: string;
    screening_completeness: string;
    areas: CandidateAreaSummaryItem[];
  };
  missing_datasets: string[];
  blocked_features: string[];
  disclaimer: string;
}

export interface DecisionMetadata {
  project: string;
  generated_utc: string;
  pipeline_step: string;
  inputs_used: Record<string, string>;
  outputs_produced: Record<string, string>;
  classification_rules_applied: {
    tier1: { rule: string; config_source: string; status: string };
    tier2: { rule: string; config_source: string; status: string };
    tier3: { rule: string; config_source: string; status: string };
    beyond: { rule: string; config_source: string; status: string };
  };
  indicators_used_in_tier: string[];
  indicators_as_context_only: string[];
  conditional_inputs_unavailable: Record<string, string>;
  capacity_status: string;
  allocation_status: string;
  crs: string;
}

// --- Village GeoJSON Types ---

export interface VillageProperties {
  village_id: number;
  village_name: string;
  tot_pop: number;
  households: number;
  pop_sc?: number;
  pop_st?: number;
  direct_zone_overlap?: boolean;
  hazard_zone_flag?: number;
  hazard_zone_label?: string;
  nearest_hazard_distance_m: number;
  proximity_band: string;
  nearest_zone_id: string;
  priority_tier: PriorityTierKey;
  mh_class_at_centroid: number;
  mh_score_at_centroid?: number;
  terrain_score_at_centroid?: number;
  flood_score_at_centroid?: number;
  illiteracy_rate?: number;
  child_proportion?: number;
  sc_proportion?: number;
  st_proportion?: number;
  non_worker_rate?: number;
  priority_reason?: string;
  priority_applied_rule?: string;
  priority_tier_display?: string;
  relocation_horizon?: string;
  relocation_horizon_display?: string;
  recommended_action?: string;
  horizon_rationale?: string;
  horizon_limitations?: string;
  planning_horizon_years?: string;
  horizon_disclaimer?: string;
  vulnerability_flag_count?: number;
  vulnerability_context?: string;
  vulnerability_disclaimer?: string;
  vf_high_child_pop?: boolean;
  vf_high_sc?: boolean;
  vf_high_dependency?: boolean;
  vf_high_illiteracy?: boolean;
  disaster_history_status?: string;
  disaster_history_note?: string;
  nearest_disaster_incident_id?: string;
  nearest_disaster_distance_m?: number;
  methodology_status?: string;
  step10c_disclaimer?: string;
}

export interface GeoJsonPoint {
  type: 'Point';
  coordinates: [number, number]; // [lon, lat]
}

export interface VillageFeature {
  type: 'Feature';
  id?: string | number;
  geometry: GeoJsonPoint;
  properties: VillageProperties;
}

export interface VillageFeatureCollection {
  type: 'FeatureCollection';
  features: VillageFeature[];
}

// --- Red Zone GeoJSON Types ---

export interface RedZoneProperties {
  zone_id: string;
  area_ha?: number;
  mean_mh_score?: number;
  max_mh_score?: number;
  description?: string;
}

export interface RedZoneFeature {
  type: 'Feature';
  id?: string | number;
  geometry: {
    type: 'Polygon' | 'MultiPolygon';
    coordinates: any;
  };
  properties: RedZoneProperties;
}

export interface RedZoneFeatureCollection {
  type: 'FeatureCollection';
  features: RedZoneFeature[];
}

// --- Candidate Area GeoJSON Types ---

export interface CandidateAreaProperties {
  area_id: string;
  area_hectares: number;
  mean_slope: number;
  slope_context: string;
  terrain_context: string;
  flood_context: string;
  hazard_buffer_context: string;
  area_scale_context: string;
  dist_to_nearest_redzone_m: number;
  nearest_village_name: string;
  nearest_village_pop: number;
  capacity_status: string;
}

export interface CandidateAreaFeature {
  type: 'Feature';
  id?: string | number;
  geometry: {
    type: 'Polygon' | 'MultiPolygon';
    coordinates: any;
  };
  properties: CandidateAreaProperties;
}

export interface CandidateAreaFeatureCollection {
  type: 'FeatureCollection';
  features: CandidateAreaFeature[];
}

// --- Disaster History GeoJSON Types ---

export interface DisasterIncidentProperties {
  incident_id: string;
  hazard_type: string;
  date: string;
  severity?: string;
  verification_status: string;
  source_metadata: string;
  description: string;
}

export interface DisasterIncidentFeature {
  type: 'Feature';
  id?: string | number;
  geometry: GeoJsonPoint;
  properties: DisasterIncidentProperties;
}

export interface DisasterIncidentFeatureCollection {
  type: 'FeatureCollection';
  features: DisasterIncidentFeature[];
}

// --- Hazards Metadata Types ---

export interface HazardLayerInfo {
  name: string;
  status: 'AVAILABLE' | 'CONFIGURED_BUT_MISSING' | 'NOT_CONFIGURED';
  file: string;
  description?: string;
}

export interface HazardsResponse {
  metadata: {
    disclaimer: string;
    crs: string;
  };
  layers: Record<string, HazardLayerInfo>;
  available_files_in_directory: string[];
}
