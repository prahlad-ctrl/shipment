import { useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { BrainCircuit } from 'lucide-react';

export default function AgentReasoningStream({ steps, isStreaming }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [steps]);

  if (!steps || steps.length === 0) return null;

  return (
    <section className="reasoning-section animate-fade-in-up">
      <div className="reasoning-header">
        <div className="reasoning-title">
          <BrainCircuit size={20} style={{ color: 'var(--accent-purple)' }} />
          Agent Reasoning
        </div>
        <span className="reasoning-count">{steps.length} steps</span>
      </div>

      <div className="reasoning-timeline">
        <AnimatePresence>
          {steps.map((step, i) => (
            <motion.div
              key={i}
              className="reasoning-step"
              data-agent={step.agent}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.4, delay: 0.05 }}
            >
              <div className="reasoning-step-dot">
                {step.icon || '🔹'}
              </div>
              <div className="reasoning-step-agent">{step.agent}</div>
              <div className="reasoning-step-title">{step.step}</div>
              <div className="reasoning-step-detail">{step.detail}</div>
            </motion.div>
          ))}
        </AnimatePresence>

        {isStreaming && (
          <div className="typing-indicator">
            <div className="typing-dots">
              <span></span><span></span><span></span>
            </div>
            <span>Agent is thinking...</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </section>
  );
}
