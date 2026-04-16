import { motion } from 'framer-motion';
import { Trophy, DollarSign, Clock, ShieldCheck, BarChart3, Leaf } from 'lucide-react';
import { formatCurrency, formatDays, capitalize } from '../utils/formatters';

export default function DecisionSummary({ recommendation, reasoningSummary, tradeOffAnalysis, sustainabilityData }) {
  if (!recommendation) return null;

  const route = recommendation.route;
  const cost = recommendation.adjusted_cost || recommendation.pricing?.cost_breakdown?.total;
  const days = recommendation.adjusted_days || route?.estimated_days;
  const riskLevel = recommendation.weather?.overall_risk_level || 'low';
  const overallScore = recommendation.overall_score;

  // Find sustainability data for the recommended route
  const routeSustainability = sustainabilityData?.find(s => s.route_id === route?.id);
  const emissions = routeSustainability?.total_emissions_kg || recommendation.sustainability?.total_emissions_kg;
  const greenScore = recommendation.green_score || routeSustainability?.green_score;
  const ecoLabel = routeSustainability?.eco_label || recommendation.sustainability?.eco_label;

  return (
    <section className="decision-section">
      <motion.div
        className="glass-card-static decision-card"
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <div className="decision-header">
          <div className="decision-icon">🏆</div>
          <div>
            <div className="decision-title">Recommended Route</div>
            <div className="decision-subtitle">{route?.name}</div>
          </div>
        </div>

        {/* Key Metrics */}
        <div className="decision-metrics">
          <motion.div className="metric-card"
            initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.1 }}
          >
            <div className="metric-label">
              <DollarSign size={12} style={{ display: 'inline', verticalAlign: 'middle' }} /> Total Cost
            </div>
            <div className="metric-value cost">{formatCurrency(cost)}</div>
          </motion.div>

          <motion.div className="metric-card"
            initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.2 }}
          >
            <div className="metric-label">
              <Clock size={12} style={{ display: 'inline', verticalAlign: 'middle' }} /> ETA
            </div>
            <div className="metric-value time">{formatDays(days)}</div>
          </motion.div>

          <motion.div className="metric-card"
            initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.3 }}
          >
            <div className="metric-label">
              <ShieldCheck size={12} style={{ display: 'inline', verticalAlign: 'middle' }} /> Risk
            </div>
            <div className="metric-value risk">{capitalize(riskLevel)}</div>
          </motion.div>

          <motion.div className="metric-card"
            initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4 }}
          >
            <div className="metric-label">
              <BarChart3 size={12} style={{ display: 'inline', verticalAlign: 'middle' }} /> Score
            </div>
            <div className="metric-value score">{overallScore?.toFixed(1)}</div>
          </motion.div>

          {/* Sustainability Metric */}
          <motion.div className="metric-card eco-metric"
            initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
          >
            <div className="metric-label">
              <Leaf size={12} style={{ display: 'inline', verticalAlign: 'middle' }} /> Carbon
            </div>
            <div className="metric-value eco">
              {emissions != null ? `${emissions}` : 'N/A'}
              {emissions != null && <span className="metric-unit">kg CO₂</span>}
            </div>
            {ecoLabel && (
              <div className="metric-sub eco-label">{ecoLabel}</div>
            )}
          </motion.div>
        </div>

        {/* Reasoning */}
        {reasoningSummary && (
          <div className="decision-reasoning">
            <div className="decision-reasoning-label">🧠 AI Reasoning</div>
            <div className="decision-reasoning-text">{reasoningSummary}</div>
          </div>
        )}

        {/* Trade-off Analysis */}
        {tradeOffAnalysis && (
          <div className="decision-reasoning">
            <div className="decision-reasoning-label">⚖️ Trade-off Analysis</div>
            <div className="decision-reasoning-text">{tradeOffAnalysis}</div>
          </div>
        )}
      </motion.div>
    </section>
  );
}
