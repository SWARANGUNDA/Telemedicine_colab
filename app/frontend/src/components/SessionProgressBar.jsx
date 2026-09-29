import React from 'react';

export default function SessionProgressBar({ currentState }) {
  const states = ['CREATED', 'EXTRACTED', 'CONFIRMED', 'ANALYZED', 'XAI_READY', 'REPORT_READY'];
  const labels = {
    CREATED: '1. Upload Reports',
    EXTRACTED: '2. IMDIE Extraction',
    CONFIRMED: '3. Data Review & Confirm',
    ANALYZED: '4. Fusion Risk Gauges',
    XAI_READY: '5. SHAP Drivers & Weights',
    REPORT_READY: '6. Grounded Report & Q&A'
  };

  const currentIndex = states.indexOf(currentState);

  return (
    <div style={{ background: 'var(--bg-secondary)', padding: '16px 24px', borderBottom: '1px solid var(--border-card)' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px', fontSize: '0.85rem', fontWeight: '500' }}>
        {states.map((st, idx) => (
          <span key={st} style={{ color: idx <= currentIndex ? 'var(--accent-blue)' : 'var(--text-secondary)' }}>
            {labels[st]}
          </span>
        ))}
      </div>
      <div className="progress-bar-bg">
        <div className="progress-bar-fill" style={{ width: `${((currentIndex + 1) / states.length) * 100}%` }} />
      </div>
    </div>
  );
}
