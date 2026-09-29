import React from 'react';
import { Check, Circle, Lock } from 'lucide-react';

export default function WorkflowStepper({ currentState, activePage, setActivePage, onAttemptLockedNavigation }) {
  const steps = [
    { num: 1, id: 'intake_upload', label: '1 Upload', page: 'intake', minState: 'CREATED' },
    { num: 2, id: 'intake_extract', label: '2 Extract', page: 'intake', minState: 'EXTRACTED' },
    { num: 3, id: 'intake_review', label: '3 Review', page: 'intake', minState: 'CONFIRMED' },
    { num: 4, id: 'risk_dashboard', label: '4 Risk', page: 'dashboard', minState: 'ANALYZED' },
    { num: 5, id: 'xai_explain', label: '5 Explain', page: 'xai', minState: 'XAI_READY' },
    { num: 6, id: 'rag_report', label: '6 Report', page: 'report', minState: 'REPORT_READY' },
  ];

  const stateOrder = ['CREATED', 'EXTRACTED', 'CONFIRMED', 'ANALYZED', 'XAI_READY', 'REPORT_READY'];
  const currentIndex = stateOrder.indexOf(currentState || 'CREATED');

  const handleStepClick = (step) => {
    const minIndex = stateOrder.indexOf(step.minState);
    const isLocked = currentIndex < stateOrder.indexOf('ANALYZED') && minIndex >= stateOrder.indexOf('ANALYZED');

    if (isLocked) {
      if (onAttemptLockedNavigation) {
        onAttemptLockedNavigation('Complete data review and run prediction first before accessing downstream stages.');
      }
      return;
    }

    setActivePage(step.page);
  };

  return (
    <div style={{
      background: 'var(--bg-primary)',
      borderBottom: '1px solid var(--border-subtle)',
      padding: '12px 0'
    }}>
      <div className="app-container" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          overflowX: 'auto',
          maxWidth: '100%',
          padding: '4px 0'
        }}>
          {steps.map((step, idx) => {
            const stepIndex = stateOrder.indexOf(step.minState);
            const isCompleted = currentIndex > stepIndex;
            const isCurrent = currentIndex === stepIndex;
            const isLocked = currentIndex < stateOrder.indexOf('ANALYZED') && stepIndex >= stateOrder.indexOf('ANALYZED');

            return (
              <React.Fragment key={step.id}>
                {idx > 0 && (
                  <div style={{
                    width: '32px',
                    height: '2px',
                    background: isCompleted ? 'var(--accent-cyan)' : 'var(--border-subtle)',
                    transition: 'background 0.3s ease'
                  }} />
                )}
                <button
                  onClick={() => handleStepClick(step)}
                  aria-disabled={isLocked}
                  title={isLocked ? 'Complete prediction first' : step.label}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    padding: '6px 14px',
                    borderRadius: '20px',
                    fontSize: '0.8rem',
                    fontWeight: isCurrent ? 700 : 500,
                    background: isCurrent
                      ? 'rgba(56, 189, 248, 0.15)'
                      : isCompleted
                      ? 'rgba(16, 185, 129, 0.1)'
                      : 'rgba(255, 255, 255, 0.03)',
                    border: isCurrent
                      ? '1px solid var(--accent-cyan)'
                      : isCompleted
                      ? '1px solid rgba(16, 185, 129, 0.4)'
                      : '1px solid var(--border-subtle)',
                    color: isCurrent
                      ? 'var(--accent-cyan)'
                      : isCompleted
                      ? 'var(--accent-emerald)'
                      : isLocked
                      ? 'var(--text-dim)'
                      : 'var(--text-muted)',
                    cursor: isLocked ? 'not-allowed' : 'pointer',
                    opacity: isLocked ? 0.45 : 1,
                    transition: 'all 0.2s ease',
                    whiteSpace: 'nowrap'
                  }}
                >
                  <span style={{ display: 'flex', alignItems: 'center' }}>
                    {isCompleted ? (
                      <Check size={14} style={{ color: 'var(--accent-emerald)' }} />
                    ) : isCurrent ? (
                      <span style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: 'var(--accent-cyan)',
                        boxShadow: '0 0 8px var(--accent-cyan)',
                        display: 'inline-block'
                      }} />
                    ) : isLocked ? (
                      <Lock size={12} style={{ color: 'var(--text-dim)' }} />
                    ) : (
                      <Circle size={10} style={{ color: 'var(--text-dim)' }} />
                    )}
                  </span>
                  <span>{step.label}</span>
                </button>
              </React.Fragment>
            );
          })}
        </div>
      </div>
    </div>
  );
}
