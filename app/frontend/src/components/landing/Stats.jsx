import React from 'react';
import { Users, Stethoscope, FileText, CheckCircle2, ShieldCheck } from 'lucide-react';
import { Card } from '../ui';

export default function Stats() {
  const statItems = [
    {
      label: 'Active Patients',
      value: '1,240+',
      detail: 'Monitored across metabolic programs',
      icon: Users,
      color: 'text-[var(--primary)]',
    },
    {
      label: 'Verified Physicians',
      value: '48+',
      detail: 'Active consultation practitioners',
      icon: Stethoscope,
      color: 'text-[var(--secondary)]',
    },
    {
      label: 'Risk Assessments',
      value: '10,000+',
      detail: 'Completed multimodal predictions',
      icon: FileText,
      color: 'text-[var(--accent)]',
    },
    {
      label: 'Prediction Accuracy',
      value: '95.0%',
      detail: 'Platt-calibrated stacking score',
      icon: CheckCircle2,
      color: 'text-[var(--success)]',
    },
    {
      label: 'Platform Uptime',
      value: '99.98%',
      detail: 'High-availability microservices',
      icon: ShieldCheck,
      color: 'text-amber-500',
    },
  ];

  return (
    <section className="py-16 bg-[var(--bg-surface)] border-y border-[var(--border-subtle)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-2 md:grid-cols-5 gap-6 text-center">
          {statItems.map((st, idx) => {
            const Icon = st.icon;
            return (
              <div key={idx} className="space-y-2 p-5 rounded-2xl hover:bg-[var(--bg-primary)] transition-all hover:scale-105 duration-200">
                <Icon className={`w-7 h-7 mx-auto ${st.color}`} />
                <div className="text-3xl font-extrabold font-mono text-[var(--text-main)] tracking-tight">{st.value}</div>
                <div className="text-xs font-bold text-[var(--text-main)] uppercase tracking-wider">{st.label}</div>
                <p className="text-[11px] text-[var(--text-muted)] font-medium leading-tight">{st.detail}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
