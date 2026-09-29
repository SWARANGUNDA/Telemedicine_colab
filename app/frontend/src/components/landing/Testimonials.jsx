import React from 'react';
import { Card, Badge } from '../ui';
import { Star, ShieldCheck, Stethoscope, UserCheck } from 'lucide-react';

export default function Testimonials() {
  const testimonials = [
    {
      name: 'Dr. Marcus Vance, MD',
      role: 'Chief of Endocrinology, Apex Medical Center',
      quote: 'TeleMed AI’s TreeSHAP drivers allow me to pinpoint the exact contribution of HbA1c vs HRV during patient consultations. It transforms black-box ML into actionable clinical decisions.',
      avatarText: 'MV',
      type: 'Physician Case Study',
      icon: Stethoscope,
    },
    {
      name: 'Elena Rostova',
      role: 'Patient, Early Prevention Program',
      quote: 'Uploading my lab PDF and wearable CSV took under two minutes. Seeing how my gut microbiome metrics connected with my fasting blood sugar was eye-opening.',
      avatarText: 'ER',
      type: 'Patient Case Study',
      icon: UserCheck,
    },
    {
      name: 'Prof. David Thorne, PhD',
      role: 'Director of Biomedical Informatics',
      quote: 'The hierarchical stacking ensemble architecture provides remarkable calibration across single and multi-modality patient data streams.',
      avatarText: 'DT',
      type: 'Researcher Case Study',
      icon: ShieldCheck,
    },
  ];

  return (
    <section className="py-24 bg-[var(--bg-primary)] border-b border-[var(--border-subtle)] space-y-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <Badge variant="warning" size="sm">CLINICAL & USER CASE STUDIES</Badge>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[var(--text-main)] tracking-tight">
            Trusted by Physicians & Researchers
          </h2>
          <p className="text-xs font-mono text-[var(--text-muted)] uppercase tracking-wider">
            (Clinical validation & physician case studies)
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {testimonials.map((t, idx) => {
            const Icon = t.icon;
            return (
              <Card key={idx} isGlass={true} className="p-8 space-y-6 flex flex-col justify-between hover:border-[var(--primary)] transition-all shadow-lg">
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1 text-amber-500">
                      {[...Array(5)].map((_, i) => (
                        <Star key={i} className="w-4 h-4 fill-amber-500" />
                      ))}
                    </div>
                    <Badge variant="secondary" size="sm">{t.type}</Badge>
                  </div>
                  <p className="text-sm text-[var(--text-main)] italic leading-relaxed">
                    "{t.quote}"
                  </p>
                </div>

                <div className="pt-4 border-t border-[var(--border-subtle)] flex items-center gap-3">
                  <div className="w-11 h-11 rounded-full bg-[var(--primary-light)] text-[var(--primary)] font-bold flex items-center justify-center text-sm shadow-sm">
                    {t.avatarText}
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-[var(--text-main)]">{t.name}</h4>
                    <p className="text-xs text-[var(--text-muted)]">{t.role}</p>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}
