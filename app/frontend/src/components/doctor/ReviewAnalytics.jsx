import React from 'react';
import { Card, Badge } from '../ui';
import { BarChart3 } from 'lucide-react';

export default function ReviewAnalytics({ consultations = [] }) {
  const total = consultations.length;
  const completed = consultations.filter(c => c.status === 'COMPLETED').length;
  const pending = consultations.filter(c => ['REQUESTED', 'ASSIGNED', 'PENDING'].includes(c.status)).length;
  const active = consultations.filter(c => ['ACCEPTED', 'CONFIRMED', 'UPCOMING', 'IN_CONSULTATION', 'ACTIVE'].includes(c.status)).length;

  const signOffPct = total > 0 ? Math.round((completed / total) * 100) : 0;
  const activePct = total > 0 ? Math.round((active / total) * 100) : 0;

  const stats = [
    { label: 'Total Assigned', value: String(total), sub: 'Assigned patient cohort' },
    { label: 'Completed Reviews', value: String(completed), sub: 'Signed off evaluations' },
    { label: 'Active Queue', value: String(active), sub: `${activePct}% active in-progress` },
    { label: 'Sign-Off Rate', value: `${signOffPct}%`, sub: 'Case resolution rate' },
  ];

  return (
    <Card isGlass={true} className="p-5 space-y-4 shadow-sm border border-[var(--border-subtle)] rounded-2xl bg-[var(--bg-surface)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-4 h-4 text-[var(--primary)]" />
          <h3 className="text-sm font-bold text-[var(--text-main)]">Review Performance</h3>
        </div>
        <Badge variant="success" size="sm">
          Live Cohort Sync
        </Badge>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        {stats.map((st, idx) => (
          <div key={idx} className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-1">
            <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">{st.label}</span>
            <div className="text-xl font-extrabold font-mono text-[var(--text-main)]">{st.value}</div>
            <p className="text-[10px] text-[var(--text-muted)] truncate">{st.sub}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
