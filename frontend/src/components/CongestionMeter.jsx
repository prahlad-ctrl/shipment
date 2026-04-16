import { capitalize } from '../utils/formatters';

const LEVEL_SEGMENTS = {
  low: 1,
  moderate: 2,
  high: 3,
  critical: 4,
};

export default function CongestionMeter({ level, score }) {
  const filled = LEVEL_SEGMENTS[level] || 1;

  return (
    <div className="congestion-meter">
      <div className="congestion-bar">
        {[1, 2, 3, 4].map((i) => (
          <div
            key={i}
            className={`congestion-segment ${i <= filled ? `filled ${level}` : ''}`}
          />
        ))}
      </div>
      <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)' }}>
        {capitalize(level)}
      </span>
    </div>
  );
}
