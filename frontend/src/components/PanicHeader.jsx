import { AlertCircle, Zap } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function PanicHeader({ activeEvent, onPanicReroute }) {
  if (!activeEvent || activeEvent.id === 'normal') return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: -50 }}
        animate={{ opacity: 1, y: 0 }}
        exit={{ opacity: 0, y: -50 }}
        style={{
          background: 'linear-gradient(90deg, #f43f5e 0%, #be123c 100%)',
          color: 'white',
          padding: '12px 24px',
          borderRadius: '12px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '24px',
          boxShadow: '0 4px 20px rgba(244, 63, 94, 0.4)',
          position: 'relative',
          overflow: 'hidden',
          zIndex: 50
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', position: 'relative', zIndex: 2 }}>
          <div style={{ background: 'rgba(255,255,255,0.2)', padding: '8px', borderRadius: '50%', animation: 'pulse-glow 1.5s infinite' }}>
            <AlertCircle size={24} />
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: '1.1em', letterSpacing: '0.05em' }}>
              BREAKING: {activeEvent.label.toUpperCase()}
            </div>
            <div style={{ fontSize: '0.9em', opacity: 0.9 }}>
              {activeEvent.description} Systems suggest immediate rerouting for active shipments.
            </div>
          </div>
        </div>
        
        <button
          onClick={onPanicReroute}
          style={{
            background: 'white',
            color: '#be123c',
            border: 'none',
            padding: '10px 20px',
            borderRadius: '8px',
            fontWeight: 700,
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.2)',
            zIndex: 2,
            transition: 'transform 0.2s',
          }}
          onMouseOver={(e) => e.currentTarget.style.transform = 'scale(1.05)'}
          onMouseOut={(e) => e.currentTarget.style.transform = 'scale(1)'}
        >
          <Zap size={16} />
          PANIC REROUTE
        </button>
      </motion.div>
    </AnimatePresence>
  );
}
