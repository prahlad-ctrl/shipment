import React from 'react';

const CargoProfile = ({ profile }) => {
  if (!profile) return null;

  const { fragility_score, vibration_sensitivity, handling_instructions } = profile;

  // Determine meter color and text based on fragility score
  let meterColor = 'var(--accent-emerald)';
  let riskLevel = 'Low Risk';
  if (fragility_score > 40) {
    meterColor = 'var(--accent-amber)';
    riskLevel = 'Medium Risk';
  }
  if (fragility_score > 70) {
    meterColor = 'var(--accent-rose)';
    riskLevel = 'High Risk';
  }

  return (
    <div className="glass-card animate-fade-in-up" style={{ padding: 'var(--space-lg)', marginBottom: 'var(--space-2xl)' }}>
      <h3 style={{
        fontSize: 'var(--font-size-lg)',
        fontWeight: '600',
        marginBottom: 'var(--space-md)',
        display: 'flex',
        alignItems: 'center',
        gap: 'var(--space-sm)'
      }}>
        📦 Cargo Handling Profile
      </h3>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
        gap: 'var(--space-xl)'
      }}>
        {/* Fragility Meter */}
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 'var(--space-xs)' }}>
            <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)' }}>
              Fragility Score
            </span>
            <span style={{ fontSize: 'var(--font-size-sm)', fontWeight: 'bold', color: meterColor }}>
              {fragility_score}/100 ({riskLevel})
            </span>
          </div>
          <div style={{
            height: '8px',
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${fragility_score}%`,
              height: '100%',
              background: meterColor,
              borderRadius: '4px',
              transition: 'width 1s ease-out'
            }} />
          </div>

          <div style={{ marginTop: 'var(--space-md)' }}>
            <span style={{ fontSize: 'var(--font-size-xs)', color: 'var(--text-tertiary)' }}>
              Vibration Sensitivity:
            </span>
            <span style={{ 
              marginLeft: 'var(--space-sm)',
              fontSize: 'var(--font-size-xs)', 
              padding: '2px 8px', 
              borderRadius: 'var(--radius-pill)',
              background: 'rgba(255, 255, 255, 0.05)',
              border: '1px solid var(--glass-border)',
              textTransform: 'uppercase'
            }}>
              {vibration_sensitivity}
            </span>
          </div>
        </div>

        {/* Handling Instructions */}
        <div>
          <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-secondary)', display: 'block', marginBottom: 'var(--space-sm)' }}>
            AI-Inferred Handling Instructions
          </span>
          {handling_instructions && handling_instructions.length > 0 ? (
            <ul style={{
              listStyleType: 'none',
              padding: 0,
              margin: 0,
              display: 'flex',
              flexDirection: 'column',
              gap: 'var(--space-xs)'
            }}>
              {handling_instructions.map((inst, i) => (
                <li key={i} style={{
                  fontSize: 'var(--font-size-sm)',
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: 'var(--space-sm)',
                  backgroundColor: 'rgba(59, 130, 246, 0.05)',
                  padding: 'var(--space-sm) var(--space-md)',
                  borderRadius: 'var(--radius-sm)',
                  border: '1px solid rgba(59, 130, 246, 0.1)'
                }}>
                  <span style={{ color: 'var(--accent-blue)' }}>⚡</span>
                  {inst}
                </li>
              ))}
            </ul>
          ) : (
            <span style={{ fontSize: 'var(--font-size-sm)', color: 'var(--text-tertiary)' }}>No special handling required.</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default CargoProfile;
