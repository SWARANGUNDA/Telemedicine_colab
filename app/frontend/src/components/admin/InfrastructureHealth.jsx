import React from 'react';
import { Card, Badge } from '../ui';
import { Server, Cpu, Database, Activity, ShieldCheck, Zap } from 'lucide-react';

export default function InfrastructureHealth() {
  const subsystems = [
    { name: 'FastAPI Microservice API', status: 'OPERATIONAL', detail: 'Active ASGI Uvicorn Engine', icon: Server, badgeVar: 'success' },
    { name: 'PostgreSQL / SQLite Database', status: 'OPERATIONAL', detail: 'Primary ORM Storage Engine', icon: Database, badgeVar: 'success' },
    { name: 'Multimodal Intake Normalizer', status: 'OPERATIONAL', detail: 'Bounds & Alias Normalization', icon: Cpu, badgeVar: 'success' },
    { name: 'Clinical Expert (CatBoost 18D)', status: 'ACTIVE IN-MEMORY', detail: 'Tabular Clinical Inferences', icon: Zap, badgeVar: 'primary' },
    { name: 'Wearable Expert (XGBoost 15D)', status: 'ACTIVE IN-MEMORY', detail: 'Continuous Telemetry Engine', icon: Activity, badgeVar: 'primary' },
    { name: 'Gut Microbiome Expert (CatBoost 49D)', status: 'ACTIVE IN-MEMORY', detail: 'Multi-Omics Abundance Expert', icon: Zap, badgeVar: 'primary' },
    { name: 'Multimodal Stacking Fusion Engine', status: 'OPERATIONAL', detail: '7-Pathway Calibrated Stacker', icon: Cpu, badgeVar: 'success' },
    { name: 'TreeSHAP Explainer Pipeline', status: 'OPERATIONAL', detail: 'Shapley Attribution Explainer', icon: ShieldCheck, badgeVar: 'success' },
    { name: 'FAISS Medical RAG Vector DB', status: 'OPERATIONAL', detail: 'ADA/EASD Clinical Index', icon: Database, badgeVar: 'success' },
  ];

  return (
    <Card isGlass={true} className="p-6 space-y-4 shadow-xl border-l-4 border-l-[var(--success)]">
      <div className="flex items-center justify-between border-b border-[var(--border-subtle)] pb-3 flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <Server className="w-5 h-5 text-[var(--success)]" />
          <h3 className="text-base font-extrabold text-[var(--text-main)]">Subsystem Infrastructure Health</h3>
        </div>
        <Badge variant="success" size="sm" className="font-mono text-xs">All Systems Operational</Badge>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        {subsystems.map((sub, idx) => {
          const Icon = sub.icon;
          return (
            <div key={idx} className="p-3.5 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] hover:border-[var(--primary)]/40 transition-all space-y-2">
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2 min-w-0">
                  <Icon className="w-4 h-4 text-[var(--primary)] shrink-0" />
                  <strong className="text-xs font-extrabold text-[var(--text-main)] truncate block">{sub.name}</strong>
                </div>
                <Badge variant={sub.badgeVar} size="sm" className="shrink-0 font-mono text-[9px] px-2 py-0.5 uppercase">
                  {sub.status}
                </Badge>
              </div>
              <div className="text-[10px] font-mono text-[var(--text-muted)] pt-1.5 border-t border-[var(--border-subtle)] truncate">
                {sub.detail}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
