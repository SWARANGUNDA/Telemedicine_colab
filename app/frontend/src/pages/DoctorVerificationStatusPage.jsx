import React from 'react';
import { CheckCircle, Clock, Shield, Lock, FileText, Stethoscope } from 'lucide-react';

export default function DoctorVerificationStatusPage({ user }) {
  const doctor = user?.doctor_profile || {};
  const status = doctor.verification_status || 'PENDING';

  const steps = [
    {
      id: 1,
      title: 'Doctor Account Registration',
      subtitle: 'Account & Professional Profile Created',
      status: 'completed',
      date: doctor.created_at ? new Date(doctor.created_at).toLocaleDateString() : 'Completed',
    },
    {
      id: 2,
      title: 'Admin Verification Audit',
      subtitle: 'System Administrator Review of License & Credentials',
      status: status === 'VERIFIED' ? 'completed' : status === 'UNDER_REVIEW' ? 'active' : 'pending',
      detail: `Current Account Status: ${status}`,
    },
    {
      id: 3,
      title: 'Credential Document Verification Workflow',
      subtitle: 'Medical License & Institution Verification (Level 4 Feature)',
      status: 'locked',
      detail: 'Level 4 Foundation Compatible',
    },
    {
      id: 4,
      title: 'Clinical Workspace & Patient Assignment Access',
      subtitle: 'Full Patient Clinical Data & AI Decision Support Activation (Level 5)',
      status: status === 'VERIFIED' ? 'active' : 'locked',
      detail: status === 'VERIFIED' ? 'Awaiting Patient Assignment (Level 5)' : 'Locked until verified',
    },
  ];

  return (
    <div style={{ padding: '32px', maxWidth: '900px', margin: '0 auto' }}>
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Shield size={28} color="var(--accent-cyan)" /> Doctor Credential Verification Status
        </h1>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '6px' }}>
          Verification lifecycle tracking for Dr. {doctor.full_name || user?.full_name || 'Doctor'} ({doctor.specialization || 'Medical Professional'})
        </p>
      </div>

      <div className="card" style={{ padding: '32px' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', position: 'relative' }}>
          {steps.map((s, idx) => (
            <div key={s.id} style={{ display: 'flex', gap: '20px', alignItems: 'flex-start' }}>
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                background: s.status === 'completed' ? 'rgba(16, 185, 129, 0.2)' : s.status === 'active' ? 'rgba(59, 130, 246, 0.2)' : 'rgba(255,255,255,0.05)',
                border: s.status === 'completed' ? '2px solid #10b981' : s.status === 'active' ? '2px solid #3b82f6' : '1px solid rgba(255,255,255,0.1)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: s.status === 'completed' ? '#10b981' : s.status === 'active' ? '#3b82f6' : '#64748b',
                fontWeight: 700,
                flexShrink: 0,
              }}>
                {s.status === 'completed' ? <CheckCircle size={20} /> : s.status === 'locked' ? <Lock size={18} /> : s.id}
              </div>

              <div style={{ flex: 1, paddingBottom: idx < steps.length - 1 ? '20px' : 0, borderBottom: idx < steps.length - 1 ? '1px solid rgba(255,255,255,0.06)' : 'none' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 600 }}>{s.title}</h3>
                  {s.date && <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>{s.date}</span>}
                </div>
                <p style={{ margin: '4px 0 6px', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>{s.subtitle}</p>
                {s.detail && (
                  <span style={{
                    display: 'inline-block',
                    padding: '2px 8px',
                    borderRadius: '6px',
                    background: 'rgba(255,255,255,0.04)',
                    color: '#cbd5e1',
                    fontSize: '0.75rem',
                    fontWeight: 500,
                  }}>
                    {s.detail}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
