import { motion } from 'framer-motion';
import { Trophy, DollarSign, Clock, ShieldCheck, BarChart3, Leaf, FileKey } from 'lucide-react';
import { formatCurrency, formatDays, capitalize } from '../utils/formatters';
import Container3D from './Container3D';
import SmartContractEscrow from './SmartContractEscrow';

export default function DecisionSummary({ recommendation, reasoningSummary, tradeOffAnalysis, sustainabilityData, negotiationLog, parsedConstraints, customsCompliance, smartContract, spatialYield }) {
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

        {/* Negotiation Log */}
        {negotiationLog && negotiationLog.length > 0 && (
          <div className="decision-reasoning" style={{ marginTop: 'var(--space-lg)' }}>
            <div className="decision-reasoning-label">🤝 Automated Agent Negotiation Match</div>
            <div style={{ fontSize: '0.8em', color: 'var(--text-tertiary)', marginBottom: '8px', lineHeight: '1.4' }}>
              Our AI Broker automatically contacts the proposed carrier to request real-time spot discounts based on active market capacity before finalizing your route.
            </div>
            <div className="negotiation-chat" style={{ background: 'rgba(0,0,0,0.2)', padding: 'var(--space-md)', borderRadius: 'var(--radius-md)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {negotiationLog.map((log, i) => (
                <div key={i} style={{
                  alignSelf: log.sender === 'You' ? 'flex-end' : 'flex-start',
                  background: log.sender === 'You' ? 'rgba(59, 130, 246, 0.15)' : 'var(--glass-bg)',
                  border: `1px solid ${log.sender === 'You' ? 'rgba(59, 130, 246, 0.3)' : 'var(--glass-border)'}`,
                  padding: '8px 12px',
                  borderRadius: '12px',
                  maxWidth: '85%',
                  fontSize: '0.85em'
                }}>
                  <strong style={{ color: log.sender === 'You' ? 'var(--accent-blue)' : 'var(--text-primary)' }}>
                    {log.sender === 'You' ? 'AI Broker' : log.sender}:
                  </strong> {log.message}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* --- ALL IN EXTRA FEATURES --- */}
        
        {customsCompliance && (
          <div className="decision-reasoning" style={{ marginTop: 'var(--space-xl)', borderLeft: '4px solid var(--accent-amber)' }}>
            <div className="decision-reasoning-label" style={{ color: 'var(--accent-amber)' }}>
              <FileKey size={16} style={{ display: 'inline', verticalAlign: 'middle', marginRight: '4px' }} />
              Customs & Regulatory Intelligence
            </div>
            <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '8px' }}>
              <span style={{ padding: '2px 8px', background: 'rgba(255,150,0,0.1)', color: 'var(--accent-amber)', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 'bold' }}>
                HS Code: {customsCompliance.hs_code}
              </span>
              <span style={{ padding: '2px 8px', background: 'rgba(255,150,0,0.1)', color: 'var(--accent-amber)', borderRadius: '4px', fontSize: '0.8rem', fontWeight: 'bold' }}>
                Tariffs: {formatCurrency(customsCompliance.estimated_tariffs_usd)}
              </span>
            </div>
            
            {customsCompliance.flagged_regulations?.length > 0 && (
              <div style={{ marginBottom: '8px' }}>
                <strong style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Blocked by Regulations:</strong>
                <ul style={{ margin: '4px 0 0 16px', fontSize: '0.85rem', color: 'var(--accent-rose)' }}>
                  {customsCompliance.flagged_regulations.map((reg, i) => <li key={i}>{reg}</li>)}
                </ul>
              </div>
            )}
            
            {customsCompliance.required_documents?.length > 0 && (
              <div>
                <strong style={{ fontSize: '0.85rem', color: 'var(--text-secondary)' }}>Required Docs:</strong>
                <ul style={{ margin: '4px 0 0 16px', fontSize: '0.85rem', color: 'var(--text-primary)' }}>
                  {customsCompliance.required_documents.map((doc, i) => <li key={i}>{doc}</li>)}
                </ul>
              </div>
            )}
          </div>
        )}

        <Container3D constraints={parsedConstraints} spatialYield={spatialYield} />

        <SmartContractEscrow 
          cost={cost} 
          routeId={route?.id || 'sim_route'}
          weatherData={recommendation.weather}
          smartContract={smartContract}
        />
        
      </motion.div>
    </section>
  );
}
