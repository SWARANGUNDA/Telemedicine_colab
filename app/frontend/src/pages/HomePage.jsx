import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import PublicCanvasLayout from '../components/landing/PublicCanvasLayout';
import Hero3DVisual from '../components/landing/Hero3DVisual';
import { ArrowRight, ShieldCheck, Stethoscope, Brain, Lock, Layers, Sparkles, UserCheck, Play } from 'lucide-react';

export default function HomePage({ user, onOpenAuth }) {
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

  return (
    <PublicCanvasLayout user={user} onOpenAuth={onOpenAuth}>
      <main className="space-y-16 pb-16 pt-4">
        
        {/* HERO SECTION */}
        <section className="relative pt-4 md:pt-8 pb-8">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
              
              {/* LEFT COLUMN: Text & CTAs */}
              <div className="lg:col-span-7 space-y-6 text-left z-10">
                
                {/* Top Badge */}
                <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50/90 border border-blue-200/80 text-blue-700 text-xs font-bold shadow-2xs">
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                  <span>AI-Powered Telemedicine Platform</span>
                </div>

                {/* Headline */}
                <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-[1.08]">
                  Smarter Insights. <br className="hidden sm:inline" />
                  Better Health. <br />
                  <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600">
                    Powered by AI.
                  </span>
                </h1>

                {/* Description */}
                <p className="text-base sm:text-lg text-slate-600 max-w-xl leading-relaxed font-medium">
                  TeleMed AI combines clinical data, wearable insights, and gut microbiome analysis to deliver personalized health insights and intelligent clinical decision support.
                </p>

                {/* CTAs */}
                <div className="flex flex-wrap items-center gap-4 pt-2">
                  <button
                    onClick={handleGetStarted}
                    className="px-7 py-3.5 rounded-full bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-extrabold text-xs sm:text-sm shadow-xl shadow-blue-500/25 hover:shadow-2xl hover:scale-[1.02] transition-all flex items-center gap-2.5 cursor-pointer group"
                  >
                    <span>Get Started</span>
                    <ArrowRight className="w-4 h-4 transition-transform group-hover:translate-x-1" />
                  </button>

                  <Link
                    to="/features"
                    className="px-6 py-3.5 rounded-full bg-white/90 hover:bg-white border border-slate-200 text-slate-800 font-extrabold text-xs sm:text-sm shadow-sm hover:shadow transition-all flex items-center gap-2 cursor-pointer"
                  >
                    <Play className="w-3.5 h-3.5 fill-slate-700 text-slate-700" />
                    <span>Explore Platform</span>
                  </Link>
                </div>

                {/* Trust Badges */}
                <div className="flex flex-wrap items-center gap-6 pt-4 text-xs font-bold text-slate-600">
                  <div className="flex items-center gap-1.5">
                    <ShieldCheck className="w-4 h-4 text-blue-600" />
                    <span>Secure & Private</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Stethoscope className="w-4 h-4 text-indigo-600" />
                    <span>Clinically Trusted</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Brain className="w-4 h-4 text-purple-600" />
                    <span>AI-Powered Insights</span>
                  </div>
                </div>

              </div>

              {/* RIGHT COLUMN: 3D Visual */}
              <div className="lg:col-span-5 flex justify-center z-10">
                <Hero3DVisual />
              </div>

            </div>
          </div>
        </section>

        {/* BOTTOM VALUE BAR (4 Cards) */}
        <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
            
            {/* Card 1 */}
            <div className="p-6 rounded-3xl bg-white/90 backdrop-blur-md border border-slate-200/80 shadow-[0_10px_30px_rgba(15,23,42,0.04)] hover:shadow-xl hover:-translate-y-1 transition-all space-y-3">
              <div className="p-3.5 rounded-2xl bg-purple-50 text-purple-600 w-fit">
                <Lock className="w-6 h-6" />
              </div>
              <h3 className="text-base font-extrabold text-slate-900">End-to-End Security</h3>
              <p className="text-xs text-slate-500 leading-relaxed font-medium">
                Your data is encrypted and protected with enterprise-grade security.
              </p>
            </div>

            {/* Card 2 */}
            <div className="p-6 rounded-3xl bg-white/90 backdrop-blur-md border border-slate-200/80 shadow-[0_10px_30px_rgba(15,23,42,0.04)] hover:shadow-xl hover:-translate-y-1 transition-all space-y-3">
              <div className="p-3.5 rounded-2xl bg-teal-50 text-teal-600 w-fit">
                <Layers className="w-6 h-6" />
              </div>
              <h3 className="text-base font-extrabold text-slate-900">Multi-Modal Analysis</h3>
              <p className="text-xs text-slate-500 leading-relaxed font-medium">
                Combining clinical, wearable and microbiome data for deeper understanding.
              </p>
            </div>

            {/* Card 3 */}
            <div className="p-6 rounded-3xl bg-white/90 backdrop-blur-md border border-slate-200/80 shadow-[0_10px_30px_rgba(15,23,42,0.04)] hover:shadow-xl hover:-translate-y-1 transition-all space-y-3">
              <div className="p-3.5 rounded-2xl bg-blue-50 text-blue-600 w-fit">
                <Brain className="w-6 h-6" />
              </div>
              <h3 className="text-base font-extrabold text-slate-900">AI-Driven Insights</h3>
              <p className="text-xs text-slate-500 leading-relaxed font-medium">
                Advanced AI models provide accurate predictions and actionable recommendations.
              </p>
            </div>

            {/* Card 4 */}
            <div className="p-6 rounded-3xl bg-white/90 backdrop-blur-md border border-slate-200/80 shadow-[0_10px_30px_rgba(15,23,42,0.04)] hover:shadow-xl hover:-translate-y-1 transition-all space-y-3">
              <div className="p-3.5 rounded-2xl bg-pink-50 text-pink-600 w-fit">
                <UserCheck className="w-6 h-6" />
              </div>
              <h3 className="text-base font-extrabold text-slate-900">Built for Healthcare</h3>
              <p className="text-xs text-slate-500 leading-relaxed font-medium">
                Designed for clinicians, researchers and healthcare innovators.
              </p>
            </div>

          </div>
        </section>

      </main>
    </PublicCanvasLayout>
  );
}
