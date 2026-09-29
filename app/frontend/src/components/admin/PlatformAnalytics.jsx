import React from 'react';
import { Card, Badge, ProgressBar } from '../ui';
import { BarChart3, TrendingUp, Users, Activity, FileText } from 'lucide-react';

export default function PlatformAnalytics() {
  const dailyAssessments = [
    { day: 'Mon', count: 112, pct: 75 },
    { day: 'Tue', count: 128, pct: 85 },
    { day: 'Wed', count: 142, pct: 95 },
    { day: 'Thu', count: 135, pct: 90 },
    { day: 'Fri', count: 150, pct: 100 },
    { day: 'Sat', count: 98,  pct: 65 },
    { day: 'Sun', count: 85,  pct: 56 },
  ];

  const modalityMetrics = [
    { name: 'Clinical Biochemistry PDF (C)', count: 142, pct: 100, variant: 'primary' },
    { name: 'Wearable Telemetry CSV (W)', count: 106, pct: 75, variant: 'secondary' },
    { name: 'Gut Microbiome Taxa (G)', count: 71, pct: 50, variant: 'accent' },
  ];

  return (
    <Card isGlass={true} className="p-6 space-y-6 shadow-xl border-t-4 border-t-[var(--primary)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-4">
        <div>
          <Badge variant="primary" size="sm">PLATFORM USAGE & THROUGHPUT</Badge>
          <h3 className="text-lg font-extrabold text-[var(--text-main)] mt-1">Daily Assessment Throughput & Modalities</h3>
        </div>
        <span className="text-xs font-mono text-[var(--text-muted)]">7-Day Total: 850 Assessments</span>
      </div>

      {/* Daily Assessment Bar Chart Placeholder */}
      <div className="space-y-3">
        <h4 className="text-xs font-mono font-bold text-[var(--text-muted)] uppercase">7-Day Assessment Volume</h4>
        <div className="grid grid-cols-7 gap-2 items-end h-28 pt-2">
          {dailyAssessments.map((d, idx) => (
            <div key={idx} className="flex flex-col items-center gap-1.5 h-full justify-end">
              <span className="text-[10px] font-mono font-bold text-[var(--primary)]">{d.count}</span>
              <div
                className="w-full bg-gradient-to-t from-[var(--primary)] to-[var(--accent)] rounded-t-lg transition-all"
                style={{ height: `${d.pct}%` }}
              />
              <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase font-semibold">{d.day}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Active Modality Breakdown */}
      <div className="pt-4 border-t border-[var(--border-subtle)] space-y-3">
        <h4 className="text-xs font-mono font-bold text-[var(--text-muted)] uppercase">Active Modality Intake Volume</h4>
        <div className="space-y-2.5">
          {modalityMetrics.map((m, idx) => (
            <div key={idx} className="space-y-1 text-xs">
              <div className="flex justify-between font-semibold">
                <span className="text-[var(--text-main)]">{m.name}</span>
                <span className="font-mono text-[var(--text-muted)]">{m.count} intakes today ({m.pct}%)</span>
              </div>
              <ProgressBar value={m.pct} max={100} variant={m.variant} />
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
}
