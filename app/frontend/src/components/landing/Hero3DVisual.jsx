import React from 'react';

export default function Hero3DVisual() {
  return (
    <div className="relative w-full max-w-[560px] aspect-square mx-auto flex items-center justify-center select-none py-2 group">
      {/* Background Soft Glow */}
      <div className="absolute inset-0 bg-gradient-to-tr from-blue-400/20 via-indigo-300/20 to-purple-400/20 rounded-full blur-3xl transform -rotate-6 scale-95 pointer-events-none" />
      <div className="absolute w-72 h-72 bg-cyan-400/20 rounded-full blur-2xl top-1/4 left-1/4 animate-pulse pointer-events-none" />

      {/* 3D Visual Asset Card Frame */}
      <div className="relative w-full h-full rounded-3xl overflow-hidden border border-white/80 shadow-[0_25px_60px_rgba(59,130,246,0.18)] transition-all duration-500 group-hover:scale-[1.02] group-hover:shadow-[0_30px_70px_rgba(79,70,229,0.25)]">
        <img
          src="/assets/3d/hero_3d_ai_pedestal.jpg"
          alt="TeleMed AI 3D Core Pedestal"
          className="w-full h-full object-cover object-center rounded-3xl"
        />
        {/* Subtle Glass Reflection Overlay */}
        <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-white/20 pointer-events-none rounded-3xl" />
      </div>
    </div>
  );
}
