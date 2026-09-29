import React, { useState } from 'react';
import { Card, Badge } from '../ui';
import { BookOpen, ChevronDown, ChevronUp, ShieldCheck, Heart, Activity, Dna, Utensils, HelpCircle } from 'lucide-react';

export default function KnowledgePanel({ predictionData }) {
  const [openIndex, setOpenIndex] = useState(0);

  const predictions = predictionData?.predictions || predictionData?.disease_outcomes || {};
  const getProb = (key) => {
    const item = predictions[key];
    if (!item) return 0;
    return item.calibrated_probability !== undefined ? item.calibrated_probability : (item.probability || 0);
  };

  const t2dRisk = getProb('Type2_Diabetes');
  const metRisk = getProb('Metabolic_Syndrome');
  const nafldRisk = getProb('NAFLD');

  // Build context-aware, patient-friendly references
  const references = [
    {
      title: 'Understanding Your Blood Sugar Results',
      icon: Activity,
      category: 'Blood Sugar',
      summary: `Your assessment checked for diabetes and prediabetes risk (currently ${Math.round(t2dRisk * 100)}%). Here's what the numbers mean:`,
      details: [
        { label: 'Normal fasting blood sugar', value: 'Below 100 mg/dL', meaning: 'Your body is handling sugar well.' },
        { label: 'Prediabetes range', value: '100-125 mg/dL', meaning: 'Your blood sugar is slightly high. Lifestyle changes can often bring it back to normal.' },
        { label: 'Diabetes range', value: '126+ mg/dL', meaning: 'Your blood sugar is elevated and needs attention. Talk to your doctor about next steps.' },
        { label: 'HbA1c (3-month average)', value: 'Normal: below 5.7%', meaning: 'This test shows your average blood sugar over the past 2-3 months, giving a bigger picture than a single test.' },
      ],
      tip: 'Simple steps like walking for 15 minutes after meals, choosing whole grains over white bread, and drinking water instead of sugary drinks can make a real difference.',
      source: 'American Diabetes Association (ADA) 2026 Clinical Guidelines'
    },
    {
      title: 'Heart Health & Blood Pressure Basics',
      icon: Heart,
      category: 'Heart Health',
      summary: `Your metabolic syndrome risk is ${Math.round(metRisk * 100)}%. Metabolic syndrome is a cluster of conditions that increase risk for heart disease. Here's what to watch:`,
      details: [
        { label: 'Healthy blood pressure', value: 'Below 120/80 mmHg', meaning: 'Your heart is pumping blood without extra strain.' },
        { label: 'Elevated blood pressure', value: '120-139/80-89 mmHg', meaning: 'Your heart is working a bit harder than ideal. Reducing salt and exercising helps.' },
        { label: 'Healthy triglycerides', value: 'Below 150 mg/dL', meaning: 'Your blood fat levels are in a good range.' },
        { label: 'Healthy HDL ("good") cholesterol', value: 'Above 40 mg/dL (men) / 50 mg/dL (women)', meaning: 'HDL helps remove harmful cholesterol from your bloodstream.' },
      ],
      tip: 'The Mediterranean diet (olive oil, fish, vegetables, nuts) is one of the most studied and effective dietary patterns for heart health.',
      source: 'American Heart Association (AHA) & National Heart, Lung, and Blood Institute (NHLBI)'
    },
    {
      title: 'Your Gut Microbiome Explained',
      icon: Dna,
      category: 'Gut Health',
      summary: 'Your gut contains trillions of bacteria that affect your digestion, immune system, and even your blood sugar. Here are the key bacteria we measured:',
      details: [
        { label: 'Akkermansia muciniphila', value: 'Healthy: 1-4%', meaning: 'This bacterium strengthens your intestinal lining. Higher levels are linked to better blood sugar control and lower inflammation.' },
        { label: 'Faecalibacterium prausnitzii', value: 'Healthy: 5-15%', meaning: 'Produces butyrate, a substance that nourishes your gut lining and reduces inflammation throughout your body.' },
        { label: 'Firmicutes/Bacteroidetes ratio', value: 'Healthy: balanced', meaning: 'An imbalance between these two major bacterial groups is linked to obesity and metabolic issues.' },
        { label: 'Shannon Diversity Index', value: 'Healthy: 2.5-4.0', meaning: 'Higher diversity generally means a healthier gut. Eating 30+ different plant foods per week supports diversity.' },
      ],
      tip: 'To support good gut bacteria: eat plenty of vegetables, fruits, and fermented foods (yogurt, kimchi); limit processed foods and artificial sweeteners; and get enough sleep.',
      source: 'Human Microbiome Project & Published Microbiome Research'
    },
    {
      title: 'Liver Health & NAFLD',
      icon: Utensils,
      category: 'Liver',
      summary: `Your liver health risk (NAFLD) is ${Math.round(nafldRisk * 100)}%. NAFLD stands for Non-Alcoholic Fatty Liver Disease — fat buildup in the liver not caused by alcohol.`,
      details: [
        { label: 'ALT enzyme', value: 'Normal: 7-35 U/L', meaning: 'ALT is released when liver cells are damaged. Higher levels may indicate liver stress or fatty liver.' },
        { label: 'AST enzyme', value: 'Normal: 8-33 U/L', meaning: 'Another liver enzyme. When both ALT and AST are elevated, it suggests the liver needs attention.' },
        { label: 'What causes NAFLD', value: 'Diet, weight, genetics', meaning: 'Excess sugar (especially fructose), being overweight, and genetic factors can all contribute.' },
      ],
      tip: 'The most effective steps: reduce added sugars (especially sodas and fruit juices), maintain a healthy weight, and exercise regularly. Even modest weight loss of 5-10% can significantly reduce liver fat.',
      source: 'American Association for the Study of Liver Diseases (AASLD)'
    },
    {
      title: 'How Our AI Analysis Works',
      icon: ShieldCheck,
      category: 'AI Method',
      summary: 'Our AI system analyzes your health data using multiple specialized models, similar to how a team of medical specialists would review your case together.',
      details: [
        { label: 'Clinical Model', value: '18 lab measurements', meaning: 'Analyzes your blood test results (blood sugar, cholesterol, liver enzymes, etc.) using patterns learned from thousands of patient records.' },
        { label: 'Wearable Model', value: '15 activity metrics', meaning: 'Evaluates your daily activity, sleep quality, and heart rate data from fitness trackers and smartwatches.' },
        { label: 'Gut Model', value: '49 bacterial markers', meaning: 'Analyzes your gut microbiome composition to identify patterns linked to metabolic health.' },
        { label: 'Explainability (SHAP)', value: 'Transparency tool', meaning: 'Shows exactly which health factors influenced your risk score the most, so you understand WHY you got your results — not just what they are.' },
      ],
      tip: 'Remember: AI results are a guide, not a diagnosis. Always discuss your results with your healthcare provider, who can consider your full medical history and symptoms.',
      source: 'TeleMed AI v4.0 — Validated Multimodal Health Assessment Engine'
    }
  ];

  return (
    <Card isGlass={true} className="p-6 space-y-4 shadow-xl border-t-4 border-t-[var(--secondary)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-[var(--secondary)]" />
          <div>
            <h3 className="text-base font-extrabold text-[var(--text-main)]">Health Knowledge Library</h3>
            <p className="text-[10px] text-[var(--text-muted)]">Easy-to-understand guides about your health measurements and what they mean</p>
          </div>
        </div>
        <Badge variant="secondary" size="sm">Patient Guide</Badge>
      </div>

      {/* Intro banner */}
      <div className="p-3 rounded-xl bg-purple-50 dark:bg-purple-900/20 border border-purple-200 dark:border-purple-800 text-xs text-purple-800 dark:text-purple-200 flex items-start gap-2">
        <HelpCircle className="w-4 h-4 mt-0.5 shrink-0" />
        <span>Click on any topic below to learn what your health measurements mean in simple, everyday language. No medical degree required!</span>
      </div>

      <div className="space-y-2 text-xs">
        {references.map((ref, idx) => {
          const isOpen = openIndex === idx;
          const Icon = ref.icon;
          return (
            <div key={idx} className="rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] overflow-hidden">
              <button
                onClick={() => setOpenIndex(isOpen ? -1 : idx)}
                className="w-full p-3 flex items-center justify-between text-left hover:bg-[var(--bg-surface-hover)] transition-colors"
              >
                <div className="flex items-center gap-2">
                  <Icon className="w-4 h-4 text-[var(--secondary)]" />
                  <Badge variant="primary" size="sm">{ref.category}</Badge>
                  <strong className="text-xs text-[var(--text-main)] font-semibold">{ref.title}</strong>
                </div>
                {isOpen ? <ChevronUp className="w-4 h-4 text-[var(--text-muted)]" /> : <ChevronDown className="w-4 h-4 text-[var(--text-muted)]" />}
              </button>

              {isOpen && (
                <div className="p-4 pt-0 space-y-3 border-t border-[var(--border-subtle)] animate-fade-in">
                  <p className="text-[11px] text-[var(--text-muted)] leading-relaxed">{ref.summary}</p>

                  <div className="space-y-2">
                    {ref.details.map((detail, dIdx) => (
                      <div key={dIdx} className="p-2.5 rounded-lg bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                        <div className="flex justify-between items-start gap-2 mb-1">
                          <strong className="text-[11px] text-[var(--text-main)]">{detail.label}</strong>
                          <span className="text-[10px] font-mono text-[var(--primary)] whitespace-nowrap">{detail.value}</span>
                        </div>
                        <p className="text-[10px] text-[var(--text-muted)] leading-relaxed">{detail.meaning}</p>
                      </div>
                    ))}
                  </div>

                  {/* Practical Tip */}
                  <div className="p-3 rounded-lg bg-green-50 dark:bg-green-900/15 border border-green-200 dark:border-green-800">
                    <strong className="text-[11px] text-green-800 dark:text-green-200 block mb-1">💡 Practical Tip</strong>
                    <p className="text-[10px] text-green-700 dark:text-green-300 leading-relaxed">{ref.tip}</p>
                  </div>

                  <p className="text-[9px] font-mono text-[var(--text-dim)] italic">Source: {ref.source}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </Card>
  );
}
