import { CloudSun, CloudRain, CloudLightning, CloudOff } from 'lucide-react';
import { getRiskClass } from '../utils/formatters';

const RISK_ICONS = {
  low: CloudSun,
  medium: CloudRain,
  high: CloudLightning,
  severe: CloudOff,
};

const RISK_LABELS = {
  low: 'Low Risk',
  medium: 'Medium Risk',
  high: 'High Risk',
  severe: 'Severe Risk',
};

export default function WeatherBadge({ level }) {
  const normalizedLevel = getRiskClass(level);
  const Icon = RISK_ICONS[normalizedLevel] || CloudSun;
  const label = RISK_LABELS[normalizedLevel] || level;

  return (
    <span className={`weather-badge ${normalizedLevel}`}>
      <Icon size={12} />
      {label}
    </span>
  );
}
