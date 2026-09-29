import React, { useState } from 'react';
import { Card, Badge, ProgressBar, Button } from '../ui';
import { ShieldCheck, Activity, ChevronDown, ChevronUp, Dna, FileText, Watch, HelpCircle } from 'lucide-react';

export default function ExplainabilityStudio({ predictionData, xaiData }) {
  const [modalityFilter, setModalityFilter] = useState('ALL');
  const [showAll, setShowAll] = useState(false);
  const [expandedIdx, setExpandedIdx] = useState(null);

  // Extract SHAP drivers from the REAL xaiData.attributions structure
  // Backend returns: { attributions: { clinical: { all_features: [...] }, wearable: { all_features: [...] }, gut: { all_features: [...] } } }
  const attributions = xaiData?.attributions || {};

  const shapDrivers = [];

  // Process each modality from xaiData attributions
  Object.keys(attributions).forEach(modality => {
    const modData = attributions[modality];
    const features = modData?.all_features || modData?.top_risk_drivers || [];

    features.forEach((f) => {
      const rawName = f.feature_name || f.feature || f.name || 'Unknown';
      shapDrivers.push({
        name: rawName,
        displayName: rawName.replace(/_/g, ' '),
        value: f.value !== undefined ? `${f.value}` : 'Extracted',
        shapValue: f.shap_value || f.shap_attribution || 0,
        shapDisplay: (f.shap_value || f.shap_attribution) ? ((f.shap_value || f.shap_attribution) > 0 ? `+${(f.shap_value || f.shap_attribution).toFixed(4)}` : (f.shap_value || f.shap_attribution).toFixed(4)) : '0.0000',
        impact: (f.shap_value || f.shap_attribution || 0) > 0 ? 'INCREASES RISK' : 'LOWERS RISK',
        direction: f.direction || ((f.shap_value || 0) > 0 ? 'Increases Risk' : 'Decreases Risk'),
        modality: modality.charAt(0).toUpperCase() + modality.slice(1),
        isImputed: f.is_imputed || false,
        pct: Math.min(Math.abs(Math.round((f.shap_value || f.shap_attribution || 0.05) * 1000)), 100),
        variant: (f.shap_value || f.shap_attribution || 0) > 0 ? 'danger' : 'success',
        explanation: getPlainExplanation(rawName, f.value, f.shap_value || f.shap_attribution || 0)
      });
    });
  });

  // Also check predictionData.top_shap_features as fallback
  if (shapDrivers.length === 0 && predictionData?.top_shap_features) {
    predictionData.top_shap_features.forEach((f, idx) => {
      const rawName = f.feature_name || f.name || `Feature ${idx + 1}`;
      shapDrivers.push({
        name: rawName,
        displayName: rawName.replace(/_/g, ' '),
        value: f.feature_value !== undefined ? `${f.feature_value}` : 'Extracted',
        shapValue: f.shap_value || 0,
        shapDisplay: f.shap_value ? (f.shap_value > 0 ? `+${f.shap_value.toFixed(4)}` : f.shap_value.toFixed(4)) : '0.0000',
        impact: (f.shap_value || 0) > 0 ? 'INCREASES RISK' : 'LOWERS RISK',
        direction: (f.shap_value || 0) > 0 ? 'Increases Risk' : 'Decreases Risk',
        modality: f.modality || 'Clinical',
        isImputed: false,
        pct: Math.min(Math.abs(Math.round((f.shap_value || 0.05) * 1000)), 100),
        variant: (f.shap_value || 0) > 0 ? 'danger' : 'success',
        explanation: getPlainExplanation(rawName, f.feature_value, f.shap_value || 0)
      });
    });
  }

  // Sort by absolute SHAP value (most impactful first)
  shapDrivers.sort((a, b) => Math.abs(b.shapValue) - Math.abs(a.shapValue));

  const filteredDrivers = shapDrivers.filter(d => modalityFilter === 'ALL' || d.modality.toLowerCase() === modalityFilter.toLowerCase());
  const visibleDrivers = showAll ? filteredDrivers : filteredDrivers.slice(0, 8);
  const hasMore = filteredDrivers.length > 8;

  // Which modalities have data
  const availableModalities = ['ALL', ...new Set(shapDrivers.map(d => d.modality))];

  return (
    <Card isGlass={true} className="p-6 space-y-5 shadow-xl border-t-4 border-t-[var(--secondary)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-[var(--secondary)]" />
          <div>
            <h3 className="text-base font-extrabold text-[var(--text-main)]">AI Explainability Studio</h3>
            <p className="text-[10px] text-[var(--text-muted)]">Understand which health factors influenced your risk scores the most</p>
          </div>
        </div>
        <Badge variant="secondary" size="sm">{filteredDrivers.length} Factors Analyzed</Badge>
      </div>

      {/* Plain language explanation banner */}
      <div className="p-3 rounded-xl bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 text-xs text-blue-800 dark:text-blue-200 flex items-start gap-2">
        <HelpCircle className="w-4 h-4 mt-0.5 shrink-0" />
        <div>
          <strong>How to read this:</strong> Each health factor below shows how much it pushed your risk score up (red = increases risk) or down (green = lowers risk). Factors at the top had the biggest influence on your results.
        </div>
      </div>

      {/* Modality Filter Pills — only show modalities that have data */}
      <div className="flex items-center gap-2 border-b border-[var(--border-subtle)] pb-2 overflow-x-auto">
        {availableModalities.map((mod) => (
          <button
            key={mod}
            onClick={() => setModalityFilter(mod)}
            className={`px-3 py-1 rounded-lg text-xs font-semibold font-mono transition-all ${
              modalityFilter === mod
                ? 'bg-[var(--secondary)] text-white shadow-sm'
                : 'bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-[var(--text-muted)] hover:text-[var(--text-main)]'
            }`}
          >
            {mod === 'ALL' ? 'All Types' : mod === 'Clinical' ? '🩺 Lab Tests' : mod === 'Wearable' ? '⌚ Wearable' : mod === 'Gut' ? '🧬 Gut Microbiome' : mod}
          </button>
        ))}
      </div>

      {/* SHAP Drivers List */}
      <div className="space-y-3">
        {visibleDrivers.length > 0 ? (
          visibleDrivers.map((d, idx) => (
            <div key={idx} className={`p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-1.5 text-xs ${d.isImputed ? 'opacity-60' : ''}`}>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Badge variant="primary" size="sm">{d.modality === 'Clinical' ? '🩺 Lab' : d.modality === 'Wearable' ? '⌚ Wearable' : d.modality === 'Gut' ? '🧬 Gut' : d.modality}</Badge>
                  <strong className="text-xs text-[var(--text-main)]">{d.displayName}</strong>
                  {d.isImputed && <Badge variant="outline" size="sm">Imputed</Badge>}
                </div>
                <span className={`font-mono font-bold text-xs px-2 py-0.5 rounded-full ${d.impact === 'INCREASES RISK' ? 'text-[var(--danger)] bg-red-50 dark:bg-red-900/20' : 'text-[var(--success)] bg-green-50 dark:bg-green-900/20'}`}>
                  {d.shapDisplay} — {d.impact === 'INCREASES RISK' ? '⬆ Increases Risk' : '⬇ Lowers Risk'}
                </span>
              </div>

              <div className="flex justify-between text-[11px] text-[var(--text-muted)] font-mono">
                <span>Your value: <strong className="text-[var(--text-main)]">{d.value}</strong></span>
                <span>Influence strength: {d.pct}%</span>
              </div>

              <ProgressBar value={d.pct} max={100} variant={d.variant} />

              {/* Expandable plain-language explanation */}
              <button
                onClick={() => setExpandedIdx(expandedIdx === idx ? null : idx)}
                className="text-[11px] font-semibold text-[var(--primary)] hover:underline flex items-center gap-1 mt-1"
              >
                {expandedIdx === idx ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                {expandedIdx === idx ? 'Hide explanation' : 'What does this mean?'}
              </button>
              {expandedIdx === idx && (
                <div className="mt-1 p-2.5 rounded-lg bg-blue-50 dark:bg-blue-900/15 text-[11px] text-[var(--text-muted)] leading-relaxed animate-fade-in border border-blue-100 dark:border-blue-800">
                  💡 {d.explanation}
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="p-8 text-center space-y-2 border border-dashed border-[var(--border-subtle)] rounded-xl">
            <ShieldCheck className="w-8 h-8 text-[var(--text-muted)] mx-auto" />
            <h4 className="text-sm font-bold text-[var(--text-main)]">No Risk Factors Available Yet</h4>
            <p className="text-xs text-[var(--text-muted)]">
              {xaiData ? 'No SHAP attributions found in your XAI data. Try selecting a different disease target on the XAI Driver Analysis page first.' : 'Visit the XAI Driver Analysis page first to generate explainability data, then come back here to explore the results.'}
            </p>
          </div>
        )}
      </div>

      {/* Show More / Show Less Toggle */}
      {hasMore && (
        <div className="text-center pt-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAll(!showAll)}
            leftIcon={showAll ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          >
            {showAll ? `Show Less (Top 8)` : `Show All ${filteredDrivers.length} Factors`}
          </Button>
        </div>
      )}
    </Card>
  );
}

/** Generate a plain-language explanation for a SHAP driver */
function getPlainExplanation(featureName, value, shapValue) {
  const name = featureName.replace(/_/g, ' ').toLowerCase();
  const direction = (shapValue || 0) > 0 ? 'increased' : 'decreased';
  const impact = (shapValue || 0) > 0 ? 'higher' : 'lower';

  if (name.includes('glucose') || name.includes('hba1c')) {
    return `Your blood sugar measurement (${value ?? 'N/A'}) ${direction} your diabetes risk. ${(shapValue || 0) > 0 ? 'This value is above the healthy range, which suggests your body may be having difficulty managing blood sugar levels.' : 'This value is within a healthy range, which is a positive sign for your metabolic health.'}`;
  }
  if (name.includes('bmi') || name.includes('adiposity') || name.includes('waist')) {
    return `Your body composition measurement (${value ?? 'N/A'}) ${direction} your risk score. ${(shapValue || 0) > 0 ? 'A higher body mass index or waist measurement is associated with increased metabolic risk.' : 'Your measurement is in a healthy range, which helps protect against metabolic conditions.'}`;
  }
  if (name.includes('heart') || name.includes('resting') || name.includes('hrv')) {
    return `Your heart rate data (${value ?? 'N/A'}) ${direction} your risk. ${(shapValue || 0) > 0 ? 'This may indicate your cardiovascular system is under more stress than ideal.' : 'Your heart metrics suggest good cardiovascular fitness.'}`;
  }
  if (name.includes('step') || name.includes('activity') || name.includes('sedentary')) {
    return `Your daily activity level (${value ?? 'N/A'}) ${direction} your risk. ${(shapValue || 0) > 0 ? 'Lower physical activity is linked to higher metabolic risk. Try to increase daily movement.' : 'Staying active is one of the best ways to protect your health — keep it up!'}`;
  }
  if (name.includes('sleep')) {
    return `Your sleep data (${value ?? 'N/A'}) ${direction} your risk. ${(shapValue || 0) > 0 ? 'Poor or insufficient sleep can affect your metabolism, blood sugar, and weight management.' : 'Getting enough quality sleep supports healthy metabolism and recovery.'}`;
  }
  if (name.includes('akkermansia') || name.includes('faecalibacterium') || name.includes('bifidobacterium') || name.includes('lactobacillus') || name.includes('roseburia')) {
    return `This beneficial gut bacteria (abundance: ${value ?? 'N/A'}%) ${direction} your risk. ${(shapValue || 0) > 0 ? 'Lower levels of this bacteria may weaken your gut barrier and affect metabolism.' : 'Healthy levels of this bacteria support your gut lining and help regulate blood sugar.'}`;
  }
  if (name.includes('firmicutes') || name.includes('bacteroidetes') || name.includes('shannon') || name.includes('diversity')) {
    return `Your gut microbiome balance indicator (${value ?? 'N/A'}) ${direction} your risk. ${(shapValue || 0) > 0 ? 'An imbalanced gut microbiome can contribute to inflammation and metabolic issues.' : 'A balanced gut microbiome supports overall metabolic health.'}`;
  }
  if (name.includes('prevotella') || name.includes('clostridium') || name.includes('ruminococcus') || name.includes('blautia') || name.includes('bacteroides') || name.includes('eubacterium') || name.includes('coprococcus') || name.includes('alistipes') || name.includes('parabacteroides')) {
    return `This gut microorganism (abundance: ${value ?? 'N/A'}%) ${direction} your risk. Different gut bacteria play different roles in digestion, inflammation, and metabolic health.`;
  }
  if (name.includes('alt') || name.includes('ast') || name.includes('liver')) {
    return `Your liver enzyme level (${value ?? 'N/A'}) ${direction} your risk for liver-related conditions. ${(shapValue || 0) > 0 ? 'Elevated liver enzymes may indicate fatty liver or liver stress.' : 'Your liver enzymes are in a healthy range.'}`;
  }
  if (name.includes('triglyceride') || name.includes('hdl') || name.includes('ldl') || name.includes('cholesterol')) {
    return `Your blood fat measurement (${value ?? 'N/A'}) ${direction} your cardiovascular risk. ${(shapValue || 0) > 0 ? 'Abnormal cholesterol or triglyceride levels increase risk for heart disease and metabolic syndrome.' : 'Your blood fat levels are in a healthy range.'}`;
  }
  if (name.includes('blood') && name.includes('pressure') || name.includes('systolic') || name.includes('diastolic')) {
    return `Your blood pressure reading (${value ?? 'N/A'}) ${direction} your risk. ${(shapValue || 0) > 0 ? 'Higher blood pressure puts additional strain on your heart and blood vessels.' : 'Your blood pressure is well-controlled.'}`;
  }
  return `This health measurement "${featureName.replace(/_/g, ' ')}" with value ${value ?? 'N/A'} made your overall risk ${impact}. The AI model determined this factor had a ${Math.abs(shapValue || 0) > 0.05 ? 'significant' : 'minor'} influence on your results.`;
}
