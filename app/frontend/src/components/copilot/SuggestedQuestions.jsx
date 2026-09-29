import React from 'react';
import { Card } from '../ui';
import { HelpCircle, ChevronRight } from 'lucide-react';

export default function SuggestedQuestions({ onSelectQuestion }) {
  const groups = [
    {
      category: 'Understanding Report',
      questions: [
        'What does my disease risk assessment mean for my overall health?',
        'How is multimodal AI clinical risk evaluated across modalities?',
      ],
    },
    {
      category: 'Biomarkers & SHAP',
      questions: [
        'How does TreeSHAP rank key physiological risk drivers?',
        'What are the primary biomarker contributors to metabolic risk?',
      ],
    },
    {
      category: 'Longitudinal Trends',
      questions: [
        'How is longitudinal risk progression tracked across assessments?',
        'What lifestyle modifications can improve my metabolic risk profile?',
      ],
    },
  ];

  return (
    <Card isGlass={true} className="p-6 space-y-4 shadow-xl border-t-4 border-t-[var(--primary)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-[var(--primary)]" />
          <h3 className="text-base font-extrabold text-[var(--text-main)]">Categorized Suggested Questions</h3>
        </div>
        <span className="text-xs font-mono text-[var(--text-muted)]">One-Click Prompts</span>
      </div>

      <div className="space-y-4 text-xs">
        {groups.map((grp, idx) => (
          <div key={idx} className="space-y-2">
            <h4 className="text-[10px] font-mono font-bold text-[var(--text-muted)] uppercase">{grp.category}</h4>
            <div className="space-y-1.5">
              {grp.questions.map((q, i) => (
                <button
                  key={i}
                  onClick={() => onSelectQuestion ? onSelectQuestion(q) : null}
                  className="w-full p-2.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)] hover:border-[var(--primary)] hover:text-[var(--primary)] text-left font-medium text-[var(--text-main)] transition-all flex items-center justify-between group text-[11px]"
                >
                  <span>{q}</span>
                  <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-[var(--primary)] shrink-0" />
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}
