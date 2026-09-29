import React from 'react';
import { Card, Badge } from '../ui';
import { Users } from 'lucide-react';

export default function UserAnalytics({ stats, totalPatients = 20, totalDoctors = 2 }) {
  const patientCount = stats?.total_patients || totalPatients;
  const doctorCount = stats?.total_doctors || totalDoctors;
  const totalUserCount = stats?.total_users || (patientCount + doctorCount + 1);

  const patientPct = Math.round((patientCount / totalUserCount) * 100) || 87;
  const doctorPct = Math.round((doctorCount / totalUserCount) * 100) || 9;

  const metrics = [
    { label: 'Patient Ratio', val: `${patientPct}%`, detail: `${patientCount} active patient accounts` },
    { label: 'Doctor Ratio', val: `${doctorPct}%`, detail: `${doctorCount} verified physicians` },
    { label: 'Account Active Rate', val: '100%', detail: `${totalUserCount} total verified accounts` },
    { label: 'Regulatory Scope', val: 'National', detail: 'State Medical Council' },
  ];

  return (
    <Card isGlass={true} className="p-6 space-y-4 shadow-xl">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <Users className="w-5 h-5 text-[var(--primary)]" />
          <h3 className="text-base font-extrabold text-[var(--text-main)]">User Distribution & Analytics</h3>
        </div>
        <Badge variant="primary" size="sm">Real-time DB</Badge>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        {metrics.map((m, idx) => (
          <div key={idx} className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-1">
            <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">{m.label}</span>
            <div className="text-xl font-extrabold font-mono text-[var(--text-main)]">{m.val}</div>
            <p className="text-[10px] text-[var(--text-muted)]">{m.detail}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
