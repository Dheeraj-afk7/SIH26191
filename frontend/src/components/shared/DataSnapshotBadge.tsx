import React from 'react';
import { Database, Clock } from 'lucide-react';
import { formatTimestamp } from '../../utils/formatters';

interface DataSnapshotBadgeProps {
  generatedUtc?: string;
  className?: string;
}

export const DataSnapshotBadge: React.FC<DataSnapshotBadgeProps> = ({
  generatedUtc,
  className = '',
}) => {
  return (
    <div className={`inline-flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-slate-500 bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-sm ${className}`}>
      <span className="inline-flex items-center gap-1 font-medium text-slate-700">
        <Database className="w-3.5 h-3.5 text-blue-600" />
        <span>Data Snapshot Mode</span>
      </span>
      <span className="text-slate-300">•</span>
      <span className="inline-flex items-center gap-1">
        <Clock className="w-3.5 h-3.5 text-slate-400" />
        <span>Generated: {formatTimestamp(generatedUtc)}</span>
      </span>
      <span className="text-slate-300">•</span>
      <span className="px-1.5 py-0.5 rounded bg-amber-50 text-amber-700 border border-amber-200 font-medium text-[10px] tracking-wider uppercase">
        Real-time: Not Integrated
      </span>
    </div>
  );
};
