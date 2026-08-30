import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { 
  ArrowLeft, 
  ArrowRight,
  ShieldAlert, 
  Users, 
  Compass,
  Map,
  BookOpenCheck,
  MapPin,
  CheckCircle2,
  AlertCircle,
  AlertTriangle,
  Info,
  Route,
  Landmark,
  Building2
} from 'lucide-react';
import { useVillage } from '../hooks';
import { PriorityBadge } from '../components/shared/PriorityBadge';
import { InfoTooltip } from '../components/shared/InfoTooltip';
import { formatNumber, formatDistance, formatPercent } from '../utils/formatters';

export const VillageDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { data: villageCollection, isLoading } = useVillage(id || '');

  const feature = villageCollection?.features?.[0];
  const p = feature?.properties;

  if (isLoading) {
    return (
      <div className="p-12 text-center bg-white rounded-xl border border-slate-200 shadow-sm">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-xs text-slate-500">Loading decision profile for habitation #{id}...</p>
      </div>
    );
  }

  if (!p) {
    return (
      <div className="p-12 text-center bg-white rounded-xl border border-slate-200 shadow-sm space-y-3">
        <AlertCircle className="w-8 h-8 text-slate-400 mx-auto" />
        <p className="text-sm font-bold text-slate-800">Village Not Found</p>
        <p className="text-xs text-slate-500">No habitation record found for ID #{id}.</p>
        <Link
          to="/villages"
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white bg-blue-700 rounded-lg hover:bg-blue-800 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Return to Village Explorer
        </Link>
      </div>
    );
  }

  const hasTier1 = p.priority_tier === 'Tier1_AttentionPriority';
  const hasTier2 = p.priority_tier === 'Tier2_ElevatedAttention';

  return (
    <div className="space-y-5">
      {/* Breadcrumb Navigation */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-1.5">
          <Link
            to="/villages"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-blue-700 transition-colors"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            Back to Village Explorer
          </Link>
          <InfoTooltip
            title="Village Explorer"
            content="Return to the full list of 653 habitations and search/filter interface."
            side="right"
          />
        </div>
        <div className="flex items-center gap-2">
          <div className="flex items-center gap-1">
            <Link
              to="/map"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-blue-700 px-2.5 py-1 rounded border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-all"
            >
              <Map className="w-3.5 h-3.5" />
              View on GIS Map
            </Link>
            <InfoTooltip
              title="Spatial Map Context"
              content="Plot this village on the interactive Leaflet map to visually verify surrounding terrain and red zones."
              side="bottom"
            />
          </div>
          <div className="flex items-center gap-1">
            <Link
              to="/methodology"
              className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-blue-700 px-2.5 py-1 rounded border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-all"
            >
              <BookOpenCheck className="w-3.5 h-3.5" />
              Review Methodology
            </Link>
            <InfoTooltip
              title="Methodology Verification"
              content="Examine the step-by-step rules, thresholds, and limitations behind this priority score."
              side="bottom"
            />
          </div>
        </div>
      </div>

      {/* Village Header Card */}
      <div className={`bg-white rounded-xl border-2 shadow-sm p-5 ${
        hasTier1 ? 'border-red-200' : hasTier2 ? 'border-amber-200' : 'border-slate-200'
      }`}>
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-3 flex-wrap">
              <h2 className="text-2xl font-bold text-slate-900 tracking-tight">
                {p.village_name}
              </h2>
              <PriorityBadge tier={p.priority_tier} size="lg" showInfoTooltip={true} />
            </div>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500 mt-2">
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-slate-400" />
                Census Village ID: <strong className="font-mono text-slate-700 ml-1">{p.village_id}</strong>
                <InfoTooltip
                  title="Census Identification"
                  content="Primary Census Abstract (PCA) 2011 identifier linked to Development Data Lab SHRUG v2.2 administrative geography."
                  side="top"
                />
              </span>
              <span>•</span>
              <span>Rudraprayag District, Uttarakhand</span>
            </div>
          </div>

          <div className="sm:border-l sm:border-slate-200 sm:pl-5 text-right shrink-0">
            <div className="flex items-center justify-end gap-1">
              <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Population (Census 2011)</p>
              <InfoTooltip
                title="Census 2011 Population"
                content="Official total resident count and household baseline from the 2011 Census of India."
                side="left"
              />
            </div>
            <p className="text-2xl font-bold text-slate-900 mt-0.5">{formatNumber(p.tot_pop)}</p>
            <p className="text-xs text-slate-500">{formatNumber(p.households)} Households</p>
          </div>
        </div>
      </div>

      {/* WHY THIS CLASSIFICATION — Restructured */}
      <div className={`rounded-xl border-2 shadow-sm overflow-hidden ${
        hasTier1 ? 'border-red-300 bg-red-50/40' : hasTier2 ? 'border-amber-300 bg-amber-50/30' : 'border-blue-200 bg-blue-50/30'
      }`}>
        {/* Header */}
        <div className={`px-5 py-3 border-b flex items-center justify-between gap-3 ${
          hasTier1 ? 'border-red-200 bg-red-50' : hasTier2 ? 'border-amber-200 bg-amber-50' : 'border-blue-200 bg-blue-50'
        }`}>
          <div className="flex items-center gap-3">
            <div className={`p-2 rounded-lg text-white shadow-sm shrink-0 ${
              hasTier1 ? 'bg-red-600' : hasTier2 ? 'bg-amber-600' : 'bg-blue-600'
            }`}>
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                Why This Classification?
              </h3>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Decision rationale generated by deterministic rule-based screening pipeline
              </p>
            </div>
          </div>
          <InfoTooltip
            title="Explainable Decision Engine"
            content="Every classification reason is generated deterministically by mathematical rules based on Euclidean distance to red zones and centroid multi-hazard score."
            side="left"
          />
        </div>

        {/* Primary Reason */}
        <div className="p-5 space-y-4">
          <div>
            <div className="flex items-center gap-1.5 mb-1.5">
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                Primary Classification Reason
              </p>
              <InfoTooltip
                title="Primary Rationale Rule"
                content="The exact rule-based logic triggered by this habitation's spatial attributes."
                side="right"
              />
            </div>
            <p className={`text-sm font-medium leading-relaxed ${
              hasTier1 ? 'text-red-900' : hasTier2 ? 'text-amber-900' : 'text-slate-800'
            }`}>
              {p.priority_reason || 'Classification assigned deterministically based on distance to nearest candidate hazard red zone and multi-hazard class at village centroid.'}
            </p>
          </div>

          {/* Supporting Indicators Grid */}
          <div>
            <div className="flex items-center gap-1.5 mb-2">
              <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
                Supporting Indicators Used in Classification
              </p>
              <InfoTooltip
                title="Classification Factors"
                content="These four spatial indicators were evaluated by the Step 10 decision engine to determine the priority tier."
                side="right"
              />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-white rounded-lg border border-slate-200 p-3 text-center relative group">
                <div className="flex items-center justify-center gap-1">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">Nearest Red Zone</p>
                  <InfoTooltip title="Nearest Hazard Red Zone ID" content="Identifier of the closest candidate hazard red zone polygon boundary." side="top" />
                </div>
                <p className="text-sm font-bold font-mono text-slate-900 mt-1">{p.nearest_zone_id}</p>
              </div>
              <div className="bg-white rounded-lg border border-slate-200 p-3 text-center relative group">
                <div className="flex items-center justify-center gap-1">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">Proximity Distance</p>
                  <InfoTooltip title="Euclidean Distance" content="Shortest distance from the village reference centroid to the edge of the nearest red zone polygon in meters." formula="Measured in UTM Zone 44N" side="top" />
                </div>
                <p className={`text-sm font-bold font-mono mt-1 ${hasTier1 ? 'text-red-700' : 'text-slate-900'}`}>
                  {formatDistance(p.nearest_hazard_distance_m)}
                </p>
              </div>
              <div className="bg-white rounded-lg border border-slate-200 p-3 text-center relative group">
                <div className="flex items-center justify-center gap-1">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">MH Class at Centroid</p>
                  <InfoTooltip title="Multi-Hazard Class" content="Class 1 = Baseline screening hazard; Class 2+ = Moderate-to-high multi-hazard proxy score." formula="Derived from 30m DEM slope + TWI" side="top" />
                </div>
                <p className="text-sm font-bold font-mono text-slate-900 mt-1">Class {p.mh_class_at_centroid || 1}</p>
              </div>
              <div className="bg-white rounded-lg border border-slate-200 p-3 text-center relative group">
                <div className="flex items-center justify-center gap-1">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">Zone Overlap</p>
                  <InfoTooltip title="Spatial Overlap Status" content="Indicates whether the village administrative centroid point falls strictly inside a red zone polygon boundary." side="top" />
                </div>
                <p className={`text-sm font-bold font-mono mt-1 ${p.direct_zone_overlap ? 'text-red-700' : 'text-emerald-700'}`}>
                  {p.direct_zone_overlap ? 'INSIDE' : 'Outside'}
                </p>
              </div>
            </div>
          </div>

          {/* Methodology Status */}
          <div className="flex items-center justify-between pt-3 border-t border-slate-200/70">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-slate-400 shrink-0" />
              <div>
                <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400">Methodology Status</p>
                <p className="text-xs font-semibold text-slate-700 mt-0.5">
                  Preliminary Rule-Based Decision Support · Census 2011 · GLO-30 DEM
                </p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <span className="px-2 py-1 rounded-md bg-amber-100 border border-amber-300 text-amber-800 text-[10px] font-bold uppercase tracking-wide shrink-0">
                Screening Only
              </span>
              <InfoTooltip
                title="Screening Level Indicator"
                content="Not an official relocation order or government decree. Official field geotechnical surveys and administrative review are mandatory."
                side="left"
              />
            </div>
          </div>
        </div>
      </div>

      {/* PS-7: Relocation Planning Horizon & Recommended Action */}
      <div className="bg-slate-900 text-white rounded-xl border border-slate-700 p-5 shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-3">
          <div className="flex items-center gap-2.5">
            <span className="text-xs font-bold uppercase tracking-wider text-blue-400">
              Planning Horizon (PS-7)
            </span>
            <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
              hasTier1 ? 'bg-red-500/20 text-red-300 border border-red-500/40' :
              hasTier2 ? 'bg-amber-500/20 text-amber-300 border border-amber-500/40' :
              'bg-blue-500/20 text-blue-300 border border-blue-500/40'
            }`}>
              {p.relocation_horizon_display || p.relocation_horizon || 'Routine Monitoring'}
            </span>
          </div>
          <div className="text-xs text-slate-400">
            Planning Horizon: <strong className="text-slate-200">{p.planning_horizon_years || (hasTier1 ? '0-1 yr' : hasTier2 ? '1-3 yrs' : '3-10 yrs')}</strong>
          </div>
        </div>

        <div>
          <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1">
            Recommended Action for Authorities (SDMA / DDMA)
          </p>
          <p className="text-xs text-slate-200 leading-relaxed font-medium">
            {p.recommended_action || (
              hasTier1 ? 'Recommend immediate field verification by SDMA/district team. Priority for geotechnical survey scheduling. Community consultation required before any relocation planning action.' :
              hasTier2 ? 'Recommend inclusion in 1-3 year district hazard planning cycle. Block-level vulnerability mapping and infrastructure audit advised.' :
              'Include in periodic district hazard monitoring programme.'
            )}
          </p>
        </div>

        <p className="text-[10px] text-slate-500 italic pt-1">
          Disclaimer: Decision-support screening category only — NOT an official government relocation order or evacuation notice.
        </p>
      </div>

      {/* Phase 1-4 Contextual Lifelines (Non-Modulating Environmental & Infrastructure Context) */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-100 pb-3">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-teal-50 text-teal-700 border border-teal-200">
              <Building2 className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wide">
                Contextual Lifelines & Spatial Infrastructure (Phases 1–4)
              </h3>
              <p className="text-[11px] text-slate-500">
                Road connectivity, historical disaster exposure, and essential services (Reference context only — does not alter priority tier)
              </p>
            </div>
          </div>
          <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-100 text-slate-600 border border-slate-200 shrink-0">
            Context Only
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          {/* Road Connectivity */}
          <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 space-y-2">
            <div className="flex items-center justify-between font-bold text-slate-800">
              <span className="flex items-center gap-1.5">
                <Route className="w-3.5 h-3.5 text-blue-600" />
                <span>Road Network (Phase 2)</span>
              </span>
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                p.road_accessibility_category === 'ACCESSIBLE' ? 'bg-emerald-100 text-emerald-800' :
                p.road_accessibility_category === 'MODERATE' ? 'bg-blue-100 text-blue-800' :
                p.road_accessibility_category === 'REMOTE' ? 'bg-amber-100 text-amber-800' :
                'bg-red-100 text-red-800'
              }`}>
                {p.road_accessibility_category || 'EVALUATED'}
              </span>
            </div>
            <div className="space-y-1 text-slate-600 divide-y divide-slate-200/60 text-[11px]">
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Nearest Road:</span>
                <span className="font-semibold text-slate-800 truncate max-w-[140px]" title={p.nearest_road_name}>
                  {p.nearest_road_name || 'Unnamed Road'}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Snapping Distance:</span>
                <span className="font-mono font-semibold">{formatDistance(p.road_snapping_distance_m)}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Arterial Network Dist:</span>
                <span className="font-mono font-semibold">{formatDistance(p.network_distance_to_arterial_m)}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Arterial Travel Time:</span>
                <span className="font-mono font-semibold">{p.network_travel_time_to_arterial_min ? `${p.network_travel_time_to_arterial_min.toFixed(1)} min` : '—'}</span>
              </div>
            </div>
          </div>

          {/* Historical Disaster Exposure */}
          <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 space-y-2">
            <div className="flex items-center justify-between font-bold text-slate-800">
              <span className="flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-orange-600" />
                <span>Disaster Context (Phase 3)</span>
              </span>
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                p.chronic_disaster_exposure_2km_flag ? 'bg-red-100 text-red-800' : 'bg-slate-200 text-slate-700'
              }`}>
                {p.chronic_disaster_exposure_2km_flag ? 'CHRONIC EXPOSURE' : 'ISOLATED/NONE'}
              </span>
            </div>
            <div className="space-y-1 text-slate-600 divide-y divide-slate-200/60 text-[11px]">
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Nearest Incident:</span>
                <span className="font-semibold text-slate-800">
                  {p.nearest_disaster_hazard_type ? `${p.nearest_disaster_hazard_type} (${p.nearest_disaster_year})` : 'None in AOI'}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Dist to Nearest Event:</span>
                <span className="font-mono font-semibold">{formatDistance(p.dist_to_nearest_disaster_m)}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Events within 1 km:</span>
                <span className="font-mono font-semibold">{p.disaster_events_within_1km_count ?? 0}</span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Events within 2 km:</span>
                <span className="font-mono font-semibold">{p.disaster_events_within_2km_count ?? 0}</span>
              </div>
            </div>
          </div>

          {/* Critical Infrastructure */}
          <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 space-y-2">
            <div className="flex items-center justify-between font-bold text-slate-800">
              <span className="flex items-center gap-1.5">
                <Landmark className="w-3.5 h-3.5 text-teal-600" />
                <span>Facilities (Phase 4)</span>
              </span>
              <span className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                p.hospital_chc_access_under_60min_flag ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
              }`}>
                {p.hospital_chc_access_under_60min_flag ? 'HOSPITAL ≤60m' : 'HOSPITAL >60m'}
              </span>
            </div>
            <div className="space-y-1 text-slate-600 divide-y divide-slate-200/60 text-[11px]">
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Nearest Health Centre:</span>
                <span className="font-semibold text-slate-800 truncate max-w-[130px]" title={p.nearest_health_facility_name}>
                  {p.nearest_health_facility_name || 'SubCentre'} ({formatDistance(p.dist_to_nearest_health_facility_m)})
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Hospital / CHC Time:</span>
                <span className="font-mono font-semibold">
                  {p.network_time_to_hospital_chc_min ? `${p.network_time_to_hospital_chc_min.toFixed(1)} min` : formatDistance(p.dist_to_nearest_hospital_chc_m)}
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Nearest School:</span>
                <span className="font-semibold text-slate-800 truncate max-w-[130px]" title={p.nearest_school_name}>
                  {p.nearest_school_name || 'School'} ({formatDistance(p.dist_to_nearest_school_m)})
                </span>
              </div>
              <div className="flex justify-between py-1">
                <span className="text-slate-500">Nearest Emergency:</span>
                <span className="font-semibold text-slate-800 truncate max-w-[130px]" title={p.nearest_emergency_service_name}>
                  {p.nearest_emergency_service_name || 'Police'} ({formatDistance(p.dist_to_nearest_emergency_service_m)})
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Hazard & Demographic Context */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Spatial Hazard Context */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Compass className="w-4 h-4 text-blue-600" />
              <span>Hazard & Proximity Context</span>
            </h3>
            <InfoTooltip
              title="Spatial Hazard Indicators"
              content="Detailed breakdown of hazard proximity band, direct polygon intersection, and coordinate metadata."
              side="left"
            />
          </div>

          <div className="space-y-0 text-xs divide-y divide-slate-100">
            <div className="flex justify-between items-center py-2">
              <span className="text-slate-500">Proximity Band</span>
              <span className="font-semibold text-slate-900">{p.proximity_band}</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-slate-500">Direct Zone Overlap</span>
              <span className={`font-semibold font-mono ${p.direct_zone_overlap ? 'text-red-700' : 'text-slate-700'}`}>
                {p.direct_zone_overlap ? 'YES — Centroid Inside Zone' : 'NO — Centroid Outside'}
              </span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-slate-500">Hazard Zone Label</span>
              <span className="font-semibold text-slate-900">{p.hazard_zone_label || 'Outside Zone'}</span>
            </div>
            {feature.geometry?.coordinates && (
              <div className="flex justify-between items-center py-2">
                <div className="flex items-center gap-1">
                  <span className="text-slate-500">Centroid (EPSG:4326)</span>
                  <InfoTooltip title="Centroid Limitation" content="Administrative reference coordinates from Census/SHRUG. Actual habitation perimeter or structures may extend closer to hazard terrain." side="top" />
                </div>
                <span className="font-mono text-[11px] text-slate-600">
                  {feature.geometry.coordinates[1].toFixed(4)}°N,&nbsp;
                  {feature.geometry.coordinates[0].toFixed(4)}°E
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Demographic & Vulnerability Context (PS-3) */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Users className="w-4 h-4 text-slate-500" />
              <span>Demographic & Vulnerability Context (PS-3)</span>
            </h3>
            <div className="flex items-center gap-1">
              <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wide border ${
                (p.vulnerability_flag_count ?? 0) >= 2 
                  ? 'bg-amber-100 border-amber-300 text-amber-800' 
                  : 'bg-slate-100 border-slate-300 text-slate-600'
              }`}>
                <Info className="w-3 h-3" />
                {p.vulnerability_context || `${p.vulnerability_flag_count ?? 0} of 4 factors flagged`}
              </span>
            </div>
          </div>

          <p className="text-[11px] text-slate-500 leading-tight bg-slate-50 px-2.5 py-1.5 rounded border border-slate-200">
            Census 2011 PCA indicators benchmarked against district upper tertile (P75). 
            Flags are <strong>context only</strong> and do not alter tier assignment.
          </p>

          <div className="space-y-0 text-xs divide-y divide-slate-100">
            <div className="flex justify-between items-center py-2">
              <span className="text-slate-500">
                Illiteracy Rate {p.vf_high_illiteracy && <span className="ml-1 text-[10px] text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded font-semibold">High (&gt;34%)</span>}
              </span>
              <span className="font-mono font-medium text-slate-800">{formatPercent(p.illiteracy_rate)}</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-slate-500">
                Children (0–6 yrs) {p.vf_high_child_pop && <span className="ml-1 text-[10px] text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded font-semibold">High (&gt;15.1%)</span>}
              </span>
              <span className="font-mono font-medium text-slate-800">{formatPercent(p.child_proportion)}</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-slate-500">
                SC Proportion {p.vf_high_sc && <span className="ml-1 text-[10px] text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded font-semibold">High (&gt;24.6%)</span>}
              </span>
              <span className="font-mono font-medium text-slate-800">{formatPercent(p.sc_proportion)}</span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-slate-500">
                Non-Worker Proportion {p.vf_high_dependency && <span className="ml-1 text-[10px] text-amber-700 bg-amber-100 px-1.5 py-0.5 rounded font-semibold">High (&gt;57.9%)</span>}
              </span>
              <span className="font-mono font-medium text-slate-800">{formatPercent(p.non_worker_rate)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Methodological Notes */}
      <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 space-y-2">
        <div className="flex items-center justify-between">
          <h4 className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
            Methodological Transparency & Limitations
          </h4>
          <InfoTooltip
            title="Scientific Caveats"
            content="Key technical limitations regarding DEM resolution, centroid approximations, and unacquired historical disaster records."
            side="left"
          />
        </div>
        <ul className="space-y-1.5 text-xs text-slate-600">
          <li className="flex items-start gap-2">
            <span className="text-slate-400 mt-0.5">•</span>
            <span><strong className="text-slate-800">Administrative Centroids:</strong> Coordinates are Census 2011 / SHRUG v2.2 reference centroids, not building footprints or settlement boundaries.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-slate-400 mt-0.5">•</span>
            <span><strong className="text-slate-800">Euclidean Distance:</strong> Proximity measured as planar Euclidean distance in UTM Zone 44N (EPSG:32644), not road or network routes.</span>
          </li>
          <li className="flex items-start gap-2">
            <span className="text-slate-400 mt-0.5">•</span>
            <span><strong className="text-slate-800">Preliminary Screening:</strong> This classification is a preliminary decision-support output. Official field geotechnical verification and administrative review are required.</span>
          </li>
        </ul>
      </div>

      {/* Footer nav */}
      <div className="flex items-center justify-between pt-2">
        <Link
          to="/villages"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-blue-700 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Village Explorer
        </Link>
        <Link
          to="/methodology"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-700 hover:text-blue-900 transition-colors"
        >
          Review Full Methodology
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
