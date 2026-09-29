import React from 'react';
import PublicCanvasLayout from '../components/landing/PublicCanvasLayout';
import About3DVisual from '../components/landing/About3DVisual';
import { Sparkles, Heart, Lightbulb, ShieldCheck, Users } from 'lucide-react';

export default function AboutPage({ user, onOpenAuth }) {

  const values = [
    {
      title: 'Patient-Centered',
      desc: 'We put patients first in everything we build.',
      icon: Heart,
      color: 'text-rose-500',
      bgColor: 'bg-rose-50'
    },
    {
      title: 'Innovation',
      desc: 'We continuously innovate to solve real-world healthcare challenges.',
      icon: Lightbulb,
      color: 'text-amber-500',
      bgColor: 'bg-amber-50'
    },
    {
      title: 'Integrity',
      desc: 'We follow the highest standards of ethics and transparency.',
      icon: ShieldCheck,
      color: 'text-emerald-500',
      bgColor: 'bg-emerald-50'
    },
    {
      title: 'Collaboration',
      desc: 'We believe in the power of collaboration to drive meaningful change.',
      icon: Users,
      color: 'text-blue-500',
      bgColor: 'bg-blue-50'
    }
  ];

  const storyStats = [
    { label: 'Founded', val: '2024' },
    { label: 'Team Members', val: '20+' },
    { label: 'Data Points Analyzed', val: '1M+' },
    { label: 'Countries Reached', val: '5+' }
  ];

  return (
    <PublicCanvasLayout user={user} onOpenAuth={onOpenAuth}>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-16">
        
        {/* HERO & 3D HEART PEDESTAL */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          
          <div className="lg:col-span-7 space-y-6">
            <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-blue-50 border border-blue-200 text-blue-700 text-sm font-bold shadow-2xs">
              <Sparkles className="w-4 h-4 text-blue-600" />
              <span>About Us</span>
            </div>
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-[1.1]">
              Our Mission
            </h1>
            <p className="text-base sm:text-lg text-slate-600 font-medium leading-relaxed max-w-xl">
              To empower healthcare with AI-driven insights that are accurate, explainable and accessible for everyone.
            </p>
          </div>

          {/* 3D Visual */}
          <div className="lg:col-span-5 flex justify-center">
            <About3DVisual />
          </div>

        </div>

        {/* 4 CORE VALUE CARDS */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {values.map((val, idx) => {
            const Icon = val.icon;
            return (
              <div key={idx} className="p-7 rounded-3xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-sm hover:shadow-lg transition-all space-y-3">
                <div className={`p-3.5 rounded-2xl ${val.bgColor} ${val.color} w-fit`}>
                  <Icon className="w-6 h-6" />
                </div>
                <h3 className="text-lg font-extrabold text-slate-900">{val.title}</h3>
                <p className="text-sm text-slate-600 leading-relaxed font-medium">
                  {val.desc}
                </p>
              </div>
            );
          })}
        </div>

        {/* OUR STORY SECTION */}
        <div className="p-8 sm:p-12 rounded-3xl bg-white/95 backdrop-blur-md border border-slate-200/90 shadow-sm">
          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-center">
            <div className="md:col-span-6 space-y-4">
              <h2 className="text-2xl sm:text-3xl font-black text-slate-900">Our Story</h2>
              <p className="text-sm sm:text-base text-slate-600 leading-relaxed font-medium">
                TeleMed AI was founded by a team of doctors, data scientists and engineers with a shared vision to transform healthcare using the power of AI data and human expertise.
              </p>
            </div>
            <div className="md:col-span-6">
              <div className="rounded-2xl overflow-hidden shadow-xl border border-slate-200">
                <img
                  src="/assets/3d/about_team_doctors.jpg"
                  alt="TeleMed AI Team of Doctors and Data Scientists"
                  className="w-full h-56 sm:h-64 object-cover object-center"
                />
              </div>
            </div>
          </div>
        </div>

        {/* STATS BANNER */}
        <div className="p-8 sm:p-10 rounded-3xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 text-white shadow-2xl">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-6 text-center">
            {storyStats.map((st, idx) => (
              <div key={idx} className="space-y-1">
                <span className="text-3xl sm:text-4xl font-black font-mono block">{st.val}</span>
                <span className="text-xs sm:text-sm font-bold text-blue-100">{st.label}</span>
              </div>
            ))}
          </div>
        </div>

      </main>
    </PublicCanvasLayout>
  );
}
