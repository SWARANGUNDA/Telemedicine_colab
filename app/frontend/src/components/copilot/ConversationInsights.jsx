import React from 'react';
import { Card, Badge } from '../ui';
import { MessageSquare, FileText, CheckCircle2 } from 'lucide-react';

export default function ConversationInsights({ predictionData }) {
  const topics = predictionData ? [
    { name: `Multimodal Assessment (${predictionData.effective_pathway || 'C+W+G'})`, type: 'Report' },
    { name: 'TreeSHAP Feature Attributions', type: 'Biomarker' },
    { name: `Data Quality Score: ${Math.round((predictionData.data_quality_score || 0.85) * 100)}%`, type: 'Quality' },
  ] : [];

  return (
    <Card isGlass={true} className="p-6 space-y-4 shadow-xl">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-[var(--primary)]" />
          <h3 className="text-base font-extrabold text-[var(--text-main)]">Conversation Insights Log</h3>
        </div>
        <Badge variant={predictionData ? 'primary' : 'outline'} size="sm">
          {topics.length} Topics
        </Badge>
      </div>

      <div className="space-y-2 text-xs">
        {topics.length > 0 ? (
          topics.map((t, idx) => (
            <div key={idx} className="p-2.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] flex items-center justify-between">
              <span className="text-[11px] font-semibold text-[var(--text-main)]">{t.name}</span>
              <Badge variant="secondary" size="sm">{t.type}</Badge>
            </div>
          ))
        ) : (
          <p className="text-xs text-[var(--text-muted)] text-center py-3">No active conversation topics logged</p>
        )}
      </div>
    </Card>
  );
}
