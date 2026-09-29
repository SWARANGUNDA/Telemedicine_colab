import React, { useState, useEffect } from 'react';
import {
  User, Stethoscope, Lock, ShieldCheck, Save, Edit3, AlertCircle,
  CheckCircle2, Mail, Phone, Calendar, Building, Award, Activity, Shield, Key
} from 'lucide-react';
import {
  Button, Card, Badge, Avatar, Input, Select, Alert, Modal
} from '../components/ui';
import { PageContainer } from '../components/layout';
import { updateUserProfile, getAuthToken } from '../api/client';

export default function AccountPage({ user, onProfileUpdated }) {
  const role = user?.role || 'PATIENT';

  // Patient Profile Form State
  const patientProfile = user?.patient_profile || {};
  const [fullName, setFullName] = useState(user?.full_name || patientProfile.full_name || '');
  const [age, setAge] = useState(patientProfile.age || '');
  const [gender, setGender] = useState(patientProfile.gender || '');
  const [heightCm, setHeightCm] = useState(patientProfile.height_cm || '');
  const [weightKg, setWeightKg] = useState(patientProfile.weight_kg || '');
  const [contactNumber, setContactNumber] = useState(patientProfile.contact_number || '');

  // Doctor Profile Form State
  const doctorProfile = user?.doctor_profile || {};
  const [docFullName, setDocFullName] = useState(user?.full_name || doctorProfile.full_name || '');
  const [docSpecialization, setDocSpecialization] = useState(doctorProfile.specialization || 'General Medicine');
  const [docQualification, setDocQualification] = useState(doctorProfile.qualification || 'MBBS');
  const [docCouncil, setDocCouncil] = useState(doctorProfile.registration_council || 'State Medical Council');
  const [docExperience, setDocExperience] = useState(doctorProfile.experience_years || 0);
  const [docContact, setDocContact] = useState(doctorProfile.contact_number || '');
  const [docHospital, setDocHospital] = useState(doctorProfile.hospital_affiliation || 'Apollo Hospitals');
  const [docEditing, setDocEditing] = useState(false);

  // Status State
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState(null);

  useEffect(() => {
    if (user) {
      if (role === 'PATIENT') {
        const p = user.patient_profile || {};
        setFullName(user.full_name || p.full_name || '');
        setAge(p.age || '');
        setGender(p.gender || '');
        setHeightCm(p.height_cm || '');
        setWeightKg(p.weight_kg || '');
        setContactNumber(p.contact_number || '');
      } else if (role === 'DOCTOR') {
        const d = user.doctor_profile || {};
        setDocFullName(user.full_name || d.full_name || '');
        setDocSpecialization(d.specialization || 'General Medicine');
        setDocQualification(d.qualification || 'MBBS');
        setDocCouncil(d.registration_council || 'State Medical Council');
        setDocExperience(d.experience_years || 0);
        setDocContact(d.contact_number || '');
        setDocHospital(d.hospital_affiliation || 'Apollo Hospitals');
      } else {
        setFullName(user.full_name || 'Admin User');
      }
    }
  }, [user, role]);

  const computeBmi = (w, h) => {
    if (!w || !h || h <= 0) return null;
    const hM = h / 100;
    const bmiVal = (w / (hM * hM)).toFixed(1);
    let statusStr = 'Normal Weight';
    let badgeVar = 'success';
    if (bmiVal < 18.5) { statusStr = 'Underweight'; badgeVar = 'warning'; }
    else if (bmiVal >= 25 && bmiVal < 30) { statusStr = 'Overweight'; badgeVar = 'warning'; }
    else if (bmiVal >= 30) { statusStr = 'Obese Class'; badgeVar = 'danger'; }
    return { value: bmiVal, status: statusStr, variant: badgeVar };
  };

  const handleProfileSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    setSaveSuccess(false);
    setSaveError(null);

    try {
      let payload = {};
      if (role === 'PATIENT') {
        payload = {
          full_name: fullName,
          age: age ? parseInt(age, 10) : null,
          gender: gender,
          height_cm: heightCm ? parseFloat(heightCm) : null,
          weight_kg: weightKg ? parseFloat(weightKg) : null,
          contact_number: contactNumber
        };
      } else if (role === 'DOCTOR') {
        payload = {
          full_name: docFullName,
          specialization: docSpecialization,
          qualification: docQualification,
          registration_council: docCouncil,
          experience_years: docExperience ? parseInt(docExperience, 10) : 0,
          contact_number: docContact,
          hospital_affiliation: docHospital
        };
      } else {
        payload = { full_name: fullName };
      }

      const res = await updateUserProfile(payload);
      const profileKey = `telemed_user_profile_${user?.user_id || 'guest'}`;
      try {
        const existing = localStorage.getItem(profileKey);
        const parsed = existing ? JSON.parse(existing) : {};
        localStorage.setItem(profileKey, JSON.stringify({ ...parsed, isUpdated: true }));
      } catch (e) {}

      setSaveSuccess(true);
      setDocEditing(false);
      window.dispatchEvent(new Event('telemed_profile_updated'));
      window.dispatchEvent(new Event('telemed:user-updated'));
      if (onProfileUpdated && res.user) {
        onProfileUpdated(res.user);
      }
      setTimeout(() => setSaveSuccess(false), 4000);
    } catch (err) {
      setSaveError(err.message || 'Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  const displayFullName = role === 'PATIENT' ? (fullName || 'Patient Account') : role === 'DOCTOR' ? (docFullName || 'Dr. Medical Officer') : (fullName || 'System Administrator');

  return (
    <PageContainer className="space-y-8 pb-24">
      
      {/* ULTRA-PREMIUM MODERN HERO HEADER BANNER */}
      <div className="relative overflow-hidden rounded-3xl bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-900 border border-indigo-500/30 p-6 md:p-8 shadow-2xl space-y-4">
        {/* Background Ambient Glow */}
        <div className="absolute top-0 right-0 -mt-8 -mr-8 w-64 h-64 rounded-full bg-blue-500/20 blur-3xl pointer-events-none"></div>
        <div className="absolute bottom-0 left-0 -mb-8 -ml-8 w-64 h-64 rounded-full bg-indigo-500/20 blur-3xl pointer-events-none"></div>

        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-center gap-4 md:gap-6">
            <Avatar
              user={user}
              name={displayFullName}
              size="lg"
              className="ring-4 ring-blue-500/40 shadow-xl shadow-blue-500/30 text-xl font-black bg-gradient-to-br from-blue-500 to-indigo-600 text-white"
            />
            <div className="space-y-1.5">
              <div className="flex items-center gap-2.5 flex-wrap">
                <h1 className="text-xl md:text-2xl font-black text-white tracking-tight">
                  {displayFullName}
                </h1>
                <span className="px-2.5 py-0.5 text-xs font-mono font-bold rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 uppercase">
                  {role === 'ADMIN' ? 'SYSTEM ADMINISTRATOR' : role === 'DOCTOR' ? 'VERIFIED PHYSICIAN' : 'PATIENT PROFILE'}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {saveSuccess && (
        <Alert variant="success">
          Profile information updated successfully!
        </Alert>
      )}

      {saveError && (
        <Alert variant="danger">
          {saveError}
        </Alert>
      )}

      {/* PATIENT PORTAL PROFILE WORKSPACE */}
      {role === 'PATIENT' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Editable Patient Demographics Form (2 cols) */}
          <Card isGlass={true} className="lg:col-span-2 p-6 bg-[var(--bg-primary)] space-y-6">
            <div className="flex items-center gap-2 pb-4 border-b border-[var(--border-subtle)]">
              <User className="w-5 h-5 text-[var(--primary)]" />
              <h3 className="text-base font-extrabold text-[var(--text-main)]">Editable Demographic Profile</h3>
            </div>

            <form onSubmit={handleProfileSave} className="space-y-4">
              <div>
                <label className="text-xs font-bold text-[var(--text-main)] block mb-1">Full Name</label>
                <Input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Enter full legal name..."
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-[var(--text-main)] block mb-1">Age (Years)</label>
                  <Input
                    type="number"
                    min="1"
                    max="120"
                    value={age}
                    onChange={(e) => setAge(e.target.value)}
                    placeholder="e.g. 32"
                  />
                </div>

                <div>
                  <label className="text-xs font-bold text-[var(--text-main)] block mb-1">Biological Gender</label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="w-full p-2.5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[var(--text-main)] text-xs focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
                  >
                    <option value="">Select Gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label className="text-xs font-bold text-[var(--text-main)] block mb-1">Height (cm)</label>
                  <Input
                    type="number"
                    step="0.1"
                    value={heightCm}
                    onChange={(e) => setHeightCm(e.target.value)}
                    placeholder="e.g. 175"
                  />
                </div>

                <div>
                  <label className="text-xs font-bold text-[var(--text-main)] block mb-1">Weight (kg)</label>
                  <Input
                    type="number"
                    step="0.1"
                    value={weightKg}
                    onChange={(e) => setWeightKg(e.target.value)}
                    placeholder="e.g. 70"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold text-[var(--text-main)] block mb-1">Contact Phone Number</label>
                <Input
                  type="text"
                  value={contactNumber}
                  onChange={(e) => setContactNumber(e.target.value)}
                  placeholder="+91 98765 43210"
                />
              </div>

              <div className="pt-2">
                <Button variant="primary" size="md" type="submit" isLoading={saving} leftIcon={<Save className="w-4 h-4" />}>
                  Save Profile Changes
                </Button>
              </div>
            </form>
          </Card>

          {/* Protected System & Biometrics Card (1 col) */}
          <div className="space-y-6">
            <Card isGlass={true} className="p-6 bg-[var(--bg-primary)] space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-[var(--border-subtle)]">
                <Activity className="w-5 h-5 text-emerald-500" />
                <h3 className="text-base font-extrabold text-[var(--text-main)]">Biometric Diagnostics</h3>
              </div>

              <div className="p-4 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-2 text-xs">
                <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">Calculated BMI Index</span>
                {(() => {
                  const bmiRes = computeBmi(weightKg, heightCm);
                  return bmiRes ? (
                    <div className="flex items-center justify-between">
                      <span className="text-lg font-black font-mono text-[var(--text-main)]">{bmiRes.value} kg/m²</span>
                      <Badge variant={bmiRes.variant} size="sm font-mono">{bmiRes.status}</Badge>
                    </div>
                  ) : (
                    <span className="text-[var(--text-muted)] italic">Enter height and weight to calculate BMI.</span>
                  );
                })()}
              </div>

              <div className="pt-2 space-y-3 text-xs">
                <div className="flex justify-between items-center p-2.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                  <span className="text-[var(--text-muted)]">Account Email:</span>
                  <strong className="font-mono text-[var(--text-main)]">{user?.email || '—'}</strong>
                </div>

                <div className="flex justify-between items-center p-2.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                  <span className="text-[var(--text-muted)]">Patient ID:</span>
                  <strong className="font-mono text-[var(--primary)]">{user?.user_id || '—'}</strong>
                </div>

                <div className="flex justify-between items-center p-2.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                  <span className="text-[var(--text-muted)]">Authentication:</span>
                  <Badge variant="success" size="sm font-mono">JWT SECURE</Badge>
                </div>
              </div>
            </Card>
          </div>

        </div>
      )}

      {/* DOCTOR PORTAL PROFILE WORKSPACE */}
      {role === 'DOCTOR' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Editable Doctor Professional Profile (2 cols) */}
          <Card isGlass={true} className="lg:col-span-2 p-6 bg-[var(--bg-primary)] space-y-6">
            <div className="flex items-center justify-between pb-4 border-b border-[var(--border-subtle)]">
              <div className="flex items-center gap-2">
                <Stethoscope className="w-5 h-5 text-[var(--primary)]" />
                <h3 className="text-base font-extrabold text-[var(--text-main)]">Doctor Professional Profile</h3>
              </div>
              {!docEditing && (
                <Button variant="outline" size="sm" onClick={() => setDocEditing(true)} leftIcon={<Edit3 className="w-3.5 h-3.5" />}>
                  Edit Profile
                </Button>
              )}
            </div>

            <form onSubmit={handleProfileSave} className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                
                {/* Full Name */}
                <div className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1">
                  <label className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">Full Name</label>
                  {docEditing ? (
                    <Input value={docFullName} onChange={e => setDocFullName(e.target.value)} required />
                  ) : (
                    <strong className="text-sm text-[var(--text-main)] block">{docFullName || 'Dr. Arjun Sarkaar'}</strong>
                  )}
                </div>

                {/* Specialization */}
                <div className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1">
                  <label className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">Specialization</label>
                  {docEditing ? (
                    <Input value={docSpecialization} onChange={e => setDocSpecialization(e.target.value)} />
                  ) : (
                    <Badge variant="primary" size="sm">{docSpecialization || 'General Medicine'}</Badge>
                  )}
                </div>

                {/* Qualification */}
                <div className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1">
                  <label className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">Medical Qualification</label>
                  {docEditing ? (
                    <Input value={docQualification} onChange={e => setDocQualification(e.target.value)} />
                  ) : (
                    <strong className="text-xs text-[var(--text-main)] block">{docQualification || 'MBBS, MD'}</strong>
                  )}
                </div>

                {/* Registration Council */}
                <div className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1">
                  <label className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">Registration Council</label>
                  {docEditing ? (
                    <Input value={docCouncil} onChange={e => setDocCouncil(e.target.value)} />
                  ) : (
                    <strong className="text-xs text-[var(--text-main)] block">{docCouncil || 'State Medical Council'}</strong>
                  )}
                </div>

                {/* Experience */}
                <div className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1">
                  <label className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">Years of Experience</label>
                  {docEditing ? (
                    <Input type="number" min="0" max="80" value={docExperience} onChange={e => setDocExperience(e.target.value)} />
                  ) : (
                    <strong className="text-xs text-[var(--text-main)] block">{docExperience || 8} Years</strong>
                  )}
                </div>

                {/* Contact Number */}
                <div className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1">
                  <label className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">Contact Number</label>
                  {docEditing ? (
                    <Input value={docContact} onChange={e => setDocContact(e.target.value)} />
                  ) : (
                    <strong className="text-xs text-[var(--text-main)] block">{docContact || '+1 (555) 345-6789'}</strong>
                  )}
                </div>

              </div>

              {/* Hospital */}
              <div className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1 text-xs">
                <label className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">Hospital / Clinical Affiliation</label>
                {docEditing ? (
                  <Input value={docHospital} onChange={e => setDocHospital(e.target.value)} />
                ) : (
                  <strong className="text-xs text-[var(--text-main)] block">{docHospital || 'Apollo Specialty Hospitals'}</strong>
                )}
              </div>

              {docEditing && (
                <div className="flex items-center gap-3 pt-2">
                  <Button variant="primary" size="md" type="submit" isLoading={saving} leftIcon={<Save className="w-4 h-4" />}>
                    Save Professional Profile
                  </Button>
                  <Button variant="outline" size="md" type="button" onClick={() => setDocEditing(false)}>
                    Cancel
                  </Button>
                </div>
              )}
            </form>
          </Card>

          {/* Admin-Controlled Credential Governance Card (1 col) */}
          <div className="space-y-6">
            <Card isGlass={true} className="p-6 bg-[var(--bg-primary)] space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-[var(--border-subtle)]">
                <ShieldCheck className="w-5 h-5 text-emerald-500" />
                <h3 className="text-base font-extrabold text-[var(--text-main)]">Credential Governance</h3>
              </div>

              <div className="p-4 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 space-y-1.5 text-xs">
                <span className="text-[11px] font-mono font-bold text-emerald-600 dark:text-emerald-300 uppercase tracking-wider flex items-center gap-1.5">
                  <Lock className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> Medical Registration # (Admin Controlled)
                </span>
                <strong className="font-mono text-lg font-black text-emerald-700 dark:text-emerald-300 block tracking-widest">
                  {doctorProfile.registration_number || 'REG-190826'}
                </strong>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex justify-between items-center p-2.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                  <span className="text-[var(--text-muted)]">Verification Status:</span>
                  <Badge variant={doctorProfile.verification_status === 'VERIFIED' ? 'success' : 'warning'} size="sm font-mono font-bold">
                    {doctorProfile.verification_status || 'VERIFIED'}
                  </Badge>
                </div>

                <div className="flex justify-between items-center p-2.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                  <span className="text-[var(--text-muted)]">Physician Doctor ID:</span>
                  <strong className="font-mono text-[var(--primary)]">{doctorProfile.doctor_id || 'DOC-101'}</strong>
                </div>

                <div className="flex justify-between items-center p-2.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                  <span className="text-[var(--text-muted)]">Account Registration:</span>
                  <strong className="font-mono text-[var(--text-main)]">{user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'Active'}</strong>
                </div>
              </div>
            </Card>
          </div>

        </div>
      )}

      {/* ADMIN PORTAL ACCOUNT WORKSPACE */}
      {role === 'ADMIN' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          
          {/* Admin Account & Governance (2 cols) */}
          <Card isGlass={true} className="lg:col-span-2 p-6 bg-[var(--bg-primary)] space-y-6">
            <div className="flex items-center gap-2 pb-4 border-b border-[var(--border-subtle)]">
              <Shield className="w-5 h-5 text-[var(--primary)]" />
              <h3 className="text-base font-extrabold text-[var(--text-main)]">System Administrator Governance</h3>
            </div>

            <form onSubmit={handleProfileSave} className="space-y-4">
              <div>
                <label className="text-xs font-bold text-[var(--text-main)] block mb-1">Administrator Full Name</label>
                <Input
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Admin Name..."
                  required
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                <div className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1">
                  <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">Administrative Role</span>
                  <Badge variant="accent" size="sm font-mono font-bold">SYSTEM ADMINISTRATOR</Badge>
                </div>

                <div className="p-3 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1">
                  <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">Security Governance Scope</span>
                  <strong className="text-xs text-[var(--text-main)] block">Full RBAC & Clinical Audit Control</strong>
                </div>
              </div>

              <div className="pt-2">
                <Button variant="primary" size="md" type="submit" isLoading={saving} leftIcon={<Save className="w-4 h-4" />}>
                  Save Administrator Profile
                </Button>
              </div>
            </form>
          </Card>

          {/* Admin System Security Card (1 col) */}
          <div className="space-y-6">
            <Card isGlass={true} className="p-6 bg-[var(--bg-primary)] space-y-4">
              <div className="flex items-center gap-2 pb-3 border-b border-[var(--border-subtle)]">
                <Key className="w-5 h-5 text-indigo-400" />
                <h3 className="text-base font-extrabold text-[var(--text-main)]">Security Credentials</h3>
              </div>

              <div className="space-y-3 text-xs">
                <div className="flex justify-between items-center p-2.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                  <span className="text-[var(--text-muted)]">Admin Email:</span>
                  <strong className="font-mono text-[var(--text-main)]">{user?.email || '—'}</strong>
                </div>

                <div className="flex justify-between items-center p-2.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                  <span className="text-[var(--text-muted)]">User ID:</span>
                  <strong className="font-mono text-[var(--primary)]">{user?.user_id || '—'}</strong>
                </div>

                <div className="flex justify-between items-center p-2.5 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
                  <span className="text-[var(--text-muted)]">Auth Token Encryption:</span>
                  <Badge variant="success" size="sm font-mono">PBKDF2 SHA-256</Badge>
                </div>
              </div>
            </Card>
          </div>

        </div>
      )}

    </PageContainer>
  );
}
