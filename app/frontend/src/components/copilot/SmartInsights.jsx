import React from 'react';
import { Card, Badge } from '../ui';
import { Sparkles, TrendingUp, AlertCircle, HeartPulse, Calendar } from 'lucide-react';

export default function SmartInsights() {
  const insightsList = [
    {
      title: 'Glycemic Stability Improved',
      desc: 'HbA1c decreased from 6.1% to 5.8% over the past 90 days. TreeSHAP indicates reduced metabolic risk contribution.',
      category: 'Key Improvement',
      variant: 'success',
    },
    {
      title: 'Targeted Biomarker: Fasting Glucose',
      desc: 'Morning glucose (105 mg/dL) remains borderline. Maintain current low-glycemic dietary intake prior to next panel.',
      category: 'Targeted Action',
      variant: 'warning',
    },
    {
      title: 'Positive Wearable Telemetry Trend',
      desc: 'Deep sleep hours increased by +45 mins weekly. Heart Rate Variability (HRV RMSSD) improved to 42 ms.',
      category: 'Lifestyle Positive',
      variant: 'primary',
    },
    {
      title: 'Next Recommended Assessment',
      desc: 'Schedule next 90-day comprehensive laboratory panel by October 30, 2026 for continuous monitoring.',
      category: 'Schedule Reminder',
      variant: 'secondary',
    },
  ];

  return (
    <Card isGlass={true} className="p-6 space-y-4 shadow-xl border-t-4 border-t-[var(--accent)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-[var(--accent)]" />
          <h3 className="text-base font-extrabold text-[var(--text-main)]">Smart AI Health Insights</h3>
        </div>
        <Badge variant="accent" size="sm">Real-Time Copilot Analysis</Badge>
      </div>

      <div className="space-y-3 text-xs">
        {insightsList.map((ins, idx) => (
          <div key={idx} className="p-3.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-1">
            <div className="flex items-center justify-between">
              <strong className="text-xs text-[var(--text-main)]">{ins.title}</strong>
              <Badge variant={ins.variant} size="sm">{ins.category}</Badge>
            </div>
            <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">{ins.desc}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
