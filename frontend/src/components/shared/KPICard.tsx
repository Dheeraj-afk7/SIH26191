import React from 'react';
import { LucideIcon } from 'lucide-react';

interface KPICardProps {
  label: string;
  value: string | number;
  subValue?: string;
  indicatorColor?: string;
  icon?: LucideIcon;
  iconBg?: string;
  iconColor?: string;
  onClick?: () => void;
  className?: string;
}

export const KPICard: React.FC<KPICardProps> = ({
  label,
  value,
  subValue,
  indicatorColor = 'border-slate-400',
  icon: Icon,
  iconBg = 'bg-slate-100',
  iconColor = 'text-slate-600',
  onClick,
  className = '',
}) => {
  const isClickable = Boolean(onClick);

  return (
    <div
      onClick={onClick}
      className={`bg-white rounded-xl border border-slate-200 border-l-4 ${indicatorColor} p-4 shadow-sm transition-all duration-200 ${
        isClickable ? 'cursor-pointer hover:shadow-md hover:border-slate-300 active:scale-[0.99]' : ''
      } ${className}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest leading-tight">
            {label}
          </p>
          <p className="mt-1.5 text-2xl font-bold text-slate-900 tracking-tight leading-none">
            {value}
          </p>
          {subValue && (
            <p className="mt-1.5 text-[11px] text-slate-500 leading-snug">
              {subValue}
            </p>
          )}
        </div>
        {Icon && (
          <div className={`p-2 rounded-lg ${iconBg} ${iconColor} shrink-0`}>
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
    </div>
  );
};
