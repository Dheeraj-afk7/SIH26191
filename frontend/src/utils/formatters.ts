/**
 * SIH26191 Display Formatters
 */

/**
 * Format numbers with Indian / standard thousand separators (e.g. 232,360 or 4,750)
 */
export function formatNumber(num?: number | null): string {
  if (num === undefined || num === null || isNaN(num)) return '—';
  return num.toLocaleString('en-IN');
}

/**
 * Format distance in meters to a human readable format:
 * < 1000m -> "42.5 m"
 * >= 1000m -> "1.2 km"
 */
export function formatDistance(meters?: number | null): string {
  if (meters === undefined || meters === null || isNaN(meters)) return '—';
  if (meters < 1000) {
    return `${meters < 10 ? meters.toFixed(1) : Math.round(meters)} m`;
  }
  return `${(meters / 1000).toFixed(1)} km`;
}

/**
 * Format area in hectares or sq meters
 */
export function formatHectares(ha?: number | null): string {
  if (ha === undefined || ha === null || isNaN(ha)) return '—';
  if (ha >= 1000) {
    return `${Math.round(ha).toLocaleString('en-IN')} ha`;
  }
  return `${ha.toFixed(2)} ha`;
}

/**
 * Format percentages (e.g. 0.2962 -> "29.6%")
 */
export function formatPercent(val?: number | null, isDecimal = true): string {
  if (val === undefined || val === null || isNaN(val)) return '—';
  const percentage = isDecimal ? val * 100 : val;
  return `${percentage.toFixed(1)}%`;
}

/**
 * Format ISO timestamp into clean UTC string for government command center
 */
export function formatTimestamp(isoString?: string | null): string {
  if (!isoString) return '—';
  try {
    const d = new Date(isoString);
    if (isNaN(d.getTime())) return isoString;
    return d.toISOString().replace('T', ' ').substring(0, 19) + ' UTC';
  } catch {
    return isoString;
  }
}
