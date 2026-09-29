import React from 'react';
import { Card, Badge } from '../ui';
import { ShieldCheck, Stethoscope, Brain, Sparkles, Layers, Lock } from 'lucide-react';

export default function TrustSection() {
  const trustItems = [
    {
      title: 'AI Clinical Decision Support',
      desc: 'Calibrated stacking ensemble models assist physicians with probabilistic disease risk stratification.',
      icon: Stethoscope,
      color: 'text-blue-500',
    },
    {
      title: 'Explainable Predictions',
      desc: 'Game-theoretic TreeSHAP feature attributions outline exact biomarker contributions.',
      icon: Brain,
      color: 'text-purple-500',
    },
    {
      title: 'HIPAA Ready Architecture',
      desc: 'Zero-retention temporary RAM ingestion & AES-256 encrypted database persistence.',
      icon: ShieldCheck,
      color: 'text-emerald-500',
    },
    {
      title: 'Research-Driven Calibration',
      desc: 'Validated against multi-modal clinical biochemistry, wearable sensor, and gut microbiome data.',
      icon: Sparkles,
      color: 'text-amber-500',
    },
    {
      title: 'Multimodal Intelligence',
      desc: 'Supports 22 clinical variables, 15 wearable telemetry metrics, and 20 microbial taxa.',
      icon: Layers,
      color: 'text-teal-500',
    },
    {
      title: 'Fast Secure Analysis',
      desc: 'Sub-35 millisecond end-to-end inference and instant printable PDF report generation.',
      icon: Lock,
      color: 'text-rose-500',
    },
  ];

  return (
    <section className="py-16 bg-[var(--bg-surface)] border-b border-[var(--border-subtle)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <Badge variant="success" size="sm">ENTERPRISE TRUST & COMPLIANCE</Badge>
          <h2 className="text-3xl font-extrabold text-[var(--text-main)] tracking-tight">
            Built for Clinical Security & Transparency
          </h2>
          <p className="text-sm text-[var(--text-muted)]">
            Architected to adhere to international medical AI reliability and patient data protection standards.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {trustItems.map((item, idx) => {
            const Icon = item.icon;
            return (
              <Card key={idx} isGlass={true} className="p-6 space-y-3 hover:border-[var(--primary)] transition-all">
                <div className="flex items-center gap-3">
                  <div className={`p-2.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] ${item.color}`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <h3 className="text-base font-bold text-[var(--text-main)]">{item.title}</h3>
                </div>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">{item.desc}</p>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}
