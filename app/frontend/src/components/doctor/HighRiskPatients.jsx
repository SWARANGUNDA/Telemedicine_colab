import React from 'react';
import { Card, Badge, Button } from '../ui';
import { ShieldCheck, ShieldAlert, Eye, MessageSquare } from 'lucide-react';

export default function HighRiskPatients({ consultations = [], onReview, onMessage }) {
  // Filter assigned cases with high urgency or high risk
  const highRiskCases = (consultations || []).filter(c => {
    const isHighUrgency = c.urgency === 'HIGH' || c.urgency === 'URGENT';
    const outcomes = c.prediction_snapshot?.disease_outcomes || {};
    const hasHighRiskOutcome = Object.values(outcomes).some(o => o.risk_level === 'HIGH');
    return (isHighUrgency || hasHighRiskOutcome) && !['COMPLETED', 'CANCELLED'].includes(c.status);
  });

  if (!highRiskCases.length) {
    return (
      <Card isGlass={true} className="p-5 space-y-4 shadow-sm border border-[var(--border-subtle)] rounded-2xl bg-[var(--bg-surface)] flex flex-col justify-between">
        <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
            <h3 className="text-sm font-bold text-[var(--text-main)]">High-Risk Patient Monitor</h3>
          </div>
          <Badge variant="success" size="sm">● PENDING</Badge>
        </div>

        <div className="py-8 text-center space-y-2 flex flex-col items-center justify-center">
          <div className="w-12 h-12 rounded-full bg-emerald-500/10 flex items-center justify-center text-emerald-500 mb-1">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <h4 className="text-sm font-extrabold text-[var(--text-main)]">No high-risk patients pending</h4>
          <p className="text-xs text-[var(--text-muted)] max-w-xs">
            All assigned patients are stable or completed.
          </p>
        </div>
      </Card>
    );
  }

  return (
    <Card isGlass={true} className="p-5 space-y-4 shadow-sm border border-rose-500/20 rounded-2xl bg-[var(--bg-surface)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <ShieldAlert className="w-4 h-4 text-rose-500" />
          <h3 className="text-sm font-bold text-[var(--text-main)]">High-Risk Patient Monitor</h3>
        </div>
        <Badge variant="danger" size="sm">{highRiskCases.length} ACTION REQUIRED</Badge>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-[var(--border-subtle)] text-[var(--text-muted)] font-mono text-[10px] uppercase">
              <th className="py-2 px-2">Patient</th>
              <th className="py-2 px-2">ID</th>
              <th className="py-2 px-2">Specialty</th>
              <th className="py-2 px-2">Urgency</th>
              <th className="py-2 px-2 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-subtle)]">
            {highRiskCases.map((c) => (
              <tr key={c.consultation_id} className="hover:bg-[var(--bg-primary)] transition-colors">
                <td className="py-2.5 px-2 font-bold text-[var(--text-main)]">{c.patient_name || 'Patient'}</td>
                <td className="py-2.5 px-2 font-mono text-[11px] text-[var(--primary)]">{c.consultation_id}</td>
                <td className="py-2.5 px-2 text-[var(--text-muted)]">{c.specialty || c.category || 'General'}</td>
                <td className="py-2.5 px-2">
                  <Badge variant="danger" size="sm">{c.urgency || 'HIGH'}</Badge>
                </td>
                <td className="py-2.5 px-2 text-right">
                  <Button variant="primary" size="sm" className="!px-2 !py-1 text-xs" onClick={() => onReview ? onReview(c) : null}>
                    Review
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
