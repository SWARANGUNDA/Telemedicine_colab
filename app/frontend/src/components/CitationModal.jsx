import React from 'react';
import { X, BookOpen, ExternalLink, ShieldCheck } from 'lucide-react';

export default function CitationModal({ isOpen, onClose, citation }) {
  if (!isOpen || !citation) return null;

  const metadata = citation.metadata || {};
  const isGuideline = metadata.evidence_type === 'CLINICAL_GUIDELINE' || !metadata.evidence_type || citation.citation_string?.includes('ADA') || citation.citation_string?.includes('WHO');

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(168, 85, 247, 0.15)', color: 'var(--accent-purple)' }}>
              <BookOpen size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.15rem', fontWeight: 700 }}>Citation & Evidence Verification</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)' }}>Traceable source grounding for [{citation.citation_id}]</p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {/* Evidence Type Badge */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span className={`badge ${isGuideline ? 'badge-purple' : 'badge-amber'}`}>
              {isGuideline ? 'Official Clinical Practice Guideline' : 'Emerging Microbiome Research'}
            </span>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-dim)', display: 'flex', alignItems: 'center', gap: '4px' }}>
              <ShieldCheck size={14} style={{ color: 'var(--accent-emerald)' }} /> Grounded & Verified
            </span>
          </div>

          {/* Source Document Details */}
          <div style={{
            background: 'var(--bg-primary)',
            border: '1px solid var(--border-medium)',
            borderRadius: '12px',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px'
          }}>
            <div style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--accent-cyan)', fontWeight: 600 }}>
              {metadata.organization || 'Authoritative Clinical Source'}
            </div>
            <div style={{ fontSize: '1rem', fontWeight: 700, color: 'var(--text-main)' }}>
              {metadata.document_title || citation.citation_string || 'Standards of Care Guidelines'}
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', display: 'flex', gap: '16px' }}>
              {metadata.publication_date && <span><strong>Published:</strong> {metadata.publication_date}</span>}
              {metadata.version && <span><strong>Version:</strong> {metadata.version}</span>}
              {metadata.section_title && <span><strong>Section:</strong> {metadata.section_title}</span>}
            </div>
          </div>

          {/* Evidence Excerpt */}
          <div style={{
            background: 'rgba(30, 41, 59, 0.5)',
            border: '1px solid var(--border-subtle)',
            borderRadius: '12px',
            padding: '16px'
          }}>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
              RETRIEVED GUIDELINE EXCERPT:
            </div>
            <div style={{ fontSize: '0.9rem', color: 'var(--text-main)', lineHeight: 1.6, fontStyle: 'italic' }}>
              "{citation.text}"
            </div>
          </div>
        </div>

        <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-primary" onClick={onClose}>
            Close Citation
          </button>
        </div>
      </div>
    </div>
  );
}
