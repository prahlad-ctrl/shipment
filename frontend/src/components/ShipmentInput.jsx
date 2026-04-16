import { useState, useEffect } from 'react';
import { Send, Sparkles, Globe, AlertTriangle, CloudLightning, Anchor } from 'lucide-react';
import { fetchPresets } from '../utils/api';

const FALLBACK_PRESETS = [
  { label: 'Dubai → Rotterdam', query: 'Ship 500kg from Dubai to Rotterdam within 5 days under $4000' },
  { label: 'Shanghai → LA (Express)', query: 'Urgent shipment of 200kg from Shanghai to Los Angeles, need it in 3 days, budget up to $8000' },
  { label: 'Mumbai → London (Budget)', query: 'Ship 1000kg of textiles from Mumbai to London, cheapest option, can wait up to 20 days' },
  { label: 'Hong Kong → New York', query: 'Rush delivery: 300kg from Hong Kong to New York in 2 days, cost is not a concern' },
];

const WORLD_EVENTS = [
  { id: 'normal', label: 'Normal', icon: '✅', description: 'Standard global conditions', color: 'var(--accent-emerald)' },
  { id: 'suez_canal_blocked', label: 'Suez Canal Blocked', icon: '🚫', description: 'Canal closed, reroute via Cape', color: 'var(--accent-rose)' },
  { id: 'port_strike', label: 'Port Strike', icon: '⚠️', description: 'European ports on strike', color: 'var(--accent-amber)' },
  { id: 'atlantic_storm', label: 'Atlantic Storm', icon: '🌀', description: 'Severe trans-Atlantic weather', color: 'var(--accent-purple)' },
];

export default function ShipmentInput({ onSubmit, isLoading, worldEvent, onWorldEventChange }) {
  const [query, setQuery] = useState('');
  const [presets, setPresets] = useState(FALLBACK_PRESETS);

  useEffect(() => {
    fetchPresets()
      .then((data) => setPresets(data.presets || FALLBACK_PRESETS))
      .catch(() => setPresets(FALLBACK_PRESETS));
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSubmit(query.trim());
    }
  };

  const handlePreset = (presetQuery) => {
    setQuery(presetQuery);
  };

  const activeEvent = WORLD_EVENTS.find(e => e.id === worldEvent) || WORLD_EVENTS[0];

  return (
    <section className="input-section">
      <form onSubmit={handleSubmit}>
        <div className="glass-card-static input-card">
          <div className="input-label">
            <Sparkles size={18} style={{ color: 'var(--accent-amber)' }} />
            Describe your shipment
          </div>
          <div className="input-hint">
            Tell us what you need to ship — include origin, destination, weight, deadline, and budget for best results.
          </div>

          <div className="input-wrapper">
            <textarea
              id="shipment-query-input"
              className="input-textarea"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder='e.g., "Ship 500kg from Dubai to Rotterdam within 5 days under $4000"'
              rows={3}
              disabled={isLoading}
            />
          </div>

          {/* World Conditions Selector */}
          <div className="world-conditions">
            <div className="world-conditions-label">
              <Globe size={14} style={{ color: 'var(--accent-cyan)' }} />
              World Conditions
            </div>
            <div className="world-conditions-grid">
              {WORLD_EVENTS.map((event) => (
                <button
                  key={event.id}
                  type="button"
                  className={`world-event-btn ${worldEvent === event.id ? 'active' : ''}`}
                  onClick={() => onWorldEventChange(event.id)}
                  disabled={isLoading}
                  style={{
                    '--event-color': event.color,
                  }}
                >
                  <span className="world-event-icon">{event.icon}</span>
                  <span className="world-event-name">{event.label}</span>
                </button>
              ))}
            </div>
            {worldEvent !== 'normal' && (
              <div className="world-event-warning">
                <AlertTriangle size={12} />
                <span>{activeEvent.description}</span>
              </div>
            )}
          </div>

          <div className="input-actions">
            <div className="presets-container">
              <span className="presets-label">Try:</span>
              {presets.map((p, i) => (
                <button
                  key={i}
                  type="button"
                  className="preset-btn"
                  onClick={() => handlePreset(p.query)}
                  disabled={isLoading}
                >
                  {p.label}
                </button>
              ))}
            </div>

            <button
              id="submit-shipment-btn"
              type="submit"
              className="submit-btn"
              disabled={!query.trim() || isLoading}
            >
              {isLoading ? (
                <>
                  <span className="spinner" />
                  Planning...
                </>
              ) : (
                <>
                  <Send size={16} />
                  Plan Route
                </>
              )}
            </button>
          </div>
        </div>
      </form>
    </section>
  );
}
