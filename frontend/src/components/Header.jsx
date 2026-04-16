import { Ship, LogOut, Shield } from 'lucide-react';

export default function Header({ user, onLogout }) {
  return (
    <header className="app-header">
      <div className="header-logo">
        <div className="header-logo-icon">
          <Ship />
        </div>
        <div>
          <div className="header-title">ShipRoute AI</div>
          <div className="header-subtitle">Intelligent Shipment Orchestration</div>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-md)' }}>
        {user && (
          <div style={{
            display: 'flex', alignItems: 'center', gap: 'var(--space-sm)',
            padding: 'var(--space-xs) var(--space-md)',
            borderRadius: 'var(--radius-pill)',
            background: 'rgba(255,255,255,0.04)', border: '1px solid var(--glass-border)',
            fontSize: 'var(--font-size-xs)', color: 'var(--text-secondary)'
          }}>
            {user.role === 'admin' && <Shield size={12} style={{ color: 'var(--accent-amber)' }} />}
            <span>{user.name || user.email}</span>
            <span style={{
              padding: '1px 8px', borderRadius: 'var(--radius-pill)',
              background: user.role === 'admin' ? 'rgba(245, 158, 11, 0.15)' : 'rgba(59, 130, 246, 0.15)',
              color: user.role === 'admin' ? 'var(--accent-amber)' : 'var(--accent-blue)',
              fontSize: '0.65rem', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.05em'
            }}>
              {user.role}
            </span>
          </div>
        )}

        <div className="header-badge">
          <span className="header-badge-dot"></span>
          <span>Multi-Agent System Active</span>
        </div>

        {onLogout && (
          <button onClick={onLogout} style={{
            display: 'flex', alignItems: 'center', gap: '6px',
            padding: '6px 14px', borderRadius: 'var(--radius-pill)',
            background: 'rgba(244, 63, 94, 0.1)', border: '1px solid rgba(244, 63, 94, 0.2)',
            color: 'var(--accent-rose)', fontSize: 'var(--font-size-xs)',
            fontWeight: 500, cursor: 'pointer', fontFamily: 'inherit',
            transition: 'all var(--transition-fast)'
          }}
          onMouseEnter={(e) => { e.currentTarget.style.background = 'rgba(244, 63, 94, 0.2)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.background = 'rgba(244, 63, 94, 0.1)'; }}
          >
            <LogOut size={12} /> Logout
          </button>
        )}
      </div>
    </header>
  );
}
