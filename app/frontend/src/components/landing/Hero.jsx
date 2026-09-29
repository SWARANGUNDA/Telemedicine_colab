import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldCheck, ArrowRight, Activity, Sparkles, Brain, FileText, Watch, Dna, CheckCircle2, ChevronDown } from 'lucide-react';
import { Button, Card, Badge, ProgressBar } from '../ui';

export default function Hero({ onOpenAuth }) {
  const navigate = useNavigate();

  const scrollToNextSection = () => {
    window.scrollTo({
      top: window.innerHeight * 0.85,
      behavior: 'smooth',
    });
  };

  return (
    <section className="relative pt-32 pb-20 md:pt-40 md:pb-28 overflow-hidden bg-gradient-to-b from-[var(--bg-primary)] via-[var(--bg-surface)] to-[var(--bg-primary)]">
      {/* Gradient Glow Effect Behind Illustration */}
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] bg-gradient-to-tr from-[var(--primary)]/15 via-[var(--secondary)]/15 to-[var(--accent)]/15 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10 space-y-16">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
          
          {/* Left Column — Text & CTAs */}
          <div className="lg:col-span-7 space-y-6 text-center lg:text-left">
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[var(--primary-light)] border border-[var(--primary)]/20 text-[var(--primary)] text-xs font-semibold shadow-sm">
              <Sparkles className="w-4 h-4 text-[var(--primary)] animate-pulse" />
              <span>Hierarchical Stacking Ensemble v4.0 Active</span>
            </div>

            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold text-[var(--text-main)] tracking-tight leading-[1.15]">
              AI-Powered <span className="bg-gradient-to-r from-[var(--primary)] via-[var(--secondary)] to-[var(--accent)] bg-clip-text text-transparent">Multimodal Disease</span> Prediction Platform
            </h1>

            <p className="text-base sm:text-lg text-[var(--text-muted)] max-w-2xl mx-auto lg:mx-0 font-normal leading-relaxed">
              Clinical Biomarkers • Wearable Telemetry • Gut Microbiome Taxa • TreeSHAP Explainability • Medical RAG. Enterprise clinical decision support for modern healthcare systems.
            </p>

            <div className="flex items-center justify-center lg:justify-start gap-4 pt-2 flex-wrap">
              <Button
                variant="primary"
                size="lg"
                className="!px-8 !py-4 text-base shadow-xl shadow-[var(--primary)]/30 hover:scale-105 transition-all duration-200"
                rightIcon={<ArrowRight className="w-5 h-5" />}
                onClick={() => onOpenAuth ? onOpenAuth('register') : navigate('/register')}
                aria-label="Start Free Analysis"
              >
                Start Free Analysis
              </Button>
              <Button
                variant="outline"
                size="lg"
                className="!px-7 !py-4 text-base hover:bg-[var(--bg-surface-hover)] transition-all"
                leftIcon={<Activity className="w-5 h-5 text-[var(--secondary)]" />}
                onClick={() => navigate('/dashboard')}
                aria-label="Explore Interactive Platform"
              >
                Explore Interactive Platform
              </Button>
            </div>

            <div className="pt-4 flex items-center justify-center lg:justify-start gap-6 text-xs text-[var(--text-muted)] flex-wrap font-medium">
              <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-[var(--success)]" /> HIPAA & GDPR Compliant</span>
              <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-[var(--success)]" /> 95.0% AI Accuracy</span>
              <span className="flex items-center gap-1.5"><CheckCircle2 className="w-4 h-4 text-[var(--success)]" /> Zero Data Retention</span>
            </div>
          </div>

          {/* Right Column — Enterprise Floating Card Illustration */}
          <div className="lg:col-span-5 relative space-y-4">
            
            {/* Card 1: Disease Risk Prediction Card with floating hover effect */}
            <Card isGlass={true} className="p-5 space-y-3 border-l-4 border-l-[var(--primary)] shadow-2xl hover:-translate-y-1.5 transition-all duration-300">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Activity className="w-5 h-5 text-[var(--primary)]" />
                  <h4 className="text-sm font-bold text-[var(--text-main)]">Type 2 Diabetes Risk Prediction</h4>
                </div>
                <Badge variant="danger" size="sm">PREDIABETES RISK (99%)</Badge>
              </div>
              <ProgressBar value={99} max={100} variant="danger" />
              <div className="flex justify-between text-[11px] font-mono text-[var(--text-muted)]">
                <span>Model Confidence: 99.5%</span>
                <span>Pathway: C + W + G</span>
              </div>
            </Card>

            {/* Card 2: TreeSHAP Feature Attribution Preview */}
            <Card isGlass={true} className="p-5 space-y-3 border-l-4 border-l-[var(--accent)] shadow-xl ml-4 sm:ml-6 hover:-translate-y-1.5 transition-all duration-300">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Brain className="w-5 h-5 text-[var(--accent)]" />
                  <h4 className="text-sm font-bold text-[var(--text-main)]">Top TreeSHAP Biomarker Driver</h4>
                </div>
                <Badge variant="accent" size="sm">+0.18 Impact</Badge>
              </div>
              <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-xs flex justify-between items-center">
                <div>
                  <strong className="text-[var(--text-main)] block">HbA1c (Glycated Hemoglobin)</strong>
                  <span className="text-[10px] font-mono text-[var(--text-muted)]">Observed: 7.2 % (Reference: 4.0 - 5.6 %)</span>
                </div>
                <Badge variant="danger" size="sm">Increases Risk</Badge>
              </div>
            </Card>

            {/* Card 3: Clinical Report Summary Badge */}
            <Card isGlass={true} className="p-4 space-y-2 border-l-4 border-l-[var(--secondary)] shadow-lg -mt-2 hover:-translate-y-1 transition-all duration-300">
              <div className="flex items-center justify-between text-xs">
                <div className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-[var(--secondary)]" />
                  <span className="font-bold text-[var(--text-main)]">Printable Clinical Report Ready</span>
                </div>
                <span className="font-mono text-[10px] text-[var(--text-muted)]">ASM-2026-8819</span>
              </div>
            </Card>

          </div>

        </div>

        {/* Animated Scroll Indicator Button */}
        <div className="flex justify-center pt-8">
          <button
            onClick={scrollToNextSection}
            className="flex flex-col items-center gap-1.5 text-xs text-[var(--text-muted)] hover:text-[var(--primary)] transition-colors group focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary)] p-2 rounded-xl"
            aria-label="Scroll to explore features"
          >
            <span className="font-mono uppercase text-[10px] tracking-widest">Scroll to explore</span>
            <ChevronDown className="w-4 h-4 animate-bounce group-hover:text-[var(--primary)]" />
          </button>
        </div>

      </div>
    </section>
  );
}
