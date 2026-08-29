import React from 'react';
import { AlertTriangle, Info, AlertCircle } from 'lucide-react';

interface WarningNoticeProps {
  title?: string;
  children: React.ReactNode;
  variant?: 'warning' | 'danger' | 'info';
  className?: string;
}

export const WarningNotice: React.FC<WarningNoticeProps> = ({
  title,
  children,
  variant = 'warning',
  className = '',
}) => {
  let bg = 'bg-amber-50';
  let border = 'border-amber-300';
  let text = 'text-amber-900';
  let iconColor = 'text-amber-600';
  let Icon = AlertTriangle;

  if (variant === 'danger') {
    bg = 'bg-red-50';
    border = 'border-red-300';
    text = 'text-red-900';
    iconColor = 'text-red-600';
    Icon = AlertCircle;
  } else if (variant === 'info') {
    bg = 'bg-blue-50';
    border = 'border-blue-300';
    text = 'text-blue-900';
    iconColor = 'text-blue-600';
    Icon = Info;
  }

  return (
    <div className={`p-3.5 rounded-lg border ${bg} ${border} ${text} ${className}`}>
      <div className="flex items-start gap-2.5">
        <Icon className={`w-5 h-5 shrink-0 ${iconColor} mt-0.5`} />
        <div className="text-xs leading-relaxed">
          {title && <p className="font-semibold mb-1 text-sm">{title}</p>}
          <div>{children}</div>
        </div>
      </div>
    </div>
  );
};
