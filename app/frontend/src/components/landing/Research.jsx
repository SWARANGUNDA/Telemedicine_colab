import React from 'react';
import { Card, Badge } from '../ui';
import { Dna, Activity, Watch, Brain, ShieldCheck, Sparkles } from 'lucide-react';

export default function Research() {
  return (
    <section className="py-20 bg-[var(--bg-surface)] border-b border-[var(--border-subtle)]">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-12">
        <div className="text-center max-w-3xl mx-auto space-y-3">
          <Badge variant="primary" size="sm">RESEARCH & ARCHITECTURE</Badge>
          <h2 className="text-3xl sm:text-4xl font-extrabold text-[var(--text-main)] tracking-tight">
            Scientific Foundation & Multimodal Fusion
          </h2>
          <p className="text-base text-[var(--text-muted)] font-normal">
            Bridging clinical biochemistry, continuous wearable telemetry, and gut microbiome sequencing into unified diagnostic stacking ensembles.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <Card isGlass={true} className="p-6 space-y-4 border-t-4 border-t-[var(--primary)]">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-[var(--primary-light)] text-[var(--primary)]">
                <Activity className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[var(--text-main)]">Clinical Expert v4</h3>
            </div>
            <p className="text-sm text-[var(--text-muted)] leading-relaxed">
              Trained on 18 canonical clinical biomarkers (blood chemistry, glycemic panels, liver/renal markers). Calibrated with Platt scaling to produce reliable probabilistic risk scores for metabolic disorders.
            </p>
          </Card>

          <Card isGlass={true} className="p-6 space-y-4 border-t-4 border-t-[var(--secondary)]">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-[var(--secondary-light)] text-[var(--secondary)]">
                <Watch className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[var(--text-main)]">Wearable Telemetry v4</h3>
            </div>
            <p className="text-sm text-[var(--text-muted)] leading-relaxed">
              Processes 15 continuous sensor and CGM time-series metrics. Captures autonomic nervous system dynamics via HRV RMSSD, resting pulse, and continuous circadian sleep fragmentation index.
            </p>
          </Card>

          <Card isGlass={true} className="p-6 space-y-4 border-t-4 border-t-[var(--accent)]">
            <div className="flex items-center gap-3">
              <div className="p-2.5 rounded-xl bg-[var(--accent-light)] text-[var(--accent)]">
                <Dna className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-[var(--text-main)]">Gut Microbiome v4</h3>
            </div>
            <p className="text-sm text-[var(--text-muted)] leading-relaxed">
              Evaluates 40 bacterial taxa abundances and 9 derived ecological/functional indices. Identifies metabolic dysbiosis patterns linked to systemic low-grade inflammation and insulin resistance.
            </p>
          </Card>
        </div>
      </div>
    </section>
  );
}
