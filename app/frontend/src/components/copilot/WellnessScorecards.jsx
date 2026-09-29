import React from 'react';
import { Card, Badge, CircularProgress } from '../ui';
import { Heart, Activity, Moon, Zap, Utensils, Dna } from 'lucide-react';

export default function WellnessScorecards({ predictionData }) {
  const dq = predictionData ? Math.round((predictionData.data_quality_score || 0.85) * 100) : null;
  const clinFeats = predictionData?.confirmed_features?.clinical || predictionData?.clinical_features || {};
  const wearFeats = predictionData?.confirmed_features?.wearable || predictionData?.wearable_features || {};

  const scorecards = predictionData ? [
    { title: 'Metabolic Health', score: dq, icon: Activity, trend: 'Evaluated', rec: clinFeats.HbA1c ? `HbA1c: ${clinFeats.HbA1c}%` : 'Assessment Active', variant: 'success' },
    { title: 'Cardiovascular Health', score: dq, icon: Heart, trend: 'Evaluated', rec: (clinFeats.Systolic_BP && clinFeats.Diastolic_BP) ? `BP ${clinFeats.Systolic_BP}/${clinFeats.Diastolic_BP} mmHg` : 'Assessment Active', variant: 'success' },
    { title: 'Wearable Telemetry', score: dq, icon: Zap, trend: 'Evaluated', rec: wearFeats.Resting_Heart_Rate ? `RHR ${wearFeats.Resting_Heart_Rate} bpm` : 'Assessment Active', variant: 'primary' },
  ] : [];

  return (
    <Card isGlass={true} className="p-6 space-y-4 shadow-xl border-t-4 border-t-[var(--secondary)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-[var(--secondary)]" />
          <h3 className="text-base font-extrabold text-[var(--text-main)]">Wellness Domain Scorecards</h3>
        </div>
        <Badge variant={predictionData ? 'secondary' : 'outline'} size="sm">
          {dq !== null ? `Data Quality ${dq}%` : 'NO ACTIVE ASSESSMENT'}
        </Badge>
      </div>

      {scorecards.length > 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
          {scorecards.map((sc, idx) => {
            const Icon = sc.icon;
            return (
              <div key={idx} className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-1 text-center">
                <div className="flex items-center justify-center gap-1.5 mb-1">
                  <Icon className="w-4 h-4 text-[var(--primary)]" />
                  <span className="font-bold text-[var(--text-main)] truncate">{sc.title}</span>
                </div>
                <div className="text-lg font-mono font-extrabold text-[var(--primary)]">{sc.score}%</div>
                <span className="text-[10px] text-[var(--text-muted)] block truncate">{sc.rec}</span>
              </div>
            );
          })}
        </div>
      ) : (
        <p className="text-xs text-[var(--text-muted)] text-center py-4">No wellness domain scorecards available. Complete your intake assessment to evaluate domains.</p>
      )}
    </Card>
  );
}
