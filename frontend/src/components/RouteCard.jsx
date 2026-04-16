import { motion } from 'framer-motion';
import { formatCurrency, formatDays, formatDistance, getModeIcon } from '../utils/formatters';
import WeatherBadge from './WeatherBadge';
import CongestionMeter from './CongestionMeter';

function getGreenIcon(score) {
  if (score >= 80) return '🌿';
  if (score >= 60) return '🍃';
  if (score >= 40) return '🍂';
  return '🏭';
}

function getGreenClass(score) {
  if (score >= 80) return 'excellent';
  if (score >= 60) return 'good';
  if (score >= 40) return 'moderate';
  return 'poor';
}

export default function RouteCard({ route, index }) {
  const { route: routeInfo, pricing, weather, congestion, sustainability,
    overall_score, cost_score, time_score, risk_score, reliability_score,
    green_score, adjusted_cost, adjusted_days,
    pros, cons, is_recommended } = route;

  const cost = adjusted_cost || pricing?.cost_breakdown?.total;
  const days = adjusted_days || routeInfo?.estimated_days;
  const withinBudget = pricing?.within_budget;
  const emissions = sustainability?.total_emissions_kg;
  const ecoLabel = sustainability?.eco_label;
  const greenScoreVal = green_score || sustainability?.green_score || 0;

  return (
    <motion.div
      className={`glass-card route-card ${is_recommended ? 'recommended' : ''}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: index * 0.1 }}
    >
      {is_recommended && (
        <div className="recommended-badge">🏆 Recommended</div>
      )}

      <div className="route-mode-icon">
        <span className={`mode-pill ${routeInfo.mode}`}>
          {getModeIcon(routeInfo.mode)} {routeInfo.mode}
        </span>
        {weather && (
          <WeatherBadge level={weather.overall_risk_level} />
        )}
        {/* Sustainability Badge */}
        {greenScoreVal > 0 && (
          <span className={`eco-badge ${getGreenClass(greenScoreVal)}`}>
            {getGreenIcon(greenScoreVal)} {ecoLabel || 'Unknown'}
          </span>
        )}
      </div>

      <div className="route-name">{routeInfo.name}</div>

      {/* Legs Timeline */}
      {routeInfo.legs && routeInfo.legs.length > 0 && (
        <div className="legs-timeline">
          <div className="leg-dot" />
          {routeInfo.legs.map((leg, i) => (
            <div className="leg-segment" key={i}>
              <div className={`leg-line ${leg.mode}`} />
              <div className="leg-label">
                {leg.from_location} → {leg.to_location}
              </div>
            </div>
          ))}
          <div className="leg-dot" />
        </div>
      )}

      {/* Key Stats */}
      <div className="route-stats">
        <div>
          <div className="route-stat-label">Cost</div>
          <div className={`route-stat-value cost ${withinBudget === false ? 'over-budget' : ''}`}>
            {formatCurrency(cost)}
          </div>
        </div>
        <div>
          <div className="route-stat-label">Transit</div>
          <div className="route-stat-value time">
            {formatDays(days)}
          </div>
        </div>
        <div>
          <div className="route-stat-label">Distance</div>
          <div className="route-stat-value">
            {formatDistance(routeInfo.total_distance_km)}
          </div>
        </div>
        <div>
          <div className="route-stat-label">CO₂</div>
          <div className={`route-stat-value eco ${getGreenClass(greenScoreVal)}`}>
            {emissions != null ? `${emissions} kg` : 'N/A'}
          </div>
        </div>
      </div>

      {/* Overall Score */}
      <div className="overall-score">
        <span className="overall-score-label">Overall Score</span>
        <span className="overall-score-value">{overall_score?.toFixed(1)}</span>
      </div>

      {/* Score Bars */}
      <div className="score-bars">
        <ScoreBar label="Cost" value={cost_score} className="cost" />
        <ScoreBar label="Time" value={time_score} className="time" />
        <ScoreBar label="Risk" value={risk_score} className="risk" />
        <ScoreBar label="Reliability" value={reliability_score} className="reliability" />
        <ScoreBar label="Green" value={greenScoreVal} className="green" />
      </div>

      {/* Pros & Cons */}
      {(pros?.length > 0 || cons?.length > 0) && (
        <div className="pros-cons">
          {pros?.map((p, i) => (
            <div key={`pro-${i}`} className="pro-item">
              <span>✅</span> <span>{p}</span>
            </div>
          ))}
          {cons?.map((c, i) => (
            <div key={`con-${i}`} className="con-item">
              <span>⚠️</span> <span>{c}</span>
            </div>
          ))}
        </div>
      )}
    </motion.div>
  );
}

function ScoreBar({ label, value, className }) {
  return (
    <div className="score-bar">
      <span className="score-bar-label">{label}</span>
      <div className="score-bar-track">
        <div
          className={`score-bar-fill ${className}`}
          style={{ width: `${Math.max(0, Math.min(100, value || 0))}%` }}
        />
      </div>
      <span className="score-bar-value">{Math.round(value || 0)}</span>
    </div>
  );
}
