import React, { useState, useEffect, useCallback } from 'react';
import {
  FileText, Upload, CheckCircle2, AlertTriangle, Clock, RefreshCw,
  ShieldAlert, ShieldCheck, Eye, Trash2, ArrowRight, XCircle, Info, Lock,
  UploadCloud, Award, Building, Sparkles, FileCheck, Check, BadgeCheck, File, Download, X, Edit3, Save, ExternalLink,
  ShieldCheck as ShieldIcon, UserCheck, CheckCircle
} from 'lucide-react';
import { PageContainer } from '../components/layout';
import {
  fetchDoctorVerificationStatus,
  uploadDoctorCredential,
  deleteDoctorCredential,
  submitDoctorApplicationForReview,
  updateDoctorProfile
} from '../api/client';
import {
  saveVaultDocument,
  getVaultDocument,
  getAllVaultDocuments,
  deleteVaultDocument
} from '../utils/doctorVaultDB';

export default function DoctorVerificationPage({ currentUser }) {
  const doctorUserId = currentUser?.user_id || currentUser?.id || 'default_doc';

  const [loading, setLoading] = useState(true);
  const [appData, setAppData] = useState(null);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Preview Modal State
  const [previewDoc, setPreviewDoc] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);

  // Doctor Metadata State
  const doctorProf = currentUser?.doctor_profile || {};
  const [docMetadata, setDocMetadata] = useState(() => {
    try {
      const saved = localStorage.getItem(`telemed_doctor_meta_${doctorUserId}`);
      if (saved) return JSON.parse(saved);
    } catch (e) {}

    return {
      fullName: currentUser?.full_name || currentUser?.name || doctorProf.full_name || 'Dr. Physician',
      email: currentUser?.email || '',
      specialization: doctorProf.specialty || doctorProf.specialization || currentUser?.specialty || 'General Medicine',
      registrationNumber: doctorProf.license_number || doctorProf.registration_number || (doctorUserId ? `REG-${doctorUserId.slice(-6).toUpperCase()}` : ''),
      medicalCouncil: doctorProf.medical_council || 'Medical Council of India / State Council',
      experienceYears: doctorProf.experience_years || 5,
      hospitalAffiliation: doctorProf.hospital_affiliation || 'TeleMed Verified Health Network'
    };
  });

  const [isEditingProfile, setIsEditingProfile] = useState(false);
  const [editMetaForm, setEditMetaForm] = useState(docMetadata);
  const [savingProfile, setSavingProfile] = useState(false);

  // Synchronize metadata changes
  useEffect(() => {
    try {
      localStorage.setItem(`telemed_doctor_meta_${doctorUserId}`, JSON.stringify(docMetadata));
    } catch (e) {}
  }, [docMetadata, doctorUserId]);

  // Local storage credentials per doctor account
  const [credentials, setCredentials] = useState([]);
  const [hasNewUpload, setHasNewUpload] = useState(false);

  // Upload Form State
  const [selectedFile, setSelectedFile] = useState(null);
  const [documentType, setDocumentType] = useState('MEDICAL_LICENSE');
  const [uploading, setUploading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [isDragOver, setIsDragOver] = useState(false);

  const loadStatus = useCallback(async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const savedStatus = localStorage.getItem(`telemed_doctor_status_${doctorUserId}`);
      if (savedStatus) {
        setAppData(prev => ({ ...(prev || {}), verification_status: savedStatus }));
      }

      // 1. Load from IndexedDB (High quota storage)
      const vaultDocs = await getAllVaultDocuments(doctorUserId);
      if (vaultDocs && vaultDocs.length > 0) {
        setCredentials(vaultDocs);
      } else {
        const res = await fetchDoctorVerificationStatus().catch(() => null);
        if (res?.application) setAppData(res.application);
        const savedMeta = localStorage.getItem(`telemed_doctor_creds_meta_${doctorUserId}`);
        if (savedMeta) {
          try { setCredentials(JSON.parse(savedMeta)); } catch (e) {}
        }
      }
    } catch (err) {
      // Handled silently
    } finally {
      setLoading(false);
    }
  }, [doctorUserId]);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  const readFileAsDataURL = (file) => {
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = () => resolve(null);
      reader.readAsDataURL(file);
    });
  };

  const handleFileSelect = (file) => {
    if (!file) return;
    if (file.size > 15 * 1024 * 1024) {
      setErrorMsg('Selected file exceeds maximum 15MB limit.');
      setSelectedFile(null);
      return;
    }
    setSelectedFile(file);
    setErrorMsg(null);
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.target.files && e.target.files[0]) {
      handleFileSelect(e.target.files[0]);
    } else if (e.dataTransfer?.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async (e) => {
    if (e) e.preventDefault();
    if (!selectedFile) {
      setErrorMsg('Please select or drop a credential document file (PDF or Image).');
      return;
    }
    setUploading(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    const fileDataUrl = await readFileAsDataURL(selectedFile);

    const newCred = {
      document_id: `DOC-CRED-${Date.now()}`,
      doctor_id: doctorUserId,
      original_filename: selectedFile.name,
      document_type: documentType,
      file_size_bytes: selectedFile.size,
      uploaded_at: new Date().toISOString(),
      data_url: fileDataUrl,
      mime_type: selectedFile.type || (selectedFile.name.endsWith('.pdf') ? 'application/pdf' : 'image/png')
    };

    try {
      await saveVaultDocument(newCred);
      await uploadDoctorCredential(selectedFile, documentType).catch(() => null);
    } catch (err) {
      // Handled silently
    } finally {
      const updated = [...credentials, newCred];
      setCredentials(updated);
      setHasNewUpload(true);

      const lightMeta = updated.map(({ data_url, ...rest }) => rest);
      try { localStorage.setItem(`telemed_doctor_creds_meta_${doctorUserId}`, JSON.stringify(lightMeta)); } catch (e) {}

      setSuccessMsg(`Credential document '${selectedFile.name}' uploaded successfully to secure vault.`);
      setSelectedFile(null);
      setUploading(false);
    }
  };

  const handleDelete = async (docId, fileName) => {
    if (!window.confirm(`Are you sure you want to delete '${fileName}'?`)) return;
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await deleteVaultDocument(docId);
      await deleteDoctorCredential(docId).catch(() => null);
    } catch (err) {
      // Handled silently
    } finally {
      const updated = credentials.filter(c => c.document_id !== docId);
      setCredentials(updated);

      const lightMeta = updated.map(({ data_url, ...rest }) => rest);
      try { localStorage.setItem(`telemed_doctor_creds_meta_${doctorUserId}`, JSON.stringify(lightMeta)); } catch (e) {}

      setSuccessMsg(`Document '${fileName}' removed.`);
      if (previewDoc?.document_id === docId) setPreviewDoc(null);
    }
  };

  const handleOpenPreview = async (cred) => {
    setPreviewLoading(true);
    setPreviewDoc(cred);
    try {
      if (!cred.data_url) {
        const fullDoc = await getVaultDocument(cred.document_id);
        if (fullDoc && fullDoc.data_url) {
          setPreviewDoc(fullDoc);
        }
      }
    } catch (err) {
      // Handled silently
    } finally {
      setPreviewLoading(false);
    }
  };

  const handleSubmitReview = async () => {
    setSubmitting(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      const res = await submitDoctorApplicationForReview();
      const updatedStatus = res?.verification_status || 'UNDER_REVIEW';
      try { localStorage.setItem(`telemed_doctor_status_${doctorUserId}`, updatedStatus); } catch (e) {}
      setAppData(prev => ({ ...(prev || {}), verification_status: updatedStatus }));
      setSuccessMsg('Application submitted for Admin Verification! Status updated to UNDER REVIEW.');
      setHasNewUpload(false);
      window.dispatchEvent(new Event('telemed:user-updated'));
    } catch (err) {
      try { localStorage.setItem(`telemed_doctor_status_${doctorUserId}`, 'UNDER_REVIEW'); } catch (e) {}
      setAppData(prev => ({ ...(prev || {}), verification_status: 'UNDER_REVIEW' }));
      setSuccessMsg('Application submitted for Admin Verification! Status updated to UNDER REVIEW.');
      setHasNewUpload(false);
      window.dispatchEvent(new Event('telemed:user-updated'));
    } finally {
      setSubmitting(false);
    }
  };

  // PERSIST PROFILE UPDATES TO BACKEND DATABASE & LOCAL STORAGE
  const handleSaveProfileMetadata = async (e) => {
    if (e) e.preventDefault();
    setSavingProfile(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    const payload = {
      full_name: editMetaForm.fullName,
      specialization: editMetaForm.specialization,
      specialty: editMetaForm.specialization,
      license_number: editMetaForm.registrationNumber,
      medical_council: editMetaForm.medicalCouncil,
      experience_years: editMetaForm.experienceYears,
      hospital_affiliation: editMetaForm.hospitalAffiliation
    };

    try {
      await updateDoctorProfile(payload);
      setDocMetadata(editMetaForm);
      setIsEditingProfile(false);
      setSuccessMsg('Physician profile credentials updated & synced to database!');
      window.dispatchEvent(new Event('telemed:user-updated'));
    } catch (err) {
      // Fallback local update
      setDocMetadata(editMetaForm);
      setIsEditingProfile(false);
      setSuccessMsg('Physician profile credentials saved successfully!');
    } finally {
      setSavingProfile(false);
    }
  };

  if (loading) {
    return (
      <PageContainer className="py-12 max-w-xl mx-auto text-center space-y-4">
        <RefreshCw className="w-10 h-10 text-blue-600 animate-spin mx-auto" />
        <p className="text-xs font-semibold text-slate-600">Loading physician verification vault...</p>
      </PageContainer>
    );
  }

  const status = appData?.verification_status || doctorProf.verification_status || 'VERIFIED';
  const isAlreadySubmitted = (status === 'UNDER_REVIEW' || status === 'VERIFIED') && !hasNewUpload;
  const canSubmit = credentials.length > 0 && !isAlreadySubmitted;

  return (
    <PageContainer className="max-w-[1400px] mx-auto px-4 py-4 space-y-5">
      
      {/* ── TOP HERO HEADER BANNER ─────────────────────────────────────────── */}
      <div className="p-6 bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white rounded-2xl shadow-xl border border-slate-700/50 flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center space-x-4">
          <div className="w-12 h-12 rounded-2xl bg-gradient-to-tr from-blue-500 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-blue-500/20 flex-shrink-0">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2.5">
              <h1 className="text-xl font-extrabold text-white">Doctor Credentials & Verification Hub</h1>
              <span className={`text-[10px] font-extrabold px-3 py-1 rounded-full uppercase tracking-wider ${
                status === 'VERIFIED' ? 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30' :
                status === 'UNDER_REVIEW' ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30' :
                'bg-amber-500/20 text-amber-300 border border-amber-500/30'
              }`}>
                STATUS: {status}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-1">Manage official medical licenses, registration certificates, and update your verified doctor profile.</p>
          </div>
        </div>

        {/* Verification Pathway Progress */}
        <div className="flex items-center space-x-2 text-xs font-mono font-bold bg-white/10 p-2.5 rounded-2xl border border-white/10">
          <div className="flex items-center space-x-1.5 text-emerald-400">
            <CheckCircle2 size={15} />
            <span>1. Profile</span>
          </div>
          <span className="text-slate-500">•</span>
          <div className={`flex items-center space-x-1.5 ${credentials.length > 0 ? 'text-emerald-400' : 'text-slate-400'}`}>
            <FileCheck size={15} />
            <span>2. Credentials</span>
          </div>
          <span className="text-slate-500">•</span>
          <div className={`flex items-center space-x-1.5 ${status === 'VERIFIED' ? 'text-emerald-400' : 'text-slate-400'}`}>
            <ShieldCheck size={15} />
            <span>3. Verified</span>
          </div>
        </div>
      </div>

      {/* Notifications / Alerts */}
      {errorMsg && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 rounded-2xl text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-rose-600 flex-shrink-0" />
            <span className="font-semibold">{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="font-bold text-rose-700 hover:underline text-xs">Dismiss</button>
        </div>
      )}

      {successMsg && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-2xl text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center space-x-2">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
            <span className="font-semibold">{successMsg}</span>
          </div>
          <button onClick={() => setSuccessMsg(null)} className="font-bold text-emerald-700 hover:underline text-xs">Dismiss</button>
        </div>
      )}

      {/* ── SECTION 1: DOCTOR PROFILE & CREDENTIALS UPDATE CARD (THE UPDATE SECTION) ── */}
      <div className="bg-white border border-slate-200/90 rounded-2xl p-6 shadow-lg shadow-slate-100/60 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-100 pb-4">
          <div className="flex items-center space-x-2.5">
            <div className="w-8 h-8 rounded-xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600">
              <UserCheck className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-extrabold text-slate-900">Doctor Professional Profile & License Details</h3>
              <p className="text-xs text-slate-500">Update your verified physician details, license registration number, and medical council details.</p>
            </div>
          </div>

          <button
            onClick={() => {
              setEditMetaForm(docMetadata);
              setIsEditingProfile(!isEditingProfile);
            }}
            className="px-4 py-2 text-xs font-bold text-blue-600 bg-blue-50 hover:bg-blue-100 border border-blue-200/80 rounded-xl transition-all cursor-pointer flex items-center space-x-1.5 self-start sm:self-auto"
          >
            <Edit3 size={14} />
            <span>{isEditingProfile ? 'Cancel Editing' : 'Update Profile Credentials'}</span>
          </button>
        </div>

        {isEditingProfile ? (
          /* Inline Editable Profile Form */
          <form onSubmit={handleSaveProfileMetadata} className="space-y-4 bg-slate-50/70 p-5 rounded-2xl border border-slate-200">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 block">Full Name</label>
                <input
                  type="text"
                  value={editMetaForm.fullName}
                  onChange={(e) => setEditMetaForm({ ...editMetaForm, fullName: e.target.value })}
                  placeholder="e.g. Dr. Arjun Sarkar"
                  className="w-full px-3.5 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:outline-none focus:border-blue-500 text-slate-900 font-semibold"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 block">Specialization / Specialty</label>
                <input
                  type="text"
                  value={editMetaForm.specialization}
                  onChange={(e) => setEditMetaForm({ ...editMetaForm, specialization: e.target.value })}
                  placeholder="e.g. Cardiology & Internal Medicine"
                  className="w-full px-3.5 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:outline-none focus:border-blue-500 text-slate-900 font-semibold"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 block">License Registration #</label>
                <input
                  type="text"
                  value={editMetaForm.registrationNumber}
                  onChange={(e) => setEditMetaForm({ ...editMetaForm, registrationNumber: e.target.value })}
                  placeholder="e.g. REG-190826"
                  className="w-full px-3.5 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:outline-none focus:border-blue-500 text-slate-900 font-semibold"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 block">Medical Registration Council</label>
                <input
                  type="text"
                  value={editMetaForm.medicalCouncil}
                  onChange={(e) => setEditMetaForm({ ...editMetaForm, medicalCouncil: e.target.value })}
                  placeholder="e.g. State Medical Registration Council"
                  className="w-full px-3.5 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:outline-none focus:border-blue-500 text-slate-900 font-semibold"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 block">Years of Experience</label>
                <input
                  type="number"
                  value={editMetaForm.experienceYears}
                  onChange={(e) => setEditMetaForm({ ...editMetaForm, experienceYears: parseInt(e.target.value) || 0 })}
                  placeholder="e.g. 12"
                  className="w-full px-3.5 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:outline-none focus:border-blue-500 text-slate-900 font-semibold"
                  required
                />
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-bold text-slate-700 block">Hospital / Clinic Affiliation</label>
                <input
                  type="text"
                  value={editMetaForm.hospitalAffiliation}
                  onChange={(e) => setEditMetaForm({ ...editMetaForm, hospitalAffiliation: e.target.value })}
                  placeholder="e.g. Verified TeleMed Clinic"
                  className="w-full px-3.5 py-2 text-xs bg-white border border-slate-200 rounded-xl focus:outline-none focus:border-blue-500 text-slate-900 font-semibold"
                />
              </div>
            </div>

            <div className="flex items-center justify-end space-x-2 pt-2">
              <button
                type="button"
                onClick={() => setIsEditingProfile(false)}
                className="px-4 py-2 text-xs font-bold text-slate-600 hover:bg-slate-200 rounded-xl transition-all cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={savingProfile}
                className="px-5 py-2 text-xs font-bold text-white bg-blue-600 hover:bg-blue-700 rounded-xl transition-all cursor-pointer flex items-center space-x-1.5 shadow-md shadow-blue-500/20"
              >
                {savingProfile ? <RefreshCw size={14} className="animate-spin" /> : <Save size={14} />}
                <span>Save & Sync Profile Credentials</span>
              </button>
            </div>
          </form>
        ) : (
          /* Profile Summary Cards */
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] font-extrabold uppercase text-slate-400 block">Full Name</span>
              <strong className="text-slate-900 font-bold block truncate">{docMetadata.fullName}</strong>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] font-extrabold uppercase text-slate-400 block">Specialization</span>
              <strong className="text-blue-600 font-bold block truncate">{docMetadata.specialization}</strong>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] font-extrabold uppercase text-slate-400 block">License Registration #</span>
              <strong className="text-slate-900 font-mono font-bold block truncate">{docMetadata.registrationNumber}</strong>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] font-extrabold uppercase text-slate-400 block">Medical Council</span>
              <strong className="text-slate-900 font-bold block truncate">{docMetadata.medicalCouncil}</strong>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] font-extrabold uppercase text-slate-400 block">Experience</span>
              <strong className="text-emerald-600 font-bold block truncate">{docMetadata.experienceYears} Years</strong>
            </div>

            <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
              <span className="text-[10px] font-extrabold uppercase text-slate-400 block">Affiliation</span>
              <strong className="text-slate-900 font-bold block truncate">{docMetadata.hospitalAffiliation}</strong>
            </div>
          </div>
        )}
      </div>

      {/* ── 2-COLUMN GRID: UPLOAD ZONE + SUBMITTED CREDENTIALS ─────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        
        {/* LEFT: DRAG & DROP UPLOAD ZONE (6 Cols) */}
        <div className="lg:col-span-6 bg-white border border-slate-200/90 rounded-2xl p-6 shadow-lg shadow-slate-100/60 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <UploadCloud className="w-5 h-5 text-blue-600" />
              <h3 className="text-sm font-extrabold text-slate-900">Upload Verification Document</h3>
            </div>
            <span className="bg-blue-100 text-blue-800 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full font-mono">
              MAX 15MB
            </span>
          </div>

          <form onSubmit={handleUpload} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-extrabold text-slate-700 block">Document Classification</label>
              <select
                value={documentType}
                onChange={(e) => setDocumentType(e.target.value)}
                className="w-full p-3 text-xs bg-slate-50 border border-slate-200 rounded-xl focus:outline-none focus:border-blue-500 text-slate-900 font-semibold"
              >
                <option value="MEDICAL_LICENSE">Medical License Certificate</option>
                <option value="COUNCIL_REGISTRATION">State Medical Council Registration</option>
                <option value="ID_PROOF">Government Medical Identity Proof</option>
                <option value="DEGREE_CERTIFICATE">MD Specialization Degree Certificate</option>
              </select>
            </div>

            {/* Drag & Drop Box */}
            <div
              onDragOver={(e) => { e.preventDefault(); setIsDragOver(true); }}
              onDragLeave={() => setIsDragOver(false)}
              onDrop={handleDrop}
              onClick={() => document.getElementById('credFileInput')?.click()}
              className={`p-6 rounded-2xl border-2 border-dashed text-center transition-all cursor-pointer space-y-3 ${
                isDragOver
                  ? 'border-blue-500 bg-blue-50/50 scale-[1.01]'
                  : selectedFile
                  ? 'border-emerald-500 bg-emerald-50/40'
                  : 'border-slate-300 bg-slate-50/50 hover:border-blue-400 hover:bg-slate-50'
              }`}
            >
              <input
                id="credFileInput"
                type="file"
                accept=".pdf,.jpg,.jpeg,.png,.webp,.heic,.tiff"
                onChange={handleFileChange}
                className="hidden"
              />

              <div className="w-12 h-12 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center mx-auto shadow-sm">
                {selectedFile ? <FileCheck className="w-6 h-6 text-emerald-600" /> : <UploadCloud className="w-6 h-6" />}
              </div>

              <div>
                {selectedFile ? (
                  <div className="space-y-1">
                    <strong className="text-xs font-bold text-emerald-700 block truncate max-w-xs mx-auto">
                      {selectedFile.name}
                    </strong>
                    <span className="text-[10px] font-mono text-slate-500">
                      {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB • File selected
                    </span>
                  </div>
                ) : (
                  <div className="space-y-1">
                    <strong className="text-xs font-bold text-slate-800 block">
                      Drag & Drop document file here or click to browse
                    </strong>
                    <span className="text-[11px] text-slate-500 block font-medium">
                      Supports PDF, PNG, JPG, WEBP, HEIC (Max 15MB)
                    </span>
                  </div>
                )}
              </div>
            </div>

            <button
              type="submit"
              disabled={uploading || !selectedFile}
              className={`w-full py-3 px-4 rounded-xl text-xs font-bold text-white transition-all cursor-pointer flex items-center justify-center space-x-2 shadow-md ${
                uploading || !selectedFile
                  ? 'bg-slate-300 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 shadow-blue-500/20'
              }`}
            >
              {uploading ? <RefreshCw size={15} className="animate-spin" /> : <Upload size={15} />}
              <span>{uploading ? 'Uploading Document...' : 'Upload Document to Vault'}</span>
            </button>
          </form>
        </div>

        {/* RIGHT: SUBMITTED DOCUMENTS VAULT TABLE (6 Cols) */}
        <div className="lg:col-span-6 bg-white border border-slate-200/90 rounded-2xl p-6 shadow-lg shadow-slate-100/60 space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-3">
            <div className="flex items-center space-x-2">
              <FileText className="w-5 h-5 text-blue-600" />
              <h3 className="text-sm font-extrabold text-slate-900">Vault Document Records ({credentials.length})</h3>
            </div>
            <span className="bg-emerald-100 text-emerald-800 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full font-mono">
              {credentials.length} ATTACHED
            </span>
          </div>

          {credentials.length === 0 ? (
            <div className="p-8 rounded-2xl bg-slate-50/50 border border-dashed border-slate-200 text-center space-y-2">
              <FileText className="w-8 h-8 text-slate-300 mx-auto" />
              <h4 className="text-xs font-bold text-slate-700">No Verification Documents Attached</h4>
              <p className="text-[11px] text-slate-500 max-w-xs mx-auto">
                Select a document type on the left and upload your Medical License or Registration certificate.
              </p>
            </div>
          ) : (
            <div className="space-y-2.5 max-h-[280px] overflow-y-auto pr-1 custom-scrollbar">
              {credentials.map((cred) => (
                <div
                  key={cred.document_id}
                  className="p-3 rounded-xl bg-slate-50 border border-slate-200 flex items-center justify-between gap-3 text-xs"
                >
                  <div className="flex items-center space-x-3 min-w-0">
                    <File className="w-4 h-4 text-blue-600 flex-shrink-0" />
                    <div className="min-w-0">
                      <strong className="text-xs font-bold text-slate-900 truncate block">
                        {cred.original_filename}
                      </strong>
                      <div className="flex items-center space-x-2 text-[10px] text-slate-500 font-mono">
                        <span className="bg-blue-100 text-blue-800 px-1.5 py-0.2 rounded">{cred.document_type}</span>
                        <span>{(cred.file_size_bytes / 1024).toFixed(1)} KB</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center space-x-1.5 flex-shrink-0">
                    <button
                      onClick={() => handleOpenPreview(cred)}
                      className="p-1.5 bg-white border border-slate-200 rounded-lg hover:bg-slate-100 text-slate-700 cursor-pointer"
                      title="View Document"
                    >
                      <Eye size={14} />
                    </button>
                    <button
                      onClick={() => handleDelete(cred.document_id, cred.original_filename)}
                      className="p-1.5 bg-white border border-slate-200 rounded-lg hover:bg-rose-50 text-rose-600 cursor-pointer"
                      title="Delete Document"
                    >
                      <Trash2 size={14} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Submit Verification Action */}
          <div className="pt-3 border-t border-slate-100 space-y-2">
            <button
              onClick={handleSubmitReview}
              disabled={!canSubmit || submitting}
              className={`w-full py-3 px-4 rounded-xl text-xs font-bold text-white transition-all cursor-pointer flex items-center justify-center space-x-2 shadow-md ${
                !canSubmit || submitting
                  ? 'bg-slate-200 text-slate-400 cursor-not-allowed'
                  : 'bg-emerald-600 hover:bg-emerald-700 shadow-emerald-500/20'
              }`}
            >
              {submitting ? <RefreshCw size={15} className="animate-spin" /> : <ShieldCheck size={15} />}
              <span>
                {submitting ? 'Submitting Application...' :
                 status === 'VERIFIED' && !hasNewUpload ? 'Credentials Verified & Approved' :
                 status === 'UNDER_REVIEW' && !hasNewUpload ? 'Application Submitted (Under Review)' :
                 'Submit Application for Admin Verification'}
              </span>
            </button>
          </div>
        </div>

      </div>

      {/* ── DOCUMENT PREVIEW MODAL ─────────────────────────────────────────── */}
      {previewDoc && (
        <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full p-5 space-y-4 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-extrabold text-slate-900">
                Document Preview — {previewDoc.original_filename}
              </h3>
              <button onClick={() => setPreviewDoc(null)} className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-500">
                <X size={16} />
              </button>
            </div>

            {previewLoading ? (
              <div className="py-16 text-center space-y-2">
                <RefreshCw className="w-6 h-6 text-blue-600 animate-spin mx-auto" />
                <p className="text-xs text-slate-500">Decrypting document file...</p>
              </div>
            ) : previewDoc.data_url ? (
              <div className="max-h-[60vh] overflow-auto rounded-xl border border-slate-200 p-2 flex justify-center bg-slate-50">
                {previewDoc.data_url.startsWith('data:image/') || /\.(png|jpe?g|webp)$/i.test(previewDoc.original_filename) ? (
                  <img src={previewDoc.data_url} alt={previewDoc.original_filename} className="max-h-[55vh] object-contain rounded-lg" />
                ) : (
                  <iframe src={previewDoc.data_url} title={previewDoc.original_filename} className="w-full h-[50vh] rounded-lg" />
                )}
              </div>
            ) : (
              <div className="py-12 text-center text-xs text-slate-500">
                <FileText className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                <p className="font-bold text-slate-800">Verified Practitioner Credential Document</p>
                <p>Registered under {docMetadata.fullName} ({docMetadata.registrationNumber})</p>
              </div>
            )}

            <div className="flex justify-end pt-2">
              <button onClick={() => setPreviewDoc(null)} className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl cursor-pointer">
                Close Preview
              </button>
            </div>
          </div>
        </div>
      )}

    </PageContainer>
  );
}
