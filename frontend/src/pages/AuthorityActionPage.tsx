import React, { useState, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import {
  ShieldAlert,
  Download,
  AlertTriangle,
  Users,
  Building2,
  AlertCircle,
  Printer,
  RefreshCw,
  Search,
  ArrowRight,
  Filter,
  CheckCircle2,
  Info
} from 'lucide-react';
import { PriorityBadge } from '../components/shared/PriorityBadge';
import { InfoTooltip } from '../components/shared/InfoTooltip';
import { formatNumber, formatDistance } from '../utils/formatters';

const API_BASE = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';

const DISCLAIMER =
  'DECISION SUPPORT ONLY — NOT AN OFFICIAL RELOCATION ORDER, EVACUATION NOTICE, OR GOVERNMENT DECLARATION. ' +
  'All classifications are preliminary GIS screening based on Copernicus GLO-30 DEM terrain proximity and Census 2011 PCA baselines. ' +
  'Mandatory field verification, geotechnical investigation, and official SDMA/DDMA authorization are required before any administrative action.';

function fetchActionQueue(highVulnOnly: boolean, tiers: string) {
  return fetch(
    `${API_BASE}/api/authority/action-queue?tiers=${encodeURIComponent(tiers)}&high_vuln_only=${highVulnOnly}&limit=200`
  ).then(r => {
    if (!r.ok) throw new Error(`HTTP error ${r.status}`);
    return r.json();
  });
}

function fetchBlockSummary() {
  return fetch(`${API_BASE}/api/authority/block-summary`).then(r => {
    if (!r.ok) throw new Error(`HTTP error ${r.status}`);
    return r.json();
  });
}

function downloadCSV(tiers: string) {
  window.open(
    `${API_BASE}/api/authority/report.csv?tiers=${encodeURIComponent(tiers)}`,
    '_blank'
  );
}

export const AuthorityActionPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'queue' | 'blocks'>('queue');
  const [showTier2, setShowTier2] = useState(true);
  const [highVulnOnly, setHighVulnOnly] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const tiers = showTier2
    ? 'Tier1_AttentionPriority,Tier2_ElevatedAttention'
    : 'Tier1_AttentionPriority';

  const { data: queueData, isLoading: queueLoading, isError: queueError } = useQuery({
    queryKey: ['authority-queue', tiers, highVulnOnly],
    queryFn: () => fetchActionQueue(highVulnOnly, tiers),
  });

  const { data: blockData, isLoading: blockLoading } = useQuery({
    queryKey: ['authority-blocks'],
    queryFn: fetchBlockSummary,
  });

  const rawQueue = queueData?.action_queue ?? [];
  const summary = queueData?.action_queue_summary ?? {};

  // Client-side search filter
  const filteredQueue = useMemo(() => {
    if (!searchQuery.trim()) return rawQueue;
    const q = searchQuery.toLowerCase().trim();
    return rawQueue.filter((v: any) =>
      v.village_name?.toLowerCase().includes(q) ||
      String(v.village_id).includes(q) ||
      v.nearest_zone_id?.toLowerCase().includes(q)
    );
  }, [rawQueue, searchQuery]);

  return (
    <div className="space-y-6">
      {/* 1. Page Header & Export Controls */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <div className="flex items-center gap-2.5">
            <div className="p-2 rounded-xl bg-red-600 text-white shadow-sm shrink-0">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
                Authority Action Center
                <span className="px-2 py-0.5 text-[10px] font-bold rounded-full bg-red-100 text-red-700 border border-red-200">
                  SDMA / DDMA
                </span>
              </h2>
              <p className="text-xs text-slate-500 mt-0.5">
                Priority decision-support register & field assessment workflow · Rudraprayag District, Uttarakhand
              </p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2 shrink-0">
          <button
            id="btn-print-authority-report"
            onClick={() => window.print()}
            className="inline-flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-slate-700 bg-white hover:bg-slate-50 rounded-lg border border-slate-300 shadow-sm transition-all hover:border-slate-400"
          >
            <Printer className="w-3.5 h-3.5 text-slate-500" />
            <span>Print Report</span>
          </button>
          <button
            id="btn-download-priority-csv"
            onClick={() => downloadCSV(tiers)}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-blue-700 hover:bg-blue-800 rounded-lg shadow-sm transition-all hover:shadow"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download CSV</span>
          </button>
        </div>
      </div>

      {/* 2. Mandatory Disclaimer Banner */}
      <div className="bg-gradient-to-r from-red-50 to-amber-50 rounded-xl border border-red-200 p-4 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="p-1.5 rounded-lg bg-red-100 border border-red-200 text-red-700 shrink-0 mt-0.5">
            <AlertTriangle className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[11px] font-bold uppercase tracking-wider text-red-800 mb-0.5">
              Statutory Authority Notice & Advisory
            </p>
            <p className="text-xs text-red-900 leading-relaxed">
              {DISCLAIMER}
            </p>
          </div>
        </div>
      </div>

      {/* 3. Summary Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:border-slate-300 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Villages Screened</span>
            <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
              <Building2 className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">
            {formatNumber(queueData?.total_villages_screened ?? 653)}
          </p>
          <p className="text-[11px] text-slate-500 mt-1 flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-emerald-500" />
            <span>100% of Census 2011 habitations</span>
          </p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:border-red-200 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tier 1 Villages</span>
            <div className="p-2 rounded-lg bg-red-50 text-red-600">
              <AlertTriangle className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-red-700 mt-2">
            {formatNumber(summary?.tier_counts?.Tier1_AttentionPriority ?? 12)}
          </p>
          <p className="text-[11px] text-red-600 font-medium mt-1">
            Immediate field verification priority
          </p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:border-amber-200 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">Tier 2 Villages</span>
            <div className="p-2 rounded-lg bg-amber-50 text-amber-600">
              <AlertCircle className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-amber-700 mt-2">
            {formatNumber(summary?.tier_counts?.Tier2_ElevatedAttention ?? 69)}
          </p>
          <p className="text-[11px] text-amber-700 font-medium mt-1">
            1–3 year district planning review
          </p>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm hover:border-indigo-200 transition-all">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">At-Risk Population</span>
            <div className="p-2 rounded-lg bg-indigo-50 text-indigo-600">
              <Users className="w-4 h-4" />
            </div>
          </div>
          <p className="text-2xl font-bold text-slate-900 mt-2">
            {formatNumber(summary?.total_at_risk_population ?? 27762)}
          </p>
          <p className="text-[11px] text-indigo-600 font-medium mt-1">
            Residents in Tier 1 & Tier 2 zones
          </p>
        </div>
      </div>

      {/* 4. Controls & Filter Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          {/* Tab Switcher */}
          <div className="flex items-center p-1 bg-slate-100 rounded-lg border border-slate-200 shrink-0">
            <button
              onClick={() => setActiveTab('queue')}
              className={`px-3.5 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'queue'
                  ? 'bg-white text-slate-900 shadow-sm border border-slate-200/80'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Priority Action Queue ({rawQueue.length})
            </button>
            <button
              onClick={() => setActiveTab('blocks')}
              className={`px-3.5 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'blocks'
                  ? 'bg-white text-slate-900 shadow-sm border border-slate-200/80'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Sub-District Summary
            </button>
          </div>

          {/* Filters & Search */}
          {activeTab === 'queue' && (
            <div className="flex flex-wrap items-center gap-3">
              {/* Search */}
              <div className="relative min-w-[200px] flex-1 sm:flex-initial">
                <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="Filter village or ID..."
                  className="w-full pl-8 pr-3 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-1 focus:ring-blue-600 focus:bg-white transition-all text-slate-800 placeholder-slate-400"
                />
              </div>

              {/* Toggles */}
              <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-700 cursor-pointer select-none bg-slate-50 px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 transition-colors">
                <input
                  type="checkbox"
                  checked={showTier2}
                  onChange={(e) => setShowTier2(e.target.checked)}
                  className="w-3.5 h-3.5 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
                />
                <span>Include Tier 2</span>
              </label>

              <label className="inline-flex items-center gap-2 text-xs font-medium text-slate-700 cursor-pointer select-none bg-slate-50 px-2.5 py-1.5 rounded-lg border border-slate-200 hover:bg-slate-100 transition-colors">
                <input
                  type="checkbox"
                  checked={highVulnOnly}
                  onChange={(e) => setHighVulnOnly(e.target.checked)}
                  className="w-3.5 h-3.5 text-blue-600 rounded border-slate-300 focus:ring-blue-500"
                />
                <span>High Vulnerability Only (≥2 flags)</span>
              </label>
            </div>
          )}
        </div>
      </div>

      {/* 5. Main Content Area */}
      {activeTab === 'queue' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          {/* Header Bar */}
          <div className="px-5 py-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 bg-slate-50/70">
            <div className="flex items-center gap-2.5">
              <h3 className="text-sm font-bold text-slate-900">
                Action Queue for District Authorities
              </h3>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-700 border border-red-200">
                {filteredQueue.length} habitations
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Sorted by proximity to hazard red zone (closest first)
            </p>
          </div>

          {/* Table / Loading / Empty */}
          {queueLoading ? (
            <div className="p-12 text-center text-slate-500 space-y-3">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-600" />
              <p className="text-xs font-medium">Loading action queue from backend...</p>
            </div>
          ) : queueError ? (
            <div className="p-12 text-center text-red-600 space-y-2">
              <AlertCircle className="w-8 h-8 mx-auto" />
              <p className="text-xs font-bold">Failed to load action queue.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                    <th className="px-4 py-3">Habitation</th>
                    <th className="px-4 py-3">Priority Classification</th>
                    <th className="px-4 py-3">Red Zone Distance</th>
                    <th className="px-4 py-3">Population</th>
                    <th className="px-4 py-3">Households</th>
                    <th className="px-4 py-3">Demographic Context (PS-3)</th>
                    <th className="px-4 py-3">Recommended Authority Action</th>
                    <th className="px-4 py-3 text-right">Details</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {filteredQueue.map((v: any) => {
                    const isTier1 = v.priority_tier === 'Tier1_AttentionPriority';
                    return (
                      <tr
                        key={v.village_id}
                        className={`hover:bg-blue-50/40 transition-colors ${
                          isTier1 ? 'bg-red-50/20' : ''
                        }`}
                      >
                        {/* Village Name & ID */}
                        <td className="px-4 py-3 font-semibold text-slate-900">
                          <Link
                            to={`/villages/${v.village_id}`}
                            className="text-blue-700 hover:text-blue-900 hover:underline font-bold"
                          >
                            {v.village_name}
                          </Link>
                          <div className="text-[11px] font-mono text-slate-400 font-normal">
                            Census ID: {v.village_id}
                          </div>
                        </td>

                        {/* Priority Badge */}
                        <td className="px-4 py-3 whitespace-nowrap">
                          <PriorityBadge tier={v.priority_tier} size="sm" />
                          <div className="text-[10px] text-slate-500 mt-1">
                            {v.relocation_horizon_display || v.relocation_horizon || 'Routine'}
                          </div>
                        </td>

                        {/* Distance */}
                        <td className="px-4 py-3 font-mono font-semibold whitespace-nowrap">
                          <span className={isTier1 ? 'text-red-700 font-bold' : 'text-slate-800'}>
                            {v.nearest_hazard_distance_m != null
                              ? formatDistance(v.nearest_hazard_distance_m)
                              : '—'}
                          </span>
                          {v.nearest_zone_id && (
                            <div className="text-[10px] font-mono text-slate-400 font-normal">
                              Zone: {v.nearest_zone_id}
                            </div>
                          )}
                        </td>

                        {/* Population */}
                        <td className="px-4 py-3 font-medium text-slate-800">
                          {formatNumber(v.tot_pop)}
                        </td>

                        {/* Households */}
                        <td className="px-4 py-3 text-slate-600">
                          {formatNumber(v.households)}
                        </td>

                        {/* Vulnerability Context */}
                        <td className="px-4 py-3">
                          <div className="space-y-1">
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold border ${
                                (v.vulnerability_flag_count ?? 0) >= 2
                                  ? 'bg-amber-100 text-amber-800 border-amber-300'
                                  : 'bg-slate-100 text-slate-600 border-slate-200'
                              }`}
                            >
                              {v.vulnerability_context || `${v.vulnerability_flag_count ?? 0} flags`}
                            </span>
                            {v.active_vulnerability_flags?.length > 0 && (
                              <div className="flex gap-1 flex-wrap">
                                {v.active_vulnerability_flags.slice(0, 2).map((flag: string) => (
                                  <span
                                    key={flag}
                                    className="px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 text-[9px] font-medium"
                                  >
                                    {flag}
                                  </span>
                                ))}
                                {v.active_vulnerability_flags.length > 2 && (
                                  <span className="text-[9px] text-slate-400 font-medium">
                                    +{v.active_vulnerability_flags.length - 2} more
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                        </td>

                        {/* Recommended Action */}
                        <td className="px-4 py-3 text-slate-600 text-[11px] max-w-xs leading-relaxed">
                          {v.recommended_action || (
                            isTier1
                              ? 'Immediate geotechnical verification & consultation required.'
                              : 'Include in medium-term district mitigation planning.'
                          )}
                        </td>

                        {/* Action Link */}
                        <td className="px-4 py-3 text-right whitespace-nowrap">
                          <Link
                            to={`/villages/${v.village_id}`}
                            className="inline-flex items-center gap-1 px-2.5 py-1 text-[11px] font-semibold text-blue-700 bg-blue-50 hover:bg-blue-100 rounded-md border border-blue-200 transition-colors"
                          >
                            Profile
                            <ArrowRight className="w-3 h-3" />
                          </Link>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>

              {filteredQueue.length === 0 && !queueLoading && (
                <div className="p-12 text-center text-slate-500 space-y-2">
                  <Filter className="w-8 h-8 text-slate-300 mx-auto" />
                  <p className="text-sm font-semibold text-slate-700">No habitations match your criteria</p>
                  <p className="text-xs text-slate-400">Try clearing the search query or enabling Tier 2.</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 6. Sub-District / Block Summary Tab */}
      {activeTab === 'blocks' && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-slate-200 bg-slate-50/70">
            <h3 className="text-sm font-bold text-slate-900">
              Administrative Sub-District / Block Aggregations
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Aggregated by administrative sub-district. Sorted by Tier 1 + Tier 2 habitation concentration.
            </p>
          </div>

          {blockLoading ? (
            <div className="p-12 text-center text-slate-500 space-y-3">
              <RefreshCw className="w-6 h-6 animate-spin mx-auto text-blue-600" />
              <p className="text-xs font-medium">Aggregating block statistics...</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-500 border-b border-slate-200">
                    <th className="px-4 py-3">Sub-District / Block ID</th>
                    <th className="px-4 py-3">Total Villages</th>
                    <th className="px-4 py-3">Tier 1 (Immediate)</th>
                    <th className="px-4 py-3">Tier 2 (Short-Term)</th>
                    <th className="px-4 py-3">Tier 3 (Monitoring)</th>
                    <th className="px-4 py-3">At-Risk Pop (T1+T2)</th>
                    <th className="px-4 py-3">High-Vulnerability Villages</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-xs">
                  {(blockData?.block_summary ?? []).map((b: any, i: number) => (
                    <tr key={b.subdist_id ?? i} className="hover:bg-slate-50 transition-colors">
                      <td className="px-4 py-3 font-bold text-slate-900 font-mono">
                        {b.subdist_id}
                      </td>
                      <td className="px-4 py-3 font-medium text-slate-700">
                        {formatNumber(b.total_villages)}
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded font-bold text-xs bg-red-100 text-red-800 border border-red-200">
                          {b.tier1_immediate}
                        </span>
                      </td>
                      <td className="px-4 py-3">
                        <span className="px-2 py-0.5 rounded font-bold text-xs bg-amber-100 text-amber-800 border border-amber-200">
                          {b.tier2_short_term}
                        </span>
                      </td>
                      <td className="px-4 py-3 font-medium text-amber-700">
                        {b.tier3_monitoring}
                      </td>
                      <td className="px-4 py-3 font-semibold text-slate-900">
                        {formatNumber(b.at_risk_population_tier1_2)}
                      </td>
                      <td className="px-4 py-3">
                        <span
                          className={`font-semibold ${
                            b.high_vulnerability_villages > 0 ? 'text-amber-700' : 'text-slate-500'
                          }`}
                        >
                          {b.high_vulnerability_villages}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {(!blockData?.block_summary || blockData.block_summary.length === 0) && (
                <div className="p-12 text-center text-slate-500 space-y-2">
                  <Info className="w-8 h-8 text-slate-300 mx-auto" />
                  <p className="text-xs font-semibold text-slate-700">
                    {blockData?.status === 'BLOCK_ID_UNAVAILABLE'
                      ? 'Sub-district aggregation unavailable — SHRUG sub-district identifiers not attached.'
                      : 'No sub-district aggregation data available.'}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* 7. Methodology & Scientific Caveats Card */}
      <div className="bg-slate-50 rounded-xl border border-slate-200 p-4 space-y-2 text-xs text-slate-600">
        <div className="flex items-center justify-between">
          <span className="font-bold text-slate-900 uppercase tracking-wide text-[11px] flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
            Decision-Support Methodology Transparency
          </span>
          <InfoTooltip
            title="Scientific Classification Rules"
            content="Tier 1: Habitation centroid within 500m of Candidate Hazard Red Zone AND Multihazard class >= 2. Tier 2: Within 2,000m. Vulnerability flags are Census 2011 upper tertile thresholds."
            side="top"
          />
        </div>
        <p className="leading-relaxed">
          Rule-based GIS screening using Copernicus GLO-30 DEM terrain classification and Census 2011 PCA baselines.
          Tier 1 represents highest priority for mandatory on-site geotechnical screening by SDMA/DDMA technical teams.
          Vulnerability flags serve strictly as demographic context and do not supersede spatial terrain criteria.
        </p>
      </div>
    </div>
  );
};
