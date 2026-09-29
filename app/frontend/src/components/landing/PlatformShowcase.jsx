import React from 'react';
import { Card, Badge, ProgressBar, Table } from '../ui';
import { FileText, Watch, Dna, Brain, Stethoscope, ShieldCheck, CheckCircle2 } from 'lucide-react';

export default function PlatformShowcase() {
  const showcaseItems = [
    {
      id: 'clinical',
      title: 'Clinical Analysis & OCR Extraction',
      subtitle: 'Automated extraction of 22 canonical blood biomarkers from unstructured diagnostic PDFs.',
      points: [
        'Hybrid Tesseract OCR parses lab reports automatically',
        'Normalizes aliased laboratory names into canonical variables',
        'Calculates missing biomarker estimations via clinical models',
      ],
      icon: FileText,
      badge: 'Clinical Modality',
      preview: (
        <Card isGlass={true} className="p-5 space-y-3 border-l-4 border-l-[var(--primary)]">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-[var(--text-main)]">Extracted Laboratory Values</span>
            <Badge variant="success" size="sm">22 Canonical Variables</Badge>
          </div>
          <div className="space-y-2 text-xs">
            <div className="p-2 rounded bg-[var(--bg-primary)] flex justify-between">
              <span>HbA1c (Glycated Hemoglobin)</span>
              <strong className="text-[var(--danger)]">7.2 % (Abnormal)</strong>
            </div>
            <div className="p-2 rounded bg-[var(--bg-primary)] flex justify-between">
              <span>Fasting Plasma Glucose</span>
              <strong className="text-[var(--danger)]">138 mg/dL (Abnormal)</strong>
            </div>
            <div className="p-2 rounded bg-[var(--bg-primary)] flex justify-between">
              <span>Serum Creatinine</span>
              <strong className="text-[var(--success)]">0.95 mg/dL (Normal)</strong>
            </div>
          </div>
        </Card>
      ),
    },
    {
      id: 'wearable',
      title: 'Wearable Sensor Telemetry',
      subtitle: '15-dimensional physiological time-series processing for continuous cardiac & sleep metrics.',
      points: [
        'Resting Heart Rate (RHR) & Heart Rate Variability (HRV)',
        'Sleep Efficiency & Circadian Fragmentation Index',
        'Active Energy Expenditure & Step Count Density',
      ],
      icon: Watch,
      badge: 'Wearable Sensor Modality',
      preview: (
        <Card isGlass={true} className="p-5 space-y-3 border-l-4 border-l-[var(--secondary)]">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-[var(--text-main)]">Continuous Sensor Telemetry</span>
            <Badge variant="secondary" size="sm">15-D Time Series</Badge>
          </div>
          <div className="space-y-3 text-xs">
            <div>
              <div className="flex justify-between mb-1">
                <span>Resting Heart Rate (RHR)</span>
                <span className="font-mono text-[var(--warning)]">78 bpm</span>
              </div>
              <ProgressBar value={78} max={100} variant="warning" />
            </div>
            <div>
              <div className="flex justify-between mb-1">
                <span>Heart Rate Variability (HRV RMSSD)</span>
                <span className="font-mono text-[var(--danger)]">28 ms</span>
              </div>
              <ProgressBar value={28} max={100} variant="danger" />
            </div>
          </div>
        </Card>
      ),
    },
    {
      id: 'microbiome',
      title: 'Gut Microbiome Intelligence',
      subtitle: '20 microbial taxa abundances and alpha diversity profiling for metabolic inflammation.',
      points: [
        'Firmicutes/Bacteroidetes ratio calculation',
        'Shannon Alpha Diversity quantification',
        'Short-chain fatty acid (SCFA) producer tracking',
      ],
      icon: Dna,
      badge: 'Gut Modality',
      preview: (
        <Card isGlass={true} className="p-5 space-y-3 border-l-4 border-l-[var(--accent)]">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-[var(--text-main)]">Microbial Taxa Abundances</span>
            <Badge variant="accent" size="sm">F/B Ratio: 2.85</Badge>
          </div>
          <div className="space-y-2 text-xs">
            <div className="p-2 rounded bg-[var(--bg-primary)] flex justify-between">
              <span>Faecalibacterium prausnitzii</span>
              <strong className="text-[var(--danger)]">1.2% (Low SCFA)</strong>
            </div>
            <div className="p-2 rounded bg-[var(--bg-primary)] flex justify-between">
              <span>Bacteroides vulgatus</span>
              <strong className="text-[var(--warning)]">14.8% (Elevated)</strong>
            </div>
          </div>
        </Card>
      ),
    },
    {
      id: 'xai',
      title: 'TreeSHAP Explainable AI',
      subtitle: 'Game-theoretic local feature attributions quantifying exact risk drivers.',
      points: [
        'Calculates exact numerical risk contribution per biomarker',
        'Differentiates risk-increasing vs risk-lowering factors',
        'Provides transparent clinical rationale for every risk score',
      ],
      icon: Brain,
      badge: 'Transparent XAI',
      preview: (
        <Card isGlass={true} className="p-5 space-y-3 border-l-4 border-l-[var(--danger)]">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-[var(--text-main)]">TreeSHAP Feature Attributions</span>
            <Badge variant="danger" size="sm">High Risk (+0.38 Total)</Badge>
          </div>
          <div className="space-y-2 text-xs">
            <div className="flex justify-between items-center p-2 rounded bg-[var(--bg-primary)]">
              <span>HbA1c (+0.18)</span>
              <Badge variant="danger" size="sm">+ Risk</Badge>
            </div>
            <div className="flex justify-between items-center p-2 rounded bg-[var(--bg-primary)]">
              <span>HRV RMSSD (+0.12)</span>
              <Badge variant="danger" size="sm">+ Risk</Badge>
            </div>
            <div className="flex justify-between items-center p-2 rounded bg-[var(--bg-primary)]">
              <span>F. prausnitzii (+0.08)</span>
              <Badge variant="danger" size="sm">+ Risk</Badge>
            </div>
          </div>
        </Card>
      ),
    },
    {
      id: 'doctor',
      title: 'Physician Consultation Workspace',
      subtitle: 'Dedicated 3-panel workspace for verified doctors to author diagnostic notes.',
      points: [
        'Real-time prediction & TreeSHAP driver inspection',
        'Structured clinical note authoring & prescription issuing',
        'Audit-logged doctor verification badge & finalization',
      ],
      icon: Stethoscope,
      badge: 'Physician Portal',
      preview: (
        <Card isGlass={true} className="p-5 space-y-3 border-l-4 border-l-[var(--success)]">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-[var(--text-main)]">Doctor Consultation Active</span>
            <Badge variant="success" size="sm">Verified MD</Badge>
          </div>
          <div className="p-3 rounded bg-[var(--bg-primary)] text-xs italic space-y-1">
            <p className="font-semibold text-[var(--text-main)]">Physician Notes:</p>
            <p className="text-[var(--text-muted)]">"Patient exhibits glycemic dysregulation exacerbated by low HRV. Recommend dietary SCFA optimization."</p>
          </div>
        </Card>
      ),
    },
    {
      id: 'reports',
      title: 'Printable Clinical Reports & RAG',
      subtitle: 'Hospital-grade PDF summaries paired with ChromaDB vector RAG medical guidelines.',
      points: [
        'Print-optimized layout with QR code report verification',
        'Retrieval-Augmented Generation (RAG) recommendations',
        'Biomarker abnormality flagging against standard reference ranges',
      ],
      icon: ShieldCheck,
      badge: 'Printable PDF',
      preview: (
        <Card isGlass={true} className="p-5 space-y-3 border-l-4 border-l-[var(--primary)]">
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-[var(--text-main)]">Medical RAG Recommendation</span>
            <Badge variant="primary" size="sm">ADA 2026 Guidelines</Badge>
          </div>
          <div className="p-3 rounded bg-[var(--bg-primary)] text-xs space-y-1">
            <p className="font-bold text-[var(--primary)]">Clinical Action Plan:</p>
            <p className="text-[var(--text-muted)]">Initiate lifestyle modification with continuous glucose monitoring. Follow-up HbA1c in 90 days.</p>
          </div>
        </Card>
      ),
    },
  ];

  return (
    <section className="py-24 bg-[var(--bg-primary)] border-b border-[var(--border-subtle)] space-y-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-20">
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <Badge variant="primary" size="sm">PLATFORM SHOWCASE</Badge>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[var(--text-main)] tracking-tight">
            Complete Multimodal Intelligence System
          </h2>
          <p className="text-base text-[var(--text-muted)] font-normal">
            Deep dive into the 6 specialized layers powering our clinical decision platform.
          </p>
        </div>

        {showcaseItems.map((item, idx) => {
          const isEven = idx % 2 === 0;
          const Icon = item.icon;

          return (
            <div
              key={item.id}
              className={`grid grid-cols-1 lg:grid-cols-12 gap-12 items-center ${
                isEven ? '' : 'lg:flex-row-reverse'
              }`}
            >
              {/* Text Column */}
              <div className={`lg:col-span-6 space-y-5 ${isEven ? '' : 'lg:order-2'}`}>
                <div className="inline-flex items-center gap-2">
                  <div className="p-2.5 rounded-xl bg-[var(--primary-light)] text-[var(--primary)]">
                    <Icon className="w-5 h-5" />
                  </div>
                  <Badge variant="secondary" size="sm">{item.badge}</Badge>
                </div>

                <h3 className="text-2xl sm:text-3xl font-extrabold text-[var(--text-main)] tracking-tight">
                  {item.title}
                </h3>

                <p className="text-sm sm:text-base text-[var(--text-muted)] leading-relaxed">
                  {item.subtitle}
                </p>

                <ul className="space-y-2.5 text-xs sm:text-sm text-[var(--text-main)]">
                  {item.points.map((pt, pIdx) => (
                    <li key={pIdx} className="flex items-center gap-2.5">
                      <CheckCircle2 className="w-4 h-4 text-[var(--success)] shrink-0" />
                      <span>{pt}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* UI Preview Card Column */}
              <div className={`lg:col-span-6 ${isEven ? '' : 'lg:order-1'}`}>
                {item.preview}
              </div>
            </div>
          );
        })}
      </div>
    </section>
  );
}
