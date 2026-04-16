import { useState, useEffect } from 'react';
import { Terminal, ShieldCheck, AlertCircle } from 'lucide-react';

export default function SmartContractEscrow({ cost, routeId, weatherData }) {
  const [logs, setLogs] = useState([]);
  const hasPenalty = weatherData?.estimated_delay_hours > 0 || weatherData?.overall_risk_level === 'high';

  useEffect(() => {
    const sequence = [
      { delay: 500, text: `> INITIATING ESCROW FOR ROUTE: ${routeId.toUpperCase()}` },
      { delay: 1500, text: `> ALLOCATING FUNDS: $${(cost || 0).toFixed(2)}` },
      { delay: 2500, text: `> DEPLOYING SOLIDITY CONTRACT 0x8F2e...4a1B` },
      { delay: 3500, text: `> VERIFYING CARRIER SIGNATURES... OK` },
      { delay: 4500, text: `> ESCROW LOCKED 🔒` }
    ];

    if (hasPenalty) {
      sequence.push({ delay: 6000, text: `> SCANNING TRANSIT EVENTS... DELAY DETECTED ⚠️` });
      sequence.push({ delay: 7500, text: `> EXECUTING CLAUSE 4.A (SLA BREACH)` });
      sequence.push({ delay: 8500, text: `> REFUNDING $200.00 TO ORIGIN WALLET 💸` });
    }

    let timeouts = [];
    sequence.forEach((item, index) => {
      const t = setTimeout(() => {
        setLogs(prev => [...prev, item.text]);
      }, item.delay);
      timeouts.push(t);
    });

    return () => timeouts.forEach(clearTimeout);
  }, [cost, routeId, hasPenalty]);

  return (
    <div className="glass-card-static" style={{ background: '#0a0a0a', border: '1px solid #333', marginTop: '1.5rem', fontFamily: 'monospace' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #333', paddingBottom: '0.75rem', marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-emerald)', fontSize: '0.9rem' }}>
          <ShieldCheck size={16} />
          <span>Smart Contract Escrow</span>
        </div>
        <Terminal size={16} style={{ color: '#666' }}/>
      </div>
      
      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', minHeight: '120px' }}>
        {logs.map((log, i) => (
          <div key={i} style={{ color: log.includes('REFUNDING') || log.includes('DELAY') ? 'var(--accent-rose)' : log.includes('LOCKED') ? 'var(--accent-cyan)' : '#4ade80', fontSize: '0.85rem' }}>
            {log}
          </div>
        ))}
        {logs.length < (hasPenalty ? 8 : 5) && (
          <div style={{ color: '#4ade80', animation: 'pulse 1s infinite' }}>_</div>
        )}
      </div>
    </div>
  );
}
