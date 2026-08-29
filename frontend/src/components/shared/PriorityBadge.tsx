import React from 'react';
import { getTierConfig } from '../../utils/tierUtils';
import { InfoTooltip } from './InfoTooltip';

interface PriorityBadgeProps {
  tier?: string | null;
  size?: 'sm' | 'md' | 'lg';
  showDot?: boolean;
  showInfoTooltip?: boolean;
  className?: string;
}

export const PriorityBadge: React.FC<PriorityBadgeProps> = ({
  tier,
  size = 'md',
  showDot = true,
  showInfoTooltip = false,
  className = '',
}) => {
  const config = getTierConfig(tier);

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs font-medium',
    md: 'px-2.5 py-1 text-xs font-semibold',
    lg: 'px-3 py-1.5 text-sm font-semibold',
  }[size];

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-md border ${config.badgeBg} ${config.badgeText} ${config.badgeBorder} ${sizeClasses} ${className}`}
    >
      {showDot && (
        <span className={`w-1.5 h-1.5 rounded-full ${config.dotColor} shrink-0`} />
      )}
      <span>{config.shortLabel}</span>
      {showInfoTooltip && (
        <InfoTooltip
          title={config.label}
          content={config.description}
          formula={config.key === 'Tier1_AttentionPriority' ? 'Dist ≤ 500m & MH Class ≥ 2' : config.key === 'Tier2_ElevatedAttention' ? 'Dist ≤ 2000m' : config.key === 'Tier3_Monitoring' ? 'Dist ≤ 5000m' : 'Dist > 5000m'}
          side="top"
          size="xs"
        />
      )}
    </span>
  );
};
