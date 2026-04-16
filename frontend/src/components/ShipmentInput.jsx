import { useState, useEffect, useRef } from 'react';
import { Send, Sparkles, Globe, AlertTriangle, Mic, Square, Image as ImageIcon, Loader2 } from 'lucide-react';
import { fetchPresets } from '../utils/api';

const FALLBACK_PRESETS = [
  { label: 'Dubai → Rotterdam', query: 'Ship 120 cartons of textiles (0.5x0.4x0.4 meters each) and 5 pallets of parts (1.2x1x1 meters each) from Dubai to Rotterdam under $4000' },
  { label: 'Shanghai → LA (Express)', query: 'Urgent shipment from Shanghai to Los Angeles: 50 crates of electronics (0.8x0.6x0.6 meters each), need it in 3 days, budget up to $8000' },
  { label: 'Mumbai → London (Budget)', query: 'Ship 1000kg of textiles from Mumbai to London, cheapest option, can wait up to 20 days' },
  { label: 'Hong Kong → New York', query: 'Rush delivery: 10 containers of medical supplies (0.4x0.4x0.4 meters each) from Hong Kong to New York in 2 days, cost is not a concern' },
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
  const [isRecording, setIsRecording] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const mediaRecorderRef = useRef(null);
  const chunksRef = useRef([]);
  const fileInputRef = useRef(null);

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

  const handleFileUpload = async (file) => {
    if (!file) return;
    setIsUploading(true);
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const response = await fetch('http://localhost:8000/api/vision/parse', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (data.success && data.query) {
        setQuery(data.query);
      } else {
        alert(data.detail || 'Failed to parse image');
      }
    } catch (e) {
      console.error(e);
      alert('Error uploading document: ' + e.message);
    } finally {
      setIsUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      handleFileUpload(file);
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    } else {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const mediaRecorder = new MediaRecorder(stream);
        mediaRecorderRef.current = mediaRecorder;
        chunksRef.current = [];
        
        mediaRecorder.ondataavailable = (e) => chunksRef.current.push(e.data);
        mediaRecorder.onstop = async () => {
          const mimeType = mediaRecorder.mimeType || 'audio/webm';
          const extension = mimeType.includes('mp4') ? 'mp4' : mimeType.includes('ogg') ? 'ogg' : 'webm';
          const blob = new Blob(chunksRef.current, { type: mimeType });
          stream.getTracks().forEach(track => track.stop());
          
          setIsUploading(true);
          const formData = new FormData();
          formData.append('file', blob, `recording.${extension}`);
          
          try {
            const response = await fetch('http://localhost:8000/api/voice/transcribe', {
              method: 'POST',
              body: formData,
            });
            const data = await response.json();
            if (response.ok && data.success && data.query) {
              setQuery(prev => prev + (prev ? ' ' : '') + data.query);
            } else {
               alert(data.detail || 'Voice API failed');
            }
          } catch (e) {
            console.error(e);
            alert('Error sending voice: ' + e.message);
          } finally {
            setIsUploading(false);
          }
        };
        
        mediaRecorder.start();
        setIsRecording(true);
      } catch (err) {
        console.error("Could not start recording", err);
        alert('Microphone access denied.');
      }
    }
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

          <div 
            className="input-wrapper"
            onDragOver={(e) => e.preventDefault()}
            onDrop={handleDrop}
          >
            <textarea
              id="shipment-query-input"
              className="input-textarea"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder='e.g., "Ship 500kg from Dubai to Rotterdam within 5 days under $4000" or upload a document.'
              rows={3}
              disabled={isLoading || isUploading}
            />
            {isUploading && (
              <div className="ingestion-overlay">
                <Loader2 size={24} className="spinner-icon" />
                <span>Processing with AI...</span>
              </div>
            )}
            <div className="ingestion-tools">
              <button 
                type="button" 
                className={`tool-btn ${isRecording ? 'recording' : ''}`}
                onClick={toggleRecording}
                title="Voice Input"
              >
                {isRecording ? <Square size={16} /> : <Mic size={16} />}
              </button>
              <button 
                type="button" 
                className="tool-btn"
                onClick={() => fileInputRef.current?.click()}
                title="Upload Bill of Lading (Image)"
              >
                <ImageIcon size={16} />
              </button>
              <input 
                type="file" 
                ref={fileInputRef} 
                className="hidden-file-input" 
                accept="image/*"
                onChange={(e) => handleFileUpload(e.target.files[0])}
              />
            </div>
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
