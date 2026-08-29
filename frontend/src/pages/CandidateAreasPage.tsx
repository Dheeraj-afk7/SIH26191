import React from 'react';
import { Layers, AlertTriangle, ArrowRight, BookOpenCheck, XCircle, Info } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useDecisionSummary } from '../hooks';
import { formatNumber, formatHectares, formatDistance } from '../utils/formatters';
import { MANDATORY_DISCLAIMERS } from '../config/constants';

export const CandidateAreasPage: React.FC = () => {
  const { data: summary, isLoading } = useDecisionSummary();

  const candidateAreas = summary?.candidate_areas;
  const areas = candidateAreas?.areas || [];

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Layers className="w-5 h-5 text-amber-700" />
            Candidate Topographically Feasible Areas
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Preliminary terrain-derived candidate extents · Rudraprayag District · {areas.length} Screened Polygons
          </p>
        </div>
        <Link
          to="/methodology"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-blue-700 px-3 py-1.5 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-all"
        >
          <BookOpenCheck className="w-3.5 h-3.5" />
          Review Methodology
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {/* Mandatory Safety Notice */}
      <div className="bg-red-50 border-2 border-red-300 rounded-xl p-4 shadow-sm">
        <div className="flex items-start gap-3">
          <XCircle className="w-5 h-5 text-red-600 shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-bold text-red-900 mb-1">
              MANDATORY SAFETY & TERMINOLOGY NOTICE
            </p>
            <p className="text-xs font-semibold text-red-950 mb-1">
              These are CANDIDATE AREA CONTEXT records only — NOT "Approved Relocation Sites", "Safe Sites", or "Recommended Sites".
            </p>
            <p className="text-xs text-red-800 leading-relaxed">
              All areas are preliminary, unverified terrain-derived extents.
              Carrying capacity is <strong>not estimated</strong> due to the absence of verified planning standards.
              Official field surveys, geotechnical assessments, and administrative clearance are mandatory prior to any planning use.
            </p>
          </div>
        </div>
      </div>

      {/* CA-0001 Special Alert */}
      <div className="bg-amber-50 border-2 border-amber-400 rounded-xl p-4 shadow-sm">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
          <div className="flex-1">
            <div className="flex items-center justify-between flex-wrap gap-2 mb-2">
              <p className="text-sm font-bold text-amber-950">
                Context regarding CA-0001 — 361,307 Hectares
              </p>
              <span className="px-2.5 py-1 rounded-md bg-amber-200 border border-amber-400 text-amber-900 text-[10px] font-bold uppercase tracking-wide">
                Very Large Unfiltered Terrain Extent
              </span>
            </div>
            <p className="text-xs text-amber-900 leading-relaxed mb-3">
              {MANDATORY_DISCLAIMERS.CA_0001_WARNING}
            </p>
            <div className="flex flex-wrap gap-2">
              {[
                'Slope Max Deg: NOT_CONFIGURED',
                'Minimum Mapping Unit: NOT_CONFIGURED',
                'Capacity Standard: NOT_CONFIGURED',
              ].map((label) => (
                <span key={label} className="px-2 py-0.5 rounded bg-amber-100 border border-amber-300 text-amber-800 text-[11px] font-mono font-medium">
                  {label}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Area Cards List */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-widest">
            Screened Terrain Polygons — {areas.length} Features
          </h3>
          {isLoading && <span className="text-xs text-slate-400 animate-pulse">Loading...</span>}
        </div>

        {areas.map((area) => {
          const isCA0001 = area.area_id === 'CA-0001';

          return (
            <div
              key={area.area_id}
              className={`bg-white rounded-xl border shadow-sm overflow-hidden ${
                isCA0001
                  ? 'border-amber-400 ring-1 ring-amber-300'
                  : 'border-slate-200'
              }`}
            >
              {/* Area Header Bar */}
              <div className={`px-5 py-3 border-b flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 ${
                isCA0001 ? 'bg-amber-50 border-amber-200' : 'bg-slate-50 border-slate-200'
              }`}>
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="font-mono text-base font-bold text-slate-900 px-2.5 py-1 rounded-md bg-white border border-slate-300 shadow-xs">
                    {area.area_id}
                  </span>
                  <span className="text-xs font-semibold text-slate-700">
                    {isCA0001 ? 'Preliminary Unfiltered Terrain Extent' : 'Candidate Feasible Terrain Cluster'}
                  </span>
                  {isCA0001 && (
                    <span className="px-2 py-0.5 rounded bg-amber-200 border border-amber-400 text-amber-900 text-[10px] font-bold uppercase tracking-wide">
                      Unfiltered
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-2 shrink-0 flex-wrap">
                  <span className="px-2.5 py-1 rounded-md bg-white border border-slate-300 text-slate-700 font-mono text-xs font-bold shadow-xs">
                    {formatHectares(area.area_hectares)}
                  </span>
                  <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-md bg-red-50 border border-red-300 text-red-800 text-[10px] font-bold uppercase tracking-wide">
                    <XCircle className="w-3 h-3" />
                    CAPACITY: NOT ESTIMATED
                  </span>
                </div>
              </div>

              {/* Attribute Grid */}
              <div className="p-5">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs mb-4">
                  <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <span className="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Topographic Slope</span>
                    <p className="font-mono font-bold text-slate-900 mt-1.5 text-sm">
                      {area.mean_slope.toFixed(1)}° Mean
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">{area.slope_context}</p>
                  </div>

                  <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <span className="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Nearest Red Zone</span>
                    <p className="font-mono font-bold text-slate-900 mt-1.5 text-sm">
                      {formatDistance(area.dist_to_nearest_redzone_m)}
                    </p>
                    <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">{area.hazard_buffer_context}</p>
                  </div>

                  <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <span className="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Nearest Habitation</span>
                    <p className="font-semibold text-slate-900 mt-1.5 text-sm">{area.nearest_village_name}</p>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {formatNumber(area.nearest_village_pop)} residents
                    </p>
                  </div>

                  <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                    <span className="text-slate-400 font-semibold uppercase tracking-wide text-[10px]">Terrain Screening</span>
                    <p className="font-medium text-slate-800 mt-1.5 text-xs leading-tight">{area.terrain_context}</p>
                    <p className="text-[11px] text-slate-500 mt-0.5 leading-snug">{area.flood_context}</p>
                  </div>
                </div>

                {/* Area Scale Context Banner */}
                <div className={`flex items-start gap-2 p-3 rounded-lg border text-xs leading-relaxed ${
                  isCA0001
                    ? 'bg-amber-50 border-amber-200 text-amber-900'
                    : 'bg-slate-50 border-slate-200 text-slate-600'
                }`}>
                  <Info className={`w-4 h-4 mt-0.5 shrink-0 ${isCA0001 ? 'text-amber-600' : 'text-slate-400'}`} />
                  <p className="font-mono text-[11px]">{area.area_scale_context}</p>
                </div>
              </div>
            </div>
          );
        })}

        {areas.length === 0 && (
          <div className="p-12 text-center bg-white rounded-xl border border-slate-200 text-xs text-slate-500">
            {isLoading ? 'Loading candidate areas context from backend...' : 'No candidate areas loaded.'}
          </div>
        )}
      </div>

      {/* Screening Status Summary */}
      {candidateAreas && (
        <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 space-y-2">
          <h4 className="text-[10px] font-bold uppercase tracking-widest text-slate-400">
            Screening Status Summary
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            <div className="flex justify-between py-1.5 border-b border-slate-200">
              <span className="text-slate-500">Capacity Status</span>
              <span className="font-mono font-bold text-red-700">NOT_ESTIMATED_REQUIRES_PLANNING_STANDARD</span>
            </div>
            <div className="flex justify-between py-1.5 border-b border-slate-200">
              <span className="text-slate-500">Allocation Status</span>
              <span className="font-mono font-bold text-red-700 text-right">NOT_GENERATED</span>
            </div>
            <div className="col-span-1 sm:col-span-2 py-1.5">
              <span className="text-slate-500">Screening Completeness: </span>
              <span className="font-medium text-amber-800">{candidateAreas.screening_completeness}</span>
            </div>
          </div>
        </div>
      )}

      {/* Footer nav */}
      <div className="flex items-center justify-end pt-1">
        <Link
          to="/methodology"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-700 hover:text-blue-900 transition-colors"
        >
          Review Full Methodology & Limitations
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
};
