import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Stethoscope, Clock, AlertTriangle, CheckCircle, CheckCircle2, ShieldAlert,
  PlusCircle, FileText, User, RefreshCw, X, Eye, Send,
  MessageCircle, Edit3, Lock, Shield, Video, VideoOff, Camera, CameraOff, Calendar, Sparkles, Brain,
  Activity, ArrowRight, Save, Check, Paperclip, ChevronRight,
  Pill, Download, Printer, UserCheck, Star, MessageSquare, ExternalLink,
  ArrowLeft, BadgeCheck, Phone, PhoneCall, PhoneOff, ShieldCheck, Zap, Search, AlertCircle,
  FileCheck, Heart, Sparkle, Mic, MicOff,
  Volume2, VolumeX, Minimize2, Maximize2, Radio, Wifi, Sliders, Waves, Headphones
} from 'lucide-react';
import { PageContainer } from '../components/layout';
import {
  createConsultationRequest,
  fetchPatientConsultations,
  fetchDoctorConsultations,
  fetchOpenConsultations,
  claimConsultation,
  fetchPatientRecords,
  sendConsultationMessage,
  fetchConsultationMessages,
  saveDoctorConsultationNote,
  fetchConsultationNote,
  completeConsultation,
  respondToDoctorAssignment,
  getAuthToken,
  getWsBaseUrl
} from '../api/client';
import useAudioCall, { CALL_STATES } from '../utils/useAudioCall';

// ── Risk Score Gauge Component ─────────────────────────────────────
function RiskScoreGauge({ score = 32, maxScore = 100 }) {
  const percentage = Math.min(100, Math.max(0, (score / maxScore) * 100));
  const riskLevel = score <= 40 ? 'Low Risk' : score <= 70 ? 'Moderate Risk' : 'High Risk';
  const riskColor = score <= 40 ? '#22C55E' : score <= 70 ? '#F59E0B' : '#EF4444';

  return (
    <div className="flex flex-col items-center gap-2 p-4 bg-slate-50 border border-slate-200/80 rounded-2xl">
      <div className="flex items-center justify-between w-full">
        <span className="text-xs font-extrabold text-slate-700">AI Metabolic Risk Assessment</span>
        <span className="text-base font-black text-slate-900">{score} <span className="text-xs font-medium text-slate-400">/ {maxScore}</span></span>
      </div>
      <div className="relative w-full mt-1">
        <div className="flex items-center gap-2">
          <div className="flex-1 h-3 rounded-full bg-slate-200 overflow-hidden">
            <div
              className="h-full rounded-full transition-all duration-1000 ease-out"
              style={{ width: `${percentage}%`, backgroundColor: riskColor }}
            />
          </div>
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold whitespace-nowrap" style={{ backgroundColor: `${riskColor}20`, color: riskColor }}>
            {riskLevel}
          </span>
        </div>
      </div>
    </div>
  );
}

// ── Consultation Timer Component ───────────────────────────────────
function ConsultationTimer({ isActive = false, startTimeStr = null }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (!isActive) {
      setElapsed(0);
      return;
    }
    const startMs = startTimeStr ? new Date(startTimeStr).getTime() : Date.now();
    const calculateElapsed = () => {
      const diffSecs = Math.max(0, Math.floor((Date.now() - (isNaN(startMs) ? Date.now() : startMs)) / 1000));
      setElapsed(diffSecs);
    };

    calculateElapsed();
    const interval = setInterval(calculateElapsed, 1000);
    return () => clearInterval(interval);
  }, [isActive, startTimeStr]);

  const hrs = String(Math.floor(elapsed / 3600)).padStart(2, '0');
  const mins = String(Math.floor((elapsed % 3600) / 60)).padStart(2, '0');
  const secs = String(elapsed % 60).padStart(2, '0');

  return (
    <div className="flex items-center space-x-2 bg-slate-100/90 border border-slate-200/80 px-3 py-1.5 rounded-xl text-xs font-mono font-bold text-slate-800">
      <Clock className="w-4 h-4 text-blue-600 animate-pulse" />
      <span>{hrs}:{mins}:{secs}</span>
    </div>
  );
}

