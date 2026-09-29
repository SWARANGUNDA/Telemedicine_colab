import React from 'react';
import Navbar from './Navbar';
import Footer from './Footer';

export default function PublicCanvasLayout({ children, user, onOpenAuth, hideFooter = false }) {
  return (
    <div className="min-h-screen bg-[#eef2f9] p-2 sm:p-4 md:p-6 font-sans antialiased text-slate-900 selection:bg-blue-600 selection:text-white">
      {/* Outer App Canvas Frame matching prelogin pages */}
      <div className="max-w-[1400px] mx-auto rounded-[28px] sm:rounded-[36px] bg-gradient-to-b from-slate-50 via-indigo-50/20 to-slate-50 border border-slate-200/90 shadow-[0_20px_70px_rgba(15,23,42,0.07)] overflow-hidden min-h-[92vh] flex flex-col justify-between">
        
        <div>
          <Navbar user={user} onOpenAuth={onOpenAuth} />
          <div>
            {children}
          </div>
        </div>

        {!hideFooter && <Footer />}
      </div>
    </div>
  );
}
