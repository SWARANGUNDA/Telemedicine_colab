import React from 'react';

export default function ModalityBadge({ routingMetadata }) {
  if (!routingMetadata) return null;

  const {
    modalities_supplied = [],
    missing_modalities = [],
    effective_pathway = 'C',
    primary_decision_anchor = 'Clinical_v3',
    cgm_status = 'NO_WEARABLE_DATA',
    imputed_features_by_modality = {}
  } = routingMetadata;

  const hasClinical = modalities_supplied.includes('clinical');
  const hasWearable = modalities_supplied.includes('wearable');
  const hasGut = modalities_supplied.includes('gut');

  const cImputed = imputed_features_by_modality.clinical || [];
  const wImputed = imputed_features_by_modality.wearable || [];
  const gImputed = imputed_features_by_modality.gut || [];
  const totalImputedCount = cImputed.length + wImputed.length + gImputed.length;

  return (
    <div style={{
      background: '#1e293b',
      border: '1px solid #334155',
      borderRadius: '12px',
      padding: '16px 20px',
      marginBottom: '24px',
      color: '#f8fafc'
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <span style={{ fontSize: '0.85rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Executed Pathway
          </span>
          <div style={{ fontSize: '1.25rem', fontWeight: '700', color: '#38bdf8', marginTop: '2px' }}>
            Pathway {effective_pathway}
          </div>
        </div>

        <div>
          <span style={{ fontSize: '0.85rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Primary Diagnostic Anchor
          </span>
          <div style={{ fontSize: '1rem', fontWeight: '600', color: '#e2e8f0', marginTop: '2px' }}>
            {primary_decision_anchor}
          </div>
        </div>

        <div>
          <span style={{ fontSize: '0.85rem', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            CGM Telemetry Status
          </span>
          <div style={{ fontSize: '0.95rem', fontWeight: '600', color: cgm_status.includes('FULL') ? '#4ade80' : cgm_status.includes('PARTIAL') ? '#facc15' : '#94a3b8', marginTop: '2px' }}>
            {cgm_status}
          </div>
        </div>
      </div>

      <hr style={{ border: '0', borderTop: '1px solid #334155', margin: '14px 0' }} />

      <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.85rem', color: '#94a3b8', fontWeight: '600' }}>Active Modalities:</span>
        <span style={{
          padding: '4px 10px', borderRadius: '20px', fontSize: '0.8rem', fontWeight: '600',
          background: hasClinical ? '#065f46' : '#334155', color: hasClinical ? '#34d399' : '#64748b'
        }}>
          {hasClinical ? '✓ Clinical Labs (18D)' : '✗ Clinical Labs Missing'}
        </span>
        <span style={{
          padding: '4px 10px', borderRadius: '20px', fontSize: '0.8rem', fontWeight: '600',
          background: hasWearable ? '#1e40af' : '#334155', color: hasWearable ? '#60a5fa' : '#64748b'
        }}>
          {hasWearable ? '✓ Wearable Telemetry (15D)' : '✗ Wearable Telemetry Missing'}
        </span>
        <span style={{
          padding: '4px 10px', borderRadius: '20px', fontSize: '0.8rem', fontWeight: '600',
          background: hasGut ? '#701a75' : '#334155', color: hasGut ? '#f0abfc' : '#64748b'
        }}>
          {hasGut ? '✓ Gut Microbiome (20 Taxa)' : '✗ Gut Microbiome Missing'}
        </span>
      </div>

      {totalImputedCount > 0 && (
        <div style={{ marginTop: '10px', fontSize: '0.8rem', color: '#fbbf24', background: 'rgba(251, 191, 36, 0.1)', padding: '6px 12px', borderRadius: '6px' }}>
          <strong>Note:</strong> {totalImputedCount} missing feature(s) inside active modalities were imputed using stored training medians:
          {cImputed.length > 0 && <span> Clinical ({cImputed.join(', ')})</span>}
          {wImputed.length > 0 && <span> Wearable ({wImputed.join(', ')})</span>}
          {gImputed.length > 0 && <span> Gut ({gImputed.join(', ')})</span>}
        </div>
      )}
    </div>
  );
}
