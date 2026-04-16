import { useState, useEffect } from 'react';
import './index.css';
import Header from './components/Header';
import ShipmentInput from './components/ShipmentInput';
import AgentReasoningStream from './components/AgentReasoningStream';
import CopilotChat from './components/CopilotChat';
import DecisionSummary from './components/DecisionSummary';
import CargoProfile from './components/CargoProfile';
import RouteMap from './components/RouteMap';
import RouteComparison from './components/RouteComparison';
import CostBreakdown from './components/CostBreakdown';
import Login from './components/Login';
import { streamShipmentPlan, fetchCurrentUser } from './utils/api';

export default function App() {
  const [user, setUser] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [reasoningSteps, setReasoningSteps] = useState([]);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [worldEvent, setWorldEvent] = useState('normal');

  // Check for existing session on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser) {
      try {
        setUser(JSON.parse(savedUser));
      } catch {
        localStorage.clear();
      }
    }
  }, []);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    setUser(null);
    setResult(null);
    setReasoningSteps([]);
  };

  const handleSubmit = async (query, history = null) => {
    setIsLoading(true);
    setReasoningSteps([]);
    
    // Hold onto the existing constraints if this is a follow-up
    const existingConstraints = history ? (result?.parsed_constraints || null) : null;
    
    setResult(null);
    setError(null);

    await streamShipmentPlan(query, worldEvent, history, existingConstraints, {
      onStep: (step) => {
        setReasoningSteps((prev) => [...prev, step]);
      },
      onResult: (data) => {
        setResult(data);
      },
      onError: (msg) => {
        setError(msg);
        setIsLoading(false);
      },
      onDone: () => {
        setIsLoading(false);
      },
    });
  };

  // Combine recommendation + alternatives for comparison
  const allRoutes = result
    ? [result.recommendation, ...(result.alternatives || [])].filter(Boolean)
    : [];

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <>
      <div className="bg-gradient-orbs" />

      <div className="app-container">
        <Header user={user} onLogout={handleLogout} />

        <ShipmentInput
          onSubmit={handleSubmit}
          isLoading={isLoading}
          worldEvent={worldEvent}
          onWorldEventChange={setWorldEvent}
        />

        {error && (
          <div className="glass-card-static animate-fade-in-up" style={{
            padding: 'var(--space-lg)',
            marginBottom: 'var(--space-xl)',
            borderColor: 'rgba(244, 63, 94, 0.3)',
            color: 'var(--accent-rose)',
          }}>
            <strong>Error:</strong> {error}
          </div>
        )}

        <AgentReasoningStream steps={reasoningSteps} isStreaming={isLoading} />

        {result && (
          <>
            <DecisionSummary
              recommendation={result.recommendation}
              reasoningSummary={result.reasoning_summary}
              tradeOffAnalysis={result.trade_off_analysis}
              sustainabilityData={result.sustainability_data}
              negotiationLog={result.negotiation_log}
              parsedConstraints={result.parsed_constraints}
              customsCompliance={result.customs_compliance}
              smartContract={result.smart_contract}
              spatialYield={result.spatial_yield}
            />

            <CargoProfile profile={result.cargo_profile} />

            <CopilotChat onSubmit={handleSubmit} isLoading={isLoading} />

            <RouteMap routes={allRoutes} />

            {result.recommendation && (
              <CostBreakdown pricing={result.recommendation.pricing} />
            )}

            <RouteComparison routes={allRoutes} />
          </>
        )}

        {!isLoading && !result && !error && (
          <div className="empty-state">
            <div className="empty-state-icon">🌐</div>
            <div className="empty-state-title">Ready to Plan Your Shipment</div>
            <div className="empty-state-text">
              Enter your shipment details above or try one of the preset examples.
              Our multi-agent AI will analyze routes, pricing, weather, and port conditions
              to find the optimal shipping strategy.
            </div>
          </div>
        )}

        <footer style={{
          textAlign: 'center',
          padding: 'var(--space-2xl) 0',
          color: 'var(--text-muted)',
          fontSize: 'var(--font-size-xs)',
          borderTop: '1px solid var(--glass-border)',
          marginTop: 'var(--space-xl)',
        }}>
          ShipRoute AI — Intelligent Shipment Orchestration Agent • Powered by Multi-Agent AI
        </footer>
      </div>
    </>
  );
}
