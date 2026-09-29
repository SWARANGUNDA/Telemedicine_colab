import React from 'react';
import { X, HelpCircle, CheckCircle, AlertTriangle, ShieldAlert } from 'lucide-react';

export default function WhyQualityModal({ isOpen, onClose, qualityData }) {
  if (!isOpen || !qualityData) return null;

  const scoreBreakdown = qualityData.score_breakdown || {};
  const overallScore = qualityData.overall_quality_score || qualityData.overall_score || 0;
  const counts = scoreBreakdown.counts || {};
  const coverage = scoreBreakdown.coverage || {};
  const deductions = scoreBreakdown.deductions_list || [];
  const qualityLabel = scoreBreakdown.quality_label || (overallScore >= 85 ? 'High Quality' : overallScore >= 60 ? 'Moderate Quality' : 'Low Quality / Verification Required');

  return (
    <div className="modal-overlay" onClick={onClose} style={{
      position: 'fixed', top: 0, left: 0, right: 0, bottom: 0,
      background: 'rgba(15, 23, 42, 0.8)', backdropFilter: 'blur(6px)', zIndex: 9999,
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '20px'
    }}>
      <div className="glass-card" onClick={(e) => e.stopPropagation()} style={{
        maxWidth: '650px', width: '100%', maxHeight: '90vh', overflowY: 'auto', padding: '24px'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{ padding: '8px', borderRadius: '8px', background: 'rgba(56, 189, 248, 0.15)', color: 'var(--accent-cyan)' }}>
              <HelpCircle size={22} />
            </div>
            <div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 800, color: 'var(--text-main)', margin: 0 }}>
                Why this Data Quality Score?
              </h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '2px 0 0 0' }}>
                Transparent feature completeness, verification, and imputation breakdown
              </p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-muted)', cursor: 'pointer' }}>
            <X size={20} />
          </button>
        </div>

        {/* Score & Label Banner */}
        <div style={{
          background: 'rgba(15, 23, 42, 0.6)',
          border: '1px solid var(--border-medium)',
          borderRadius: '12px',
          padding: '16px 20px',
          marginBottom: '20px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <div style={{ fontSize: '0.825rem', color: 'var(--text-muted)' }}>Input Data Quality Score</div>
            <div style={{ fontSize: '2rem', fontWeight: 800, color: overallScore >= 85 ? 'var(--accent-emerald)' : overallScore >= 60 ? 'var(--accent-amber)' : 'var(--accent-rose)' }}>
              {Number(overallScore).toFixed(1)}%
            </div>
          </div>
          <span className={`badge ${overallScore >= 85 ? 'badge-emerald' : overallScore >= 60 ? 'badge-amber' : 'badge-rose'}`} style={{ fontSize: '0.85rem', padding: '6px 14px' }}>
            {qualityLabel}
          </span>
        </div>

        {/* Counts Grid */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '10px' }}>
            Feature Status Counts:
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>{counts.provided ?? 0}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Provided</div>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent-emerald)' }}>{counts.extracted ?? 0}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Extracted</div>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent-purple)' }}>{counts.manual ?? 0}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Manual</div>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent-amber)' }}>{counts.edited ?? 0}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Edited</div>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent-rose)' }}>{counts.missing ?? 0}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Missing</div>
            </div>
            <div style={{ background: 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent-cyan)' }}>{counts.imputed ?? 0}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Imputed</div>
            </div>
            <div style={{ background: counts.verify > 0 ? 'rgba(245, 158, 11, 0.15)' : 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent-amber)' }}>{counts.verify ?? 0}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Verify</div>
            </div>
            <div style={{ background: counts.conflict > 0 ? 'rgba(244, 63, 94, 0.15)' : 'rgba(255,255,255,0.03)', padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
              <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent-rose)' }}>{counts.conflict ?? 0}</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>Conflicts</div>
            </div>
          </div>
        </div>

        {/* Modality Coverage */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '8px' }}>
            Active Modality Coverage:
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            <span className={`badge ${coverage.clinical ? 'badge-cyan' : 'badge-outline'}`}>
              Clinical: {coverage.clinical ? 'Supplied' : 'Not Provided'}
            </span>
            <span className={`badge ${coverage.wearable ? 'badge-purple' : 'badge-outline'}`}>
              Wearable: {coverage.wearable ? 'Supplied' : 'Not Provided'}
            </span>
            <span className={`badge ${coverage.gut ? 'badge-emerald' : 'badge-outline'}`}>
              Gut: {coverage.gut ? 'Supplied' : 'Not Provided'}
            </span>
            <span className={`badge ${coverage.cgm ? 'badge-amber' : 'badge-outline'}`}>
              CGM: {coverage.cgm ? 'Supplied' : 'Not Provided'}
            </span>
          </div>
        </div>

        {/* Deductions & Rules */}
        <div style={{ marginBottom: '20px' }}>
          <div style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-main)', marginBottom: '8px' }}>
            Score Deductions & Explanations:
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            {deductions.map((d, idx) => (
              <div key={idx} style={{
                background: 'rgba(255,255,255,0.02)',
                border: '1px solid var(--border-subtle)',
                borderRadius: '8px',
                padding: '8px 12px',
                fontSize: '0.8rem',
                color: 'var(--text-muted)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <AlertTriangle size={14} style={{ color: 'var(--accent-amber)', flexShrink: 0 }} />
                <span>{d}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Exclusion Rule Notice */}
        <div style={{
          background: 'rgba(56, 189, 248, 0.05)',
          border: '1px solid rgba(56, 189, 248, 0.2)',
          borderRadius: '10px',
          padding: '12px 16px',
          fontSize: '0.8rem',
          color: 'var(--accent-cyan)'
        }}>
          ℹ️ <strong>Input Quality Notice:</strong> Data Quality Score measures input data availability, extraction confidence, and verification status. It is strictly independent of ML disease risk probabilities or model confidence.
        </div>

        <div style={{ marginTop: '24px', display: 'flex', justifyContent: 'flex-end' }}>
          <button className="btn btn-primary" onClick={onClose}>
            Close Breakdown
          </button>
        </div>
      </div>
    </div>
  );
}

