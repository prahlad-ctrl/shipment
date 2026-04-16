import React from 'react';
import { Play, Pause } from 'lucide-react';

export default function TimelineScrubber({ progress, setProgress, isPlaying, setIsPlaying }) {
  return (
    <div style={{ marginTop: '1rem', background: 'var(--bg-glass)', padding: '1rem', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'center', gap: '1rem' }}>
      <button 
        onClick={() => setIsPlaying(!isPlaying)}
        style={{
          background: 'var(--accent-blue)', color: 'white', border: 'none', borderRadius: '50%', width: '40px', height: '40px', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer'
        }}
      >
        {isPlaying ? <Pause size={20} /> : <Play size={20} style={{ marginLeft: '2px' }} />}
      </button>
      
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
          <span>Origin</span>
          <span style={{ color: 'var(--accent-purple)', fontWeight: 600 }}>{Math.round(progress * 100)}% Complete</span>
          <span>Destination</span>
        </div>
        <input 
          type="range" 
          min="0" 
          max="1" 
          step="0.001" 
          value={progress}
          onChange={(e) => {
            setIsPlaying(false);
            setProgress(parseFloat(e.target.value));
          }}
          style={{ width: '100%', cursor: 'pointer', accentColor: 'var(--accent-blue)' }}
        />
      </div>
    </div>
  );
}
