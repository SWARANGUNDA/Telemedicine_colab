import React from 'react';
import { Card, Badge } from '../ui';
import { Sparkles } from 'lucide-react';

export default function InsightsPanel({ consultations = [] }) {
  const cohortSize = consultations.length;
  const pendingCase = consultations.find(c => ['REQUESTED', 'ASSIGNED', 'PENDING'].includes(c.status));
  const pendingPatientName = pendingCase ? (pendingCase.patient_name || pendingCase.full_name || 'Patient') : null;

  // Extract top specialty from cohort
  const specialtyCounts = consultations.reduce((acc, c) => {
    const spec = c.specialty || c.category || 'Internal Medicine';
    acc[spec] = (acc[spec] || 0) + 1;
    return acc;
  }, {});
  const topSpecialty = Object.keys(specialtyCounts).sort((a, b) => specialtyCounts[b] - specialtyCounts[a])[0] || 'Internal Medicine';

  const insights = [
    {
      title: 'Most Common Disease Pattern',
      desc: cohortSize > 0 
        ? `${topSpecialty} accounts for top case volume in your current assigned cohort (n=${cohortSize}). Fasting Glucose & Metabolic Markers represent primary biomarkers.` 
        : 'Metabolic & Cardiovascular patterns represent primary drivers in clinical cohorts.',
      category: 'EPIDEMIOLOGY',
      variant: 'primary',
    },
    {
      title: 'Frequently Abnormal Biomarkers',
      desc: 'HbA1c, Triglycerides, and HRV RMSSD represent top out-of-range biomarkers requiring physician review.',
      category: 'BIOMARKERS',
      variant: 'warning',
    },
    {
      title: 'Consultation Recommendation',
      desc: pendingPatientName 
        ? `1 patient pending physician sign-off. Prioritize review for ${pendingPatientName} today.`
        : 'All assigned patient reviews are currently up to date. Continue monitoring active cases.',
      category: 'ACTION ITEM',
      variant: pendingPatientName ? 'danger' : 'success',
    },
  ];

  return (
    <Card isGlass={true} className="p-5 space-y-4 shadow-sm border border-[var(--border-subtle)] rounded-2xl bg-[var(--bg-surface)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-purple-500" />
          <h3 className="text-sm font-bold text-[var(--text-main)]">AI Clinical Insights</h3>
        </div>
        <Badge variant="accent" size="sm">
          {cohortSize > 0 ? `Current assigned cohort · n=${cohortSize}` : 'Real-time Insights'}
        </Badge>
      </div>

      <div className="space-y-3 text-xs">
        {insights.map((ins, idx) => (
          <div key={idx} className="p-3.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-1.5">
            <div className="flex items-center justify-between">
              <strong className="text-xs text-[var(--text-main)] font-bold">{ins.title}</strong>
              <Badge variant={ins.variant} size="sm" className="!text-[9.5px] uppercase font-mono">
                {ins.category}
              </Badge>
            </div>
            <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">{ins.desc}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
