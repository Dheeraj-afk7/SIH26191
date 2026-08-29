import React, { useState } from 'react';
import { Building2, Search, ArrowRight, Map } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useVillages } from '../hooks';
import { PriorityBadge } from '../components/shared/PriorityBadge';
import { PriorityTierKey, PRIORITY_TIERS } from '../config/constants';
import { formatNumber, formatDistance } from '../utils/formatters';

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

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <Building2 className="w-5 h-5 text-blue-700" />
            Village Decision-Support Explorer
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Directory of 653 habitations in Rudraprayag District attributed with multi-hazard proximity and priority tiers
          </p>
        </div>
        <Link
          to="/map"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-blue-700 px-3 py-1.5 rounded-lg border border-slate-200 hover:border-blue-300 hover:bg-blue-50 transition-all"
        >
          <Map className="w-3.5 h-3.5" />
          View on GIS Map
          <ArrowRight className="w-3 h-3" />
        </Link>
      </div>

      {/* Filter and Search Bar */}
      <div className="bg-white rounded-xl border border-slate-200 p-3.5 shadow-sm">
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
              className="w-full pl-9 pr-4 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 bg-slate-50 placeholder:text-slate-400"
            />
          </div>

          {/* Tier Filter Buttons */}
          <div className="flex flex-wrap items-center gap-1.5 w-full sm:w-auto">
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
            {Object.values(PRIORITY_TIERS).map((t) => (
              <button
                key={t.key}
                onClick={() => { setSelectedTier(t.key); setPage(0); }}
                className={`px-2.5 py-1.5 rounded-lg text-[11px] font-bold border transition-colors ${
                  selectedTier === t.key
                    ? 'bg-blue-700 text-white border-blue-700 shadow-sm'
                    : `${t.badgeBg} ${t.badgeText} ${t.badgeBorder} hover:brightness-95`
                }`}
              >
                {t.shortLabel}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-100/80 text-slate-500 uppercase font-bold text-[10px] tracking-wider border-b border-slate-200">
              <tr>
                <th className="py-3 px-4">Village</th>
                <th className="py-3 px-4">Priority Classification</th>
                <th className="py-3 px-4">Dist to Red Zone</th>
                <th className="py-3 px-4">Nearest Zone</th>
                <th className="py-3 px-4">Population</th>
                <th className="py-3 px-4">MH Class</th>
                <th className="py-3 px-4 text-right">Actions</th>
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
                      <PriorityBadge tier={p.priority_tier} size="sm" />
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
            >
              ← Previous
            </button>
            <span className="font-bold text-slate-700 px-1">Page {page + 1}</span>
            <button
              disabled={villages.length < limit}
              onClick={() => setPage(page + 1)}
              className="px-3 py-1 rounded border border-slate-300 bg-white font-medium hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Next →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
