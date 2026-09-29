import React from 'react';
import { Card, Badge, ProgressBar } from '../ui';
import { Clock } from 'lucide-react';

export default function WorkloadPanel({ consultations = [] }) {
  const total = consultations.length || 1;
  const rawTotal = consultations.length;
  
  const pending = consultations.filter(c => ['REQUESTED', 'ASSIGNED', 'PENDING'].includes(c.status)).length;
  const accepted = consultations.filter(c => ['ACCEPTED', 'CONFIRMED', 'UPCOMING', 'IN_CONSULTATION', 'ACTIVE'].includes(c.status)).length;
  const inReview = accepted;
  const completed = consultations.filter(c => c.status === 'COMPLETED').length;

  const pctAssigned = rawTotal > 0 ? 100 : 0;
  const pctAccepted = rawTotal > 0 ? Math.round((accepted / rawTotal) * 100) : 0;
  const pctInReview = rawTotal > 0 ? Math.round((inReview / rawTotal) * 100) : 0;
  const pctCompleted = rawTotal > 0 ? Math.round((completed / rawTotal) * 100) : 0;

  const workloadMetrics = [
    { label: "Assigned Cases", count: rawTotal, max: rawTotal, pct: pctAssigned, variant: 'success' },
    { label: "Accepted for Review", count: accepted, max: rawTotal, pct: pctAccepted, variant: 'success' },
    { label: "In Review", count: inReview, max: rawTotal, pct: pctInReview, variant: 'primary' },
    { label: "Completed Sign-Offs", count: completed, max: rawTotal, pct: pctCompleted, variant: 'success' },
  ];

  return (
    <Card isGlass={true} className="p-5 space-y-4 shadow-sm border border-[var(--border-subtle)] rounded-2xl bg-[var(--bg-surface)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <Clock className="w-4 h-4 text-[var(--primary)]" />
          <h3 className="text-sm font-bold text-[var(--text-main)]">Clinical Workload & Progress</h3>
        </div>
        <Badge variant={pctCompleted === 100 && rawTotal > 0 ? 'success' : 'primary'} size="sm">
          {pctCompleted}% COMPLETE
        </Badge>
      </div>

      <div className="space-y-3.5">
        {workloadMetrics.map((wm, idx) => (
          <div key={idx} className="space-y-1 text-xs">
            <div className="flex justify-between font-semibold">
              <span className="text-[var(--text-main)] text-xs">{wm.label}</span>
              <span className="font-mono text-[11px] text-[var(--text-muted)]">
                {wm.count} / {wm.max} ({wm.pct}%)
              </span>
            </div>
            <ProgressBar value={wm.pct} max={100} variant={wm.variant} />
          </div>
        ))}
      </div>
    </Card>
  );
}
