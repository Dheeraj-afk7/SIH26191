import React, { useState } from 'react';
import { Building2, Search, ArrowRight, Map, Filter, RotateCcw } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useVillages } from '../hooks';
import { PriorityBadge } from '../components/shared/PriorityBadge';
import { PriorityTierKey, PRIORITY_TIERS } from '../config/constants';
import { formatNumber, formatDistance } from '../utils/formatters';
import { InfoTooltip } from '../components/shared/InfoTooltip';

export const VillageExplorerPage: React.FC = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedTier, setSelectedTier] = useState<PriorityTierKey | undefined>(undefined);
  const [page, setPage] = useState(0);
  const limit = 25;

  const { data: villageData, isLoading } = useVillages({
    name: searchTerm || undefined,
    priority_tier: selectedTier,
    limit,
    offset: page * limit,
  });

  const villages = villageData?.features || [];

  const handleResetFilters = () => {
    setSearchTerm('');
    setSelectedTier(undefined);
    setPage(0);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
              <Building2 className="w-5 h-5 text-blue-700" />
              Village Decision-Support Explorer
            </h2>
            <InfoTooltip
              title="Village Explorer"
              content="Directory of all 653 habitations in Rudraprayag District attributed with multi-hazard proximity distance, hazard class, and priority classification."
              side="bottom"
            />
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            Directory of 653 habitations in Rudraprayag District attributed with multi-hazard proximity and priority tiers
          </p>
        </div>
        <div className="flex items-center gap-1.5 shrink-0">
          <Link
            to="/map"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-blue-700 px-3 py-1.5 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-all"
          >
            <Map className="w-3.5 h-3.5" />
            View on GIS Map
            <ArrowRight className="w-3 h-3" />
          </Link>
          <InfoTooltip
            title="Spatial Map View"
            content="View all 653 habitations plotted on the Leaflet spatial map alongside 289 red zone polygons and candidate terrain."
            side="bottom"
          />
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-3.5 shadow-sm space-y-2.5">
        <div className="flex items-center justify-between text-xs text-slate-500 pb-1 border-b border-slate-100">
          <div className="flex items-center gap-1.5 font-semibold text-slate-700">
            <Filter className="w-3.5 h-3.5 text-blue-600" />
            <span>Search & Tier Filters</span>
            <InfoTooltip
              title="Filtering System"
              content="Filter habitations by typing a village name/ID or clicking a specific priority tier button."
              side="right"
            />
          </div>
          {(searchTerm || selectedTier) && (
            <button
              onClick={handleResetFilters}
              className="inline-flex items-center gap-1 text-[11px] font-semibold text-slate-500 hover:text-rose-600 transition-colors"
            >
              <RotateCcw className="w-3 h-3" />
              Reset Filters
            </button>
          )}
        </div>

        <div className="flex flex-col sm:flex-row items-center gap-3">
          {/* Search Input */}
          <div className="relative flex-1 w-full">
            <Search className="w-4 h-4 absolute left-3 top-2.5 text-slate-400" />
            <input
              type="text"
              placeholder="Search by village name (e.g. Marora, Gaurikund, Khat)..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(0);
              }}
              className="w-full pl-9 pr-8 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-slate-50 placeholder:text-slate-400"
            />
            <div className="absolute right-2.5 top-2">
              <InfoTooltip
                title="Search Filter"
                content="Search for habitations in real-time by village name or census identifier across the full 653-village directory."
                side="left"
              />
            </div>
          </div>

          {/* Tier Filter Buttons */}
          <div className="flex flex-wrap items-center gap-1.5 w-full sm:w-auto">
            <div className="inline-flex items-center">
              <button
                onClick={() => { setSelectedTier(undefined); setPage(0); }}
                className={`px-2.5 py-1.5 rounded-lg text-[11px] font-bold border transition-colors ${
                  selectedTier === undefined
                    ? 'bg-slate-800 text-white border-slate-800 shadow-sm'
                    : 'bg-white text-slate-600 border-slate-300 hover:bg-slate-50'
                }`}
              >
                All Tiers
              </button>
            </div>
            {Object.values(PRIORITY_TIERS).map((t) => (
              <div key={t.key} className="inline-flex items-center">
                <button
                  onClick={() => { setSelectedTier(t.key); setPage(0); }}
                  className={`px-2.5 py-1.5 rounded-lg text-[11px] font-bold border transition-colors ${
                    selectedTier === t.key
                      ? 'bg-blue-700 text-white border-blue-700 shadow-sm'
                      : `${t.badgeBg} ${t.badgeText} ${t.badgeBorder} hover:brightness-95`
                  }`}
                  title={t.label}
                >
                  {t.shortLabel}
                </button>
              </div>
            ))}
            <InfoTooltip
              title="Tier Filter Options"
              content="Filter the village table by deterministic priority tier: Tier 1 (Attention ≤500m), Tier 2 (Elevated ≤2km), Tier 3 (Monitoring ≤5km), or Beyond Proximity (>5km)."
              side="top"
            />
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/80 text-slate-500 uppercase font-bold text-[10px] tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">
                  <div className="flex items-center gap-1">
                    <span>Village</span>
                    <InfoTooltip title="Village Name & Census ID" content="Administrative Census 2011 village name and primary numeric census ID." side="top" />
                  </div>
                </th>
                <th className="py-3 px-4">
                  <div className="flex items-center gap-1">
                    <span>Priority Classification</span>
                    <InfoTooltip title="Priority Classification Tier" content="Deterministic screening tier assigned based on proximity to candidate red zones and centroid multi-hazard class." side="top" />
                  </div>
                </th>
                <th className="py-3 px-4">
                  <div className="flex items-center gap-1">
                    <span>Dist to Red Zone</span>
                    <InfoTooltip title="Distance to Candidate Red Zone" content="Planar Euclidean distance in meters from the village centroid to the nearest candidate hazard red zone polygon boundary." side="top" />
                  </div>
                </th>
                <th className="py-3 px-4">
                  <div className="flex items-center gap-1">
                    <span>Nearest Zone</span>
                    <InfoTooltip title="Nearest Hazard Zone ID" content="Identifier of the closest candidate hazard red zone polygon (RZ-xxxx)." side="top" />
                  </div>
                </th>
                <th className="py-3 px-4">
                  <div className="flex items-center gap-1">
                    <span>Population</span>
                    <InfoTooltip title="Population Baseline" content="Census 2011 total resident population." side="top" />
                  </div>
                </th>
                <th className="py-3 px-4">
                  <div className="flex items-center gap-1">
                    <span>MH Class</span>
                    <InfoTooltip title="Multi-Hazard Class at Centroid" content="Multi-hazard screening score class at the village centroid pixel: Class 1 (Baseline) vs Class 2+ (Moderate-to-High)." side="top" />
                  </div>
                </th>
                <th className="py-3 px-4 text-right">
                  <div className="flex items-center justify-end gap-1">
                    <span>Actions</span>
                    <InfoTooltip title="View Decision Profile" content="Opens full decision-support dossier for this village including reasoning, hazard proximity metrics, and demographic indicators." side="top" />
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-800">
              {villages.map((feature) => {
                const p = feature.properties;
                const isTier1 = p.priority_tier === 'Tier1_AttentionPriority';
                return (
                  <tr
                    key={p.village_id}
                    className={`hover:bg-slate-50 transition-colors ${isTier1 ? 'bg-red-50/30' : ''}`}
                  >
                    <td className="py-2.5 px-4">
                      <div>
                        <span className="font-bold text-slate-900">{p.village_name}</span>
                        <span className="ml-1.5 font-mono text-[10px] text-slate-400">#{p.village_id}</span>
                      </div>
                    </td>
                    <td className="py-2.5 px-4">
                      <PriorityBadge tier={p.priority_tier} size="sm" showInfoTooltip={true} />
                    </td>
                    <td className={`py-2.5 px-4 font-mono font-semibold ${isTier1 ? 'text-red-700' : 'text-slate-700'}`}>
                      {formatDistance(p.nearest_hazard_distance_m)}
                    </td>
                    <td className="py-2.5 px-4 font-mono text-slate-500 text-[11px]">{p.nearest_zone_id}</td>
                    <td className="py-2.5 px-4 font-mono">{formatNumber(p.tot_pop)}</td>
                    <td className="py-2.5 px-4 font-mono text-slate-600">
                      <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold ${
                        (p.mh_class_at_centroid || 1) >= 2
                          ? 'bg-amber-100 text-amber-800 border border-amber-200'
                          : 'bg-slate-100 text-slate-600 border border-slate-200'
                      }`}>
                        Class {p.mh_class_at_centroid || 1}
                      </span>
                    </td>
                    <td className="py-2.5 px-4 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Link
                          to={`/villages/${p.village_id}`}
                          className="inline-flex items-center gap-1 text-[11px] font-semibold text-blue-700 hover:text-blue-900 bg-blue-50 hover:bg-blue-100 px-2 py-1 rounded border border-blue-200 transition-colors"
                          title={`Inspect decision profile for ${p.village_name}`}
                        >
                          Profile
                          <ArrowRight className="w-3 h-3" />
                        </Link>
                      </div>
                    </td>
                  </tr>
                );
              })}

              {villages.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-10 text-center text-slate-500 text-xs">
                    {isLoading
                      ? 'Fetching habitations from backend...'
                      : 'No matching habitations found. Try adjusting the search or filter.'}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Bar */}
        <div className="px-4 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-600">
          <div>
            {villages.length > 0 && (
              <span>
                Showing <strong>{page * limit + 1}–{page * limit + villages.length}</strong> habitations
                {selectedTier && <span> · Filtered: <strong>{PRIORITY_TIERS[selectedTier]?.label}</strong></span>}
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              disabled={page === 0}
              onClick={() => setPage(page - 1)}
              className="px-3 py-1 rounded border border-slate-300 bg-white font-medium hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              title="Previous 25 habitations"
            >
              ← Previous
            </button>
            <span className="font-bold text-slate-700 px-1">Page {page + 1}</span>
            <button
              disabled={villages.length < limit}
              onClick={() => setPage(page + 1)}
              className="px-3 py-1 rounded border border-slate-300 bg-white font-medium hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              title="Next 25 habitations"
            >
              Next →
            </button>
            <InfoTooltip
              title="Table Pagination"
              content="Browse habitations 25 records per page. Use Previous and Next to navigate."
              side="top"
            />
          </div>
        </div>
      </div>
    </div>
  );
};
