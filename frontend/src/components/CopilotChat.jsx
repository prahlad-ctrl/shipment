import { useState, useRef, useEffect } from 'react';
import { Send, Bot, MessageSquare } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function CopilotChat({ onSubmit, isLoading }) {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState([
    { sender: 'AI', text: "Route planned! Need to adjust something? Just tell me (e.g. 'Make it cheaper' or 'Must arrive by Friday')." }
  ]);
  const [inputValue, setInputValue] = useState('');
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isOpen]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const formattedHistory = messages
      .filter(m => m.sender === 'User' || !m.text.startsWith('Route planned!'))
      .map(m => ({ sender: m.sender, message: m.text }));

    setMessages(prev => [...prev, { sender: 'User', text: inputValue }]);
    
    onSubmit(inputValue, formattedHistory);
    setInputValue('');
  };

  // Whenever a new plan is done loading, we can inject a follow up, but keeping it simple is fine.
  
  return (
    <>
      <button 
        className="copilot-toggle-btn"
        onClick={() => setIsOpen(!isOpen)}
        style={{
          position: 'fixed',
          bottom: '32px',
          right: '32px',
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          background: 'var(--gradient-accent)',
          border: 'none',
          color: 'white',
          boxShadow: 'var(--shadow-glow-blue)',
          cursor: 'pointer',
          zIndex: 100,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}
      >
        <MessageSquare size={24} />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div 
            initial={{ opacity: 0, y: 20, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.9 }}
            style={{
              position: 'fixed',
              bottom: '100px',
              right: '32px',
              width: '350px',
              height: '450px',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--glass-border)',
              borderRadius: 'var(--radius-lg)',
              boxShadow: 'var(--shadow-lg)',
              display: 'flex',
              flexDirection: 'column',
              zIndex: 100,
              overflow: 'hidden'
            }}
          >
            <div style={{ padding: '16px', background: 'rgba(255,255,255,0.05)', borderBottom: '1px solid var(--glass-border)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Bot size={18} style={{ color: 'var(--accent-blue)' }} />
              <strong style={{ fontSize: '14px' }}>AI Logistics Payer</strong>
            </div>
            
            <div style={{ flex: 1, overflowY: 'auto', padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {messages.map((msg, i) => (
                <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: msg.sender === 'User' ? 'flex-end' : 'flex-start' }}>
                  <div style={{
                    background: msg.sender === 'User' ? 'var(--accent-blue)' : 'var(--bg-tertiary)',
                    color: 'white',
                    padding: '8px 12px',
                    borderRadius: '12px',
                    borderBottomRightRadius: msg.sender === 'User' ? '0' : '12px',
                    borderBottomLeftRadius: msg.sender === 'User' ? '12px' : '0',
                    fontSize: '13px',
                    maxWidth: '85%',
                    lineHeight: '1.5'
                  }}>
                    {msg.text}
                  </div>
                </div>
              ))}
              {isLoading && (
                <div style={{ alignSelf: 'flex-start', background: 'var(--bg-tertiary)', padding: '8px 12px', borderRadius: '12px', fontSize: '13px' }}>
                  <span className="typing-dots"><span></span><span></span><span></span></span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            
            <form onSubmit={handleSubmit} style={{ borderTop: '1px solid var(--glass-border)', padding: '12px', display: 'flex', gap: '8px', background: 'var(--bg-primary)' }}>
              <input
                type="text"
                value={inputValue}
                onChange={e => setInputValue(e.target.value)}
                placeholder="Adjust the route..."
                disabled={isLoading}
                style={{ flex: 1, background: 'rgba(255,255,255,0.05)', border: '1px solid var(--glass-border)', borderRadius: '20px', padding: '8px 16px', color: 'white', fontSize: '13px', outline: 'none' }}
              />
              <button 
                type="submit"
                disabled={!inputValue.trim() || isLoading}
                style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'var(--accent-blue)', color: 'white', border: 'none', display: 'flex', alignItems: 'center', justifyContent: 'center', cursor: 'pointer', opacity: (!inputValue.trim() || isLoading) ? 0.5 : 1 }}
              >
                <Send size={14} />
              </button>
            </form>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
