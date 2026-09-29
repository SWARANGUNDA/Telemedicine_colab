import React from 'react';
import {
  CheckCircle2, Clock, AlertCircle, RefreshCw, MinusCircle, ArrowRight,
  ShieldCheck, Brain, FileText, Activity, Watch, Dna, Layers, Sparkles
} from 'lucide-react';

export default function AnalysisJourneyView({
  stage, // 'intake' | 'dq' | 'clinical' | 'wearable' | 'gut' | 'fusion' | 'predict' | 'xai' | 'rag' | 'complete' | 'failed'
  error,
  suppliedModalities = ['clinical'],
  pathway = 'C',
  dqScore = null,
  positiveSignalsCount = 0,
  onNavigateDashboard,
  onRetry
}) {
  const hasClinical = suppliedModalities.includes('clinical');
  const hasWearable = suppliedModalities.includes('wearable');
  const hasGut = suppliedModalities.includes('gut');

  // Define the ordered steps of the journey
  const stagesOrder = [
    { key: 'intake', label: 'Intake Validated', desc: 'Canonical feature mapping & physiological boundary validation', icon: Activity },
    { key: 'dq', label: 'Data Quality Assessment', desc: dqScore !== null ? `Calculated DQ Score: ${Number(dqScore).toFixed(1)}%` : 'Evaluating completeness, freshness & sensor noise', icon: ShieldCheck },
    { key: 'clinical', label: 'Clinical Expert Engine', desc: hasClinical ? 'Evaluating CatBoost/LightGBM Clinical Expert v4' : 'Not Supplied', icon: Activity, unsupplied: !hasClinical },
    { key: 'wearable', label: 'Wearable Telemetry Expert', desc: hasWearable ? 'Evaluating 15D sensor streams & circadian metrics' : 'Not Supplied (Modality Restricted)', icon: Watch, unsupplied: !hasWearable },
    { key: 'gut', label: 'Gut Microbiome Expert', desc: hasGut ? 'Evaluating 20 Taxa relative abundance profile' : 'Not Supplied (Modality Restricted)', icon: Dna, unsupplied: !hasGut },
    { key: 'fusion', label: 'Effective Fusion Pathway', desc: `Routed to Pathway ${pathway} based on active modalities`, icon: Layers },
    { key: 'predict', label: 'Multimodal Risk Prediction', desc: 'Calibrated probability inference across 5 cardiometabolic targets', icon: Activity },
    { key: 'xai', label: 'SHAP TreeExplainer Drivers', desc: 'Computing feature attributions & model influence rankings', icon: Brain },
    { key: 'rag', label: 'Medical Evidence & RAG Retrieval', desc: 'Retrieving grounded guideline chunks & clinical evidence', icon: FileText },
    { key: 'complete', label: 'Report & Command Center Ready', desc: 'Synthesizing personalized recommendations & timeline', icon: CheckCircle2 }
  ];

  const getStageIndex = (k) => stagesOrder.findIndex(s => s.key === k);
  const currentIdx = getStageIndex(stage);

  const getStepStatus = (itemIndex, isUnsupplied) => {
    if (stage === 'failed' && itemIndex === currentIdx) return 'failed';
    if (isUnsupplied) return 'unsupplied';
    if (stage === 'complete') return 'complete';
    if (itemIndex < currentIdx) return 'complete';
    if (itemIndex === currentIdx) return 'processing';
    return 'waiting';
  };

  return (
    <div className="glass-card" style={{ maxWidth: '840px', margin: '0 auto', padding: '32px 28px' }}>
      {/* Journey Header */}
      <div style={{ textAlign: 'center', marginBottom: '28px' }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 14px',
          borderRadius: '20px',
          background: 'rgba(6, 182, 212, 0.12)',
          border: '1px solid rgba(6, 182, 212, 0.3)',
          color: 'var(--accent-cyan)',
          fontSize: '0.8rem',
          fontWeight: 700,
          marginBottom: '12px'
        }}>
          <Sparkles size={16} /> V3.3 MULTIMODAL INFERENCE LIFECYCLE
        </div>

        <h2 style={{ fontSize: '1.6rem', fontWeight: 800, color: 'var(--text-main)', margin: '0 0 6px 0' }}>
          {stage === 'complete' ? 'Health Assessment Completed Successfully! 🎉' : (stage === 'failed' ? 'Assessment Execution Failed' : 'Executing AI Multimodal Analysis Journey...')}
        </h2>
        <p style={{ fontSize: '0.88rem', color: 'var(--text-muted)', margin: 0 }}>
          {stage === 'complete'
            ? 'All 5 model-estimated screening scores, SHAP drivers, and RAG guidelines are synthesized and ready.'
            : (stage === 'failed' ? 'An unexpected error occurred during pipeline execution. Review details below.' : 'Real-time scientific model execution across active expert algorithms and pathway fusion.')}
        </p>
      </div>

      {/* Steps List */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '28px' }}>
        {stagesOrder.map((item, idx) => {
          const Icon = item.icon;
          const status = getStepStatus(idx, item.unsupplied);

          let statusBg = 'rgba(30, 41, 59, 0.4)';
          let statusBorder = 'rgba(255, 255, 255, 0.08)';
          let statusColor = 'var(--text-dim)';
          let iconElement = <Clock size={18} style={{ color: 'var(--text-dim)' }} />;

          if (status === 'complete') {
            statusBg = 'rgba(16, 185, 129, 0.1)';
            statusBorder = 'rgba(16, 185, 129, 0.3)';
            statusColor = 'var(--text-main)';
            iconElement = <CheckCircle2 size={18} style={{ color: '#10b981' }} />;
          } else if (status === 'processing') {
            statusBg = 'rgba(6, 182, 212, 0.15)';
            statusBorder = 'rgba(6, 182, 212, 0.4)';
            statusColor = 'var(--accent-cyan)';
            iconElement = <RefreshCw size={18} className="spin" style={{ color: 'var(--accent-cyan)' }} />;
          } else if (status === 'unsupplied') {
            statusBg = 'rgba(30, 41, 59, 0.2)';
            statusBorder = 'rgba(255, 255, 255, 0.05)';
            statusColor = 'var(--text-dim)';
            iconElement = <MinusCircle size={18} style={{ color: 'var(--text-dim)' }} />;
          } else if (status === 'failed') {
            statusBg = 'rgba(239, 68, 68, 0.15)';
            statusBorder = 'rgba(239, 68, 68, 0.4)';
            statusColor = '#fca5a5';
            iconElement = <AlertCircle size={18} style={{ color: '#ef4444' }} />;
          }

          return (
            <div
              key={item.key}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                borderRadius: '10px',
                background: statusBg,
                border: `1px solid ${statusBorder}`,
                transition: 'all 0.25s ease'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                <div style={{ flexShrink: 0 }}>{iconElement}</div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: '0.88rem', color: statusColor }}>
                    {item.label}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: status === 'unsupplied' ? 'var(--text-dim)' : 'var(--text-muted)', marginTop: '2px' }}>
                    {item.desc}
                  </div>
                </div>
              </div>

              <div style={{ flexShrink: 0 }}>
                {status === 'complete' && <span className="badge badge-emerald" style={{ fontSize: '0.7rem' }}>COMPLETE</span>}
                {status === 'processing' && <span className="badge badge-cyan" style={{ fontSize: '0.7rem' }}>PROCESSING...</span>}
                {status === 'unsupplied' && <span className="badge badge-outline" style={{ fontSize: '0.7rem', opacity: 0.6 }}>NOT SUPPLIED</span>}
                {status === 'waiting' && <span className="badge badge-outline" style={{ fontSize: '0.7rem', opacity: 0.5 }}>WAITING</span>}
                {status === 'failed' && <span className="badge badge-rose" style={{ fontSize: '0.7rem' }}>FAILED</span>}
              </div>
            </div>
          );
        })}
      </div>

      {/* FAILED STATE CARD */}
      {stage === 'failed' && (
        <div style={{
          padding: '16px 20px',
          borderRadius: '12px',
          background: 'rgba(239, 68, 68, 0.15)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          marginBottom: '24px',
          color: '#fca5a5',
          fontSize: '0.88rem'
        }}>
          <div style={{ fontWeight: 700, marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertCircle size={18} style={{ color: '#ef4444' }} /> Pipeline Error Details:
          </div>
          <div>{error || 'Unable to complete AI analysis. Check input data or retry execution.'}</div>
          {typeof onRetry === 'function' && (
            <button className="btn btn-outline" onClick={onRetry} style={{ marginTop: '12px', fontSize: '0.8rem', borderColor: '#ef4444', color: '#f87171' }}>
              <RefreshCw size={14} /> Retry Analysis Execution
            </button>
          )}
        </div>
      )}

      {/* COMPLETION SUMMARY BOX */}
      {stage === 'complete' && (
        <div style={{
          padding: '20px',
          borderRadius: '12px',
          background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.12) 0%, rgba(6, 182, 212, 0.12) 100%)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          marginBottom: '24px',
          textAlign: 'center'
        }}>
          <div style={{ fontSize: '1rem', fontWeight: 800, color: 'var(--text-main)', marginBottom: '8px' }}>
            Assessment Summary Ready
          </div>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '16px', flexWrap: 'wrap', fontSize: '0.82rem', color: 'var(--text-muted)', marginBottom: '16px' }}>
            <span>✓ 5 Screening Signals Generated</span>
            <span>✓ SHAP Explainability Calculated</span>
            <span>✓ RAG Evidence Grounded</span>
          </div>

          <button
            className="btn btn-primary"
            onClick={onNavigateDashboard}
            style={{ padding: '10px 28px', fontSize: '0.92rem', borderRadius: '8px' }}
          >
            View Health Command Center <ArrowRight size={16} />
          </button>
        </div>
      )}
    </div>
  );
}
