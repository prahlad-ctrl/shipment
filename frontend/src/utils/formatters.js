/**
 * Format a number as USD currency.
 */
export function formatCurrency(amount) {
  if (amount == null) return 'N/A';
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);
}

/**
 * Format days with decimal precision.
 */
export function formatDays(days) {
  if (days == null) return 'N/A';
  if (days <= 1) return `${Math.round(days * 24)}h`;
  if (Number.isInteger(days)) return `${days} days`;
  return `${days.toFixed(1)} days`;
}

/**
 * Format distance in km.
 */
export function formatDistance(km) {
  if (km == null) return 'N/A';
  if (km >= 1000) return `${(km / 1000).toFixed(1)}k km`;
  return `${Math.round(km)} km`;
}

/**
 * Get mode emoji/icon label.
 */
export function getModeIcon(mode) {
  const icons = {
    air: '✈️',
    sea: '🚢',
    road: '🚛',
    rail: '🚂',
    multimodal: '🔄',
  };
  return icons[mode] || '📦';
}

/**
 * Get a risk color class name.
 */
export function getRiskClass(level) {
  const levels = {
    low: 'low',
    medium: 'medium',
    high: 'high',
    severe: 'severe',
    moderate: 'moderate',
    critical: 'critical',
  };
  return levels[level?.toLowerCase()] || 'low';
}

/**
 * Capitalize first letter.
 */
export function capitalize(str) {
  if (!str) return '';
  return str.charAt(0).toUpperCase() + str.slice(1);
}
