import React from 'react';

export default function DisclaimerBanner() {
  return (
    <div style={{ background: 'rgba(251, 191, 36, 0.15)', borderBottom: '1px solid rgba(251, 191, 36, 0.3)', padding: '10px 20px', textAlign: 'center', fontSize: '0.85rem', color: '#fbbf24' }}>
      <strong>RESEARCH PROTOTYPE DISCLAIMER:</strong> This AI system is trained on synthetic multimodal data for decision-support evaluation. Model output probabilities and XAI attributions do NOT constitute clinical diagnosis or medical prescription. Always consult a licensed healthcare professional.
    </div>
  );
}
