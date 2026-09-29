import React, { useState } from 'react';
import { User, Shield, Stethoscope, Lock, Mail, AlertCircle, CheckCircle, ArrowRight } from 'lucide-react';
import { loginUser, registerPatient, registerDoctor } from '../api/client';

export default function AuthModal({ onLoginSuccess }) {
  const [tab, setTab] = useState('login'); // 'login' | 'reg_patient' | 'reg_doctor'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Login Form State
  const [loginEmail, setLoginEmail] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Patient Registration Form State
  const [pEmail, setPEmail] = useState('');
  const [pPassword, setPPassword] = useState('');
  const [pFullName, setPFullName] = useState('');
  const [pAge, setPAge] = useState('');
  const [pGender, setPGender] = useState('Male');
  const [pHeight, setPHeight] = useState('');
  const [pWeight, setPWeight] = useState('');

  // Doctor Registration Form State
  const [dEmail, setDEmail] = useState('');
  const [dPassword, setDPassword] = useState('');
  const [dFullName, setDFullName] = useState('');
  const [dSpecialization, setDSpecialization] = useState('Endocrinology & Diabetology');
  const [dRegNum, setDRegNum] = useState('');
  const [dExpYears, setDExpYears] = useState('5');
  const [dHospital, setDHospital] = useState('');

  const handleLoginSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await loginUser(loginEmail, loginPassword);
      onLoginSuccess(res.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handlePatientRegisterSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await registerPatient({
        email: pEmail,
        password: pPassword,
        full_name: pFullName,
        age: pAge ? parseInt(pAge) : null,
        gender: pGender,
        height_cm: pHeight ? parseFloat(pHeight) : null,
        weight_kg: pWeight ? parseFloat(pWeight) : null,
      });
      onLoginSuccess(res.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleDoctorRegisterSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await registerDoctor({
        email: dEmail,
        password: dPassword,
        full_name: dFullName,
        specialization: dSpecialization,
        registration_number: dRegNum,
        experience_years: dExpYears ? parseInt(dExpYears) : 0,
        hospital_affiliation: dHospital,
      });
      setSuccessMsg('Doctor account created successfully! Verification status: PENDING.');
      setTimeout(() => {
        onLoginSuccess(res.user);
      }, 1200);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'radial-gradient(circle at 50% 20%, #1e293b 0%, #0f172a 100%)',
      padding: '24px',
      fontFamily: 'Inter, system-ui, sans-serif',
      color: '#f8fafc',
    }}>
      <div style={{
        width: '100%',
        maxWidth: '540px',
        background: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(16px)',
        border: '1px solid rgba(255, 255, 255, 0.1)',
        borderRadius: '20px',
        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)',
        overflow: 'hidden',
      }}>
        {/* Header Branding */}
        <div style={{
          padding: '32px 32px 24px',
          textAlign: 'center',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          background: 'linear-gradient(180deg, rgba(30, 41, 59, 0.5) 0%, rgba(15, 23, 42, 0) 100%)'
        }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '56px',
            height: '56px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, var(--accent-cyan, #06b6d4) 0%, var(--accent-blue, #3b82f6) 100%)',
            boxShadow: '0 8px 20px rgba(6, 182, 212, 0.3)',
            marginBottom: '16px',
          }}>
            <Shield size={32} color="#ffffff" />
          </div>
          <h1 style={{ fontSize: '1.75rem', fontWeight: 700, margin: 0, letterSpacing: '-0.025em' }}>
            TeleMed <span style={{ color: 'var(--accent-cyan, #06b6d4)' }}>AI</span> Platform
          </h1>
          <p style={{ color: '#94a3b8', fontSize: '0.875rem', marginTop: '6px' }}>
            Generative AI Multimodal Decision Support & RBAC Security System
          </p>
        </div>

        {/* Tab Navigation */}
        <div style={{
          display: 'flex',
          background: 'rgba(30, 41, 59, 0.6)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          padding: '6px',
          gap: '4px',
        }}>
          <button
            type="button"
            onClick={() => { setTab('login'); setError(null); }}
            style={{
              flex: 1,
              padding: '10px 12px',
              borderRadius: '10px',
              border: 'none',
              background: tab === 'login' ? 'var(--accent-cyan, #06b6d4)' : 'transparent',
              color: tab === 'login' ? '#ffffff' : '#94a3b8',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
            }}
          >
            <User size={16} /> Login
          </button>

          <button
            type="button"
            onClick={() => { setTab('reg_patient'); setError(null); }}
            style={{
              flex: 1,
              padding: '10px 12px',
              borderRadius: '10px',
              border: 'none',
              background: tab === 'reg_patient' ? 'var(--accent-cyan, #06b6d4)' : 'transparent',
              color: tab === 'reg_patient' ? '#ffffff' : '#94a3b8',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
            }}
          >
            <User size={16} /> Patient Signup
          </button>

          <button
            type="button"
            onClick={() => { setTab('reg_doctor'); setError(null); }}
            style={{
              flex: 1,
              padding: '10px 12px',
              borderRadius: '10px',
              border: 'none',
              background: tab === 'reg_doctor' ? 'var(--accent-cyan, #06b6d4)' : 'transparent',
              color: tab === 'reg_doctor' ? '#ffffff' : '#94a3b8',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer',
              transition: 'all 0.2s ease',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
            }}
          >
            <Stethoscope size={16} /> Doctor Signup
          </button>
        </div>

        {/* Content Body */}
        <div style={{ padding: '28px 32px 32px' }}>
          {error && (
            <div style={{
              background: 'rgba(239, 68, 68, 0.15)',
              border: '1px solid rgba(239, 68, 68, 0.4)',
              borderRadius: '12px',
              padding: '12px 16px',
              marginBottom: '20px',
              color: '#fca5a5',
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}>
              <AlertCircle size={18} style={{ flexShrink: 0 }} />
              <span>{error}</span>
            </div>
          )}

          {successMsg && (
            <div style={{
              background: 'rgba(16, 185, 129, 0.15)',
              border: '1px solid rgba(16, 185, 129, 0.4)',
              borderRadius: '12px',
              padding: '12px 16px',
              marginBottom: '20px',
              color: '#6ee7b7',
              fontSize: '0.875rem',
              display: 'flex',
              alignItems: 'center',
              gap: '10px',
            }}>
              <CheckCircle size={18} style={{ flexShrink: 0 }} />
              <span>{successMsg}</span>
            </div>
          )}

          {/* TAB 1: LOGIN */}
          {tab === 'login' && (
            <form onSubmit={handleLoginSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '6px' }}>
                  Email Address
                </label>
                <div style={{ position: 'relative' }}>
                  <Mail size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
                  <input
                    type="email"
                    required
                    value={loginEmail}
                    onChange={(e) => setLoginEmail(e.target.value)}
                    placeholder="patient@telemed.ai or doctor@telemed.ai"
                    style={{
                      width: '100%',
                      padding: '12px 12px 12px 40px',
                      background: 'rgba(30, 41, 59, 0.7)',
                      border: '1px solid rgba(255, 255, 255, 0.12)',
                      borderRadius: '10px',
                      color: '#ffffff',
                      fontSize: '0.9rem',
                      outline: 'none',
                    }}
                  />
                </div>
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '6px' }}>
                  Password
                </label>
                <div style={{ position: 'relative' }}>
                  <Lock size={18} style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#64748b' }} />
                  <input
                    type="password"
                    required
                    autoComplete="current-password"
                    value={loginPassword}
                    onChange={(e) => setLoginPassword(e.target.value)}
                    placeholder="Enter your password"
                    style={{
                      width: '100%',
                      padding: '12px 12px 12px 40px',
                      background: 'rgba(30, 41, 59, 0.7)',
                      border: '1px solid rgba(255, 255, 255, 0.12)',
                      borderRadius: '10px',
                      color: '#ffffff',
                      fontSize: '0.9rem',
                      outline: 'none',
                    }}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                style={{
                  marginTop: '8px',
                  padding: '12px',
                  borderRadius: '10px',
                  border: 'none',
                  background: 'linear-gradient(135deg, var(--accent-cyan, #06b6d4) 0%, var(--accent-blue, #3b82f6) 100%)',
                  color: '#ffffff',
                  fontWeight: 600,
                  fontSize: '0.95rem',
                  cursor: loading ? 'wait' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                  boxShadow: '0 4px 14px rgba(6, 182, 212, 0.3)',
                }}
              >
                {loading ? 'Authenticating...' : <>Login to Portal <ArrowRight size={18} /></>}
              </button>
            </form>
          )}

          {/* TAB 2: REGISTER PATIENT */}
          {tab === 'reg_patient' && (
            <form onSubmit={handlePatientRegisterSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  value={pFullName}
                  onChange={(e) => setPFullName(e.target.value)}
                  placeholder="e.g. Eleanor Vance"
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    background: 'rgba(30, 41, 59, 0.7)',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    borderRadius: '8px',
                    color: '#ffffff',
                    fontSize: '0.875rem',
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>
                    Email
                  </label>
                  <input
                    type="email"
                    required
                    value={pEmail}
                    onChange={(e) => setPEmail(e.target.value)}
                    placeholder="patient@example.com"
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      background: 'rgba(30, 41, 59, 0.7)',
                      border: '1px solid rgba(255, 255, 255, 0.12)',
                      borderRadius: '8px',
                      color: '#ffffff',
                      fontSize: '0.875rem',
                    }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>
                    Password
                  </label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    autoComplete="new-password"
                    value={pPassword}
                    onChange={(e) => setPPassword(e.target.value)}
                    placeholder="Min 8 chars"
                    style={{
                      width: '100%',
                      padding: '10px 12px',
                      background: 'rgba(30, 41, 59, 0.7)',
                      border: '1px solid rgba(255, 255, 255, 0.12)',
                      borderRadius: '8px',
                      color: '#ffffff',
                      fontSize: '0.875rem',
                    }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr 1fr', gap: '8px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: '#cbd5e1', marginBottom: '4px' }}>Age</label>
                  <input
                    type="number"
                    value={pAge}
                    onChange={(e) => setPAge(e.target.value)}
                    placeholder="52"
                    style={{ width: '100%', padding: '8px', background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '6px', color: '#fff', fontSize: '0.85rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: '#cbd5e1', marginBottom: '4px' }}>Gender</label>
                  <select
                    value={pGender}
                    onChange={(e) => setPGender(e.target.value)}
                    style={{ width: '100%', padding: '8px', background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '6px', color: '#fff', fontSize: '0.85rem' }}
                  >
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: '#cbd5e1', marginBottom: '4px' }}>Height (cm)</label>
                  <input
                    type="number"
                    value={pHeight}
                    onChange={(e) => setPHeight(e.target.value)}
                    placeholder="175"
                    style={{ width: '100%', padding: '8px', background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '6px', color: '#fff', fontSize: '0.85rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.75rem', color: '#cbd5e1', marginBottom: '4px' }}>Weight (kg)</label>
                  <input
                    type="number"
                    value={pWeight}
                    onChange={(e) => setPWeight(e.target.value)}
                    placeholder="82"
                    style={{ width: '100%', padding: '8px', background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '6px', color: '#fff', fontSize: '0.85rem' }}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                style={{
                  marginTop: '12px',
                  padding: '12px',
                  borderRadius: '10px',
                  border: 'none',
                  background: 'linear-gradient(135deg, var(--accent-cyan, #06b6d4) 0%, var(--accent-blue, #3b82f6) 100%)',
                  color: '#ffffff',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  cursor: loading ? 'wait' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                {loading ? 'Creating Account...' : 'Register & Launch Patient Workspace'}
              </button>
            </form>
          )}

          {/* TAB 3: REGISTER DOCTOR */}
          {tab === 'reg_doctor' && (
            <form onSubmit={handleDoctorRegisterSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              <div style={{
                background: 'rgba(245, 158, 11, 0.1)',
                border: '1px solid rgba(245, 158, 11, 0.25)',
                borderRadius: '8px',
                padding: '10px 12px',
                fontSize: '0.75rem',
                color: '#fef08a',
              }}>
                ℹ️ <strong>Doctor Verification Lifecycle:</strong> Newly registered doctors default to <code>PENDING</code> status. Patient clinical workspace access is granted after Admin verification.
              </div>

              <div>
                <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>
                  Doctor Full Name
                </label>
                <input
                  type="text"
                  required
                  value={dFullName}
                  onChange={(e) => setDFullName(e.target.value)}
                  placeholder="e.g. Dr. Marcus Vance"
                  style={{
                    width: '100%',
                    padding: '10px 12px',
                    background: 'rgba(30, 41, 59, 0.7)',
                    border: '1px solid rgba(255, 255, 255, 0.12)',
                    borderRadius: '8px',
                    color: '#ffffff',
                    fontSize: '0.875rem',
                  }}
                />
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>
                    Email
                  </label>
                  <input
                    type="email"
                    required
                    value={dEmail}
                    onChange={(e) => setDEmail(e.target.value)}
                    placeholder="doctor@hospital.org"
                    style={{ width: '100%', padding: '9px 12px', background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>
                    Password
                  </label>
                  <input
                    type="password"
                    required
                    minLength={8}
                    autoComplete="new-password"
                    value={dPassword}
                    onChange={(e) => setDPassword(e.target.value)}
                    placeholder="Min 8 chars (Upper, Lower, Digit, Symbol)"
                    style={{ width: '100%', padding: '9px 12px', background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 1fr', gap: '10px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>
                    Specialization
                  </label>
                  <input
                    type="text"
                    required
                    value={dSpecialization}
                    onChange={(e) => setDSpecialization(e.target.value)}
                    placeholder="Endocrinology, Internal Med"
                    style={{ width: '100%', padding: '9px 12px', background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>
                    License / Reg ID
                  </label>
                  <input
                    type="text"
                    required
                    value={dRegNum}
                    onChange={(e) => setDRegNum(e.target.value)}
                    placeholder="MED-778899"
                    style={{ width: '100%', padding: '9px 12px', background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
                  />
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1.5fr', gap: '10px' }}>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>
                    Experience (Years)
                  </label>
                  <input
                    type="number"
                    value={dExpYears}
                    onChange={(e) => setDExpYears(e.target.value)}
                    placeholder="8"
                    style={{ width: '100%', padding: '9px 12px', background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
                  />
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 600, color: '#cbd5e1', marginBottom: '4px' }}>
                    Hospital / Institution
                  </label>
                  <input
                    type="text"
                    value={dHospital}
                    onChange={(e) => setDHospital(e.target.value)}
                    placeholder="St. Jude Medical Center"
                    style={{ width: '100%', padding: '9px 12px', background: 'rgba(30, 41, 59, 0.7)', border: '1px solid rgba(255,255,255,0.12)', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                style={{
                  marginTop: '10px',
                  padding: '12px',
                  borderRadius: '10px',
                  border: 'none',
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
                  color: '#ffffff',
                  fontWeight: 600,
                  fontSize: '0.9rem',
                  cursor: loading ? 'wait' : 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  gap: '8px',
                }}
              >
                {loading ? 'Submitting Registration...' : 'Submit Doctor Registration (PENDING Status)'}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
