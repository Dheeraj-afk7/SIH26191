import React from 'react';
import { CheckCircle2, AlertTriangle, XCircle, HelpCircle } from 'lucide-react';

export type DataStatusType = 
  | 'AVAILABLE' 
  | 'CONFIGURED_BUT_MISSING' 
  | 'NOT_CONFIGURED' 
  | 'NOT_ACQUIRED' 
  | 'PASS' 
  | 'WARNING' 
  | 'FAIL';

interface StatusBadgeProps {
  status: DataStatusType | string;
  label?: string;
  size?: 'sm' | 'md';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status,
  label,
  size = 'md',
}) => {
  let bg = 'bg-slate-100';
  let text = 'text-slate-700';
  let border = 'border-slate-300';
  let Icon = HelpCircle;
  let defaultLabel = status;

  switch (status) {
    case 'AVAILABLE':
    case 'PASS':
      bg = 'bg-emerald-50';
      text = 'text-emerald-800';
      border = 'border-emerald-300';
      Icon = CheckCircle2;
      defaultLabel = status === 'PASS' ? 'Pass' : 'Available';
      break;

    case 'CONFIGURED_BUT_MISSING':
    case 'WARNING':
      bg = 'bg-amber-50';
      text = 'text-amber-800';
      border = 'border-amber-300';
      Icon = AlertTriangle;
      defaultLabel = status === 'WARNING' ? 'Warning' : 'Configured (Missing File)';
      break;

    case 'NOT_CONFIGURED':
      bg = 'bg-slate-100';
      text = 'text-slate-600';
      border = 'border-slate-300';
      Icon = HelpCircle;
      defaultLabel = 'Not Configured';
      break;

    case 'NOT_ACQUIRED':
    case 'FAIL':
      bg = 'bg-rose-50';
      text = 'text-rose-800';
      border = 'border-rose-300';
      Icon = XCircle;
      defaultLabel = status === 'FAIL' ? 'Fail' : 'Not Acquired';
      break;
  }

  const sizeClasses = size === 'sm' ? 'px-2 py-0.5 text-xs' : 'px-2.5 py-1 text-xs font-medium';

  return (
    <span className={`inline-flex items-center gap-1.5 rounded border ${bg} ${text} ${border} ${sizeClasses}`}>
      <Icon className="w-3.5 h-3.5 shrink-0" />
      <span>{label || defaultLabel}</span>
    </span>
  );
};
