import React from 'react';
import { Card, Badge, ProgressBar } from '../ui';
import { Target, CheckCircle2, Flame, Award } from 'lucide-react';

export default function GoalsCoach() {
  const goals = [
    { name: 'Daily Step Target', current: '8,500 steps', target: '10,000 steps', pct: 85, variant: 'primary' },
    { name: 'Sleep Target', current: '7.5 hours', target: '8.0 hours', pct: 93, variant: 'success' },
    { name: 'Target HbA1c Level', current: '5.8%', target: '<5.7%', pct: 92, variant: 'success' },
    { name: 'Blood Pressure Target', current: '118/78 mmHg', target: '<120/80', pct: 100, variant: 'success' },
    { name: 'BMI Target', current: '23.4 kg/m²', target: '18.5 - 24.9', pct: 100, variant: 'primary' },
  ];

  return (
    <Card isGlass={true} className="p-6 space-y-4 shadow-xl">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <Target className="w-5 h-5 text-[var(--primary)]" />
          <h3 className="text-base font-extrabold text-[var(--text-main)]">Personalized Health Goals</h3>
        </div>
        <Badge variant="primary" size="sm">4 of 5 On Track</Badge>
      </div>

      <div className="space-y-3.5">
        {goals.map((g, idx) => (
          <div key={idx} className="space-y-1 text-xs">
            <div className="flex justify-between font-semibold">
              <span className="text-[var(--text-main)]">{g.name}</span>
              <span className="font-mono text-[var(--text-muted)]">{g.current} (Goal: {g.target})</span>
            </div>
            <ProgressBar value={g.pct} max={100} variant={g.variant} />
          </div>
        ))}
      </div>
    </Card>
  );
}
