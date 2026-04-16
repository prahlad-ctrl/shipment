import { motion } from 'framer-motion';
import { Receipt } from 'lucide-react';
import { formatCurrency } from '../utils/formatters';

const COST_COLORS = {
  freight: { bg: 'var(--accent-blue)', label: 'Freight' },
  fuel_surcharge: { bg: 'var(--accent-amber)', label: 'Fuel Surcharge' },
  customs_and_docs: { bg: 'var(--accent-purple)', label: 'Customs & Docs' },
  insurance: { bg: 'var(--accent-cyan)', label: 'Insurance' },
  handling: { bg: 'var(--accent-emerald)', label: 'Handling' },
};

export default function CostBreakdown({ pricing }) {
  if (!pricing?.cost_breakdown) return null;

  const breakdown = pricing.cost_breakdown;
  const total = breakdown.total || 1;
  const items = Object.entries(COST_COLORS).map(([key, config]) => ({
    key,
    label: config.label,
    value: breakdown[key] || 0,
    percentage: ((breakdown[key] || 0) / total) * 100,
    bg: config.bg,
  })).filter(item => item.value > 0);

  return (
    <section className="cost-breakdown animate-fade-in-up">
      <div className="section-header">
        <div className="section-icon" style={{ background: 'rgba(16, 185, 129, 0.15)' }}>
          <Receipt size={18} style={{ color: 'var(--accent-emerald)' }} />
        </div>
        <div className="section-title">Cost Breakdown</div>
      </div>

      <div className="glass-card-static">
        <div className="cost-chart">
          {items.map((item, i) => (
            <div className="cost-item" key={item.key}>
              <div className="cost-item-label">{item.label}</div>
              <div className="cost-item-bar">
                <motion.div
                  className={`cost-item-fill ${item.key === 'fuel_surcharge' ? 'fuel' : item.key === 'customs_and_docs' ? 'customs' : item.key}`}
                  initial={{ width: 0 }}
                  animate={{ width: `${Math.max(item.percentage, 8)}%` }}
                  transition={{ duration: 0.8, delay: i * 0.1 }}
                >
                  {formatCurrency(item.value)}
                </motion.div>
              </div>
            </div>
          ))}
        </div>

        <div className="cost-total">
          <span className="cost-total-label">Total Cost</span>
          <span className="cost-total-value">{formatCurrency(total)}</span>
        </div>

        {pricing.within_budget !== null && pricing.within_budget !== undefined && (
          <div style={{
            padding: 'var(--space-sm) var(--space-lg)',
            fontSize: 'var(--font-size-sm)',
            color: pricing.within_budget ? 'var(--accent-emerald)' : 'var(--accent-rose)',
            textAlign: 'right'
          }}>
            {pricing.within_budget
              ? `✅ Within budget — saves ${formatCurrency(pricing.budget_delta)}`
              : `❌ Over budget by ${formatCurrency(Math.abs(pricing.budget_delta))}`
            }
          </div>
        )}
      </div>
    </section>
  );
}
