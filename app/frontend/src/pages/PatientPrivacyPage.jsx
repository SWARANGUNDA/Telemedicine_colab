import React, { useState, useEffect } from 'react';
import {
  Shield, Download, Trash2, Eye, Lock, FileText, AlertCircle, CheckCircle2,
  Clock, RefreshCw, X, ShieldAlert, Check
} from 'lucide-react';
import {
  Button, Card, Badge, Table, TableRow, TableCell, Modal, Alert, EmptyState
} from '../components/ui';
import { PageContainer, PageHeader, ContentSection } from '../components/layout';
import { fetchPatientAccessHistory, exportUserAccountData, requestAccountDeletion } from '../api/client';

export default function PatientPrivacyPage({ user }) {
  const [accessLogs, setAccessLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Deletion modal
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteReason, setDeleteReason] = useState('');
  const [deleting, setDeleting] = useState(false);
  const [deleteStatus, setDeleteStatus] = useState(null);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    loadAccessHistory();
  }, []);

  const loadAccessHistory = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetchPatientAccessHistory();
      setAccessLogs(res.access_history || []);
    } catch (err) {
      setAccessLogs([]);
    } finally {
      setLoading(false);
    }
  };

  const handleExportData = async () => {
    setExporting(true);
    try {
      const data = await exportUserAccountData();
      const content = typeof data === 'string' ? data : JSON.stringify(data, null, 2);
      const blob = new Blob([content], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `telemed_account_data_${user?.user_id || 'export'}.json`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.message || 'Failed to export account data.');
    } finally {
      setExporting(false);
    }
  };

  const handleDeleteSubmit = async (e) => {
    e.preventDefault();
    setDeleting(true);
    setError(null);
    try {
      const res = await requestAccountDeletion(deleteReason);
      setDeleteStatus(res);
      setShowDeleteModal(false);
    } catch (err) {
      setError(err.message || 'Failed to submit deletion request.');
    } finally {
      setDeleting(false);
    }
  };

  return (
    <PageContainer className="space-y-8 pb-24">
      <PageHeader
        title="Data Privacy, Access Logs & Governance"
        description="Complete transparency into who accessed your clinical data, export personal records, or manage account governance"
        badge="Platform Governance"
        actions={
          <div className="flex items-center gap-3">
            <Button
              variant="outline"
              size="sm"
              leftIcon={<Download className="w-4 h-4 text-[var(--primary)]" />}
              onClick={handleExportData}
              isLoading={exporting}
            >
              Export My Data (JSON)
            </Button>
            <Button
              variant="outline"
              size="sm"
              className="!text-rose-500 border-rose-500/30 hover:bg-rose-500/10 font-bold"
              leftIcon={<Trash2 className="w-4 h-4 text-rose-500" />}
              onClick={() => setShowDeleteModal(true)}
            >
              Delete Account
            </Button>
          </div>
        }
      />

      {deleteStatus && (
        <Alert variant="info" title={`Deletion Request Submitted (ID: ${deleteStatus.request_id})`}>
          <div className="space-y-1">
            <p className="font-semibold">{deleteStatus.message}</p>
            <p className="text-xs opacity-80">{deleteStatus.policy_note}</p>
          </div>
        </Alert>
      )}

      {error && (
        <Alert variant="danger">
          {error}
        </Alert>
      )}

      {/* ACCESS HISTORY TABLE */}
      <ContentSection title="Who Accessed My Data? (Audit Trail)">
        <Table headers={['Timestamp (UTC)', 'Accessor', 'Role', 'Action / Purpose', 'Resource ID', 'Status']}>
          {loading ? (
            <TableRow>
              <TableCell colSpan={6} className="py-8 text-center text-xs font-mono text-[var(--text-muted)]">
                Loading encrypted audit logs...
              </TableCell>
            </TableRow>
          ) : accessLogs.length > 0 ? (
            accessLogs.map((log) => (
              <TableRow key={log.event_id}>
                <TableCell className="font-mono text-xs text-[var(--text-muted)]">
                  {new Date(log.timestamp).toLocaleString()}
                </TableCell>
                <TableCell className="font-semibold text-xs text-[var(--text-main)]">
                  {log.actor_email || log.actor_user_id}
                </TableCell>
                <TableCell>
                  <Badge variant="primary" size="sm font-mono">
                    {log.role}
                  </Badge>
                </TableCell>
                <TableCell className="font-mono text-xs font-semibold text-[var(--primary)]">
                  {log.action}
                </TableCell>
                <TableCell className="font-mono text-xs text-[var(--text-muted)]">
                  {log.resource_type} ({log.resource_id.slice(0, 10)})
                </TableCell>
                <TableCell>
                  <Badge variant={log.outcome === 'SUCCESS' ? 'success' : 'danger'} size="sm font-mono font-bold">
                    {log.outcome}
                  </Badge>
                </TableCell>
              </TableRow>
            ))
          ) : (
            <TableRow>
              <TableCell colSpan={6} className="py-8">
                <EmptyState
                  title="No Access Events Recorded"
                  description="No external clinical data access events are logged for this account."
                  icon={<Eye className="w-8 h-8 text-[var(--text-muted)]" />}
                />
              </TableCell>
            </TableRow>
          )}
        </Table>
      </ContentSection>

      {/* PLATFORM RETENTION & GOVERNANCE POLICY */}
      <Card isGlass={true} className="p-6 bg-[var(--bg-primary)] space-y-4">
        <div className="flex items-center gap-2 pb-3 border-b border-[var(--border-subtle)]">
          <Lock className="w-5 h-5 text-indigo-400" />
          <h3 className="text-base font-extrabold text-[var(--text-main)]">Platform Data Retention & Governance Policy</h3>
        </div>

        <p className="text-xs text-[var(--text-muted)] leading-relaxed">
          In accordance with TeleMed AI platform data governance and HIPAA/GDPR clinical compliance guidelines:
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
          <div className="p-3.5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1">
            <strong className="text-[var(--text-main)] font-extrabold block">Consent Revocation</strong>
            <p className="text-[var(--text-muted)] text-[11px]">Revoking doctor access immediately removes clinical visibility for that practitioner.</p>
          </div>

          <div className="p-3.5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1">
            <strong className="text-[var(--text-main)] font-extrabold block">Data Minimization</strong>
            <p className="text-[var(--text-muted)] text-[11px]">Raw passwords, salts, and session keys are never written to audit trails.</p>
          </div>

          <div className="p-3.5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1">
            <strong className="text-[var(--text-main)] font-extrabold block">Cryptographic Hash Integrity</strong>
            <p className="text-[var(--text-muted)] text-[11px]">Audit records use SHA-256 hash chaining to ensure logs cannot be modified or deleted.</p>
          </div>

          <div className="p-3.5 rounded-2xl bg-[var(--bg-surface)] border border-[var(--border-subtle)] space-y-1">
            <strong className="text-[var(--text-main)] font-extrabold block">Legal Retention Note</strong>
            <p className="text-[var(--text-muted)] text-[11px]">Account deletion requests queue for administrative processing; historical audit events remain retained per policy.</p>
          </div>
        </div>
      </Card>

      {/* ACCOUNT DELETION MODAL */}
      <Modal
        isOpen={showDeleteModal}
        onClose={() => setShowDeleteModal(false)}
        title="Confirm Account Deletion Request"
        size="md"
      >
        <form onSubmit={handleDeleteSubmit} className="space-y-4">
          <Alert variant="warning" title="Warning: Administrative Queueing">
            Account deletion requests are queued for administrative compliance review. Clinical audit trails will remain hash-sealed per legal retention policy.
          </Alert>

          <div className="space-y-1.5">
            <label className="text-xs font-bold text-[var(--text-main)] block">Reason for Deletion (Optional)</label>
            <textarea
              rows={3}
              value={deleteReason}
              onChange={(e) => setDeleteReason(e.target.value)}
              placeholder="Provide context or feedback for your account deletion request..."
              className="w-full p-2.5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[var(--text-main)] text-xs focus:outline-none focus:ring-2 focus:ring-[var(--primary)] resize-none"
            />
          </div>

          <div className="flex justify-between gap-2 pt-2 border-t border-[var(--border-subtle)]">
            <Button variant="outline" size="sm" onClick={() => setShowDeleteModal(false)}>
              Cancel
            </Button>
            <Button
              variant="outline"
              size="sm"
              type="submit"
              isLoading={deleting}
              className="!bg-rose-500 !text-white hover:!bg-rose-600 font-bold"
              leftIcon={<Trash2 className="w-4 h-4" />}
            >
              Confirm Deletion Request
            </Button>
          </div>
        </form>
      </Modal>

    </PageContainer>
  );
}
