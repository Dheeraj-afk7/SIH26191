/**
 * SIH26191 Priority Tier Helper Utilities
 */

import { PRIORITY_TIERS, PriorityTierKey, PriorityTierConfig } from '../config/constants';

export function getTierConfig(tier?: string | null): PriorityTierConfig {
  if (!tier || !(tier in PRIORITY_TIERS)) {
    return PRIORITY_TIERS.BeyondProximity;
  }
  return PRIORITY_TIERS[tier as PriorityTierKey];
}

export function getTierLabel(tier?: string | null): string {
  return getTierConfig(tier).label;
}

export function getTierBadgeClasses(tier?: string | null): string {
  const config = getTierConfig(tier);
  return `${config.badgeBg} ${config.badgeText} ${config.badgeBorder} border`;
}

export const TIER_ORDER: PriorityTierKey[] = [
  'Tier1_AttentionPriority',
  'Tier2_ElevatedAttention',
  'Tier3_Monitoring',
  'BeyondProximity',
];
