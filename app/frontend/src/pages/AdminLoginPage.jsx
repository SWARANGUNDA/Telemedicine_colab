import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Shield, Lock, Mail, ArrowRight, Eye, EyeOff, KeyRound, AlertTriangle, ChevronLeft } from 'lucide-react';
import { loginUser } from '../api/client';

export default function AdminLoginPage({ onLogin, onLoginSuccess, user }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const navigate = useNavigate();

  useEffect(() => {
    if (user && user.role === 'ADMIN') {
      navigate('/admin/dashboard', { replace: true });
    }
  }, [user, navigate]);

  const handleAdminLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);

    try {
      let authenticatedUser = null;
      if (onLogin) {
        authenticatedUser = await onLogin(email.trim(), password, 'ADMIN');
      } else {
        const data = await loginUser(email.trim(), password, 'ADMIN');
        authenticatedUser = data.user || data;
        if (data.refresh_token) {
          try { sessionStorage.setItem('telemed_refresh_token', data.refresh_token); } catch (e) {}
        }
        if (onLoginSuccess) {
          onLoginSuccess(authenticatedUser);
        }
      }

      if (authenticatedUser) {
        navigate('/admin/dashboard', { replace: true });
      }
    } catch (err) {
      setErrorMsg(err.message || 'Administrative authentication failed. Verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-slate-100/50 to-slate-50 text-slate-900 flex flex-col justify-between selection:bg-indigo-600 selection:text-white relative overflow-hidden">
      
      {/* Ambient Lighting Background */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-full max-w-7xl h-[380px] bg-gradient-to-b from-indigo-100/50 via-blue-50/30 to-transparent blur-3xl pointer-events-none" />
      <div className="absolute top-[-5%] right-[-5%] w-[450px] h-[450px] bg-blue-400/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-[-5%] left-[-5%] w-[450px] h-[450px] bg-purple-400/10 rounded-full blur-[100px] pointer-events-none" />

      {/* Top Navbar */}
      <header className="relative z-10 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-5 flex items-center justify-between">
        <Link 
          to="/login"
          className="inline-flex items-center gap-2 text-xs font-bold text-slate-600 hover:text-slate-900 transition-colors bg-white/90 border border-slate-200/90 hover:border-slate-300 px-3 py-1.5 rounded-xl shadow-2xs backdrop-blur-md"
        >
          <ChevronLeft className="w-4 h-4" />
          <span>Patient & Doctor Portal</span>
        </Link>

        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-50/90 border border-indigo-200/80 text-indigo-700 text-xs font-extrabold tracking-wider uppercase shadow-2xs">
          <span className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse" />
          <span>Restricted Gateway</span>
        </div>
      </header>

      {/* Main Command Center Container */}
      <main className="relative z-10 flex-1 flex items-center justify-center px-4 py-8">
        <div className="w-full max-w-md space-y-6">

          {/* Secure Header & Badge */}
          <div className="text-center space-y-2.5">
            <div className="relative inline-block">
              <div className="w-14 h-14 rounded-2xl bg-gradient-to-br from-indigo-600 via-indigo-700 to-purple-700 shadow-xl shadow-indigo-500/25 flex items-center justify-center mx-auto text-white">
                <Shield className="w-7 h-7" />
              </div>
              <div className="absolute -bottom-1 -right-1 w-5 h-5 rounded-full bg-emerald-500 border-2 border-white flex items-center justify-center shadow-xs">
                <KeyRound className="w-3 h-3 text-white" />
              </div>
            </div>

            <h1 className="text-2xl sm:text-3xl font-black tracking-tight text-slate-900">
              Administrator Portal
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 max-w-xs mx-auto font-medium leading-relaxed">
              Authenticate with administrative credentials to access platform infrastructure and audit controls.
            </p>
          </div>

          {/* Login Card */}
          <div className="bg-white border border-slate-200/90 rounded-3xl p-6 sm:p-7 shadow-[0_20px_50px_rgba(15,23,42,0.06)] space-y-4">
            
            {user && user.role !== 'ADMIN' && (
              <div className="p-3 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 text-xs font-semibold flex items-start gap-2.5">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  Currently signed in as <span className="font-black text-slate-900">{user.email}</span> ({user.role}). Sign in below with an Administrator account to access the Command Center.
                </div>
              </div>
            )}

            {errorMsg && (
              <div className="p-3 rounded-2xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold leading-relaxed">
                {errorMsg}
              </div>
            )}

            <form onSubmit={handleAdminLogin} autoComplete="off" className="space-y-4 text-left">
              
              {/* Admin Email */}
              <div className="space-y-1">
                <label className="text-xs font-extrabold text-slate-700">
                  Administrator Email
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                  <input
                    type="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter administrator email"
                    autoComplete="off"
                    className="w-full pl-10 pr-4 py-3 rounded-xl bg-slate-50/70 border border-slate-200 text-sm text-slate-900 placeholder:text-slate-400 font-medium focus:bg-white focus:outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 transition-all"
                  />
                </div>
              </div>

              {/* Admin Password */}
              <div className="space-y-1">
                <label className="text-xs font-extrabold text-slate-700">
                  Security Key / Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3.5" />
                  <input
                    type={showPassword ? 'text' : 'password'}
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter password"
                    autoComplete="new-password"
                    className="w-full pl-10 pr-10 py-3 rounded-xl bg-slate-50/70 border border-slate-200 text-sm text-slate-900 placeholder:text-slate-400 font-medium focus:bg-white focus:outline-none focus:border-indigo-600 focus:ring-2 focus:ring-indigo-500/20 transition-all"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3.5 top-3.5 text-slate-400 hover:text-slate-600 cursor-pointer"
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={loading}
                className="w-full py-3.5 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-extrabold text-sm shadow-md shadow-indigo-500/20 hover:shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-75"
              >
                {loading ? (
                  <span>Authorizing System Session...</span>
                ) : (
                  <>
                    <span>Enter Command Center</span>
                    <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </form>

          </div>

          {/* Security Compliance Footer */}
          <div className="text-center text-[11px] text-slate-400 font-medium space-y-1">
            <p>Protected by TeleMed AI Multi-Factor RBAC Architecture</p>
            <p className="text-slate-400/80">All administrative sessions are cryptographically logged for HIPAA compliance.</p>
          </div>

        </div>
      </main>

      {/* Bottom Footer bar */}
      <footer className="relative z-10 py-4 text-center text-xs text-slate-400 border-t border-slate-200/80">
        TeleMed AI • Enterprise Healthcare Infrastructure
      </footer>

    </div>
  );
}
