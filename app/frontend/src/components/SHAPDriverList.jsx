import React, { useState } from 'react';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, ReferenceLine } from 'recharts';
import { ArrowUpRight, ArrowDownRight, ChevronDown, ChevronUp, Info, HelpCircle } from 'lucide-react';
import { classifyBiomarker } from '../utils/clinicalRanges';

const FEATURE_PATIENT_METADATA = {
  Fasting_Blood_Glucose: { friendlyName: 'Fasting Blood Glucose', unit: 'mg/dL', refRange: '70–99 mg/dL' },
  HbA1c: { friendlyName: 'HbA1c (Long-term Glucose)', unit: '%', refRange: '< 5.7%' },
  Systolic_BP: { friendlyName: 'Systolic Blood Pressure', unit: 'mmHg', refRange: '< 120 mmHg' },
  Diastolic_BP: { friendlyName: 'Diastolic Blood Pressure', unit: 'mmHg', refRange: '< 80 mmHg' },
  BMI: { friendlyName: 'Body Mass Index (BMI)', unit: 'kg/m²', refRange: '18.5–24.9 kg/m²' },
  Waist_Circumference: { friendlyName: 'Waist Circumference', unit: 'cm', refRange: '< 88–102 cm' },
  Triglycerides: { friendlyName: 'Triglycerides', unit: 'mg/dL', refRange: '< 150 mg/dL' },
  HDL: { friendlyName: 'HDL (Good Cholesterol)', unit: 'mg/dL', refRange: '≥ 40 mg/dL' },
  LDL: { friendlyName: 'LDL (Cholesterol)', unit: 'mg/dL', refRange: '< 100 mg/dL' },
  ALT: { friendlyName: 'ALT (Liver Enzyme)', unit: 'U/L', refRange: '7–56 U/L' },
  AST: { friendlyName: 'AST (Liver Enzyme)', unit: 'U/L', refRange: '10–40 U/L' },
  Age: { friendlyName: 'Age', unit: 'years', refRange: 'Demographic baseline' },
  Gender: { friendlyName: 'Gender', unit: '', refRange: 'Demographic baseline' },
  Family_History_Diabetes: { friendlyName: 'Family History of Diabetes', unit: '', refRange: 'Yes/No' },
  Family_History_Hypertension: { friendlyName: 'Family History of Hypertension', unit: '', refRange: 'Yes/No' },
  Resting_Heart_Rate: { friendlyName: 'Resting Heart Rate', unit: 'bpm', refRange: '60–100 bpm' },
  Daily_Steps: { friendlyName: 'Daily Step Count', unit: 'steps/day', refRange: '8,000–10,000 steps' },
  Sleep_Hours: { friendlyName: 'Sleep Duration', unit: 'hours/night', refRange: '7–9 hours' }
};

function getFeatureMeta(rawKey, val) {
  const numVal = parseFloat(val);
  const info = classifyBiomarker(rawKey, !isNaN(numVal) ? numVal : val);
  const fallback = FEATURE_PATIENT_METADATA[rawKey] || {};
  return {
    friendlyName: info.friendlyName || fallback.friendlyName || rawKey.replace(/_/g, ' '),
    unit: info.unit || fallback.unit || '',
    refRange: info.refRange || fallback.refRange || 'Standard range',
    status: info.label
  };
}

