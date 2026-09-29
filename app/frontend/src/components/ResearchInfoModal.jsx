import React from 'react';
import { Info, X, ShieldAlert } from 'lucide-react';

export default function ResearchInfoModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.15)', color: 'var(--accent-cyan)' }}>
              <Info size={22} />
            </div>
            <h3 style={{ fontSize: '1.25rem', fontWeight: 700 }}>About This Research System</h3>
          </div>
          <button
            onClick={onClose}
            style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer', padding: '4px' }}
          >
            <X size={20} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontSize: '0.925rem', color: 'var(--text-main)', lineHeight: 1.6 }}>
          <p>
            This platform uses machine-learning models developed using <strong>clinically informed, rule-based synthetic multimodal data</strong> designed to reproduce plausible real-world clinical patterns.
          </p>
          <p>
            The platform is intended for <strong>research and academic decision-support evaluation</strong> and has not yet undergone external clinical validation.
          </p>
          <p>
            Model-estimated risk scores and AI-generated explanations should <strong>not be interpreted as clinical diagnoses or medical prescriptions</strong>.
          </p>

          <div style={{
            marginTop: '8px',
            padding: '14px 18px',
            borderRadius: '10px',
            background: 'rgba(245, 158, 11, 0.1)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            display: 'flex',
            gap: '12px',
            alignItems: 'flex-start'
          }}>
            <ShieldAlert size={20} style={{ color: 'var(--accent-amber)', flexShrink: 0, marginTop: '2px' }} />
            <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              <strong style={{ color: 'var(--accent-amber)' }}>Academic Positioning Notice:</strong> All predictions reflect statistical model output thresholds on synthetic benchmark datasets.
            </div>
          </div>
        </div>

        <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-primary" onClick={onClose}>
            Understand & Close
          </button>
        </div>
      </div>
    </div>
  );
}
