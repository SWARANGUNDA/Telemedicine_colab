import React from 'react';
import { Card, Badge } from '../ui';
import { TrendingUp, ArrowRight, BarChart2 } from 'lucide-react';

export default function OutcomeTracking({ consultations = [], onOpenAnalytics }) {
  const total = consultations.length;

  const completed = consultations.filter(c => c.status === 'COMPLETED').length;
  const active = consultations.filter(c => ['ACCEPTED', 'CONFIRMED', 'UPCOMING', 'IN_CONSULTATION', 'ACTIVE'].includes(c.status)).length;
  const pending = consultations.filter(c => ['REQUESTED', 'ASSIGNED', 'PENDING'].includes(c.status)).length;
  const cancelled = consultations.filter(c => ['CANCELLED', 'REJECTED', 'NO_SHOW'].includes(c.status)).length;

  const getPct = (count) => total > 0 ? `${Math.round((count / total) * 100)}%` : '0%';

  const cohortOutcomes = [
    { category: 'Completed & Signed Off', count: completed, pct: getPct(completed), variant: 'success' },
    { category: 'Active In-Progress', count: active, pct: getPct(active), variant: 'primary' },
    { category: 'Pending Physician Review', count: pending, pct: getPct(pending), variant: 'warning' },
    { category: 'Cancelled / Declined', count: cancelled, pct: getPct(cancelled), variant: 'danger' },
  ];

  return (
    <Card isGlass={true} className="p-5 space-y-4 shadow-sm border border-[var(--border-subtle)] rounded-2xl bg-[var(--bg-surface)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <TrendingUp className="w-4 h-4 text-emerald-500" />
          <h3 className="text-sm font-bold text-[var(--text-main)]">Patient Outcome Tracking</h3>
        </div>
        <Badge variant="primary" size="sm">
          {total} Total Cases
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        {cohortOutcomes.map((co, idx) => (
          <div key={idx} className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-1">
            <div className="flex justify-between items-center">
              <span className="text-[11px] font-semibold text-[var(--text-main)] truncate">{co.category}</span>
              <Badge variant={co.variant} size="sm" className="!px-1.5 !py-0 text-[10px]">
                {co.pct}
              </Badge>
            </div>
            <div className="text-base font-extrabold font-mono text-[var(--text-main)]">
              {co.count} {co.count === 1 ? 'Patient' : 'Patients'}
            </div>
          </div>
        ))}
      </div>

      <div className="pt-1 text-right">
        <button
          onClick={onOpenAnalytics}
          className="text-xs font-bold text-[var(--primary)] hover:text-blue-700 hover:underline flex items-center justify-end gap-1 ml-auto cursor-pointer transition-all"
        >
          <span>View Detailed Analytics</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </Card>
  );
}
