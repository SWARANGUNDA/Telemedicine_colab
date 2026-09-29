import React from 'react';
import { Card, Badge } from '../ui';
import { AlertTriangle, ShieldCheck, Clock, Eye, AlertCircle } from 'lucide-react';

export default function ClinicalAlerts({ consultations = [], onSelectConsultation }) {
  // Extract real clinical alerts from doctor's assigned consultations with high urgency or high risk
  const alertsList = (consultations || []).filter(c => {
    const isHighUrgency = c.urgency === 'HIGH' || c.urgency === 'URGENT';
    const outcomes = c.prediction_snapshot?.disease_outcomes || {};
    const hasHighRiskOutcome = Object.values(outcomes).some(o => o.risk_level === 'HIGH');
    return (isHighUrgency || hasHighRiskOutcome) && !['COMPLETED', 'CANCELLED'].includes(c.status);
  }).map((c, idx) => {
    const outcomes = c.prediction_snapshot?.disease_outcomes || {};
    const highRiskDiseases = Object.entries(outcomes)
      .filter(([_, o]) => o.risk_level === 'HIGH')
      .map(([k, _]) => k.replace(/_/g, ' '));

    const patientLabel = c.patient_name || c.patient_full_name || `Patient (${c.user_id ? c.user_id.slice(-6) : c.consultation_id ? c.consultation_id.slice(-6) : 'ID'})`;

    const title = highRiskDiseases.length > 0 
      ? `High Risk Escalation: ${highRiskDiseases.join(', ')}`
      : `High Priority Consultation Request (${c.specialization || 'General'})`;

    const priority = c.urgency === 'URGENT' ? 'CRITICAL' : 'HIGH';

    return {
      id: c.consultation_id || `ALT-${idx}`,
      title,
      patient: patientLabel,
      time: c.created_at ? new Date(c.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Recently',
      priority,
      variant: priority === 'CRITICAL' ? 'danger' : 'warning',
      consultation: c
    };
  });

  return (
    <Card isGlass={true} className={`p-6 space-y-4 shadow-xl border-l-4 ${alertsList.length > 0 ? 'border-l-[var(--danger)]' : 'border-l-[var(--success)]'}`}>
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          {alertsList.length > 0 ? (
            <AlertTriangle className="w-5 h-5 text-[var(--danger)]" />
          ) : (
            <ShieldCheck className="w-5 h-5 text-[var(--success)]" />
          )}
          <h3 className="text-base font-extrabold text-[var(--text-main)]">Clinical Alerts & Warnings</h3>
        </div>
        <Badge variant={alertsList.length > 0 ? 'danger' : 'success'} size="sm">
          {alertsList.length > 0 ? `${alertsList.length} Active Alerts` : 'Nominal Baseline'}
        </Badge>
      </div>

      {alertsList.length === 0 ? (
        <div className="py-6 text-center space-y-2">
          <div className="w-10 h-10 rounded-full bg-[var(--success)]/10 text-[var(--success)] flex items-center justify-center mx-auto mb-1">
            <ShieldCheck className="w-5 h-5" />
          </div>
          <h4 className="text-xs font-bold text-[var(--text-main)]">No active clinical alerts</h4>
          <p className="text-[11px] text-[var(--text-muted)] max-w-xs mx-auto">
            All active patient consultations are operating within nominal baseline parameters.
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {alertsList.map((a) => (
            <div 
              key={a.id} 
              className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-1 text-xs hover:border-[var(--primary)] transition-colors cursor-pointer"
              onClick={() => onSelectConsultation && onSelectConsultation(a.consultation)}
            >
              <div className="flex items-center justify-between">
                <strong className="text-xs text-[var(--text-main)]">{a.title}</strong>
                <Badge variant={a.variant} size="sm">{a.priority}</Badge>
              </div>
              <p className="text-[11px] text-[var(--text-muted)]">{a.patient} • {a.time}</p>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
