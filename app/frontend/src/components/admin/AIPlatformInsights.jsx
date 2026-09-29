import React from 'react';
import { Card, Badge } from '../ui';
import { Sparkles, Brain, Cpu, ShieldCheck } from 'lucide-react';

export default function AIPlatformInsights() {
  const insights = [
    { label: 'Avg Stacking Confidence', val: '94.8%', detail: 'Calibrated logistic stacker' },
    { label: 'Avg Input Data Quality', val: '98.2%', detail: 'Zero critical missing features' },
    { label: 'Pipeline Success Rate', val: '99.9%', detail: '0 failed inferences today' },
    { label: 'Avg Report Build Time', val: '2.4s', detail: 'HTML5/PDF generation' },
  ];

  return (
    <Card isGlass={true} className="p-6 space-y-4 shadow-xl border-t-4 border-t-[var(--accent)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-[var(--accent)]" />
          <h3 className="text-base font-extrabold text-[var(--text-main)]">AI Model Performance & Latency</h3>
        </div>
        <Badge variant="accent" size="sm">Optimal Accuracy</Badge>
      </div>

      <div className="grid grid-cols-2 gap-3 text-xs">
        {insights.map((ins, idx) => (
          <div key={idx} className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-1">
            <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">{ins.label}</span>
            <div className="text-xl font-extrabold font-mono text-[var(--text-main)]">{ins.val}</div>
            <p className="text-[10px] text-[var(--text-muted)]">{ins.detail}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
