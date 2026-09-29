import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import PublicCanvasLayout from '../components/landing/PublicCanvasLayout';
import { Activity, User, Mail, Lock, ArrowRight, ShieldCheck, Briefcase, Hash, Eye, EyeOff, Check, Sparkles, TrendingUp, Users } from 'lucide-react';
import { registerPatient, registerDoctor } from '../api/client';
import GoogleAuthModal from '../components/auth/GoogleAuthModal';

export default function RegisterPage({ onLoginSuccess, user, onOpenAuth }) {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [role, setRole] = useState('PATIENT');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [isGoogleModalOpen, setIsGoogleModalOpen] = useState(false);

  // Doctor-specific fields
  const [specialization, setSpecialization] = useState('');
  const [registrationNumber, setRegistrationNumber] = useState('');

  const navigate = useNavigate();

  useEffect(() => {
    if (user) {
      const dashPath = user.role === 'ADMIN' ? '/admin/dashboard' : user.role === 'DOCTOR' ? '/doctor/dashboard' : '/dashboard';
      navigate(dashPath, { replace: true });
    }
  }, [user, navigate]);

  // Password strength validation
  const hasMinLength = password.length >= 8;
  const hasNumber = /\d/.test(password);
  const hasSpecial = /[!@#$%^&*(),.?":{}|<>]/.test(password);

  const handleRegisterSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setErrorMsg(null);

    try {
      let res;
      if (role === 'DOCTOR') {
        if (!specialization.trim()) {
          throw new Error('Specialization is required for doctor registration.');
        }
        if (!registrationNumber.trim()) {
          throw new Error('Medical registration number is required.');
        }
        res = await registerDoctor({
          email: email.trim(),
          password,
          full_name: fullName.trim(),
          specialization: specialization.trim(),
          registration_number: registrationNumber.trim(),
        });
      } else {
        res = await registerPatient({
          email: email.trim(),
          password,
          full_name: fullName.trim(),
        });
      }

      const registeredUser = res.user || res;

      if (onLoginSuccess) {
        onLoginSuccess(registeredUser);
      } else {
        const dashPath = role === 'DOCTOR' ? '/doctor/dashboard' : '/intake';
        navigate(dashPath);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Registration failed. Please check your information.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleAuth = () => {
    setIsGoogleModalOpen(true);
  };

  const handleGoogleSuccess = (authenticatedUser) => {
    if (onLoginSuccess) {
      onLoginSuccess(authenticatedUser);
    } else {
      const dashPath = authenticatedUser.role === 'ADMIN' ? '/admin/dashboard' : authenticatedUser.role === 'DOCTOR' ? '/doctor/dashboard' : '/dashboard';
      navigate(dashPath);
    }
  };

  return (
    <PublicCanvasLayout user={user} onOpenAuth={onOpenAuth} hideFooter={true}>
      <main className="px-4 sm:px-6 lg:px-8 py-2 sm:py-3 flex items-center justify-center min-h-[calc(100vh-6rem)]">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 lg:gap-8 items-center w-full max-w-7xl mx-auto">
          
          {/* LEFT COLUMN: Benefits & Stunning 16:9 3D Hologram Stage */}
          <div className="lg:col-span-7 grid grid-cols-1 md:grid-cols-12 gap-5 items-center hidden md:grid">
            
            {/* Copy & Benefits Left Side */}
            <div className="md:col-span-6 space-y-3 text-left">
              
              {/* Pill Badge */}
              <div>
                <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-blue-50/90 border border-blue-200/80 text-blue-600 text-xs font-bold shadow-2xs">
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                  <span>Join TeleMed AI</span>
                </div>
              </div>

              {/* Headline */}
              <h1 className="text-3xl sm:text-4xl lg:text-[42px] font-black text-slate-900 tracking-tight leading-tight">
                Create Your <br />
                Account
              </h1>

              {/* Subtitle */}
              <p className="text-xs sm:text-sm text-slate-600 font-medium leading-relaxed max-w-xs">
                Get started with AI-powered insights for smarter health decisions.
              </p>

              {/* 3 WHITE BENEFIT CARDS matching Reference Screenshot */}
              <div className="space-y-2.5 pt-0.5">
                <div className="p-3 rounded-2xl bg-white border border-slate-200/80 shadow-2xs flex items-start gap-3">
                  <div className="p-2 rounded-xl bg-blue-50 text-blue-600 shrink-0">
                    <ShieldCheck className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs sm:text-sm font-extrabold text-slate-900">Secure & Private</h4>
                    <p className="text-[11px] text-slate-500 font-medium leading-tight mt-0.5">
                      Your data is protected with industry-leading privacy.
                    </p>
                  </div>
                </div>

                <div className="p-3 rounded-2xl bg-white border border-slate-200/80 shadow-2xs flex items-start gap-3">
                  <div className="p-2 rounded-xl bg-purple-50 text-purple-600 shrink-0">
                    <TrendingUp className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs sm:text-sm font-extrabold text-slate-900">AI-Powered Insights</h4>
                    <p className="text-[11px] text-slate-500 font-medium leading-tight mt-0.5">
                      Multimodal AI analyzes data to deliver personalized insights.
                    </p>
                  </div>
                </div>

                <div className="p-3 rounded-2xl bg-white border border-slate-200/80 shadow-2xs flex items-start gap-3">
                  <div className="p-2 rounded-xl bg-indigo-50 text-indigo-600 shrink-0">
                    <Users className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="text-xs sm:text-sm font-extrabold text-slate-900">Healthcare Focused</h4>
                    <p className="text-[11px] text-slate-500 font-medium leading-tight mt-0.5">
                      Built for clinicians and patients to improve outcomes.
                    </p>
                  </div>
                </div>
              </div>

              {/* Bottom Trust Badge */}
              <div className="pt-1 flex items-center gap-2 text-xs text-slate-500 font-medium">
                <ShieldCheck className="w-4 h-4 text-slate-400 shrink-0" />
                <div>
                  <span className="font-extrabold text-slate-700">Your health data is safe with us. </span>
                  <span>We prioritize privacy and security.</span>
                </div>
              </div>

            </div>

            {/* FULLY EXPANDED ATTRACTIVE 16:9 3D STAGE */}
            <div className="md:col-span-6 flex justify-center items-center h-full relative">
              <div className="absolute inset-0 bg-gradient-to-tr from-blue-500/20 via-indigo-500/20 to-purple-500/20 rounded-3xl blur-2xl" />
              <div className="relative w-full h-[360px] sm:h-[400px] lg:h-[420px] rounded-3xl overflow-hidden shadow-[0_25px_70px_rgba(15,23,42,0.14)] border border-slate-200/90 bg-slate-950 flex items-center justify-center">
                <img
                  src="/assets/3d/register_3d_security_shield.jpg"
                  alt="TeleMed AI 3D Heart Hexagon Pedestal"
                  className="w-full h-full object-cover object-center scale-105 transition-transform duration-700 hover:scale-110"
                />
              </div>
            </div>

          </div>

          {/* RIGHT COLUMN: Compact White Registration Card (Zero Vertical Overflow) */}
          <div className="lg:col-span-5 flex justify-center lg:justify-end">
            <div className="w-full max-w-[390px] sm:max-w-[400px] rounded-[28px] bg-white border border-slate-200/90 p-5 sm:p-6 shadow-[0_20px_50px_rgba(15,23,42,0.06)] space-y-3">
              
              {/* Card Header Icon & Titles */}
              <div className="text-center space-y-1">
                <div className="w-10 h-10 rounded-2xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white flex items-center justify-center mx-auto shadow-md shadow-blue-500/20">
                  <Activity className="w-5 h-5" />
                </div>
                <h2 className="text-xl sm:text-2xl font-black text-slate-900 tracking-tight">
                  Create TeleMed AI Account
                </h2>
                <p className="text-xs text-slate-500 font-medium">
                  Get started with explainable multimodal AI risk prediction.
                </p>
              </div>

              {errorMsg && (
                <div className="p-2 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-bold leading-normal">
                  {errorMsg}
                </div>
              )}

              <form onSubmit={handleRegisterSubmit} className="space-y-2.5 text-left">
                
                {/* ROLE SEGMENTED CONTROL: Patient & Doctor */}
                <div className="space-y-1">
                  <label className="text-[10px] font-black text-slate-500 uppercase tracking-wider block">
                    I WANT TO REGISTER AS
                  </label>
                  <div className="grid grid-cols-2 gap-1.5 p-1 rounded-xl bg-slate-100/90 border border-slate-200/80">
                    <button
                      type="button"
                      onClick={() => setRole('PATIENT')}
                      className={`py-1.5 px-3 rounded-lg text-xs font-extrabold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                        role === 'PATIENT'
                          ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-xs'
                          : 'text-slate-700 hover:text-slate-900 hover:bg-slate-200/60'
                      }`}
                    >
                      <User className="w-3.5 h-3.5" />
                      <span>Patient</span>
                    </button>

                    <button
                      type="button"
                      onClick={() => setRole('DOCTOR')}
                      className={`py-1.5 px-3 rounded-lg text-xs font-extrabold transition-all flex items-center justify-center gap-1.5 cursor-pointer ${
                        role === 'DOCTOR'
                          ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-xs'
                          : 'text-slate-700 hover:text-slate-900 hover:bg-slate-200/60'
                      }`}
                    >
                      <Briefcase className="w-3.5 h-3.5" />
                      <span>Doctor</span>
                    </button>
                  </div>
                </div>

                {/* Full Name */}
                <div className="space-y-0.5">
                  <label className="text-xs font-extrabold text-slate-700">Full Name</label>
                  <div className="relative">
                    <User className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                    <input
                      type="text"
                      value={fullName}
                      onChange={(e) => setFullName(e.target.value)}
                      placeholder="Enter your full name"
                      required
                      className="w-full pl-8 pr-3 py-2.5 rounded-xl bg-slate-50/70 border border-slate-200 text-xs sm:text-sm font-medium focus:bg-white focus:outline-none focus:border-blue-600 transition-all h-10 sm:h-11"
                    />
                  </div>
                </div>

                {/* Email Address */}
                <div className="space-y-0.5">
                  <label className="text-xs font-extrabold text-slate-700">Email Address</label>
                  <div className="relative">
                    <Mail className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                    <input
                      type="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="Enter your email address"
                      required
                      className="w-full pl-8 pr-3 py-2.5 rounded-xl bg-slate-50/70 border border-slate-200 text-xs sm:text-sm font-medium focus:bg-white focus:outline-none focus:border-blue-600 transition-all h-10 sm:h-11"
                    />
                  </div>
                </div>

                {/* Password & Strength Meter */}
                <div className="space-y-0.5">
                  <label className="text-xs font-extrabold text-slate-700">Password</label>
                  <div className="relative">
                    <Lock className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="Create a strong password"
                      required
                      className="w-full pl-8 pr-8 py-2.5 rounded-xl bg-slate-50/70 border border-slate-200 text-xs sm:text-sm font-medium focus:bg-white focus:outline-none focus:border-blue-600 transition-all h-10 sm:h-11"
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-3 text-slate-400 hover:text-slate-600 cursor-pointer"
                    >
                      {showPassword ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
                    </button>
                  </div>

                  {/* Compact Password Strength Indicators */}
                  <div className="flex flex-wrap gap-1 pt-0.5">
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center gap-1 ${
                      hasMinLength ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-500'
                    }`}>
                      <Check className={`w-3 h-3 ${hasMinLength ? 'text-emerald-600' : 'text-slate-400'}`} />
                      <span>8+ characters</span>
                    </span>

                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center gap-1 ${
                      hasNumber ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-500'
                    }`}>
                      <Check className={`w-3 h-3 ${hasNumber ? 'text-emerald-600' : 'text-slate-400'}`} />
                      <span>1 number</span>
                    </span>

                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold flex items-center gap-1 ${
                      hasSpecial ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-500'
                    }`}>
                      <Check className={`w-3 h-3 ${hasSpecial ? 'text-emerald-600' : 'text-slate-400'}`} />
                      <span>1 special character</span>
                    </span>
                  </div>
                </div>

                {/* Doctor-Specific Fields */}
                {role === 'DOCTOR' && (
                  <div className="space-y-2 pt-1 border-t border-slate-100">
                    <div className="space-y-0.5">
                      <label className="text-xs font-extrabold text-slate-700">Specialization</label>
                      <div className="relative">
                        <Briefcase className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                        <input
                          type="text"
                          value={specialization}
                          onChange={(e) => setSpecialization(e.target.value)}
                          placeholder="e.g., General Medicine / Cardiology"
                          required
                          className="w-full pl-8 pr-3 py-2 rounded-xl bg-slate-50/70 border border-slate-200 text-xs sm:text-sm font-medium focus:bg-white focus:outline-none focus:border-blue-600 transition-all h-10"
                        />
                      </div>
                    </div>

                    <div className="space-y-0.5">
                      <label className="text-xs font-extrabold text-slate-700">Medical Registration Number</label>
                      <div className="relative">
                        <Hash className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-3" />
                        <input
                          type="text"
                          value={registrationNumber}
                          onChange={(e) => setRegistrationNumber(e.target.value)}
                          placeholder="e.g., REG-123456"
                          required
                          className="w-full pl-8 pr-3 py-2 rounded-xl bg-slate-50/70 border border-slate-200 text-xs sm:text-sm font-medium focus:bg-white focus:outline-none focus:border-blue-600 transition-all h-10"
                        />
                      </div>
                    </div>
                  </div>
                )}

                {/* Primary Button */}
                <button
                  type="submit"
                  disabled={loading}
                  className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-extrabold text-xs sm:text-sm shadow-md shadow-blue-500/20 hover:shadow-lg transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-75 h-11"
                >
                  {loading ? (
                    <span>Creating Account...</span>
                  ) : (
                    <>
                      <span>Create Account & Start Analysis</span>
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>

              </form>

              {/* Social Auth Divider */}
              <div className="space-y-2 pt-0.5">
                <div className="flex items-center gap-3 text-[10px] text-slate-400 uppercase font-bold">
                  <div className="flex-1 h-px bg-slate-200" />
                  <span>OR</span>
                  <div className="flex-1 h-px bg-slate-200" />
                </div>

                <button
                  type="button"
                  onClick={handleGoogleAuth}
                  className="w-full py-2.5 px-3 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 text-slate-700 font-extrabold text-xs shadow-2xs transition-all flex items-center justify-center gap-2 cursor-pointer"
                >
                  <svg className="w-4 h-4" viewBox="0 0 24 24">
                    <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                    <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                    <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
                    <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
                  </svg>
                  <span>Continue with Google</span>
                </button>
              </div>

              {/* Bottom Link */}
              <div className="pt-0.5 text-center text-xs font-medium text-slate-600">
                <span>Already have an account? </span>
                <Link to="/login" className="font-extrabold text-blue-600 hover:text-blue-700 underline">
                  Sign in
                </Link>
              </div>

            </div>
          </div>

        </div>
      </main>

      {/* Google Single Sign-On Modal */}
      <GoogleAuthModal
        isOpen={isGoogleModalOpen}
        onClose={() => setIsGoogleModalOpen(false)}
        onSuccess={handleGoogleSuccess}
        initialRole={role}
      />
    </PublicCanvasLayout>
  );
}
