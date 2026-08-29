import React from 'react';
import { 
  Building2, 
  Users, 
  AlertTriangle, 
  Layers, 
  Map, 
  FileText, 
  ArrowRight,
  ShieldAlert,
  TrendingUp,
  Activity,
  CheckCircle2
} from 'lucide-react';
import { Link } from 'react-router-dom';
import { useDecisionSummary } from '../hooks';
import { KPICard } from '../components/shared/KPICard';
import { PriorityBadge } from '../components/shared/PriorityBadge';
import { TierDistributionChart } from '../components/dashboard/TierDistributionChart';
import { DashboardMapPreview } from '../components/dashboard/DashboardMapPreview';
import { formatNumber } from '../utils/formatters';

export const DashboardPage: React.FC = () => {
  const { data: summary, isLoading } = useDecisionSummary();

  const villagePriority = summary?.village_priority;
  const tierDistribution = villagePriority?.tier_distribution;
  const candidateAreas = summary?.candidate_areas;

  const tier1Count = tierDistribution?.Tier1_AttentionPriority?.count ?? 12;
  const tier1Pop = tierDistribution?.Tier1_AttentionPriority?.population ?? 4750;
  const tier2Count = tierDistribution?.Tier2_ElevatedAttention?.count ?? 69;
  const tier3Count = tierDistribution?.Tier3_Monitoring?.count ?? 204;
  const totalHabitations = villagePriority?.total_habitations ?? 653;
  const totalPop = villagePriority?.total_population ?? 232360;

  return (
    <div className="space-y-5">
      {/* 1. Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            District Decision-Support Overview
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Rudraprayag District, Uttarakhand · Deterministic GIS Multi-Hazard & Exposure Analysis
          </p>
        </div>
        <Link
          to="/map"
          className="inline-flex items-center gap-2 px-3.5 py-2 text-xs font-semibold text-white bg-blue-700 hover:bg-blue-800 rounded-lg shadow-sm transition-colors"
        >
          <Map className="w-4 h-4" />
          <span>Open Interactive GIS Map</span>
        </Link>
      </div>

      {/* 2. Executive Screening Insight Banner */}
      <div className="bg-gradient-to-r from-slate-900 to-navy-900 rounded-xl border border-slate-700 p-5 shadow-md">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-5">
          <div className="flex items-start gap-4">
            <div className="p-2.5 rounded-lg bg-red-500/20 border border-red-500/30 shrink-0">
              <ShieldAlert className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <p className="text-[11px] font-semibold uppercase tracking-widest text-slate-400 mb-1">
                Priority Screening Overview
              </p>
              <p className="text-xl font-bold text-white leading-tight">
                <span className="text-red-400">{isLoading ? '...' : tier1Count}</span> habitations currently require highest attention
              </p>
              <p className="text-xs text-slate-400 mt-1">
                Based on preliminary hazard-proximity screening of {isLoading ? '...' : formatNumber(totalHabitations)} habitations
                across Rudraprayag District.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-3 gap-3 lg:shrink-0">
            <div className="bg-white/5 rounded-lg p-3 border border-white/10 text-center">
              <p className="text-[10px] font-semibold uppercase text-slate-400 tracking-wider">Tier 1 Population</p>
              <p className="text-lg font-bold text-white mt-0.5">{isLoading ? '...' : formatNumber(tier1Pop)}</p>
              <p className="text-[10px] text-slate-500">residents</p>
            </div>
            <div className="bg-white/5 rounded-lg p-3 border border-white/10 text-center">
              <p className="text-[10px] font-semibold uppercase text-slate-400 tracking-wider">Classification</p>
              <p className="text-[11px] font-bold text-amber-300 mt-0.5 leading-tight">Rule-Based<br/>Preliminary</p>
            </div>
            <div className="bg-white/5 rounded-lg p-3 border border-white/10 text-center">
              <p className="text-[10px] font-semibold uppercase text-slate-400 tracking-wider">Review Status</p>
              <p className="text-[11px] font-bold text-orange-300 mt-0.5 leading-tight">Field<br/>Validation Req.</p>
            </div>
          </div>
        </div>

        <div className="mt-4 pt-4 border-t border-white/10 flex flex-wrap items-center gap-4 text-[11px] text-slate-400">
          <div className="flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400" />
            <span><strong className="text-slate-300">{formatNumber(totalHabitations)}</strong> habitations analysed</span>
          </div>
          <div className="flex items-center gap-1.5">
            <Activity className="w-3.5 h-3.5 text-blue-400" />
            <span>Multi-Hazard Proximity + MH Class Rule</span>
          </div>
          <div className="flex items-center gap-1.5">
            <TrendingUp className="w-3.5 h-3.5 text-amber-400" />
            <span>Census 2011 Baseline · 30m DEM · SHRUG v2.2</span>
          </div>
          <Link to="/methodology" className="ml-auto inline-flex items-center gap-1 text-blue-400 hover:text-blue-300 font-semibold transition-colors">
            <FileText className="w-3.5 h-3.5" />
            Review Full Methodology
          </Link>
        </div>
      </div>

      {/* 3. Top-Level KPI Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
        <KPICard
          label="Total Habitations"
          value={isLoading ? '...' : formatNumber(totalHabitations)}
          subValue={isLoading ? '' : `${formatNumber(totalPop)} residents`}
          indicatorColor="border-slate-600"
          icon={Building2}
          iconBg="bg-slate-100"
          iconColor="text-slate-600"
        />
        <KPICard
          label="Tier 1 — Attention"
          value={isLoading ? '...' : formatNumber(tier1Count)}
          subValue={isLoading ? '' : `${formatNumber(tier1Pop)} population`}
          indicatorColor="border-red-600"
          icon={AlertTriangle}
          iconBg="bg-red-50"
          iconColor="text-red-600"
        />
        <KPICard
          label="Tier 2 — Elevated"
          value={isLoading ? '...' : formatNumber(tier2Count)}
          subValue={isLoading ? '' : `${formatNumber(tierDistribution?.Tier2_ElevatedAttention?.population ?? 23012)} population`}
          indicatorColor="border-amber-500"
          icon={Users}
          iconBg="bg-amber-50"
          iconColor="text-amber-600"
        />
        <KPICard
          label="Tier 3 — Monitoring"
          value={isLoading ? '...' : formatNumber(tier3Count)}
          subValue={isLoading ? '' : `${formatNumber(tierDistribution?.Tier3_Monitoring?.population ?? 64463)} population`}
          indicatorColor="border-blue-400"
          icon={Building2}
          iconBg="bg-blue-50"
          iconColor="text-blue-500"
        />
        <KPICard
          label="Candidate Areas"
          value={isLoading ? '...' : `${candidateAreas?.total_features ?? 5} Areas`}
          subValue="Unfiltered Terrain Extent"
          indicatorColor="border-amber-600"
          icon={Layers}
          iconBg="bg-amber-50"
          iconColor="text-amber-600"
        />
      </div>

      {/* 4. Interactive Preview & Tier Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <TierDistributionChart />
        <DashboardMapPreview />
      </div>

      {/* 5. Quick Actions */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-sm">
        <h3 className="text-[11px] font-bold text-slate-500 uppercase tracking-widest mb-3">
          Decision-Support Exploration Flow
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5">
          <Link
            to="/villages"
            className="flex items-start gap-3 p-3 rounded-lg border border-red-200 bg-red-50/50 hover:bg-red-50 hover:border-red-300 transition-all group"
          >
            <div className="p-2 bg-red-100 text-red-700 rounded-md shrink-0 mt-0.5">
              <ShieldAlert className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-red-950">Explore Priority Villages</span>
                <ArrowRight className="w-3.5 h-3.5 text-red-500 group-hover:translate-x-0.5 transition-transform" />
              </div>
              <p className="text-[11px] text-red-700/70 mt-0.5 leading-snug">
                Step 1 · Browse all {formatNumber(totalHabitations)} habitations by tier
              </p>
            </div>
          </Link>

          <Link
            to="/map"
            className="flex items-start gap-3 p-3 rounded-lg border border-blue-200 bg-blue-50/50 hover:bg-blue-50 hover:border-blue-300 transition-all group"
          >
            <div className="p-2 bg-blue-100 text-blue-700 rounded-md shrink-0 mt-0.5">
              <Map className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-blue-950">Interactive GIS Map</span>
                <ArrowRight className="w-3.5 h-3.5 text-blue-500 group-hover:translate-x-0.5 transition-transform" />
              </div>
              <p className="text-[11px] text-blue-700/70 mt-0.5 leading-snug">
                Step 2 · Red zones, villages & terrain
              </p>
            </div>
          </Link>

          <Link
            to="/candidate-areas"
            className="flex items-start gap-3 p-3 rounded-lg border border-amber-200 bg-amber-50/50 hover:bg-amber-50 hover:border-amber-300 transition-all group"
          >
            <div className="p-2 bg-amber-100 text-amber-700 rounded-md shrink-0 mt-0.5">
              <Layers className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-amber-950">Candidate Area Context</span>
                <ArrowRight className="w-3.5 h-3.5 text-amber-600 group-hover:translate-x-0.5 transition-transform" />
              </div>
              <p className="text-[11px] text-amber-700/70 mt-0.5 leading-snug">
                Step 3 · Preliminary terrain screening
              </p>
            </div>
          </Link>

          <Link
            to="/methodology"
            className="flex items-start gap-3 p-3 rounded-lg border border-slate-200 bg-slate-50/60 hover:bg-slate-100 hover:border-slate-300 transition-all group"
          >
            <div className="p-2 bg-slate-200 text-slate-700 rounded-md shrink-0 mt-0.5">
              <FileText className="w-4 h-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-900">Methodology & Limitations</span>
                <ArrowRight className="w-3.5 h-3.5 text-slate-500 group-hover:translate-x-0.5 transition-transform" />
              </div>
              <p className="text-[11px] text-slate-600 mt-0.5 leading-snug">
                Step 4 · Data sources, rules & caveats
              </p>
            </div>
          </Link>
        </div>
      </div>

      {/* 6. Top Attention Priority Habitations Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b border-slate-200 flex items-center justify-between bg-slate-50/60">
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              Tier 1 — Highest Attention Priority Habitations
            </h3>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Within 500 m of Candidate Red Zone + Multi-Hazard Class ≥ 2 at centroid · {formatNumber(tier1Count)} habitations · {formatNumber(tier1Pop)} population
            </p>
          </div>
          <Link
            to="/villages"
            className="text-xs font-semibold text-blue-700 hover:text-blue-800 inline-flex items-center gap-1 transition-colors"
          >
            <span>Explore All {formatNumber(totalHabitations)}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/70 text-slate-600 uppercase font-semibold text-[10px] tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-2.5 px-4">Village</th>
                <th className="py-2.5 px-4">Priority</th>
                <th className="py-2.5 px-4">Dist. to Red Zone</th>
                <th className="py-2.5 px-4">Nearest Zone</th>
                <th className="py-2.5 px-4">Population</th>
                <th className="py-2.5 px-4 text-right">Profile</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-800">
              {villagePriority?.top_attention_priority_villages?.map((v) => (
                <tr key={v.village_id} className="hover:bg-red-50/40 transition-colors">
                  <td className="py-2.5 px-4">
                    <div>
                      <span className="font-bold text-slate-900">{v.village_name}</span>
                      <span className="ml-2 font-mono text-[10px] text-slate-400">#{v.village_id}</span>
                    </div>
                  </td>
                  <td className="py-2.5 px-4">
                    <PriorityBadge tier="Tier1_AttentionPriority" size="sm" />
                  </td>
                  <td className="py-2.5 px-4 font-mono text-red-700 font-semibold">
                    {v.nearest_hazard_distance_m.toFixed(0)} m
                  </td>
                  <td className="py-2.5 px-4 font-mono text-slate-500 text-[11px]">{v.nearest_zone_id}</td>
                  <td className="py-2.5 px-4 font-mono">{formatNumber(v.tot_pop)}</td>
                  <td className="py-2.5 px-4 text-right">
                    <Link
                      to={`/villages/${v.village_id}`}
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-700 hover:text-blue-900 bg-blue-50 hover:bg-blue-100 px-2 py-1 rounded border border-blue-200 transition-colors"
                    >
                      Decision Profile
                      <ArrowRight className="w-3 h-3" />
                    </Link>
                  </td>
                </tr>
              )) || (
                <tr>
                  <td colSpan={6} className="py-8 text-center text-slate-500 text-xs">
                    {isLoading ? 'Loading priority habitations from backend...' : 'No data loaded.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
