import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight, Mail, Sparkles } from 'lucide-react';
import { Button } from '../ui';

export default function CTA({ onOpenAuth }) {
  const navigate = useNavigate();

  return (
    <section className="py-20 bg-gradient-to-r from-[var(--bg-dark)] via-slate-900 to-[var(--bg-dark)] text-white relative overflow-hidden">
      <div className="absolute top-0 right-0 w-96 h-96 bg-[var(--primary)]/20 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-[var(--secondary)]/20 rounded-full blur-3xl pointer-events-none" />

      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center space-y-6 relative z-10">
        <div className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white/10 text-white text-xs font-semibold backdrop-blur-md">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <span>Production-Ready Multimodal AI</span>
        </div>

        <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white leading-tight">
          Ready to Experience AI-Powered Healthcare?
        </h2>

        <p className="text-base sm:text-lg text-slate-300 max-w-2xl mx-auto font-normal leading-relaxed">
          Upload medical lab PDFs, sync wearable telemetry, or analyze gut microbiome taxa for explainable risk assessment.
        </p>

        <div className="flex items-center justify-center gap-4 pt-4 flex-wrap">
          <Button
            variant="primary"
            size="lg"
            className="!px-8 !py-3.5 text-base shadow-xl"
            rightIcon={<ArrowRight className="w-5 h-5" />}
            onClick={() => onOpenAuth ? onOpenAuth('register') : navigate('/register')}
          >
            Start Free Analysis
          </Button>
          <Button
            variant="outline"
            size="lg"
            className="!px-8 !py-3.5 text-base border-white/20 text-white hover:bg-white/10"
            leftIcon={<Mail className="w-5 h-5" />}
            onClick={() => navigate('/contact')}
          >
            Contact Us
          </Button>
        </div>
      </div>
    </section>
  );
}
