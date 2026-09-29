import React, { useState } from 'react';
import { UploadCloud, Layers, Sliders, Activity, Brain, FileText, Database, ArrowRight, CheckCircle2 } from 'lucide-react';
import { Card, Badge, Button } from '../ui';

export default function Workflow() {
  const [activeStepIndex, setActiveStepIndex] = useState(0);

  const timelineSteps = [
    {
      id: 'upload',
      num: '01',
      title: 'Upload & OCR',
      short: 'Upload PDF',
      desc: 'Drag-and-drop unstructured lab report PDFs. Hybrid Tesseract OCR extracts raw table values automatically.',
      icon: UploadCloud,
      badge: 'Data Ingestion',
      detail: 'Supports PDF reports from Quest Diagnostics, LabCorp, and major hospital EHR systems.',
    },
    {
      id: 'extraction',
      num: '02',
      title: 'Canonical Extraction',
      short: 'Biomarker Extraction',
      desc: 'Raw text strings are parsed and mapped into 22 canonical clinical variables with reference range flags.',
      icon: Layers,
      badge: 'Normalization',
      detail: 'Resolves alias variations such as "HbA1c", "Glycated Hemoglobin", and "A1C" into a single canonical feature.',
    },
    {
      id: 'fusion',
      num: '03',
      title: 'Multimodal Fusion',
      short: 'Signal Fusion',
      desc: 'Synchronizes clinical biochemistry, 15D wearable telemetry metrics, and 20 gut microbiome taxa.',
      icon: Sliders,
      badge: 'Multimodal Layer',
      detail: 'Handles complete (C+W+G) or partial (C+W, C+G, Clinical Only) patient data availability seamlessly.',
    },
    {
      id: 'prediction',
      num: '04',
      title: 'AI Stacking Ensemble',
      short: 'AI Ensemble',
      desc: 'Gradient boosted tree ensembles compute calibrated probabilistic risk scores for metabolic disorders.',
      icon: Activity,
      badge: 'XGBoost & LightGBM',
      detail: 'Calibrated with Platt scaling to guarantee risk probability accuracy across diverse patient cohorts.',
    },
    {
      id: 'treeshap',
      num: '05',
      title: 'TreeSHAP Attributions',
      short: 'TreeSHAP Drivers',
      desc: 'Local game-theoretic explainer computes precise SHAP values to rank top risk-increasing and risk-lowering factors.',
      icon: Brain,
      badge: 'Explainable AI',
      detail: 'Ensures absolute transparency by pinpointing exact biomarker contributions for every prediction.',
    },
    {
      id: 'rag',
      num: '06',
      title: 'Medical RAG Query',
      short: 'RAG Knowledge',
      desc: 'ChromaDB vector embeddings query peer-reviewed medical guidelines (ADA, ACC, AHA) for clinical recommendations.',
      icon: Database,
      badge: 'Vector Embeddings',
      detail: 'Retrieves evidence-based clinical action plans tailored to the patient’s specific biomarker abnormalities.',
    },
    {
      id: 'report',
      num: '07',
      title: 'Clinical Report Generation',
      short: 'Printable Report',
      desc: 'Generates a hospital-grade printable summary report complete with QR code verification and physician sign-off fields.',
      icon: FileText,
      badge: 'Physician Report',
      detail: 'Ready for electronic health record (EHR) attachment or direct patient consultation review.',
    },
  ];

  const currentStep = timelineSteps[activeStepIndex];
  const StepIcon = currentStep.icon;

  return (
    <section className="py-24 bg-[var(--bg-surface)] border-b border-[var(--border-subtle)] space-y-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        
        {/* Header */}
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <Badge variant="accent" size="sm">7-STEP RESEARCH TIMELINE</Badge>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[var(--text-main)] tracking-tight">
            Interactive AI Pipeline Architecture
          </h2>
          <p className="text-base text-[var(--text-muted)] font-normal">
            Click through each stage to explore how TeleMed AI processes multimodal data in sub-35ms runtime.
          </p>
        </div>

        {/* Horizontal Stepper Buttons */}
        <div className="flex items-center justify-between overflow-x-auto pb-4 gap-2 no-scrollbar">
          {timelineSteps.map((st, idx) => {
            const Icon = st.icon;
            const isActive = idx === activeStepIndex;
            return (
              <button
                key={st.id}
                onClick={() => setActiveStepIndex(idx)}
                className={`flex flex-col items-center min-w-[110px] p-3 rounded-2xl border transition-all text-center ${
                  isActive
                    ? 'bg-[var(--primary-light)] border-[var(--primary)] text-[var(--primary)] shadow-md scale-105'
                    : 'bg-[var(--bg-primary)] border-[var(--border-subtle)] text-[var(--text-muted)] hover:text-[var(--text-main)] hover:bg-[var(--bg-surface-hover)]'
                }`}
              >
                <div className={`p-2 rounded-xl mb-1.5 ${isActive ? 'bg-[var(--primary)] text-white' : 'bg-[var(--bg-surface)]'}`}>
                  <Icon className="w-4 h-4" />
                </div>
                <span className="text-[10px] font-mono font-bold uppercase tracking-wider block">STEP {st.num}</span>
                <span className="text-xs font-semibold tracking-tight truncate max-w-[100px]">{st.short}</span>
              </button>
            );
          })}
        </div>

        {/* Selected Step Detail Panel */}
        <Card isGlass={true} className="p-8 space-y-6 border-l-4 border-l-[var(--primary)] animate-fade-in shadow-xl">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--border-subtle)] pb-6">
            <div className="flex items-center gap-4">
              <div className="p-4 rounded-2xl bg-[var(--primary-light)] text-[var(--primary)]">
                <StepIcon className="w-8 h-8" />
              </div>
              <div>
                <span className="text-xs font-mono font-bold text-[var(--text-muted)] uppercase">STAGE {currentStep.num} OF 07</span>
                <h3 className="text-2xl font-extrabold text-[var(--text-main)]">{currentStep.title}</h3>
              </div>
            </div>
            <Badge variant="primary" size="md">{currentStep.badge}</Badge>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-12 gap-6 items-center">
            <div className="md:col-span-8 space-y-3">
              <p className="text-base text-[var(--text-main)] font-medium leading-relaxed">
                {currentStep.desc}
              </p>
              <div className="p-3.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-xs text-[var(--text-muted)] flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-[var(--success)] shrink-0" />
                <span>{currentStep.detail}</span>
              </div>
            </div>

            <div className="md:col-span-4 flex justify-end">
              <Button
                variant="outline"
                size="md"
                className="w-full md:w-auto"
                rightIcon={<ArrowRight className="w-4 h-4" />}
                onClick={() => setActiveStepIndex((prev) => (prev + 1) % timelineSteps.length)}
              >
                Next Pipeline Stage →
              </Button>
            </div>
          </div>
        </Card>

      </div>
    </section>
  );
}
