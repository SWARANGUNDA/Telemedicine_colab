import React, { useEffect, useRef } from 'react';
import ReactDOM from 'react-dom';
import { FileText, CheckCircle2, AlertCircle, HelpCircle, X, ExternalLink, ShieldCheck, Tag } from 'lucide-react';

export default function ProvenancePopover({
  isOpen,
  onClose,
  featureName,
  normalizedValue,
  unit = '',
  status = 'EXTRACTED',
  provenanceData = null,
  anchorRect = null
}) {
  const popoverRef = useRef(null);

  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (popoverRef.current && !popoverRef.current.contains(e.target)) {
        onClose();
      }
    };
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') onClose();
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleOutsideClick);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  if (!isOpen) return null;

  // Calculate Popover Floating Position
  const popTop = anchorRect ? Math.min(anchorRect.bottom + 8, window.innerHeight - 340) : 100;
  const popLeft = anchorRect ? Math.min(Math.max(anchorRect.left - 120, 16), window.innerWidth - 380) : 100;

  const sourceFile = provenanceData?.source_file || null;
  const sourcePage = provenanceData?.source_page || 1;
  const rawValue = provenanceData?.raw_value || null;
  const method = provenanceData?.extraction_method || null;
  const confidence = provenanceData?.confidence !== undefined && provenanceData?.confidence !== null ? (provenanceData.confidence <= 1 ? (provenanceData.confidence * 100).toFixed(0) + '%' : provenanceData.confidence + '%') : null;
  const snippet = provenanceData?.original_text_snippet || null;

  const hasProvenance = Boolean(sourceFile || rawValue || method || snippet);

  return ReactDOM.createPortal(
    <div
      ref={popoverRef}
      className="glass-card"
      style={{
        position: 'fixed',
        top: `${popTop}px`,
        left: `${popLeft}px`,
        width: 'min(360px, 92vw)',
        padding: '18px',
        zIndex: 99999,
        boxShadow: '0 20px 40px rgba(0,0,0,0.7)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '14px',
        background: 'rgba(15, 23, 42, 0.98)',
        backdropFilter: 'blur(20px)',
        color: 'var(--text-main)',
        fontSize: '0.84rem'
      }}
    >
      {/* Popover Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '10px' }}>
        <div>
          <div style={{ fontSize: '0.72rem', color: 'var(--accent-cyan)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em' }}>
            EXTRACTION PROVENANCE & AUDIT
          </div>
          <strong style={{ fontSize: '0.98rem', color: '#ffffff' }}>{featureName ? featureName.replace(/_/g, ' ') : 'Feature Provenance'}</strong>
        </div>
        <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', padding: '2px' }}>
          <X size={18} />
        </button>
      </div>

      {/* Feature Value & Status Summary */}
      <div style={{ padding: '10px', background: 'var(--bg-primary)', borderRadius: '8px', marginBottom: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-dim)' }}>Normalized Value</div>
          <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>
            {normalizedValue !== null && normalizedValue !== undefined && normalizedValue !== '' ? `${normalizedValue} ${unit}` : 'Missing'}
          </div>
        </div>
        <span className={`badge ${status === 'VERIFIED' ? 'badge-emerald' : status === 'CONFLICT' ? 'badge-rose' : status === 'MANUAL' ? 'badge-purple' : 'badge-cyan'}`}>
          {status}
        </span>
      </div>

      {/* Provenance Metadata Details */}
      {hasProvenance ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {sourceFile && (
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed rgba(255,255,255,0.08)', paddingBottom: '6px' }}>
              <span style={{ color: 'var(--text-dim)' }}>Source Document:</span>
              <span style={{ fontWeight: 600, color: 'var(--text-main)', fontFamily: 'monospace', fontSize: '0.78rem' }}>
                📄 {sourceFile} {sourcePage ? `(Page ${sourcePage})` : ''}
              </span>
            </div>
          )}

          {rawValue && (
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed rgba(255,255,255,0.08)', paddingBottom: '6px' }}>
              <span style={{ color: 'var(--text-dim)' }}>Original Extracted Text:</span>
              <span style={{ fontWeight: 700, color: '#fbbf24' }}>"{rawValue}"</span>
            </div>
          )}

          {method && (
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed rgba(255,255,255,0.08)', paddingBottom: '6px' }}>
              <span style={{ color: 'var(--text-dim)' }}>Extraction Method:</span>
              <span style={{ fontWeight: 600, color: 'var(--accent-cyan)' }}>{method}</span>
            </div>
          )}

          {confidence !== null && (
            <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px dashed rgba(255,255,255,0.08)', paddingBottom: '6px' }}>
              <span style={{ color: 'var(--text-dim)' }}>Extraction Confidence:</span>
              <span style={{ fontWeight: 700, color: '#10b981' }}>{confidence}</span>
            </div>
          )}

          {snippet && (
            <div style={{ marginTop: '6px', padding: '8px 10px', background: 'rgba(6, 182, 212, 0.08)', borderRadius: '6px', borderLeft: '3px solid var(--accent-cyan)' }}>
              <div style={{ fontSize: '0.7rem', color: 'var(--accent-cyan)', fontWeight: 700, marginBottom: '2px' }}>
                Source Document Context Snippet:
              </div>
              <div style={{ fontSize: '0.78rem', color: 'var(--text-main)', fontStyle: 'italic' }}>
                "{snippet}"
              </div>
            </div>
          )}
        </div>
      ) : (
        <div style={{ padding: '16px', textAlign: 'center', color: 'var(--text-dim)', background: 'rgba(30,41,59,0.3)', borderRadius: '8px', fontSize: '0.8rem' }}>
          <HelpCircle size={20} style={{ color: 'var(--text-dim)', marginBottom: '4px' }} />
          <div>Provenance unavailable</div>
          <div style={{ fontSize: '0.72rem', marginTop: '2px', color: 'var(--text-muted)' }}>
            This value was manually entered or provided without raw OCR/document metadata.
          </div>
        </div>
      )}
    </div>,
    document.body
  );
}
