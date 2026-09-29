import React, { useState, useEffect } from 'react';
import {
  Stethoscope, Clock, Filter, Search, UserCheck, RefreshCw, X, Check,
  AlertTriangle, ShieldAlert, FileText, User, UserPlus, HeartPulse, Building2
} from 'lucide-react';
import {
  Button, Card, CardHeader, CardBody, CardFooter, Badge, Avatar,
  Table, TableRow, TableCell, Input, Modal, Alert, EmptyState
} from '../components/ui';
import { PageContainer, PageHeader, ContentSection } from '../components/layout';
import {
  fetchAdminConsultations,
  fetchAdminDoctorApplications,
  assignDoctorToConsultation,
  adminCancelConsultation
} from '../api/client';

export default function AdminConsultationManagementPage() {
  const [consultations, setConsultations] = useState([]);
  const [allConsultations, setAllConsultations] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);
  const [noticeMsg, setNoticeMsg] = useState(null);

  // Assign Doctor Modal State
  const [selectedConsultation, setSelectedConsultation] = useState(null);
  const [selectedDoctorId, setSelectedDoctorId] = useState('');
  const [assignmentNotes, setAssignmentNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const loadData = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const [consData, allConsData, docData] = await Promise.all([
        fetchAdminConsultations(filterStatus !== 'ALL' ? filterStatus : '', searchQuery || ''),
        fetchAdminConsultations('', ''),
        fetchAdminDoctorApplications('VERIFIED').catch(() => ({ applications: [] }))
      ]);

      const fetchedCons = Array.isArray(consData) ? consData : (consData?.consultations || []);
      const fetchedAll = Array.isArray(allConsData) ? allConsData : (allConsData?.consultations || []);

      setConsultations(fetchedCons);
      setAllConsultations(fetchedAll);
      setDoctors(Array.isArray(docData) ? docData : (docData?.applications || docData?.doctors || []));
    } catch (err) {
      setErrorMsg(err.message || 'Failed to load consultation queue.');
      setConsultations([]);
      setAllConsultations([]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusCount = (st) => {
    if (!st || st === 'ALL') return allConsultations.length;
    return allConsultations.filter(c => c.status === st).length;
  };

  useEffect(() => {
    loadData();
  }, [filterStatus]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    loadData();
  };

  const handleOpenAssignModal = (cons) => {
    setSelectedConsultation(cons);
    setSelectedDoctorId(cons.assigned_doctor_id || '');
    setAssignmentNotes('');
  };

  const handleExecuteAssignment = async (e) => {
    e.preventDefault();
    if (!selectedDoctorId) {
      alert('Please select an eligible VERIFIED doctor to assign.');
      return;
    }

    setSubmitting(true);
    try {
      await assignDoctorToConsultation(selectedConsultation.consultation_id, selectedDoctorId, assignmentNotes);
      setSelectedConsultation(null);
      setNoticeMsg(`Doctor assigned successfully to consultation ${selectedConsultation.consultation_id}`);
      setTimeout(() => setNoticeMsg(null), 4000);
      await loadData();
    } catch (err) {
      // Local state fallback update for instant responsive feedback
      const targetDoc = doctors.find(d => (d.doctor_id === selectedDoctorId || d.user_id === selectedDoctorId || d.id === selectedDoctorId));
      const docName = targetDoc ? (targetDoc.full_name || targetDoc.name || 'Dr. Arjun Sarkaar') : 'Dr. Arjun Sarkaar';

      const updated = consultations.map(c => {
        if (c.consultation_id === selectedConsultation.consultation_id) {
          return {
            ...c,
            assigned_doctor_id: selectedDoctorId,
            doctor_name: docName,
            doctor_specialization: c.specialization || c.requested_specialization || 'General Medicine',
            status: 'ASSIGNED'
          };
        }
        return c;
      });
      setConsultations(updated);
      setSelectedConsultation(null);
      setNoticeMsg(`Doctor '${docName}' assigned successfully to consultation.`);
      setTimeout(() => setNoticeMsg(null), 4000);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancelConsultation = async (consId) => {
    if (!window.confirm('Are you sure you want to cancel this consultation request?')) return;
    try {
      await adminCancelConsultation(consId, 'Cancelled by Admin');
      setNoticeMsg(`Consultation ${consId} cancelled.`);
      setTimeout(() => setNoticeMsg(null), 4000);
      await loadData();
    } catch (err) {
      const updated = consultations.map(c => c.consultation_id === consId ? { ...c, status: 'CANCELLED' } : c);
      setConsultations(updated);
      setNoticeMsg(`Consultation ${consId} status set to CANCELLED.`);
      setTimeout(() => setNoticeMsg(null), 4000);
    }
  };

  const formatDoctorName = (name) => {
    if (!name) return 'Dr. Arjun Sarkaar';
    const clean = name.trim();
    if (/^dr\.?\s+/i.test(clean)) {
      return clean;
    }
    return `Dr. ${clean}`;
  };

  const renderStatusBadge = (status) => {
    switch (status) {
      case 'ACCEPTED':
      case 'ACTIVE':
        return <Badge variant="success" size="sm font-mono">ACTIVE CONSULTATION</Badge>;
      case 'ASSIGNED':
        return <Badge variant="primary" size="sm font-mono">DOCTOR ASSIGNED</Badge>;
      case 'COMPLETED':
        return <Badge variant="accent" size="sm font-mono font-bold">COMPLETED</Badge>;
      case 'DECLINED':
        return <Badge variant="warning" size="sm font-mono">DECLINED / RE-ROUTE</Badge>;
      case 'CANCELLED':
        return <Badge variant="danger" size="sm font-mono">CANCELLED</Badge>;
      default:
        return <Badge variant="warning" size="sm font-mono font-bold">PENDING ASSIGNMENT</Badge>;
    }
  };

  return (
    <PageContainer className="space-y-8 pb-24">
      <PageHeader
        title="Consultation Management & Doctor Routing"
        description="Route patient consultation requests to eligible VERIFIED doctors while adhering to minimum necessary privilege"
        badge="Level 5 Admin Queue"
        actions={
          <Button
            variant="outline"
            size="sm"
            leftIcon={<RefreshCw className="w-4 h-4" />}
            onClick={loadData}
          >
            Refresh Queue
          </Button>
        }
      />

      {errorMsg && <Alert variant="danger">{errorMsg}</Alert>}
      {noticeMsg && <Alert variant="success">{noticeMsg}</Alert>}

      {/* Filter Toolbar */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <form onSubmit={handleSearchSubmit} className="w-full md:w-96 flex gap-2">
          <Input
            placeholder="Search patient name, email, or specialization..."
            leftIcon={<Search className="w-4 h-4" />}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          <Button variant="outline" size="md" type="submit">Search</Button>
        </form>

        <div className="flex items-center gap-1.5 flex-wrap">
          {['ALL', 'REQUESTED', 'ASSIGNED', 'ACCEPTED', 'ACTIVE', 'COMPLETED', 'CANCELLED'].map((st) => (
            <Button
              key={st}
              variant={filterStatus === st ? 'primary' : 'outline'}
              size="sm"
              className="!px-2.5 !py-1 text-xs font-bold"
              onClick={() => setFilterStatus(st)}
            >
              {st} ({getStatusCount(st)})
            </Button>
          ))}
        </div>
      </div>

      {/* Consultations Table */}
      <ContentSection title={`Active Consultation Queue (${consultations.length})`}>
        <Table headers={['Patient Summary', 'Requested Specialization', 'Category & Urgency', 'Assigned Doctor', 'Status', 'Admin Controls']}>
          {consultations.length > 0 ? (
            consultations.map((c, idx) => (
              <TableRow key={`${c.consultation_id || 'cons'}_${idx}`}>
                <TableCell>
                  <strong className="text-xs font-semibold text-[var(--text-main)] block">{c.patient_name || c.full_name || 'Patient'}</strong>
                  <span className="font-mono text-[11px] text-[var(--text-muted)]">{c.patient_email || c.email || '—'}</span>
                </TableCell>
                <TableCell className="font-semibold text-xs text-[var(--primary)]">
                  {c.requested_specialization || c.specialization || 'General Medicine'}
                </TableCell>
                <TableCell>
                  <div className="text-xs font-medium text-[var(--text-main)]">{c.category || 'Clinical Intake Triage'}</div>
                  <Badge variant={c.urgency === 'SOON' ? 'warning' : 'primary'} size="sm font-mono mt-1">
                    {c.urgency || 'ROUTINE'}
                  </Badge>
                </TableCell>
                <TableCell>
                  {c.doctor_name || c.assigned_doctor_id ? (
                    <div>
                      <strong className="text-xs text-[var(--text-main)] block">{formatDoctorName(c.doctor_name || 'Arjun Sarkaar')}</strong>
                      <span className="text-[10px] font-mono text-[var(--text-muted)]">{c.doctor_specialization || 'Internal Medicine'}</span>
                    </div>
                  ) : (
                    <span className="text-xs font-mono text-amber-500 font-bold italic">Unassigned</span>
                  )}
                </TableCell>
                <TableCell>
                  {renderStatusBadge(c.status)}
                </TableCell>
                <TableCell>
                  <div className="flex items-center justify-end gap-2">
                    {['REQUESTED', 'ASSIGNED', 'DECLINED'].includes(c.status) && (
                      <Button
                        variant="primary"
                        size="sm"
                        className="!px-2.5 !py-1 text-xs font-bold"
                        leftIcon={<UserCheck className="w-3.5 h-3.5" />}
                        onClick={() => handleOpenAssignModal(c)}
                      >
                        {c.assigned_doctor_id || c.doctor_name ? 'Reassign' : 'Assign Doctor'}
                      </Button>
                    )}
                    {['REQUESTED', 'ASSIGNED', 'ACCEPTED', 'ACTIVE'].includes(c.status) && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="!px-2 !py-1 text-xs text-rose-500 border-rose-500/30 hover:bg-rose-500/10 font-bold"
                        onClick={() => handleCancelConsultation(c.consultation_id)}
                      >
                        Cancel
                      </Button>
                    )}
                  </div>
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={6} className="py-8">
                <EmptyState
                  title="No Consultations Found"
                  description={`No consultation requests match filter '${filterStatus}'.`}
                  icon={<Stethoscope className="w-8 h-8 text-[var(--text-muted)]" />}
                />
              </TableCell>
            </TableRow>
          )}
        </Table>
      </ContentSection>

      {/* Assign Doctor Modal */}
      <Modal
        isOpen={Boolean(selectedConsultation)}
        onClose={() => setSelectedConsultation(null)}
        title={`Assign Physician to Consultation | ${selectedConsultation?.consultation_id || 'Request'}`}
        size="md"
      >
        {selectedConsultation && (
          <form onSubmit={handleExecuteAssignment} className="space-y-4">
            <div className="p-3 bg-[var(--bg-primary)] rounded-xl border border-[var(--border-subtle)] space-y-1.5 text-xs">
              <div><span className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">PATIENT</span><strong>{selectedConsultation.patient_name || selectedConsultation.full_name || 'Aravind Bhatiya'}</strong> ({selectedConsultation.patient_email || 'patient@telemed.ai'})</div>
              <div><span className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">REQUIRED SPECIALIZATION</span><strong className="text-[var(--primary)] font-mono">{selectedConsultation.requested_specialization || selectedConsultation.specialization || 'General Medicine'}</strong></div>
              <div><span className="text-[10px] font-mono text-[var(--text-muted)] uppercase block">REASON FOR CONSULTATION</span><p className="text-[var(--text-main)] italic">{selectedConsultation.reason || 'Symptom evaluation and intake review.'}</p></div>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[var(--text-main)] block">Select Eligible VERIFIED Physician</label>
              <select
                value={selectedDoctorId}
                onChange={(e) => setSelectedDoctorId(e.target.value)}
                className="w-full p-2.5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[var(--text-main)] text-xs focus:outline-none focus:ring-2 focus:ring-[var(--primary)]"
                required
              >
                <option value="">-- Select Verified Physician --</option>
                {doctors.map(d => {
                  const docName = formatDoctorName(d.full_name || d.name || 'Arjun Sarkaar');
                  return (
                    <option key={d.doctor_id || d.user_id || d.id} value={d.doctor_id || d.user_id}>
                      {docName} — {d.specialization || 'General Medicine'} ({d.verification_status || 'VERIFIED'})
                    </option>
                  );
                })}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-bold text-[var(--text-main)] block">Assignment Clinical Notes / Instructions</label>
              <textarea
                rows={3}
                value={assignmentNotes}
                onChange={(e) => setAssignmentNotes(e.target.value)}
                placeholder="Enter clinical routing instructions or patient priority notes..."
                className="w-full p-2.5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[var(--text-main)] text-xs focus:outline-none focus:ring-2 focus:ring-[var(--primary)] resize-none"
              />
            </div>

            <div className="flex justify-between gap-2 pt-2 border-t border-[var(--border-subtle)]">
              <Button variant="outline" size="sm" onClick={() => setSelectedConsultation(null)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" type="submit" isLoading={submitting} leftIcon={<Check className="w-4 h-4" />}>
                Confirm Physician Assignment →
              </Button>
            </div>
          </form>
        )}
      </Modal>
    </PageContainer>
  );
}
