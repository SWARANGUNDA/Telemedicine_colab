import React from 'react';
import { ResponsiveContainer, RadialBarChart, RadialBar, PolarAngleAxis } from 'recharts';
import { Info } from 'lucide-react';

export default function RiskGauge({ diseaseName = '', probability = 0, threshold = 0.3, prediction = 0, showHeader = false }) {
  const safeProb = Number(probability) || 0;
  const safeThresh = Number(threshold) || 0.3;
  const probPct = (safeProb * 100).toFixed(1);
  const cutoffPct = (safeThresh * 100).toFixed(0);
  const isPositive = prediction === 1 || prediction === true;
  const displayName = diseaseName ? String(diseaseName).replace(/_/g, ' ') : '';

  const data = [
    {
      name: displayName,
      value: Math.min(Math.max(safeProb * 100, 2), 100), // ensure visual arc for tiny/zero values
      fill: isPositive ? '#f43f5e' : '#10b981'
    }
  ];

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      width: '100%',
      position: 'relative'
    }}>
      {showHeader && displayName && (
        <div style={{
          fontSize: '0.95rem',
          fontWeight: 700,
          color: 'var(--text-main)',
          marginBottom: '10px',
          textAlign: 'center',
          lineHeight: 1.2,
          minHeight: '2.4em',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center'
        }}>
          {displayName}
        </div>
      )}

      {/* RadialBarChart Gauge */}
      <div style={{ width: '100%', height: '130px', position: 'relative' }}>
        <ResponsiveContainer width="100%" height="100%">
          <RadialBarChart
            cx="50%"
            cy="50%"
            innerRadius="70%"
            outerRadius="100%"
            barSize={10}
            data={data}
            startAngle={225}
            endAngle={-45}
          >
            <PolarAngleAxis type="number" domain={[0, 100]} angleAxisId={0} tick={false} />
            <RadialBar
              background={{ fill: 'rgba(255, 255, 255, 0.08)' }}
              dataKey="value"
              cornerRadius={5}
              angleAxisId={0}
            />
          </RadialBarChart>
        </ResponsiveContainer>

        <div style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          textAlign: 'center',
          width: '80%'
        }}>
          <div style={{ fontSize: '1.5rem', fontWeight: 800, color: isPositive ? 'var(--accent-rose)' : 'var(--accent-emerald)' }}>
            {probPct}%
          </div>
          <div style={{ fontSize: '0.65rem', color: 'var(--text-dim)', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.03em' }}>
            MODEL-ESTIMATED SCORE
          </div>
        </div>
      </div>

      {/* Status & Threshold Info */}
      <div style={{ marginTop: '8px', textAlign: 'center', width: '100%' }}>
        <span className={`badge ${isPositive ? 'badge-rose' : 'badge-emerald'}`} style={{ fontSize: '0.7rem', padding: '4px 10px', letterSpacing: '0.02em' }}>
          {isPositive ? 'POSITIVE SCREENING SIGNAL' : 'NEGATIVE SCREENING SIGNAL'}
        </span>

        <div style={{ fontSize: '0.75rem', color: 'var(--text-dim)', marginTop: '8px', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px' }}>
          <span>Decision threshold: {cutoffPct}%</span>
          <span title="The decision threshold is the model's classification cutoff and is not a clinical diagnostic cutoff. Model-estimated scores are decision-support outputs, not medical diagnoses.">
            <Info size={13} style={{ color: 'var(--accent-cyan)', cursor: 'pointer', flexShrink: 0 }} />
          </span>
        </div>
      </div>
    </div>
  );
}

