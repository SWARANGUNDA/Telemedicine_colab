import React from 'react';
import { useNavigate } from 'react-router-dom';
import PublicCanvasLayout from '../components/landing/PublicCanvasLayout';
import Research3DVisual from '../components/landing/Research3DVisual';
import { Sparkles, Brain, Layers, Eye, Activity, ArrowRight } from 'lucide-react';

export default function ResearchPage({ user, onOpenAuth }) {
  const navigate = useNavigate();

  const metrics = [
    { label: 'Research Papers', val: '15+', sub: 'Published in reputed conferences & journals' },
    { label: 'Ongoing Studies', val: '8+', sub: 'Active research projects in healthcare AI' },
    { label: 'Collaborations', val: '3', sub: 'With leading hospitals and institutions' },
    { label: 'Patients Impacted', val: '10K+', sub: 'Through research and innovation' }
  ];

  const focusAreas = [
    {
      title: 'AI in Healthcare',
      desc: 'Predictive modeling, risk assessment',
      icon: Brain
    },
    {
      title: 'Multi-Modal Learning',
      desc: 'Clinical, wearable & microbiome data',
      icon: Layers
    },
    {
      title: 'Explainable AI',
      desc: 'Interpretable models for clinical trust',
      icon: Eye
    },
    {
      title: 'Real-World Impact',
      desc: 'Translating research into better healthcare',
      icon: Activity
    }
  ];

  return (
    <PublicCanvasLayout user={user} onOpenAuth={onOpenAuth}>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-16">
        
        {/* HEADER & 3D MICROSCOPE VISUAL */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-sm font-bold shadow-2xs">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span>Research</span>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-[1.1]">
              Advancing Healthcare <br />
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600">
                Through Research
              </span>
            </h1>
            <p className="text-base sm:text-lg text-slate-600 font-medium leading-relaxed max-w-xl">
              We are committed to advancing the field of AI in healthcare through cutting-edge research and real-world impact.
            </p>
          </div>

          {/* 3D Visual */}
          <div className="lg:col-span-5 flex justify-center">
            <Research3DVisual />
          </div>

        </div>

        {/* METRICS GRID */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-5">
          {metrics.map((m, i) => (
            <div key={i} className="p-7 rounded-3xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-[0_10px_30px_rgba(15,23,42,0.04)] text-center space-y-1.5">
              <span className="text-4xl sm:text-5xl font-black text-blue-600 font-mono block">{m.val}</span>
              <h4 className="text-sm sm:text-base font-extrabold text-slate-900">{m.label}</h4>
              <p className="text-xs sm:text-sm text-slate-500 font-medium">{m.sub}</p>
            </div>
          ))}
        </div>

        {/* RESEARCH FOCUS SECTION */}
        <div className="space-y-8">
          <h2 className="text-2xl sm:text-3xl font-black text-slate-900">Our Research Focus</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {focusAreas.map((area, idx) => {
              const Icon = area.icon;
              return (
                <div key={idx} className="p-7 rounded-3xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-sm hover:shadow-lg transition-all space-y-3">
                  <div className="p-3.5 rounded-2xl bg-blue-50 text-blue-600 w-fit">
                    <Icon className="w-6 h-6" />
                  </div>
                  <h3 className="text-lg font-extrabold text-slate-900">{area.title}</h3>
                  <p className="text-sm text-slate-600 leading-relaxed font-medium">
                    {area.desc}
                  </p>
                </div>
              );
            })}
          </div>
        </div>

        {/* COLLABORATION CTA BANNER */}
        <div className="p-8 sm:p-12 rounded-3xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-2xl flex flex-col sm:flex-row items-center justify-between gap-6">
          <div className="space-y-2 text-center sm:text-left">
            <h3 className="text-2xl sm:text-3xl font-black tracking-tight">Interested in collaborating with us?</h3>
            <p className="text-sm sm:text-base text-blue-100 font-medium">We partner with researchers, hospitals and innovators worldwide.</p>
          </div>
          <button
            onClick={() => navigate('/contact')}
            className="px-8 py-4 rounded-full bg-white text-blue-700 hover:bg-blue-50 font-extrabold text-sm sm:text-base shadow-xl hover:scale-105 transition-all shrink-0 flex items-center gap-2.5 cursor-pointer"
          >
            <span>Contact Us</span>
            <ArrowRight className="w-5 h-5" />
          </button>
        </div>

      </main>
    </PublicCanvasLayout>
  );
}
