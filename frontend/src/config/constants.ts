/**
 * SIH26191 Central Frontend Constants & Terminology
 * 
 * Strict enforcement of project terminology and safety standards:
 * - "Candidate Hazard-Based Red Zone" (NOT official government red zones)
 * - "Candidate Topographically Feasible Site" / "Candidate Area Context" (NOT "Safe Site" or "Approved Relocation Site")
 * - "Preliminary Spatial Capacity Estimate" (NOT engineering-certified carrying capacity)
 * - "Decision Support — Requires Official Verification & Geotechnical Assessment"
 */

export const PROJECT_INFO = {
  ID: 'SIH26191',
  NAME: 'Intelligent Identification of Hazard-Based Red Zones & Decision Support',
  SHORT_TITLE: 'Hazard Red Zone & Relocation Decision Support',
  PILOT_DISTRICT: 'Rudraprayag',
  STATE: 'Uttarakhand',
  COUNTRY: 'India',
  PIPELINE_VERSION: '1.0',
  POPULATION_BASELINE: 'Census of India 2011 (PCA)',
  STORAGE_CRS: 'EPSG:4326 (WGS 84)',
  METRIC_CRS: 'EPSG:32644 (UTM Zone 44N)',
  LIVE_MONITORING_STATUS: 'NOT INTEGRATED (Deterministic Static Snapshot)',
} as const;

export const MANDATORY_DISCLAIMERS = {
  BANNER: 'PRELIMINARY DECISION-SUPPORT SCREENING SYSTEM — NOT an official government relocation authorization, safe-site certification, or real-time disaster alert platform. All outputs require official geotechnical and administrative review.',
  DECISION_SUPPORT: 'Decision Support — Requires Official Verification & Geotechnical Assessment',
  CA_0001_WARNING: 'Preliminary unfiltered topographically feasible terrain extent (~361,307 ha) — represents district-wide terrain screening with unconfigured threshold filters. Requires additional screening and geotechnical field verification. NOT a discrete relocation site.',
  CAPACITY_STATUS: 'NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD',
  CAPACITY_LABEL: 'Requires Planning Standard (Not Estimated)',
  CENTROID_LIMITATION: 'Village coordinates represent administrative reference centroids from Census 2011/SHRUG, not actual settlement footprints or building boundaries.',
} as const;

export type PriorityTierKey = 
  | 'Tier1_AttentionPriority'
  | 'Tier2_ElevatedAttention'
  | 'Tier3_Monitoring'
  | 'BeyondProximity';

export interface PriorityTierConfig {
  key: PriorityTierKey;
  label: string;
  shortLabel: string;
  badgeBg: string;
  badgeText: string;
  badgeBorder: string;
  dotColor: string;
  mapColor: string;
  mapSize: number;
  description: string;
}

export const PRIORITY_TIERS: Record<PriorityTierKey, PriorityTierConfig> = {
  Tier1_AttentionPriority: {
    key: 'Tier1_AttentionPriority',
    label: 'Tier 1 — Attention Priority',
    shortLabel: 'Tier 1 Priority',
    badgeBg: 'bg-red-50',
    badgeText: 'text-red-800',
    badgeBorder: 'border-red-300',
    dotColor: 'bg-red-600',
    mapColor: '#DC2626',
    mapSize: 9,
    description: 'Distance ≤ 500m to Red Zone AND MH Class ≥ 2; or direct zone overlap',
  },
  Tier2_ElevatedAttention: {
    key: 'Tier2_ElevatedAttention',
    label: 'Tier 2 — Elevated Attention',
    shortLabel: 'Tier 2 Elevated',
    badgeBg: 'bg-amber-50',
    badgeText: 'text-amber-800',
    badgeBorder: 'border-amber-300',
    dotColor: 'bg-amber-600',
    mapColor: '#D97706',
    mapSize: 7,
    description: 'Distance ≤ 2,000m to Candidate Red Zone boundary',
  },
  Tier3_Monitoring: {
    key: 'Tier3_Monitoring',
    label: 'Tier 3 — Monitoring',
    shortLabel: 'Tier 3 Monitoring',
    badgeBg: 'bg-blue-50',
    badgeText: 'text-blue-800',
    badgeBorder: 'border-blue-300',
    dotColor: 'bg-blue-600',
    mapColor: '#2563EB',
    mapSize: 5,
    description: 'Distance ≤ 5,000m to Candidate Red Zone boundary',
  },
  BeyondProximity: {
    key: 'BeyondProximity',
    label: 'Beyond Proximity — Lower Attention',
    shortLabel: 'Beyond Proximity',
    badgeBg: 'bg-slate-100',
    badgeText: 'text-slate-700',
    badgeBorder: 'border-slate-300',
    dotColor: 'bg-slate-500',
    mapColor: '#64748B',
    mapSize: 4,
    description: 'Distance > 5,000m outside monitoring proximity threshold',
  },
};

export const MAP_DEFAULTS = {
  RUDRAPRAYAG_CENTER: [30.40, 79.05] as [number, number],
  DEFAULT_ZOOM: 10,
  MIN_ZOOM: 8,
  MAX_ZOOM: 16,
  BOUNDS: [
    [30.15, 78.75], // Southwest corner
    [30.85, 79.40], // Northeast corner
  ] as [[number, number], [number, number]],
};
