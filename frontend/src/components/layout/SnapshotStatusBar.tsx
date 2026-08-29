import React from 'react';
import { Database, Clock, ShieldCheck, AlertCircle } from 'lucide-react';
import { useDecisionSummary } from '../../hooks';
import { formatTimestamp } from '../../utils/formatters';
import { PROJECT_INFO } from '../../config/constants';

export const SnapshotStatusBar: React.FC = () => {
  const { data: summary, isLoading, isError } = useDecisionSummary();

  const generatedUtc = summary?.generated_utc;

  return (
    <footer className="bg-navy-950 text-slate-400 text-[11px] border-t border-navy-800 py-1.5 px-4 z-20 shrink-0">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-y-1 gap-x-4">
        {/* Left Side: Generation Timestamp & Population Baseline */}
        <div className="flex items-center gap-3 flex-wrap">
          <div className="flex items-center gap-1.5 text-slate-300">
            <Database className="w-3.5 h-3.5 text-blue-400" />
            <span className="font-semibold text-white">Dataset Mode:</span>
            <span>Deterministic GIS Snapshot</span>
          </div>

          <span className="text-navy-700 hidden sm:inline">|</span>

          <div className="flex items-center gap-1.5">
            <Clock className="w-3.5 h-3.5 text-slate-400" />
            <span>Generated:</span>
            <span className="font-mono text-slate-200">
              {isLoading ? 'Loading timestamp...' : isError ? 'Backend Offline' : formatTimestamp(generatedUtc)}
            </span>
          </div>

          <span className="text-navy-700 hidden md:inline">|</span>

          <div className="hidden md:flex items-center gap-1 text-slate-400">
            <span>Baseline:</span>
            <span className="text-slate-300">{PROJECT_INFO.POPULATION_BASELINE}</span>
          </div>
        </div>

        {/* Right Side: Real-time Status Badge & CRS */}
        <div className="flex items-center gap-3">
          <div className="inline-flex items-center gap-1 px-2 py-0.5 rounded bg-amber-950/80 text-amber-300 border border-amber-800 text-[10px] font-medium tracking-wide">
            <AlertCircle className="w-3 h-3 text-amber-400" />
            <span>Real-time Alerts: NOT INTEGRATED</span>
          </div>

          <div className="hidden lg:flex items-center gap-1 text-slate-400">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
            <span>Spatial Engine: {PROJECT_INFO.METRIC_CRS}</span>
          </div>
        </div>
      </div>
    </footer>
  );
};
