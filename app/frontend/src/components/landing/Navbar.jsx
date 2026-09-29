import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { Heart, Lock, ArrowRight, Menu, X } from 'lucide-react';

export default function Navbar({ user, onOpenAuth }) {
  const location = useLocation();
  const navigate = useNavigate();
  const [scrolled, setScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const navLinks = [
    { name: 'Features', path: '/features' },
    { name: 'How It Works', path: '/how-it-works' },
    { name: 'Research', path: '/research' },
    { name: 'About', path: '/about' },
    { name: 'Contact', path: '/contact' },
  ];

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

  const handleLogin = () => {
    if (user) {
      const dashboardPath = user.role === 'ADMIN' ? '/admin/dashboard' : user.role === 'DOCTOR' ? '/doctor/dashboard' : '/dashboard';
      navigate(dashboardPath);
    } else if (onOpenAuth) {
      onOpenAuth('login');
    } else {
      navigate('/login');
    }
  };

  return (
    <header className={`sticky top-0 z-50 transition-all duration-300 ${scrolled ? 'bg-white/85 backdrop-blur-md shadow-sm border-b border-slate-200/60 py-3' : 'bg-transparent py-4'}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex items-center justify-between">
        
        {/* LOGO + TAGLINE */}
        <Link to="/" className="flex items-center gap-3 group">
          <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 p-0.5 shadow-md shadow-blue-500/20 group-hover:scale-105 transition-transform">
            <div className="w-full h-full bg-white rounded-[14px] flex items-center justify-center text-blue-600">
              <Heart className="w-5 h-5 fill-blue-600 text-blue-600" />
            </div>
          </div>
          <div>
            <span className="text-lg font-black text-slate-900 tracking-tight block leading-none">TeleMed AI</span>
            <span className="text-[10px] font-bold text-slate-400 tracking-wider">AI-Powered. Patient-Centered.</span>
          </div>
        </Link>

        {/* DESKTOP NAV LINKS */}
        <nav className="hidden md:flex items-center gap-8">
          {navLinks.map((link) => {
            const isActive = location.pathname === link.path;
            return (
              <Link
                key={link.path}
                to={link.path}
                className={`text-sm font-bold transition-colors ${isActive ? 'text-blue-600 font-extrabold' : 'text-slate-700 hover:text-slate-900'}`}
              >
                {link.name}
              </Link>
            );
          })}
        </nav>

        {/* RIGHT ACTION BUTTONS */}
        <div className="hidden md:flex items-center gap-3.5">
          {user ? (
            <button
              onClick={handleGetStarted}
              className="px-6 py-2.5 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-extrabold text-sm shadow-md shadow-blue-500/20 hover:shadow-lg transition-all flex items-center gap-2 cursor-pointer"
            >
              <span>Go to Portal</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          ) : (
            <>
              <button
                onClick={handleLogin}
                className="px-5 py-2.5 rounded-full border border-slate-200/80 hover:border-slate-300 bg-white/70 hover:bg-white text-slate-800 font-bold text-sm shadow-2xs transition-all flex items-center gap-2 cursor-pointer"
              >
                <Lock className="w-4 h-4 text-slate-400" />
                <span>Log In</span>
              </button>
              <button
                onClick={handleGetStarted}
                className="px-6 py-2.5 rounded-full bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white font-extrabold text-sm shadow-md shadow-blue-500/20 hover:shadow-lg hover:scale-[1.02] transition-all flex items-center gap-2 cursor-pointer"
              >
                <span>Get Started</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </>
          )}
        </div>

        {/* MOBILE MENU BUTTON */}
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="md:hidden p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100/60"
        >
          {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>

      </div>

      {/* MOBILE MENU DROPDOWN */}
      {mobileMenuOpen && (
        <div className="md:hidden bg-white/95 backdrop-blur-lg border-b border-slate-200 px-4 pt-3 pb-6 space-y-3 shadow-xl">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              onClick={() => setMobileMenuOpen(false)}
              className="block text-sm font-bold text-slate-700 hover:text-blue-600 py-1.5"
            >
              {link.name}
            </Link>
          ))}
          <div className="pt-3 border-t border-slate-100 flex flex-col gap-2.5">
            <button
              onClick={() => { setMobileMenuOpen(false); handleLogin(); }}
              className="w-full py-2.5 rounded-xl border border-slate-200 text-slate-700 font-bold text-xs flex items-center justify-center gap-2"
            >
              <Lock className="w-3.5 h-3.5 text-slate-400" />
              <span>Log In</span>
            </button>
            <button
              onClick={() => { setMobileMenuOpen(false); handleGetStarted(); }}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-bold text-xs flex items-center justify-center gap-2"
            >
              <span>Get Started</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      )}
    </header>
  );
}
