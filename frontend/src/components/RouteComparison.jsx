import { GitCompareArrows } from 'lucide-react';
import RouteCard from './RouteCard';

export default function RouteComparison({ routes }) {
  if (!routes || routes.length === 0) return null;

  return (
    <section className="routes-section animate-fade-in-up">
      <div className="section-header">
        <div className="section-icon" style={{ background: 'rgba(139, 92, 246, 0.15)' }}>
          <GitCompareArrows size={18} style={{ color: 'var(--accent-purple)' }} />
        </div>
        <div className="section-title">Route Comparison</div>
      </div>

      <div className="routes-grid">
        {routes.map((route, i) => (
          <RouteCard key={route.route?.id || i} route={route} index={i} />
        ))}
      </div>
    </section>
  );
}
