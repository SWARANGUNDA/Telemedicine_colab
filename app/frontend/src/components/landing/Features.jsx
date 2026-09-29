import React from 'react';
import { FileText, Watch, Dna, Brain, ShieldCheck, Stethoscope } from 'lucide-react';
import { Card, Badge } from '../ui';

export default function Features() {
  const featureList = [
    {
      title: 'Clinical Intelligence',
      desc: 'Automated OCR extraction and canonical mapping for 22 vital blood biomarkers including HbA1c, Fasting Glucose, Lipid Profile, and Renal markers.',
      icon: FileText,
      badge: 'Clinical Modality',
      variant: 'primary'
    },
    {
      title: 'Wearable Analytics',
      desc: '15-dimensional physiological sensor analysis tracking Resting Heart Rate, Heart Rate Variability (HRV), Sleep Efficiency, and Active Energy Expenditure.',
      icon: Watch,
      badge: 'Wearable Modality',
      variant: 'secondary'
    },
    {
      title: 'Gut Microbiome Analysis',
      desc: '20 microbial taxa sequencing evaluation quantifying Firmicutes/Bacteroidetes ratio, Shannon Alpha Diversity, and short-chain fatty acid producers.',
      icon: Dna,
      badge: 'Gut Modality',
      variant: 'accent'
    },
    {
      title: 'Explainable AI (TreeSHAP)',
      desc: 'Mathematically rigorous TreeSHAP feature attributions detailing exact numerical risk contributions and directional influence for every biomarker.',
      icon: Brain,
      badge: 'Transparent XAI',
      variant: 'warning'
    },
    {
      title: 'Physician Reports',
      desc: 'Printable hospital-grade clinical summary reports complete with patient history, biomarker abnormality flags, and Medical RAG recommendations.',
      icon: ShieldCheck,
      badge: 'Printable PDF',
      variant: 'success'
    },
    {
      title: 'Doctor Collaboration',
      desc: 'Dedicated 3-panel consultation workspace enabling verified physicians to review predictions, author diagnostic notes, and issue digital prescriptions.',
      icon: Stethoscope,
      badge: 'Physician Portal',
      variant: 'primary'
    }
  ];

  return (
    <section className="py-20 bg-[var(--bg-surface)] border-b border-[var(--border-subtle)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <Badge variant="secondary" size="sm">CORE PLATFORM CAPABILITIES</Badge>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[var(--text-main)] tracking-tight">
            Comprehensive Multimodal Architecture
          </h2>
          <p className="text-base text-[var(--text-muted)] font-normal">
            Designed for high precision across early metabolic syndrome and gut-microbiome risk detection.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {featureList.map((f, idx) => {
            const Icon = f.icon;
            return (
              <Card key={idx} isGlass={true} className="p-6 space-y-4 hover:-translate-y-1 transition-all duration-200">
                <div className="flex items-center justify-between">
                  <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-[var(--primary)]">
                    <Icon className="w-6 h-6" />
                  </div>
                  <Badge variant={f.variant} size="sm">{f.badge}</Badge>
                </div>
                <h3 className="text-lg font-bold text-[var(--text-main)]">{f.title}</h3>
                <p className="text-sm text-[var(--text-muted)] leading-relaxed">{f.desc}</p>
              </Card>
            );
          })}
        </div>
      </div>
    </section>
  );
}
