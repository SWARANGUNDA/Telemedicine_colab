import React, { createContext, useContext, useState, useCallback, useRef } from 'react';
import { CheckCircle2, AlertTriangle, Info, XCircle, X } from 'lucide-react';

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const recentMapRef = useRef(new Map());

  const removeToast = useCallback((id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const addToast = useCallback(({ type = 'info', title, message, duration = 4000 }) => {
    const msgKey = `${type}:${title || ''}:${message}`;
    const now = Date.now();
    const lastSeen = recentMapRef.current.get(msgKey);

    // Prevent duplicate toast if fired within 2 seconds
    if (lastSeen && now - lastSeen < 2000) {
      return;
    }
    recentMapRef.current.set(msgKey, now);

    const id = `toast_${now}_${Math.random().toString(36).substr(2, 6)}`;
    const newToast = { id, type, title, message, duration };

    setToasts((prev) => [...prev.slice(-4), newToast]); // Keep max 5 toasts

    if (duration > 0) {
      setTimeout(() => {
        removeToast(id);
      }, duration);
    }
  }, [removeToast]);

  const toast = {
    success: (message, title = 'Success') => addToast({ type: 'success', title, message }),
    error: (message, title = 'Error') => addToast({ type: 'error', title, message, duration: 6000 }),
    info: (message, title = 'Notice') => addToast({ type: 'info', title, message }),
    warning: (message, title = 'Warning') => addToast({ type: 'warning', title, message, duration: 5000 }),
  };

  return (
    <ToastContext.Provider value={{ toast, addToast, removeToast }}>
      {children}
      {/* Toast Container Floating Overlay */}
      <div
        style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          zIndex: 999999,
          display: 'flex',
          flexDirection: 'column',
          gap: '10px',
          maxWidth: '420px',
          width: 'calc(100vw - 40px)',
          pointerEvents: 'none',
        }}
      >
        {toasts.map((t) => (
          <ToastItem key={t.id} toast={t} onClose={() => removeToast(t.id)} />
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    // Return fallback no-op if context is missing
    return {
      success: () => {},
      error: () => {},
      info: () => {},
      warning: () => {},
    };
  }
  return context.toast;
}

function ToastItem({ toast, onClose }) {
  const { type, title, message } = toast;

  let borderColor = 'var(--accent-cyan)';
  let bgGradient = 'rgba(6, 182, 212, 0.12)';
  let Icon = Info;
  let iconColor = 'var(--accent-cyan)';

  if (type === 'success') {
    borderColor = 'var(--accent-emerald)';
    bgGradient = 'rgba(16, 185, 129, 0.12)';
    Icon = CheckCircle2;
    iconColor = 'var(--accent-emerald)';
  } else if (type === 'error') {
    borderColor = 'var(--accent-rose)';
    bgGradient = 'rgba(244, 63, 94, 0.14)';
    Icon = XCircle;
    iconColor = 'var(--accent-rose)';
  } else if (type === 'warning') {
    borderColor = 'var(--accent-amber)';
    bgGradient = 'rgba(245, 158, 11, 0.14)';
    Icon = AlertTriangle;
    iconColor = 'var(--accent-amber)';
  }

  return (
    <div
      style={{
        pointerEvents: 'auto',
        display: 'flex',
        alignItems: 'flex-start',
        gap: '12px',
        padding: '14px 16px',
        borderRadius: '12px',
        background: 'var(--bg-surface)',
        backgroundColor: bgGradient,
        borderLeft: `4px solid ${borderColor}`,
        borderTop: '1px solid var(--border-subtle)',
        borderRight: '1px solid var(--border-subtle)',
        borderBottom: '1px solid var(--border-subtle)',
        boxShadow: '0 12px 30px rgba(0, 0, 0, 0.25)',
        backdropFilter: 'blur(16px)',
        color: 'var(--text-main)',
        fontSize: '0.88rem',
        animation: 'slideInRight 0.25s ease-out',
        position: 'relative',
      }}
    >
      <Icon size={20} style={{ color: iconColor, flexShrink: 0, marginTop: '2px' }} />
      <div style={{ flex: 1, minWidth: 0 }}>
        {title && (
          <strong style={{ display: 'block', fontSize: '0.88rem', fontWeight: 700, marginBottom: '2px', color: 'var(--text-main)' }}>
            {title}
          </strong>
        )}
        <div style={{ color: 'var(--text-muted)', fontSize: '0.84rem', lineHeight: 1.4, wordBreak: 'break-word' }}>
          {message}
        </div>
      </div>
      <button
        onClick={onClose}
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--text-muted)',
          cursor: 'pointer',
          padding: '2px',
          borderRadius: '4px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
        }}
        title="Close Toast"
      >
        <X size={16} />
      </button>
    </div>
  );
}
