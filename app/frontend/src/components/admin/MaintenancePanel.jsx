import React from 'react';
import { Card, Badge } from '../ui';
import { HardDrive, Server, RefreshCw, Shield } from 'lucide-react';

export default function MaintenancePanel() {
  const maintenanceStatus = [
    { label: 'Database Backup Status', val: 'COMPLETED (04:00 AM)', status: 'HEALTHY' },
    { label: 'Storage Utilization (S3)', val: '42.8 GB / 500 GB (8.5%)', status: 'HEALTHY' },
    { label: 'System Clean-up Schedule', val: 'Every Sunday 02:00 AM', status: 'SCHEDULED' },
    { label: 'TeleMed AI Build Version', val: 'v4.2.0-STABLE', status: 'RELEASE' },
  ];

  return (
    <Card isGlass={true} className="p-6 space-y-4 shadow-xl">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <HardDrive className="w-5 h-5 text-[var(--secondary)]" />
          <h3 className="text-base font-extrabold text-[var(--text-main)] font-mono">Maintenance & Infrastructure Status</h3>
        </div>
        <Badge variant="secondary" size="sm">Read-Only Control</Badge>
      </div>

      <div className="space-y-3 text-xs">
        {maintenanceStatus.map((m, idx) => (
          <div key={idx} className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] flex items-center justify-between">
            <div>
              <strong className="text-xs text-[var(--text-main)] block">{m.label}</strong>
              <span className="text-[11px] font-mono text-[var(--text-muted)]">{m.val}</span>
            </div>
            <Badge variant="secondary" size="sm">{m.status}</Badge>
          </div>
        ))}
      </div>
    </Card>
  );
}
