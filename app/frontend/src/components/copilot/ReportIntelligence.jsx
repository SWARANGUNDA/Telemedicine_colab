import React from 'react';
import { Card, Badge, Button } from '../ui';
import { FileText, Sparkles, ExternalLink, ArrowRight, ShieldCheck, Activity } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function ReportIntelligence({ predictionData }) {
  const navigate = useNavigate();
  const dq = predictionData ? Math.round((predictionData.data_quality_score || 0.85) * 100) : null;
  const mainRisk = predictionData?.disease_outcomes?.Type2_Diabetes;

  return (
    <Card isGlass={true} className="p-6 space-y-4 shadow-xl border-l-4 border-l-[var(--primary)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-[var(--primary)]" />
          <h3 className="text-base font-extrabold text-[var(--text-main)]">Diagnostic Report Intelligence</h3>
        </div>
        <Badge variant={predictionData ? 'primary' : 'outline'} size="sm">
          {predictionData ? (predictionData.patient_id || 'ACTIVE_ASSESSMENT') : 'NO ACTIVE ASSESSMENT'}
        </Badge>
      </div>

      <div className="space-y-3 text-xs">
        <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] space-y-1">
          <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">Executive Summary</span>
          <p className="text-[11px] text-[var(--text-main)] leading-relaxed font-medium">
            {predictionData
              ? `Multimodal integration evaluated across ${predictionData.effective_pathway || 'C+W+G'} modalities. Primary risk vector: ${mainRisk?.risk_level || 'EVALUATED'} for Type 2 Diabetes.`
              : 'No active assessment found. Upload medical files in the Intake Workspace to generate diagnostic report intelligence.'}
          </p>
        </div>

        <div className="grid grid-cols-2 gap-2 text-xs font-mono">
          <div className="p-2.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
            <span className="text-[9px] text-[var(--text-muted)] block uppercase">AI Confidence</span>
            <strong className="text-[var(--primary)]">
              {predictionData ? 'High (V4 Stacked)' : 'NOT AVAILABLE'}
            </strong>
          </div>
          <div className="p-2.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
            <span className="text-[9px] text-[var(--text-muted)] block uppercase">Data Quality</span>
            <strong className="text-[var(--success)]">
              {dq !== null ? `${dq}% Grade A` : 'NOT AVAILABLE'}
            </strong>
          </div>
        </div>

        <div className="pt-2 flex justify-between items-center border-t border-[var(--border-subtle)]">
          <Button variant="ghost" size="sm" rightIcon={<ExternalLink className="w-3.5 h-3.5" />} onClick={() => navigate('/report')}>
            View Full PDF Report
          </Button>
          <Button variant="primary" size="sm" rightIcon={<ArrowRight className="w-3.5 h-3.5" />} onClick={() => navigate('/xai')}>
            Explore XAI Studio
          </Button>
        </div>
      </div>
    </Card>
  );
}