// ── VOIP Audio Visualizer Waveform Component ──────────────────────
function AudioVisualizerWaveform({ isConnected, isMuted }) {
  const bars = [
    { delay: '0.0s', height: '18px' },
    { delay: '0.2s', height: '32px' },
    { delay: '0.4s', height: '48px' },
    { delay: '0.1s', height: '24px' },
    { delay: '0.35s', height: '42px' },
    { delay: '0.15s', height: '54px' },
    { delay: '0.5s', height: '36px' },
    { delay: '0.25s', height: '58px' },
    { delay: '0.45s', height: '44px' },
    { delay: '0.1s', height: '52px' },
    { delay: '0.3s', height: '34px' },
    { delay: '0.55s', height: '48px' },
    { delay: '0.2s', height: '28px' },
    { delay: '0.4s', height: '40px' },
    { delay: '0.15s', height: '22px' },
    { delay: '0.05s', height: '14px' }
  ];

  if (!isConnected) {
    return (
      <div className="flex items-center justify-center space-x-2 h-14 my-3 px-4 rounded-2xl bg-indigo-950/40 border border-indigo-500/20">
        <span className="w-2 h-2 rounded-full bg-indigo-400 animate-ping" />
        <span className="text-xs font-mono font-bold text-indigo-300 tracking-wide">Syncing Opus Audio Stream (48 kHz)...</span>
      </div>
    );
  }

  if (isMuted) {
    return (
      <div className="flex items-center justify-center space-x-2 h-14 my-3 px-4 rounded-2xl bg-amber-950/40 border border-amber-500/30">
        <MicOff className="w-4 h-4 text-amber-400" />
        <span className="text-xs font-mono font-bold text-amber-300">Microphone Muted • Audio Paused</span>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center space-x-1.5 h-16 my-3 px-4 py-2 rounded-2xl bg-slate-950/50 border border-indigo-500/20 shadow-inner">
      {bars.map((b, i) => (
        <span
          key={i}
          className="w-1.5 rounded-full bg-gradient-to-t from-blue-600 via-indigo-400 to-emerald-400 shadow-xs shadow-indigo-500/50 transition-all"
          style={{
            animation: 'soundWaveBar 1.1s ease-in-out infinite alternate',
            animationDelay: b.delay,
            height: b.height,
            minHeight: '6px'
          }}
        />
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// MAIN CONSULTATIONS WORKSPACE COMPONENT
// ═══════════════════════════════════════════════════════════════════════
export default function ConsultationWorkspacePage({ user, consultationContext, initialContext, predictionData, onNavigate }) {
  const navigate = useNavigate();
  const effectiveContext = consultationContext || initialContext;
  const role = user?.role?.toUpperCase() || 'PATIENT';
  const isPatient = role === 'PATIENT';
  const isDoctor = role === 'DOCTOR' || role === 'ADMIN';

  // Patient Navigation State: 'OVERVIEW' (Default dashboard) vs 'CHAT_WORKSPACE' (Attending a live consultation)
  const [patientViewMode, setPatientViewMode] = useState('OVERVIEW');
  const [summaryModalConsultation, setSummaryModalConsultation] = useState(null);

  // Data States
  const [consultations, setConsultations] = useState([]);
  const [healthRecords, setHealthRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [toastMsg, setToastMsg] = useState(null);

  // Search & Filter State
  const [queueFilter, setQueueFilter] = useState('ALL'); // 'ALL', 'ACTIVE', 'PENDING', 'COMPLETED'
  const [searchQuery, setSearchQuery] = useState('');
  const [workspaceTab, setWorkspaceTab] = useState('chat'); // 'chat', 'soap', 'records'

  // Live Audio Call UI Enhancements
  const [isCallMinimized, setIsCallMinimized] = useState(false);
  const [isSpeakerOn, setIsSpeakerOn] = useState(true);
  const [isNoiseFilterActive, setIsNoiseFilterActive] = useState(true);
  const [showInCallNotes, setShowInCallNotes] = useState(false);
  const [inCallNoteText, setInCallNoteText] = useState('');

  // Request New Consultation Modal State
  const [isNewModalOpen, setIsNewModalOpen] = useState(false);
  const [newRequestForm, setNewRequestForm] = useState({
    specialization: 'General Medicine',
    category: 'General Consultation',
    reason: '',
    urgency: 'ROUTINE',
    message: '',
    record_ids: []
  });
  const [submittingRequest, setSubmittingRequest] = useState(false);

  // Active Selected Consultation State
  const [selectedConsultation, setSelectedConsultation] = useState(null);
  const [patientNewMessage, setPatientNewMessage] = useState('');
  const [messageSending, setMessageSending] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('connecting');
  const [isOtherTyping, setIsOtherTyping] = useState(false);

  // SOAP Clinical Notes State (Doctor Portal)
  const [savingNotes, setSavingNotes] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [clinicalNotes, setClinicalNotes] = useState({
    chiefComplaints: '',
    examination: '',
    historyOfPresentIllness: '',
    assessmentDiagnosis: '',
    prescription: '',
    treatmentPlan: ''
  });

  const socketRef = useRef(null);
  const chatEndRef = useRef(null);

  // Trigger Toast Notification
  const notify = (msg) => {
    setToastMsg(msg);
    setTimeout(() => setToastMsg(null), 4000);
  };

  // Load Real Application State from Backend APIs
  const loadWorkspaceData = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true);
    else setLoading(true);
    setErrorMsg(null);

    try {
      const [consRes, recRes] = await Promise.all([
        isDoctor ? Promise.all([
          fetchDoctorConsultations('').catch(() => ({ consultations: [] })),
          fetchOpenConsultations().catch(() => ({ consultations: [] }))
        ]).then(([assigned, open]) => {
          const a = assigned?.consultations || [];
          const o = open?.consultations || [];
          const allMap = new Map();
          a.forEach(c => allMap.set(c.consultation_id, c));
          o.forEach(c => {
             if (!allMap.has(c.consultation_id)) {
               allMap.set(c.consultation_id, c);
             }
          });
          return { consultations: Array.from(allMap.values()) };
        }).catch(() => ({ consultations: [] })) : fetchPatientConsultations().catch(() => ({ consultations: [] })),
        (!isDoctor) ? fetchPatientRecords().catch(() => ({ records: [] })) : Promise.resolve({ records: [] })
      ]);

      const consList = consRes?.consultations || (Array.isArray(consRes) ? consRes : []);
      const recList = recRes?.records || (Array.isArray(recRes) ? recRes : []);

      setConsultations(consList);
      setHealthRecords(recList);

      // Select active consultation from props/session or first item
      let targetId = effectiveContext?.consultationId || effectiveContext?.consultation_id;
      if (!targetId) {
        try {
          const saved = sessionStorage.getItem('telemed_consultation_context');
          if (saved) {
            const parsed = JSON.parse(saved);
            targetId = parsed.consultationId || parsed.consultation_id;
          }
        } catch (e) {}
      }

      if (targetId) {
        const found = consList.find(c => (c.consultation_id === targetId || c.id === targetId));
        if (found) {
          setSelectedConsultation(found);
          if (isPatient) setPatientViewMode('CHAT_WORKSPACE');
        } else if (consList.length > 0) {
          setSelectedConsultation(consList[0]);
        }
      } else if (consList.length > 0 && !selectedConsultation) {
        setSelectedConsultation(consList[0]);
      }
    } catch (err) {
      setErrorMsg(err.message || 'Failed to sync clinical workspace.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [isDoctor, effectiveContext, isPatient, selectedConsultation]);

  useEffect(() => {
    loadWorkspaceData();
  }, [loadWorkspaceData]);

  // Load SOAP Clinical Notes when selected consultation changes
  useEffect(() => {
    const cId = selectedConsultation?.consultation_id || selectedConsultation?.id;
    const consStatus = (selectedConsultation?.status || '').toUpperCase();
    if (!cId || consStatus === 'REQUESTED' || consStatus === 'PENDING') {
      setClinicalNotes({
        chiefComplaints: selectedConsultation?.reason || '',
        examination: '',
        historyOfPresentIllness: selectedConsultation?.message || '',
        assessmentDiagnosis: '',
        prescription: '',
        treatmentPlan: ''
      });
      return;
    }

    fetchConsultationNote(cId)
      .then(note => {
        if (note) {
          setClinicalNotes({
            chiefComplaints: note.symptoms || note.chiefComplaints || selectedConsultation?.reason || '',
            examination: note.observations || note.examination || '',
            historyOfPresentIllness: note.history || selectedConsultation?.message || '',
            assessmentDiagnosis: note.assessment || note.assessmentDiagnosis || '',
            prescription: note.prescription || '',
            treatmentPlan: note.follow_up_guidance || note.patient_summary || note.treatmentPlan || ''
          });
        }
      })
      .catch(() => {
        setClinicalNotes({
          chiefComplaints: selectedConsultation?.reason || '',
          examination: '',
          historyOfPresentIllness: selectedConsultation?.message || '',
          assessmentDiagnosis: '',
          prescription: '',
          treatmentPlan: ''
        });
      });
  }, [selectedConsultation]);

  // Messages Thread State & Sync
  const [messagesThread, setMessagesThread] = useState([]);
  const [loadingMessages, setLoadingMessages] = useState(false);

  const loadMessages = useCallback(async (cId, silent = false) => {
    if (!silent) setLoadingMessages(true);
    try {
      const msgs = await fetchConsultationMessages(cId);
      if (msgs && Array.isArray(msgs)) {
        setMessagesThread(msgs.map(m => ({
          id: m.message_id || m.id,
          sender: m.sender_name || (m.sender_role === 'PATIENT' ? (selectedConsultation?.patient_name || 'Patient') : (selectedConsultation?.doctor_name || 'Doctor')),
          role: m.sender_role || (m.sender_user_id === user?.user_id ? role : 'OTHER'),
          time: m.created_at ? new Date(m.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Just now',
          text: m.content || m.message || '',
        })));
      }
    } catch (err) {
      // Handled silently
    } finally {
      if (!silent) setLoadingMessages(false);
    }
  }, [selectedConsultation, user, role]);

  // Real-Time WebSocket & Polling Chat Sync
  useEffect(() => {
    const activeCons = selectedConsultation || (consultations && consultations.length > 0 ? consultations[0] : null);
    const cId = activeCons?.consultation_id || activeCons?.id;
    const consStatus = (activeCons?.status || '').toUpperCase();
    if (!cId) return;

    // Awaiting doctor assignment: skip message polling and WS connection to avoid 403 loops
    if (consStatus === 'REQUESTED' || consStatus === 'PENDING') {
      setMessagesThread([]);
      setConnectionStatus('waiting_doctor');
      return;
    }

    loadMessages(cId);
    setConnectionStatus('connecting');

    let ws = null;
    let pingInterval = null;

    try {
      const wsBase = getWsBaseUrl();
      const token = getAuthToken() || user?.user_id || '';
      const wsUrl = `${wsBase}/ws/chat/${cId}?token=${encodeURIComponent(token)}`;
      ws = new WebSocket(wsUrl);
      socketRef.current = ws;

      ws.onopen = () => {
        setConnectionStatus('connected');
        pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) ws.send('ping');
        }, 15000);
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const evt = data.event || data.type;
          if (evt === 'typing_start' && data.sender_id !== user?.user_id) {
            setIsOtherTyping(true);
          } else if (evt === 'typing_stop' && data.sender_id !== user?.user_id) {
            setIsOtherTyping(false);
          } else if (evt === 'chat_message' || evt === 'NEW_MESSAGE') {
            setIsOtherTyping(false);
            loadMessages(cId, true);
          }
        } catch (e) {}
      };

      ws.onerror = () => setConnectionStatus('disconnected');
      ws.onclose = () => setConnectionStatus('disconnected');
    } catch (e) {
      setConnectionStatus('disconnected');
    }

    const pollInterval = setInterval(() => loadMessages(cId, true), 3000);

    return () => {
      if (ws) {
        if (ws.readyState === WebSocket.CONNECTING) {
          ws.onopen = () => ws.close();
        } else if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      }
      if (pingInterval) clearInterval(pingInterval);
      clearInterval(pollInterval);
      socketRef.current = null;
    };
  }, [selectedConsultation, consultations, loadMessages, user]);

  // Auto-scroll chat feed
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messagesThread, isOtherTyping]);

  // Handle Messaging Actions
  const handleInputChange = (e) => {
    setPatientNewMessage(e.target.value);
  };

  const handleSendMessage = async (e) => {
    if (e) e.preventDefault();
    const text = patientNewMessage.trim();
    const activeCons = selectedConsultation || (consultations && consultations.length > 0 ? consultations[0] : null);
    if (!text || messageSending || !activeCons) return;

    const cId = activeCons.consultation_id || activeCons.id;
    setPatientNewMessage('');
    setMessageSending(true);

    try {
      await sendConsultationMessage(cId, text);
      await loadMessages(cId, true);
    } catch (err) {
      setErrorMsg(err.message || 'Failed to send message.');
    } finally {
      setMessageSending(false);
    }
  };

  // Create New Consultation Request Handler
  const handleCreateRequest = async (e) => {
    e.preventDefault();
    if (!newRequestForm.reason.trim()) {
      setErrorMsg("Please provide a reason for your consultation request.");
      return;
    }
    setSubmittingRequest(true);
    setErrorMsg(null);
    try {
      const res = await createConsultationRequest(newRequestForm);
      notify("Consultation request created successfully!");
      setIsNewModalOpen(false);
      setNewRequestForm({
        specialization: 'General Medicine',
        category: 'General Consultation',
        reason: '',
        urgency: 'ROUTINE',
        message: '',
        record_ids: []
      });
      await loadWorkspaceData(true);
      if (res.consultation) {
        setSelectedConsultation(res.consultation);
      }
    } catch (err) {
      setErrorMsg(err.message || "Failed to submit consultation request.");
    } finally {
      setSubmittingRequest(false);
    }
  };

  // Handle Save SOAP Notes
  const handleSaveClinicalNotes = async () => {
    if (!selectedConsultation) return;
    const cId = selectedConsultation.consultation_id || selectedConsultation.id;
    setSavingNotes(true);
    setErrorMsg(null);

    try {
      await saveDoctorConsultationNote(cId, {
        symptoms: clinicalNotes.chiefComplaints,
        observations: clinicalNotes.examination,
        history: clinicalNotes.historyOfPresentIllness,
        assessment: clinicalNotes.assessmentDiagnosis,
        prescription: clinicalNotes.prescription,
        patient_summary: clinicalNotes.treatmentPlan,
        follow_up_guidance: clinicalNotes.treatmentPlan
      });
      notify("SOAP Clinical Notes saved to medical record!");
    } catch (err) {
      setErrorMsg(err.message || "Failed to save clinical notes.");
    } finally {
      setSavingNotes(false);
    }
  };

  // Handle Complete Consultation
  const handleCompleteConsultation = async () => {
    if (!selectedConsultation) return;
    const cId = selectedConsultation.consultation_id || selectedConsultation.id;
    setCompleting(true);

    try {
      await completeConsultation(cId, clinicalNotes.assessmentDiagnosis || "Consultation completed.");
      notify("Consultation signed off & completed.");
      await loadWorkspaceData(true);
    } catch (err) {
      setErrorMsg(err.message || "Failed to complete consultation.");
    } finally {
      setCompleting(false);
    }
  };

  // Handle Accept Doctor Assignment
  const handleAcceptAssignment = async () => {
    if (!selectedConsultation) return;
    const cId = selectedConsultation.consultation_id || selectedConsultation.id;
    try {
      await respondToDoctorAssignment(cId, 'ACCEPT');
      notify("Consultation case accepted.");
      await loadWorkspaceData(true);
    } catch (err) {
      setErrorMsg(err.message || "Failed to accept assignment.");
    }
  };

  // Filtered Consultations Queue
  const filteredConsultations = useMemo(() => {
    let list = [...consultations];

    if (queueFilter === 'OPEN_QUEUE') {
      list = list.filter(c => ['REQUESTED', 'PENDING'].includes((c.status || '').toUpperCase()) && !c.assigned_doctor_id);
    } else if (queueFilter === 'ACTIVE') {
      list = list.filter(c => ['ACTIVE', 'ASSIGNED', 'ACCEPTED', 'IN_CONSULTATION', 'IN_PROGRESS'].includes((c.status || '').toUpperCase()));
    } else if (queueFilter === 'PENDING') {
      list = list.filter(c => ['ASSIGNED', 'PENDING', 'REQUESTED'].includes((c.status || '').toUpperCase()));
    } else if (queueFilter === 'COMPLETED') {
      list = list.filter(c => ['COMPLETED', 'CLOSED', 'CANCELLED'].includes((c.status || '').toUpperCase()));
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      list = list.filter(c =>
        (c.patient_name || '').toLowerCase().includes(q) ||
        (c.doctor_name || '').toLowerCase().includes(q) ||
        (c.consultation_id || '').toLowerCase().includes(q) ||
        (c.category || c.specialization || '').toLowerCase().includes(q) ||
        (c.reason || '').toLowerCase().includes(q)
      );
    }

    return list;
  }, [consultations, queueFilter, searchQuery]);

  const handleClaimConsultation = async (cId) => {
    try {
      setLoading(true);
      await claimConsultation(cId);
      await loadWorkspaceData();
      setQueueFilter('ACTIVE');
    } catch (err) {
      setErrorMsg(err.message || 'Failed to claim consultation.');
    } finally {
      setLoading(false);
    }
  };

  const activeConsultation = selectedConsultation || consultations[0];
  const patientDisplayName = activeConsultation?.patient_name || user?.full_name || user?.name || 'Patient';
  const patientDisplayId = activeConsultation?.patient_id || activeConsultation?.user_id || 'PID-10001';
  const doctorDisplayName = activeConsultation?.doctor_name || activeConsultation?.assigned_doctor_name || 'Assigned Physician';

  // ── Audio Call Hook ────────────────────────────────────────────────────
  const activeConsId = activeConsultation?.consultation_id || activeConsultation?.id || null;
  const audioCall = useAudioCall(activeConsId, user);

  // Check if consultation is eligible for audio call (has an active consultation selected)
  const isCallEligible = Boolean(activeConsultation) && !['COMPLETED', 'CANCELLED', 'ARCHIVED'].includes((activeConsultation.status || '').toUpperCase());

  // Format call duration
  const formatDuration = (secs) => {
    const m = String(Math.floor(secs / 60)).padStart(2, '0');
    const s = String(secs % 60).padStart(2, '0');
    return `${m}:${s}`;
  };

  // Register audio call cleanup on window for logout handler in App.jsx
  useEffect(() => {
    window.__telemedAudioCallCleanup = audioCall.fullCleanup;
    return () => {
      window.__telemedAudioCallCleanup = null;
    };
  }, [audioCall.fullCleanup]);

  // ═══════════════════════════════════════════════════════════════════════
  // RENDER: PATIENT PORTAL DASHBOARD (OVERVIEW MODE)
  // ═══════════════════════════════════════════════════════════════════════
  if (isPatient && patientViewMode === 'OVERVIEW') {
    return (
      <PageContainer className="max-w-[1440px] mx-auto px-4 sm:px-6 py-6 space-y-8">
        
        {/* Toast Alert */}
        {toastMsg && (
          <div className="fixed bottom-5 right-5 z-50 bg-slate-900 text-white text-xs font-bold px-4 py-3 rounded-2xl shadow-2xl border border-slate-700 flex items-center gap-2 animate-slide-up">
            <CheckCircle2 size={16} className="text-emerald-400" />
            <span>{toastMsg}</span>
          </div>
        )}

        {/* ── HERO BANNER & STATS ────────────────────────────────────────── */}
        <div className="relative overflow-hidden p-6 sm:p-8 bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 text-white rounded-3xl shadow-2xl border border-slate-800/80">
          <div className="absolute -top-24 -right-24 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
          <div className="absolute -bottom-24 -left-24 w-96 h-96 bg-indigo-500/10 rounded-full blur-3xl pointer-events-none" />
          
          <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
            <div className="space-y-2 max-w-2xl">
              <div className="flex items-center space-x-2.5">
                <span className="px-3 py-1 bg-gradient-to-r from-blue-500/20 to-indigo-500/20 border border-blue-400/30 text-blue-300 text-xs font-extrabold rounded-full flex items-center gap-1.5 shadow-xs">
                  <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  TeleMed Physician Network Active
                </span>
                <span className="text-xs text-slate-400 font-mono">Level 8 Telehealth Protocol</span>
              </div>

              <h1 className="text-2xl sm:text-3xl font-black text-white tracking-tight">
                My Doctor Consultations
              </h1>
              <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
                Connect directly with board-certified medical specialists, attend live chat teleconsultations, review clinical prescriptions, and manage your health records.
              </p>
            </div>

            <div className="flex flex-wrap items-center gap-3 shrink-0">
              <button
                onClick={() => setIsNewModalOpen(true)}
                className="px-5 py-3 bg-gradient-to-r from-blue-600 via-indigo-600 to-blue-500 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-extrabold rounded-2xl shadow-lg shadow-blue-600/30 flex items-center space-x-2 transition-all transform hover:-translate-y-0.5 cursor-pointer"
              >
                <PlusCircle className="w-4 h-4" />
                <span>Request New Consultation</span>
              </button>

              <button
                onClick={() => navigate('/appointments')}
                className="px-5 py-3 bg-slate-800/90 hover:bg-slate-800 text-slate-200 border border-slate-700/80 text-xs font-extrabold rounded-2xl transition-all cursor-pointer flex items-center space-x-2"
              >
                <Calendar className="w-4 h-4 text-blue-400" />
                <span>Book Appointment</span>
              </button>

              <button
                onClick={() => loadWorkspaceData(true)}
                className="p-3 bg-slate-800/80 hover:bg-slate-700 text-slate-300 border border-slate-700 rounded-2xl transition-all cursor-pointer"
                title="Refresh Workspace"
              >
                <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
              </button>
            </div>
          </div>
        </div>

        {/* ── CONSULTATION MODALITY OPTIONS ─────────────────────────────── */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-extrabold text-[var(--text-main)] uppercase tracking-wider flex items-center gap-2">
              <Zap className="w-4 h-4 text-[var(--primary)]" />
              <span>Teleconsultation Options</span>
            </h2>
            <span className="text-xs font-semibold text-[var(--text-muted)]">Supported Modalities</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Live Chat Option */}
            <div className="p-5 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-2xl text-[var(--text-main)] shadow-md relative overflow-hidden group hover:border-[var(--primary)] transition-all">
              <div className="flex items-center justify-between mb-3">
                <div className="w-10 h-10 rounded-xl bg-blue-500/20 border border-blue-400/30 flex items-center justify-center text-blue-400">
                  <MessageSquare className="w-5 h-5" />
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center gap-1">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  AVAILABLE NOW
                </span>
              </div>
              <h3 className="text-sm font-extrabold mb-1 text-[var(--text-main)]">Live Chat Consultation</h3>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed mb-4">
                Instant 2-way secure clinical text chat, real-time file sharing, and physician guidance.
              </p>
              <div className="flex items-center text-[11px] font-bold text-[var(--primary)] group-hover:underline transition-colors">
                <span>Active for Assigned Consultations</span>
                <ChevronRight className="w-3.5 h-3.5 ml-1" />
              </div>
            </div>

            {/* Audio Call Option */}
            <div
              className={`p-5 bg-[var(--bg-surface)] border rounded-2xl text-[var(--text-main)] shadow-md relative overflow-hidden group transition-all ${
                isCallEligible ? 'border-indigo-400/50 hover:border-indigo-500 cursor-pointer hover:shadow-lg' : 'border-[var(--border-subtle)]'
              }`}
              onClick={() => { if (isCallEligible && audioCall.callState === 'IDLE') audioCall.startCall(); }}
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  isCallEligible ? 'bg-indigo-500/20 border border-indigo-400/40 text-indigo-400' : 'bg-indigo-500/10 border border-indigo-500/20 text-indigo-400/50'
                }`}>
                  <PhoneCall className="w-5 h-5" />
                </div>
                {isCallEligible ? (
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    AVAILABLE NOW
                  </span>
                ) : (
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-indigo-500/20 border border-indigo-500/30 text-indigo-400">
                    REQUIRES ACTIVE CONSULTATION
                  </span>
                )}
              </div>
              <h3 className="text-sm font-extrabold mb-1 text-[var(--text-main)]">Voice Telehealth Call</h3>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed mb-4">
                {isCallEligible ? 'Click to start a secure WebRTC audio call with your attending specialist.' : 'Direct encrypted VoIP audio call consultation with your attending specialist.'}
              </p>
              <div className={`flex items-center text-[11px] font-bold ${
                isCallEligible ? 'text-indigo-400 group-hover:underline' : 'text-[var(--text-dim)]'
              }`}>
                <span>{isCallEligible ? 'Start Audio Call' : 'Needs an assigned doctor to enable'}</span>
                {isCallEligible && <ChevronRight className="w-3.5 h-3.5 ml-1" />}
              </div>
            </div>

            {/* HD Video Teleconsultation Option */}
            <div
              className={`p-5 bg-[var(--bg-surface)] border rounded-2xl text-[var(--text-main)] shadow-md relative overflow-hidden group transition-all ${
                isCallEligible ? 'border-purple-400/50 hover:border-purple-500 cursor-pointer hover:shadow-lg' : 'border-[var(--border-subtle)]'
              }`}
              onClick={() => { if (isCallEligible && audioCall.callState === 'IDLE') audioCall.startCall('video'); }}
            >
              <div className="flex items-center justify-between mb-3">
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                  isCallEligible ? 'bg-purple-500/20 border border-purple-400/40 text-purple-400' : 'bg-purple-500/10 border border-purple-500/20 text-purple-400/50'
                }`}>
                  <Video className="w-5 h-5" />
                </div>
                {isCallEligible ? (
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-emerald-500/20 border border-emerald-500/40 text-emerald-400 flex items-center gap-1">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    AVAILABLE NOW
                  </span>
                ) : (
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-purple-500/20 border border-purple-500/30 text-purple-400">
                    REQUIRES ACTIVE CONSULTATION
                  </span>
                )}
              </div>
              <h3 className="text-sm font-extrabold mb-1 text-[var(--text-main)]">HD Video Teleconsultation</h3>
              <p className="text-xs text-[var(--text-muted)] leading-relaxed mb-4">
                {isCallEligible ? 'High-definition 1-to-1 encrypted video call & virtual physician examination.' : 'High-definition interactive video call & virtual physician examination room.'}
              </p>
              <div className={`flex items-center text-[11px] font-bold ${
                isCallEligible ? 'text-purple-400 group-hover:underline' : 'text-[var(--text-dim)]'
              }`}>
                <span>{isCallEligible ? 'Start Video Consultation' : 'Needs an assigned doctor to enable'}</span>
                {isCallEligible && <ChevronRight className="w-3.5 h-3.5 ml-1" />}
              </div>
            </div>
          </div>
        </div>

        {/* ── CONSULTATIONS CARDS GRID & SEARCH BAR ────────────────────────── */}
        <div className="space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-[var(--bg-surface)] p-4 rounded-2xl border border-[var(--border-subtle)] shadow-xs">
            {/* Filter Pills */}
            <div className="flex items-center space-x-1.5 overflow-x-auto custom-scrollbar pb-1 sm:pb-0">
              {[
                { id: 'ALL', label: `All Consultations (${consultations.length})` },
                ...(isDoctor ? [{ id: 'OPEN_QUEUE', label: 'Open Requests' }] : []),
                { id: 'ACTIVE', label: 'Active & Assigned' },
                { id: 'PENDING', label: 'Pending Assignment' },
                { id: 'COMPLETED', label: 'Completed' },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setQueueFilter(tab.id)}
                  className={`px-3.5 py-1.5 rounded-xl text-xs font-extrabold transition-all whitespace-nowrap cursor-pointer ${
                    queueFilter === tab.id
                      ? 'bg-[var(--primary)] text-white shadow-sm'
                      : 'bg-[var(--bg-primary)] text-[var(--text-muted)] hover:text-[var(--text-main)]'
                  }`}
                >
                  {tab.label}
                </button>
              ))}
            </div>

            {/* Search Input */}
            <div className="relative min-w-[240px]">
              <Search className="w-4 h-4 text-[var(--text-dim)] absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search doctor name or specialty..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-3 py-1.5 bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-xl text-xs text-[var(--text-main)] focus:outline-none focus:border-[var(--primary)] placeholder:text-[var(--text-dim)]"
              />
            </div>
          </div>

          {/* Cards List */}
          {loading ? (
            <div className="py-20 text-center space-y-3 bg-white rounded-3xl border border-slate-200/80">
              <RefreshCw className="w-8 h-8 text-blue-600 animate-spin mx-auto" />
              <p className="text-xs font-bold text-slate-600">Syncing patient consultation workspace...</p>
            </div>
          ) : filteredConsultations.length === 0 ? (
            <div className="py-16 text-center space-y-4 px-6 border-2 border-dashed border-slate-200/80 rounded-3xl bg-slate-50/50">
              <div className="w-14 h-14 rounded-2xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 mx-auto shadow-sm">
                <Stethoscope className="w-7 h-7" />
              </div>
              <div>
                <h3 className="text-base font-extrabold text-slate-900">No Consultation Records Found</h3>
                <p className="text-xs text-slate-500 max-w-md mx-auto mt-1 leading-relaxed">
                  You currently have no doctor consultations matching this filter. You can request a new consultation with a specialist anytime.
                </p>
              </div>
              <button
                onClick={() => setIsNewModalOpen(true)}
                className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-xs font-bold rounded-xl shadow-md hover:from-blue-700 hover:to-indigo-700 transition-all cursor-pointer inline-flex items-center space-x-2"
              >
                <PlusCircle size={16} />
                <span>Request New Consultation</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredConsultations.map((c, idx) => {
                const statusUpper = (c.status || 'ACTIVE').toUpperCase();
                const isCompleted = statusUpper === 'COMPLETED';
                const isPending = ['PENDING', 'REQUESTED'].includes(statusUpper);
                const isActive = ['ACTIVE', 'ASSIGNED', 'ACCEPTED', 'IN_CONSULTATION', 'IN_PROGRESS'].includes(statusUpper);
                const docName = c.doctor_name || c.assigned_doctor_name || (isPending ? 'Searching for Specialist' : 'Attending Physician');

                return (
                  <div
                    key={c.consultation_id || c.id || idx}
                    className="p-5 bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[var(--primary)] rounded-3xl shadow-sm hover:shadow-md transition-all flex flex-col justify-between space-y-4"
                  >
                    <div className="space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex items-center space-x-3">
                          <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold flex items-center justify-center text-sm shadow-md shrink-0">
                            {docName.split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                          </div>
                          <div>
                            <h3 className="text-sm font-extrabold text-[var(--text-main)]">{docName}</h3>
                            <p className="text-xs text-[var(--text-muted)] font-medium">
                              {c.category || c.specialization || 'General Consultation'}
                            </p>
                          </div>
                        </div>

                        <span className={`text-[10px] font-extrabold px-2.5 py-1 rounded-full uppercase flex items-center gap-1.5 ${
                          isCompleted ? 'bg-[var(--bg-primary)] text-[var(--text-muted)] border border-[var(--border-subtle)]' :
                          isActive ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-amber-500/20 text-amber-400 border border-amber-500/30'
                        }`}>
                          {isActive && <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />}
                          {statusUpper}
                        </span>
                      </div>

                      <div className="p-3 bg-[var(--bg-primary)] border border-[var(--border-subtle)] rounded-2xl space-y-1.5 text-xs">
                        <div className="flex items-center justify-between text-[var(--text-muted)]">
                          <span className="font-semibold">Consultation ID:</span>
                          <span className="font-mono text-[var(--text-main)] font-bold">{c.consultation_id}</span>
                        </div>
                        <div className="flex items-center justify-between text-[var(--text-muted)]">
                          <span className="font-semibold">Primary Reason:</span>
                          <span className="text-[var(--text-main)] font-medium truncate max-w-[180px]">{c.reason || 'General Health Check'}</span>
                        </div>
                        <div className="flex items-center justify-between text-[var(--text-muted)]">
                          <span className="font-semibold">Urgency:</span>
                          <span className={`font-bold ${c.urgency === 'URGENT' ? 'text-rose-500' : 'text-[var(--primary)]'}`}>
                            {c.urgency || 'ROUTINE'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Primary Action Button */}
                    <div className="pt-2 border-t border-[var(--border-subtle)]">
                      {isActive ? (
                        <button
                          onClick={() => {
                            setSelectedConsultation(c);
                            setPatientViewMode('CHAT_WORKSPACE');
                          }}
                          className="w-full py-2.5 px-4 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-extrabold rounded-xl shadow-md shadow-blue-500/20 flex items-center justify-center space-x-2 transition-all cursor-pointer"
                        >
                          <MessageSquare className="w-4 h-4 animate-bounce" />
                          <span>Attend Consultation (Live Chat)</span>
                        </button>
                      ) : isCompleted ? (
                        <button
                          onClick={() => setSummaryModalConsultation(c)}
                          className="w-full py-2.5 px-4 bg-slate-900 hover:bg-slate-800 text-white text-xs font-bold rounded-xl flex items-center justify-center space-x-2 transition-all cursor-pointer"
                        >
                          <FileText className="w-4 h-4 text-emerald-400" />
                          <span>View Summary & Prescription</span>
                        </button>
                      ) : (
                        isDoctor && isPending && !c.assigned_doctor_id ? (
                          <button
                            onClick={() => handleClaimConsultation(c.consultation_id || c.id)}
                            className="w-full py-2.5 px-4 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-bold rounded-xl flex items-center justify-center space-x-2 transition-all cursor-pointer"
                          >
                            <Stethoscope className="w-4 h-4 text-emerald-100" />
                            <span>Attend Request (Claim)</span>
                          </button>
                        ) : (
                          <div className="w-full py-2.5 px-4 bg-amber-50 border border-amber-200 text-amber-800 text-xs font-bold rounded-xl text-center flex items-center justify-center space-x-2">
                            <Clock className="w-4 h-4 text-amber-600" />
                            <span>Awaiting Doctor Assignment</span>
                          </div>
                        )
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* ── REQUEST NEW CONSULTATION MODAL ───────────────────────────────── */}
        {isNewModalOpen && (
          <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-5 animate-scale-up">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center space-x-2">
                  <div className="w-9 h-9 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                    <Stethoscope size={18} />
                  </div>
                  <h3 className="text-base font-extrabold text-slate-900">Request Doctor Consultation</h3>
                </div>
                <button onClick={() => setIsNewModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                  <X size={18} />
                </button>
              </div>

              <form onSubmit={handleCreateRequest} className="space-y-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Target Medical Specialization</label>
                  <select
                    value={newRequestForm.specialization}
                    onChange={(e) => setNewRequestForm({ ...newRequestForm, specialization: e.target.value })}
                    className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 font-medium focus:outline-none focus:border-blue-500"
                  >
                    <option value="General Medicine">General Medicine & Internal Care</option>
                    <option value="Cardiology">Cardiology & Cardiovascular</option>
                    <option value="Endocrinology">Endocrinology & Diabetes</option>
                    <option value="Gastroenterology">Gastroenterology & Gut Health</option>
                    <option value="Hepatology">Hepatology & Liver</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Reason for Consultation</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g. Follow up on HbA1c lab results and dietary plan"
                    value={newRequestForm.reason}
                    onChange={(e) => setNewRequestForm({ ...newRequestForm, reason: e.target.value })}
                    className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Urgency Level</label>
                  <div className="grid grid-cols-2 gap-2">
                    {['ROUTINE', 'SOON'].map((u) => (
                      <button
                        key={u}
                        type="button"
                        onClick={() => setNewRequestForm({ ...newRequestForm, urgency: u })}
                        className={`p-2.5 rounded-xl border text-xs font-extrabold transition-all cursor-pointer ${
                          newRequestForm.urgency === u
                            ? 'bg-blue-600 text-white border-blue-600'
                            : 'bg-slate-50 text-slate-700 border-slate-200'
                        }`}
                      >
                        {u === 'ROUTINE' ? 'Routine Consultation' : 'Urgent Assessment'}
                      </button>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Additional Notes for Attending Doctor</label>
                  <textarea
                    rows={3}
                    placeholder="Provide any specific symptoms or health context..."
                    value={newRequestForm.message}
                    onChange={(e) => setNewRequestForm({ ...newRequestForm, message: e.target.value })}
                    className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:border-blue-500"
                  />
                </div>

                <div className="pt-2 flex items-center justify-end space-x-2">
                  <button
                    type="button"
                    onClick={() => setIsNewModalOpen(false)}
                    className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-bold rounded-xl"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={submittingRequest}
                    className="px-5 py-2 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-bold rounded-xl flex items-center space-x-1.5 shadow-md shadow-blue-500/20"
                  >
                    {submittingRequest ? <RefreshCw size={14} className="animate-spin" /> : <Check size={14} />}
                    <span>Submit Request</span>
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* ── SUMMARY MODAL FOR COMPLETED CONSULTATIONS ───────────────────── */}
        {summaryModalConsultation && (
          <div className="fixed inset-0 z-50 bg-slate-950/70 backdrop-blur-xs flex items-center justify-center p-4">
            <div className="bg-white rounded-3xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center space-x-2">
                  <FileText className="w-5 h-5 text-emerald-600" />
                  <h3 className="text-base font-extrabold text-slate-900">Consultation Summary & Prescription</h3>
                </div>
                <button onClick={() => setSummaryModalConsultation(null)} className="text-slate-400 hover:text-slate-600">
                  <X size={18} />
                </button>
              </div>

              <div className="space-y-3 text-xs">
                <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex justify-between">
                  <div>
                    <span className="text-slate-500 font-bold block">Attending Doctor</span>
                    <span className="text-slate-900 font-extrabold">{summaryModalConsultation.doctor_name || 'Dr. Medical Officer'}</span>
                  </div>
                  <div className="text-right">
                    <span className="text-slate-500 font-bold block">Consultation ID</span>
                    <span className="text-slate-900 font-mono font-bold">{summaryModalConsultation.consultation_id}</span>
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="font-extrabold text-slate-800">Doctor Diagnosis & Clinical Notes:</span>
                  <div className="p-3 bg-blue-50/50 border border-blue-100 rounded-xl text-slate-900 leading-relaxed font-medium">
                    {clinicalNotes.assessmentDiagnosis || summaryModalConsultation.notes || 'Routine health evaluation completed cleanly.'}
                  </div>
                </div>

                <div className="space-y-1">
                  <span className="font-extrabold text-slate-800">Prescription & Medical Guidance:</span>
                  <div className="p-3 bg-emerald-50/50 border border-emerald-100 rounded-xl text-slate-900 font-mono text-[11px]">
                    {clinicalNotes.prescription || 'No specific prescription modification recorded.'}
                  </div>
                </div>
              </div>

              <div className="pt-2 flex justify-end">
                <button
                  onClick={() => setSummaryModalConsultation(null)}
                  className="px-5 py-2 bg-slate-900 text-white font-bold text-xs rounded-xl"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        )}

      </PageContainer>
    );
  }

  // ═══════════════════════════════════════════════════════════════════════
  // RENDER: LIVE CHAT WORKSPACE (PATIENT ATTEND MODE & DOCTOR PORTAL)
  // ═══════════════════════════════════════════════════════════════════════
  return (
    <PageContainer className="max-w-[1480px] mx-auto px-4 py-4 space-y-4">
      
      {/* Toast Alert */}
      {toastMsg && (
        <div className="fixed bottom-5 right-5 z-50 bg-slate-900 text-white text-xs font-bold px-4 py-3 rounded-2xl shadow-2xl border border-slate-700 flex items-center gap-2 animate-slide-up">
          <CheckCircle2 size={16} className="text-emerald-400" />
          <span>{toastMsg}</span>
        </div>
      )}

      {/* ── TOP HEADER BANNER ──────────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 p-5 bg-gradient-to-r from-slate-900 via-slate-800 to-indigo-950 text-white rounded-2xl shadow-xl border border-slate-700/50">
        <div className="flex items-center space-x-3.5">
          {isPatient && (
            <button
              onClick={() => setPatientViewMode('OVERVIEW')}
              className="p-2.5 bg-white/10 hover:bg-white/20 text-white rounded-xl border border-white/15 transition-all cursor-pointer mr-1 flex items-center space-x-1"
              title="Return to Consultations List"
            >
              <ArrowLeft className="w-4 h-4" />
              <span className="text-xs font-bold">Back</span>
            </button>
          )}

          <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-blue-500 to-indigo-600 flex items-center justify-center shadow-lg shadow-blue-500/20 text-white shrink-0">
            <Stethoscope className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-extrabold tracking-tight text-white">
                {isDoctor ? 'Doctor Clinical Workspace' : 'Attending Consultation Live Chat'}
              </h1>
              <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-[10px] font-bold px-2.5 py-0.5 rounded-full flex items-center gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                {isDoctor ? 'Doctor Portal Active' : 'Live Chat Workspace Active'}
              </span>
            </div>
            <p className="text-xs text-slate-300 mt-0.5">
              {isDoctor
                ? 'Review assigned patient intake reports, maintain SOAP clinical notes, and manage teleconsultations.'
                : `Communicating live with ${doctorDisplayName} for Consultation ID ${activeConsultation?.consultation_id || 'Active'}`}
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2.5">
          {/* Audio & Video Call Launch Buttons */}
          {isCallEligible && audioCall.callState === 'IDLE' && (
            <>
              <button
                onClick={() => audioCall.startCall('audio')}
                className="px-3.5 py-2 bg-indigo-500/30 hover:bg-indigo-500/50 text-indigo-200 border border-indigo-400/30 rounded-xl transition-all cursor-pointer flex items-center space-x-2 text-xs font-bold"
                title="Start Voice Telehealth Call"
              >
                <PhoneCall className="w-4 h-4" />
                <span className="hidden sm:inline">Audio Call</span>
              </button>
              <button
                onClick={() => audioCall.startCall('video')}
                className="px-3.5 py-2 bg-purple-500/30 hover:bg-purple-500/50 text-purple-200 border border-purple-400/30 rounded-xl transition-all cursor-pointer flex items-center space-x-2 text-xs font-bold shadow-md shadow-purple-500/20"
                title="Start HD Video Teleconsultation"
              >
                <Video className="w-4 h-4" />
                <span className="hidden sm:inline">Video Call</span>
              </button>
            </>
          )}
          {/* Active Call Duration Badge */}
          {audioCall.callState === 'CONNECTED' && (
            <div className="px-3 py-1.5 bg-emerald-500/20 border border-emerald-400/30 rounded-xl flex items-center space-x-2 text-xs font-mono font-bold text-emerald-300 animate-pulse">
              {audioCall.callType === 'video' ? <Video className="w-3.5 h-3.5" /> : <Phone className="w-3.5 h-3.5" />}
              <span>{formatDuration(audioCall.callDuration)}</span>
            </div>
          )}
          <button
            onClick={() => loadWorkspaceData(true)}
            className="p-2.5 bg-white/10 hover:bg-white/15 text-slate-200 border border-white/15 rounded-xl transition-all cursor-pointer"
            title="Refresh Workspace"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </div>

      {errorMsg && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span className="font-medium">{errorMsg}</span>
          </div>
          <button onClick={() => setErrorMsg(null)} className="font-bold text-rose-700 hover:text-rose-900 underline cursor-pointer text-xs">Dismiss</button>
        </div>
      )}

      {/* ── ULTRA-PREMIUM WEBRTC AUDIO & VIDEO TELECONSULTATION OVERLAY ──── */}
      {audioCall.callState !== 'IDLE' && !isCallMinimized && (
        <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-slate-950/85 backdrop-blur-md p-3 sm:p-6 animate-fade-in" style={{ pointerEvents: 'auto' }}>
          <div className={`w-full ${audioCall.callType === 'video' ? 'max-w-4xl' : 'max-w-lg'} bg-gradient-to-b from-slate-900 via-slate-900/98 to-indigo-950 border border-indigo-500/30 rounded-3xl shadow-[0_25px_80px_rgba(0,0,0,0.85)] overflow-hidden relative text-white transition-all`}>
            
            {/* Hidden audio element for remote audio playback */}
            <audio ref={audioCall.remoteAudioRef} autoPlay playsInline />

            {/* Ambient Background Glows */}
            <div className="absolute -top-20 -left-20 w-64 h-64 bg-blue-600/20 rounded-full blur-3xl pointer-events-none call-aura-glow" />
            <div className="absolute -bottom-20 -right-20 w-64 h-64 bg-indigo-600/25 rounded-full blur-3xl pointer-events-none call-aura-glow" style={{ animationDelay: '2s' }} />

            {/* Top Navigation & Status Bar */}
            <div className="p-4 sm:p-5 pb-2 flex items-center justify-between border-b border-slate-800/80 relative z-20">
              <div className="flex items-center space-x-2">
                <div className="flex items-center space-x-1.5 px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-[11px] font-bold shadow-xs">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
                  <span>{audioCall.callType === 'video' ? '256-Bit Encrypted HD Video' : '256-Bit Encrypted VoIP'}</span>
                </div>
                <div className="hidden sm:flex items-center space-x-1 px-2.5 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-[10px] font-mono">
                  <Wifi className="w-3 h-3 text-emerald-400" />
                  <span>{audioCall.callType === 'video' ? 'WebRTC HD • 720p 30fps' : 'HD Voice • 48 kHz'}</span>
                </div>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  type="button"
                  onClick={() => setIsCallMinimized(true)}
                  className="p-2 text-slate-400 hover:text-white bg-slate-800/80 hover:bg-slate-700/80 border border-slate-700/60 rounded-xl transition-all cursor-pointer shadow-xs"
                  title="Minimize to Floating Widget (PiP)"
                >
                  <Minimize2 className="w-4 h-4" />
                </button>
              </div>
            </div>

            {/* Main Video View vs Audio View */}
            {audioCall.callType === 'video' ? (
              /* ── VIDEO CONSULTATION INTERFACE ── */
              <div className="relative aspect-video w-full max-h-[520px] bg-slate-950 flex items-center justify-center overflow-hidden">
                {/* Remote Participant Primary Video Feed */}
                <video
                  ref={audioCall.remoteVideoRef}
                  autoPlay
                  playsInline
                  className={`w-full h-full object-cover transition-opacity duration-300 ${
                    audioCall.isRemoteVideoAvailable && audioCall.callState === 'CONNECTED' ? 'opacity-100' : 'opacity-0 absolute'
                  }`}
                />

                {/* Remote Video Fallback (When remote camera is off or connecting) */}
                {(!audioCall.isRemoteVideoAvailable || audioCall.callState !== 'CONNECTED') && (
                  <div className="flex flex-col items-center justify-center p-6 text-center space-y-3 z-10">
                    <div className="relative">
                      {(audioCall.callState === 'CONNECTED' || audioCall.callState === 'CALLING' || audioCall.callState === 'RINGING') && (
                        <>
                          <div className="absolute -inset-4 rounded-full border border-purple-500/30 animate-ping" />
                          <div className="absolute -inset-8 rounded-full border border-indigo-500/20 animate-pulse" />
                        </>
                      )}
                      <div className="w-24 h-24 sm:w-28 sm:h-28 rounded-3xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-blue-600 p-1 shadow-2xl flex items-center justify-center">
                        <div className="w-full h-full rounded-[22px] bg-slate-900 flex items-center justify-center">
                          {audioCall.callState === 'RINGING' ? (
                            <Video className="w-12 h-12 text-emerald-400 animate-bounce" />
                          ) : (
                            <span className="text-3xl font-black text-white">
                              {(isDoctor ? patientDisplayName : doctorDisplayName).substring(0, 2).toUpperCase()}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    <div className="space-y-1">
                      <h3 className="text-xl font-bold text-white">
                        {audioCall.callState === 'RINGING' ? (audioCall.incomingCallInfo?.senderName || 'Incoming Video Call') : (isDoctor ? patientDisplayName : doctorDisplayName)}
                      </h3>
                      <p className="text-xs text-purple-300 font-semibold">
                        {audioCall.callState === 'CONNECTED'
                          ? 'Camera feed paused by remote participant (Audio live)'
                          : audioCall.callState === 'CALLING'
                          ? 'Calling for HD Video Teleconsultation...'
                          : audioCall.callState === 'RINGING'
                          ? 'Incoming HD Video Teleconsultation Request'
                          : 'Establishing secure video link...'}
                      </p>
                    </div>
                  </div>
                )}

                {/* Local Camera Picture-in-Picture (PiP) Floating Preview */}
                <div className="absolute bottom-4 right-4 z-20 w-36 sm:w-48 aspect-video rounded-2xl bg-slate-900 border-2 border-indigo-500/50 shadow-2xl overflow-hidden group">
                  <video
                    ref={audioCall.localVideoRef}
                    autoPlay
                    playsInline
                    muted
                    className={`w-full h-full object-cover -scale-x-100 ${audioCall.isVideoEnabled ? 'block' : 'hidden'}`}
                  />
                  {!audioCall.isVideoEnabled && (
                    <div className="w-full h-full flex flex-col items-center justify-center bg-slate-900/90 text-slate-400 p-2 text-center">
                      <CameraOff className="w-5 h-5 mb-1 text-slate-500" />
                      <span className="text-[10px] font-bold">Camera Off</span>
                    </div>
                  )}
                  <div className="absolute bottom-1 left-2 px-1.5 py-0.5 rounded bg-black/60 backdrop-blur-xs text-[9px] font-bold text-white">
                    You {audioCall.isMuted && '• Muted'}
                  </div>
                </div>

                {/* Video Call Live HUD Badge */}
                {audioCall.callState === 'CONNECTED' && (
                  <div className="absolute top-4 left-4 z-20 flex items-center space-x-2 bg-black/60 backdrop-blur-md px-3 py-1.5 rounded-xl border border-white/10 text-xs text-white">
                    <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                    <span className="font-mono font-bold text-emerald-300">{formatDuration(audioCall.callDuration)}</span>
                    <span className="text-[10px] text-slate-300">| {isDoctor ? patientDisplayName : doctorDisplayName}</span>
                  </div>
                )}
              </div>
            ) : (
              /* ── AUDIO CONSULTATION INTERFACE ── */
              <div className="p-6 text-center relative z-10">
                <div className="relative my-4 flex items-center justify-center">
                  {(audioCall.callState === 'CONNECTED' || audioCall.callState === 'CALLING' || audioCall.callState === 'RINGING') && (
                    <>
                      <div className="absolute w-28 h-28 rounded-full border border-indigo-500/40 call-pulse-ring-1" />
                      <div className="absolute w-36 h-36 rounded-full border border-blue-400/25 call-pulse-ring-2" />
                      <div className="absolute w-44 h-44 rounded-full border border-indigo-400/15 call-pulse-ring-3" />
                    </>
                  )}
                  
                  <div className="relative w-24 h-24 rounded-3xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 p-1 shadow-2xl shadow-indigo-500/50 ring-4 ring-indigo-500/30 flex items-center justify-center transition-all transform hover:scale-105">
                    <div className="w-full h-full rounded-[22px] bg-slate-900 flex items-center justify-center overflow-hidden">
                      {audioCall.callState === 'RINGING' ? (
                        <PhoneCall className="w-10 h-10 text-emerald-400 animate-bounce" />
                      ) : audioCall.callState === 'CONNECTED' ? (
                        <div className="flex flex-col items-center justify-center">
                          <span className="text-2xl font-black text-white tracking-wider">
                            {(isDoctor ? patientDisplayName : doctorDisplayName).substring(0, 2).toUpperCase()}
                          </span>
                          <div className="flex items-center gap-1 mt-0.5">
                            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                            <span className="text-[9px] font-mono text-emerald-400 uppercase font-bold">Live</span>
                          </div>
                        </div>
                      ) : audioCall.callState === 'CALLING' ? (
                        <PhoneCall className="w-10 h-10 text-indigo-400 animate-pulse" />
                      ) : audioCall.callState === 'CONNECTING' || audioCall.callState === 'ACCEPTED' ? (
                        <Activity className="w-10 h-10 text-blue-400 animate-spin" />
                      ) : (
                        <PhoneOff className="w-10 h-10 text-rose-400" />
                      )}
                    </div>
                    
                    <div className="absolute -bottom-1 -right-1 w-7 h-7 rounded-full bg-blue-600 border-2 border-slate-900 flex items-center justify-center text-white shadow-md">
                      {isDoctor ? <Heart className="w-3.5 h-3.5 fill-current text-white" /> : <Stethoscope className="w-3.5 h-3.5 text-white" />}
                    </div>
                  </div>
                </div>

                {/* Participant Name & Specialization */}
                <div className="space-y-1 mt-2">
                  <h2 className="text-2xl font-black text-white tracking-tight flex items-center justify-center gap-2">
                    <span>{audioCall.callState === 'RINGING' ? (audioCall.incomingCallInfo?.senderName || 'Incoming Patient Call') : (isDoctor ? patientDisplayName : doctorDisplayName)}</span>
                    <BadgeCheck className="w-5 h-5 text-blue-400 shrink-0" />
                  </h2>
                  <div className="flex items-center justify-center gap-2 text-xs text-indigo-300 font-semibold">
                    <span>{isDoctor ? 'Patient Telehealth Case' : 'Attending Medical Specialist'}</span>
                    <span>•</span>
                    <span className="px-2 py-0.5 rounded-md bg-indigo-500/20 text-indigo-200 text-[10px] font-mono font-bold">
                      {activeConsultation?.specialization || 'Clinical Specialist'}
                    </span>
                  </div>
                </div>

                {/* Status & Live Timer Badge */}
                <div className="mt-3">
                  {audioCall.callState === 'CALLING' && (
                    <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-indigo-500/20 border border-indigo-400/30 text-indigo-200 text-xs font-bold animate-pulse shadow-sm">
                      <PhoneCall className="w-3.5 h-3.5 animate-bounce" />
                      <span>Connecting audio channel...</span>
                    </div>
                  )}
                  {audioCall.callState === 'RINGING' && (
                    <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-amber-500/20 border border-amber-400/30 text-amber-200 text-xs font-bold animate-pulse shadow-sm">
                      <PhoneCall className="w-3.5 h-3.5 animate-bounce" />
                      <span>Incoming Audio Consultation Request</span>
                    </div>
                  )}
                  {(audioCall.callState === 'CONNECTING' || audioCall.callState === 'ACCEPTED') && (
                    <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-blue-500/20 border border-blue-400/30 text-blue-200 text-xs font-bold animate-pulse shadow-sm">
                      <Activity className="w-3.5 h-3.5 animate-spin text-blue-400" />
                      <span>Negotiating WebRTC Peer Connection...</span>
                    </div>
                  )}
                  {audioCall.callState === 'CONNECTED' && (
                    <div className="inline-flex items-center space-x-2.5 px-5 py-2 rounded-full bg-emerald-500/15 border border-emerald-500/30 shadow-inner">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-400 animate-pulse shadow-[0_0_10px_#34d399]" />
                      <span className="text-xl font-mono font-black text-emerald-300 tracking-wider">
                        {formatDuration(audioCall.callDuration)}
                      </span>
                      <span className="text-[10px] font-extrabold text-emerald-400/90 uppercase tracking-widest bg-emerald-500/20 px-2 py-0.5 rounded-full">
                        Connected
                      </span>
                    </div>
                  )}
                  {audioCall.callState === 'RECONNECTING' && (
                    <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-amber-500/20 border border-amber-400/30 text-amber-200 text-xs font-bold animate-pulse">
                      <RefreshCw className="w-3.5 h-3.5 animate-spin text-amber-400" />
                      <span>Signal dropped • Reconnecting...</span>
                    </div>
                  )}
                  {audioCall.callState === 'DECLINED' && (
                    <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-rose-500/20 border border-rose-400/30 text-rose-300 text-xs font-bold">
                      <span>Call Declined</span>
                    </div>
                  )}
                  {audioCall.callState === 'MISSED' && (
                    <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-amber-500/20 border border-amber-400/30 text-amber-300 text-xs font-bold">
                      <span>Call Missed</span>
                    </div>
                  )}
                  {audioCall.callState === 'ENDED' && (
                    <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-slate-800 border border-slate-700 text-slate-300 text-xs font-bold">
                      <span>Call Concluded</span>
                    </div>
                  )}
                  {audioCall.callState === 'FAILED' && (
                    <div className="inline-flex items-center space-x-2 px-4 py-1.5 rounded-full bg-rose-500/20 border border-rose-400/30 text-rose-300 text-xs font-bold">
                      <span>Connection Failed</span>
                    </div>
                  )}
                </div>

                {/* Dynamic Sound Wave Visualizer */}
                <AudioVisualizerWaveform
                  isConnected={audioCall.callState === 'CONNECTED'}
                  isMuted={audioCall.isMuted}
                />
              </div>
            )}

            {/* Error Message */}
            {audioCall.error && (
              <div className="mx-6 mb-2 px-4 py-2 bg-rose-500/20 border border-rose-500/30 rounded-xl text-xs text-rose-300 font-medium text-center">
                {audioCall.error}
              </div>
            )}

            {/* Bottom Ergonomic Action Dock */}
            <div className="p-4 sm:p-6 pt-3 bg-slate-950/90 border-t border-slate-800/80 flex items-center justify-center gap-3 sm:gap-4 relative z-20">
              
              {/* RINGING State Actions */}
              {audioCall.callState === 'RINGING' && (
                <>
                  <button
                    onClick={audioCall.declineCall}
                    className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-rose-600 to-red-500 hover:from-rose-700 hover:to-red-600 text-white flex flex-col items-center justify-center shadow-xl shadow-rose-600/40 hover:scale-105 active:scale-95 transition-all cursor-pointer"
                    title="Decline Call"
                  >
                    <PhoneOff className="w-6 h-6" />
                    <span className="text-[10px] font-bold mt-1">Decline</span>
                  </button>
                  <button
                    onClick={() => audioCall.acceptCall(audioCall.incomingCallInfo?.callType || 'video')}
                    className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 hover:from-emerald-700 hover:to-teal-600 text-white flex flex-col items-center justify-center shadow-xl shadow-emerald-500/40 hover:scale-105 active:scale-95 transition-all cursor-pointer animate-pulse"
                    title={audioCall.incomingCallInfo?.callType === 'video' ? 'Accept Video Call' : 'Accept Audio Call'}
                  >
                    {audioCall.incomingCallInfo?.callType === 'video' ? <Video className="w-6 h-6" /> : <Phone className="w-6 h-6" />}
                    <span className="text-[10px] font-bold mt-1">Accept</span>
                  </button>
                </>
              )}

              {/* CALLING State Actions */}
              {audioCall.callState === 'CALLING' && (
                <button
                  onClick={audioCall.cancelCall}
                  className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-rose-600 to-red-500 hover:from-rose-700 hover:to-red-600 text-white flex flex-col items-center justify-center shadow-xl shadow-rose-600/40 hover:scale-105 active:scale-95 transition-all cursor-pointer"
                  title="Cancel Call"
                >
                  <PhoneOff className="w-6 h-6" />
                  <span className="text-[10px] font-bold mt-1">Cancel</span>
                </button>
              )}

              {/* CONNECTED & RECONNECTING State Actions */}
              {(audioCall.callState === 'CONNECTED' || audioCall.callState === 'RECONNECTING') && (
                <>
                  {/* Microphone Mute */}
                  <button
                    onClick={audioCall.toggleMute}
                    className={`w-14 h-14 rounded-2xl flex flex-col items-center justify-center transition-all cursor-pointer ${
                      audioCall.isMuted
                        ? 'bg-amber-500 hover:bg-amber-600 text-white shadow-xl shadow-amber-500/40 ring-2 ring-amber-400/50 scale-105'
                        : 'bg-slate-800/90 hover:bg-slate-700 text-slate-200 border border-slate-700/80 shadow-md'
                    }`}
                    title={audioCall.isMuted ? 'Unmute Microphone' : 'Mute Microphone'}
                  >
                    {audioCall.isMuted ? <MicOff className="w-5 h-5" /> : <Mic className="w-5 h-5" />}
                    <span className="text-[10px] font-bold mt-0.5">{audioCall.isMuted ? 'Muted' : 'Mute'}</span>
                  </button>

                  {/* Camera Video Toggle (For Video Calls) */}
                  {audioCall.callType === 'video' && (
                    <button
                      onClick={audioCall.toggleVideo}
                      className={`w-14 h-14 rounded-2xl flex flex-col items-center justify-center transition-all cursor-pointer ${
                        !audioCall.isVideoEnabled
                          ? 'bg-amber-500 hover:bg-amber-600 text-white shadow-xl shadow-amber-500/40 ring-2 ring-amber-400/50'
                          : 'bg-slate-800/90 hover:bg-slate-700 text-slate-200 border border-slate-700/80 shadow-md'
                      }`}
                      title={audioCall.isVideoEnabled ? 'Turn Off Camera' : 'Turn On Camera'}
                    >
                      {audioCall.isVideoEnabled ? <Camera className="w-5 h-5 text-purple-400" /> : <CameraOff className="w-5 h-5" />}
                      <span className="text-[10px] font-bold mt-0.5">{audioCall.isVideoEnabled ? 'Camera' : 'Cam Off'}</span>
                    </button>
                  )}

                  {/* Speaker Output Toggle */}
                  <button
                    onClick={() => setIsSpeakerOn(!isSpeakerOn)}
                    className={`w-14 h-14 rounded-2xl flex flex-col items-center justify-center transition-all cursor-pointer ${
                      isSpeakerOn
                        ? 'bg-slate-800/90 hover:bg-slate-700 text-slate-200 border border-slate-700/80 shadow-md'
                        : 'bg-slate-900 text-slate-500 border border-slate-800'
                    }`}
                    title="Toggle Speaker Output"
                  >
                    {isSpeakerOn ? <Volume2 className="w-5 h-5 text-blue-400" /> : <VolumeX className="w-5 h-5 text-slate-500" />}
                    <span className="text-[10px] font-bold mt-0.5">Speaker</span>
                  </button>

                  {/* End Call Button */}
                  <button
                    onClick={audioCall.endCall}
                    className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-rose-600 via-rose-500 to-red-600 hover:from-rose-700 hover:to-red-700 text-white flex flex-col items-center justify-center shadow-xl shadow-rose-600/50 hover:scale-105 active:scale-95 transition-all cursor-pointer ring-2 ring-rose-400/30"
                    title="End Teleconsultation"
                  >
                    <PhoneOff className="w-6 h-6" />
                    <span className="text-[10px] font-black mt-0.5">End</span>
                  </button>
                </>
              )}

              {/* CONNECTING / ACCEPTED State Action */}
              {(audioCall.callState === 'CONNECTING' || audioCall.callState === 'ACCEPTED') && (
                <button
                  onClick={audioCall.endCall}
                  className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-rose-600 to-red-500 hover:from-rose-700 hover:to-red-600 text-white flex flex-col items-center justify-center shadow-xl shadow-rose-600/40 hover:scale-105 active:scale-95 transition-all cursor-pointer"
                  title="Cancel"
                >
                  <PhoneOff className="w-6 h-6" />
                  <span className="text-[10px] font-bold mt-1">Cancel</span>
                </button>
              )}

              {/* Terminal States Actions */}
              {['DECLINED', 'MISSED', 'ENDED', 'FAILED'].includes(audioCall.callState) && (
                <div className="flex items-center space-x-3 w-full justify-center">
                  <button
                    onClick={() => {
                      audioCall.resetToIdle();
                      setIsCallMinimized(false);
                    }}
                    className="px-6 py-3 bg-slate-800 hover:bg-slate-700 text-white rounded-2xl border border-slate-700 text-xs font-bold transition-all cursor-pointer shadow-md"
                  >
                    Return to Workspace
                  </button>
                  {['DECLINED', 'FAILED', 'MISSED'].includes(audioCall.callState) && (
                    <button
                      onClick={() => {
                        const prevType = audioCall.callType;
                        audioCall.resetToIdle();
                        setIsCallMinimized(false);
                        setTimeout(() => audioCall.startCall(prevType), 300);
                      }}
                      className="px-6 py-3 bg-gradient-to-r from-blue-600 via-indigo-600 to-purple-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-2xl text-xs font-extrabold transition-all cursor-pointer shadow-xl shadow-indigo-500/40 flex items-center gap-2"
                    >
                      <RefreshCw className="w-3.5 h-3.5" />
                      <span>Retry Call</span>
                    </button>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ── DOCKED FLOATING PIP CALL WIDGET (When Minimized) ───────────────── */}
      {audioCall.callState !== 'IDLE' && isCallMinimized && (
        <div className="fixed bottom-6 right-6 z-[9999] bg-slate-950/95 backdrop-blur-2xl border border-indigo-500/40 rounded-2xl shadow-[0_15px_50px_rgba(0,0,0,0.8)] p-3 flex items-center space-x-3.5 text-white animate-scale-in">
          {/* Avatar with pulse dot */}
          <div className="relative">
            <div className="w-11 h-11 rounded-xl bg-gradient-to-tr from-blue-600 via-indigo-600 to-purple-600 flex items-center justify-center font-black text-sm shadow-md">
              {(isDoctor ? patientDisplayName : doctorDisplayName).substring(0, 2).toUpperCase()}
            </div>
            {audioCall.callState === 'CONNECTED' && (
              <>
                <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 border-2 border-slate-950 rounded-full animate-ping" />
                <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 bg-emerald-500 border-2 border-slate-950 rounded-full" />
              </>
            )}
          </div>

          {/* Call Metadata */}
          <div className="text-left min-w-[130px]">
            <div className="text-xs font-black text-white flex items-center space-x-1.5 truncate max-w-[140px]">
              <span className="truncate">{isDoctor ? patientDisplayName : doctorDisplayName}</span>
              <span className="text-[9px] px-1.5 py-0.2 bg-indigo-500/30 text-indigo-300 rounded font-mono font-bold">HD</span>
            </div>
            <div className="flex items-center space-x-1.5 text-[11px] font-mono font-bold text-emerald-400 mt-0.5">
              <span>{formatDuration(audioCall.callDuration)}</span>
              <span className="text-slate-600">•</span>
              <span className="text-slate-400 text-[10px]">{audioCall.isMuted ? 'Muted' : 'Active'}</span>
            </div>
          </div>

          {/* Quick Action Controls */}
          <div className="flex items-center space-x-1.5 pl-2 border-l border-slate-800">
            <button
              onClick={audioCall.toggleMute}
              className={`p-2 rounded-xl transition-all cursor-pointer ${
                audioCall.isMuted ? 'bg-amber-500 text-white' : 'bg-slate-800 hover:bg-slate-700 text-slate-200'
              }`}
              title={audioCall.isMuted ? 'Unmute' : 'Mute'}
            >
              {audioCall.isMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
            </button>
            <button
              onClick={() => setIsCallMinimized(false)}
              className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700/60 transition-all cursor-pointer"
              title="Expand Calling Window"
            >
              <Maximize2 className="w-4 h-4" />
            </button>
            <button
              onClick={audioCall.endCall}
              className="p-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white shadow-md shadow-rose-600/40 transition-all cursor-pointer"
              title="End Call"
            >
              <PhoneOff className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* ── 2-COLUMN CLINICAL WORKSPACE GRID ───────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start h-[calc(100vh-170px)] min-h-[640px] max-h-[880px]">

        {/* ── LEFT COLUMN: Case Queue / Consultations List (3.5 cols) ───────── */}
        <div className="lg:col-span-4 bg-white border border-slate-200/90 rounded-2xl p-4 space-y-3.5 shadow-lg shadow-slate-100/60 flex flex-col h-full overflow-hidden">
          {/* Queue Header & Filters */}
          <div className="space-y-2 shrink-0">
            <div className="flex items-center justify-between">
              <h3 className="text-sm font-black text-slate-900 flex items-center space-x-2">
                <span>{isDoctor ? 'Assigned Patient Queue' : 'My Consultation Cases'}</span>
                <span className="bg-slate-100 text-slate-700 text-xs px-2 py-0.5 rounded-full font-mono">
                  {filteredConsultations.length}
                </span>
              </h3>
              {isPatient && (
                <button
                  onClick={() => setIsNewModalOpen(true)}
                  className="text-xs font-bold text-blue-600 hover:text-blue-800 flex items-center space-x-1"
                >
                  <PlusCircle size={14} />
                  <span>New Request</span>
                </button>
              )}
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center space-x-1 bg-slate-100/80 p-1 rounded-xl text-xs font-bold text-slate-600">
              {['ALL', 'ACTIVE', 'PENDING', 'COMPLETED'].map((f) => (
                <button
                  key={f}
                  onClick={() => setQueueFilter(f)}
                  className={`flex-1 py-1 rounded-lg transition-all text-[11px] cursor-pointer ${
                    queueFilter === f ? 'bg-white text-slate-900 shadow-xs font-extrabold' : 'hover:text-slate-900'
                  }`}
                >
                  {f}
                </button>
              ))}
            </div>

            {/* Search Box */}
            <div className="relative">
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                placeholder={isDoctor ? "Search patient name..." : "Search doctor name or specialty..."}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200/80 rounded-xl text-xs text-slate-900 focus:outline-none focus:border-blue-500 focus:bg-white"
              />
              {searchQuery && (
                <button onClick={() => setSearchQuery('')} className="absolute right-2.5 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600">
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Case List */}
          <div className="flex-1 overflow-y-auto space-y-2 pr-1 custom-scrollbar">
            {loading ? (
              <div className="py-12 text-center text-xs text-slate-400 space-y-2">
                <RefreshCw className="w-5 h-5 animate-spin mx-auto text-blue-600" />
                <p>Retrieving consultation records...</p>
              </div>
            ) : filteredConsultations.length === 0 ? (
              <div className="py-10 text-center space-y-2.5 px-3 border border-dashed border-slate-200/80 rounded-2xl bg-slate-50/50 my-auto">
                <Stethoscope className="w-8 h-8 text-slate-300 mx-auto" />
                <p className="text-xs font-bold text-slate-700">No consultations found</p>
                <p className="text-[11px] text-slate-500">
                  {isDoctor ? 'Assigned patient teleconsultations will appear here.' : 'Your booked doctor consultations will appear here.'}
                </p>
              </div>
            ) : (
              filteredConsultations.map((c, idx) => {
                const isSelected = activeConsultation && (activeConsultation.consultation_id === c.consultation_id || activeConsultation.id === c.id);
                const displayName = isDoctor
                  ? (c.patient_name || 'Patient')
                  : (c.doctor_name || c.assigned_doctor_name || 'Attending Physician');
                const urgencyUpper = (c.urgency || 'ROUTINE').toUpperCase();
                const statusUpper = (c.status || 'ACTIVE').toUpperCase();

                return (
                  <div
                    key={`${c.consultation_id || c.id || 'cons'}_${idx}`}
                    onClick={() => setSelectedConsultation(c)}
                    className={`p-3 rounded-2xl cursor-pointer transition-all border ${
                      isSelected
                        ? 'bg-gradient-to-r from-blue-50/90 to-indigo-50/80 border-blue-500/80 shadow-md shadow-blue-500/5 ring-1 ring-blue-500/20'
                        : 'bg-white border-slate-200/70 hover:border-slate-300 hover:bg-slate-50/80'
                    }`}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold flex items-center justify-center text-xs shrink-0 shadow-sm">
                        {(displayName || 'Doc').split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-0.5">
                          <h4 className="text-xs font-bold text-slate-900 truncate">{displayName}</h4>
                          <span className={`text-[9px] font-extrabold px-2 py-0.5 rounded-full ${
                            urgencyUpper === 'URGENT' || urgencyUpper === 'HIGH' ? 'bg-rose-100 text-rose-700' :
                            urgencyUpper === 'SOON' ? 'bg-amber-100 text-amber-800' : 'bg-blue-100 text-blue-700'
                          }`}>
                            {urgencyUpper}
                          </span>
                        </div>

                        <p className="text-[11px] font-semibold text-slate-500 truncate mb-1">
                          {c.category || c.specialization || 'Clinical Evaluation'}
                        </p>

                        <div className="flex items-center justify-between text-[10px]">
                          <span className="text-slate-400 font-mono">ID: {c.consultation_id}</span>
                          <span className={`font-bold ${statusUpper === 'COMPLETED' ? 'text-emerald-600' : 'text-blue-600'}`}>
                            {statusUpper}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </div>

        {/* ── RIGHT COLUMN: Active Clinical Workspace (8.5 cols) ───────────── */}
        <div className="lg:col-span-8 bg-white border border-slate-200/90 rounded-2xl flex flex-col h-full overflow-hidden shadow-lg shadow-slate-100/60">
          
          {!activeConsultation ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-slate-50/50">
              <div className="w-16 h-16 rounded-3xl bg-blue-50 border border-blue-100 flex items-center justify-center text-blue-600 mb-4 shadow-sm">
                <Stethoscope className="w-8 h-8" />
              </div>
              <h3 className="text-base font-extrabold text-slate-900 mb-1">
                {isDoctor ? 'No Patient Consultation Selected' : 'No Active Doctor Consultation'}
              </h3>
              <p className="text-xs text-slate-500 max-w-md mb-6 leading-relaxed">
                {isDoctor
                  ? 'Select an assigned patient consultation case from the left panel to review clinical data, chat live, or issue diagnoses & prescriptions.'
                  : 'You do not currently have an active doctor consultation. Create a new consultation request or book an appointment to begin.'}
              </p>
              {!isDoctor && (
                <button
                  onClick={() => setIsNewModalOpen(true)}
                  className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-xs font-bold rounded-xl hover:from-blue-700 hover:to-indigo-700 transition-all cursor-pointer shadow-md shadow-blue-500/20 flex items-center space-x-2"
                >
                  <PlusCircle size={16} />
                  <span>Request Doctor Consultation</span>
                </button>
              )}
            </div>
          ) : (
            <>
              {/* Active Workspace Header Bar */}
              <div className="p-4 border-b border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white shrink-0 shadow-2xs">
                <div className="flex items-center space-x-3.5">
                  <div className="w-11 h-11 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold flex items-center justify-center text-sm shadow-md shrink-0">
                    {(isDoctor ? patientDisplayName : doctorDisplayName).split(' ').map(n => n[0]).join('').slice(0, 2).toUpperCase()}
                  </div>

                  <div>
                    <div className="flex items-center space-x-2.5">
                      <h3 className="text-sm font-extrabold text-slate-900">
                        {isDoctor ? patientDisplayName : doctorDisplayName}
                      </h3>
                      {isDoctor && (
                        <span className="text-[10px] font-mono font-bold text-slate-500 bg-slate-100 px-2 py-0.5 rounded-md">
                          {patientDisplayId}
                        </span>
                      )}
                      <span className="bg-emerald-100 text-emerald-800 text-[10px] font-extrabold px-2.5 py-0.5 rounded-full flex items-center gap-1">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                        {(activeConsultation?.status || 'ACTIVE').toUpperCase()}
                      </span>
                    </div>

                    <p className="text-xs text-slate-500 mt-0.5">
                      {activeConsultation?.category || activeConsultation?.specialization || 'Clinical Assessment'} • {isDoctor ? 'Registered Patient' : 'Attending Physician'}
                    </p>
                  </div>
                </div>

                {/* Header Right Action Buttons */}
                <div className="flex items-center space-x-2 shrink-0">
                  <ConsultationTimer isActive={activeConsultation?.status !== 'COMPLETED'} />

                  {isDoctor && (activeConsultation?.status === 'ASSIGNED' || activeConsultation?.status === 'REQUESTED') && (
                    <button
                      onClick={handleAcceptAssignment}
                      className="px-3.5 py-2 text-xs font-bold text-white bg-emerald-600 hover:bg-emerald-700 rounded-xl transition-all cursor-pointer flex items-center space-x-1.5 shadow-md shadow-emerald-600/20"
                    >
                      <Check size={14} />
                      <span>Accept Case</span>
                    </button>
                  )}

                  {isDoctor && activeConsultation?.status !== 'COMPLETED' && (
                    <button
                      onClick={handleCompleteConsultation}
                      disabled={completing}
                      className="px-3.5 py-2 text-xs font-bold text-white bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 rounded-xl transition-all cursor-pointer flex items-center space-x-1.5 shadow-md shadow-blue-500/20"
                    >
                      {completing ? <RefreshCw size={14} className="animate-spin" /> : <CheckCircle size={14} />}
                      <span>Sign & Complete</span>
                    </button>
                  )}
                </div>
              </div>

              {/* Workspace Navigation Tabs */}
              <div className="flex items-center justify-between border-b border-slate-100 bg-slate-50/50 px-4 shrink-0">
                <div className="flex items-center space-x-1">
                  <button
                    onClick={() => setWorkspaceTab('chat')}
                    className={`px-4 py-2.5 text-xs font-extrabold border-b-2 transition-all flex items-center space-x-2 cursor-pointer ${
                      workspaceTab === 'chat'
                        ? 'border-blue-600 text-blue-600 bg-white'
                        : 'border-transparent text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    <MessageSquare size={14} />
                    <span>Live Consultation Chat</span>
                  </button>

                  {isDoctor && (
                    <button
                      onClick={() => setWorkspaceTab('soap')}
                      className={`px-4 py-2.5 text-xs font-extrabold border-b-2 transition-all flex items-center space-x-2 cursor-pointer ${
                        workspaceTab === 'soap'
                          ? 'border-blue-600 text-blue-600 bg-white'
                          : 'border-transparent text-slate-500 hover:text-slate-800'
                      }`}
                    >
                      <Edit3 size={14} />
                      <span>SOAP Clinical Notes</span>
                    </button>
                  )}

                  <button
                    onClick={() => setWorkspaceTab('records')}
                    className={`px-4 py-2.5 text-xs font-extrabold border-b-2 transition-all flex items-center space-x-2 cursor-pointer ${
                      workspaceTab === 'records'
                        ? 'border-blue-600 text-blue-600 bg-white'
                        : 'border-transparent text-slate-500 hover:text-slate-800'
                    }`}
                  >
                    <FileText size={14} />
                    <span>Biomarkers & Records</span>
                  </button>
                </div>

                <div className="flex items-center space-x-2 text-[11px] text-slate-500 font-medium">
                  <ShieldCheck size={14} className="text-emerald-500" />
                  <span>HIPAA Encrypted Channel</span>
                </div>
              </div>

              {/* TAB 1: LIVE CHAT AREA */}
              {workspaceTab === 'chat' && (
                <div className="flex-1 flex flex-col justify-between overflow-hidden bg-slate-50/40">
                  {/* Messages Feed */}
                  <div className="flex-1 p-4 overflow-y-auto space-y-3 custom-scrollbar">
                    {loadingMessages ? (
                      <div className="py-12 text-center text-xs text-slate-400 space-y-2">
                        <RefreshCw className="w-5 h-5 animate-spin mx-auto text-blue-600" />
                        <p>Syncing encrypted message log...</p>
                      </div>
                    ) : messagesThread.length === 0 ? (
                      <div className="py-12 text-center space-y-2 text-slate-400">
                        <MessageCircle className="w-8 h-8 text-slate-300 mx-auto" />
                        <p className="text-xs font-bold text-slate-600">No messages sent yet in this consultation session.</p>
                        <p className="text-[11px]">Type a message below to communicate directly with your attending physician.</p>
                      </div>
                    ) : (
                      messagesThread.map((msg, i) => {
                        const isSelf = msg.role === role || msg.sender === (user?.full_name || user?.name);
                        return (
                          <div
                            key={msg.id || i}
                            className={`flex flex-col ${isSelf ? 'items-end' : 'items-start'}`}
                          >
                            <div className="flex items-center space-x-1.5 mb-1 px-1">
                              <span className="text-[10px] font-bold text-slate-500">{msg.sender}</span>
                              <span className="text-[9px] text-slate-400">• {msg.time}</span>
                            </div>
                            <div
                              className={`max-w-[75%] p-3.5 rounded-2xl text-xs leading-relaxed font-medium shadow-xs ${
                                isSelf
                                  ? 'bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-br-none'
                                  : 'bg-white border border-slate-200/90 text-slate-900 rounded-bl-none shadow-slate-100'
                              }`}
                            >
                              {msg.text}
                            </div>
                          </div>
                        );
                      })
                    )}

                    {isOtherTyping && (
                      <div className="flex items-center space-x-2 text-xs text-slate-400 italic">
                        <div className="flex space-x-1">
                          <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce" />
                          <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:0.2s]" />
                          <span className="w-1.5 h-1.5 bg-blue-500 rounded-full animate-bounce [animation-delay:0.4s]" />
                        </div>
                        <span>Attending physician is typing...</span>
                      </div>
                    )}
                    <div ref={chatEndRef} />
                  </div>

                  {/* Chat Input Bar */}
                  <form onSubmit={handleSendMessage} className="p-3 bg-white border-t border-slate-200/80 flex items-center space-x-2 shrink-0">
                    <input
                      type="text"
                      placeholder={activeConsultation?.status === 'COMPLETED' ? 'Consultation completed (read only).' : 'Type message to attending doctor...'}
                      disabled={activeConsultation?.status === 'COMPLETED' || messageSending}
                      value={patientNewMessage}
                      onChange={handleInputChange}
                      className="flex-1 p-2.5 bg-slate-50 border border-slate-200 rounded-xl text-xs text-slate-900 focus:outline-none focus:border-blue-500 focus:bg-white disabled:opacity-60"
                    />
                    <button
                      type="submit"
                      disabled={!patientNewMessage.trim() || activeConsultation?.status === 'COMPLETED' || messageSending}
                      className="px-4 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white text-xs font-bold rounded-xl disabled:opacity-50 transition-all cursor-pointer shadow-md shadow-blue-500/20 flex items-center space-x-1.5"
                    >
                      {messageSending ? <RefreshCw size={14} className="animate-spin" /> : <Send size={14} />}
                      <span>Send</span>
                    </button>
                  </form>
                </div>
              )}

              {/* TAB 2: SOAP CLINICAL NOTES (DOCTOR PORTAL) */}
              {workspaceTab === 'soap' && (
                <div className="flex-1 p-5 overflow-y-auto custom-scrollbar space-y-4 bg-slate-50/30">
                  <div className="flex items-center justify-between">
                    <h4 className="text-xs font-extrabold text-slate-900 uppercase tracking-wider">SOAP Clinical Documentation</h4>
                    {isDoctor && (
                      <button
                        onClick={handleSaveClinicalNotes}
                        disabled={savingNotes}
                        className="px-3.5 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-bold rounded-xl flex items-center space-x-1.5 shadow-sm"
                      >
                        {savingNotes ? <RefreshCw size={12} className="animate-spin" /> : <Save size={12} />}
                        <span>Save Clinical Notes</span>
                      </button>
                    )}
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">Chief Symptoms & Complaints</label>
                      <textarea
                        rows={3}
                        value={clinicalNotes.chiefComplaints}
                        onChange={(e) => setClinicalNotes({ ...clinicalNotes, chiefComplaints: e.target.value })}
                        placeholder="Patient reported symptoms..."
                        className="w-full p-2.5 text-xs bg-white border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:border-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-slate-700 mb-1">Physical & Vital Examinations</label>
                      <textarea
                        rows={3}
                        value={clinicalNotes.examination}
                        onChange={(e) => setClinicalNotes({ ...clinicalNotes, examination: e.target.value })}
                        placeholder="Vital observations..."
                        className="w-full p-2.5 text-xs bg-white border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:border-blue-500"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Assessment & Diagnosis</label>
                    <textarea
                      rows={3}
                      value={clinicalNotes.assessmentDiagnosis}
                      onChange={(e) => setClinicalNotes({ ...clinicalNotes, assessmentDiagnosis: e.target.value })}
                      placeholder="Doctor diagnosis & assessment..."
                      className="w-full p-2.5 text-xs bg-white border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Prescription & Medications</label>
                    <textarea
                      rows={3}
                      value={clinicalNotes.prescription}
                      onChange={(e) => setClinicalNotes({ ...clinicalNotes, prescription: e.target.value })}
                      placeholder="Rx dosage & instructions..."
                      className="w-full p-2.5 text-xs bg-white border border-slate-200 rounded-xl text-slate-900 focus:outline-none focus:border-blue-500 font-mono"
                    />
                  </div>
                </div>
              )}

              {/* TAB 3: BIOMARKERS & RECORDS HUB */}
              {workspaceTab === 'records' && (
                <div className="flex-1 p-5 overflow-y-auto custom-scrollbar space-y-4 bg-slate-50/30">
                  <RiskScoreGauge score={38} maxScore={100} />

                  <div className="p-4 bg-white border border-slate-200/90 rounded-2xl space-y-3 shadow-xs">
                    <div className="flex items-center justify-between">
                      <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider">Patient Clinical Records ({healthRecords.length})</h4>
                      <button onClick={() => navigate('/records')} className="text-xs text-blue-600 font-bold hover:underline flex items-center gap-1">
                        <span>Open Records Hub</span>
                        <ExternalLink size={12} />
                      </button>
                    </div>

                    {healthRecords.length === 0 ? (
                      <p className="text-xs text-slate-400 py-3 italic text-center">No specific lab reports attached to this case file.</p>
                    ) : (
                      <div className="space-y-2">
                        {healthRecords.map(r => (
                          <div key={r.record_id || r.id} className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between text-xs">
                            <div className="flex items-center space-x-3">
                              <FileText className="w-4 h-4 text-blue-600" />
                              <div>
                                <span className="font-bold text-slate-900 block">{r.file_name || r.title || 'Lab Report'}</span>
                                <span className="text-[10px] text-slate-400 font-mono">{r.record_type || 'Biomarker Assessment'}</span>
                              </div>
                            </div>

                            <button onClick={() => navigate('/records')} className="px-3 py-1 bg-white border border-slate-200 text-slate-700 font-bold rounded-lg text-[11px] hover:bg-slate-100">
                              View File
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}

        </div>

      </div>

    </PageContainer>
  );
}
