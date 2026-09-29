import React, { useMemo } from 'react';
import { Activity, Watch, Dna, Layers, Info } from 'lucide-react';
import { Card, Badge } from './ui';

/**
 * ModalityContributionChart — Assessment Provenance Visualization
 * 
 * Shows the percentage contribution of each modality (Clinical, Wearable, Gut)
 * to the final Fusion prediction, calculated from SHAP attribution sums.
 */

const MODALITY_THEMES = {
  clinical: {
    label: 'Clinical Signal',
    icon: Activity,
    gradient: 'from-red-400 to-red-500',
    bg: 'bg-red-50',
    text: 'text-red-600',
    border: 'border-red-200',
    ring: 'ring-red-100',
  },
  wearable: {
    label: 'Wearable Signal',
    icon: Watch,
    gradient: 'from-blue-400 to-blue-500',
    bg: 'bg-blue-50',
    text: 'text-blue-600',
    border: 'border-blue-200',
    ring: 'ring-blue-100',
  },
  gut: {
    label: 'Gut Microbiome Signal',
    icon: Dna,
    gradient: 'from-emerald-400 to-emerald-500',
    bg: 'bg-emerald-50',
    text: 'text-emerald-600',
    border: 'border-emerald-200',
    ring: 'ring-emerald-100',
  },
};

export default function ModalityContributionChart({ attributions, selectedDisease }) {
  // Compute modality contribution percentages from SHAP attribution sums
  const contributions = useMemo(() => {
    if (!attributions) return [];

    const modSums = {};
    let totalAbsShap = 0;

    ['clinical', 'wearable', 'gut'].forEach(mod => {
      const modObj = attributions[mod] || {};
      const feats = modObj.all_features || modObj.top_risk_drivers || modObj.drivers || [];
      let absSum = 0;

      feats.forEach(f => {
        const shapVal = typeof f === 'number' ? f : (f.shap_attribution ?? f.shap_value ?? f.attribution ?? f.shap ?? 0);
        absSum += Math.abs(Number(shapVal) || 0);
      });

      modSums[mod] = absSum;
      totalAbsShap += absSum;
    });

    if (totalAbsShap === 0) return [];

    return Object.entries(modSums)
      .filter(([, sum]) => sum > 0)
      .map(([mod, sum]) => ({
        modality: mod,
        percentage: Math.round((sum / totalAbsShap) * 100),
        rawSum: sum,
        ...(MODALITY_THEMES[mod] || {}),
      }))
      .sort((a, b) => b.percentage - a.percentage);
  }, [attributions]);

  if (contributions.length === 0) return null;

  const dominant = contributions[0];

  return (
    <Card isGlass={true} className="p-6 space-y-5 border border-[var(--border-medium)]">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-purple-100 border border-purple-200 flex items-center justify-center">
            <Layers className="w-5 h-5 text-purple-600" />
          </div>
          <div>
            <h3 className="text-sm font-extrabold text-[var(--text-main)]">Assessment Provenance</h3>
            <p className="text-[10px] text-[var(--text-muted)] mt-0.5">
              Which data modality most influenced the {selectedDisease?.replace(/_/g, ' ')} prediction
            </p>
          </div>
        </div>
        <Badge variant="accent" size="sm">
          Dominant: {dominant.label}
        </Badge>
      </div>

      {/* Contribution Bars */}
      <div className="space-y-3">
        {contributions.map(contrib => {
          const Icon = contrib.icon;
          return (
            <div key={contrib.modality} className="space-y-1.5">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className={`w-7 h-7 rounded-lg ${contrib.bg} ${contrib.border} border flex items-center justify-center`}>
                    <Icon className={`w-4 h-4 ${contrib.text}`} />
                  </div>
                  <span className="text-xs font-bold text-[var(--text-main)]">{contrib.label}</span>
                </div>
                <span className={`text-sm font-extrabold tabular-nums ${contrib.text}`}>
                  {contrib.percentage}%
                </span>
              </div>

              {/* Bar */}
              <div className="w-full h-3 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className={`h-full rounded-full bg-gradient-to-r ${contrib.gradient} transition-all duration-700 ease-out`}
                  style={{ width: `${contrib.percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Interpretation Note */}
      <div className="flex items-start gap-2 p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
        <Info className="w-4 h-4 text-[var(--text-muted)] mt-0.5 shrink-0" />
        <p className="text-[10px] text-[var(--text-muted)] leading-relaxed">
          The Fusion Meta-Learner assigned <strong className="text-[var(--text-main)]">{dominant.percentage}%</strong> of its decision weight to the <strong className="text-[var(--text-main)]">{dominant.label}</strong> for predicting {selectedDisease?.replace(/_/g, ' ')}. 
          This means the AI relied most heavily on {dominant.modality === 'clinical' ? 'blood test biomarkers' : dominant.modality === 'wearable' ? 'wearable sensor metrics' : 'gut microbiome taxa data'} when making this specific prediction.
        </p>
      </div>
    </Card>
  );
}
