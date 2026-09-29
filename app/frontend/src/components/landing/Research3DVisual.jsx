import React from 'react';

export default function Research3DVisual() {
  return (
    <div className="relative w-full max-w-[460px] aspect-square mx-auto flex items-center justify-center select-none py-2 group">
      {/* Background Soft Glow */}
      <div className="absolute inset-0 bg-gradient-to-tr from-blue-300/20 via-purple-300/20 to-indigo-300/20 rounded-full blur-3xl pointer-events-none" />

      {/* 3D Visual Asset Card Frame */}
      <div className="relative w-full h-full rounded-3xl overflow-hidden border border-white/80 shadow-[0_20px_50px_rgba(59,130,246,0.15)] transition-all duration-500 group-hover:scale-[1.02] group-hover:shadow-[0_25px_60px_rgba(139,92,246,0.22)]">
        <img
          src="/assets/3d/research_3d_microscope.jpg"
          alt="3D Scientific Microscope Artwork"
          className="w-full h-full object-cover object-center rounded-3xl"
        />
        {/* Glass Overlay */}
        <div className="absolute inset-0 bg-gradient-to-tr from-transparent via-white/5 to-white/20 pointer-events-none rounded-3xl" />
      </div>
    </div>
  );
}
