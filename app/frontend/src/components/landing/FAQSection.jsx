import React, { useState } from 'react';
import { Card, Badge, Accordion } from '../ui';
import { HelpCircle } from 'lucide-react';

export default function FAQSection() {
  const faqs = [
    {
      id: 'faq-1',
      title: 'How does the OCR extraction work for lab PDF reports?',
      content: 'TeleMed AI utilizes a hybrid Tesseract OCR engine coupled with Regex and fuzzy string matching. When a lab PDF is uploaded, the parser scans tables for blood biomarker names, normalizes them to canonical feature keys (e.g., HbA1c, Fasting Glucose), and flags out-of-range values against standard clinical reference intervals.',
    },
    {
      id: 'faq-2',
      title: 'What clinical conditions does TeleMed AI predict?',
      content: 'The platform currently focuses on early metabolic syndrome risk stratification, including Type 2 Diabetes, Insulin Resistance, Metabolic Dysbiosis, and Cardiopulmonary Telemetry Risk.',
    },
    {
      id: 'faq-3',
      title: 'What data modalities are required to run an analysis?',
      content: 'TeleMed AI supports flexible partial modality combinations. While a full analysis utilizes Clinical Biochemistry + Wearables + Gut Microbiome (C+W+G), predictions can be executed with Clinical + Wearable (C+W), Clinical + Microbiome (C+G), or Clinical Biochemistry alone.',
    },
    {
      id: 'faq-4',
      title: 'How are TreeSHAP feature attributions calculated?',
      content: 'TreeSHAP (SHapley Additive exPlanations) is a game-theoretic approach that computes the exact contribution of each biomarker to the final risk probability score. Positive SHAP values indicate factors that increase risk, while negative values indicate protective factors.',
    },
    {
      id: 'faq-5',
      title: 'Is patient health data secure and HIPAA compliant?',
      content: 'Yes. TeleMed AI enforces strict data privacy controls. Uploaded files are processed in zero-retention temporary RAM memory. Persistent records stored in the database are encrypted at rest using AES-256 standards.',
    },
    {
      id: 'faq-6',
      title: 'How does the Medical RAG recommendation system work?',
      content: 'Our Retrieval-Augmented Generation (RAG) engine indexes peer-reviewed clinical guidelines (such as ADA 2026 Standards of Care) in ChromaDB vector space. For detected risk factors, it retrieves evidence-based clinical action plans for physician review.',
    },
    {
      id: 'faq-7',
      title: 'How do physicians interact with the platform?',
      content: 'Verified doctors access a dedicated 3-panel Consultation Workspace. They can review patient biomarker profiles, inspect TreeSHAP driver charts, author diagnostic notes, and issue digital recommendations.',
    },
    {
      id: 'faq-8',
      title: 'Can wearable telemetry data be synced automatically?',
      content: 'Yes. The system processes 15-dimensional wearable sensor time-series data, including Resting Heart Rate, Heart Rate Variability (HRV), Sleep Efficiency, and Active Energy Expenditure.',
    },
    {
      id: 'faq-9',
      title: 'How accurate are the AI prediction models?',
      content: 'Our hierarchical stacking ensembles achieve a calibrated 95.0% prediction accuracy across evaluated multi-modality clinical test cohorts, verified with Platt scaling.',
    },
    {
      id: 'faq-10',
      title: 'Can I export clinical reports for electronic health records (EHR)?',
      content: 'Yes. Every assessment generates a printable hospital-grade PDF clinical report complete with QR code verification badges for quick authenticity validation.',
    },
  ];

  return (
    <section className="py-24 bg-[var(--bg-primary)] border-b border-[var(--border-subtle)] space-y-12">
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <Badge variant="primary" size="sm">FREQUENTLY ASKED QUESTIONS</Badge>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[var(--text-main)] tracking-tight">
            Healthcare AI & Clinical FAQs
          </h2>
          <p className="text-base text-[var(--text-muted)] font-normal">
            Everything you need to know about our multimodal disease prediction engine and clinical decision support.
          </p>
        </div>

        <Card isGlass={true} className="p-6 md:p-8 shadow-xl">
          <Accordion items={faqs} allowMultiple={false} />
        </Card>
      </div>
    </section>
  );
}
