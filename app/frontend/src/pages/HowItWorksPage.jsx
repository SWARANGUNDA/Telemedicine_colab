import React from 'react';
import { useNavigate } from 'react-router-dom';
import PublicCanvasLayout from '../components/landing/PublicCanvasLayout';
import HowItWorks3DVisual from '../components/landing/HowItWorks3DVisual';
import { Sparkles, FileText, Brain, LineChart, Stethoscope, Lock, ArrowRight, ShieldCheck, Activity } from 'lucide-react';

export default function HowItWorksPage({ user, onOpenAuth }) {
  const navigate = useNavigate();

  const handleGetStarted = () => {
    if (user) {
      const dashboardPath = user.role === 'ADMIN' ? '/admin/dashboard' : user.role === 'DOCTOR' ? '/doctor/dashboard' : '/dashboard';
      navigate(dashboardPath);
    } else if (onOpenAuth) {
      onOpenAuth('register');
    } else {
      navigate('/register');
    }
  };

  const steps = [
    {
      num: '01',
      title: 'Collect Data',
      desc: 'We collect clinical reports, wearable data and gut microbiome information into a unified intake pipeline.',
      icon: FileText
    },
    {
      num: '02',
      title: 'AI Analysis',
      desc: 'Our calibrated AI expert models analyze multiple data sources to identify hidden health patterns.',
      icon: Brain
    },
    {
      num: '03',
      title: 'Generate Insights',
      desc: 'Get personalized insights, risk predictions and explainable SHAP biomarker drivers.',
      icon: LineChart
    },
    {
      num: '04',
      title: 'Actionable Support',
      desc: 'Use evidence-based insights to help users and clinicians make informed care decisions.',
      icon: Stethoscope
    }
  ];

  return (
    <PublicCanvasLayout user={user} onOpenAuth={onOpenAuth}>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-16">
        
        {/* 2-COLUMN HERO LAYOUT matching Home, Research, About pages */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          
          {/* LEFT COLUMN: Text & CTAs */}
          <div className="lg:col-span-7 space-y-6 text-left">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-sm font-bold shadow-2xs">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span>How It Works</span>
            </div>
            
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-[1.1]">
              Simple Process. <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600">
                Powerful Results.
              </span>
            </h1>
            
            <p className="text-base sm:text-lg text-slate-600 font-medium leading-relaxed max-w-xl">
              TeleMed AI follows a simple 4-step process to transform complex clinical reports, wearable metrics, and gut microbiome data into clear, actionable health insights.
            </p>

            <div className="flex flex-wrap items-center gap-4 pt-2">
              <button
                onClick={handleGetStarted}
                className="px-7 py-3.5 rounded-full bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-extrabold text-sm shadow-xl shadow-blue-500/25 hover:shadow-2xl hover:scale-[1.02] transition-all flex items-center gap-2.5 cursor-pointer"
              >
                <span>Get Started</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

            <div className="flex flex-wrap items-center gap-6 pt-2 text-sm font-bold text-slate-600">
              <div className="flex items-center gap-1.5">
                <ShieldCheck className="w-4 h-4 text-blue-600" />
                <span>Privacy First</span>
              </div>
              <div className="flex items-center gap-1.5">
                <Activity className="w-4 h-4 text-indigo-600" />
                <span>Automated Extraction</span>
              </div>
            </div>

          </div>

          {/* RIGHT COLUMN: 3D AI Cube Image */}
          <div className="lg:col-span-5 flex justify-center">
            <HowItWorks3DVisual />
          </div>

        </div>

        {/* 4-STEP CONNECTED PIPELINE GRID */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {steps.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div
                key={idx}
                className="p-8 rounded-3xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-[0_10px_30px_rgba(15,23,42,0.04)] hover:shadow-xl hover:-translate-y-1 transition-all space-y-4 relative"
              >
                <div className="flex items-center justify-between">
                  <span className="text-3xl font-black text-blue-600 font-mono">{step.num}</span>
                  <div className="p-3.5 rounded-2xl bg-blue-50 text-blue-600">
                    <Icon className="w-6 h-6" />
                  </div>
                </div>
                <h3 className="text-lg font-extrabold text-slate-900">{step.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed font-medium">
                  {step.desc}
                </p>
              </div>
            );
          })}
        </div>

        {/* PRIVACY FIRST BANNER */}
        <div className="p-8 sm:p-10 rounded-3xl bg-blue-50/90 border border-blue-200/90 flex flex-col sm:flex-row items-center gap-5 shadow-sm">
          <div className="p-4 rounded-2xl bg-blue-600 text-white shrink-0 shadow-md">
            <Lock className="w-8 h-8" />
          </div>
          <div className="space-y-1.5 text-center sm:text-left">
            <h3 className="text-lg sm:text-xl font-extrabold text-slate-900">Privacy first. Always secure.</h3>
            <p className="text-sm text-slate-600 font-medium">
              Your data belongs to you and is never sold or shared with third parties.
            </p>
          </div>
        </div>

      </main>
    </PublicCanvasLayout>
  );
}
