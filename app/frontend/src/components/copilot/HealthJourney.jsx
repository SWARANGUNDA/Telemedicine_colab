import React from 'react';
import { Card, Badge } from '../ui';
import { Activity, FileText, CheckCircle2, Stethoscope, TrendingUp } from 'lucide-react';

export default function HealthJourney() {
  const milestones = [
    { title: 'Multimodal Intake Uploaded', date: 'Aug 1, 2026', desc: 'Clinical biochemistry PDF & wearable CSV submitted', icon: FileText, status: 'COMPLETED' },
    { title: 'Hierarchical Stacker AI Execution', date: 'Aug 1, 2026', desc: 'Ensemble risk evaluation (18.4% Low Risk)', icon: Activity, status: 'COMPLETED' },
    { title: 'Physician Review & Sign-off', date: 'Aug 2, 2026', desc: 'Dr. Marcus Vance reviewed and validated TreeSHAP drivers', icon: Stethoscope, status: 'COMPLETED' },
    { title: 'Teleconsultation Completed', date: 'Aug 3, 2026', desc: 'Reviewed 90-day glycemic trend & lifestyle protocol', icon: CheckCircle2, status: 'COMPLETED' },
    { title: 'Target Trajectory Reached', date: 'In Progress', desc: 'HbA1c optimization goal 5.8% achieved', icon: TrendingUp, status: 'ACTIVE' },
  ];

  return (
    <Card isGlass={true} className="p-6 space-y-4 shadow-xl">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-[var(--primary)]" />
          <h3 className="text-base font-extrabold text-[var(--text-main)]">Health Journey Timeline</h3>
        </div>
        <Badge variant="primary" size="sm">Phase 4 Active</Badge>
      </div>

      <div className="space-y-4 text-xs relative pl-4 border-l-2 border-l-[var(--border-subtle)] ml-2">
        {milestones.map((m, idx) => {
          const Icon = m.icon;
          const isDone = m.status === 'COMPLETED';
          return (
            <div key={idx} className="relative space-y-1">
              <div className={`absolute -left-[23px] top-0.5 w-4 h-4 rounded-full flex items-center justify-center ${
                isDone ? 'bg-[var(--success)] text-white' : 'bg-[var(--primary)] text-white animate-pulse'
              }`}>
                <Icon className="w-2.5 h-2.5" />
              </div>
              <div className="flex justify-between items-center">
                <strong className="text-xs text-[var(--text-main)]">{m.title}</strong>
                <span className="text-[10px] font-mono text-[var(--text-muted)]">{m.date}</span>
              </div>
              <p className="text-[11px] text-[var(--text-muted)]">{m.desc}</p>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
