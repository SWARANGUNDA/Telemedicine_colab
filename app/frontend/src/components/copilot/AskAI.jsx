import React from 'react';
import { Card, Button } from '../ui';
import { HelpCircle, Sparkles, MessageSquare, ChevronRight } from 'lucide-react';

export default function AskAI({ onSelectPrompt }) {
  const suggestedPrompts = [
    'Explain my latest diagnostic report in simple terms',
    'Why did my metabolic risk score change from last month?',
    'What are the key biomarkers I should focus on improving?',
    'How does TreeSHAP calculate feature importance for HbA1c?',
    'What dietary changes will help optimize my gut microbiome?',
    'Compare my current assessment with 90 days ago',
  ];

  return (
    <Card isGlass={true} className="p-6 space-y-4 shadow-xl border-t-4 border-t-[var(--accent)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <HelpCircle className="w-5 h-5 text-[var(--accent)]" />
          <h3 className="text-base font-extrabold text-[var(--text-main)]">Ask AI Copilot</h3>
        </div>
        <span className="text-xs font-mono text-[var(--text-muted)]">Suggested Prompts</span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
        {suggestedPrompts.map((prompt, idx) => (
          <button
            key={idx}
            onClick={() => onSelectPrompt ? onSelectPrompt(prompt) : null}
            className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] hover:border-[var(--primary)] hover:text-[var(--primary)] text-left font-medium text-[var(--text-main)] transition-all flex items-center justify-between group"
          >
            <span className="text-[11px] leading-snug">{prompt}</span>
            <ChevronRight className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity text-[var(--primary)]" />
          </button>
        ))}
      </div>
    </Card>
  );
}
