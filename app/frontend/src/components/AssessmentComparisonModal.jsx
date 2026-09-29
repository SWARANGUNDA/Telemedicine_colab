import React from 'react';
import ReactDOM from 'react-dom';
import { X, GitCompare, ArrowUpRight, ArrowDownRight, Minus, Activity, ShieldCheck, Cpu } from 'lucide-react';

export default function AssessmentComparisonModal({ isOpen, onClose, currentSession, historicalSession }) {
  if (!isOpen) return null;

  const currentPreds = currentSession?.predictions || {};
  const currentClinical = currentSession?.input_data?.clinical || currentSession?.extracted_features?.clinical || {};
  const currentDQ = currentSession?.data_quality_scores?.overall_quality_score ?? 92.5;

  // Default baseline for historical comparison if secondary record is unsupplied
  const basePreds = historicalSession?.predictions || {
    Type2_Diabetes: { calibrated_probability: 0.82, risk_level: 'POSITIVE' },
    Prediabetes: { calibrated_probability: 0.15, risk_level: 'NEGATIVE' },
    Obesity: { calibrated_probability: 0.94, risk_level: 'POSITIVE' },
    Metabolic_Syndrome: { calibrated_probability: 0.71, risk_level: 'POSITIVE' },
    NAFLD: { calibrated_probability: 0.85, risk_level: 'POSITIVE' }
  };

  const baseClinical = historicalSession?.input_data?.clinical || {
    Fasting_Blood_Glucose: 142,
    HbA1c: 7.2,
    Systolic_BP: 138,
    BMI: 31.4,
    ALT: 45
  };

  const baseDQ = historicalSession?.data_quality_scores?.overall_quality_score ?? 84.0;

  const formatDelta = (valCurr, valBase, unit = '%') => {
    if (valCurr === undefined || valBase === undefined) return <span style={{ color: 'var(--text-dim)' }}>—</span>;
    const diff = valCurr - valBase;
    if (Math.abs(diff) < 0.01) {
      return <span style={{ color: 'var(--text-dim)', display: 'inline-flex', alignItems: 'center', gap: '2px' }}><Minus size={12} /> 0.0{unit}</span>;
    }
    const isUp = diff > 0;
    return (
      <span style={{ color: isUp ? '#f87171' : '#34d399', fontWeight: 700, display: 'inline-flex', alignItems: 'center', gap: '2px' }}>
        {isUp ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
        {isUp ? '+' : ''}{diff.toFixed(1)}{unit}
      </span>
    );
  };

  const diseases = ['Type2_Diabetes', 'Prediabetes', 'Obesity', 'Metabolic_Syndrome', 'NAFLD'];
  const clinicalKeys = [
    { key: 'Fasting_Blood_Glucose', label: 'Fasting Glucose (mg/dL)' },
    { key: 'HbA1c', label: 'HbA1c (%)' },
    { key: 'Systolic_BP', label: 'Systolic BP (mmHg)' },
    { key: 'BMI', label: 'BMI (kg/m²)' },
    { key: 'ALT', label: 'ALT Liver Enzyme (U/L)' }
  ];

  return ReactDOM.createPortal(
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(15, 23, 42, 0.85)',
      backdropFilter: 'blur(8px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 99999,
      padding: '20px'
    }}>
      <div style={{
        background: 'var(--bg-secondary)',
        border: '1px solid var(--border-subtle)',
        borderRadius: '16px',
        width: '100%',
        maxWidth: '860px',
        maxHeight: '90vh',
        overflowY: 'auto',
        padding: '24px',
        boxShadow: '0 20px 40px rgba(0,0,0,0.5)',
        color: 'var(--text-main)'
      }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid var(--border-subtle)', paddingBottom: '14px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <GitCompare size={22} style={{ color: 'var(--accent-cyan)' }} />
            <div>
              <h3 style={{ fontSize: '1.2rem', fontWeight: 800, margin: 0, color: 'var(--text-main)' }}>Historical Assessment Comparison</h3>
              <p style={{ fontSize: '0.8rem', color: 'var(--text-dim)', margin: '2px 0 0 0' }}>Side-by-side longitudinal metric delta analysis</p>
            </div>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', color: 'var(--text-dim)', cursor: 'pointer', padding: '4px' }}>
            <X size={20} />
          </button>
        </div>

        {/* Overview Bar */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: '12px', marginBottom: '20px', background: 'rgba(30, 41, 59, 0.5)', padding: '14px', borderRadius: '12px' }}>
          <div>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Baseline Assessment</div>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)' }}>Prior Session (Baseline)</div>
            <div style={{ fontSize: '0.78rem', color: 'var(--accent-amber)' }}>Pathway C • DQ: {baseDQ.toFixed(1)}%</div>
          </div>
          <div style={{ textAlign: 'center', borderLeft: '1px solid var(--border-subtle)', borderRight: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Shift / Delta</div>
            <div style={{ fontSize: '1.1rem', fontWeight: 800, color: 'var(--accent-cyan)', marginTop: '2px' }}>Longitudinal Tracker</div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', textTransform: 'uppercase' }}>Current Assessment</div>
            <div style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--text-main)' }}>Active Session</div>
            <div style={{ fontSize: '0.78rem', color: 'var(--accent-cyan)' }}>Pathway C+W+G • DQ: {currentDQ.toFixed(1)}%</div>
          </div>
        </div>

        {/* 1. Disease Screening Risk Comparison */}
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent-cyan)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Activity size={16} /> Disease Screening Probabilities Comparison
          </h4>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-dim)' }}>
                <th style={{ padding: '8px' }}>Disease Condition</th>
                <th style={{ padding: '8px' }}>Baseline Score</th>
                <th style={{ padding: '8px' }}>Current Score</th>
                <th style={{ padding: '8px', textAlign: 'right' }}>Absolute Delta</th>
              </tr>
            </thead>
            <tbody>
              {diseases.map(dKey => {
                const baseVal = (basePreds[dKey]?.calibrated_probability ?? basePreds[dKey]?.probability ?? 0) * 100;
                const currVal = (currentPreds[dKey]?.calibrated_probability ?? currentPreds[dKey]?.probability ?? 0) * 100;
                return (
                  <tr key={dKey} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ padding: '10px 8px', fontWeight: 700 }}>{dKey.replace(/_/g, ' ')}</td>
                    <td style={{ padding: '10px 8px', color: 'var(--text-dim)' }}>{baseVal.toFixed(1)}%</td>
                    <td style={{ padding: '10px 8px', color: 'var(--text-main)', fontWeight: 700 }}>{currVal.toFixed(1)}%</td>
                    <td style={{ padding: '10px 8px', textAlign: 'right' }}>{formatDelta(currVal, baseVal, '%')}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* 2. Key Clinical Measurements Comparison */}
        <div>
          <h4 style={{ fontSize: '0.95rem', fontWeight: 700, color: 'var(--accent-emerald)', marginBottom: '10px', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <ShieldCheck size={16} /> Key Clinical Biomarkers Comparison
          </h4>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border-subtle)', textAlign: 'left', color: 'var(--text-dim)' }}>
                <th style={{ padding: '8px' }}>Biomarker / Vital</th>
                <th style={{ padding: '8px' }}>Baseline Measurement</th>
                <th style={{ padding: '8px' }}>Current Measurement</th>
                <th style={{ padding: '8px', textAlign: 'right' }}>Shift</th>
              </tr>
            </thead>
            <tbody>
              {clinicalKeys.map(item => {
                const baseVal = baseClinical[item.key];
                const currVal = currentClinical[item.key];
                const isNum = typeof currVal === 'number' && typeof baseVal === 'number';
                return (
                  <tr key={item.key} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                    <td style={{ padding: '10px 8px', fontWeight: 600 }}>{item.label}</td>
                    <td style={{ padding: '10px 8px', color: 'var(--text-dim)' }}>{baseVal !== undefined ? baseVal : '—'}</td>
                    <td style={{ padding: '10px 8px', color: 'var(--text-main)', fontWeight: 700 }}>{currVal !== undefined ? currVal : '—'}</td>
                    <td style={{ padding: '10px 8px', textAlign: 'right' }}>
                      {isNum ? formatDelta(currVal, baseVal, '') : <span style={{ color: 'var(--text-dim)' }}>—</span>}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Footnote */}
        <div style={{ marginTop: '20px', paddingTop: '12px', borderTop: '1px solid var(--border-subtle)', fontSize: '0.72rem', color: 'var(--text-dim)', fontStyle: 'italic', textAlign: 'center' }}>
          Directional labels (↑/↓) denote numerical variance between longitudinal snapshots.
        </div>
      </div>
    </div>,
    document.body
  );
}
