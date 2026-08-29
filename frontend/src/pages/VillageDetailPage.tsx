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
  Info
} from 'lucide-react';
import { useVillage } from '../hooks';
import { PriorityBadge } from '../components/shared/PriorityBadge';
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
        <Link
          to="/villages"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-500 hover:text-blue-700 transition-colors"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          Back to Village Explorer
        </Link>
        <div className="flex items-center gap-2">
          <Link
            to="/map"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-blue-700 px-2.5 py-1 rounded border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-all"
          >
            <Map className="w-3.5 h-3.5" />
            View on GIS Map
          </Link>
          <Link
            to="/methodology"
            className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-600 hover:text-blue-700 px-2.5 py-1 rounded border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-all"
          >
            <BookOpenCheck className="w-3.5 h-3.5" />
            Review Methodology
          </Link>
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
              <PriorityBadge tier={p.priority_tier} size="lg" />
            </div>
            <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500 mt-2">
              <span className="flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5" />
                Census Village ID: <strong className="font-mono text-slate-700 ml-1">{p.village_id}</strong>
              </span>
              <span>•</span>
              <span>Rudraprayag District, Uttarakhand</span>
            </div>
          </div>

          <div className="sm:border-l sm:border-slate-200 sm:pl-5 text-right shrink-0">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-slate-500">Population (Census 2011)</p>
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
        <div className={`px-5 py-3 border-b flex items-center gap-3 ${
          hasTier1 ? 'border-red-200 bg-red-50' : hasTier2 ? 'border-amber-200 bg-amber-50' : 'border-blue-200 bg-blue-50'
        }`}>
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

        {/* Primary Reason */}
        <div className="p-5 space-y-4">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-1.5">
              Primary Classification Reason
            </p>
            <p className={`text-sm font-medium leading-relaxed ${
              hasTier1 ? 'text-red-900' : hasTier2 ? 'text-amber-900' : 'text-slate-800'
            }`}>
              {p.priority_reason || 'Classification assigned deterministically based on distance to nearest candidate hazard red zone and multi-hazard class at village centroid.'}
            </p>
          </div>

          {/* Supporting Indicators Grid */}
          <div>
            <p className="text-[10px] font-bold uppercase tracking-widest text-slate-400 mb-2">
              Supporting Indicators Used in Classification
            </p>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              <div className="bg-white rounded-lg border border-slate-200 p-3 text-center">
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">Nearest Red Zone</p>
                <p className="text-sm font-bold font-mono text-slate-900 mt-1">{p.nearest_zone_id}</p>
              </div>
              <div className="bg-white rounded-lg border border-slate-200 p-3 text-center">
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">Proximity Distance</p>
                <p className={`text-sm font-bold font-mono mt-1 ${hasTier1 ? 'text-red-700' : 'text-slate-900'}`}>
                  {formatDistance(p.nearest_hazard_distance_m)}
                </p>
              </div>
              <div className="bg-white rounded-lg border border-slate-200 p-3 text-center">
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">MH Class at Centroid</p>
                <p className="text-sm font-bold font-mono text-slate-900 mt-1">Class {p.mh_class_at_centroid || 1}</p>
              </div>
              <div className="bg-white rounded-lg border border-slate-200 p-3 text-center">
                <p className="text-[10px] font-semibold text-slate-400 uppercase tracking-wide">Zone Overlap</p>
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
            <span className="px-2 py-1 rounded-md bg-amber-100 border border-amber-300 text-amber-800 text-[10px] font-bold uppercase tracking-wide shrink-0">
              Screening Only
            </span>
          </div>
        </div>
      </div>

      {/* Hazard & Demographic Context */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Spatial Hazard Context */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-3">
          <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
            <Compass className="w-4 h-4 text-blue-600" />
            <span>Hazard & Proximity Context</span>
          </h3>

          <div className="space-y-0 text-xs divide-y divide-slate-100">
            <div className="flex justify-between py-2">
              <span className="text-slate-500">Proximity Band</span>
              <span className="font-semibold text-slate-900">{p.proximity_band}</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-500">Direct Zone Overlap</span>
              <span className={`font-semibold font-mono ${p.direct_zone_overlap ? 'text-red-700' : 'text-slate-700'}`}>
                {p.direct_zone_overlap ? 'YES — Centroid Inside Zone' : 'NO — Centroid Outside'}
              </span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-500">Hazard Zone Label</span>
              <span className="font-semibold text-slate-900">{p.hazard_zone_label || 'Outside Zone'}</span>
            </div>
            {feature.geometry?.coordinates && (
              <div className="flex justify-between py-2">
                <span className="text-slate-500">Centroid (EPSG:4326)</span>
                <span className="font-mono text-[11px] text-slate-600">
                  {feature.geometry.coordinates[1].toFixed(4)}°N,&nbsp;
                  {feature.geometry.coordinates[0].toFixed(4)}°E
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Demographic Context — NOT used in classification */}
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <Users className="w-4 h-4 text-slate-500" />
              <span>Demographic Context</span>
            </h3>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-slate-100 border border-slate-300 text-slate-600 text-[10px] font-bold uppercase tracking-wide">
              <Info className="w-3 h-3" />
              Context Only — Not Used in Priority
            </span>
          </div>

          <p className="text-[11px] text-slate-500 leading-tight bg-slate-50 px-2.5 py-1.5 rounded border border-slate-200">
            Census 2011 social indicators are provided for planning context only.
            They were <strong>NOT</strong> used in determining this village's priority tier.
          </p>

          <div className="space-y-0 text-xs divide-y divide-slate-100">
            <div className="flex justify-between py-2">
              <span className="text-slate-500">Illiteracy Rate</span>
              <span className="font-mono font-medium text-slate-800">{formatPercent(p.illiteracy_rate)}</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-500">Children (0–6 yrs) Proportion</span>
              <span className="font-mono font-medium text-slate-800">{formatPercent(p.child_proportion)}</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-500">SC Proportion</span>
              <span className="font-mono font-medium text-slate-800">{formatPercent(p.sc_proportion)}</span>
            </div>
            <div className="flex justify-between py-2">
              <span className="text-slate-500">Non-Worker Proportion</span>
              <span className="font-mono font-medium text-slate-800">{formatPercent(p.non_worker_rate)}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Methodological Notes */}
      <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 space-y-2">
        <h4 className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
          Methodological Transparency & Limitations
        </h4>
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
