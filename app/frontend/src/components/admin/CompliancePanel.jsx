import React from 'react';
import { Card, Badge, ProgressBar } from '../ui';
import { ShieldCheck, Lock, FileText, CheckCircle2 } from 'lucide-react';

export default function CompliancePanel() {
  const complianceItems = [
    { name: 'HIPAA Security Controls', pct: 100, status: 'COMPLIANT', variant: 'success' },
    { name: 'Physician Credential Verification', pct: 98, status: '98% VERIFIED', variant: 'primary' },
    { name: 'System Audit Trail Coverage', pct: 100, status: 'AUDITED', variant: 'success' },
    { name: 'Data Retention & Encryption at Rest', pct: 100, status: 'AES-256', variant: 'secondary' },
  ];

  return (
    <Card isGlass={true} className="p-6 space-y-4 shadow-xl border-t-4 border-t-[var(--success)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-5 h-5 text-[var(--success)]" />
          <h3 className="text-base font-extrabold text-[var(--text-main)]">Regulatory & HIPAA Compliance</h3>
        </div>
        <Badge variant="success" size="sm">100% Audit Score</Badge>
      </div>

      <div className="space-y-3">
        {complianceItems.map((c, idx) => (
          <div key={idx} className="space-y-1 text-xs">
            <div className="flex justify-between font-semibold">
              <span className="text-[var(--text-main)]">{c.name}</span>
              <Badge variant={c.variant} size="sm">{c.status}</Badge>
            </div>
            <ProgressBar value={c.pct} max={100} variant={c.variant} />
          </div>
        ))}
      </div>
    </Card>
  );
}
