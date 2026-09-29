import React from 'react';
import { Activity, ShieldCheck } from 'lucide-react';

export default function Footer() {
  return (
    <footer style={{
      background: 'var(--bg-primary)',
      borderTop: '1px solid var(--border-subtle)',
      padding: '24px 0',
      marginTop: 'auto',
      fontSize: '0.8rem',
      color: 'var(--text-dim)'
    }}>
      <div className="app-container" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Activity size={16} style={{ color: 'var(--accent-cyan)' }} />
          <span><strong>TeleMed AI Platform</strong> — Multimodal Metabolic Health Decision Support System</span>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--accent-emerald)' }}>
            <ShieldCheck size={14} /> Synthetic Multimodal Benchmark Model
          </span>
        </div>
      </div>
    </footer>
  );
}
