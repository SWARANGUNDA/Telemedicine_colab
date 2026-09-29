import React from 'react';
import { Link } from 'react-router-dom';
import { Heart, ShieldCheck, Globe, Share2, Code } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-300 pt-14 pb-8 border-t border-slate-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-10">
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          
          {/* Col 1: Brand */}
          <div className="space-y-3 md:col-span-1">
            <Link to="/" className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-500 to-indigo-500 p-0.5 shadow-md flex items-center justify-center">
                <div className="w-full h-full bg-slate-900 rounded-[10px] flex items-center justify-center text-blue-400">
                  <Heart className="w-4 h-4 fill-blue-400" />
                </div>
              </div>
              <div>
                <span className="text-base font-black text-white tracking-tight block leading-none">TeleMed AI</span>
                <span className="text-[9.5px] font-bold text-slate-400 tracking-wider">AI-Powered. Patient-Centered.</span>
              </div>
            </Link>
            <p className="text-xs text-slate-400 leading-relaxed pt-1">
              Combining clinical data, wearable insights, and gut microbiome analysis for personalized precision healthcare.
            </p>
          </div>

          {/* Col 2: Navigation Links */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-black text-white uppercase tracking-wider">Platform Nav</h4>
            <ul className="space-y-1.5 text-xs text-slate-400 font-medium">
              <li><Link to="/features" className="hover:text-blue-400 transition-colors">Features</Link></li>
              <li><Link to="/how-it-works" className="hover:text-blue-400 transition-colors">How It Works</Link></li>
              <li><Link to="/research" className="hover:text-blue-400 transition-colors">Research</Link></li>
              <li><Link to="/about" className="hover:text-blue-400 transition-colors">About Us</Link></li>
              <li><Link to="/contact" className="hover:text-blue-400 transition-colors">Contact Support</Link></li>
            </ul>
          </div>

          {/* Col 3: Portals & Access */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-black text-white uppercase tracking-wider">Portals & Workspaces</h4>
            <ul className="space-y-1.5 text-xs text-slate-400 font-medium">
              <li><Link to="/login" className="hover:text-blue-400 transition-colors">Patient Portal Sign In</Link></li>
              <li><Link to="/login" className="hover:text-blue-400 transition-colors">Doctor Clinical Portal</Link></li>
              <li><Link to="/login" className="hover:text-blue-400 transition-colors">Admin Governance</Link></li>
              <li><Link to="/register" className="hover:text-blue-400 transition-colors">Create Account</Link></li>
            </ul>
          </div>

          {/* Col 4: Trust & Compliance */}
          <div className="space-y-3">
            <h4 className="text-xs font-black text-white uppercase tracking-wider">Security & Privacy</h4>
            <div className="p-3 rounded-xl bg-slate-800/60 border border-slate-700/60 space-y-1.5">
              <div className="flex items-center gap-2 text-xs font-bold text-slate-200">
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
                <span>Privacy-First Architecture</span>
              </div>
              <p className="text-[10.5px] text-slate-400 leading-snug">
                Your medical data is encrypted and protected with enterprise-grade security protocols.
              </p>
            </div>
          </div>

        </div>

        {/* Bottom Bar */}
        <div className="pt-6 border-t border-slate-800/80 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-slate-500 font-medium">
          <p>© {new Date().getFullYear()} TeleMed AI. All rights reserved.</p>
          <div className="flex items-center gap-4">
            <a href="https://github.com/SWARANGUNDA/TeleMed" target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors"><Code className="w-4 h-4" /></a>
            <a href="#" className="hover:text-white transition-colors"><Globe className="w-4 h-4" /></a>
            <a href="#" className="hover:text-white transition-colors"><Share2 className="w-4 h-4" /></a>
          </div>
        </div>

      </div>
    </footer>
  );
}
