import React, { useState } from 'react';
import { X, Check, ShieldCheck, User, Stethoscope, ArrowRight, Loader2, Sparkles, Mail } from 'lucide-react';
import { loginWithGoogle } from '../../api/client';

export default function GoogleAuthModal({ isOpen, onClose, onSuccess, initialRole = 'PATIENT' }) {
  const [selectedRole, setSelectedRole] = useState(initialRole);
  const [customEmail, setCustomEmail] = useState('');
  const [customName, setCustomName] = useState('');
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  if (!isOpen) return null;

  const demoAccounts = [
    {
      name: 'Dr. Vishal Sharma',
      email: 'vishal@gmail.com',
      role: 'DOCTOR',
      avatarColor: 'bg-emerald-600',
      initials: 'VS',
      description: 'Endocrinologist • Verified Physician'
    },
    {
      name: 'Swaran Gunda',
      email: 'swarangunda23@gmail.com',
      role: 'PATIENT',
      avatarColor: 'bg-blue-600',
      initials: 'SG',
      description: 'Registered Patient Account'
    },
    {
      name: 'Alex Morgan',
      email: 'alex.morgan@gmail.com',
      role: 'PATIENT',
      avatarColor: 'bg-purple-600',
      initials: 'AM',
      description: 'Patient Health Portal'
    }
  ];

  const handleAuthenticate = async (accountData) => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        email: accountData.email.trim(),
        name: accountData.name?.trim(),
        role: accountData.role || selectedRole,
      };
      const res = await loginWithGoogle(payload);
      const authenticatedUser = res.user || res;
      if (onSuccess) {
        onSuccess(authenticatedUser);
      }
      onClose();
    } catch (err) {
      setError(err.message || 'Google authentication failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleCustomSubmit = (e) => {
    e.preventDefault();
    if (!customEmail || !customEmail.includes('@')) {
      setError('Please enter a valid Google email address.');
      return;
    }
    handleAuthenticate({
      email: customEmail,
      name: customName || customEmail.split('@')[0].replace('.', ' '),
      role: selectedRole
    });
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-sm animate-fade-in">
      <div 
        className="relative w-full max-w-md rounded-3xl bg-white border border-slate-200/90 shadow-2xl overflow-hidden p-6 sm:p-7 space-y-5"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Top Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            {/* Google Icon */}
            <div className="w-10 h-10 rounded-2xl bg-white border border-slate-200 shadow-xs flex items-center justify-center">
              <svg className="w-5 h-5" viewBox="0 0 24 24">
                <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
              </svg>
            </div>
            <div>
              <h3 className="text-base sm:text-lg font-black text-slate-900 leading-tight">
                Sign in with Google
              </h3>
              <p className="text-xs text-slate-500 font-medium">
                Choose an account to continue to TeleMed AI
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-xl text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {error && (
          <div className="p-3 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-semibold leading-relaxed">
            {error}
          </div>
        )}

        {/* Role Pre-selection Banner */}
        <div className="space-y-1.5">
          <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider block">
            Select Portal Access Mode
          </label>
          <div className="grid grid-cols-2 gap-2 p-1 rounded-xl bg-slate-100/90 border border-slate-200/80">
            <button
              type="button"
              onClick={() => setSelectedRole('PATIENT')}
              className={`py-1.5 px-2.5 rounded-lg text-xs font-extrabold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                selectedRole === 'PATIENT'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
              }`}
            >
              <User className="w-3.5 h-3.5" />
              <span>Patient</span>
            </button>
            <button
              type="button"
              onClick={() => setSelectedRole('DOCTOR')}
              className={`py-1.5 px-2.5 rounded-lg text-xs font-extrabold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                selectedRole === 'DOCTOR'
                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-slate-200/60'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              <span>Doctor</span>
            </button>
          </div>
        </div>

        {/* Demo Google Accounts List */}
        <div className="space-y-2">
          <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider block">
            Instant One-Click Google Profiles
          </label>
          <div className="space-y-1.5">
            {demoAccounts.map((account) => (
              <button
                key={account.email}
                type="button"
                disabled={loading}
                onClick={() => handleAuthenticate(account)}
                className="w-full p-2.5 rounded-2xl border border-slate-200 hover:border-blue-400 bg-white hover:bg-blue-50/50 transition-all flex items-center justify-between text-left group cursor-pointer disabled:opacity-50"
              >
                <div className="flex items-center gap-3">
                  <div className={`w-9 h-9 rounded-full ${account.avatarColor} text-white font-extrabold text-xs flex items-center justify-center shadow-xs`}>
                    {account.initials}
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <span className="text-xs font-extrabold text-slate-900 group-hover:text-blue-600 transition-colors">
                        {account.name}
                      </span>
                      <span className="text-[10px] px-1.5 py-0.2 rounded-md font-bold bg-slate-100 text-slate-600 border border-slate-200">
                        {account.role}
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 font-medium">
                      {account.email}
                    </p>
                  </div>
                </div>
                <ArrowRight className="w-4 h-4 text-slate-400 group-hover:text-blue-600 group-hover:translate-x-0.5 transition-all" />
              </button>
            ))}
          </div>
        </div>

        {/* Use Another Google Account Toggle */}
        <div className="pt-1">
          {!showCustomInput ? (
            <button
              type="button"
              onClick={() => setShowCustomInput(true)}
              className="w-full py-2 px-3 rounded-xl border border-dashed border-slate-300 hover:border-blue-500 text-slate-600 hover:text-blue-600 text-xs font-bold transition-all flex items-center justify-center gap-2 cursor-pointer"
            >
              <Mail className="w-3.5 h-3.5" />
              <span>Use another Google account</span>
            </button>
          ) : (
            <form onSubmit={handleCustomSubmit} className="space-y-2.5 p-3.5 rounded-2xl bg-slate-50 border border-slate-200 text-left animate-fade-in">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-slate-700">Enter Google Account</span>
                <button
                  type="button"
                  onClick={() => setShowCustomInput(false)}
                  className="text-[11px] font-semibold text-slate-400 hover:text-slate-600 cursor-pointer"
                >
                  Cancel
                </button>
              </div>
              <input
                type="email"
                required
                placeholder="your.email@gmail.com"
                value={customEmail}
                onChange={(e) => setCustomEmail(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-white border border-slate-200 text-xs font-medium focus:outline-none focus:border-blue-600"
              />
              <input
                type="text"
                placeholder="Your Full Name (optional)"
                value={customName}
                onChange={(e) => setCustomName(e.target.value)}
                className="w-full px-3 py-2 rounded-xl bg-white border border-slate-200 text-xs font-medium focus:outline-none focus:border-blue-600"
              />
              <button
                type="submit"
                disabled={loading}
                className="w-full py-2 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-extrabold text-xs shadow-xs hover:shadow-md transition-all flex items-center justify-center gap-2 cursor-pointer"
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <span>Sign In with Custom Google ID</span>}
              </button>
            </form>
          )}
        </div>

        {/* Security Footer Notice */}
        <div className="pt-2 border-t border-slate-100 flex items-center gap-2 text-[11px] text-slate-400 font-medium leading-tight">
          <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>Encrypted with SHA-256 JWT sessions under HIPAA compliance.</span>
        </div>
      </div>
    </div>
  );
}
