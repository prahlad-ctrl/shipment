import { useState, useEffect } from 'react';
import { Terminal, ShieldCheck, AlertCircle, Code } from 'lucide-react';

export default function SmartContractEscrow({ cost, routeId, weatherData, smartContract }) {
  const [logs, setLogs] = useState([]);
  const hasPenalty = weatherData?.estimated_delay_hours > 0 || weatherData?.overall_risk_level === 'high';

  useEffect(() => {
    const AI_sequence = smartContract?.milestones?.map((m, i) => ({ delay: 500 + (1000 * i), text: `> MILESTONE: ${m.toUpperCase()}` })) || [];

    const sequence = [
      { delay: 500, text: `> INITIATING ESCROW FOR ROUTE: ${routeId.toUpperCase()}` },
      { delay: 1500, text: `> ALLOCATING FUNDS: $${(cost || 0).toFixed(2)}` },
      { delay: 2500, text: `> DEPLOYING AUTO-GENERATED SOLIDITY CONTRACT...` }
    ].concat(AI_sequence).concat([
      { delay: 2500 + (1000 * (AI_sequence.length + 1)), text: `> VERIFYING CARRIER ORACLES... OK` },
      { delay: 3500 + (1000 * (AI_sequence.length + 1)), text: `> ESCROW LOCKED 🔒` }
    ]);

    if (hasPenalty) {
      sequence.push({ delay: 5000 + (1000 * AI_sequence.length), text: `> SCANNING TRANSIT EVENTS... DELAY DETECTED ⚠️` });
      sequence.push({ delay: 6500 + (1000 * AI_sequence.length), text: `> EXECUTING CLAUSE 4.A (SLA BREACH)` });
      sequence.push({ delay: 7500 + (1000 * AI_sequence.length), text: `> REFUNDING $200.00 TO ORIGIN WALLET 💸` });
    }

    let timeouts = [];
    sequence.forEach((item, index) => {
      const t = setTimeout(() => {
        setLogs(prev => [...prev, item.text]);
      }, item.delay);
      timeouts.push(t);
    });

    return () => timeouts.forEach(clearTimeout);
  }, [cost, routeId, hasPenalty, smartContract]);

  return (
    <div className="glass-card-static" style={{ background: '#0a0a0a', border: '1px solid #333', marginTop: '1.5rem', fontFamily: 'monospace' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', borderBottom: '1px solid #333', paddingBottom: '0.75rem', marginBottom: '0.75rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent-emerald)', fontSize: '0.9rem' }}>
          <ShieldCheck size={16} />
          <span>Smart Contract Escrow</span>
        </div>
        <Terminal size={16} style={{ color: '#666' }}/>
      </div>
      
      <div style={{ display: 'grid', gridTemplateColumns: smartContract ? '1fr 1fr' : '1fr', gap: '1rem', minHeight: '120px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {logs.map((log, i) => (
            <div key={i} style={{ color: log.includes('REFUNDING') || log.includes('DELAY') ? 'var(--accent-rose)' : log.includes('LOCKED') ? 'var(--accent-cyan)' : '#4ade80', fontSize: '0.85rem' }}>
              {log}
            </div>
          ))}
          {logs.length < (hasPenalty ? 8 : 5) && (
            <div style={{ color: '#4ade80', animation: 'pulse 1s infinite' }}>_</div>
          )}
        </div>
        
        {smartContract?.solidity_code && (
          <div style={{ 
            background: 'rgba(0,0,0,0.4)', 
            borderLeft: '1px solid #333', 
            paddingLeft: '1rem',
            overflowY: 'auto',
            maxHeight: '200px'
          }}>
            <div style={{ color: '#666', fontSize: '0.75rem', marginBottom: '0.5rem', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <Code size={12}/> auto-generated contract logic
            </div>
            <pre style={{ 
              color: '#dcdcaa', 
              fontSize: '0.75rem', 
              margin: 0,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              lineHeight: 1.4
            }}>
              {smartContract.solidity_code.replace(/```solidity/g, '').replace(/```/g, '').trim()}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}