export default function SHAPDriverList({ drivers, isDoctorView = false }) {
  const [showTechnical, setShowTechnical] = useState(false);

  if (!drivers || drivers.length === 0) {
    return (
      <div style={{ fontSize: '0.875rem', color: 'var(--text-muted)', fontStyle: 'italic', padding: '16px' }}>
        No statistical feature attributions available for this model expert.
      </div>
    );
  }

  // Process data for presentation
  const processedData = drivers.map((d) => {
    const rawKey = d.feature || d.feature_name || '';
    const isMissing = d.is_missing_value_influence || d.value === 'Not provided (missing-value model influence)';
    const isImputed = d.is_imputed === true;
    const rawVal = d.value !== undefined ? d.value : d.scaled_value;
    const valDisplay = isMissing ? 'Not provided' : (rawVal !== undefined && rawVal !== null ? rawVal : 'N/A');
    const rawShap = d.shap_attribution ?? d.shap_value ?? d.shap_val ?? 0;
    const meta = getFeatureMeta(rawKey, rawVal);

    // Patient friendly explanation (Max 1 sentence, strictly non-causal)
    const directionLabel = rawShap > 0 ? 'Higher-score factor' : 'Lower-score factor';
    const explanation = rawShap > 0
      ? `Measurement value of ${valDisplay} ${meta.unit ? meta.unit : ''} contributed to a higher screening score in model estimation.`
      : `Measurement value of ${valDisplay} ${meta.unit ? meta.unit : ''} contributed to a lower screening score in model estimation.`;

    return {
      rawKey,
      friendlyName: meta.friendlyName,
      unit: meta.unit,
      status: meta.status,
      refRange: meta.refRange,
      rawShap: typeof rawShap === 'number' && !isNaN(rawShap) ? rawShap : 0,
      absShap: Math.abs(typeof rawShap === 'number' && !isNaN(rawShap) ? rawShap : 0),
      directionLabel,
      explanation,
      valueDisplay: valDisplay,
      isMissing,
      isImputed
    };
  });

  // Sort by attribution magnitude
  const sortedData = [...processedData].sort((a, b) => b.absShap - a.absShap);
  const mainFactors = sortedData.slice(0, 3);
  const otherFactors = sortedData.slice(3);

  const CustomSHAPTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const item = payload[0].payload;
      const shapNum = item.rawShap || 0;
      return (
        <div className="custom-recharts-tooltip">
          <p style={{ fontWeight: 700, color: 'var(--text-main)' }}>{item.friendlyName} ({item.rawKey})</p>
          <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: '4px 0' }}>
            Measured Value: <strong style={{ color: item.isMissing ? 'var(--accent-amber)' : 'var(--text-main)' }}>{item.valueDisplay} {item.unit}</strong>
          </p>
          <p style={{ fontSize: '0.8rem', color: shapNum > 0 ? 'var(--accent-rose)' : 'var(--accent-emerald)' }}>
            TreeSHAP Attribution: <strong>{shapNum > 0 ? `+${shapNum.toFixed(4)}` : shapNum.toFixed(4)}</strong> ({item.directionLabel})
          </p>
          <p style={{ fontSize: '0.7rem', color: 'var(--text-dim)', marginTop: '6px', fontStyle: 'italic' }}>
            TreeSHAP log-odds contribution to active expert model. Indicates statistical model association, NOT biological causality.
          </p>
        </div>
      );
    }
    return null;
  };

  // DOCTOR TECHNICAL VIEW
  if (isDoctorView) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
        <div style={{ width: '100%', height: `${processedData.length * 45 + 35}px` }}>
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              layout="vertical"
              data={processedData}
              margin={{ top: 5, right: 30, left: 160, bottom: 5 }}
            >
              <XAxis type="number" stroke="var(--text-dim)" fontSize={11} />
              <YAxis type="category" dataKey="rawKey" stroke="var(--text-main)" fontSize={12} tickLine={false} width={150} />
              <Tooltip content={<CustomSHAPTooltip />} />
              <ReferenceLine x={0} stroke="var(--border-medium)" />
              <Bar dataKey="rawShap" radius={[4, 4, 4, 4]} barSize={16}>
                {processedData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.rawShap > 0 ? '#f43f5e' : '#10b981'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {processedData.map((item, idx) => (
            <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: 'var(--bg-primary)', borderRadius: '8px', border: '1px solid var(--border-subtle)', fontSize: '0.82rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontWeight: 700, color: 'var(--text-main)' }}>{item.rawKey}</span>
                <span style={{ color: 'var(--text-muted)' }}>Value: {item.valueDisplay} {item.unit}</span>
              </div>
              <span className={`badge ${item.rawShap > 0 ? 'badge-rose' : 'badge-emerald'}`}>
                {item.rawShap > 0 ? `+${item.rawShap.toFixed(4)}` : item.rawShap.toFixed(4)} log-odds
              </span>
            </div>
          ))}
        </div>
      </div>
    );
  }

  // PATIENT-FRIENDLY VIEW
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
      {/* Summary Banner */}
      <div style={{ padding: '12px 16px', background: 'var(--bg-primary)', borderRadius: '10px', borderLeft: '3px solid var(--accent-cyan)', fontSize: '0.85rem', color: 'var(--text-main)' }}>
        <strong>Summary:</strong> Your score was mainly influenced by these health measurements.
      </div>

      {/* SECTION 1: Main Factors */}
      <div>
        <div style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--accent-cyan)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '8px' }}>
          Main Factors (Top Predictors)
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {mainFactors.map((item, idx) => {
            const isHigher = item.rawShap > 0;
            return (
              <div
                key={idx}
                style={{
                  padding: '14px 16px',
                  background: 'var(--bg-primary)',
                  borderRadius: '10px',
                  border: '1px solid var(--border-subtle)',
                  borderLeft: `4px solid ${isHigher ? 'var(--accent-rose)' : 'var(--accent-emerald)'}`,
                  display: 'flex',
                  flexDirection: 'column',
                  gap: '6px'
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <span style={{ fontWeight: 800, fontSize: '0.92rem', color: 'var(--text-main)' }}>
                      {item.friendlyName}
                    </span>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-dim)' }}>
                      (Value: <strong style={{ color: 'var(--text-main)' }}>{item.valueDisplay} {item.unit}</strong>)
                    </span>
                    {item.status && (
                      <span className={`badge ${item.status === 'Elevated' ? 'badge-rose' : (item.status === 'Borderline' ? 'badge-amber' : 'badge-emerald')}`} style={{ fontSize: '0.68rem', padding: '1px 6px' }}>
                        {item.status}
                      </span>
                    )}
                  </div>
                  <span className={`badge ${isHigher ? 'badge-rose' : 'badge-emerald'}`} style={{ fontSize: '0.72rem' }}>
                    {isHigher ? <ArrowUpRight size={12} /> : <ArrowDownRight size={12} />}
                    {item.directionLabel}
                  </span>
                </div>

                <p style={{ fontSize: '0.8rem', color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>
                  {item.explanation}
                </p>
              </div>
            );
          })}
        </div>
      </div>

      {/* SECTION 2: Other Factors (if any) */}
      {otherFactors.length > 0 && (
        <div>
          <div style={{ fontSize: '0.78rem', fontWeight: 800, color: 'var(--text-dim)', textTransform: 'uppercase', letterSpacing: '0.04em', marginBottom: '8px' }}>
            Other Factors
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {otherFactors.map((item, idx) => {
              const isHigher = item.rawShap > 0;
              return (
                <div key={idx} style={{ padding: '10px 14px', background: 'var(--bg-primary)', borderRadius: '8px', border: '1px solid var(--border-subtle)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '8px' }}>
                  <div>
                    <span style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--text-main)' }}>{item.friendlyName}</span>
                    <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', marginLeft: '8px' }}>
                      {item.valueDisplay} {item.unit}
                    </span>
                  </div>
                  <span className={`badge ${isHigher ? 'badge-rose' : 'badge-emerald'}`} style={{ fontSize: '0.68rem' }}>
                    {item.directionLabel}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* SECTION 3: Technical Details (Collapsed by Default) */}
      <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '12px', marginTop: '4px' }}>
        <button
          className="btn btn-outline"
          onClick={() => setShowTechnical(!showTechnical)}
          style={{ width: '100%', fontSize: '0.78rem', padding: '6px 12px', justifyContent: 'space-between' }}
        >
          <span>Technical SHAP Attribution Details (Model Experts)</span>
          {showTechnical ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        </button>

        {showTechnical && (
          <div style={{ marginTop: '12px', padding: '14px', borderRadius: '10px', background: 'var(--bg-surface)', border: '1px solid var(--border-subtle)' }}>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', fontStyle: 'italic', marginBottom: '12px' }}>
              TreeSHAP log-odds feature contributions calculated across frozen expert ensembles prior to sigmoid calibration.
            </div>

            <div style={{ width: '100%', height: `${processedData.length * 40 + 30}px`, marginBottom: '12px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  layout="vertical"
                  data={processedData}
                  margin={{ top: 5, right: 30, left: 160, bottom: 5 }}
                >
                  <XAxis type="number" stroke="var(--text-dim)" fontSize={11} />
                  <YAxis type="category" dataKey="rawKey" stroke="var(--text-main)" fontSize={11} tickLine={false} width={150} />
                  <Tooltip content={<CustomSHAPTooltip />} />
                  <ReferenceLine x={0} stroke="var(--border-medium)" />
                  <Bar dataKey="rawShap" radius={[4, 4, 4, 4]} barSize={14}>
                    {processedData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.rawShap > 0 ? '#f43f5e' : '#10b981'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      <div style={{ fontSize: '0.72rem', color: 'var(--text-dim)', fontStyle: 'italic', marginTop: '4px' }}>
        Note: Model feature attributions reflect statistical pattern association within the trained dataset, NOT biological causality, medical diagnosis, or treatment efficacy.
      </div>
    </div>
  );
}

