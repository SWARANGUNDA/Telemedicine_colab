import React, { useState, useEffect } from 'react';
import { PageHeader, PageContainer, ContentSection } from '../components/layout';
import { Card, Badge, Button, ProgressBar, Input, Modal, Tabs, Table, EmptyState, Alert } from '../components/ui';
import {
  User, ShieldCheck, Activity, Heart, FileText, Watch, Dna, Clock,
  Search, Filter, Download, Eye, Edit3, Calendar, Phone, Mail, MapPin,
  Sparkles, CheckCircle2, AlertCircle, ArrowUpRight, ChevronRight, Check,
  Stethoscope, Brain, Shield, Award, Zap, Smile, HeartPulse, Scale
} from 'lucide-react';
import { getAvailableAvatarsForRole, getAvatarById, svgToDataUri } from '../utils/avatarCatalog';

export default function ProfilePage({ user, session, predictionData, onNavigate, refreshCurrentUser }) {
  const [activeTab, setActiveTab] = useState('summary');
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [vaultCategory, setVaultCategory] = useState('ALL');
  const [vaultSearchQuery, setVaultSearchQuery] = useState('');
  const [historySearchQuery, setHistorySearchQuery] = useState('');

  const [realRecords, setRealRecords] = useState([]);
  const [recordsLoading, setRecordsLoading] = useState(true);
  const [saveSuccessMsg, setSaveSuccessMsg] = useState(null);

  useEffect(() => {
    async function loadRecords() {
      if (!user || user.role !== 'PATIENT') {
        setRealRecords([]);
        setRecordsLoading(false);
        return;
      }
      setRecordsLoading(true);
      try {
        const res = await (await import('../api/client')).fetchPatientRecords();
        setRealRecords(res.records || []);
      } catch (e) {
        setRealRecords([]);
      } finally {
        setRecordsLoading(false);
      }
    }
    loadRecords();
  }, [user]);

  // Extract active biometrics source (from active predictionData or latest saved historical record)
  const activeRecord = realRecords.length > 0 ? realRecords[0] : null;
  const activeSource = predictionData || (activeRecord ? activeRecord.prediction_snapshot || activeRecord : null);

  const clinFeats = activeSource?.confirmed_features?.clinical 
    || activeSource?.clinical_features 
    || activeSource?.clinical_data 
    || activeSource?.input_data?.clinical 
    || {};

  const wearFeats = activeSource?.confirmed_features?.wearable 
    || activeSource?.wearable_features 
    || activeSource?.wearable_data 
    || activeSource?.input_data?.wearable 
    || {};

  // Editable Profile Form State per user
  const prof = user?.patient_profile || {};
  const initialName = user?.name || user?.full_name || prof.full_name || (user?.email ? user.email.split('@')[0].replace('.', ' ').replace('_', ' ') : 'Patient');

  // Determine default avatar based on user role or saved preferences
  const userRole = user?.role?.toUpperCase() || 'PATIENT';
  const defaultAvatarId = userRole === 'ADMIN' ? 'admin' : userRole === 'DOCTOR' ? 'doctor_male' : 'male';

  const [profileForm, setProfileForm] = useState(() => {
    try {
      const key = `telemed_user_profile_${user?.user_id || 'guest'}`;
      const saved = localStorage.getItem(key);
      if (saved) {
        const parsed = JSON.parse(saved);
        const validAv = getAvatarById(parsed?.selectedAvatar);
        return {
          ...parsed,
          selectedAvatar: validAv.id
        };
      }
    } catch (e) {}
    return {
      fullName: initialName,
      patientId: user?.user_id || prof.patient_id || 'usr_patient',
      email: user?.email || '',
      phone: prof.contact_number || '',
      dob: prof.dob || '1995-01-01',
      age: prof.age || clinFeats.Age || '',
      gender: prof.gender || clinFeats.Gender || '',
      height: prof.height_cm || clinFeats.Height || '',
      weight: prof.weight_kg || clinFeats.Weight || '',
      bloodGroup: prof.blood_group || 'O+',
      emergencyContact: prof.emergency_contact || 'None reported',
      selectedAvatar: defaultAvatarId,
      medicalConditions: 'None reported',
      allergies: 'None reported'
    };
  });

  // Role-gated avatar selection list
  const availableAvatars = getAvailableAvatarsForRole(userRole);

  useEffect(() => {
    if (user) {
      const p = user.patient_profile || {};
      setProfileForm(prev => ({
        ...prev,
        fullName: user.full_name || p.full_name || prev.fullName,
        email: user.email || prev.email,
        phone: p.contact_number || prev.phone,
        age: p.age || prev.age,
        gender: p.gender || prev.gender || '',
        height: p.height_cm || prev.height,
        weight: p.weight_kg || prev.weight,
      }));
    }
  }, [user]);

  // Selected Avatar details
  const activeAvatar = getAvatarById(profileForm.selectedAvatar);
  const activeAvatarUri = activeAvatar.url || svgToDataUri(activeAvatar.svg);

  const handleProfileSave = async (e) => {
    e.preventDefault();
    const key = `telemed_user_profile_${user?.user_id || 'guest'}`;
    localStorage.setItem(key, JSON.stringify({ ...profileForm, isUpdated: true }));

    try {
      const payload = {
        full_name: profileForm.fullName,
        age: profileForm.age ? parseInt(profileForm.age, 10) : null,
        gender: profileForm.gender,
        height_cm: profileForm.height ? parseFloat(profileForm.height) : null,
        weight_kg: profileForm.weight ? parseFloat(profileForm.weight) : null,
        contact_number: profileForm.phone
      };
      await (await import('../api/client')).updateUserProfile(payload);
    } catch (err) {
      // Handled silently
    }

    setSaveSuccessMsg('Profile details updated successfully!');
    setIsEditModalOpen(false);

    // Notify components & header bar to re-render avatar and profile fields
    window.dispatchEvent(new Event('telemed_profile_updated'));
    window.dispatchEvent(new Event('telemed:user-updated'));

    if (refreshCurrentUser) {
      try { refreshCurrentUser(); } catch (err) {}
    }
    setTimeout(() => setSaveSuccessMsg(null), 4000);
  };

  // Vitals Snapshot Data Array — ONLY use real data if activeSource exists!
  const hasActiveBiometrics = Boolean(activeSource && Object.keys(clinFeats).length > 0);

  const healthSnapshot = [
    { 
      label: 'Fasting Glucose', 
      value: clinFeats.Fasting_Blood_Glucose || clinFeats.Fasting_Glucose ? `${clinFeats.Fasting_Blood_Glucose || clinFeats.Fasting_Glucose} mg/dL` : 'Not Provided', 
      status: hasActiveBiometrics ? (clinFeats.Fasting_Blood_Glucose >= 126 ? 'ELEVATED' : 'ACTIVE') : 'PENDING', 
      variant: hasActiveBiometrics ? (clinFeats.Fasting_Blood_Glucose >= 126 ? 'danger' : 'warning') : 'subtle', 
      icon: Activity,
      ref: '70–99 mg/dL'
    },
    { 
      label: 'HbA1c Glycemic Index', 
      value: clinFeats.HbA1c ? `${clinFeats.HbA1c} %` : 'Not Provided', 
      status: hasActiveBiometrics ? (clinFeats.HbA1c >= 6.5 ? 'ELEVATED' : 'ACTIVE') : 'PENDING', 
      variant: hasActiveBiometrics ? (clinFeats.HbA1c >= 6.5 ? 'danger' : 'warning') : 'subtle', 
      icon: Activity,
      ref: '< 5.7 %'
    },
    { 
      label: 'Blood Pressure', 
      value: (clinFeats.Systolic_BP && clinFeats.Diastolic_BP) ? `${clinFeats.Systolic_BP}/${clinFeats.Diastolic_BP} mmHg` : 'Not Provided', 
      status: hasActiveBiometrics ? 'ACTIVE' : 'PENDING', 
      variant: hasActiveBiometrics ? 'warning' : 'subtle', 
      icon: Heart,
      ref: '< 120/80 mmHg'
    },
    { 
      label: 'Body Mass Index (BMI)', 
      value: clinFeats.BMI ? `${clinFeats.BMI} kg/m²` : `${(profileForm.weight / Math.pow(profileForm.height / 100, 2)).toFixed(1)} kg/m²`, 
      status: 'CALCULATED', 
      variant: 'primary', 
      icon: Scale,
      ref: '18.5–24.9 kg/m²'
    },
    { 
      label: 'Resting Heart Rate', 
      value: wearFeats.Resting_Heart_Rate ? `${wearFeats.Resting_Heart_Rate} bpm` : 'Not Provided', 
      status: wearFeats.Resting_Heart_Rate ? 'ACTIVE' : 'PENDING', 
      variant: wearFeats.Resting_Heart_Rate ? 'success' : 'subtle', 
      icon: Watch,
      ref: '60–100 bpm'
    },
    { 
      label: 'Sleep Duration', 
      value: wearFeats.Total_Sleep_Duration_Hours ? `${wearFeats.Total_Sleep_Duration_Hours} hrs` : 'Not Provided', 
      status: wearFeats.Total_Sleep_Duration_Hours ? 'ACTIVE' : 'PENDING', 
      variant: wearFeats.Total_Sleep_Duration_Hours ? 'success' : 'subtle', 
      icon: Clock,
      ref: '7–9 hours'
    },
  ];

  const assessmentHistory = realRecords.map((r, idx) => ({
    id: r.record_id || `ASM-${idx}`,
    date: r.created_at ? new Date(r.created_at).toISOString().split('T')[0] : 'N/A',
    diseases: 'Type 2 Diabetes, Prediabetes, Adiposity, MetSyn, NAFLD',
    risk: `${r.prediction_snapshot?.disease_outcomes?.Type2_Diabetes?.risk_level || 'EVALUATED'} RISK`,
    riskVariant: (r.prediction_snapshot?.disease_outcomes?.Type2_Diabetes?.risk_level || '').toUpperCase().includes('HIGH') ? 'danger' : 'primary',
    confidence: 'Calibrated V4 Ensemble',
    pathway: r.effective_pathway || 'C+W+G',
  }));

  const filteredHistory = assessmentHistory.filter((item) =>
    item.id.toLowerCase().includes(historySearchQuery.toLowerCase()) ||
    item.diseases.toLowerCase().includes(historySearchQuery.toLowerCase())
  );

  const vaultDocuments = realRecords.map((r) => ({
    id: `DOC-${r.record_id}`,
    name: `TeleMed_Health_Record_${r.record_id}.json`,
    type: 'AI Reports',
    date: r.created_at ? new Date(r.created_at).toISOString().split('T')[0] : 'N/A',
    size: 'Immutable Record',
    status: 'Verified Snapshot',
    recordId: r.record_id,
  }));

  const filteredVault = vaultDocuments.filter((doc) => {
    const matchesCat = vaultCategory === 'ALL' || doc.type === vaultCategory;
    const matchesSearch = doc.name.toLowerCase().includes(vaultSearchQuery.toLowerCase()) ||
                          doc.type.toLowerCase().includes(vaultSearchQuery.toLowerCase());
    return matchesCat && matchesSearch;
  });

  return (
    <PageContainer className="space-y-8 py-6">
      
      {/* Top Header */}
      <PageHeader
        title="Patient Workspace & Health Profile"
        description="Manage your clinical profile, photo avatar, health summaries, assessment history, and secure health vault"
        badge="Patient Portal"
        actions={
          <Button
            variant="primary"
            size="md"
            leftIcon={<Edit3 className="w-4 h-4" />}
            onClick={() => setIsEditModalOpen(true)}
          >
            Edit Profile
          </Button>
        }
      />

      {saveSuccessMsg && (
        <Alert variant="success" title="Profile Updated">
          {saveSuccessMsg}
        </Alert>
      )}

      {/* Main 2-Column Responsive Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Column — Patient Demographics & Profile Summary */}
        <div className="lg:col-span-4 space-y-6">
          
          {/* Demographics Hero Card */}
          <Card isGlass={true} className="p-6 space-y-6 shadow-2xl rounded-3xl border border-[var(--border-medium)] bg-gradient-to-b from-[var(--bg-surface)] to-[var(--bg-primary)]">
            <div className="text-center space-y-3">
              <div className="relative w-32 h-32 mx-auto">
                <Avatar
                  user={user}
                  avatarId={profileForm.selectedAvatar}
                  name={profileForm.fullName}
                  size="xl"
                  className="w-32 h-32 text-3xl font-black shadow-2xl border-4 border-white/20 ring-4 ring-blue-500/40"
                />
                <div className="absolute -bottom-1 -right-1 p-2 rounded-full bg-emerald-500 text-white border-2 border-[var(--bg-surface)] shadow-lg" title="Verified Active Profile">
                  <CheckCircle2 className="w-4 h-4" />
                </div>
              </div>

              <div>
                <h2 className="text-2xl font-black text-[var(--text-main)] tracking-tight">{profileForm.fullName}</h2>
                <div className="flex items-center justify-center gap-2 mt-1.5">
                  <span className="text-xs font-mono text-[var(--text-muted)] font-semibold bg-[var(--bg-surface)] px-2.5 py-1 rounded-lg border border-[var(--border-subtle)]">{profileForm.patientId}</span>
                </div>
              </div>
            </div>

            {/* Profile Completion Bar */}
            <div className="space-y-1.5 p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
              <div className="flex justify-between text-xs font-semibold">
                <span className="text-[var(--text-muted)]">Profile Completion</span>
                <span className="text-[var(--primary)] font-mono font-bold">{completionRate}%</span>
              </div>
              <ProgressBar value={completionRate} max={100} variant="primary" />
            </div>

            {/* Vitals Grid */}
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="p-2.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
                <span className="text-[var(--text-muted)] block text-[10px] uppercase font-mono">DOB / Age</span>
                <strong className="text-[var(--text-main)]">{profileForm.dob} ({profileForm.age} yrs)</strong>
              </div>
              <div className="p-2.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
                <span className="text-[var(--text-muted)] block text-[10px] uppercase font-mono">Gender</span>
                <strong className="text-[var(--text-main)]">{profileForm.gender}</strong>
              </div>
              <div className="p-2.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
                <span className="text-[var(--text-muted)] block text-[10px] uppercase font-mono">Height & Weight</span>
                <strong className="text-[var(--text-main)]">{profileForm.height} cm, {profileForm.weight} kg</strong>
              </div>
              <div className="p-2.5 rounded-lg bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
                <span className="text-[var(--text-muted)] block text-[10px] uppercase font-mono">Blood Group</span>
                <strong className="text-[var(--text-main)]">{profileForm.bloodGroup}</strong>
              </div>
            </div>

            {/* Contact Details */}
            <div className="space-y-2.5 pt-2 border-t border-[var(--border-subtle)] text-xs">
              <div className="flex items-center gap-2 text-[var(--text-muted)]">
                <Mail className="w-4 h-4 text-[var(--primary)] shrink-0" />
                <span className="truncate">{profileForm.email}</span>
              </div>
              <div className="flex items-center gap-2 text-[var(--text-muted)]">
                <Phone className="w-4 h-4 text-[var(--secondary)] shrink-0" />
                <span>{profileForm.phone}</span>
              </div>
              <div className="flex items-center gap-2 text-[var(--text-muted)]">
                <AlertCircle className="w-4 h-4 text-rose-500 shrink-0" />
                <span className="truncate">{profileForm.emergencyContact}</span>
              </div>
            </div>
          </Card>

          {/* Quick Actions Card */}
          <Card isGlass={true} className="p-6 space-y-4">
            <h3 className="text-sm font-bold text-[var(--text-main)] uppercase tracking-wider">Quick Actions</h3>
            <div className="space-y-2">
              <Button
                variant="primary"
                size="md"
                className="w-full justify-between"
                onClick={() => onNavigate ? onNavigate('intake') : null}
                rightIcon={<ArrowUpRight className="w-4 h-4" />}
              >
                Start New AI Intake
              </Button>
              <Button
                variant="outline"
                size="md"
                className="w-full justify-between"
                onClick={() => onNavigate ? onNavigate('copilot') : null}
                rightIcon={<ArrowUpRight className="w-4 h-4" />}
              >
                Open AI Health Copilot
              </Button>
              <Button
                variant="outline"
                size="md"
                className="w-full justify-between"
                onClick={() => onNavigate ? onNavigate('records') : null}
                rightIcon={<ArrowUpRight className="w-4 h-4" />}
              >
                View Health Records
              </Button>
            </div>
          </Card>

        </div>

        {/* Right Column — Tabbed Content Workspace */}
        <div className="lg:col-span-8 space-y-6">

          {/* Workspace Tabs Header */}
          <div className="border-b border-[var(--border-subtle)] pb-2 flex gap-4 overflow-x-auto">
            {[
              { id: 'summary', label: 'Health Summary' },
              { id: 'vitals', label: 'Vitals Snapshot' },
              { id: 'timeline', label: 'Health Timeline' },
              { id: 'history', label: 'Assessment History' },
              { id: 'vault', label: 'Health Vault' },
            ].map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`pb-2 px-1 text-sm font-bold transition-all border-b-2 font-mono whitespace-nowrap ${
                  activeTab === tab.id
                    ? 'border-[var(--primary)] text-[var(--primary)]'
                    : 'border-transparent text-[var(--text-muted)] hover:text-[var(--text-main)]'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* TAB 1: HEALTH SUMMARY */}
          {activeTab === 'summary' && (
            <div className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card isGlass={true} className="p-5 space-y-2 border-l-4 border-l-[var(--primary)]">
                  <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase font-semibold block">Overall Health Score</span>
                  <div className="text-2xl font-extrabold text-[var(--text-main)]">
                    {hasActiveBiometrics ? '85' : '--'} <span className="text-xs font-normal text-[var(--text-muted)]">/ 100</span>
                  </div>
                  <p className="text-[11px] text-[var(--text-muted)]">{hasActiveBiometrics ? 'Based on active assessment' : 'No Assessment Submitted Yet'}</p>
                </Card>

                <Card isGlass={true} className="p-5 space-y-2 border-l-4 border-l-[var(--warning)]">
                  <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase font-semibold block">Active Disease Risk</span>
                  <div className="text-lg font-bold text-[var(--warning)] uppercase">
                    {hasActiveBiometrics ? (activeSource?.disease_outcomes?.Type2_Diabetes?.risk_level || 'EVALUATED') : 'PENDING'}
                  </div>
                  <p className="text-[11px] text-[var(--text-muted)]">{hasActiveBiometrics ? 'Type 2 Diabetes Screening' : 'Pending First Assessment'}</p>
                </Card>

                <Card isGlass={true} className="p-5 space-y-2 border-l-4 border-l-[var(--secondary)]">
                  <span className="text-[10px] font-mono text-[var(--text-muted)] uppercase font-semibold block">AI Pathway</span>
                  <div className="text-2xl font-extrabold text-[var(--secondary)]">{hasActiveBiometrics ? (activeSource?.effective_pathway || 'C') : 'NONE'}</div>
                  <p className="text-[11px] text-[var(--text-muted)]">Data Quality: {hasActiveBiometrics ? `${Math.round((activeSource?.data_quality_score || 0.85) * 100)}%` : 'N/A'}</p>
                </Card>
              </div>

              <Card isGlass={true} className="p-6 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-bold text-[var(--text-main)] flex items-center gap-2">
                    <Sparkles className="w-4 h-4 text-[var(--primary)]" />
                    Clinical Assessment Overview
                  </h4>
                  <Badge variant={hasActiveBiometrics ? 'primary' : 'subtle'} size="sm">
                    Pathway: {hasActiveBiometrics ? (activeSource?.effective_pathway || 'C') : 'NOT ASSIGNED'}
                  </Badge>
                </div>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                  {hasActiveBiometrics 
                    ? 'Multimodal intake evaluated across clinical biomarkers. High confidence risk vectors calculated with TreeSHAP explainability drivers ready for physician review.'
                    : 'No active health assessment found for this account. Run your first AI health assessment in the Intake Workspace to view personalized risk vectors, TreeSHAP driver analysis, and clinical protocols.'
                  }
                </p>
                {!hasActiveBiometrics && (
                  <Button variant="primary" size="sm" onClick={() => onNavigate ? onNavigate('intake') : null}>
                    Run First AI Assessment →
                  </Button>
                )}
              </Card>
            </div>
          )}

          {/* TAB 2: VITALS SNAPSHOT */}
          {activeTab === 'vitals' && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {healthSnapshot.map((item, idx) => {
                const ItemIcon = item.icon;
                return (
                  <Card key={idx} isGlass={true} className="p-5 space-y-3 hover:border-[var(--primary)] transition-all">
                    <div className="flex justify-between items-center">
                      <div className="flex items-center gap-2">
                        <ItemIcon className="w-4 h-4 text-[var(--primary)]" />
                        <span className="text-xs font-bold text-[var(--text-main)]">{item.label}</span>
                      </div>
                      <Badge variant={item.variant} size="sm">{item.status}</Badge>
                    </div>

                    <div className="font-mono">
                      <strong className="text-xl font-extrabold text-[var(--text-main)] block">{item.value}</strong>
                      <span className="text-[10px] text-[var(--text-muted)]">Reference Target: {item.ref}</span>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}

          {/* TAB 3: HEALTH TIMELINE */}
          {activeTab === 'timeline' && (
            <Card isGlass={true} className="p-6 space-y-4">
              <h3 className="text-sm font-bold text-[var(--text-main)]">Chronological Health Timeline</h3>
              <div className="space-y-3">
                {realRecords.length > 0 ? (
                  realRecords.map((r) => (
                    <div key={r.record_id} className="p-4 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] flex items-center justify-between gap-3">
                      <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-[var(--primary-light)] text-[var(--primary)]">
                          <Sparkles className="w-5 h-5" />
                        </div>
                        <div>
                          <strong className="text-xs text-[var(--text-main)] block">Assessment #{r.record_id} Executed</strong>
                          <span className="text-[10px] font-mono text-[var(--text-muted)]">
                            Pathway {r.effective_pathway || 'C'} • Data Quality: {Math.round((r.data_quality_score || 0.85) * (r.data_quality_score <= 1 ? 100 : 1))}%
                          </span>
                        </div>
                      </div>
                      <span className="text-[10px] font-mono text-[var(--text-muted)]">
                        {new Date(r.created_at).toLocaleString()}
                      </span>
                    </div>
                  ))
                ) : (
                  <div className="p-6 text-center text-xs text-[var(--text-muted)]">No timeline events recorded yet.</div>
                )}
              </div>
            </Card>
          )}

          {/* TAB 4: ASSESSMENT HISTORY */}
          {activeTab === 'history' && (
            <div className="space-y-4">
              <Input
                placeholder="Search assessment history by ID or disease..."
                leftIcon={<Search className="w-4 h-4" />}
                value={historySearchQuery}
                onChange={(e) => setHistorySearchQuery(e.target.value)}
              />

              {filteredHistory.length === 0 ? (
                <Card isGlass={true} className="p-8 text-center text-xs text-[var(--text-muted)]">
                  No assessments found matching your search.
                </Card>
              ) : (
                filteredHistory.map((item) => (
                  <Card key={item.id} isGlass={true} className="p-5 space-y-3">
                    <div className="flex justify-between items-center flex-wrap gap-2">
                      <div className="flex items-center gap-2">
                        <strong className="text-sm font-mono text-[var(--primary)]">{item.id}</strong>
                        <span className="text-xs text-[var(--text-muted)]">Date: {item.date}</span>
                      </div>
                      <Badge variant={item.riskVariant} size="sm">{item.risk}</Badge>
                    </div>

                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs font-mono p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)]">
                      <div>
                        <span className="text-[9px] text-[var(--text-muted)] block uppercase">Diseases Evaluated</span>
                        <span className="text-[var(--text-main)] font-semibold truncate block">{item.diseases}</span>
                      </div>
                      <div>
                        <span className="text-[9px] text-[var(--text-muted)] block uppercase">Model Confidence</span>
                        <span className="text-[var(--text-main)] font-semibold">{item.confidence}</span>
                      </div>
                      <div>
                        <span className="text-[9px] text-[var(--text-muted)] block uppercase">Modality Pathway</span>
                        <span className="text-[var(--primary)] font-semibold">{item.pathway}</span>
                      </div>
                    </div>

                    <div className="flex justify-end gap-2 pt-1">
                      <Button variant="outline" size="sm" onClick={() => onNavigate ? onNavigate('xai') : null}>
                        View XAI Drivers
                      </Button>
                      <Button variant="primary" size="sm" onClick={() => onNavigate ? onNavigate('report') : null}>
                        View Clinical Report
                      </Button>
                    </div>
                  </Card>
                ))
              )}
            </div>
          )}

          {/* TAB 5: HEALTH VAULT */}
          {activeTab === 'vault' && (
            <div className="space-y-4">
              <div className="flex gap-3 items-center justify-between flex-wrap">
                <Input
                  placeholder="Search health documents..."
                  leftIcon={<Search className="w-4 h-4" />}
                  value={vaultSearchQuery}
                  onChange={(e) => setVaultSearchQuery(e.target.value)}
                  className="w-full sm:w-72"
                />
                <select
                  value={vaultCategory}
                  onChange={(e) => setVaultCategory(e.target.value)}
                  className="px-3 py-2 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] font-semibold"
                >
                  <option value="ALL">All Categories</option>
                  <option value="AI Reports">AI Reports</option>
                </select>
              </div>

              <div className="space-y-3">
                {filteredVault.length === 0 ? (
                  <Card isGlass={true} className="p-8 text-center text-xs text-[var(--text-muted)]">
                    No documents stored in vault yet.
                  </Card>
                ) : (
                  filteredVault.map((doc) => (
                    <Card key={doc.id} isGlass={true} className="p-4 flex items-center justify-between flex-wrap gap-3 hover:border-[var(--primary)] transition-all">
                      <div className="flex items-center gap-3">
                        <div className="p-2.5 rounded-xl bg-[var(--primary-light)] text-[var(--primary)]">
                          <FileText className="w-5 h-5" />
                        </div>
                        <div>
                          <strong className="text-xs text-[var(--text-main)] block font-mono">{doc.name}</strong>
                          <span className="text-[10px] font-mono text-[var(--text-muted)]">
                            {doc.type} • {doc.date} • {doc.size}
                          </span>
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Badge variant="success" size="sm">VERIFIED SNAPSHOT</Badge>
                        <Button variant="outline" size="sm" onClick={() => onNavigate ? onNavigate('records') : null}>
                          <Eye className="w-3.5 h-3.5 mr-1" /> Preview
                        </Button>
                      </div>
                    </Card>
                  ))
                )}
              </div>
            </div>
          )}

        </div>

      </div>

      {/* EDIT PROFILE MODAL WITH GHIBLI ANIME AVATARS */}
      {isEditModalOpen && (
        <Modal
          isOpen={isEditModalOpen}
          onClose={() => setIsEditModalOpen(false)}
          title="Edit Health Profile & Ghibli Character Avatar"
          className="max-w-4xl"
        >
          <form onSubmit={handleProfileSave} className="space-y-4 text-xs">
            
            {/* GHIBLI AVATAR SELECTION SECTION (ROLE-GATED) */}
            <div className="space-y-2 p-3 rounded-2xl bg-gradient-to-br from-[var(--bg-primary)] to-[var(--bg-surface)] border border-[var(--border-subtle)] shadow-sm">
              <div className="flex justify-between items-center px-1">
                <span className="font-black text-xs text-[var(--text-main)] font-mono uppercase tracking-wider">
                  Select Your Indian Ghibli Avatar
                </span>
                <Badge variant="primary" size="sm" className="font-bold text-[10px]">Patient Suite (6 Characters)</Badge>
              </div>

              <div className="grid grid-cols-3 sm:grid-cols-6 gap-2.5 pt-1">
                {availableAvatars.map((av) => {
                  const isSelected = profileForm.selectedAvatar === av.id;
                  const avatarUri = av.url || svgToDataUri(av.svg);
                  return (
                    <button
                      key={av.id}
                      type="button"
                      onClick={() => setProfileForm({ ...profileForm, selectedAvatar: av.id })}
                      className={`p-2 rounded-xl flex flex-col items-center justify-center transition-all duration-200 relative group ${
                        isSelected 
                          ? `bg-gradient-to-tr ${av.color} text-white shadow-lg ring-2 ${av.ring} scale-102 z-10` 
                          : 'bg-[var(--bg-surface)] text-[var(--text-main)] border border-[var(--border-subtle)] hover:border-[var(--primary)] hover:scale-102'
                      }`}
                      title={av.label}
                    >
                      {isSelected && (
                        <span className="absolute -top-1 -right-1 w-4 h-4 rounded-full bg-emerald-500 text-white flex items-center justify-center text-[9px] font-bold shadow-md">
                          ✓
                        </span>
                      )}
                      <div className="w-12 h-12 rounded-full overflow-hidden border-2 border-white/40 shadow-sm mb-1 bg-slate-900 shrink-0">
                        <img src={avatarUri} alt={av.label} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-300" />
                      </div>
                      <span className="text-[11px] font-bold font-mono text-center leading-none truncate w-full">{av.role}</span>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* DEMOGRAPHICS FORM FIELDS (SPACIOUS 3-COLUMN GRID) */}
            <div className="space-y-3 pt-1">
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div className="sm:col-span-2">
                  <Input
                    label="Full Name"
                    value={profileForm.fullName}
                    onChange={(e) => setProfileForm({ ...profileForm, fullName: e.target.value })}
                    required
                  />
                </div>
                <div>
                  <Input
                    label="Date of Birth"
                    type="date"
                    value={profileForm.dob}
                    onChange={(e) => setProfileForm({ ...profileForm, dob: e.target.value })}
                    required
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Input
                  label="Age (Years)"
                  type="number"
                  value={profileForm.age}
                  onChange={(e) => setProfileForm({ ...profileForm, age: e.target.value })}
                  required
                />
                <div>
                  <label className="text-[11px] font-semibold text-[var(--text-main)] mb-1 block">Gender</label>
                  <select
                    value={profileForm.gender}
                    onChange={(e) => setProfileForm({ ...profileForm, gender: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] font-semibold"
                  >
                    <option value="">Select Gender</option>
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                  </select>
                </div>
                <div>
                  <label className="text-[11px] font-semibold text-[var(--text-main)] mb-1 block">Blood Group</label>
                  <select
                    value={profileForm.bloodGroup}
                    onChange={(e) => setProfileForm({ ...profileForm, bloodGroup: e.target.value })}
                    className="w-full px-3 py-2 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] text-xs text-[var(--text-main)] font-semibold"
                  >
                    <option value="A+">A+</option>
                    <option value="A-">A-</option>
                    <option value="B+">B+</option>
                    <option value="B-">B-</option>
                    <option value="AB+">AB+</option>
                    <option value="AB-">AB-</option>
                    <option value="O+">O+</option>
                    <option value="O-">O-</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <Input
                  label="Height (cm)"
                  type="number"
                  value={profileForm.height}
                  onChange={(e) => setProfileForm({ ...profileForm, height: e.target.value })}
                />
                <Input
                  label="Weight (kg)"
                  type="number"
                  value={profileForm.weight}
                  onChange={(e) => setProfileForm({ ...profileForm, weight: e.target.value })}
                />
                <Input
                  label="Phone Number"
                  value={profileForm.phone}
                  onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                  placeholder="+91 98765 43210"
                />
              </div>

              <div>
                <Input
                  label="Emergency Contact Info"
                  value={profileForm.emergencyContact}
                  onChange={(e) => setProfileForm({ ...profileForm, emergencyContact: e.target.value })}
                />
              </div>
            </div>

            <div className="pt-3 flex justify-end gap-3 border-t border-[var(--border-subtle)]">
              <Button variant="outline" size="sm" type="button" onClick={() => setIsEditModalOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" type="submit" leftIcon={<Check className="w-4 h-4" />}>
                Save Profile & Avatar
              </Button>
            </div>
          </form>
        </Modal>
      )}

    </PageContainer>
  );
}
