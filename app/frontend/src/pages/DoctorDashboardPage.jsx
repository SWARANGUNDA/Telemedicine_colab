import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  RefreshCw, Search, CheckCircle2, ShieldCheck, Clock, FileText,
  Hourglass, Bell, ChevronRight, Eye, MessageCircle, ShieldAlert,
  Sparkles, TrendingUp, BarChart3, ArrowRight, User
} from 'lucide-react';
import {
  Button, Card, Badge, Table, TableRow, TableCell, Modal
} from '../components/ui';
import { PageContainer } from '../components/layout';
import {
  fetchDoctorConsultations,
  respondToDoctorAssignment,
  getAuthToken,
  getWsBaseUrl
} from '../api/client';
import WorkloadPanel from '../components/doctor/WorkloadPanel';
import HighRiskPatients from '../components/doctor/HighRiskPatients';
import ReviewAnalytics from '../components/doctor/ReviewAnalytics';
import InsightsPanel from '../components/doctor/InsightsPanel';
import OutcomeTracking from '../components/doctor/OutcomeTracking';

export default function DoctorDashboardPage({ user, onNavigate }) {
  const navigate = useNavigate();
  const doctor = user?.doctor_profile || {};
  const verificationStatus = doctor.verification_status || 'VERIFIED';
  
  // Doctor identity resolution
  const doctorName = user?.full_name || user?.name || doctor.full_name || 'Physician';
  const formattedDoctorName = doctorName.startsWith('Dr.') ? doctorName : `Dr. ${doctorName}`;
  const doctorSpecialty = doctor.specialty || doctor.specialization || 'General Practice & Medicine';

  const [allConsultations, setAllConsultations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [submittingAction, setSubmittingAction] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);
  const [successMsg, setSuccessMsg] = useState(null);

  // Queue state & filters
  const [activeQueueTab, setActiveQueueTab] = useState('ALL'); // 'ALL', 'PENDING', 'IN_REVIEW', 'COMPLETED'
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedConsultationForDetails, setSelectedConsultationForDetails] = useState(null);
  const [showDetailedAnalyticsModal, setShowDetailedAnalyticsModal] = useState(false);

  useEffect(() => {
    loadAllConsultations();
  }, [user]);

  useEffect(() => {
    if (!user?.user_id) return;
    let ws = null;
    try {
      const wsBase = getWsBaseUrl();
      if (!wsBase) return;
      const token = getAuthToken() || user.user_id;
      ws = new WebSocket(`${wsBase}/ws/notifications/${user.user_id}?token=${encodeURIComponent(token)}`);
      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          const evt = data.event || data.type;
          if (evt && (evt.startsWith('APPOINTMENT_') || evt.startsWith('CONSULTATION_') || evt === 'DOCTOR_AVAILABILITY_UPDATED')) {
            loadAllConsultations();
          }
        } catch (e) {}
      };
      ws.onerror = () => {};
    } catch (e) {}
    return () => {
      if (ws) {
        if (ws.readyState === WebSocket.CONNECTING) {
          ws.onopen = () => ws.close();
        } else if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      }
    };
  }, [user]);

  const loadAllConsultations = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const data = await fetchDoctorConsultations('');
      setAllConsultations(Array.isArray(data) ? data : (data?.consultations || []));
    } catch (err) {
      setErrorMsg(err.message || 'Failed to fetch assigned consultations.');
      setAllConsultations([]);
    } finally {
      setLoading(false);
    }
  };

  const handleRespondAssignment = async (consultationId, action) => {
    let reason = '';
    if (action === 'REJECT' || action === 'DECLINE') {
      reason = window.prompt("Reason for declining this consultation request (optional):") || '';
    }
    setSubmittingAction(true);
    setErrorMsg(null);
    setSuccessMsg(null);
    try {
      await respondToDoctorAssignment(consultationId, action, reason);
      setSuccessMsg(`Consultation request ${action === 'ACCEPT' ? 'confirmed' : 'declined'} successfully.`);
      setSelectedConsultationForDetails(null);
      await loadAllConsultations();
    } catch (err) {
      setErrorMsg(err.message || `Failed to ${action.toLowerCase()} consultation request.`);
    } finally {
      setSubmittingAction(false);
    }
  };

  const handleOpenConsultationWorkspace = (consultation) => {
    const targetId = typeof consultation === 'object' ? (consultation?.consultation_id || consultation?.id) : consultation;
    if (onNavigate) {
      onNavigate('/doctor/consultations', { consultationContext: { consultationId: targetId } });
    } else {
      navigate('/doctor/consultations');
    }
  };

  // Metrics calculation from source of truth (allConsultations)
  const pendingConsultations = allConsultations.filter(c => ['REQUESTED', 'ASSIGNED', 'PENDING'].includes(c.status));
  const inReviewConsultations = allConsultations.filter(c => ['ACCEPTED', 'CONFIRMED', 'UPCOMING', 'IN_CONSULTATION', 'ACTIVE'].includes(c.status));
  const completedConsultations = allConsultations.filter(c => c.status === 'COMPLETED');
  
  const totalCount = allConsultations.length;
  const pendingCount = pendingConsultations.length;
  const inReviewCount = inReviewConsultations.length;
  const completedCount = completedConsultations.length;

  // Filtered queue for table
  const filteredQueue = allConsultations.filter(c => {
    // Tab filter
    if (activeQueueTab === 'PENDING' && !['REQUESTED', 'ASSIGNED', 'PENDING'].includes(c.status)) return false;
    if (activeQueueTab === 'IN_REVIEW' && !['ACCEPTED', 'CONFIRMED', 'UPCOMING', 'IN_CONSULTATION', 'ACTIVE'].includes(c.status)) return false;
    if (activeQueueTab === 'COMPLETED' && c.status !== 'COMPLETED') return false;

    // Search query
    const pName = (c.patient_name || c.full_name || '').toLowerCase();
    const pId = (c.patient_id || c.user_id || '').toLowerCase();
    const cId = (c.consultation_id || c.id || '').toLowerCase();
    const spec = (c.specialty || c.category || '').toLowerCase();
    const q = searchQuery.toLowerCase();

    return !q || pName.includes(q) || pId.includes(q) || cId.includes(q) || spec.includes(q);
  });

  // Highlight pending case for Action Required Banner
  const actionRequiredCase = pendingConsultations[0];

  if (verificationStatus !== 'VERIFIED') {
    return (
      <PageContainer className="space-y-8 py-8">
        <Card isGlass={true} className="p-8 text-center space-y-4 max-w-xl mx-auto border border-amber-500/20 rounded-2xl">
          <ShieldAlert className="w-12 h-12 text-amber-500 mx-auto" />
          <h3 className="text-lg font-bold text-[var(--text-main)]">Physician Verification Pending</h3>
          <p className="text-xs text-[var(--text-muted)] leading-relaxed">
            Your medical license credentials are currently under review by the TeleMed AI Administration Board. Once verified, you will be granted access to clinical case intake reports and Virtual Chat consultations.
          </p>
        </Card>
      </PageContainer>
    );
  }

  return (
    <PageContainer className="space-y-6 py-6 pb-20">
      {/* 1. MAIN WELCOME HEADER BANNER */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--border-subtle)] pb-5">
        <div className="space-y-1">
          <div className="flex items-center gap-2.5 flex-wrap">
            <h1 className="text-2xl font-black text-[var(--text-main)] tracking-tight">
              Welcome back, {formattedDoctorName}
            </h1>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> License Verified
            </span>
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-sky-500/10 text-sky-600 dark:text-sky-400 border border-sky-500/20">
              {doctorSpecialty}
            </span>
          </div>
          <p className="text-xs text-[var(--text-muted)]">
            Clinical case review, AI insights, and patient care management
          </p>
        </div>

        <Button
          variant="outline"
          size="sm"
          className="self-start md:self-auto !px-3.5 !py-2 rounded-xl text-xs font-semibold"
          leftIcon={<RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin' : ''}`} />}
          onClick={loadAllConsultations}
        >
          Refresh Data
        </Button>
      </div>

      {/* 2. FIVE RESPONSIVE KPI CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3.5">
        {/* Active Cases */}
        <Card isGlass={true} className="p-4 space-y-2 border-l-4 border-l-sky-500 rounded-2xl bg-[var(--bg-surface)] shadow-sm">
          <div className="flex justify-between items-center text-xs">
            <span className="font-mono text-[10px] text-[var(--text-muted)] uppercase font-semibold">Active Cases</span>
            <FileText className="w-4 h-4 text-sky-500" />
          </div>
          <div className="text-2xl font-black font-mono text-[var(--text-main)]">{totalCount}</div>
          <p className="text-[10px] text-[var(--text-muted)] font-medium">Assigned to you</p>
        </Card>

        {/* Pending Review */}
        <Card isGlass={true} className="p-4 space-y-2 border-l-4 border-l-amber-500 rounded-2xl bg-[var(--bg-surface)] shadow-sm">
          <div className="flex justify-between items-center text-xs">
            <span className="font-mono text-[10px] text-[var(--text-muted)] uppercase font-semibold">Pending Review</span>
            <Clock className="w-4 h-4 text-amber-500" />
          </div>
          <div className="text-2xl font-black font-mono text-amber-600 dark:text-amber-400">{pendingCount}</div>
          <p className="text-[10px] text-[var(--text-muted)] font-medium">Requires your review</p>
        </Card>

        {/* Completed Consults */}
        <Card isGlass={true} className="p-4 space-y-2 border-l-4 border-l-emerald-500 rounded-2xl bg-[var(--bg-surface)] shadow-sm">
          <div className="flex justify-between items-center text-xs">
            <span className="font-mono text-[10px] text-[var(--text-muted)] uppercase font-semibold">Completed Consults</span>
            <CheckCircle2 className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-2xl font-black font-mono text-emerald-600 dark:text-emerald-400">{completedCount}</div>
          <p className="text-[10px] text-[var(--text-muted)] font-medium">This month</p>
        </Card>

        {/* Cases In Review */}
        <Card isGlass={true} className="p-4 space-y-2 border-l-4 border-l-purple-500 rounded-2xl bg-[var(--bg-surface)] shadow-sm">
          <div className="flex justify-between items-center text-xs">
            <span className="font-mono text-[10px] text-[var(--text-muted)] uppercase font-semibold">Cases In Review</span>
            <Hourglass className="w-4 h-4 text-purple-500" />
          </div>
          <div className="text-2xl font-black font-mono text-purple-600 dark:text-purple-400">{inReviewCount}</div>
          <p className="text-[10px] text-[var(--text-muted)] font-medium">Under evaluation</p>
        </Card>

        {/* Verification */}
        <Card isGlass={true} className="p-4 space-y-2 border-l-4 border-l-emerald-500 rounded-2xl bg-[var(--bg-surface)] shadow-sm">
          <div className="flex justify-between items-center text-xs">
            <span className="font-mono text-[10px] text-[var(--text-muted)] uppercase font-semibold">Verification</span>
            <ShieldCheck className="w-4 h-4 text-emerald-500" />
          </div>
          <div className="text-xl font-black font-mono text-emerald-600 dark:text-emerald-400">Active</div>
          <p className="text-[10px] text-[var(--text-muted)] font-medium">Doctor verified access</p>
        </Card>
      </div>

      {/* 3. ACTION REQUIRED SECTION (ALERT CARD) */}
      <div className="p-5 rounded-2xl border border-amber-500/30 bg-gradient-to-r from-amber-500/10 via-amber-500/5 to-transparent shadow-sm space-y-3">
        <div className="flex items-center gap-2 text-amber-700 dark:text-amber-400">
          <Bell className="w-4 h-4 text-amber-500 animate-bounce" />
          <h3 className="text-sm font-black tracking-tight">Action Required</h3>
          <span className="text-xs font-semibold text-[var(--text-muted)]">
            • {pendingCount} {pendingCount === 1 ? 'consultation' : 'consultations'} awaiting your review and sign-off
          </span>
        </div>

        {actionRequiredCase ? (
          <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-xl bg-[var(--bg-surface)] border border-[var(--border-subtle)]">
            <div className="flex items-center gap-3.5">
              <div className="w-10 h-10 rounded-full bg-purple-500/10 text-purple-600 dark:text-purple-400 font-extrabold text-sm flex items-center justify-center border border-purple-500/20 shrink-0">
                {(actionRequiredCase.patient_name || 'Rahul Reddy').split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()}
              </div>
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-bold text-[var(--text-main)]">
                    {actionRequiredCase.patient_name || 'Patient'}
                  </span>
                  <span className="text-xs font-medium text-[var(--text-muted)]">
                    • {actionRequiredCase.specialty || doctorSpecialty}
                  </span>
                  <span className="font-mono text-[11px] text-[var(--primary)] font-semibold">
                    Consultation ID: {actionRequiredCase.consultation_id || actionRequiredCase.id}
                  </span>
                  <span className="px-2 py-0.5 text-[9.5px] font-bold rounded-full bg-purple-500/10 text-purple-600 dark:text-purple-400 border border-purple-500/20">
                    AI Report Ready
                  </span>
                </div>
                <p className="text-xs text-[var(--text-muted)]">
                  AI analysis completed — Physician review and sign-off required
                </p>
              </div>
            </div>

            <Button
              variant="primary"
              size="sm"
              className="!px-4 !py-2 text-xs font-bold rounded-xl shrink-0"
              onClick={() => handleOpenConsultationWorkspace(actionRequiredCase)}
            >
              Review Case →
            </Button>
          </div>
        ) : (
          <div className="p-3 text-xs text-[var(--text-muted)] font-medium italic">
            You're all caught up — No consultations awaiting review.
          </div>
        )}
      </div>

      {/* 4. PATIENT REVIEW QUEUE SECTION */}
      <Card isGlass={true} className="p-5 space-y-4 shadow-sm border border-[var(--border-subtle)] rounded-2xl bg-[var(--bg-surface)]">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-[var(--border-subtle)] pb-4">
          <div className="space-y-0.5">
            <div className="flex items-center gap-2">
              <FileText className="w-4 h-4 text-[var(--primary)]" />
              <h3 className="text-base font-bold text-[var(--text-main)]">Patient Review Queue</h3>
            </div>
            <p className="text-xs text-[var(--text-muted)]">
              Consultations requiring physician review and sign-off
            </p>
          </div>

          <div className="flex items-center gap-3 flex-wrap">
            {/* Search Input */}
            <div className="relative w-64">
              <Search className="w-3.5 h-3.5 absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]" />
              <input
                type="text"
                placeholder="Search patient, ID, specialty..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-[var(--bg-primary)] text-xs text-[var(--text-main)] rounded-xl pl-8 pr-3 py-1.5 border border-[var(--border-subtle)] focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
              />
            </div>

            {/* Filter Tabs */}
            <div className="flex items-center p-1 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-xs font-semibold">
              <button
                onClick={() => setActiveQueueTab('ALL')}
                className={`px-3 py-1 rounded-lg transition-all ${activeQueueTab === 'ALL' ? 'bg-[var(--bg-surface)] text-[var(--primary)] shadow-sm' : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'}`}
              >
                All ({totalCount})
              </button>
              <button
                onClick={() => setActiveQueueTab('PENDING')}
                className={`px-3 py-1 rounded-lg transition-all ${activeQueueTab === 'PENDING' ? 'bg-[var(--bg-surface)] text-amber-600 dark:text-amber-400 shadow-sm' : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'}`}
              >
                Pending ({pendingCount})
              </button>
              <button
                onClick={() => setActiveQueueTab('IN_REVIEW')}
                className={`px-3 py-1 rounded-lg transition-all ${activeQueueTab === 'IN_REVIEW' ? 'bg-[var(--bg-surface)] text-purple-600 dark:text-purple-400 shadow-sm' : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'}`}
              >
                In Review ({inReviewCount})
              </button>
              <button
                onClick={() => setActiveQueueTab('COMPLETED')}
                className={`px-3 py-1 rounded-lg transition-all ${activeQueueTab === 'COMPLETED' ? 'bg-[var(--bg-surface)] text-emerald-600 dark:text-emerald-400 shadow-sm' : 'text-[var(--text-muted)] hover:text-[var(--text-main)]'}`}
              >
                Completed ({completedCount})
              </button>
            </div>
          </div>
        </div>

        {/* Table */}
        <Table headers={['CONSULTATION ID', 'PATIENT NAME', 'SPECIALTY', 'STATUS', 'SCHEDULED DATE', 'ACTION']}>
          {filteredQueue.length > 0 ? (
            filteredQueue.map((c, idx) => {
              const isPending = ['REQUESTED', 'ASSIGNED', 'PENDING'].includes(c.status);
              const isInReview = ['ACCEPTED', 'CONFIRMED', 'UPCOMING', 'IN_CONSULTATION', 'ACTIVE'].includes(c.status);
              const isCompleted = c.status === 'COMPLETED';

              return (
                <TableRow key={c.consultation_id || c.id || `queue-row-${idx}`}>
                  <TableCell className="font-mono text-xs font-bold text-[var(--primary)]">
                    {c.consultation_id || c.id}
                  </TableCell>
                  <TableCell className="font-semibold text-xs text-[var(--text-main)]">
                    {c.patient_name || c.full_name || 'Patient Record'}
                  </TableCell>
                  <TableCell className="text-xs text-[var(--text-muted)] font-medium">
                    {c.specialty || c.category || doctorSpecialty}
                  </TableCell>
                  <TableCell>
                    <Badge
                      variant={isCompleted ? 'success' : isInReview ? 'accent' : 'warning'}
                      size="sm"
                      className="!text-[10px] uppercase font-mono font-bold"
                    >
                      {c.status}
                    </Badge>
                  </TableCell>
                  <TableCell className="font-mono text-xs text-[var(--text-muted)]">
                    {c.appointment_date || c.scheduled_at || 'Today'}
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center gap-2">
                      {isPending && (
                        <Button
                          variant="primary"
                          size="sm"
                          className="!px-3 !py-1 text-xs font-bold rounded-lg"
                          onClick={() => handleOpenConsultationWorkspace(c)}
                        >
                          👁 Review Case
                        </Button>
                      )}
                      {isInReview && (
                        <Button
                          variant="primary"
                          size="sm"
                          className="!px-3 !py-1 text-xs font-bold rounded-lg"
                          onClick={() => handleOpenConsultationWorkspace(c)}
                        >
                          👁 Continue Review
                        </Button>
                      )}
                      {isCompleted && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="!px-3 !py-1 text-xs font-semibold rounded-lg"
                          onClick={() => setSelectedConsultationForDetails(c)}
                        >
                          👁 View Summary
                        </Button>
                      )}
                    </div>
                  </TableCell>
                </TableRow>
              );
            })
          ) : (
            <TableRow>
              <TableCell colSpan={6} className="text-center py-8 text-[var(--text-muted)] text-xs font-medium">
                No consultations found in the selected queue filter.
              </TableCell>
            </TableRow>
          )}
        </Table>

        <div className="pt-2 text-right">
          <button
            onClick={() => onNavigate ? onNavigate('/doctor/consultations') : navigate('/doctor/consultations')}
            className="text-xs font-bold text-[var(--primary)] hover:underline inline-flex items-center gap-1"
          >
            View all consultations →
          </button>
        </div>
      </Card>

      {/* 5. LOWER ANALYTICS & INSIGHTS GRID (2 COLUMNS) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column (8 cols): Workload, High Risk Monitor, Review Analytics */}
        <div className="lg:col-span-8 space-y-6">
          <WorkloadPanel consultations={allConsultations} />
          <HighRiskPatients
            consultations={allConsultations}
            onReview={(c) => handleOpenConsultationWorkspace(c)}
            onMessage={(c) => handleOpenConsultationWorkspace(c)}
          />
          <ReviewAnalytics consultations={allConsultations} />
        </div>

        {/* Right Column (4 cols): AI Clinical Insights & Patient Outcome Tracking */}
        <div className="lg:col-span-4 space-y-6">
          <InsightsPanel consultations={allConsultations} />
          <OutcomeTracking
            consultations={allConsultations}
            onOpenAnalytics={() => setShowDetailedAnalyticsModal(true)}
          />
        </div>
      </div>

      {/* 6. FOOTER */}
      <div className="pt-8 border-t border-[var(--border-subtle)] flex flex-col sm:flex-row items-center justify-between text-[11px] text-[var(--text-muted)] font-medium gap-2">
        <span>© 2024 TeleMed AI, All rights reserved.</span>
        <span>HIPAA Compliant • Secure • Encrypted</span>
      </div>

      {/* SUMMARY MODAL */}
      <Modal
        isOpen={Boolean(selectedConsultationForDetails)}
        onClose={() => setSelectedConsultationForDetails(null)}
        title={`Consultation Summary | ${selectedConsultationForDetails?.consultation_id || ''}`}
        size="md"
      >
        {selectedConsultationForDetails && (
          <div className="space-y-4 text-xs">
            <div className="p-4 rounded-xl bg-[var(--bg-primary)] space-y-2 border border-[var(--border-subtle)]">
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)] font-mono uppercase">Patient Name</span>
                <strong className="text-[var(--text-main)]">{selectedConsultationForDetails.patient_name || 'Patient'}</strong>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)] font-mono uppercase">Specialty</span>
                <span>{selectedConsultationForDetails.specialty || doctorSpecialty}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-[var(--text-muted)] font-mono uppercase">Status</span>
                <Badge variant="success" size="sm">COMPLETED</Badge>
              </div>
            </div>

            <div className="space-y-1">
              <label className="font-bold text-[var(--text-main)]">Clinical Notes & Summary</label>
              <div className="p-3 rounded-xl bg-[var(--bg-primary)] border border-[var(--border-subtle)] text-[var(--text-main)] leading-relaxed">
                {selectedConsultationForDetails.clinical_notes || selectedConsultationForDetails.reason_for_visit || 'Consultation completed and published to patient health records.'}
              </div>
            </div>

            <div className="pt-3 border-t border-[var(--border-subtle)] flex justify-end">
              <Button variant="outline" size="sm" onClick={() => setSelectedConsultationForDetails(null)}>
                Close Summary
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* DETAILED CLINICAL ANALYTICS MODAL */}
      <Modal
        isOpen={showDetailedAnalyticsModal}
        onClose={() => setShowDetailedAnalyticsModal(false)}
        title="Detailed Clinical Analytics & Cohort Metrics"
        size="lg"
      >
        <div className="space-y-5 text-xs p-1">
          <div className="p-4 bg-gradient-to-r from-slate-900 to-indigo-950 text-white rounded-2xl flex items-center justify-between shadow-md">
            <div>
              <h4 className="text-sm font-extrabold text-white">Real-Time Clinical Performance Overview</h4>
              <p className="text-xs text-slate-300 mt-0.5">Calculated directly from {allConsultations.length} live assigned patient cases.</p>
            </div>
            <div className="text-right">
              <span className="text-2xl font-black text-emerald-400">
                {allConsultations.length > 0 ? Math.round((completedCount / allConsultations.length) * 100) : 0}%
              </span>
              <span className="text-[10px] text-slate-400 block font-semibold">Sign-Off Rate</span>
            </div>
          </div>

          {/* Status Breakdown Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div className="p-3 rounded-xl bg-blue-50 border border-blue-200 text-blue-900 space-y-1">
              <span className="text-[10px] font-bold uppercase text-blue-600 block">Total Cohort</span>
              <span className="text-xl font-extrabold text-blue-950 block">{totalCount} Patients</span>
            </div>
            <div className="p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-900 space-y-1">
              <span className="text-[10px] font-bold uppercase text-amber-600 block">Pending Review</span>
              <span className="text-xl font-extrabold text-amber-950 block">{pendingCount} Cases</span>
            </div>
            <div className="p-3 rounded-xl bg-indigo-50 border border-indigo-200 text-indigo-900 space-y-1">
              <span className="text-[10px] font-bold uppercase text-indigo-600 block">Active In-Review</span>
              <span className="text-xl font-extrabold text-indigo-950 block">{inReviewCount} Cases</span>
            </div>
            <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-900 space-y-1">
              <span className="text-[10px] font-bold uppercase text-emerald-600 block">Signed Off</span>
              <span className="text-xl font-extrabold text-emerald-950 block">{completedCount} Cases</span>
            </div>
          </div>

          {/* Specialty Distribution */}
          <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-3">
            <h4 className="text-xs font-extrabold text-slate-800 uppercase tracking-wider">Specialty & Category Breakdown</h4>
            
            {allConsultations.length === 0 ? (
              <p className="text-xs text-slate-400 italic">No consultations available for distribution analysis.</p>
            ) : (
              <div className="space-y-2">
                {Object.entries(
                  allConsultations.reduce((acc, c) => {
                    const spec = c.specialization || c.specialty || c.category || 'General Medicine';
                    acc[spec] = (acc[spec] || 0) + 1;
                    return acc;
                  }, {})
                ).map(([spec, count]) => {
                  const pct = Math.round((count / allConsultations.length) * 100);
                  return (
                    <div key={spec} className="space-y-1">
                      <div className="flex justify-between font-bold text-slate-800 text-xs">
                        <span>{spec}</span>
                        <span className="font-mono text-slate-500">{count} Cases ({pct}%)</span>
                      </div>
                      <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                        <div className="h-full bg-blue-600 rounded-full" style={{ width: `${pct}%` }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          <div className="pt-2 text-right">
            <Button variant="primary" size="sm" onClick={() => setShowDetailedAnalyticsModal(false)}>
              Close Detailed Analytics
            </Button>
          </div>
        </div>
      </Modal>
    </PageContainer>
  );
}
